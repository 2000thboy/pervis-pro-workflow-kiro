import React, { useState, useCallback, useEffect } from 'react';
import { 
  Search, 
  Sliders, 
  Eye, 
  Mic, 
  FileText, 
  Settings,
  Play,
  Pause,
  Volume2,
  Image as ImageIcon,
  Video,
  Star,
  Filter,
  RefreshCw,
  Info,
  Zap
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Card } from '../ui/Card';

// 搜索结果类型
export interface MultimodalSearchResult {
  id: string;
  type: 'video' | 'image';
  filename: string;
  thumbnail_url?: string;
  proxy_url?: string;
  original_url: string;
  similarity_score: number;
  match_reason: string;
  match_details?: Record<string, any>;
  metadata?: {
    match_modes?: string[];
    duration?: number;
    width?: number;
    height?: number;
    file_size?: number;
    type: string;
  };
  tags?: Record<string, string[]>;
  color_palette?: string[];
}

// 搜索配置
export interface SearchConfig {
  search_modes: string[];
  weights: Record<string, number>;
  fuzziness: number;
  limit: number;
}

// 组件属性
export interface MultimodalSearchPanelProps {
  projectId?: string;
  beatId?: string;
  onResultSelect?: (result: MultimodalSearchResult) => void;
  onResultsChange?: (results: MultimodalSearchResult[]) => void;
  className?: string;
}

