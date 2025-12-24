import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  Play, 
  Image as ImageIcon,
  Video,
  Clock,
  Star,
  Tag,
  Sliders,
  X,
  Check,
  Eye,
  Download
} from 'lucide-react';
import { Modal, ModalContent, ModalFooter } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';

// 素材类型定义
export interface Asset {
  id: string;
  type: 'video' | 'image';
  filename: string;
  thumbnail_url?: string;
  proxy_url?: string;
  original_url: string;
  duration?: number;
  width?: number;
  height?: number;
  file_size: number;
  tags?: Record<string, string[]>;
  metadata?: Record<string, any>;
  created_at: string;
}

// 搜索结果类型
export interface SearchResult extends Asset {
  similarity_score?: number;
  match_reason?: string;
  segments?: Array<{
    start_time: number;
    end_time: number;
    description: string;
    tags: Record<string, string[]>;
  }>;
}

// 组件属性
export interface AssetPickerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (asset: Asset | SearchResult) => void;
  onMultiSelect?: (assets: (Asset | SearchResult)[]) => void;
  title?: string;
  subtitle?: string;
  projectId?: string;
  beatContent?: string;
  beatTags?: {
    emotion_tags?: string[];
    scene_tags?: string[];
    action_tags?: string[];
    cinematography_tags?: string[];
  };
  allowMultiSelect?: boolean;
  assetTypes?: ('video' | 'image')[];
  className?: string;
}

type ViewMode = 'grid' | 'list';
type SearchMode = 'semantic' | 'keyword' | 'tags';

