
import React, { useEffect, useState, useRef } from 'react';
import { Beat } from '../types';
import { Maximize, Minimize, Grid3x3, Grid, ChevronLeft, ChevronRight, Monitor } from 'lucide-react';

interface PreviewProps {
  activeBeat: Beat | null;
  currentTime: number;
  beatStartTime: number;
  previewMode: 'fit' | 'fill';
  previewGrid: 0 | 3 | 4;
  onToggleMode: () => void;
  onToggleGrid: () => void;
  onPrevFrame: () => void;
  onNextFrame: () => void;
  demoMode?: boolean;
}

export const Preview: React.FC<PreviewProps> = ({
  activeBeat,
  currentTime,
  beatStartTime,
  previewMode,
  previewGrid,
  onToggleMode,
  onToggleGrid,
  onPrevFrame,
  onNextFrame,
  demoMode
}) => {
  const [assetIndex, setAssetIndex] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Slideshow Sequencer & Video Logic
  useEffect(() => {
    if (!activeBeat || activeBeat.assets.length <= 1) {
        setAssetIndex(0);
        return;
    }

    // Determine local time within the beat
    const localTime = Math.max(0, currentTime - beatStartTime);
    
    // Switch asset every 0.3s (Storyreel mode) if they are images
    // If it's a single video asset, logic is different, but here we handle "multiple assets"
    const calculatedIndex = Math.floor(localTime / 0.3);
    
    // Clamp to valid range (stay on last asset if time exceeds sequence)
    const index = Math.min(calculatedIndex, activeBeat.assets.length - 1);
    
    if (index !== assetIndex) {
        setAssetIndex(index);
    }
  }, [currentTime, beatStartTime, activeBeat]);

  const displayAsset = activeBeat 
    ? (activeBeat.assets.length > 0 ? activeBeat.assets[assetIndex] : null) 
    : null;

  // Video Loop Logic for Trimming
  // Add an event listener to the video element to enforce the loop
  useEffect(() => {
    const vid = videoRef.current;
    if (!vid) return;

    const handleTimeUpdate = () => {
        if (!displayAsset || displayAsset.type !== 'video') return;
        const inPoint = displayAsset.inPoint || 0;
        const outPoint = displayAsset.outPoint || vid.duration;

        // If video is outside trim range, loop back to inPoint
        if (vid.currentTime < inPoint) vid.currentTime = inPoint;
        if (outPoint > 0 && vid.currentTime > outPoint) vid.currentTime = inPoint;
    };

    vid.addEventListener('timeupdate', handleTimeUpdate);
    return () => vid.removeEventListener('timeupdate', handleTimeUpdate);
  }, [displayAsset]);

  const renderGrid = () => {
    if (previewGrid === 0) return null;
    return (
      <div className="absolute inset-0 pointer-events-none z-20 flex flex-col">
          {Array.from({ length: previewGrid }).map((_, r) => (
             <div key={r} className="flex-1 flex border-b border-white/20 last:border-0">
                {Array.from({ length: previewGrid }).map((_, c) => (
                    <div key={c} className="flex-1 border-r border-white/20 last:border-0"></div>
                ))}
             </div>
          ))}
      </div>
    );
  };

  return (
    <div className="relative w-full h-full bg-black flex flex-col group">
        {/* Main Display Area */}
        <div className="flex-1 relative overflow-hidden flex items-center justify-center bg-zinc-900/20">
            {displayAsset ? (
                displayAsset.type === 'video' ? (
                     <video 
                        ref={videoRef}
                        src={displayAsset.mediaUrl} 
                        className={`w-full h-full ${previewMode === 'fit' ? 'object-contain' : 'object-cover'}`} 
                        muted 
                        autoPlay
                        loop
                     />
                ) : (
                     <img src={displayAsset.mediaUrl} className={`w-full h-full ${previewMode === 'fit' ? 'object-contain' : 'object-cover'}`} />
                )
            ) : (
                 <div className="text-zinc-600 flex flex-col items-center select-none">
                    <Monitor size={48} strokeWidth={1} />
                    <span className="mt-2 text-sm">{activeBeat ? "暂无画面" : "未选择节拍"}</span>
                 </div>
            )}
            
            {/* Demo Watermark */}
            {demoMode && (
                <div className="absolute top-4 right-4 text-white/20 text-4xl font-black uppercase pointer-events-none rotate-12 z-10 select-none">
                    DEMO MODE
                </div>
            )}
            
            {/* Grid Overlay */}
            {renderGrid()}

            {/* Info Overlay */}
            {activeBeat && (
                <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/60 px-4 py-1.5 rounded-full text-white text-xs backdrop-blur-md z-30 font-mono flex items-center gap-3 border border-white/10">
                    <span className="font-bold text-indigo-300">{activeBeat.tags?.scene_slug || `SCENE ${activeBeat.order + 1}`}</span>
                    {activeBeat.assets.length > 1 && (
                        <span className="text-zinc-400">
                           CAM {assetIndex + 1}/{activeBeat.assets.length}
                        </span>
                    )}
                    {displayAsset?.inPoint !== undefined && (
                        <span className="text-yellow-500 text-[9px] border border-yellow-500/50 px-1 rounded">TRIMMED</span>
                    )}
                </div>
            )}
        </div>

        {/* Mini Toolbar */}
        <div className="h-10 bg-zinc-950 border-t border-zinc-800 flex items-center justify-between px-4 z-40 select-none">
            <div className="flex items-center gap-1">
                 <button onClick={() => { onPrevFrame(); }} className="p-1.5 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors" title="上一帧 (-0.04s)">
                    <ChevronLeft size={16} />
                 </button>
                 <button onClick={() => { onNextFrame(); }} className="p-1.5 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors" title="下一帧 (+0.04s)">
                    <ChevronRight size={16} />
                 </button>
            </div>
            
            <div className="flex items-center gap-3">
                <button onClick={() => { onToggleGrid(); }} className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-zinc-800 text-xs text-zinc-400 hover:text-white transition-colors">
                    {previewGrid === 0 ? <Grid size={14}/> : <Grid3x3 size={14}/>}
                    <span className="font-medium">{previewGrid === 0 ? '网格: 关' : `${previewGrid}x${previewGrid}`}</span>
                </button>
                <div className="w-px h-4 bg-zinc-800"></div>
                <button onClick={() => { onToggleMode(); }} className="flex items-center gap-1.5 px-2 py-1 rounded hover:bg-zinc-800 text-xs text-zinc-400 hover:text-white transition-colors">
                    {previewMode === 'fit' ? <Maximize size={14}/> : <Minimize size={14}/>}
                    <span className="font-medium">{previewMode === 'fit' ? '适应' : '填充'}</span>
                </button>
            </div>
        </div>
    </div>
  );
};