export const MultimodalSearchPanel: React.FC<MultimodalSearchPanelProps> = ({
  projectId,
  beatId,
  onResultSelect,
  onResultsChange,
  className = ''
}) => {
  // 状态管理
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MultimodalSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // 搜索配置
  const [searchConfig, setSearchConfig] = useState<SearchConfig>({
    search_modes: ['semantic', 'transcription', 'visual'],
    weights: {
      semantic: 0.4,
      transcription: 0.3,
      visual: 0.3
    },
    fuzziness: 0.7,
    limit: 20
  });

  // 模型信息
  const [modelInfo, setModelInfo] = useState<any>(null);

  // 加载模型信息
  useEffect(() => {
    loadModelInfo();
  }, []);

  const loadModelInfo = async () => {
    try {
      const response = await fetch('/api/multimodal/model/info');
      if (response.ok) {
        const data = await response.json();
        setModelInfo(data);
      }
    } catch (error) {
      console.error('Failed to load model info:', error);
    }
  };

  // 执行多模态搜索
  const performSearch = useCallback(async () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const searchPayload = {
        query: query.trim(),
        beat_id: beatId,
        search_modes: searchConfig.search_modes,
        weights: searchConfig.weights,
        fuzziness: searchConfig.fuzziness,
        limit: searchConfig.limit
      };

      const response = await fetch('/api/multimodal/search', {
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
      
      if (data.status === 'success') {
        setResults(data.results || []);
        onResultsChange?.(data.results || []);
      } else {
        throw new Error(data.message || '搜索失败');
      }

    } catch (err) {
      console.error('Multimodal search failed:', err);
      setError(`搜索失败: ${err}`);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, beatId, searchConfig, onResultsChange]);

  // 处理搜索模式切换
  const handleSearchModeToggle = (mode: string) => {
    setSearchConfig(prev => ({
      ...prev,
      search_modes: prev.search_modes.includes(mode)
        ? prev.search_modes.filter(m => m !== mode)
        : [...prev.search_modes, mode]
    }));
  };

  // 处理权重调整
  const handleWeightChange = (mode: string, weight: number) => {
    setSearchConfig(prev => ({
      ...prev,
      weights: {
        ...prev.weights,
        [mode]: weight
      }
    }));
  };

  // 处理结果选择
  const handleResultSelect = (result: MultimodalSearchResult) => {
    onResultSelect?.(result);
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

  // 格式化时长
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 渲染搜索模式选择器
  const renderSearchModeSelector = () => (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-white">搜索模式</h4>
      <div className="space-y-2">
        {[
          { key: 'semantic', label: '语义搜索', icon: FileText, description: '基于内容语义理解' },
          { key: 'transcription', label: '音频转录', icon: Mic, description: '搜索语音和对话内容' },
          { key: 'visual', label: '视觉分析', icon: Eye, description: '基于画面和视觉特征' }
        ].map(mode => (
          <div key={mode.key} className="flex items-center justify-between p-3 bg-zinc-800/30 rounded-lg">
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant={searchConfig.search_modes.includes(mode.key) ? 'primary' : 'ghost'}
                onClick={() => handleSearchModeToggle(mode.key)}
                icon={mode.icon}
              >
                {mode.label}
              </Button>
              <span className="text-xs text-zinc-400">{mode.description}</span>
            </div>
            
            {searchConfig.search_modes.includes(mode.key) && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-400">权重:</span>
                <input
                  type="range"
                  min="0.1"
                  max="0.8"
                  step="0.1"
                  value={searchConfig.weights[mode.key] || 0.3}
                  onChange={(e) => handleWeightChange(mode.key, parseFloat(e.target.value))}
                  className="w-16"
                />
                <span className="text-xs text-zinc-300 w-8">
                  {((searchConfig.weights[mode.key] || 0.3) * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  // 渲染搜索结果
  const renderSearchResults = () => {
    if (loading) {
      return (
        <div className="text-center py-8">
          <div className="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full mx-auto mb-2" />
          <p className="text-zinc-400">多模态搜索中...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="text-center py-8">
          <p className="text-red-400 mb-2">{error}</p>
          <Button variant="ghost" onClick={performSearch}>
            重试
          </Button>
        </div>
      );
    }

    if (results.length === 0 && query) {
      return (
        <div className="text-center py-8">
          <Search size={48} className="mx-auto mb-3 opacity-50 text-zinc-500" />
          <p className="text-zinc-400">没有找到匹配的结果</p>
          <p className="text-xs text-zinc-500 mt-1">尝试调整搜索模式或降低匹配精度</p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {results.map((result, index) => (
          <Card
            key={result.id}
            variant="elevated"
            hover
            onClick={() => handleResultSelect(result)}
            className="cursor-pointer group"
          >
            {/* 缩略图区域 */}
            <div className="relative aspect-video bg-zinc-800 rounded-lg overflow-hidden mb-3">
              {result.thumbnail_url ? (
                <img
                  src={result.thumbnail_url}
                  alt={result.filename}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  {result.type === 'video' ? (
                    <Video size={32} className="text-zinc-500" />
                  ) : (
                    <ImageIcon size={32} className="text-zinc-500" />
                  )}
                </div>
              )}
              
              {/* 类型和相似度指示器 */}
              <div className="absolute top-2 left-2 right-2 flex justify-between">
                <div className="flex items-center gap-1 px-2 py-1 bg-black/60 backdrop-blur-sm rounded-md text-xs text-white">
                  {result.type === 'video' ? (
                    <>
                      <Video size={12} />
                      {result.metadata?.duration && formatDuration(result.metadata.duration)}
                    </>
                  ) : (
                    <>
                      <ImageIcon size={12} />
                      {result.metadata?.width && result.metadata?.height && 
                        `${result.metadata.width}×${result.metadata.height}`}
                    </>
                  )}
                </div>
                
                <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/80 backdrop-blur-sm rounded-md text-xs text-black font-medium">
                  <Star size={12} />
                  {(result.similarity_score * 100).toFixed(0)}%
                </div>
              </div>
              
              {/* 匹配模式指示器 */}
              {result.metadata?.match_modes && (
                <div className="absolute bottom-2 left-2 flex gap-1">
                  {result.metadata.match_modes.map((mode: string) => (
                    <div
                      key={mode}
                      className="w-2 h-2 rounded-full"
                      style={{
                        backgroundColor: mode === 'semantic' ? '#10b981' : 
                                       mode === 'transcription' ? '#3b82f6' : 
                                       mode === 'visual' ? '#f59e0b' : '#6b7280'
                      }}
                      title={`${mode} 匹配`}
                    />
                  ))}
                </div>
              )}
              
              {/* 悬停操作 */}
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <Button size="sm" variant="secondary" icon={Eye}>
                  预览
                </Button>
                {result.proxy_url && (
                  <Button size="sm" variant="secondary" icon={Play}>
                    播放
                  </Button>
                )}
              </div>
            </div>
            
            {/* 结果信息 */}
            <div className="space-y-2">
              <h4 className="font-medium text-white truncate" title={result.filename}>
                {result.filename}
              </h4>
              
              {/* 匹配理由 */}
              <p className="text-xs text-amber-400 line-clamp-2">
                {result.match_reason}
              </p>
              
              {/* 标签 */}
              {result.tags && (
                <div className="flex flex-wrap gap-1">
                  {Object.entries(result.tags).slice(0, 2).map(([category, tags]) =>
                    tags.slice(0, 2).map((tag, tagIndex) => (
                      <span
                        key={`${category}-${tagIndex}`}
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
                <span>#{index + 1}</span>
                {result.metadata?.file_size && (
                  <span>{formatFileSize(result.metadata.file_size)}</span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 搜索输入区域 */}
      <Card title="多模态智能搜索" variant="elevated">
        <div className="space-y-4">
          {/* 主搜索输入 */}
          <div className="flex items-center gap-3">
            <div className="flex-1">
              <Input
                placeholder="描述你想要的内容、画面、声音或情绪..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && performSearch()}
                leftIcon={Search}
              />
            </div>
            
            <Button 
              onClick={performSearch} 
              loading={loading}
              icon={Zap}
            >
              搜索
            </Button>
            
            <Button
              variant="ghost"
              icon={Settings}
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              高级
            </Button>
          </div>
          
          {/* 快速搜索建议 */}
          <div className="flex flex-wrap gap-2">
            {[
              '城市夜景',
              '紧张追逐',
              '温馨对话',
              '爆炸场面',
              '自然风光',
              '人物特写'
            ].map(suggestion => (
              <Button
                key={suggestion}
                size="sm"
                variant="ghost"
                onClick={() => {
                  setQuery(suggestion);
                  // 自动搜索
                  setTimeout(() => performSearch(), 100);
                }}
                className="text-xs"
              >
                {suggestion}
              </Button>
            ))}
          </div>
          
          {/* 高级配置面板 */}
          {showAdvanced && (
            <div className="p-4 bg-zinc-800/30 rounded-lg space-y-4">
              {renderSearchModeSelector()}
              
              {/* 全局配置 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">匹配精度</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0.3"
                      max="1.0"
                      step="0.1"
                      value={searchConfig.fuzziness}
                      onChange={(e) => setSearchConfig(prev => ({
                        ...prev,
                        fuzziness: parseFloat(e.target.value)
                      }))}
                      className="flex-1"
                    />
                    <span className="text-sm text-zinc-300 w-12">
                      {(searchConfig.fuzziness * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">结果数量</label>
                  <select
                    value={searchConfig.limit}
                    onChange={(e) => setSearchConfig(prev => ({
                      ...prev,
                      limit: parseInt(e.target.value)
                    }))}
                    className="w-full px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value={10}>10个结果</option>
                    <option value={20}>20个结果</option>
                    <option value={50}>50个结果</option>
                    <option value={100}>100个结果</option>
                  </select>
                </div>
              </div>
              
              {/* 模型信息 */}
              {modelInfo && (
                <div className="p-3 bg-zinc-700/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <Info size={16} className="text-amber-400" />
                    <span className="text-sm font-medium text-white">模型信息</span>
                  </div>
                  <div className="text-xs text-zinc-400 space-y-1">
                    <p>支持的搜索模式: {modelInfo.supported_search_modes?.join(', ')}</p>
                    <p>视觉分析: {modelInfo.multimodal_capabilities?.visual_analysis?.available ? '可用' : '不可用'}</p>
                    <p>音频转录: {modelInfo.multimodal_capabilities?.audio_transcription?.available ? '可用' : '不可用'}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
      
      {/* 搜索结果区域 */}
      {(results.length > 0 || loading || error) && (
        <Card 
          title={`搜索结果 ${results.length > 0 ? `(${results.length})` : ''}`}
          variant="elevated"
        >
          {renderSearchResults()}
        </Card>
      )}
    </div>
  );
};

export default MultimodalSearchPanel;