import React, { useState, useEffect } from 'react';
import { SceneGroup, Beat, Asset } from '../types';
import { 
    ArrowRight, 
    Image as ImageIcon, 
    MoreHorizontal,
    GripHorizontal,
    Video
} from 'lucide-react';
import { searchVisualAssets } from '../services/apiClient';
import { useLanguage } from './LanguageContext';
import { Inspector } from './Inspector';

interface Props {
  scenes: SceneGroup[];
  beats: Beat[];
  onUpdateBeat: (beat: Beat) => void;
  onNext: () => void;
}

export const StepBeatBoard: React.FC<Props> = ({ scenes, beats, onUpdateBeat, onNext }) => {
  const { t } = useLanguage();
  const [selectedBeatId, setSelectedBeatId] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  
  // Inspector State
  const [previewMode, setPreviewMode] = useState<'fit' | 'fill'>('fill');
  const [previewGrid, setPreviewGrid] = useState<0 | 3 | 4>(0);
  
  // Local state for the prompt input
  const [localPrompt, setLocalPrompt] = useState("");

  const selectedBeat = beats.find(b => b.id === selectedBeatId);

  // Sync local prompt when selection changes
  useEffect(() => {
      if (selectedBeat) {
          setLocalPrompt(selectedBeat.tags?.visual_notes || selectedBeat.content);
      } else {
          setLocalPrompt("");
      }
  }, [selectedBeatId]);

  const handleSelectBeat = (beatId: string) => {
      setSelectedBeatId(beatId);
      const el = document.getElementById(`beat-card-${beatId}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
  };

  const handleSearch = async () => {
      if (!selectedBeat) return;
      setIsSearching(true);
      try {
          const updatedTags = { ...selectedBeat.tags, visual_notes: localPrompt };
          const newCandidates = await searchVisualAssets(localPrompt);
          
          onUpdateBeat({ 
              ...selectedBeat, 
              tags: updatedTags,
              candidates: newCandidates 
          });
      } catch (e) {
          console.error(e);
      } finally {
          setIsSearching(false);
      }
  };

  const handleAddCandidate = (asset: Asset) => {
      if (!selectedBeat) return;
      // Add to assets list and make it main
      const existing = selectedBeat.assets.find(a => a.id === asset.id);
      let newAssets = selectedBeat.assets;
      if (!existing) {
          newAssets = [...selectedBeat.assets, asset];
      }
      onUpdateBeat({ ...selectedBeat, assets: newAssets, mainAssetId: asset.id });
  };

  const getProgress = () => {
      const done = beats.filter(b => b.mainAssetId).length;
      return Math.round((done / beats.length) * 100);
  };

  return (
    <div className="flex h-full bg-zinc-950 overflow-hidden">
        
        {/* --- LEFT: MAIN KANBAN BOARD --- */}
        <div className="flex-1 flex flex-col min-w-0 bg-zinc-950/50">
            
            {/* Toolbar */}
            <div className="h-14 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-900/80 backdrop-blur z-20 flex-shrink-0">
                <div className="flex items-center gap-4">
                     <span className="text-sm font-bold text-zinc-300">{t('board.title')}</span>
                     <div className="h-4 w-px bg-zinc-700"></div>
                     <div className="flex items-center gap-2 text-xs">
                        <span className="text-zinc-500">{t('board.progress')}:</span>
                        <div className="w-24 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                            <div className="h-full bg-yellow-500 transition-all duration-500" style={{ width: `${getProgress()}%` }}></div>
                        </div>
                        <span className="text-yellow-500 font-bold">{getProgress()}%</span>
                     </div>
                </div>
                <button 
                    onClick={onNext} 
                    className="flex items-center gap-2 px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded shadow-lg shadow-indigo-900/20 transition-all"
                >
                    {t('board.enter_timeline')} <ArrowRight size={14} />
                </button>
            </div>

            {/* Board Scroll Area */}
            <div className="flex-1 overflow-x-auto overflow-y-hidden p-6 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent">
                <div className="flex gap-6 h-full">
                    {scenes.map((scene, sIdx) => (
                        <div key={scene.id} className="flex flex-col w-[320px] h-full flex-shrink-0 bg-zinc-900/40 border border-zinc-800/50 rounded-xl overflow-hidden">
                            
                            {/* Scene Header */}
                            <div className="p-3 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between group">
                                <div className="flex items-center gap-2">
                                    <span className="bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold">{t('board.scene')} {sIdx + 1}</span>
                                    <span className="text-xs font-bold text-zinc-300 truncate max-w-[180px]" title={scene.title}>{scene.title}</span>
                                </div>
                                <MoreHorizontal size={14} className="text-zinc-600 opacity-0 group-hover:opacity-100 cursor-pointer hover:text-white" />
                            </div>

                            {/* Beats Stack */}
                            <div className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin scrollbar-thumb-zinc-800">
                                {scene.beats.map((beat) => {
                                    const isSelected = selectedBeatId === beat.id;
                                    const activeAsset = beat.assets.find(a => a.id === beat.mainAssetId) || beat.assets[0];
                                    const displayUrl = activeAsset?.thumbnailUrl;
                                    
                                    return (
                                        <div 
                                            key={beat.id}
                                            id={`beat-card-${beat.id}`}
                                            onClick={() => handleSelectBeat(beat.id)}
                                            className={`relative group rounded-lg overflow-hidden border transition-all cursor-pointer ${
                                                isSelected 
                                                ? 'ring-2 ring-indigo-500 border-transparent shadow-[0_0_20px_rgba(99,102,241,0.3)] z-10' 
                                                : 'border-zinc-800 hover:border-zinc-600 bg-zinc-950'
                                            }`}
                                        >
                                            {/* Visual Area */}
                                            <div className="aspect-video bg-black relative">
                                                {displayUrl ? (
                                                    activeAsset?.type === 'video' ? (
                                                        <video src={displayUrl} className="w-full h-full object-cover opacity-90" muted />
                                                    ) : (
                                                        <img src={displayUrl} className="w-full h-full object-cover opacity-90" />
                                                    )
                                                ) : (
                                                    <div className="w-full h-full flex flex-col items-center justify-center text-zinc-700 pattern-grid">
                                                        <ImageIcon size={24} strokeWidth={1} />
                                                        <span className="text-[9px] mt-1 font-mono uppercase">Empty Slot</span>
                                                    </div>
                                                )}
                                                
                                                {/* Status Badges */}
                                                {activeAsset?.type === 'video' && (
                                                    <div className="absolute top-2 right-2 text-white/70 bg-black/50 p-0.5 rounded">
                                                        <Video size={10} />
                                                    </div>
                                                )}

                                                <div className={`absolute inset-0 bg-black/50 flex items-center justify-center transition-opacity duration-200 ${isSelected ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'}`}>
                                                    <span className="text-[10px] text-white font-bold border border-white/30 px-2 py-1 rounded-full backdrop-blur-sm">Click to Edit</span>
                                                </div>
                                            </div>

                                            {/* Content Area */}
                                            <div className="p-3 bg-zinc-900">
                                                <div className="flex justify-between items-start mb-1">
                                                    <div className="bg-zinc-800 text-[9px] font-bold text-zinc-400 px-1 rounded">Shot {beat.order + 1}</div>
                                                    <span className="text-[9px] font-mono text-zinc-500">{beat.duration}s</span>
                                                </div>
                                                <p className={`text-[10px] line-clamp-3 leading-relaxed ${isSelected ? 'text-zinc-200' : 'text-zinc-400'}`}>
                                                    {beat.content}
                                                </p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* --- RIGHT: INSPECTOR & AI --- */}
        <div className="w-[400px] border-l border-zinc-800 bg-zinc-900 flex flex-col z-30 shadow-2xl">
             {selectedBeat ? (
                 <Inspector 
                    selectedBeat={selectedBeat}
                    currentTime={0} // Not used in board mode extensively
                    beatStartTime={0}
                    totalDuration={100}
                    projectId="" // Pass if needed
                    projectLibrary={[]} // Pass if needed for lookup, though mostly handled inside
                    onUpdateBeat={onUpdateBeat}
                    onRegisterAsset={() => {}} // Placeholder
                    previewMode={previewMode}
                    previewGrid={previewGrid}
                    onTogglePreviewMode={() => setPreviewMode(m => m === 'fit' ? 'fill' : 'fit')}
                    onTogglePreviewGrid={() => setPreviewGrid(g => g === 0 ? 3 : 0)}
                    onTimeUpdate={() => {}}
                    demoMode={false}
                 />
             ) : (
                 <div className="h-full flex flex-col items-center justify-center text-zinc-600 p-8 text-center">
                     <div className="w-20 h-20 bg-zinc-800/50 rounded-full flex items-center justify-center mb-4">
                         <GripHorizontal size={32} className="opacity-50" />
                     </div>
                     <h3 className="text-sm font-bold text-zinc-400 mb-2">{t('board.no_beat')}</h3>
                     <p className="text-xs text-zinc-500 max-w-[200px] leading-relaxed">
                        {t('board.no_beat_desc')}
                     </p>
                 </div>
             )}
        </div>

    </div>
  );
};