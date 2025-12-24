import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2, VolumeX, Scissors, Trash2, Plus } from 'lucide-react';
import { Button } from '../ui/Button';
import { useSyncService } from '../../services/syncService';

interface Asset {
  id: string;
  filename: string;
  mime_type: string;
  duration?: number;
  thumbnail_path?: string;
}

interface Clip {
  id: string;
  timeline_id: string;
  asset_id: string;
  asset?: Asset;
  start_time: number;
  end_time: number;
  trim_start: number;
  trim_end: number | null;
  volume: number;
  is_muted: number;
  audio_fade_in: number;
  audio_fade_out: number;
  transition_type: string | null;
  transition_duration: number;
  order_index: number;
  clip_metadata: any;
}

interface Timeline {
  id: string;
  project_id: string;
  name: string;
  duration: number;
  clips: Clip[];
}

interface TimelineEditorProps {
  projectId: string;
  timelineId?: string;
  clips?: Clip[];
  onSave?: (timeline: Timeline) => void;
  onTimeUpdate?: (time: number) => void;
  onPlayStateChange?: (isPlaying: boolean) => void;
}

const TimelineEditor: React.FC<TimelineEditorProps> = ({ 
  projectId, 
  timelineId, 
  clips: externalClips,
  onSave,
  onTimeUpdate,
  onPlayStateChange
}) => {
  // 同步服务
  const {
    syncState,
    isSyncEnabled,
    updateTime,
    updatePlayState,
    updateDuration
  } = useSyncService('timeline-editor');
  
  // 状态管理
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [clips, setClips] = useState<Clip[]>(externalClips || []);
  const [selectedClips, setSelectedClips] = useState<string[]>([]);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [totalDuration, setTotalDuration] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [draggedClip, setDraggedClip] = useState<string | null>(null);
  const [scale, setScale] = useState<number>(1);
  
  // 使用同步状态或本地状态
  const playhead = isSyncEnabled ? syncState.currentTime : currentTime;
  const playState = isSyncEnabled ? syncState.isPlaying : isPlaying;
  
  // Refs
  const timelineRef = useRef<HTMLDivElement>(null);
  const playheadRef = useRef<HTMLDivElement>(null);
  
  // 计算总时长
  useEffect(() => {
    if (clips.length > 0) {
      const maxEndTime = Math.max(...clips.map(clip => clip.end_time));
      setTotalDuration(maxEndTime);
      if (isSyncEnabled) {
        updateDuration(maxEndTime);
      }
    } else {
      setTotalDuration(0);
      if (isSyncEnabled) {
        updateDuration(0);
      }
    }
  }, [clips, isSyncEnabled, updateDuration]);

  // 同步外部clips
  useEffect(() => {
    if (externalClips) {
      setClips(externalClips);
    }
  }, [externalClips]);

  // 播放控制
  const togglePlayback = useCallback(() => {
    const newPlayState = !playState;
    setIsPlaying(newPlayState);
    if (isSyncEnabled) {
      updatePlayState(newPlayState);
    }
    onPlayStateChange?.(newPlayState);
  }, [playState, isSyncEnabled, updatePlayState, onPlayStateChange]);

  // 时间更新
  const handleTimeUpdate = useCallback((time: number) => {
    const clampedTime = Math.max(0, Math.min(time, totalDuration));
    setCurrentTime(clampedTime);
    if (isSyncEnabled) {
      updateTime(clampedTime);
    }
    onTimeUpdate?.(clampedTime);
  }, [totalDuration, isSyncEnabled, updateTime, onTimeUpdate]);

  // 时间轴点击
  const handleTimelineClick = useCallback((e: React.MouseEvent) => {
    if (timelineRef.current && totalDuration > 0) {
      const rect = timelineRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const newTime = (clickX / rect.width) * totalDuration;
      handleTimeUpdate(newTime);
    }
  }, [totalDuration, handleTimeUpdate]);

  // 添加素材到时间轴
  const addAssetToTimeline = useCallback((asset: Asset, insertTime?: number) => {
    const startTime = insertTime ?? totalDuration;
    const duration = asset.duration || 5;
    
    const newClip: Clip = {
      id: `clip-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      timeline_id: timelineId || 'default',
      asset_id: asset.id,
      asset,
      start_time: startTime,
      end_time: startTime + duration,
      trim_start: 0,
      trim_end: duration,
      volume: 1.0,
      is_muted: 0,
      audio_fade_in: 0,
      audio_fade_out: 0,
      transition_type: null,
      transition_duration: 0,
      order_index: clips.length,
      clip_metadata: {}
    };
    
    setClips(prev => [...prev, newClip]);
  }, [clips.length, timelineId, totalDuration]);

  // 删除片段
  const deleteClip = useCallback((clipId: string) => {
    setClips(prev => prev.filter(clip => clip.id !== clipId));
    setSelectedClips(prev => prev.filter(id => id !== clipId));
  }, []);

  // 分割片段
  const splitClip = useCallback((clipId: string, splitTime: number) => {
    setClips(prev => {
      const clipIndex = prev.findIndex(clip => clip.id === clipId);
      if (clipIndex === -1) return prev;
      
      const originalClip = prev[clipIndex];
      if (splitTime <= originalClip.start_time || splitTime >= originalClip.end_time) {
        return prev;
      }
      
      // 创建两个新片段
      const firstClip: Clip = {
        ...originalClip,
        id: `${originalClip.id}-1`,
        end_time: splitTime,
        trim_end: originalClip.trim_start + (splitTime - originalClip.start_time)
      };
      
      const secondClip: Clip = {
        ...originalClip,
        id: `${originalClip.id}-2`,
        start_time: splitTime,
        trim_start: originalClip.trim_start + (splitTime - originalClip.start_time)
      };
      
      const newClips = [...prev];
      newClips[clipIndex] = firstClip;
      newClips.splice(clipIndex + 1, 0, secondClip);
      
      return newClips;
    });
  }, []);

  // 片段拖拽开始
  const handleClipDragStart = useCallback((clipId: string) => {
    setDraggedClip(clipId);
  }, []);

  // 片段拖拽结束
  const handleClipDragEnd = useCallback(() => {
    setDraggedClip(null);
  }, []);

  // 格式化时间显示
  const formatTime = useCallback((seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const frames = Math.floor((seconds % 1) * 30); // 假设30fps
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
  }, []);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }
      
      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlayback();
          break;
        case 'Delete':
        case 'Backspace':
          selectedClips.forEach(clipId => deleteClip(clipId));
          break;
        case 'Home':
          handleTimeUpdate(0);
          break;
        case 'End':
          handleTimeUpdate(totalDuration);
          break;
        case 'ArrowLeft':
          handleTimeUpdate(playhead - 1);
          break;
        case 'ArrowRight':
          handleTimeUpdate(playhead + 1);
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayback, selectedClips, deleteClip, handleTimeUpdate, totalDuration, playhead]);

  return (
    <div className="w-full bg-zinc-900 text-white">
      {/* 时间轴控制栏 */}
      <div className="flex items-center justify-between p-4 bg-zinc-800 border-b border-zinc-700">
        <div className="flex items-center gap-4">
          {/* 播放控制 */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleTimeUpdate(0)}
              title="回到开始 (Home)"
            >
              <SkipBack size={16} />
            </Button>
            
            <Button
              onClick={togglePlayback}
              title={playState ? '暂停 (Space)' : '播放 (Space)'}
            >
              {playState ? <Pause size={16} /> : <Play size={16} />}
            </Button>
            
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleTimeUpdate(totalDuration)}
              title="跳到结尾 (End)"
            >
              <SkipForward size={16} />
            </Button>
          </div>
          
          {/* 时间显示 */}
          <div className="flex items-center gap-2 text-sm font-mono">
            <span className="text-amber-400">{formatTime(playhead)}</span>
            <span className="text-zinc-500">/</span>
            <span className="text-zinc-400">{formatTime(totalDuration)}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* 缩放控制 */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setScale(prev => Math.max(0.1, prev - 0.1))}
            >
              -
            </Button>
            <span className="text-sm w-12 text-center">{Math.round(scale * 100)}%</span>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setScale(prev => Math.min(5, prev + 0.1))}
            >
              +
            </Button>
          </div>
          
          {/* 工具按钮 */}
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                if (selectedClips.length === 1) {
                  splitClip(selectedClips[0], playhead);
                }
              }}
              disabled={selectedClips.length !== 1}
              title="分割片段 (S)"
            >
              <Scissors size={16} />
            </Button>
            
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                selectedClips.forEach(clipId => deleteClip(clipId));
              }}
              disabled={selectedClips.length === 0}
              title="删除片段 (Delete)"
            >
              <Trash2 size={16} />
            </Button>
          </div>
        </div>
      </div>
      
      {/* 时间轴区域 */}
      <div className="relative">
        {/* 时间标尺 */}
        <div className="h-8 bg-zinc-800 border-b border-zinc-700 relative overflow-hidden">
          {totalDuration > 0 && Array.from({ length: Math.ceil(totalDuration) + 1 }, (_, i) => (
            <div
              key={i}
              className="absolute top-0 bottom-0 border-l border-zinc-600"
              style={{ left: `${(i / totalDuration) * 100}%` }}
            >
              <span className="absolute top-1 left-1 text-xs text-zinc-400">
                {formatTime(i)}
              </span>
            </div>
          ))}
        </div>
        
        {/* 时间轴轨道 */}
        <div
          ref={timelineRef}
          className="relative h-32 bg-zinc-900 border-b border-zinc-700 cursor-pointer overflow-hidden"
          onClick={handleTimelineClick}
          style={{ transform: `scaleX(${scale})`, transformOrigin: 'left' }}
        >
          {/* 片段 */}
          {clips.map((clip) => {
            const leftPercent = totalDuration > 0 ? (clip.start_time / totalDuration) * 100 : 0;
            const widthPercent = totalDuration > 0 ? ((clip.end_time - clip.start_time) / totalDuration) * 100 : 0;
            const isSelected = selectedClips.includes(clip.id);
            const isDragged = draggedClip === clip.id;
            
            return (
              <div
                key={clip.id}
                className={`absolute top-4 h-24 rounded border-2 cursor-move transition-all ${
                  isSelected 
                    ? 'border-amber-400 bg-gradient-to-r from-amber-500/80 to-yellow-500/80' 
                    : 'border-zinc-600 bg-gradient-to-r from-blue-500/60 to-purple-500/60'
                } ${isDragged ? 'opacity-50' : ''} hover:border-amber-300`}
                style={{
                  left: `${leftPercent}%`,
                  width: `${widthPercent}%`,
                  minWidth: '60px'
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  if (e.ctrlKey || e.metaKey) {
                    setSelectedClips(prev => 
                      prev.includes(clip.id) 
                        ? prev.filter(id => id !== clip.id)
                        : [...prev, clip.id]
                    );
                  } else {
                    setSelectedClips([clip.id]);
                  }
                }}
                onMouseDown={() => handleClipDragStart(clip.id)}
                onMouseUp={handleClipDragEnd}
              >
                <div className="p-2 h-full flex flex-col justify-between text-xs">
                  <div className="font-medium text-white truncate">
                    {clip.asset?.filename || `Clip ${clip.order_index + 1}`}
                  </div>
                  <div className="text-zinc-200 opacity-75">
                    {formatTime(clip.end_time - clip.start_time)}
                  </div>
                </div>
                
                {/* 音量指示器 */}
                {clip.is_muted ? (
                  <VolumeX size={12} className="absolute top-1 right-1 text-red-400" />
                ) : clip.volume !== 1 ? (
                  <Volume2 size={12} className="absolute top-1 right-1 text-blue-400" />
                ) : null}
              </div>
            );
          })}
          
          {/* 播放头 */}
          <div
            ref={playheadRef}
            className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-20 pointer-events-none"
            style={{ 
              left: totalDuration > 0 ? `${(playhead / totalDuration) * 100}%` : '0%',
              transform: `scaleX(${1/scale})` // 保持播放头宽度不变
            }}
          >
            <div className="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rotate-45 transform origin-center" />
          </div>
        </div>
        
        {/* 空状态 */}
        {clips.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center text-zinc-500">
            <div className="text-center">
              <Plus size={48} className="mx-auto mb-2 opacity-50" />
              <p>拖拽素材到此处开始编辑</p>
              <p className="text-sm mt-1">或使用素材选择器添加片段</p>
            </div>
          </div>
        )}
      </div>
      
      {/* 状态栏 */}
      <div className="flex items-center justify-between p-2 bg-zinc-800 text-xs text-zinc-400">
        <div className="flex items-center gap-4">
          <span>片段: {clips.length}</span>
          <span>已选择: {selectedClips.length}</span>
          <span>总时长: {formatTime(totalDuration)}</span>
        </div>
        
        <div className="flex items-center gap-4">
          {isSyncEnabled && (
            <span className="text-green-400">● 同步已启用</span>
          )}
          <span>缩放: {Math.round(scale * 100)}%</span>
        </div>
      </div>
    </div>
  );
};

export default TimelineEditor;