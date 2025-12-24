import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Play, 
  Pause, 
  Clock, 
  Target, 
  Zap, 
  Image as ImageIcon,
  Video,
  Search,
  Filter,
  Grid,
  List,
  Eye,
  Download
} from 'lucide-react';
import { useSyncService } from '../../services/syncService';
import { Button } from '../ui/Button';

interface Beat {
  id: string;
  order_index: number;
  content: string;
  duration: number;
  emotion_tags: string[];
  scene_tags: string[];
  action_tags: string[];
}

interface MediaRecommendation {
  id: string;
  type: 'video' | 'image';
  filename: string;
  thumbnail_url?: string;
  proxy_url?: string;
  original_url: string;
  similarity_score: number;
  match_reason: string;
  tags?: Record<string, string[]>;
  metadata?: Record<string, any>;
}

interface EnhancedBeatBoardProps {
  projectId: string;
  beats: Beat[];
  onBeatSelect?: (beatIndex: number) => void;
  enableImageRecommendations?: boolean;
  className?: string;
}

type MediaFilter = 'all' | 'video' | 'image';
type RecommendationView = 'grid' | 'list';

const EnhancedBeatBoard: React.FC<EnhancedBeatBoardProps> = ({
  projectId,
  beats,
  onBeatSelect,
  enableImageRecommendations = true,
  className = ''
}) => {
  const {
    syncState,
    isSyncEnabled,
    updatePlayState,
    updateDuration,
    seekTo,
    formatTime,
    calculateBeatPosition,
    findBeatAtTime
  } = useSyncService('beatboard');
  
  const [localCurrentBeat, setLocalCurrentBeat] = useState<number>(0);
  const [localIsPlaying, setLocalIsPlaying] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<MediaRecommendation[]>([]);
  const [loadingRecommendations, setLoadingRecommendations] = useState<boolean>(false);
  const [mediaFilter, setMediaFilter] = useState<MediaFilter>('all');
  const [recommendationView, setRecommendationView] = useState<RecommendationView>('grid');
  const [showRecommendations, setShowRecommendations] = useState<boolean>(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // 计算总时长
  const totalDuration = beats.reduce((sum, beat) => sum + (beat.duration || 0), 0);
  
  // 同步总时长
  useEffect(() => {
    if (isSyncEnabled && totalDuration > 0) {
      updateDuration(totalDuration);
    }
  }, [totalDuration, isSyncEnabled, updateDuration]);
  
  // 根据同步时间查找当前Beat
  const currentBeatInfo = isSyncEnabled 
    ? findBeatAtTime(syncState.currentTime, beats)
    : { index: localCurrentBeat, beat: beats[localCurrentBeat], progress: 0 };
  
  const currentBeatIndex = currentBeatInfo?.index ?? 0;
  const currentBeat = currentBeatInfo?.beat;
  const beatProgress = currentBeatInfo?.progress ?? 0;

  // 获取媒体推荐
  const fetchRecommendations = useCallback(async (beat: Beat) => {
    if (!beat || !enableImageRecommendations) return;

    setLoadingRecommendations(true);
    try {
      // 构建搜索查询
      const searchQuery = [
        beat.content,
        ...beat.emotion_tags,
        ...beat.scene_tags,
        ...beat.action_tags
      ].join(' ');

      // 使用BeatBoard专用的媒体搜索API
      const response = await fetch('/api/multimodal/search/beatboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: searchQuery,
          beat_id: beat.id,
          search_modes: ['semantic', 'transcription', 'visual'],
          weights: { semantic: 0.4, transcription: 0.3, visual: 0.3 },
          limit: 12
        })
      });

      const mediaRecommendations: MediaRecommendation[] = [];

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success' && data.results) {
          data.results.forEach((result: any) => {
            mediaRecommendations.push({
              id: result.id,
              type: result.type,
              filename: result.filename,
              thumbnail_url: result.thumbnail_url,
              proxy_url: result.proxy_url,
              original_url: result.original_url,
              similarity_score: result.similarity_score,
              match_reason: result.match_reason,
              tags: result.tags,
              metadata: result.metadata
            });
          });
        }
      }
      
      setRecommendations(mediaRecommendations);
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      setRecommendations([]);
    } finally {
      setLoadingRecommendations(false);
    }
  }, [projectId, enableImageRecommendations]);

  // 当前Beat变化时获取推荐
  useEffect(() => {
    if (currentBeat) {
      fetchRecommendations(currentBeat);
    }
  }, [currentBeat, fetchRecommendations]);
  
  // 播放控制
  const handlePlayPause = () => {
    const newPlayState = isSyncEnabled ? !syncState.isPlaying : !localIsPlaying;
    
    if (isSyncEnabled) {
      updatePlayState(newPlayState);
    } else {
      setLocalIsPlaying(newPlayState);
    }
  };
  
  // 跳转到指定Beat
  const handleBeatClick = (beatIndex: number) => {
    const beatPosition = calculateBeatPosition(beatIndex, beats);
    
    if (isSyncEnabled) {
      seekTo(beatPosition);
    } else {
      setLocalCurrentBeat(beatIndex);
    }
    
    onBeatSelect?.(beatIndex);
  };
  
  // 本地播放逻辑（非同步模式）
  useEffect(() => {
    if (!isSyncEnabled && localIsPlaying) {
      intervalRef.current = setInterval(() => {
        setLocalCurrentBeat(prev => {
          const nextBeat = prev + 1;
          if (nextBeat >= beats.length) {
            setLocalIsPlaying(false);
            return 0;
          }
          return nextBeat;
        });
      }, (beats[localCurrentBeat]?.duration || 3) * 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [localIsPlaying, localCurrentBeat, beats, isSyncEnabled]);

  // 过滤推荐
  const filteredRecommendations = recommendations.filter(rec => {
    if (mediaFilter === 'all') return true;
    return rec.type === mediaFilter;
  });

  // 处理媒体预览
  const handleMediaPreview = (media: MediaRecommendation) => {
    if (media.type === 'image') {
      // 打开图片预览
      window.open(media.original_url, '_blank');
    } else {
      // 打开视频预览
      window.open(media.proxy_url || media.original_url, '_blank');
    }
  };

  // 处理媒体下载
  const handleMediaDownload = (media: MediaRecommendation) => {
    const link = document.createElement('a');
    link.href = media.original_url;
    link.download = media.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };
  
  // 渲染Beat卡片
  const renderBeat = (beat: Beat, index: number) => {
    const isActive = index === currentBeatIndex;
    const beatStartTime = calculateBeatPosition(index, beats);
    
    return (
      <div
        key={beat.id}
        className={`relative p-4 rounded-lg border-2 cursor-pointer transition-all ${
          isActive
            ? 'border-amber-400 bg-amber-400/10 shadow-lg shadow-amber-400/20'
            : 'border-zinc-600 bg-zinc-800 hover:border-zinc-500'
        }`}
        onClick={() => handleBeatClick(index)}
      >
        {/* Beat头部 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
              isActive ? 'bg-amber-400 text-black' : 'bg-zinc-600 text-white'
            }`}>
              {index + 1}
            </div>
            <div className="text-xs text-zinc-400 font-mono">
              {formatTime(beatStartTime)}
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Clock size={12} className="text-zinc-400" />
            <span className="text-xs text-zinc-400">
              {formatTime(beat.duration)}
            </span>
          </div>
        </div>
        
        {/* Beat内容 */}
        <div className="mb-3">
          <p className="text-sm text-white leading-relaxed">
            {beat.content}
          </p>
        </div>
        
        {/* 标签 */}
        <div className="space-y-2">
          {beat.emotion_tags && beat.emotion_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {beat.emotion_tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-2 py-1 text-xs bg-red-500/20 text-red-300 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          
          {beat.scene_tags && beat.scene_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {beat.scene_tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-2 py-1 text-xs bg-blue-500/20 text-blue-300 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
        
        {/* 进度条（仅在播放时显示） */}
        {isActive && (isSyncEnabled ? syncState.isPlaying : localIsPlaying) && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-zinc-700 rounded-b-lg overflow-hidden">
            <div 
              className="h-full bg-amber-400 transition-all duration-100"
              style={{ width: `${beatProgress * 100}%` }}
            />
          </div>
        )}
        
        {/* 同步指示器 */}
        {isActive && isSyncEnabled && (
          <div className="absolute top-2 right-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          </div>
        )}
      </div>
    );
  };

  // 处理拖拽开始
  const handleDragStart = (event: React.DragEvent, media: MediaRecommendation) => {
    // 设置拖拽数据
    const dragData = {
      type: 'media-recommendation',
      mediaId: media.id,
      mediaType: media.type,
      filename: media.filename,
      originalUrl: media.original_url,
      thumbnailUrl: media.thumbnail_url,
      proxyUrl: media.proxy_url,
      similarityScore: media.similarity_score,
      matchReason: media.match_reason,
      tags: media.tags,
      metadata: media.metadata
    };
    
    event.dataTransfer.setData('application/json', JSON.stringify(dragData));
    event.dataTransfer.effectAllowed = 'copy';
    
    // 设置拖拽图像
    if (media.thumbnail_url) {
      const img = new Image();
      img.src = media.thumbnail_url;
      event.dataTransfer.setDragImage(img, 50, 50);
    }
  };

  // 渲染媒体推荐
  const renderMediaRecommendation = (media: MediaRecommendation) => {
    return (
      <div
        key={media.id}
        className="group relative bg-zinc-800 rounded-lg overflow-hidden border border-zinc-700 hover:border-zinc-600 transition-colors cursor-grab active:cursor-grabbing"
        draggable={true}
        onDragStart={(e) => handleDragStart(e, media)}
      >
        {/* 媒体缩略图 */}
        <div className="aspect-video bg-zinc-900 relative overflow-hidden">
          <img
            src={media.thumbnail_url || media.original_url}
            alt={media.filename}
            className="w-full h-full object-cover"
            loading="lazy"
          />
          
          {/* 媒体类型指示器 */}
          <div className="absolute top-2 left-2">
            <div className={`
              px-2 py-1 rounded text-xs font-medium
              ${media.type === 'video' 
                ? 'bg-blue-500/80 text-white' 
                : 'bg-green-500/80 text-white'
              }
            `}>
              {media.type === 'video' ? <Video size={12} /> : <ImageIcon size={12} />}
            </div>
          </div>

          {/* 相似度评分 */}
          <div className="absolute top-2 right-2">
            <div className="px-2 py-1 bg-black/70 text-white text-xs rounded">
              {Math.round(media.similarity_score * 100)}%
            </div>
          </div>

          {/* 悬停操作 */}
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleMediaPreview(media)}
              className="bg-black/50 hover:bg-black/70"
            >
              <Eye size={14} />
              预览
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleMediaDownload(media)}
              className="bg-black/50 hover:bg-black/70"
            >
              <Download size={14} />
              下载
            </Button>
          </div>
        </div>

        {/* 媒体信息 */}
        <div className="p-3">
          <h4 className="text-sm font-medium text-white truncate mb-1" title={media.filename}>
            {media.filename}
          </h4>
          <p className="text-xs text-zinc-400 line-clamp-2" title={media.match_reason}>
            {media.match_reason}
          </p>
          
          {/* 标签 */}
          {media.tags && Object.keys(media.tags).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {Object.entries(media.tags).slice(0, 2).map(([category, tags]) => (
                tags.slice(0, 2).map((tag, i) => (
                  <span
                    key={`${category}-${i}`}
                    className="px-1 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded"
                  >
                    {tag}
                  </span>
                ))
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };
  
  return (
    <div className={`bg-zinc-900 rounded-lg ${className}`}>
      {/* 头部控制 */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-700">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-white">Enhanced BeatBoard</h3>
          
          {isSyncEnabled && (
            <div className="flex items-center gap-2 px-2 py-1 bg-amber-500/20 rounded text-amber-400 text-xs">
              <Zap size={12} />
              <span>同步模式</span>
            </div>
          )}

          {enableImageRecommendations && (
            <div className="flex items-center gap-2 px-2 py-1 bg-green-500/20 rounded text-green-400 text-xs">
              <ImageIcon size={12} />
              <span>图片推荐</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          {/* 当前Beat信息 */}
          <div className="text-sm text-zinc-400">
            Beat {currentBeatIndex + 1} / {beats.length}
          </div>
          
          {/* 播放控制 */}
          <button
            onClick={handlePlayPause}
            className="flex items-center justify-center w-10 h-10 bg-amber-500 hover:bg-amber-600 text-white rounded-full transition-colors"
          >
            {(isSyncEnabled ? syncState.isPlaying : localIsPlaying) ? (
              <Pause size={18} />
            ) : (
              <Play size={18} />
            )}
          </button>
        </div>
      </div>

      <div className="flex">
        {/* Beat网格 */}
        <div className="flex-1 p-4">
          {beats.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {beats.map((beat, index) => renderBeat(beat, index))}
            </div>
          ) : (
            <div className="text-center py-12 text-zinc-400">
              <Target size={48} className="mx-auto mb-4 opacity-50" />
              <p>还没有创建Beat</p>
              <p className="text-sm mt-1">开始创建您的故事节拍</p>
            </div>
          )}
        </div>

        {/* 媒体推荐面板 */}
        {enableImageRecommendations && showRecommendations && (
          <div className="w-80 border-l border-zinc-700 bg-zinc-900/50">
            <div className="p-4 border-b border-zinc-700">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-semibold text-white">媒体推荐</h4>
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={() => setShowRecommendations(false)}
                >
                  隐藏
                </Button>
              </div>

              {/* 媒体类型过滤 */}
              <div className="flex gap-1 mb-3">
                {[
                  { key: 'all', label: '全部', icon: Filter },
                  { key: 'video', label: '视频', icon: Video },
                  { key: 'image', label: '图片', icon: ImageIcon }
                ].map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setMediaFilter(key as MediaFilter)}
                    className={`
                      flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors
                      ${mediaFilter === key 
                        ? 'bg-amber-500 text-black' 
                        : 'bg-zinc-800 text-zinc-400 hover:text-white'
                      }
                    `}
                  >
                    <Icon size={12} />
                    {label}
                  </button>
                ))}
              </div>

              {/* 视图切换 */}
              <div className="flex gap-1">
                <button
                  onClick={() => setRecommendationView('grid')}
                  className={`
                    p-1 rounded transition-colors
                    ${recommendationView === 'grid' 
                      ? 'bg-amber-500 text-black' 
                      : 'bg-zinc-800 text-zinc-400 hover:text-white'
                    }
                  `}
                >
                  <Grid size={14} />
                </button>
                <button
                  onClick={() => setRecommendationView('list')}
                  className={`
                    p-1 rounded transition-colors
                    ${recommendationView === 'list' 
                      ? 'bg-amber-500 text-black' 
                      : 'bg-zinc-800 text-zinc-400 hover:text-white'
                    }
                  `}
                >
                  <List size={14} />
                </button>
              </div>
            </div>

            {/* 推荐内容 */}
            <div className="p-4 max-h-96 overflow-y-auto">
              {loadingRecommendations ? (
                <div className="text-center py-8">
                  <div className="animate-spin w-6 h-6 border-2 border-amber-500 border-t-transparent rounded-full mx-auto mb-2" />
                  <p className="text-xs text-zinc-400">加载推荐中...</p>
                </div>
              ) : filteredRecommendations.length > 0 ? (
                <div className={
                  recommendationView === 'grid' 
                    ? 'grid grid-cols-1 gap-3'
                    : 'space-y-2'
                }>
                  {filteredRecommendations.map(renderMediaRecommendation)}
                </div>
              ) : (
                <div className="text-center py-8 text-zinc-400">
                  <Search size={32} className="mx-auto mb-2 opacity-50" />
                  <p className="text-xs">暂无推荐内容</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* 底部状态栏 */}
      <div className="border-t border-zinc-700 p-3 bg-zinc-800/50">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-4">
            <span className="text-zinc-400">
              总时长: {formatTime(totalDuration)}
            </span>
            {isSyncEnabled && (
              <span className="text-zinc-400">
                当前时间: {formatTime(syncState.currentTime)}
              </span>
            )}
            {enableImageRecommendations && (
              <span className="text-zinc-400">
                推荐: {filteredRecommendations.length} 个媒体
              </span>
            )}
          </div>
          
          {currentBeat && (
            <div className="text-amber-400 max-w-xs truncate">
              {currentBeat.content}
            </div>
          )}

          {/* 推荐面板切换 */}
          {enableImageRecommendations && !showRecommendations && (
            <Button
              variant="ghost"
              size="xs"
              onClick={() => setShowRecommendations(true)}
            >
              <ImageIcon size={12} />
              显示推荐
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedBeatBoard;