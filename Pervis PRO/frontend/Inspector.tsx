
import React, { useState } from 'react';
import { Beat, ProjectAsset, Asset, FeedbackType } from '../types';
import { AssetWall } from './AssetWall';
import { Preview } from './Preview';
import { Clock, AlignLeft, Sparkles, Loader2, Scissors, Wand2, RefreshCw, AlertTriangle, ShieldCheck, ThumbsUp, ThumbsDown } from 'lucide-react';
import { searchVisualAssets, performAIRoughCut, recordAssetFeedback } from './services/geminiService';
import { api } from '../services/api';
import { useLanguage } from './LanguageContext';

interface InspectorProps {
  selectedBeat: Beat | null;
  currentTime: number;
  beatStartTime: number;
  totalDuration: number; // Used for nextFrame logic boundary
  projectId: string;
  projectLibrary: ProjectAsset[];
  onUpdateBeat: (beat: Beat) => void;
  onRegisterAsset: (asset: ProjectAsset) => void;
  // Preview props
  previewMode: 'fit' | 'fill';
  previewGrid: 0 | 3 | 4;
  onTogglePreviewMode: () => void;
  onTogglePreviewGrid: () => void;
  onTimeUpdate: (time: number) => void;
  demoMode: boolean;
}

export const Inspector: React.FC<InspectorProps> = ({
  selectedBeat,
  currentTime,
  beatStartTime,
  totalDuration,
  projectId,
  projectLibrary,
  onUpdateBeat,
  onRegisterAsset,
  previewMode,
  previewGrid,
  onTogglePreviewMode,
  onTogglePreviewGrid,
  onTimeUpdate,
  demoMode
}) => {
  const { t } = useLanguage();
  const [isSearching, setIsSearching] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState("");
  const [activeTab, setActiveTab] = useState<'visual' | 'script'>('visual');
  const [aiReason, setAiReason] = useState<string | null>(null);

  // Asset Wall Logic Hooks
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedBeat || !e.target.files?.[0]) return;
    const file = e.target.files[0];
    
    setIsUploading(true);
    try {
        // Upload via API Layer
        const pa = await api.uploadAsset(file, projectId);
        
        // Register global
        onRegisterAsset(pa);

        // Add Instance
        const asset: Asset = {
            id: `inst-${Date.now()}`,
            projectAssetId: pa.id,
            mediaUrl: pa.mediaUrl,
            thumbnailUrl: pa.thumbnailUrl,
            type: pa.mimeType.startsWith('video') ? 'video' : 'image',
            name: pa.filename,
            source: 'upload',
            notes: ''
        };
        
        const newAssets = [...selectedBeat.assets, asset];
        onUpdateBeat({ ...selectedBeat, assets: newAssets, mainAssetId: selectedBeat.assets.length === 0 ? asset.id : selectedBeat.mainAssetId });
    } catch (e) {
        console.error("Upload failed", e);
        alert(e instanceof Error ? e.message : "Upload failed");
    } finally {
        setIsUploading(false);
    }
  };

  const handleLinkLocal = async () => {
      if (!selectedBeat) return;

      try {
          // 1. Check Config via API
          const settings = await api.getSettings();
          let baseUrl = settings.localServer.baseUrl;

          if (!baseUrl) {
              alert(t('asset.server_not_configured'));
              return;
          }
          
          // Ensure trailing slash
          if (!baseUrl.endsWith('/')) baseUrl += '/';

          // 2. Prompt for Filename
          const filename = prompt(t('asset.enter_filename'));
          if (!filename) return;

          const fullUrl = baseUrl + filename;
          const isVideo = filename.match(/\.(mp4|mov|webm)$/i);

          // 3. Register Asset (Virtual)
          const pa: ProjectAsset = {
            id: `pa-local-${Date.now()}`,
            projectId,
            mediaUrl: fullUrl,
            thumbnailUrl: fullUrl, // Use full URL for local thumbnail
            filename: filename,
            mimeType: isVideo ? 'video/mp4' : 'image/jpeg',
            source: 'local',
            createdAt: Date.now()
          };
          onRegisterAsset(pa);

          // 4. Add Instance
          const asset: Asset = {
            id: `inst-local-${Date.now()}`,
            projectAssetId: pa.id,
            mediaUrl: fullUrl,
            thumbnailUrl: fullUrl,
            type: isVideo ? 'video' : 'image',
            name: filename,
            source: 'local',
            notes: 'Local server asset'
          };

          const newAssets = [...selectedBeat.assets, asset];
          onUpdateBeat({ ...selectedBeat, assets: newAssets, mainAssetId: selectedBeat.assets.length === 0 ? asset.id : selectedBeat.mainAssetId });
      } catch (e) {
          console.error("Failed to link local", e);
      }
  };

  const handleSmartMatch = async () => {
    if (!selectedBeat) return;
    setIsSearching(true);
    try {
        const query = selectedBeat.content + (selectedBeat.tags?.visual_notes || '');
        const results = await searchVisualAssets(query);
        
        if (results.length > 0) {
            // Filter out assets already in the beat to avoid duplicates
            const existingIds = new Set(selectedBeat.assets.map(a => a.projectAssetId));
            const newCandidates = results.filter(r => !existingIds.has(r.projectAssetId));
            
            if (newCandidates.length > 0) {
                // Add top candidate automatically? 
                // Better: Add to asset list but don't force select, let user decide based on wall.
                // Or: Add all candidates to the list.
                const topMatch = newCandidates[0];
                
                // For MVP, we add the top match directly as an asset instance
                const pa: ProjectAsset = {
                    id: topMatch.projectAssetId,
                    projectId,
                    mediaUrl: topMatch.mediaUrl,
                    thumbnailUrl: topMatch.thumbnailUrl,
                    filename: topMatch.name,
                    mimeType: topMatch.type === 'video' ? 'video/mp4' : 'image/jpeg',
                    source: 'external',
                    createdAt: Date.now()
                };
                onRegisterAsset(pa); // Ensure it's in library context (idempotent usually)

                const asset: Asset = {
                    id: `inst-${Date.now()}`,
                    projectAssetId: pa.id,
                    mediaUrl: topMatch.mediaUrl,
                    thumbnailUrl: topMatch.thumbnailUrl,
                    type: topMatch.type,
                    name: topMatch.name,
                    source: 'library',
                    notes: topMatch.notes // Contains score info
                };
                
                const newAssets = [...selectedBeat.assets, asset];
                onUpdateBeat({ ...selectedBeat, assets: newAssets, mainAssetId: selectedBeat.assets.length === 0 ? asset.id : selectedBeat.mainAssetId });
            }
        }
    } catch (e) {
        console.error(e);
    } finally {
        setIsSearching(false);
    }
  };

  const handleAssetFeedback = async (asset: Asset, type: FeedbackType) => {
      if (!selectedBeat) return;
      
      // Visual feedback to user
      console.log(`User feedback: ${type} on ${asset.name}`);
      
      // Update System State
      const queryContext = selectedBeat.content; // Use beat content as query context
      await recordAssetFeedback(projectId, asset.projectAssetId, type, queryContext);
      
      // If rejected, maybe remove from this beat?
      if (type === 'explicit_reject') {
          const newAssets = selectedBeat.assets.filter(a => a.id !== asset.id);
          let newMainId = selectedBeat.mainAssetId;
          if (selectedBeat.mainAssetId === asset.id) {
              newMainId = newAssets.length > 0 ? newAssets[0].id : undefined;
          }
          onUpdateBeat({ ...selectedBeat, assets: newAssets, mainAssetId: newMainId });
      }
  };

  const handleAIRoughCut = async () => {
      if (!selectedBeat || !activeAsset || activeAsset.type !== 'video') return;
      
      const projectAsset = projectLibrary.find(pa => pa.id === activeAsset.projectAssetId);
      if (!projectAsset) {
          alert("Could not find asset details.");
          return;
      }
      
      if (!projectAsset.metadata?.timeLog) {
          alert("This video has not been AI analyzed yet. Please wait for processing to finish in the library.");
          return;
      }

      setIsAnalyzing(true);
      setAnalysisStatus("Querying Video Log...");
      setAiReason(null);
      
      try {
          const result = await performAIRoughCut(selectedBeat.content, projectAsset.metadata);
          setAnalysisStatus("Applying Trim...");

          const updatedAsset = { ...activeAsset, inPoint: result.inPoint, outPoint: result.outPoint };
          const updatedAssets = selectedBeat.assets.map(a => a.id === updatedAsset.id ? updatedAsset : a);
          
          const newDuration = parseFloat((result.outPoint - result.inPoint).toFixed(2));
          
          onUpdateBeat({ ...selectedBeat, assets: updatedAssets, duration: newDuration });
          setAiReason(result.reason);

      } catch(e) {
          console.error("AI Cut Failed", e);
          alert("AI Analysis failed. Check console for details.");
      } finally {
          setIsAnalyzing(false);
          setAnalysisStatus("");
      }
  };

  const updateActiveAssetTrim = (key: 'inPoint' | 'outPoint', val: number) => {
      if (!selectedBeat || !activeAsset) return;
      const updatedAsset = { ...activeAsset, [key]: val };
      const updatedAssets = selectedBeat.assets.map(a => a.id === updatedAsset.id ? updatedAsset : a);
      onUpdateBeat({ ...selectedBeat, assets: updatedAssets });
  };

  const activeAssetId = selectedBeat ? (selectedBeat.mainAssetId || (selectedBeat.assets[0]?.id)) : null;
  const activeAsset = selectedBeat?.assets.find(a => a.id === activeAssetId);
  const activeProjectAsset = activeAsset ? projectLibrary.find(pa => pa.id === activeAsset.projectAssetId) : null;

  return (
    <div className="flex flex-col h-full bg-zinc-900 text-zinc-300">
      {/* 1. Top: Preview Player (Always Visible) */}
      <div className="aspect-video bg-black border-b border-zinc-800 relative shadow-lg">
         <Preview 
            activeBeat={selectedBeat}
            currentTime={currentTime}
            beatStartTime={beatStartTime}
            previewMode={previewMode}
            previewGrid={previewGrid}
            onToggleMode={onTogglePreviewMode}
            onToggleGrid={onTogglePreviewGrid}
            onPrevFrame={() => onTimeUpdate(Math.max(0, currentTime - 0.04))}
            onNextFrame={() => onTimeUpdate(Math.min(totalDuration, currentTime + 0.04))}
            demoMode={demoMode}
         />
      </div>

      {/* 2. Middle: Tabs */}
      <div className="flex border-b border-zinc-800">
          <button 
            onClick={() => setActiveTab('visual')}
            className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider transition-colors ${activeTab === 'visual' ? 'text-white border-b-2 border-indigo-500 bg-zinc-800/30' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            视觉 & 素材
          </button>
          <button 
            onClick={() => setActiveTab('script')}
            className={`flex-1 py-3 text-xs font-bold uppercase tracking-wider transition-colors ${activeTab === 'script' ? 'text-white border-b-2 border-indigo-500 bg-zinc-800/30' : 'text-zinc-500 hover:text-zinc-300'}`}
          >
            剧本 & 笔记
          </button>
      </div>

      {/* 3. Bottom: Scrollable Properties */}
      <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-zinc-800">
        {!selectedBeat ? (
            <div className="h-full flex items-center justify-center text-zinc-600 text-xs">
                选择一个镜头以编辑属性
            </div>
        ) : (
            <div className="space-y-6">
                
                {/* Visual Tab Content */}
                {activeTab === 'visual' && (
                    <>
                        {/* Asset Trust Score Header */}
                        {activeProjectAsset && activeProjectAsset.metadata && (
                            <div className="flex flex-col gap-2 bg-zinc-950 p-2 rounded border border-zinc-800">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <ShieldCheck size={14} className={activeProjectAsset.metadata.assetTrustScore > 0.7 ? "text-green-500" : "text-yellow-500"} />
                                        <span className="text-[10px] font-bold text-zinc-400 uppercase">System Trust</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="h-1.5 w-16 bg-zinc-800 rounded-full overflow-hidden">
                                            <div className={`h-full ${activeProjectAsset.metadata.assetTrustScore > 0.7 ? "bg-green-500" : "bg-yellow-500"}`} style={{width: `${(activeProjectAsset.metadata.assetTrustScore || 0.5) * 100}%`}}></div>
                                        </div>
                                        <span className="text-xs font-mono text-zinc-300">{activeProjectAsset.metadata.assetTrustScore || 0.5}</span>
                                    </div>
                                </div>
                                {activeAsset?.notes && activeAsset.notes.startsWith('Score:') && (
                                    <div className="text-[9px] text-zinc-500 border-t border-zinc-900 pt-1 mt-1">
                                        Reasoning: {activeAsset.notes}
                                    </div>
                                )}
                            </div>
                        )}

                        <div className="space-y-2">
                             <div className="flex justify-between items-center">
                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">素材库 (Asset Drawer)</label>
                                <button 
                                    onClick={handleSmartMatch}
                                    disabled={isSearching}
                                    className="flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300"
                                >
                                    {isSearching ? <Loader2 size={10} className="animate-spin"/> : <Sparkles size={10}/>}
                                    AI 智能匹配
                                </button>
                             </div>
                             <div className="bg-zinc-950/50 rounded-lg p-3 border border-zinc-800/50 min-h-[120px] relative">
                                {isUploading && (
                                    <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-20 backdrop-blur-sm rounded-lg">
                                        <Loader2 size={20} className="text-white animate-spin" />
                                    </div>
                                )}
                                <AssetWall 
                                    assets={selectedBeat.assets}
                                    mainAssetId={selectedBeat.mainAssetId}
                                    selectedAssetId={activeAssetId}
                                    onSelect={(a) => onUpdateBeat({ ...selectedBeat, mainAssetId: a.id })} 
                                    onSetMain={(id) => onUpdateBeat({ ...selectedBeat, mainAssetId: id })}
                                    onRemove={(id) => onUpdateBeat({ ...selectedBeat, assets: selectedBeat.assets.filter(a => a.id !== id) })}
                                    onFeedback={handleAssetFeedback}
                                    onUpload={() => document.getElementById('inspector-upload')?.click()}
                                    onLinkLocal={handleLinkLocal}
                                    onOpenLibrary={() => {}} // Placeholder
                                />
                                <input id="inspector-upload" type="file" className="hidden" onChange={handleUpload} />
                             </div>
                             <p className="text-[9px] text-zinc-600 text-center">
                                 Tip: Hover over asset to provide feedback (👍/👎) and improve AI ranking.
                             </p>
                        </div>

                        {/* --- AI Rough Cut Section (Only for Video) --- */}
                        {activeAsset && activeAsset.type === 'video' && (
                            <div className="space-y-2 animate-in fade-in slide-in-from-top-2">
                                <div className="flex justify-between items-center">
                                    <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-1">
                                        <Scissors size={12} /> AI 粗剪 (Rough Cut)
                                    </label>
                                    <button 
                                        onClick={handleAIRoughCut}
                                        disabled={isAnalyzing}
                                        className="text-[9px] bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 px-2 py-0.5 rounded border border-indigo-600/30 flex items-center gap-1 transition-colors min-w-[120px] justify-center"
                                    >
                                        {isAnalyzing ? (
                                            <>
                                                <Loader2 size={10} className="animate-spin"/> {analysisStatus}
                                            </>
                                        ) : (
                                            <>
                                                <Wand2 size={10} /> 根据剧本自动裁剪
                                            </>
                                        )}
                                    </button>
                                </div>
                                <div className="bg-zinc-900 border border-zinc-800 p-3 rounded-lg space-y-3">
                                    {aiReason && (
                                        <div className="bg-indigo-900/20 border border-indigo-500/30 p-2 rounded text-[10px] text-indigo-200 mb-2">
                                            <span className="font-bold block mb-1">AI Reasoning:</span>
                                            {aiReason}
                                        </div>
                                    )}
                                    <div className="flex gap-2">
                                        <div className="flex-1 space-y-1">
                                            <label className="text-[9px] text-zinc-500 block">In Point</label>
                                            <input 
                                                type="number" 
                                                step="0.1"
                                                className="w-full bg-black border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300 font-mono"
                                                value={activeAsset.inPoint || 0}
                                                onChange={(e) => updateActiveAssetTrim('inPoint', parseFloat(e.target.value))}
                                            />
                                        </div>
                                        <div className="flex-1 space-y-1">
                                            <label className="text-[9px] text-zinc-500 block">Out Point</label>
                                            <input 
                                                type="number" 
                                                step="0.1"
                                                className="w-full bg-black border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300 font-mono"
                                                value={activeAsset.outPoint || 0}
                                                onChange={(e) => updateActiveAssetTrim('outPoint', parseFloat(e.target.value))}
                                            />
                                        </div>
                                    </div>
                                    {(activeAsset.inPoint !== undefined && activeAsset.outPoint !== undefined) && (
                                        <div className="text-[9px] text-zinc-500 text-center">
                                            Clip Duration: <span className="text-zinc-300">{(activeAsset.outPoint - activeAsset.inPoint).toFixed(2)}s</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="space-y-2">
                             <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">时长设定 (Timing)</label>
                             <div className="flex items-center gap-3 bg-zinc-800 p-2 rounded border border-zinc-700">
                                 <Clock size={16} className="text-zinc-400"/>
                                 <input 
                                    type="range" min="0.5" max="20" step="0.1" 
                                    value={selectedBeat.duration}
                                    onChange={(e) => onUpdateBeat({ ...selectedBeat, duration: parseFloat(e.target.value) })}
                                    className="flex-1 accent-indigo-500 h-1 bg-zinc-600 rounded-lg appearance-none cursor-pointer"
                                 />
                                 <span className="font-mono text-xs w-12 text-right">{selectedBeat.duration.toFixed(1)}s</span>
                             </div>
                        </div>
                    </>
                )}

                {/* Script Tab Content */}
                {activeTab === 'script' && (
                    <>
                        <div className="space-y-2">
                             <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">剧本原文 (Script Context)</label>
                             <div className="bg-zinc-950 p-3 rounded border border-zinc-800 text-sm text-zinc-300 leading-relaxed italic">
                                "{selectedBeat.content}"
                             </div>
                        </div>

                        <div className="space-y-2">
                             <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
                                <AlignLeft size={12}/> 导演笔记 (Director's Notes)
                             </label>
                             <textarea 
                                className="w-full h-32 bg-zinc-800 border border-zinc-700 rounded p-3 text-xs text-zinc-200 focus:outline-none focus:border-indigo-500 resize-none"
                                placeholder="光影要求、运镜方式、演员调度..."
                                value={selectedBeat.userNotes || ''}
                                onChange={(e) => onUpdateBeat({ ...selectedBeat, userNotes: e.target.value })}
                             />
                        </div>
                        
                        {selectedBeat.tags && (
                             <div className="space-y-2">
                                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">AI 标签 (AI Tags)</label>
                                <div className="flex flex-wrap gap-1">
                                    {Object.entries(selectedBeat.tags).map(([k, v]) => {
                                        if (!v || k === 'visual_notes') return null;
                                        const val = Array.isArray(v) ? v.join(', ') : v;
                                        return (
                                            <span key={k} className="px-1.5 py-0.5 bg-zinc-800 rounded text-[9px] text-zinc-400 border border-zinc-700">
                                                {k}: <span className="text-zinc-300">{val}</span>
                                            </span>
                                        );
                                    })}
                                </div>
                             </div>
                        )}
                    </>
                )}
            </div>
        )}
      </div>
    </div>
  );
};
