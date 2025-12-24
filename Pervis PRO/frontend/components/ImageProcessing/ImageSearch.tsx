import React, { useState, useCallback, useRef } from 'react';
import { 
  Search, 
  Image as ImageIcon, 
  Tag, 
  Palette, 
  Upload, 
  X, 
  Loader2,
  Filter,
  SlidersHorizontal
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';

export interface SearchResult {
  id: string;
  filename: string;
  description?: string;
  thumbnail_url?: string;
  original_url: string;
  similarity_score: number;
  match_reason: string;
  tags?: Record<string, string[]>;
  color_palette?: Record<string, any>;
  metadata: Record<string, any>;
}

export interface ImageSearchProps {
  projectId: string;
  onSearchResults?: (results: SearchResult[]) => void;
  onResultSelect?: (result: SearchResult) => void;
  className?: string;
}

type SearchMode = 'text' | 'image' | 'tags' | 'color';

export const ImageSearch: React.FC<ImageSearchProps> = ({
  projectId,
  onSearchResults,
  onResultSelect,
  className = ''
}) => {
  const [searchMode, setSearchMode] = useState<SearchMode>('text');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  
  // 文本搜索
  const [textQuery, setTextQuery] = useState('');
  
  // 图片搜索
  const [referenceImage, setReferenceImage] = useState<File | null>(null);
  const [referenceImagePreview, setReferenceImagePreview] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // 标签搜索
  const [tagQuery, setTagQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [tagMatchMode, setTagMatchMode] = useState<'any' | 'all'>('any');
  
  // 颜色搜索
  const [colorQuery, setColorQuery] = useState('#3b82f6');
  const [colorTolerance, setColorTolerance] = useState(0.3);
  
  // 高级选项
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.3);
  const [maxResults, setMaxResults] = useState(20);

  // 执行文本搜索
  const handleTextSearch = useCallback(async () => {
    if (!textQuery.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/images/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: textQuery,
          project_id: projectId,
          limit: maxResults,
          similarity_threshold: similarityThreshold
        })
      });

      if (!response.ok) {
        throw new Error(`搜索失败: ${response.statusText}`);
      }

      const searchResults = await response.json();
      setResults(searchResults);
      onSearchResults?.(searchResults);
    } catch (error) {
      console.error('Text search failed:', error);
      alert(`搜索失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [textQuery, projectId, maxResults, similarityThreshold, onSearchResults]);

  // 执行图片搜索
  const handleImageSearch = useCallback(async () => {
    if (!referenceImage) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', referenceImage);
      formData.append('project_id', projectId);
      formData.append('limit', maxResults.toString());
      formData.append('similarity_threshold', similarityThreshold.toString());

      const response = await fetch('/api/images/similar', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`搜索失败: ${response.statusText}`);
      }

      const searchResults = await response.json();
      setResults(searchResults);
      onSearchResults?.(searchResults);
    } catch (error) {
      console.error('Image search failed:', error);
      alert(`搜索失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [referenceImage, projectId, maxResults, similarityThreshold, onSearchResults]);

  // 执行标签搜索
  const handleTagSearch = useCallback(async () => {
    if (selectedTags.length === 0) return;

    setLoading(true);
    try {
      const response = await fetch('/api/images/search/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tags: selectedTags,
          project_id: projectId,
          match_mode: tagMatchMode,
          limit: maxResults
        })
      });

      if (!response.ok) {
        throw new Error(`搜索失败: ${response.statusText}`);
      }

      const searchResults = await response.json();
      setResults(searchResults);
      onSearchResults?.(searchResults);
    } catch (error) {
      console.error('Tag search failed:', error);
      alert(`搜索失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [selectedTags, projectId, tagMatchMode, maxResults, onSearchResults]);

  // 执行颜色搜索
  const handleColorSearch = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/images/search/color', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          color: colorQuery,
          project_id: projectId,
          tolerance: colorTolerance,
          limit: maxResults
        })
      });

      if (!response.ok) {
        throw new Error(`搜索失败: ${response.statusText}`);
      }

      const searchResults = await response.json();
      setResults(searchResults);
      onSearchResults?.(searchResults);
    } catch (error) {
      console.error('Color search failed:', error);
      alert(`搜索失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [colorQuery, projectId, colorTolerance, maxResults, onSearchResults]);

  // 处理图片文件选择
  const handleImageFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setReferenceImage(file);
      setReferenceImagePreview(URL.createObjectURL(file));
    }
  }, []);

  // 移除参考图片
  const removeReferenceImage = useCallback(() => {
    if (referenceImagePreview) {
      URL.revokeObjectURL(referenceImagePreview);
    }
    setReferenceImage(null);
    setReferenceImagePreview('');
  }, [referenceImagePreview]);

  // 添加标签
  const addTag = useCallback(() => {
    if (tagQuery.trim() && !selectedTags.includes(tagQuery.trim())) {
      setSelectedTags(prev => [...prev, tagQuery.trim()]);
      setTagQuery('');
    }
  }, [tagQuery, selectedTags]);

  // 移除标签
  const removeTag = useCallback((tag: string) => {
    setSelectedTags(prev => prev.filter(t => t !== tag));
  }, []);

  // 执行搜索
  const handleSearch = useCallback(() => {
    switch (searchMode) {
      case 'text':
        handleTextSearch();
        break;
      case 'image':
        handleImageSearch();
        break;
      case 'tags':
        handleTagSearch();
        break;
      case 'color':
        handleColorSearch();
        break;
    }
  }, [searchMode, handleTextSearch, handleImageSearch, handleTagSearch, handleColorSearch]);

  // 清空结果
  const clearResults = useCallback(() => {
    setResults([]);
    onSearchResults?.([]);
  }, [onSearchResults]);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 搜索模式选择 */}
      <Card padding="md">
        <div className="flex flex-wrap gap-2 mb-4">
          {[
            { mode: 'text' as const, icon: Search, label: '文本搜索' },
            { mode: 'image' as const, icon: ImageIcon, label: '相似图片' },
            { mode: 'tags' as const, icon: Tag, label: '标签搜索' },
            { mode: 'color' as const, icon: Palette, label: '颜色搜索' }
          ].map(({ mode, icon: Icon, label }) => (
            <button
              key={mode}
              onClick={() => setSearchMode(mode)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${searchMode === mode
                  ? 'bg-amber-500 text-black'
                  : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700 hover:text-white'
                }
              `}
            >
              <Icon size={16} />
              {label}
            </button>
          ))}
        </div>

        {/* 搜索输入区域 */}
        <div className="space-y-4">
          {searchMode === 'text' && (
            <div className="flex gap-2">
              <Input
                placeholder="描述你要找的图片..."
                value={textQuery}
                onChange={(e) => setTextQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleTextSearch()}
                leftIcon={Search}
              />
              <Button
                variant="primary"
                onClick={handleTextSearch}
                loading={loading}
                disabled={!textQuery.trim()}
              >
                搜索
              </Button>
            </div>
          )}

          {searchMode === 'image' && (
            <div className="space-y-4">
              {!referenceImage ? (
                <div
                  className="border-2 border-dashed border-zinc-700 rounded-lg p-8 text-center cursor-pointer hover:border-zinc-600 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload size={32} className="mx-auto text-zinc-500 mb-2" />
                  <p className="text-zinc-400">点击上传参考图片</p>
                  <p className="text-xs text-zinc-500 mt-1">支持 JPG, PNG, WebP, GIF</p>
                </div>
              ) : (
                <div className="relative inline-block">
                  <img
                    src={referenceImagePreview}
                    alt="参考图片"
                    className="max-w-xs max-h-48 rounded-lg border border-zinc-700"
                  />
                  <button
                    onClick={removeReferenceImage}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white hover:bg-red-600"
                  >
                    <X size={14} />
                  </button>
                </div>
              )}
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageFileSelect}
                className="hidden"
              />
              
              <Button
                variant="primary"
                onClick={handleImageSearch}
                loading={loading}
                disabled={!referenceImage}
                icon={Search}
              >
                查找相似图片
              </Button>
            </div>
          )}

          {searchMode === 'tags' && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="输入标签..."
                  value={tagQuery}
                  onChange={(e) => setTagQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addTag()}
                  leftIcon={Tag}
                />
                <Button
                  variant="secondary"
                  onClick={addTag}
                  disabled={!tagQuery.trim()}
                >
                  添加
                </Button>
              </div>

              {selectedTags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {selectedTags.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-amber-500/20 text-amber-400 rounded-full text-sm"
                    >
                      {tag}
                      <button
                        onClick={() => removeTag(tag)}
                        className="hover:text-amber-300"
                      >
                        <X size={12} />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-400">匹配模式:</span>
                  <select
                    value={tagMatchMode}
                    onChange={(e) => setTagMatchMode(e.target.value as 'any' | 'all')}
                    className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-white"
                  >
                    <option value="any">任意匹配</option>
                    <option value="all">全部匹配</option>
                  </select>
                </div>

                <Button
                  variant="primary"
                  onClick={handleTagSearch}
                  loading={loading}
                  disabled={selectedTags.length === 0}
                  icon={Search}
                >
                  搜索
                </Button>
              </div>
            </div>
          )}

          {searchMode === 'color' && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-400">颜色:</span>
                  <input
                    type="color"
                    value={colorQuery}
                    onChange={(e) => setColorQuery(e.target.value)}
                    className="w-12 h-8 rounded border border-zinc-700 bg-transparent cursor-pointer"
                  />
                  <Input
                    value={colorQuery}
                    onChange={(e) => setColorQuery(e.target.value)}
                    placeholder="#3b82f6"
                    className="w-24"
                    size="sm"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-400">容差:</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={colorTolerance}
                    onChange={(e) => setColorTolerance(parseFloat(e.target.value))}
                    className="w-20"
                  />
                  <span className="text-sm text-zinc-300 w-8">{colorTolerance}</span>
                </div>
              </div>

              <Button
                variant="primary"
                onClick={handleColorSearch}
                loading={loading}
                icon={Search}
              >
                搜索
              </Button>
            </div>
          )}
        </div>

        {/* 高级选项 */}
        <div className="mt-4 pt-4 border-t border-zinc-800">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-300"
          >
            <SlidersHorizontal size={16} />
            高级选项
          </button>

          {showAdvanced && (
            <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-zinc-400 mb-1">相似度阈值</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={similarityThreshold}
                  onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                  className="w-full"
                />
                <span className="text-xs text-zinc-500">{similarityThreshold}</span>
              </div>

              <div>
                <label className="block text-xs text-zinc-400 mb-1">最大结果数</label>
                <select
                  value={maxResults}
                  onChange={(e) => setMaxResults(parseInt(e.target.value))}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm text-white"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* 搜索结果 */}
      {results.length > 0 && (
        <Card title={`搜索结果 (${results.length})`} padding="md">
          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-zinc-400">
              找到 {results.length} 个相关图片
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearResults}
              icon={X}
            >
              清空结果
            </Button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {results.map((result) => (
              <div
                key={result.id}
                className="group cursor-pointer"
                onClick={() => onResultSelect?.(result)}
              >
                <div className="aspect-square rounded-lg overflow-hidden bg-zinc-800 border border-zinc-700 hover:border-amber-500/50 transition-colors">
                  <img
                    src={result.thumbnail_url || result.original_url}
                    alt={result.filename}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                  
                  {/* 相似度评分 */}
                  <div className="absolute top-2 left-2">
                    <span className="px-2 py-1 bg-black/70 text-white text-xs rounded">
                      {Math.round(result.similarity_score * 100)}%
                    </span>
                  </div>
                </div>

                <div className="mt-2">
                  <p className="text-sm text-white truncate" title={result.filename}>
                    {result.filename}
                  </p>
                  <p className="text-xs text-zinc-400 truncate" title={result.match_reason}>
                    {result.match_reason}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 加载状态 */}
      {loading && (
        <Card padding="md">
          <div className="flex items-center justify-center py-8">
            <Loader2 size={24} className="animate-spin text-amber-500 mr-3" />
            <span className="text-zinc-400">搜索中...</span>
          </div>
        </Card>
      )}
    </div>
  );
};

export default ImageSearch;