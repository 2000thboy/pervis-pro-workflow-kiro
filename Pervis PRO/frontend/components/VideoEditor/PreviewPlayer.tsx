import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw, Settings } from 'lucide-react';

interface PreviewPlayerProps {
  timelineClips: Array<{
    id: string;
    asset: {
      id: string;
      filename: string;
      mime_type: string;
      duration?: number;
    };
    start_time: number;
    end_time: number;
    trim_start: number;
    trim_end: number;
  }>;
  currentTime: number;
  isPlaying: boolean;
  totalDuration: number;
  onTimeUpdate: (time: number) => void;
  onPlayStateChange: (playing: boolean) => void;
}

const PreviewPlayer: React.FC<PreviewPlayerProps> = ({
  timelineClips,
  currentTime,
  isPlaying,
  totalDuration,
  onTimeUpdate,
  onPlayStateChange
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [volume, setVolume] = useState<number>(1);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [playbackRate, setPlaybackRate] = useState<number>(1);
  const [showControls, setShowControls] = useState<boolean>(true);
  const [currentClip, setCurrentClip] = useState<any>(null);
  
  // 播放速度选项
  const playbackRates = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2];
  
  // 根据当前时间找到对应的片段
  useEffect(() => {
    const activeClip = timelineClips.find(clip => 
      currentTime >= clip.start_time && currentTime < clip.end_time
    );
    
    if (activeClip && activeClip !== currentClip) {
      setCurrentClip(activeClip);
      
      // 更新视频源
      if (videoRef.current) {
        // 这里应该根据asset_id获取实际的视频文件路径
        // 暂时使用占位符
        const videoSrc = `/api/assets/${activeClip.asset.id}/stream`;
        videoRef.current.src = videoSrc;
        
        // 设置视频的播放位置
        const clipTime = currentTime - activeClip.start_time + activeClip.trim_start;
        videoRef.current.currentTime = clipTime;
      }
    }
  }, [currentTime, timelineClips, currentClip]);
  
  // 同步播放状态
  useEffect(() => {
    if (!videoRef.current) return;
    
    if (isPlaying && currentClip) {
      videoRef.current.play().catch(console.error);
    } else {
      videoRef.current.pause();
    }
  }, [isPlaying, currentClip]);
  
  // 视频时间更新
  const handleVideoTimeUpdate = () => {
    if (!videoRef.current || !currentClip) return;
    
    const videoTime = videoRef.current.currentTime;
    const timelineTime = currentClip.start_time + (videoTime - currentClip.trim_start);
    
    // 检查是否超出片段范围
    if (timelineTime >= currentClip.end_time) {
      // 跳到下一个片段或停止播放
      const nextClip = timelineClips.find(clip => clip.start_time >= currentClip.end_time);
      if (nextClip) {
        onTimeUpdate(nextClip.start_time);
      } else {
        onPlayStateChange(false);
        onTimeUpdate(totalDuration);
      }
    } else {
      onTimeUpdate(timelineTime);
    }
  };
  
  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
    }
  };
  
  const handleMuteToggle = () => {
    setIsMuted(!isMuted);
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
    }
  };
  
  const handlePlaybackRateChange = (rate: number) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  };
  
  const handleFullscreenToggle = () => {
    if (!document.fullscreenElement) {
      videoRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };
  
  const handleSeek = (event: React.MouseEvent<HTMLDivElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const percentage = x / rect.width;
    const newTime = percentage * totalDuration;
    onTimeUpdate(newTime);
  };
  
  // 时间格式化
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  // 控制栏自动隐藏
  useEffect(() => {
    let timeout: NodeJS.Timeout;
    
    const resetTimeout = () => {
      setShowControls(true);
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        if (isPlaying) {
          setShowControls(false);
        }
      }, 3000);
    };
    
    resetTimeout();
    
    return () => clearTimeout(timeout);
  }, [isPlaying]);
  
  return (
    <div 
      className="relative bg-black rounded-lg overflow-hidden group aspect-video"
      onMouseMove={() => setShowControls(true)}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      {/* 视频元素 */}
      {currentClip ? (
        <video
          ref={videoRef}
          className="w-full h-full object-contain"
          onTimeUpdate={handleVideoTimeUpdate}
          onPlay={() => onPlayStateChange(true)}
          onPause={() => onPlayStateChange(false)}
          onEnded={() => onPlayStateChange(false)}
          playsInline
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-zinc-800">
          <div className="text-center text-zinc-500">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-zinc-700 flex items-center justify-center">
              <Play size={24} />
            </div>
            <p className="text-lg font-medium">预览播放器</p>
            <p className="text-sm mt-1">添加素材到时间轴开始预览</p>
          </div>
        </div>
      )}
      
      {/* 播放按钮覆盖层 */}
      {!isPlaying && currentClip && (
        <div 
          className="absolute inset-0 flex items-center justify-center bg-black/20 cursor-pointer"
          onClick={() => onPlayStateChange(true)}
        >
          <div className="w-16 h-16 bg-amber-500/90 rounded-full flex items-center justify-center hover:bg-amber-500 transition-colors">
            <Play size={24} className="text-white ml-1" />
          </div>
        </div>
      )}
      
      {/* 控制栏 */}
      <div className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 transition-opacity duration-300 ${
        showControls ? 'opacity-100' : 'opacity-0'
      }`}>
        {/* 进度条 */}
        <div 
          className="w-full h-2 bg-white/20 rounded-full cursor-pointer mb-3 group"
          onClick={handleSeek}
        >
          <div 
            className="h-full bg-amber-500 rounded-full relative group-hover:bg-amber-400 transition-colors"
            style={{ width: `${totalDuration > 0 ? (currentTime / totalDuration) * 100 : 0}%` }}
          >
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
        
        {/* 控制按钮 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* 播放/暂停 */}
            <button
              onClick={() => onPlayStateChange(!isPlaying)}
              className="text-white hover:text-amber-400 transition-colors"
              disabled={!currentClip}
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>
            
            {/* 音量控制 */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleMuteToggle}
                className="text-white hover:text-amber-400 transition-colors"
              >
                {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
              </button>
              
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={isMuted ? 0 : volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                className="w-16 accent-amber-500"
              />
            </div>
            
            {/* 时间显示 */}
            <div className="text-white text-sm font-mono">
              {formatTime(currentTime)} / {formatTime(totalDuration)}
            </div>
            
            {/* 当前片段信息 */}
            {currentClip && (
              <div className="text-white text-sm bg-black/50 px-2 py-1 rounded">
                {currentClip.asset.filename}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {/* 播放速度 */}
            <div className="relative group">
              <button className="text-white hover:text-amber-400 transition-colors flex items-center gap-1">
                <Settings size={16} />
                <span className="text-xs">{playbackRate}x</span>
              </button>
              
              <div className="absolute bottom-full right-0 mb-2 bg-zinc-800 rounded-lg p-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none group-hover:pointer-events-auto">
                <div className="text-xs text-zinc-400 mb-2">播放速度</div>
                {playbackRates.map(rate => (
                  <button
                    key={rate}
                    onClick={() => handlePlaybackRateChange(rate)}
                    className={`block w-full text-left px-2 py-1 text-sm rounded transition-colors ${
                      rate === playbackRate 
                        ? 'bg-amber-500 text-white' 
                        : 'text-zinc-300 hover:bg-zinc-700'
                    }`}
                  >
                    {rate}x
                  </button>
                ))}
              </div>
            </div>
            
            {/* 重置 */}
            <button
              onClick={() => onTimeUpdate(0)}
              className="text-white hover:text-amber-400 transition-colors"
              title="回到开始"
            >
              <RotateCcw size={16} />
            </button>
            
            {/* 全屏 */}
            <button
              onClick={handleFullscreenToggle}
              className="text-white hover:text-amber-400 transition-colors"
            >
              <Maximize size={16} />
            </button>
          </div>
        </div>
      </div>
      
      {/* 全屏状态指示 */}
      {isFullscreen && (
        <div className="absolute top-4 right-4 bg-black/50 text-white px-2 py-1 rounded text-xs">
          按 ESC 退出全屏
        </div>
      )}
    </div>
  );
};

export default PreviewPlayer;