
import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Beat, SceneGroup } from '../types';
import { 
  Play, Pause, SkipBack, SkipForward, 
  ZoomIn, ZoomOut, GripVertical, 
  Video, Mic, Type, Split, MoreHorizontal,
  Scissors
} from 'lucide-react';

interface TimelineProps {
  beats: Beat[];
  scenes: SceneGroup[];
  currentBeatId: string | null;
  currentTime: number;
  isPlaying: boolean;
  zoom: number; // pixels per second
  onSelectBeat: (id: string) => void;
  onDurationChange: (id: string, newDuration: number) => void;
  onTimeUpdate: (time: number | ((prev: number) => number)) => void;
  onPlayPause: (isPlaying: boolean) => void;
  onZoomChange: (zoom: number) => void;
}

// Utility to format time to MM:SS:FF (assuming 24fps)
const formatTimecode = (seconds: number) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const f = Math.floor((seconds % 1) * 24);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}:${f.toString().padStart(2, '0')}`;
};

export const Timeline: React.FC<TimelineProps> = ({ 
  beats, 
  scenes,
  currentBeatId, 
  currentTime, 
  isPlaying, 
  zoom, 
  onSelectBeat, 
  onDurationChange,
  onTimeUpdate,
  onPlayPause,
  onZoomChange
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rulerRef = useRef<HTMLCanvasElement>(null);
  const tracksScrollRef = useRef<HTMLDivElement>(null);
  
  // State
  const [scrollLeft, setScrollLeft] = useState(0);
  const [isScrubbing, setIsScrubbing] = useState(false);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  
  // Refs for Drag Logic
  const dragStartXRef = useRef<number>(0);
  const dragStartDurationRef = useRef<number>(0);

  const totalDuration = beats.reduce((acc, beat) => acc + beat.duration, 0);
  const TRACK_HEADER_WIDTH = 100; // px
  
  // Sync scroll between Ruler and Tracks
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const left = e.currentTarget.scrollLeft;
    setScrollLeft(left);
  };

  // --- Keyboard Shortcuts & Wheel ---
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
        if (!containerRef.current?.contains(e.target as Node)) return;
        
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            onZoomChange(Math.min(200, Math.max(10, zoom * delta)));
        } else if (e.shiftKey) {
            // Horizontal scroll via shift+wheel is handled natively by overflow-x, 
            // but we can enhance smooth scrolling here if needed.
        }
    };
    window.addEventListener('wheel', handleWheel, { passive: false });
    return () => window.removeEventListener('wheel', handleWheel);
  }, [zoom, onZoomChange]);

  // --- Canvas Ruler Rendering ---
  useEffect(() => {
    const canvas = rulerRef.current;
    if (!canvas || !tracksScrollRef.current) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Dimensions
    const width = tracksScrollRef.current.scrollWidth; // Use full scrollable width
    const height = 24;
    
    // Resize canvas to match actual scroll width to avoid blur, 
    // but we only render the visible part + buffer for performance in a real app.
    // For simplicity here, we size it to the viewport and apply translation.
    const viewportWidth = tracksScrollRef.current.clientWidth;
    canvas.width = viewportWidth;
    canvas.height = height;

    // Clear
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#27272a'; // zinc-800
    ctx.fillRect(0, 0, viewportWidth, height);

    ctx.strokeStyle = '#52525b'; // zinc-600
    ctx.fillStyle = '#a1a1aa'; // zinc-400
    ctx.font = '9px monospace';
    ctx.textBaseline = 'top';

    // Draw ticks
    // We need to draw based on scrollLeft
    const startSec = scrollLeft / zoom;
    const endSec = (scrollLeft + viewportWidth) / zoom;
    
    // Determine step size based on zoom
    let step = 1; // 1 second
    if (zoom < 20) step = 5;
    if (zoom < 10) step = 10;
    if (zoom > 60) step = 0.5;
    if (zoom > 100) step = 0.1;

    // Align start to step
    const firstTick = Math.floor(startSec / step) * step;

    for (let t = firstTick; t <= endSec; t += step) {
        const x = (t * zoom) - scrollLeft;
        
        // Major tick
        if (Number.isInteger(t)) {
             ctx.beginPath();
             ctx.moveTo(x, 12);
             ctx.lineTo(x, 24);
             ctx.stroke();
             // Draw time text every 5 or 1 second depending on density
             if (step >= 1 || Math.floor(t) % 1 === 0) {
                 ctx.fillText(formatTimecode(t).slice(3,8), x + 2, 2);
             }
        } else {
             // Minor tick
             ctx.beginPath();
             ctx.moveTo(x, 18);
             ctx.lineTo(x, 24);
             ctx.stroke();
        }
    }

  }, [zoom, scrollLeft, totalDuration]);

  // --- Playhead Scrubbing Logic ---
  const handleScrubStart = (e: React.MouseEvent) => {
      setIsScrubbing(true);
      onPlayPause(false);
      handleScrubMove(e);
  };

  const handleScrubMove = (e: React.MouseEvent) => {
      if (!tracksScrollRef.current) return;
      const rect = tracksScrollRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left + scrollLeft;
      const t = Math.max(0, x / zoom);
      onTimeUpdate(t);
  };

  const handleScrubEnd = () => {
      setIsScrubbing(false);
  };

  useEffect(() => {
      if (isScrubbing) {
          window.addEventListener('mousemove', handleScrubMove as any);
          window.addEventListener('mouseup', handleScrubEnd);
      }
      return () => {
          window.removeEventListener('mousemove', handleScrubMove as any);
          window.removeEventListener('mouseup', handleScrubEnd);
      };
  }, [isScrubbing, scrollLeft, zoom]);


  // --- Clip Resize Logic ---
  const handleClipResizeStart = (e: React.MouseEvent, beat: Beat) => {
      e.stopPropagation();
      setDraggingId(beat.id);
      dragStartXRef.current = e.clientX;
      dragStartDurationRef.current = beat.duration;
  };

  useEffect(() => {
      const handleMouseMove = (e: MouseEvent) => {
          if (!draggingId) return;
          const deltaX = e.clientX - dragStartXRef.current;
          const deltaSec = deltaX / zoom;
          const newDur = Math.max(0.5, dragStartDurationRef.current + deltaSec);
          onDurationChange(draggingId, newDur);
      };
      const handleMouseUp = () => {
          setDraggingId(null);
      };
      if (draggingId) {
          window.addEventListener('mousemove', handleMouseMove);
          window.addEventListener('mouseup', handleMouseUp);
      }
      return () => {
          window.removeEventListener('mousemove', handleMouseMove);
          window.removeEventListener('mouseup', handleMouseUp);
      };
  }, [draggingId, zoom, onDurationChange]);


  // --- Playback Interval ---
  useEffect(() => {
    let interval: number;
    if (isPlaying) {
      interval = window.setInterval(() => {
        onTimeUpdate(prev => {
          if (prev >= totalDuration) {
            onPlayPause(false);
            return prev;
          }
          return prev + 0.033;
        });
      }, 33);
    }
    return () => clearInterval(interval);
  }, [isPlaying, totalDuration]);


  // --- Render Helpers ---
  const TrackHeader = ({ title, icon: Icon, color }: { title: string, icon: any, color: string }) => (
      <div className="h-full border-b border-zinc-800 bg-zinc-900 flex items-center px-2 gap-2 text-zinc-400 select-none group hover:bg-zinc-800 transition-colors">
          <div className={`p-1 rounded ${color} bg-opacity-20`}>
             <Icon size={12} className={color.replace('bg-', 'text-')} />
          </div>
          <span className="text-[10px] font-bold tracking-wider">{title}</span>
          <div className="ml-auto opacity-0 group-hover:opacity-100 flex gap-1">
             <button className="p-1 hover:bg-black/40 rounded"><MoreHorizontal size={10}/></button>
          </div>
      </div>
  );

  return (
    <div className="flex-1 flex flex-col bg-zinc-950 select-none" ref={containerRef}>
      
      {/* 1. Toolbar */}
      <div className="h-9 border-b border-zinc-800 flex items-center justify-between px-2 bg-zinc-900/80">
          <div className="flex items-center gap-2">
               {/* Transport Controls */}
               <div className="flex items-center bg-zinc-950 rounded-md border border-zinc-800 p-0.5">
                   <button className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800" onClick={() => onTimeUpdate(0)}><SkipBack size={12}/></button>
                   <button 
                       className={`w-6 h-6 flex items-center justify-center rounded mx-0.5 ${isPlaying ? 'bg-indigo-600 text-white' : 'text-zinc-300 hover:bg-zinc-800'}`}
                       onClick={() => onPlayPause(!isPlaying)}
                   >
                       {isPlaying ? <Pause size={10} fill="currentColor"/> : <Play size={10} fill="currentColor" className="ml-0.5"/>}
                   </button>
                   <button className="p-1 text-zinc-400 hover:text-white rounded hover:bg-zinc-800" onClick={() => onTimeUpdate(totalDuration)}><SkipForward size={12}/></button>
               </div>
               
               {/* Timecode Display */}
               <div className="font-mono text-sm font-bold text-indigo-400 bg-black px-2 py-0.5 rounded border border-zinc-800 ml-2">
                   {formatTimecode(currentTime)}
               </div>

               {/* Tools (Visual Only for now) */}
               <div className="h-4 w-px bg-zinc-700 mx-2"></div>
               <div className="flex gap-0.5">
                   <button className="p-1.5 bg-zinc-800 text-yellow-500 rounded"><GripVertical size={12}/></button>
                   <button className="p-1.5 text-zinc-400 hover:text-white hover:bg-zinc-800 rounded"><Scissors size={12}/></button>
               </div>
          </div>

          <div className="flex items-center gap-2">
               <ZoomOut size={12} className="text-zinc-500 cursor-pointer" onClick={() => onZoomChange(Math.max(10, zoom / 1.2))} />
               <input 
                  type="range" min="10" max="200" value={zoom} onChange={(e) => onZoomChange(Number(e.target.value))} 
                  className="w-20 h-1 bg-zinc-700 rounded-lg accent-zinc-500 cursor-pointer"
               />
               <ZoomIn size={12} className="text-zinc-500 cursor-pointer" onClick={() => onZoomChange(Math.min(200, zoom * 1.2))} />
          </div>
      </div>

      {/* 2. Timeline Body */}
      <div className="flex-1 flex overflow-hidden relative">
          
          {/* Left: Track Headers */}
          <div 
            className="flex-shrink-0 border-r border-zinc-800 bg-zinc-900 z-20 flex flex-col"
            style={{ width: TRACK_HEADER_WIDTH }}
          >
               <div className="h-6 border-b border-zinc-800 bg-zinc-950"></div> {/* Ruler Spacer */}
               <div className="flex-1 flex flex-col">
                   <div className="h-6"><TrackHeader title="SCENE" icon={Split} color="text-yellow-500" /></div>
                   <div className="h-28"><TrackHeader title="VIDEO 1" icon={Video} color="text-indigo-400" /></div>
                   <div className="h-16"><TrackHeader title="AUDIO 1" icon={Mic} color="text-emerald-400" /></div>
               </div>
          </div>

          {/* Right: Ruler & Tracks */}
          <div className="flex-1 flex flex-col relative min-w-0 bg-zinc-950/50">
               
               {/* Timeline Ruler */}
               <div 
                  className="h-6 w-full cursor-ew-resize relative border-b border-zinc-800"
                  onMouseDown={handleScrubStart}
               >
                   <canvas ref={rulerRef} className="absolute inset-0 block h-full w-full" />
                   {/* Playhead Cap */}
                   <div 
                        className="absolute top-0 w-3 h-full -ml-1.5 z-30 pointer-events-none"
                        style={{ left: (currentTime * zoom) - scrollLeft }}
                   >
                        <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-yellow-500 mx-auto"></div>
                   </div>
               </div>

               {/* Tracks Container */}
               <div 
                  ref={tracksScrollRef}
                  className="flex-1 overflow-x-auto overflow-y-hidden relative custom-scrollbar scroll-smooth"
                  onScroll={handleScroll}
               >
                  <div 
                      className="min-h-full relative pb-10"
                      style={{ width: Math.max((totalDuration * zoom) + 500, tracksScrollRef.current?.clientWidth || 0) }}
                  >
                       
                       {/* Playhead Line */}
                       <div 
                            className="absolute top-0 bottom-0 w-px bg-yellow-500 z-40 pointer-events-none"
                            style={{ left: currentTime * zoom }}
                       ></div>

                       {/* TRACK 1: Scene Structure */}
                       <div className="h-6 flex relative w-full border-b border-zinc-800/50 bg-black/20">
                           {scenes.map((scene, idx) => (
                               <div 
                                  key={scene.id}
                                  className={`h-full border-r border-zinc-900/50 flex items-center px-2 overflow-hidden whitespace-nowrap text-[9px] font-bold ${idx%2===0 ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-800/80 text-zinc-500'}`}
                                  style={{ width: scene.duration * zoom }}
                               >
                                  {scene.title}
                               </div>
                           ))}
                       </div>

                       {/* TRACK 2: Video (Main Beats) */}
                       <div className="h-28 flex relative w-full border-b border-zinc-800 bg-zinc-900/30">
                           {beats.map((beat, idx) => {
                               const isActive = beat.id === currentBeatId;
                               const asset = beat.assets.find(a => a.id === beat.mainAssetId) || beat.assets[0];
                               
                               return (
                                   <div 
                                       key={beat.id}
                                       className={`group relative h-full flex-shrink-0 border-r border-black overflow-hidden cursor-pointer transition-colors ${
                                           isActive 
                                           ? 'bg-indigo-900/30 ring-2 ring-indigo-500 z-10' 
                                           : 'bg-zinc-800 hover:bg-zinc-700'
                                       }`}
                                       style={{ width: beat.duration * zoom }}
                                       onMouseDown={(e) => { e.stopPropagation(); onSelectBeat(beat.id); }}
                                   >
                                       {/* Thumbnail Strip (Approximation) */}
                                       <div className="h-16 w-full relative bg-black">
                                           {asset ? (
                                               asset.type === 'video' ? (
                                                   <video src={asset.thumbnailUrl} className="w-full h-full object-cover opacity-80" muted />
                                               ) : (
                                                   <img src={asset.thumbnailUrl} className="w-full h-full object-cover opacity-80" />
                                               )
                                           ) : (
                                               <div className="w-full h-full flex items-center justify-center text-zinc-700 text-[10px]">NO MEDIA</div>
                                           )}
                                           
                                           {/* Beat Index */}
                                           <div className="absolute top-1 left-1 bg-black/50 text-white text-[8px] px-1 rounded">
                                               {beat.order + 1}
                                           </div>
                                       </div>

                                       {/* Script Content Preview */}
                                       <div className="p-1.5 h-12 border-t border-zinc-900/50">
                                            <p className={`text-[9px] leading-tight line-clamp-2 font-serif ${isActive ? 'text-indigo-200' : 'text-zinc-400'}`}>
                                                {beat.content}
                                            </p>
                                       </div>

                                       {/* Resize Handle (Right) */}
                                       <div 
                                          className="absolute top-0 right-0 bottom-0 w-2 cursor-col-resize hover:bg-yellow-500/50 z-20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100"
                                          onMouseDown={(e) => handleClipResizeStart(e, beat)}
                                       >
                                            <div className="w-0.5 h-4 bg-white/50 rounded-full"></div>
                                       </div>
                                   </div>
                               );
                           })}
                       </div>

                       {/* TRACK 3: Audio Placeholder */}
                       <div className="h-16 flex relative w-full border-b border-zinc-800 bg-zinc-900/30 opacity-50">
                           {/* Simulated Audio Waveform Blocks */}
                           {scenes.map((scene, idx) => (
                                <div 
                                    key={`audio-${scene.id}`}
                                    className="h-full border-r border-zinc-900 flex items-center px-2 bg-emerald-900/20"
                                    style={{ width: scene.duration * zoom }}
                                >
                                    <div className="w-full h-8 flex items-center gap-0.5 overflow-hidden opacity-30">
                                        {Array.from({ length: Math.floor(scene.duration * 2) }).map((_, i) => (
                                            <div key={i} className="w-1 bg-emerald-500 rounded-full" style={{ height: `${20 + Math.random() * 60}%` }}></div>
                                        ))}
                                    </div>
                                </div>
                           ))}
                       </div>

                  </div>
               </div>
          </div>
      </div>
    </div>
  );
};
