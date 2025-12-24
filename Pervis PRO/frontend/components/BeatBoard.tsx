
import React, { useRef, useEffect } from 'react';
import { Beat, SceneGroup } from '../types';
import { BeatCard } from './BeatCard';
import { Film } from 'lucide-react';

interface BeatBoardProps {
  scenes: SceneGroup[];
  currentBeatId: string | null;
  onSelectBeat: (beatId: string) => void;
}

export const BeatBoard: React.FC<BeatBoardProps> = ({ 
  scenes, 
  currentBeatId, 
  onSelectBeat
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logic for board
  useEffect(() => {
    if (currentBeatId) {
        const el = document.getElementById(`board-beat-${currentBeatId}`);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
    }
  }, [currentBeatId]);

  return (
    <div className="flex-1 overflow-y-auto p-8 pb-32 bg-zinc-950 scrollbar-thin scrollbar-thumb-zinc-800" ref={containerRef}>
      {scenes.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-zinc-600">
              <Film size={48} strokeWidth={1} className="mb-4 opacity-20" />
              <p>暂无场次。请在左侧解析剧本。</p>
          </div>
      )}

      <div className="flex flex-col gap-10 max-w-[1600px] mx-auto">
          {scenes.map((scene, sceneIdx) => (
              <div key={scene.id} className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards" style={{ animationDelay: `${sceneIdx * 50}ms` }}>
                  {/* Scene Header */}
                  <div className="flex items-center gap-3 mb-4 sticky top-0 z-20 bg-zinc-950/90 backdrop-blur-sm py-2 border-b border-zinc-800/50">
                      <div className="w-1.5 h-8 bg-indigo-500 rounded-full"></div>
                      <div>
                          <h3 className="text-sm font-bold text-zinc-200 uppercase tracking-wide">
                              {scene.title}
                          </h3>
                          <div className="flex items-center gap-2 text-[10px] text-zinc-500 mt-0.5">
                              <span>第 {sceneIdx + 1} 场</span>
                              <span>•</span>
                              <span>{scene.beats.length} 个镜头</span>
                              <span>•</span>
                              <span>{scene.duration.toFixed(1)}s</span>
                              {scene.beats[0]?.tags?.primary_emotion && (
                                  <>
                                    <span>•</span>
                                    <span className="text-indigo-400">{scene.beats[0].tags.primary_emotion}</span>
                                  </>
                              )}
                          </div>
                      </div>
                  </div>

                  {/* Shot Container (Flow Layout) */}
                  <div className="flex flex-wrap gap-4 pl-4">
                      {scene.beats.map((beat, beatIdx) => (
                          <div id={`board-beat-${beat.id}`} key={beat.id}>
                            <BeatCard 
                                beat={beat}
                                isSelected={beat.id === currentBeatId}
                                onSelect={() => onSelectBeat(beat.id)}
                                indexInScene={beatIdx}
                            />
                          </div>
                      ))}
                      
                      {/* "Add Shot" Ghost Card (Visual Hint) */}
                      <div className="w-[220px] aspect-video border border-dashed border-zinc-800 rounded-md flex items-center justify-center text-zinc-700 hover:border-zinc-600 hover:bg-zinc-900 transition-colors cursor-pointer group">
                          <span className="text-2xl font-light group-hover:scale-110 transition-transform">+</span>
                      </div>
                  </div>
              </div>
          ))}
      </div>
    </div>
  );
};
