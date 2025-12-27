/**
 * 候选素材切换器
 * 显示 Top 5 候选素材，支持丝滑切换
 */

import React, { useState, useEffect } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Image as ImageIcon,
  Video,
  Star,
  Check,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { wizardApi, AssetCandidate } from './api';

interface CandidateSwitcherProps {
  sceneId: string;
  query?: string;
  onSelect?: (candidate: AssetCandidate) => void;
  selectedId?: string;
}

export const CandidateSwitcher: React.FC<CandidateSwitcherProps> = ({
  sceneId,
  query,
  onSelect,
  selectedId
}) => {
  const [candidates, setCandidates] = useState<AssetCandidate[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载候选
  useEffect(() => {
    if (sceneId) {
      loadCandidates();
    }
  }, [sceneId]);

  const loadCandidates = async () => {
    setLoading(true);
    setError(null);
    try {
      // 先尝试获取缓存的候选
      const cached = await wizardApi.getCachedCandidates(sceneId);
      if (cached.candidates.length > 0) {
        setCandidates(cached.candidates);
      } else if (query) {
        // 如果没有缓存，执行新的召回
        const result = await wizardApi.recallAssets({
          scene_id: sceneId,
          query: query,
          strategy: 'hybrid'
        });
        setCandidates(result.candidates);
        if (!result.has_match) {
          setError(result.placeholder_message || '未找到匹配素材');
        }
      }
    } catch (err) {
      setError('加载候选失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 切换候选
  const handleSwitch = async (direction: 'prev' | 'next') => {
    const newIndex = direction === 'next' 
      ? Math.min(currentIndex + 1, candidates.length - 1)
      : Math.max(currentIndex - 1, 0);
    
    if (newIndex !== currentIndex) {
      try {
        const result = await wizardApi.switchCandidate(
          sceneId,
          currentIndex + 1,
          newIndex + 1
        );
        if (result.success) {
          setCurrentIndex(newIndex);
        }
      } catch (err) {
        console.error('切换失败:', err);
      }
    }
  };

  // 选择候选
  const handleSelect = (candidate: AssetCandidate) => {
    if (onSelect) {
      onSelect(candidate);
    }
  };

  const currentCandidate = candidates[currentIndex];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 bg-zinc-900 rounded-lg">
        <Loader2 className="text-amber-500 animate-spin" size={24} />
      </div>
    );
  }

  if (error || candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 bg-zinc-900 rounded-lg border border-zinc-800">
        <AlertCircle className="text-zinc-600 mb-2" size={32} />
        <div className="text-sm text-zinc-500">{error || '暂无候选素材'}</div>
        <div className="text-xs text-zinc-600 mt-1">请上传素材或调整搜索条件</div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
      {/* 主预览区 */}
      <div className="relative aspect-video bg-black">
        {currentCandidate && (
          <>
            {/* 预览图/视频 */}
            <div className="absolute inset-0 flex items-center justify-center">
              {currentCandidate.asset_path.match(/\.(mp4|mov|avi|mkv)$/i) ? (
                <Video className="text-zinc-700" size={48} />
              ) : (
                <img
                  src={currentCandidate.asset_path}
                  alt={`候选 ${currentCandidate.rank}`}
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              )}
            </div>

            {/* 匹配分数 */}
            <div className="absolute top-2 left-2 px-2 py-1 bg-black/70 rounded text-xs text-white flex items-center gap-1">
              <Star size={12} className="text-amber-400" />
              <span>{Math.round(currentCandidate.score * 100)}%</span>
            </div>

            {/* 排名 */}
            <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs text-zinc-400">
              #{currentCandidate.rank} / {candidates.length}
            </div>

            {/* 选中标记 */}
            {selectedId === currentCandidate.candidate_id && (
              <div className="absolute bottom-2 right-2 p-1.5 bg-emerald-500 rounded-full">
                <Check size={14} className="text-white" />
              </div>
            )}
          </>
        )}

        {/* 左右切换按钮 */}
        <button
          onClick={() => handleSwitch('prev')}
          disabled={currentIndex === 0}
          className="absolute left-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeft size={20} />
        </button>
        <button
          onClick={() => handleSwitch('next')}
          disabled={currentIndex === candidates.length - 1}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRight size={20} />
        </button>
      </div>

      {/* 信息区 */}
      {currentCandidate && (
        <div className="p-3">
          <div className="text-sm text-zinc-300 truncate mb-1">
            {currentCandidate.asset_path.split('/').pop()}
          </div>
          <div className="text-xs text-zinc-500 mb-2">
            {currentCandidate.match_reason}
          </div>
          
          {/* 标签 */}
          {currentCandidate.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {currentCandidate.tags.slice(0, 5).map((tag, i) => (
                <span key={i} className="px-1.5 py-0.5 bg-zinc-800 rounded text-[10px] text-zinc-400">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* 选择按钮 */}
          <button
            onClick={() => handleSelect(currentCandidate)}
            className={`w-full py-2 rounded text-sm font-medium transition-colors ${
              selectedId === currentCandidate.candidate_id
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-amber-500 hover:bg-amber-400 text-black'
            }`}
          >
            {selectedId === currentCandidate.candidate_id ? '已选择' : '选择此素材'}
          </button>
        </div>
      )}

      {/* 缩略图列表 */}
      <div className="flex gap-1 p-2 border-t border-zinc-800 overflow-x-auto">
        {candidates.map((candidate, index) => (
          <button
            key={candidate.candidate_id}
            onClick={() => setCurrentIndex(index)}
            className={`flex-shrink-0 w-12 h-12 rounded overflow-hidden border-2 transition-colors ${
              index === currentIndex
                ? 'border-amber-500'
                : 'border-transparent hover:border-zinc-600'
            }`}
          >
            <div className="w-full h-full bg-zinc-800 flex items-center justify-center">
              <span className="text-xs text-zinc-500">#{candidate.rank}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default CandidateSwitcher;
