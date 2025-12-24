import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, Clock, Target, Zap } from 'lucide-react';
import { useSyncService } from '../../services/syncService';

interface Beat {
  id: string;
  order_index: number;
  content: string;
  duration: number;
  emotion_tags: string[];
  scene_tags: string[];
  action_tags: string[];
}

interface SyncBeatBoardProps {
  projectId: string;
  beats: Beat[];
  onBeatSelect?: (beatIndex: number) => void;
  className?: string;
}

const SyncBeatBoard: React.FC<SyncBeatBoardProps> = ({
  projectId,
  beats,
  onBeatSelect,
  className = ''
}) => {
  const {
    syncState,
    isSyncEnabled,
    updateTime,
    updatePlayState,
    updateDuration,
    seekTo,
    formatTime,
    calculateBeatPosition,
    findBeatAtTime
  } = useSyncService('beatboard');
  
  const [localCurrentBeat, setLocalCurrentBeat] = useState<number>(0);
  const [localIsPlaying, setLocalIsPlaying] = useState<boolean>(false);
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
  
  return (
    <div className={`bg-zinc-900 rounded-lg ${className}`}>
      {/* 头部控制 */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-700">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-white">BeatBoard</h3>
          
          {isSyncEnabled && (
            <div className="flex items-center gap-2 px-2 py-1 bg-amber-500/20 rounded text-amber-400 text-xs">
              <Zap size={12} />
              <span>同步模式</span>
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
      
      {/* Beat网格 */}
      <div className="p-4">
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
      
      {/* 底部状态栏 */}
      {isSyncEnabled && (
        <div className="border-t border-zinc-700 p-3 bg-zinc-800/50">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-4">
              <span className="text-zinc-400">
                总时长: {formatTime(totalDuration)}
              </span>
              <span className="text-zinc-400">
                当前时间: {formatTime(syncState.currentTime)}
              </span>
            </div>
            
            {currentBeat && (
              <div className="text-amber-400">
                {currentBeat.content.slice(0, 30)}
                {currentBeat.content.length > 30 ? '...' : ''}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SyncBeatBoard;