export const AssetPickerModal: React.FC<AssetPickerModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  onMultiSelect,
  title = '选择素材',
  subtitle,
  projectId,
  beatContent,
  beatTags,
  allowMultiSelect = false,
  assetTypes = ['video', 'image'],
  className = ''
}) => {
  // 状态管理
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchMode, setSearchMode] = useState<SearchMode>('semantic');
  const [searchQuery, setSearchQuery] = useState('');
  const [fuzziness, setFuzziness] = useState(0.7);
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());
  const [assets, setAssets] = useState<Asset[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  
  // 筛选状态
  const [filters, setFilters] = useState({
    assetType: 'all' as 'all' | 'video' | 'image',
    minDuration: 0,
    maxDuration: 300,
    tags: [] as string[],
    dateRange: 'all' as 'all' | 'week' | 'month' | 'year'
  });

  // 初始化时加载素材
  useEffect(() => {
    if (isOpen) {
      loadAssets();
      // 如果有Beat内容，自动进行语义搜索
      if (beatContent && beatTags) {
        performSemanticSearch();
      }
    }
  }, [isOpen, projectId]);

  // 加载项目素材
  const loadAssets = useCallback(async () => {
    if (!projectId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/assets/project/${projectId}`);
      if (!response.ok) {
        throw new Error(`Failed to load assets: ${response.statusText}`);
      }
      
      const data = await response.json();
      setAssets(data.assets || []);
    } catch (err) {
      console.error('Failed to load assets:', err);
      setError(`加载素材失败: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // 执行语义搜索
  const performSemanticSearch = useCallback(async () => {
    if (!beatContent || !beatTags) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const searchPayload = {
        beat_content: beatContent,
        emotion_tags: beatTags.emotion_tags || [],
        scene_tags: beatTags.scene_tags || [],
        action_tags: beatTags.action_tags || [],
        cinematography_tags: beatTags.cinematography_tags || [],
        fuzziness: fuzziness,
        limit: 20
      };
      
      const response = await fetch('/api/multimodal/search/beatboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(searchPayload)
      });
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSearchResults(data.recommendations || []);
    } catch (err) {
      console.error('Semantic search failed:', err);
      setError(`语义搜索失败: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [beatContent, beatTags, fuzziness]);

  // 执行关键词搜索
  const performKeywordSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/search/keyword', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: searchQuery,
          asset_types: assetTypes,
          limit: 20
        })
      });
      
      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Keyword search failed:', err);
      setError(`关键词搜索失败: ${err}`);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, assetTypes]);

  // 处理搜索
  const handleSearch = useCallback(() => {
    switch (searchMode) {
      case 'semantic':
        performSemanticSearch();
        break;
      case 'keyword':
        performKeywordSearch();
        break;
      case 'tags':
        // TODO: 实现标签搜索
        break;
    }
  }, [searchMode, performSemanticSearch, performKeywordSearch]);

  // 处理素材选择
  const handleAssetSelect = useCallback((asset: Asset | SearchResult) => {
    if (allowMultiSelect) {
      const newSelected = new Set(selectedAssets);
      if (newSelected.has(asset.id)) {
        newSelected.delete(asset.id);
      } else {
        newSelected.add(asset.id);
      }
      setSelectedAssets(newSelected);
    } else {
      onSelect(asset);
      onClose();
    }
  }, [allowMultiSelect, selectedAssets, onSelect, onClose]);

  // 处理多选确认
  const handleMultiSelectConfirm = useCallback(() => {
    if (!onMultiSelect) return;
    
    const selectedAssetList = [...assets, ...searchResults].filter(
      asset => selectedAssets.has(asset.id)
    );
    
    onMultiSelect(selectedAssetList);
    onClose();
  }, [assets, searchResults, selectedAssets, onMultiSelect, onClose]);

  // 过滤后的素材列表
  const filteredAssets = useMemo(() => {
    const allAssets = searchResults.length > 0 ? searchResults : assets;
    
    return allAssets.filter(asset => {
      // 类型筛选
      if (filters.assetType !== 'all' && asset.type !== filters.assetType) {
        return false;
      }
      
      // 时长筛选（仅视频）
      if (asset.type === 'video' && asset.duration) {
        if (asset.duration < filters.minDuration || asset.duration > filters.maxDuration) {
          return false;
        }
      }
      
      // 标签筛选
      if (filters.tags.length > 0) {
        const assetTags = Object.values(asset.tags || {}).flat();
        const hasMatchingTag = filters.tags.some(tag => 
          assetTags.some(assetTag => 
            assetTag.toLowerCase().includes(tag.toLowerCase())
          )
        );
        if (!hasMatchingTag) return false;
      }
      
      return true;
    });
  }, [assets, searchResults, filters]);

  // 格式化时长
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  // 渲染素材卡片
  const renderAssetCard = (asset: Asset | SearchResult) => {
    const isSelected = selectedAssets.has(asset.id);
    const isSearchResult = 'similarity_score' in asset;
    
    return (
      <Card
        key={asset.id}
        variant="elevated"
        hover
        selected={isSelected}
        onClick={() => handleAssetSelect(asset)}
        className="cursor-pointer group"
      >
        {/* 缩略图区域 */}
        <div className="relative aspect-video bg-zinc-800 rounded-lg overflow-hidden mb-3">
          {asset.thumbnail_url ? (
            <img
              src={asset.thumbnail_url}
              alt={asset.filename}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              {asset.type === 'video' ? (
                <Video size={32} className="text-zinc-500" />
              ) : (
                <ImageIcon size={32} className="text-zinc-500" />
              )}
            </div>
          )}
          
          {/* 类型指示器 */}
          <div className="absolute top-2 left-2">
            <div className="flex items-center gap-1 px-2 py-1 bg-black/60 backdrop-blur-sm rounded-md text-xs text-white">
              {asset.type === 'video' ? (
                <>
                  <Video size={12} />
                  {asset.duration && formatDuration(asset.duration)}
                </>
              ) : (
                <>
                  <ImageIcon size={12} />
                  {asset.width && asset.height && `${asset.width}×${asset.height}`}
                </>
              )}
            </div>
          </div>
          
          {/* 相似度分数 */}
          {isSearchResult && asset.similarity_score && (
            <div className="absolute top-2 right-2">
              <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/80 backdrop-blur-sm rounded-md text-xs text-black font-medium">
                <Star size={12} />
                {(asset.similarity_score * 100).toFixed(0)}%
              </div>
            </div>
          )}
          
          {/* 选中指示器 */}
          {isSelected && (
            <div className="absolute inset-0 bg-amber-500/20 flex items-center justify-center">
              <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center">
                <Check size={16} className="text-black" />
              </div>
            </div>
          )}
          
          {/* 悬停操作 */}
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <Button size="sm" variant="secondary" icon={Eye}>
              预览
            </Button>
            {asset.proxy_url && (
              <Button size="sm" variant="secondary" icon={Play}>
                播放
              </Button>
            )}
          </div>
        </div>
        
        {/* 素材信息 */}
        <div className="space-y-2">
          <h4 className="font-medium text-white truncate" title={asset.filename}>
            {asset.filename}
          </h4>
          
          {/* 匹配理由 */}
          {isSearchResult && asset.match_reason && (
            <p className="text-xs text-amber-400 line-clamp-2">
              {asset.match_reason}
            </p>
          )}
          
          {/* 标签 */}
          {asset.tags && (
            <div className="flex flex-wrap gap-1">
              {Object.entries(asset.tags).slice(0, 2).map(([category, tags]) =>
                tags.slice(0, 2).map((tag, index) => (
                  <span
                    key={`${category}-${index}`}
                    className="px-2 py-1 bg-zinc-700/50 text-xs text-zinc-300 rounded-md"
                  >
                    {tag}
                  </span>
                ))
              )}
            </div>
          )}
          
          {/* 元数据 */}
          <div className="flex items-center justify-between text-xs text-zinc-500">
            <span>{formatFileSize(asset.file_size)}</span>
            <span>{new Date(asset.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </Card>
    );
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      subtitle={subtitle || `从 ${filteredAssets.length} 个素材中选择`}
      size="xl"
      className={className}
    >
      <ModalContent scrollable={false} className="p-0">
        {/* 搜索和筛选栏 */}
        <div className="p-6 border-b border-zinc-800/50 space-y-4">
          {/* 搜索模式切换 */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={searchMode === 'semantic' ? 'primary' : 'ghost'}
              onClick={() => setSearchMode('semantic')}
            >
              语义搜索
            </Button>
            <Button
              size="sm"
              variant={searchMode === 'keyword' ? 'primary' : 'ghost'}
              onClick={() => setSearchMode('keyword')}
            >
              关键词搜索
            </Button>
            <Button
              size="sm"
              variant={searchMode === 'tags' ? 'primary' : 'ghost'}
              onClick={() => setSearchMode('tags')}
            >
              标签搜索
            </Button>
          </div>
          
          {/* 搜索输入 */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Input
                placeholder={
                  searchMode === 'semantic' 
                    ? '描述你想要的画面或情绪...'
                    : searchMode === 'keyword'
                    ? '输入关键词搜索...'
                    : '输入标签搜索...'
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                leftIcon={Search}
              />
            </div>
            
            <Button onClick={handleSearch} loading={loading}>
              搜索
            </Button>
            
            <Button
              variant="ghost"
              icon={Filter}
              onClick={() => setShowFilters(!showFilters)}
            >
              筛选
            </Button>
          </div>
          
          {/* Fuzziness 控制（仅语义搜索） */}
          {searchMode === 'semantic' && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-zinc-400">匹配精度:</span>
              <div className="flex-1 max-w-xs">
                <input
                  type="range"
                  min="0.3"
                  max="1.0"
                  step="0.1"
                  value={fuzziness}
                  onChange={(e) => setFuzziness(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
              <span className="text-sm text-zinc-400 w-12">
                {(fuzziness * 100).toFixed(0)}%
              </span>
            </div>
          )}
          
          {/* 筛选面板 */}
          {showFilters && (
            <div className="p-4 bg-zinc-800/30 rounded-lg space-y-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* 素材类型 */}
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">类型</label>
                  <select
                    value={filters.assetType}
                    onChange={(e) => setFilters(prev => ({ ...prev, assetType: e.target.value as any }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value="all">全部</option>
                    <option value="video">视频</option>
                    <option value="image">图片</option>
                  </select>
                </div>
                
                {/* 时长范围 */}
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">最小时长(秒)</label>
                  <input
                    type="number"
                    value={filters.minDuration}
                    onChange={(e) => setFilters(prev => ({ ...prev, minDuration: parseInt(e.target.value) || 0 }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  />
                </div>
                
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">最大时长(秒)</label>
                  <input
                    type="number"
                    value={filters.maxDuration}
                    onChange={(e) => setFilters(prev => ({ ...prev, maxDuration: parseInt(e.target.value) || 300 }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  />
                </div>
                
                {/* 日期范围 */}
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">创建时间</label>
                  <select
                    value={filters.dateRange}
                    onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value as any }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value="all">全部</option>
                    <option value="week">最近一周</option>
                    <option value="month">最近一月</option>
                    <option value="year">最近一年</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* 视图控制 */}
        <div className="px-6 py-3 border-b border-zinc-800/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={viewMode === 'grid' ? 'primary' : 'ghost'}
              icon={Grid}
              onClick={() => setViewMode('grid')}
            >
              网格
            </Button>
            <Button
              size="sm"
              variant={viewMode === 'list' ? 'primary' : 'ghost'}
              icon={List}
              onClick={() => setViewMode('list')}
            >
              列表
            </Button>
          </div>
          
          <div className="text-sm text-zinc-400">
            {allowMultiSelect && selectedAssets.size > 0 && (
              <span>已选择 {selectedAssets.size} 个素材</span>
            )}
          </div>
        </div>
        
        {/* 素材列表 */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {error && (
            <div className="text-center py-8">
              <p className="text-red-400">{error}</p>
              <Button
                variant="ghost"
                onClick={() => {
                  setError(null);
                  loadAssets();
                }}
                className="mt-2"
              >
                重试
              </Button>
            </div>
          )}
          
          {loading && (
            <div className="text-center py-8">
              <div className="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full mx-auto mb-2" />
              <p className="text-zinc-400">加载中...</p>
            </div>
          )}
          
          {!loading && !error && filteredAssets.length === 0 && (
            <div className="text-center py-8">
              <p className="text-zinc-400">没有找到匹配的素材</p>
              <Button
                variant="ghost"
                onClick={() => {
                  setSearchQuery('');
                  setSearchResults([]);
                  loadAssets();
                }}
                className="mt-2"
              >
                显示全部素材
              </Button>
            </div>
          )}
          
          {!loading && !error && filteredAssets.length > 0 && (
            <div className={
              viewMode === 'grid'
                ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4'
                : 'space-y-3'
            }>
              {filteredAssets.map(renderAssetCard)}
            </div>
          )}
        </div>
      </ModalContent>
      
      {/* 底部操作 */}
      <ModalFooter>
        <Button variant="ghost" onClick={onClose}>
          取消
        </Button>
        
        {allowMultiSelect && selectedAssets.size > 0 && (
          <Button onClick={handleMultiSelectConfirm}>
            确认选择 ({selectedAssets.size})
          </Button>
        )}
      </ModalFooter>
    </Modal>
  );
};

export default AssetPickerModal;