/**
 * 故事板素材推荐组件
 * 解决Beat中缺乏合适素材的问题
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Upload, Search, Image, Video, Star, AlertCircle, Plus } from 'lucide-react';

interface Asset {
  id: string;
  filename: string;
  media_type: 'video' | 'image';
  thumbnail_url: string;
  preview_url?: string;
  duration?: number;
  tags: {
    scene_tags: string[];
    emotion_tags: string[];
    action_tags: string[];
    style_tags: string[];
  };
}

interface AssetRecommendation {
  asset: Asset;
  match_score: number;
  match_reason: string;
  matched_tags: string[];
}

interface Beat {
  id: string;
  content: string;
  emotion_tags: string[];
  scene_tags: string[];
  action_tags: string[];
  duration: number;
}

interface StoryboardAssetRecommendationProps {
  beat: Beat;
  onAssetSelect: (asset: Asset) => void;
  onUploadRequest: () => void;
  className?: string;
}

const StoryboardAssetRecommendation: React.FC<StoryboardAssetRecommendationProps> = ({
  beat,
  onAssetSelect,
  onUploadRequest,
  className = ''
}) => {
  const [recommendations, setRecommendations] = useState<AssetRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMediaTypes, setSelectedMediaTypes] = useState<string[]>(['video', 'image']);
  const [minMatchScore, setMinMatchScore] = useState(0.6);

  // 获取素材推荐
  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/storyboard/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          beat_id: beat.id,
          media_types: selectedMediaTypes,
          min_score: minMatchScore,
          limit: 12
        }),
      });

      if (!response.ok) {
        throw new Error('获取推荐失败');
      }

      const data = await response.json();
      setRecommendations(data.recommendations || []);

    } catch (err) {
      setError(err instanceof Error ? err.message : '未知错误');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  }, [beat.id, selectedMediaTypes, minMatchScore]);

  // Beat变化时重新获取推荐
  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  // 渲染匹配度指示器
  const renderMatchScore = (score: number) => {
    const percentage = Math.round(score * 100);
    const color = score >= 0.8 ? 'text-green-400' : score >= 0.6 ? 'text-yellow-400' : 'text-red-400';
    
    return (
      <div className={`flex items-center gap-1 ${color}`}>
        <Star size={12} fill="currentColor" />
        <span className="text-xs font-medium">{percentage}%</span>
      </div>
    );
  };

  // 渲染素材卡片
  const renderAssetCard = (recommendation: AssetRecommendation) => {
    const { asset, match_score, match_reason, matched_tags } = recommendation;
    
    return (
      <div
        key={asset.id}
        className="bg-zinc-800 rounded-lg border border-zinc-600 hover:border-amber-400 transition-all cursor-pointer group"
        onClick={() => onAssetSelect(asset)}
      >
        {/* 缩略图 */}
        <div className="relative aspect-video bg-zinc-900 rounded-t-lg overflow-hidden">
          <img
            src={asset.thumbnail_url}
            alt={asset.filename}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
          />
          
          {/* 媒体类型标识 */}
          <div className="absolute top-2 left-2">
            <div className="flex items-center gap-1 px-2 py-1 bg-black/70 rounded text-white text-xs">
              {asset.media_type === 'video' ? (
                <>
                  <Video size={12} />
                  <span>{asset.duration ? `${Math.round(asset.duration)}s` : 'Video'}</span>
                </>
              ) : (
                <>
                  <Image size={12} />
                  <span>Image</span>
                </>
              )}
            </div>
          </div>

          {/* 匹配度 */}
          <div className="absolute top-2 right-2">
            {renderMatchScore(match_score)}
          </div>

          {/* 选择指示器 */}
          <div className="absolute inset-0 bg-amber-400/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <div className="bg-amber-400 text-black px-3 py-1 rounded-full text-sm font-medium">
              选择素材
            </div>
          </div>
        </div>

        {/* 信息区域 */}
        <div className="p-3">
          {/* 文件名 */}
          <div className="text-sm text-white font-medium mb-2 truncate">
            {asset.filename}
          </div>

          {/* 匹配原因 */}
          <div className="text-xs text-zinc-400 mb-2 line-clamp-2">
            {match_reason}
          </div>

          {/* 匹配的标签 */}
          {matched_tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {matched_tags.slice(0, 3).map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-amber-500/20 text-amber-300 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
              {matched_tags.length > 3 && (
                <span className="text-xs text-zinc-500">
                  +{matched_tags.length - 3}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // 渲染空状态
  const renderEmptyState = () => (
    <div className="col-span-full text-center py-12">
      <AlertCircle size={48} className="mx-auto mb-4 text-zinc-500" />
      <h3 className="text-lg font-medium text-white mb-2">
        没有找到匹配的素材
      </h3>
      <p className="text-zinc-400 mb-6">
        当前Beat: "{beat.content.slice(0, 50)}..."
        <br />
        尝试调整筛选条件或上传新的素材
      </p>
      
      <div className="flex justify-center gap-3">
        <button
          onClick={() => setMinMatchScore(Math.max(0.3, minMatchScore - 0.1))}
          className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg transition-colors"
        >
          降低匹配要求
        </button>
        <button
          onClick={onUploadRequest}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black rounded-lg transition-colors flex items-center gap-2"
        >
          <Plus size={16} />
          上传素材
        </button>
      </div>
    </div>
  );

  return (
    <div className={`bg-zinc-900 rounded-lg ${className}`}>
      {/* 头部控制 */}
      <div className="p-4 border-b border-zinc-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">素材推荐</h3>
          
          <div className="flex items-center gap-2">
            <button
              onClick={fetchRecommendations}
              disabled={loading}
              className="px-3 py-1 bg-amber-500 hover:bg-amber-600 disabled:bg-zinc-600 text-black disabled:text-zinc-400 rounded text-sm transition-colors flex items-center gap-1"
            >
              <Search size={14} />
              {loading ? '搜索中...' : '刷新'}
            </button>
          </div>
        </div>

        {/* Beat信息 */}
        <div className="bg-zinc-800 rounded-lg p-3 mb-4">
          <div className="text-sm text-zinc-300 mb-2">
            当前Beat: {beat.content}
          </div>
          
          {/* Beat标签 */}
          <div className="flex flex-wrap gap-1">
            {beat.emotion_tags.map((tag, index) => (
              <span key={index} className="px-2 py-1 bg-red-500/20 text-red-300 text-xs rounded">
                {tag}
              </span>
            ))}
            {beat.scene_tags.map((tag, index) => (
              <span key={index} className="px-2 py-1 bg-blue-500/20 text-blue-300 text-xs rounded">
                {tag}
              </span>
            ))}
            {beat.action_tags.map((tag, index) => (
              <span key={index} className="px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded">
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* 筛选控制 */}
        <div className="flex items-center gap-4 text-sm">
          {/* 媒体类型选择 */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-400">类型:</span>
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={selectedMediaTypes.includes('video')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedMediaTypes([...selectedMediaTypes, 'video']);
                  } else {
                    setSelectedMediaTypes(selectedMediaTypes.filter(t => t !== 'video'));
                  }
                }}
                className="rounded"
              />
              <Video size={14} className="text-zinc-400" />
              <span className="text-white">视频</span>
            </label>
            <label className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={selectedMediaTypes.includes('image')}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedMediaTypes([...selectedMediaTypes, 'image']);
                  } else {
                    setSelectedMediaTypes(selectedMediaTypes.filter(t => t !== 'image'));
                  }
                }}
                className="rounded"
              />
              <Image size={14} className="text-zinc-400" />
              <span className="text-white">图片</span>
            </label>
          </div>

          {/* 匹配度阈值 */}
          <div className="flex items-center gap-2">
            <span className="text-zinc-400">匹配度:</span>
            <input
              type="range"
              min="0.3"
              max="0.9"
              step="0.1"
              value={minMatchScore}
              onChange={(e) => setMinMatchScore(parseFloat(e.target.value))}
              className="w-20"
            />
            <span className="text-white text-xs w-8">
              {Math.round(minMatchScore * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* 推荐结果 */}
      <div className="p-4">
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
            <div className="flex items-center gap-2 text-red-300">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          </div>
        )}

        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, index) => (
              <div key={index} className="bg-zinc-800 rounded-lg animate-pulse">
                <div className="aspect-video bg-zinc-700 rounded-t-lg" />
                <div className="p-3">
                  <div className="h-4 bg-zinc-700 rounded mb-2" />
                  <div className="h-3 bg-zinc-700 rounded w-2/3" />
                </div>
              </div>
            ))}
          </div>
        ) : recommendations.length > 0 ? (
          <>
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm text-zinc-400">
                找到 {recommendations.length} 个匹配素材
              </span>
              
              {recommendations.length > 0 && (
                <div className="text-xs text-zinc-500">
                  平均匹配度: {Math.round(recommendations.reduce((sum, r) => sum + r.match_score, 0) / recommendations.length * 100)}%
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {recommendations.map(renderAssetCard)}
            </div>
          </>
        ) : (
          renderEmptyState()
        )}
      </div>
    </div>
  );
};

export default StoryboardAssetRecommendation;