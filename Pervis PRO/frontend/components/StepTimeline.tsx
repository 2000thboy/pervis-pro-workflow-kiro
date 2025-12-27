
import React, { useState } from 'react';
import { Project, SceneGroup, Beat } from '../types';
import { Timeline } from './Timeline';
import { MonitorPlay, Settings, Download, Layers } from 'lucide-react';
import { Preview } from './Preview';
import { useLanguage } from './LanguageContext';
import { ExportDialog } from './Export';

interface Props {
  project: Project;
  scenes: SceneGroup[];
  onUpdateBeats: (beats: Beat[]) => void;
}

export const StepTimeline: React.FC<Props> = ({ project, scenes, onUpdateBeats }) => {
  const { t } = useLanguage();
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [zoom, setZoom] = useState(40); // Initial zoom: 40px per second
  const [currentBeatId, setCurrentBeatId] = useState<string | null>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);

  const totalDuration = project.beats.reduce((acc, b) => acc + b.duration, 0);

  // Derive active beat from current time if no manual selection
  const activeBeat = project.beats.find(b => b.id === currentBeatId) || (() => {
      let t = 0;
      for (const beat of project.beats) {
          if (currentTime >= t && currentTime < t + beat.duration) return beat;
          t += beat.duration;
      }
      return null;
  })();

  // Calculate local start time for the active beat
  const beatStartTime = (() => {
      let t = 0;
      if(!activeBeat) return 0;
      for (const b of project.beats) {
          if (b.id === activeBeat.id) return t;
          t += b.duration;
      }
      return 0;
  })();

  const handleDurationChange = (beatId: string, newDur: number) => {
      const newBeats = project.beats.map(b => b.id === beatId ? {...b, duration: newDur} : b);
      onUpdateBeats(newBeats);
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950">
        
        {/* Top: Preview Monitor Area */}
        <div className="flex-[2] min-h-[300px] flex bg-black border-b border-zinc-800 relative">
             
             {/* Main Viewer */}
             <div className="flex-1 flex items-center justify-center relative p-8">
                 <div className="aspect-video h-full shadow-2xl bg-zinc-900 border border-zinc-800 overflow-hidden relative">
                    <Preview 
                        activeBeat={activeBeat || null}
                        currentTime={currentTime}
                        beatStartTime={beatStartTime}
                        previewMode="fit"
                        previewGrid={0}
                        onToggleMode={() => {}}
                        onToggleGrid={() => {}}
                        onPrevFrame={() => setCurrentTime(Math.max(0, currentTime - 0.041))} // 24fps
                        onNextFrame={() => setCurrentTime(Math.min(totalDuration, currentTime + 0.041))}
                        demoMode={false}
                    />
                 </div>
             </div>

             {/* Right Panel: Scene/Shot Info (Floating or Sidebar) */}
             <div className="w-80 border-l border-zinc-800 bg-zinc-900/50 p-6 flex flex-col">
                 <div className="mb-6">
                     <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-2">{t('timeline.current_shot')}</h3>
                     {activeBeat ? (
                         <div className="space-y-4">
                             <div className="bg-zinc-800 p-3 rounded border border-zinc-700">
                                 <div className="flex justify-between items-center mb-2">
                                     <span className="text-yellow-500 font-bold text-sm">
                                         {activeBeat.tags?.scene_slug || "SCENE"}
                                     </span>
                                     <span className="text-[10px] bg-zinc-950 px-1.5 py-0.5 rounded text-zinc-400">
                                         Shot {activeBeat.order + 1}
                                     </span>
                                 </div>
                                 <p className="text-sm text-zinc-200 font-serif leading-relaxed">
                                     {activeBeat.content}
                                 </p>
                             </div>
                             
                             <div className="grid grid-cols-2 gap-2">
                                 <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                                     <label className="text-[9px] text-zinc-500 block">{t('timeline.duration')}</label>
                                     <span className="text-xs font-mono text-zinc-300">{activeBeat.duration.toFixed(2)}s</span>
                                 </div>
                                 <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                                     <label className="text-[9px] text-zinc-500 block">{t('timeline.global_in')}</label>
                                     <span className="text-xs font-mono text-zinc-300">{beatStartTime.toFixed(2)}s</span>
                                 </div>
                             </div>
                         </div>
                     ) : (
                         <div className="text-zinc-600 text-xs italic">
                             Playhead is at {currentTime.toFixed(2)}s. No clip selected.
                         </div>
                     )}
                 </div>

                 <div className="mt-auto">
                     <button className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-xs font-bold text-zinc-300 rounded transition-colors flex items-center justify-center gap-2 mb-2">
                         <Settings size={14} /> {t('timeline.seq_settings')}
                     </button>
                     <button 
                         onClick={() => setShowExportDialog(true)}
                         className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white rounded transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-900/20"
                     >
                         <Download size={14} /> {t('timeline.export')}
                     </button>
                 </div>
             </div>
        </div>

        {/* Bottom: Timeline Area */}
        <div className="h-[360px] flex flex-col flex-shrink-0 z-10 shadow-[0_-5px_20px_rgba(0,0,0,0.5)]">
            <Timeline 
                beats={project.beats}
                scenes={scenes}
                currentBeatId={activeBeat?.id || null}
                currentTime={currentTime}
                isPlaying={isPlaying}
                zoom={zoom}
                onSelectBeat={(id) => {
                    setCurrentBeatId(id);
                    // Also jump playhead to start of this beat
                    // calculate start time
                    let t = 0;
                    for(let b of project.beats) {
                        if(b.id === id) break;
                        t += b.duration;
                    }
                    setCurrentTime(t);
                }}
                onDurationChange={handleDurationChange}
                onTimeUpdate={setCurrentTime}
                onPlayPause={setIsPlaying}
                onZoomChange={setZoom}
            />
        </div>

        {/* Export Dialog */}
        <ExportDialog
            isOpen={showExportDialog}
            onClose={() => setShowExportDialog(false)}
            mode="timeline"
            projectId={project.id}
            timelineId={project.id}
            beats={project.beats.map(b => ({ id: b.id, title: b.content.substring(0, 30) }))}
            scenes={scenes.map(s => ({ id: s.id, title: s.title }))}
        />
    </div>
  );
};
