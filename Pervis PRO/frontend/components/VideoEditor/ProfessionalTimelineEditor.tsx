import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward, 
  Volume2, 
  VolumeX, 
  Scissors, 
  Trash2, 
  Copy, 
  Move,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Settings,
  Download,
  Upload,
  Split,
  Link,
  Unlink,
  RotateCcw,
  RotateCw,
  Layers,
  Eye,
  EyeOff,
  Lock,
  Unlock
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { AssetPickerButton } from '../AssetPicker';
import { useSyncService } from '../../services/syncService';

// 专业时间线数据类型
interface ProfessionalClip {
  id: string;
  timeline_id: string;
  asset_id: string;
  asset_filename?: string;
  asset_type: 'video' | 'image' | 'audio';
  track_id: string;
  start_time: number;
  end_time: number;
  trim_start: number;
  trim_end: number | null;
  volume: number;
  is_muted: boolean;
  is_locked: boolean;
  is_visible: boolean;
  audio_fade_in: number;
  audio_fade_out: number;
  transition_type: string | null;
  transition_duration: number;
  order_index: number;
  color?: string;
  clip_metadata: any;
  proxy_url?: string;
  thumbnail_url?: string;
  waveform_data?: number[];
}

interface Track {
  id: string;
  name: string;
  type: 'video' | 'audio';
  height: number;
  is_locked: boolean;
  is_visible: boolean;
  is_muted: boolean;
  color: string;
  order_index: number;
}

interface ProfessionalTimeline {
  id: string;
  project_id: string;
  name: string;
  duration: number;
  frame_rate: number;
  resolution: { width: number; height: number };
  tracks: Track[];
  clips: ProfessionalClip[];
  markers: Array<{
    id: string;
    time: number;
    name: string;
    color: string;
    type: 'marker' | 'chapter' | 'cue';
  }>;
}

interface ProfessionalTimelineEditorProps {
  projectId: string;
  timelineId?: string;
  onSave?: (timeline: ProfessionalTimeline) => void;
  onExport?: (format: 'xml' | 'edl' | 'json') => void;
  className?: string;
}

// 磁性吸附配置
const SNAP_THRESHOLD = 10; // 像素
const SNAP_TARGETS = ['clip_start', 'clip_end', 'playhead', 'marker'] as const;

// 帧精确控制配置
const FRAME_RATES = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60];

