import React, { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize, RotateCcw, Settings } from 'lucide-react';

interface VideoPlayerProps {
  timelineId?: string;
  playhead: number;
  isPlaying: boolean;
  onPlayheadChange: (time: number) => void;
  onPlayStateChange: (playing: boolean) => void;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  timelineId,
  playhead,
  isPlaying,
  onPlayheadChange,
  onPlayStateChange
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [volume, setVolume] = useState<number>(1);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [duration, setDuration] = useState<number>(0);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [playbackRate, setPlaybackRate] = useState<number>(1);
  const [showControls, setShowControls] = useState<boolean>(true);
  
  // 播放速度选项
  const playbackRates = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2];
  
  // 同步播放状态
  useEffect(() => {
    if (!videoRef.current) return;
    
    if (isPlaying) {
      videoRef.current.play();
    } else {
      videoRef.current.pause();
    }
  }, [isPlaying]);
  
  // 同步播放头位置
  useEffect(() => {
    if (!videoRef.current) return;
    
    const video = videoRef.current;
    if (Math.abs(video.currentTime - playhead) > 0.1) {
      video.currentTime = playhead;
    }
  }, [playhead]);
  
  // 视频事件处理
  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };
  
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      onPlayheadChange(videoRef.current.currentTime);
    }
  };
  
  const handlePlay = () => {
    onPlayStateChange(true);
  };
  
  const handlePause = () => {
    onPlayStateChange(false);
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
    const newTime = percentage * duration;
    onPlayheadChange(newTime);
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
      className="relative bg-black rounded-lg overflow-hidden group"
      onMouseMove={() => setShowControls(true)}
      onMouseLeave={() => isPlaying && setShowControls(false)}
    >
      {/* 视频元素 */}
      <video
        ref={videoRef}
        className="w-full h-full object-contain"
        onLoadedMetadata={handleLoadedMetadata}
        onTimeUpdate={handleTimeUpdate}
        onPlay={handlePlay}
        onPause={handlePause}
        onEnded={() => onPlayStateChange(false)}
        playsInline
      >
        {/* TODO: 根据时间轴动态加载视频源 */}
        <source src="/api/preview/video" type="video/mp4" />
        您的浏览器不支持视频播放。
      </video>
      
      {/* 加载状态 */}
      {!duration && (
        <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/80">
          <div className="text-white text-center">
            <div className="animate-spin w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full mx-auto mb-2" />
            <div className="text-sm">加载预览...</div>
          </div>
        </div>
      )}
      
      {/* 播放按钮覆盖层 */}
      {!isPlaying && duration > 0 && (
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
            style={{ width: `${(playhead / duration) * 100}%` }}
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
              {formatTime(playhead)} / {formatTime(duration)}
            </div>
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
              onClick={() => onPlayheadChange(0)}
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

export default VideoPlayer;