export const ProfessionalTimelineEditor: React.FC<ProfessionalTimelineEditorProps> = ({
  projectId,
  timelineId,
  onSave,
  onExport,
  className = ''
}) => {
  // 同步服务
  const {
    syncState,
    isSyncEnabled,
    updateTime,
    updatePlayState,
    updateDuration
  } = useSyncService('professional-timeline');

  // 核心状态
  const [timeline, setTimeline] = useState<ProfessionalTimeline | null>(null);
  const [selectedClips, setSelectedClips] = useState<string[]>([]);
  const [selectedTracks, setSelectedTracks] = useState<string[]>([]);
  const [localPlayhead, setLocalPlayhead] = useState<number>(0);
  const [localIsPlaying, setLocalIsPlaying] = useState<boolean>(false);
  
  // 视图状态
  const [zoom, setZoom] = useState<number>(1);
  const [verticalZoom, setVerticalZoom] = useState<number>(1);
  const [scrollLeft, setScrollLeft] = useState<number>(0);
  const [scrollTop, setScrollTop] = useState<number>(0);
  
  // 编辑状态
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragData, setDragData] = useState<any>(null);
  const [isResizing, setIsResizing] = useState<boolean>(false);
  const [resizeData, setResizeData] = useState<any>(null);
  const [snapEnabled, setSnapEnabled] = useState<boolean>(true);
  const [rippleEdit, setRippleEdit] = useState<boolean>(false);
  
  // 工具状态
  const [activeTool, setActiveTool] = useState<'select' | 'razor' | 'slip' | 'slide'>('select');
  const [showWaveforms, setShowWaveforms] = useState<boolean>(true);
  const [showThumbnails, setShowThumbnails] = useState<boolean>(true);
  
  // 使用同步状态或本地状态
  const playhead = isSyncEnabled ? syncState.currentTime : localPlayhead;
  const isPlaying = isSyncEnabled ? syncState.isPlaying : localIsPlaying;
  
  // Refs
  const timelineRef = useRef<HTMLDivElement>(null);
  const playheadRef = useRef<HTMLDivElement>(null);
  const tracksRef = useRef<HTMLDivElement>(null);
  
  // 时间轴配置
  const PIXELS_PER_SECOND = 50 * zoom;
  const BASE_TRACK_HEIGHT = 80;
  const TRACK_HEIGHT = BASE_TRACK_HEIGHT * verticalZoom;
  const RULER_HEIGHT = 40;
  const TRACK_HEADER_WIDTH = 200;
  
  // 帧精确计算
  const frameRate = timeline?.frame_rate || 30;
  const frameToTime = (frame: number) => frame / frameRate;
  const timeToFrame = (time: number) => Math.round(time * frameRate);
  const snapToFrame = (time: number) => frameToTime(timeToFrame(time));

  // 加载时间轴数据
  useEffect(() => {
    if (timelineId) {
      loadTimeline(timelineId);
    } else {
      // 创建默认时间轴
      createDefaultTimeline();
    }
  }, [timelineId]);

  // 同步时间轴时长
  useEffect(() => {
    if (timeline && isSyncEnabled) {
      updateDuration(timeline.duration);
    }
  }, [timeline?.duration, isSyncEnabled, updateDuration]);

  const loadTimeline = async (id: string) => {
    try {
      const response = await fetch(`/api/timeline/professional/${id}`);
      if (response.ok) {
        const data = await response.json();
        setTimeline(data);
      }
    } catch (error) {
      console.error('Failed to load professional timeline:', error);
    }
  };

  const createDefaultTimeline = () => {
    const defaultTimeline: ProfessionalTimeline = {
      id: 'new-timeline',
      project_id: projectId,
      name: '新时间轴',
      duration: 300, // 5分钟
      frame_rate: 30,
      resolution: { width: 1920, height: 1080 },
      tracks: [
        {
          id: 'video-1',
          name: 'Video 1',
          type: 'video',
          height: TRACK_HEIGHT,
          is_locked: false,
          is_visible: true,
          is_muted: false,
          color: '#3b82f6',
          order_index: 0
        },
        {
          id: 'audio-1',
          name: 'Audio 1',
          type: 'audio',
          height: TRACK_HEIGHT / 2,
          is_locked: false,
          is_visible: true,
          is_muted: false,
          color: '#10b981',
          order_index: 1
        }
      ],
      clips: [],
      markers: []
    };
    setTimeline(defaultTimeline);
  };

  // 时间格式化（帧精确）
  const formatTime = (seconds: number, showFrames: boolean = true): string => {
    const totalFrames = Math.round(seconds * frameRate);
    const hours = Math.floor(totalFrames / (frameRate * 3600));
    const minutes = Math.floor((totalFrames % (frameRate * 3600)) / (frameRate * 60));
    const secs = Math.floor((totalFrames % (frameRate * 60)) / frameRate);
    const frames = totalFrames % frameRate;
    
    if (showFrames) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${Math.floor(frames).toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  };

  // 磁性吸附计算
  const calculateSnapTargets = useCallback(() => {
    if (!timeline || !snapEnabled) return [];
    
    const targets: Array<{ time: number; type: string; id?: string }> = [];
    
    // 播放头
    targets.push({ time: playhead, type: 'playhead' });
    
    // 片段开始和结束点
    timeline.clips.forEach(clip => {
      targets.push({ time: clip.start_time, type: 'clip_start', id: clip.id });
      targets.push({ time: clip.end_time, type: 'clip_end', id: clip.id });
    });
    
    // 标记点
    timeline.markers.forEach(marker => {
      targets.push({ time: marker.time, type: 'marker', id: marker.id });
    });
    
    // 时间轴网格点（每秒）
    for (let i = 0; i <= timeline.duration; i++) {
      targets.push({ time: i, type: 'grid' });
    }
    
    return targets;
  }, [timeline, playhead, snapEnabled]);

  const findSnapTarget = useCallback((time: number, excludeIds: string[] = []) => {
    const targets = calculateSnapTargets();
    const timePixel = time * PIXELS_PER_SECOND;
    
    let closestTarget = null;
    let closestDistance = SNAP_THRESHOLD;
    
    targets.forEach(target => {
      if (excludeIds.includes(target.id || '')) return;
      
      const targetPixel = target.time * PIXELS_PER_SECOND;
      const distance = Math.abs(timePixel - targetPixel);
      
      if (distance < closestDistance) {
        closestDistance = distance;
        closestTarget = target;
      }
    });
    
    return closestTarget;
  }, [calculateSnapTargets, PIXELS_PER_SECOND]);

  // 播放控制
  const handlePlay = () => {
    const newPlayState = !isPlaying;
    
    if (isSyncEnabled) {
      updatePlayState(newPlayState);
    } else {
      setLocalIsPlaying(newPlayState);
    }
  };

  const handleSeek = (time: number, snapToFrames: boolean = true) => {
    let targetTime = Math.max(0, Math.min(time, timeline?.duration || 0));
    
    if (snapToFrames) {
      targetTime = snapToFrame(targetTime);
    }
    
    if (isSyncEnabled) {
      updateTime(targetTime);
    } else {
      setLocalPlayhead(targetTime);
    }
  };

  const handleFrameStep = (direction: 1 | -1) => {
    const currentFrame = timeToFrame(playhead);
    const newFrame = Math.max(0, currentFrame + direction);
    const newTime = frameToTime(newFrame);
    handleSeek(newTime, false);
  };

  // 时间轴交互
  const handleTimelineClick = (event: React.MouseEvent) => {
    if (!timelineRef.current || activeTool === 'razor') return;
    
    const rect = timelineRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left + scrollLeft;
    const time = x / PIXELS_PER_SECOND;
    
    // 检查磁性吸附
    const snapTarget = findSnapTarget(time);
    const finalTime = snapTarget ? snapTarget.time : time;
    
    handleSeek(finalTime);
  };

  // 片段拖拽
  const handleClipDragStart = (event: React.DragEvent, clip: ProfessionalClip) => {
    if (clip.is_locked) return;
    
    setIsDragging(true);
    setDragData({
      type: 'clip',
      clip,
      startX: event.clientX,
      originalStartTime: clip.start_time
    });
    
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('application/json', JSON.stringify({
      type: 'timeline-clip',
      clipId: clip.id
    }));
  };

  const handleClipDrag = (event: React.DragEvent) => {
    if (!isDragging || !dragData) return;
    
    const deltaX = event.clientX - dragData.startX;
    const deltaTime = deltaX / PIXELS_PER_SECOND;
    const newStartTime = dragData.originalStartTime + deltaTime;
    
    // 检查磁性吸附
    const snapTarget = findSnapTarget(newStartTime, [dragData.clip.id]);
    const finalStartTime = snapTarget ? snapTarget.time : newStartTime;
    
    // 更新拖拽预览
    // TODO: 实现拖拽预览效果
  };

  const handleClipDrop = async (event: React.DragEvent) => {
    event.preventDefault();
    
    if (!isDragging || !dragData) return;
    
    const rect = timelineRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = event.clientX - rect.left + scrollLeft;
    const dropTime = x / PIXELS_PER_SECOND;
    
    // 检查磁性吸附
    const snapTarget = findSnapTarget(dropTime, [dragData.clip.id]);
    const finalTime = snapTarget ? snapTarget.time : dropTime;
    
    // 更新片段位置
    await updateClipPosition(dragData.clip.id, finalTime);
    
    setIsDragging(false);
    setDragData(null);
  };

  // 片段调整大小
  const handleClipResizeStart = (clip: ProfessionalClip, edge: 'start' | 'end', event: React.MouseEvent) => {
    if (clip.is_locked) return;
    
    event.stopPropagation();
    setIsResizing(true);
    setResizeData({
      clip,
      edge,
      startX: event.clientX,
      originalStartTime: clip.start_time,
      originalEndTime: clip.end_time
    });
  };

  const handleClipResize = (event: React.MouseEvent) => {
    if (!isResizing || !resizeData) return;
    
    const deltaX = event.clientX - resizeData.startX;
    const deltaTime = deltaX / PIXELS_PER_SECOND;
    
    let newTime: number;
    if (resizeData.edge === 'start') {
      newTime = resizeData.originalStartTime + deltaTime;
      // 检查磁性吸附
      const snapTarget = findSnapTarget(newTime, [resizeData.clip.id]);
      newTime = snapTarget ? snapTarget.time : newTime;
      // 确保不超过结束时间
      newTime = Math.min(newTime, resizeData.clip.end_time - 0.1);
    } else {
      newTime = resizeData.originalEndTime + deltaTime;
      // 检查磁性吸附
      const snapTarget = findSnapTarget(newTime, [resizeData.clip.id]);
      newTime = snapTarget ? snapTarget.time : newTime;
      // 确保不小于开始时间
      newTime = Math.max(newTime, resizeData.clip.start_time + 0.1);
    }
    
    // 帧精确调整
    newTime = snapToFrame(newTime);
    
    // TODO: 实时更新预览
  };

  const handleClipResizeEnd = async () => {
    if (!isResizing || !resizeData) return;
    
    // 应用调整
    await updateClipTiming(resizeData.clip.id, resizeData.edge, resizeData.newTime);
    
    setIsResizing(false);
    setResizeData(null);
  };

  // 片段操作
  const updateClipPosition = async (clipId: string, newStartTime: number) => {
    try {
      const response = await fetch(`/api/clips/${clipId}/position`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_time: snapToFrame(newStartTime) })
      });
      
      if (response.ok && timelineId) {
        loadTimeline(timelineId);
      }
    } catch (error) {
      console.error('Failed to update clip position:', error);
    }
  };

  const updateClipTiming = async (clipId: string, edge: 'start' | 'end', newTime: number) => {
    try {
      const updateData = edge === 'start' 
        ? { start_time: snapToFrame(newTime) }
        : { end_time: snapToFrame(newTime) };
      
      const response = await fetch(`/api/clips/${clipId}/timing`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
      });
      
      if (response.ok && timelineId) {
        loadTimeline(timelineId);
      }
    } catch (error) {
      console.error('Failed to update clip timing:', error);
    }
  };

  const splitClipAtPlayhead = async (clipId: string) => {
    try {
      const response = await fetch(`/api/clips/${clipId}/split`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ split_time: snapToFrame(playhead) })
      });
      
      if (response.ok && timelineId) {
        loadTimeline(timelineId);
      }
    } catch (error) {
      console.error('Failed to split clip:', error);
    }
  };

  // 轨道操作
  const toggleTrackLock = async (trackId: string) => {
    const track = timeline?.tracks.find(t => t.id === trackId);
    if (!track) return;
    
    try {
      const response = await fetch(`/api/tracks/${trackId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_locked: !track.is_locked })
      });
      
      if (response.ok && timelineId) {
        loadTimeline(timelineId);
      }
    } catch (error) {
      console.error('Failed to toggle track lock:', error);
    }
  };

  const toggleTrackVisibility = async (trackId: string) => {
    const track = timeline?.tracks.find(t => t.id === trackId);
    if (!track) return;
    
    try {
      const response = await fetch(`/api/tracks/${trackId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_visible: !track.is_visible })
      });
      
      if (response.ok && timelineId) {
        loadTimeline(timelineId);
      }
    } catch (error) {
      console.error('Failed to toggle track visibility:', error);
    }
  };

  // 导出功能
  const handleExport = async (format: 'xml' | 'edl' | 'json') => {
    if (!timeline) return;
    
    try {
      const response = await fetch(`/api/timeline/${timeline.id}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format, include_media_references: true })
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${timeline.name}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        onExport?.(format);
      }
    } catch (error) {
      console.error('Failed to export timeline:', error);
    }
  };

  // 渲染时间标尺
  const renderRuler = () => {
    if (!timeline) return null;
    
    const duration = timeline.duration;
    const ticks = [];
    
    // 主要刻度（秒）
    for (let i = 0; i <= duration; i += 1) {
      const x = i * PIXELS_PER_SECOND;
      const isSecond = i % 1 === 0;
      const isFiveSecond = i % 5 === 0;
      const isTenSecond = i % 10 === 0;
      
      ticks.push(
        <div
          key={`second-${i}`}
          className={`absolute border-l ${
            isTenSecond 
              ? 'border-amber-400 h-8' 
              : isFiveSecond 
                ? 'border-zinc-300 h-6' 
                : 'border-zinc-500 h-4'
          }`}
          style={{ left: x }}
        >
          {isFiveSecond && (
            <span className="absolute -top-6 -left-8 text-xs text-zinc-300 font-mono">
              {formatTime(i, false)}
            </span>
          )}
        </div>
      );
    }
    
    // 帧刻度（如果缩放足够大）
    if (zoom > 2) {
      for (let i = 0; i <= duration * frameRate; i += 1) {
        const time = frameToTime(i);
        const x = time * PIXELS_PER_SECOND;
        
        if (i % frameRate !== 0) { // 跳过秒刻度
          ticks.push(
            <div
              key={`frame-${i}`}
              className="absolute border-l border-zinc-600 h-2"
              style={{ left: x }}
            />
          );
        }
      }
    }
    
    return ticks;
  };

  // 渲染轨道头部
  const renderTrackHeader = (track: Track) => (
    <div
      key={track.id}
      className="flex items-center justify-between p-3 bg-zinc-800 border-b border-zinc-700"
      style={{ height: track.height, minHeight: track.height }}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <div 
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: track.color }}
        />
        <span className="text-sm font-medium text-white truncate">
          {track.name}
        </span>
      </div>
      
      <div className="flex items-center gap-1">
        <Button
          size="sm"
          variant="ghost"
          onClick={() => toggleTrackVisibility(track.id)}
          className="p-1"
        >
          {track.is_visible ? (
            <Eye size={14} className="text-zinc-400" />
          ) : (
            <EyeOff size={14} className="text-red-400" />
          )}
        </Button>
        
        <Button
          size="sm"
          variant="ghost"
          onClick={() => toggleTrackLock(track.id)}
          className="p-1"
        >
          {track.is_locked ? (
            <Lock size={14} className="text-red-400" />
          ) : (
            <Unlock size={14} className="text-zinc-400" />
          )}
        </Button>
      </div>
    </div>
  );

  // 渲染片段
  const renderClip = (clip: ProfessionalClip) => {
    const track = timeline?.tracks.find(t => t.id === clip.track_id);
    if (!track) return null;
    
    const x = clip.start_time * PIXELS_PER_SECOND;
    const width = (clip.end_time - clip.start_time) * PIXELS_PER_SECOND;
    const isSelected = selectedClips.includes(clip.id);
    const trackIndex = timeline?.tracks.findIndex(t => t.id === clip.track_id) || 0;
    const y = timeline?.tracks.slice(0, trackIndex).reduce((sum, t) => sum + t.height, 0) || 0;
    
    return (
      <div
        key={clip.id}
        className={`absolute rounded border-2 cursor-pointer transition-all ${
          isSelected 
            ? 'border-amber-400 shadow-lg shadow-amber-400/20 z-10' 
            : 'border-zinc-600 hover:border-amber-300 z-5'
        } ${clip.is_locked ? 'opacity-60' : ''}`}
        style={{
          left: x,
          top: y + 2,
          width: Math.max(width, 20),
          height: track.height - 4,
          backgroundColor: clip.color || track.color,
          backgroundImage: clip.asset_type === 'video' && showThumbnails && clip.thumbnail_url
            ? `url(${clip.thumbnail_url})`
            : 'none',
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }}
        draggable={!clip.is_locked}
        onDragStart={(e) => handleClipDragStart(e, clip)}
        onDrag={handleClipDrag}
        onDragEnd={handleClipDrop}
        onClick={(e) => {
          e.stopPropagation();
          if (activeTool === 'razor') {
            splitClipAtPlayhead(clip.id);
          } else {
            setSelectedClips(prev => 
              e.ctrlKey || e.metaKey
                ? prev.includes(clip.id) 
                  ? prev.filter(id => id !== clip.id)
                  : [...prev, clip.id]
                : [clip.id]
            );
          }
        }}
      >
        {/* 片段内容 */}
        <div className="relative h-full p-2 flex flex-col justify-between text-white text-xs overflow-hidden">
          {/* 顶部信息 */}
          <div className="flex items-center justify-between">
            <span className="font-medium truncate">
              {clip.asset_filename || `Asset ${clip.asset_id.slice(0, 8)}`}
            </span>
            {clip.is_locked && <Lock size={10} className="text-red-300" />}
          </div>
          
          {/* 音频波形 */}
          {clip.asset_type === 'video' && showWaveforms && clip.waveform_data && (
            <div className="flex-1 flex items-center">
              <div className="w-full h-8 flex items-end gap-px">
                {clip.waveform_data.slice(0, Math.floor(width / 2)).map((amplitude, i) => (
                  <div
                    key={i}
                    className="bg-green-400 opacity-60"
                    style={{
                      height: `${Math.max(1, amplitude * 100)}%`,
                      width: '1px'
                    }}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* 底部信息 */}
          <div className="flex justify-between items-end">
            <span className="font-mono text-xs">
              {formatTime(clip.start_time, false)}
            </span>
            <div className="flex items-center gap-1">
              {clip.is_muted && <VolumeX size={10} className="text-red-300" />}
              {clip.transition_type && (
                <div className="w-2 h-2 bg-purple-400 rounded-full" />
              )}
            </div>
          </div>
        </div>
        
        {/* 调整手柄 */}
        {!clip.is_locked && (
          <>
            <div 
              className="absolute left-0 top-0 w-2 h-full bg-amber-400 opacity-0 hover:opacity-100 cursor-ew-resize transition-opacity"
              onMouseDown={(e) => handleClipResizeStart(clip, 'start', e)}
            />
            <div 
              className="absolute right-0 top-0 w-2 h-full bg-amber-400 opacity-0 hover:opacity-100 cursor-ew-resize transition-opacity"
              onMouseDown={(e) => handleClipResizeStart(clip, 'end', e)}
            />
          </>
        )}
        
        {/* 磁性吸附指示器 */}
        {snapEnabled && (
          <>
            <div className="absolute -left-1 top-0 w-0.5 h-full bg-red-500 opacity-0 snap-indicator" />
            <div className="absolute -right-1 top-0 w-0.5 h-full bg-red-500 opacity-0 snap-indicator" />
          </>
        )}
      </div>
    );
  };

  // 渲染播放头
  const renderPlayhead = () => {
    const x = playhead * PIXELS_PER_SECOND;
    const totalHeight = timeline?.tracks.reduce((sum, track) => sum + track.height, 0) || 0;
    
    return (
      <div
        ref={playheadRef}
        className="absolute pointer-events-none z-30"
        style={{ left: x, top: RULER_HEIGHT, height: totalHeight }}
      >
        <div className="w-0.5 h-full bg-red-500 shadow-lg">
          <div className="absolute -top-2 -left-2 w-4 h-4 bg-red-500 rounded-full border-2 border-white shadow-lg" />
          <div className="absolute -bottom-2 -left-2 w-4 h-4 bg-red-500 rounded-full border-2 border-white shadow-lg" />
        </div>
        
        {/* 时间显示 */}
        <div className="absolute -top-8 -left-12 px-2 py-1 bg-red-500 text-white text-xs font-mono rounded">
          {formatTime(playhead)}
        </div>
      </div>
    );
  };

  // 渲染标记点
  const renderMarkers = () => {
    if (!timeline) return null;
    
    return timeline.markers.map(marker => {
      const x = marker.time * PIXELS_PER_SECOND;
      
      return (
        <div
          key={marker.id}
          className="absolute pointer-events-none z-20"
          style={{ left: x, top: 0, height: RULER_HEIGHT }}
        >
          <div 
            className="w-0.5 h-full shadow-lg"
            style={{ backgroundColor: marker.color }}
          >
            <div 
              className="absolute -top-1 -left-1 w-2 h-2 rounded-full border border-white shadow-lg"
              style={{ backgroundColor: marker.color }}
            />
          </div>
          
          <div className="absolute -top-6 -left-8 px-1 py-0.5 text-xs text-white rounded text-center">
            {marker.name}
          </div>
        </div>
      );
    });
  };

  if (!timeline) {
    return (
      <div className="flex items-center justify-center h-64 bg-zinc-900 rounded-lg">
        <div className="text-zinc-400">加载专业时间轴...</div>
      </div>
    );
  }

  const totalTrackHeight = timeline.tracks.reduce((sum, track) => sum + track.height, 0);

  return (
    <div className={`bg-zinc-900 rounded-lg overflow-hidden ${className}`}>
      {/* 专业工具栏 */}
      <div className="flex items-center justify-between p-4 bg-zinc-800 border-b border-zinc-700">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-white">{timeline.name}</h3>
          <div className="flex items-center gap-2 text-sm text-zinc-400">
            <span>{timeline.resolution.width}×{timeline.resolution.height}</span>
            <span>•</span>
            <span>{timeline.frame_rate}fps</span>
            <span>•</span>
            <span>{formatTime(timeline.duration)}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* 工具选择 */}
          <div className="flex items-center gap-1 mr-4">
            {[
              { tool: 'select', icon: Move, label: '选择' },
              { tool: 'razor', icon: Scissors, label: '剃刀' },
              { tool: 'slip', icon: Split, label: '滑移' },
              { tool: 'slide', icon: Link, label: '滑动' }
            ].map(({ tool, icon: Icon, label }) => (
              <Button
                key={tool}
                size="sm"
                variant={activeTool === tool ? 'primary' : 'ghost'}
                onClick={() => setActiveTool(tool as any)}
                icon={Icon}
                title={label}
              />
            ))}
          </div>
          
          {/* 视图选项 */}
          <Button
            size="sm"
            variant={snapEnabled ? 'primary' : 'ghost'}
            onClick={() => setSnapEnabled(!snapEnabled)}
            title="磁性吸附"
          >
            磁吸
          </Button>
          
          <Button
            size="sm"
            variant={showWaveforms ? 'primary' : 'ghost'}
            onClick={() => setShowWaveforms(!showWaveforms)}
            title="显示波形"
          >
            波形
          </Button>
          
          <Button
            size="sm"
            variant={showThumbnails ? 'primary' : 'ghost'}
            onClick={() => setShowThumbnails(!showThumbnails)}
            title="显示缩略图"
          >
            缩略图
          </Button>
          
          {/* 导出选项 */}
          <div className="flex items-center gap-1 ml-4">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleExport('xml')}
              title="导出Premiere Pro XML"
            >
              XML
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleExport('edl')}
              title="导出EDL"
            >
              EDL
            </Button>
          </div>
        </div>
      </div>
      
      {/* 播放控制栏 */}
      <div className="flex items-center justify-between p-3 bg-zinc-800/50 border-b border-zinc-700">
        <div className="flex items-center gap-2">
          {/* 帧精确控制 */}
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleFrameStep(-1)}
            title="上一帧"
          >
            <SkipBack size={14} />
          </Button>
          
          <Button
            onClick={handlePlay}
            className="p-2 bg-amber-500 hover:bg-amber-600 text-white rounded-full"
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          </Button>
          
          <Button
            size="sm"
            variant="ghost"
            onClick={() => handleFrameStep(1)}
            title="下一帧"
          >
            <SkipForward size={14} />
          </Button>
          
          {/* 时间显示 */}
          <div className="ml-4 font-mono text-sm text-white bg-zinc-700 px-2 py-1 rounded">
            {formatTime(playhead)}
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* 缩放控制 */}
          <div className="flex items-center gap-2">
            <Button size="sm" variant="ghost" onClick={() => setZoom(Math.max(0.1, zoom - 0.2))}>
              <ZoomOut size={14} />
            </Button>
            <span className="text-xs text-zinc-400 w-12 text-center">{zoom.toFixed(1)}x</span>
            <Button size="sm" variant="ghost" onClick={() => setZoom(Math.min(5, zoom + 0.2))}>
              <ZoomIn size={14} />
            </Button>
          </div>
          
          {/* 垂直缩放 */}
          <div className="flex items-center gap-2">
            <Button size="sm" variant="ghost" onClick={() => setVerticalZoom(Math.max(0.5, verticalZoom - 0.2))}>
              <Layers size={14} />
            </Button>
            <span className="text-xs text-zinc-400 w-12 text-center">{verticalZoom.toFixed(1)}x</span>
            <Button size="sm" variant="ghost" onClick={() => setVerticalZoom(Math.min(3, verticalZoom + 0.2))}>
              <Maximize2 size={14} />
            </Button>
          </div>
          
          {/* 素材选择器 */}
          <AssetPickerButton
            projectId={projectId}
            onSelect={(asset) => {
              // TODO: 添加素材到当前播放头位置
              console.log('Add asset to timeline:', asset);
            }}
            buttonText="添加素材"
            size="sm"
            variant="outline"
          />
        </div>
      </div>
      
      {/* 时间轴主体 */}
      <div className="flex">
        {/* 轨道头部 */}
        <div 
          className="flex-shrink-0 bg-zinc-800"
          style={{ width: TRACK_HEADER_WIDTH }}
        >
          {/* 标尺占位 */}
          <div style={{ height: RULER_HEIGHT }} className="border-b border-zinc-700" />
          
          {/* 轨道头部 */}
          {timeline.tracks.map(renderTrackHeader)}
        </div>
        
        {/* 时间轴内容 */}
        <div className="flex-1 overflow-auto" style={{ maxHeight: '60vh' }}>
          <div className="relative">
            {/* 时间标尺 */}
            <div 
              className="relative bg-zinc-800 border-b border-zinc-700"
              style={{ 
                height: RULER_HEIGHT,
                width: Math.max(timeline.duration * PIXELS_PER_SECOND, 800)
              }}
            >
              {renderRuler()}
              {renderMarkers()}
            </div>
            
            {/* 轨道区域 */}
            <div
              ref={timelineRef}
              className="relative bg-zinc-900 cursor-pointer"
              style={{ 
                height: totalTrackHeight,
                width: Math.max(timeline.duration * PIXELS_PER_SECOND, 800)
              }}
              onClick={handleTimelineClick}
              onMouseMove={isResizing ? handleClipResize : undefined}
              onMouseUp={isResizing ? handleClipResizeEnd : undefined}
            >
              {/* 网格背景 */}
              <div className="absolute inset-0 opacity-10">
                {Array.from({ length: Math.ceil(timeline.duration) }, (_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 bottom-0 border-l border-zinc-600"
                    style={{ left: i * PIXELS_PER_SECOND }}
                  />
                ))}
              </div>
              
              {/* 轨道分隔线 */}
              {timeline.tracks.map((track, index) => {
                const y = timeline.tracks.slice(0, index + 1).reduce((sum, t) => sum + t.height, 0);
                return (
                  <div
                    key={`separator-${track.id}`}
                    className="absolute left-0 right-0 border-b border-zinc-700"
                    style={{ top: y }}
                  />
                );
              })}
              
              {/* 片段 */}
              {timeline.clips.map(renderClip)}
              
              {/* 播放头 */}
              {renderPlayhead()}
            </div>
          </div>
        </div>
      </div>
      
      {/* 选中片段控制面板 */}
      {selectedClips.length > 0 && (
        <div className="p-4 bg-zinc-800 border-t border-zinc-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-sm text-zinc-400">
                已选择 {selectedClips.length} 个片段
              </span>
              
              {selectedClips.length === 1 && timeline.clips.find(c => c.id === selectedClips[0]) && (
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-zinc-400">
                    开始: {formatTime(timeline.clips.find(c => c.id === selectedClips[0])!.start_time)}
                  </span>
                  <span className="text-zinc-400">
                    结束: {formatTime(timeline.clips.find(c => c.id === selectedClips[0])!.end_time)}
                  </span>
                  <span className="text-zinc-400">
                    时长: {formatTime(
                      timeline.clips.find(c => c.id === selectedClips[0])!.end_time - 
                      timeline.clips.find(c => c.id === selectedClips[0])!.start_time
                    )}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {/* TODO: 复制片段 */}}
                icon={Copy}
                title="复制"
              />
              
              <Button
                size="sm"
                variant="ghost"
                onClick={() => splitClipAtPlayhead(selectedClips[0])}
                icon={Scissors}
                title="在播放头处分割"
                disabled={selectedClips.length !== 1}
              />
              
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  selectedClips.forEach(clipId => {
                    // TODO: 删除片段
                  });
                  setSelectedClips([]);
                }}
                icon={Trash2}
                title="删除"
                className="text-red-400 hover:text-red-300"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfessionalTimelineEditor;