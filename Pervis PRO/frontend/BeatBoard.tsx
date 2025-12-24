
import React, { useRef, useEffect } from 'react';
import { Beat, SceneGroup } from './types';
import { BeatCard } from './BeatCard';
import { Film, Share2 } from 'lucide-react';
import { AssetPickerModal } from './components/AssetPickerModal';
import { api } from './services/api';

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

  // Search State
  const [pickerOpen, setPickerOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [searchResults, setSearchResults] = React.useState<any[]>([]);
  const [isSearching, setIsSearching] = React.useState(false);

  const handleSearch = async (sceneTitle: string, beatContent: string) => {
    setSearchQuery(`${sceneTitle} ${beatContent}`);
    setPickerOpen(true);
    setIsSearching(true);
    setSearchResults([]);

    try {
      const mod = await import('./services/geminiService');
      const res = await mod.searchVisualAssets(`${sceneTitle} ${beatContent}`);
      setSearchResults(res);
    } catch (e) {
      console.error("Search failed", e);
    } finally {
      setIsSearching(false);
    }
  };

  const handleApplyAsset = (asset: any) => {
    console.log("Applied asset:", asset);
    setPickerOpen(false);
    // Here you would call a prop function (e.g., onUpdateBeat) to save the selection
    showToast(`已选择素材: ${asset.projectAssetId}\n(演示: 模拟关联成功)`, 'success');
  };

  // Export State
  const [exportOpen, setExportOpen] = React.useState(false);
  const [toast, setToast] = React.useState<{ msg: string, type: 'success' | 'error' | 'info' } | null>(null);

  const showToast = (msg: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleExport = async (type: 'docx' | 'pdf' | 'md' | 'fcpxml' | 'edl') => {
    setExportOpen(false);
    try {
      showToast("Exporting... Please wait...", 'info');
      let res;
      // In a real app we would get the actual project ID from props/context
      const projectId = "temp_session";

      if (['docx', 'pdf', 'md'].includes(type)) {
        res = await api.remoteExportScript(projectId, type as any);
      } else {
        res = await api.remoteExportNLE(projectId, type as any);
      }

      if (res.status === 'success' && res.file_path) {
        console.log("Export Success:", res);
        showToast(`Export Success! Saved to: ${res.file_path}`, 'success');
        // Optional: Trigger download logic here
      } else {
        showToast("Export Failed: " + (res.message || "Unknown error"), 'error');
      }
    } catch (e) {
      console.error(e);
      showToast("Export Error (See Console)", 'error');
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 pb-32 bg-zinc-950 scrollbar-thin scrollbar-thumb-zinc-800 relative" ref={containerRef}>
      {/* Toast Notification */}
      {toast && (
        <div className={`fixed top-20 right-8 z-[100] px-6 py-3 rounded shadow-xl border flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300 ${toast.type === 'success' ? 'bg-green-950/90 border-green-800 text-green-200' :
            toast.type === 'error' ? 'bg-red-950/90 border-red-800 text-red-200' :
              'bg-blue-950/90 border-blue-800 text-blue-200'
          }`}>
          {toast.type === 'success' ? <div className="w-2 h-2 rounded-full bg-green-500" /> :
            toast.type === 'error' ? <div className="w-2 h-2 rounded-full bg-red-500" /> :
              <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />}
          <span className="text-sm font-medium">{toast.msg}</span>
        </div>
      )}

      {/* Header Actions */}
      <div className="flex justify-end mb-4 px-4 gap-3">
        <div className="relative">
          <button
            onClick={() => setExportOpen(!exportOpen)}
            className="px-4 py-2 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-300 hover:text-white hover:border-yellow-500 transition-colors flex items-center gap-2"
          >
            <Share2 size={14} />
            <span>Export</span>
          </button>

          {exportOpen && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 overflow-hidden text-left flex flex-col">
              <div className="p-2 border-b border-zinc-800 text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Documents</div>
              <button onClick={() => handleExport('docx')} className="px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-800 text-left">Word Script (.docx)</button>
              <button onClick={() => handleExport('pdf')} className="px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-800 text-left">PDF Script (.pdf)</button>
              <button onClick={() => handleExport('md')} className="px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-800 text-left">Markdown (.md)</button>

              <div className="p-2 border-b border-zinc-800 border-t text-[10px] text-zinc-500 font-bold uppercase tracking-wider">NLE / Production</div>
              <button onClick={() => handleExport('fcpxml')} className="px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-800 text-left flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full"></span> Premiere / Resolve (XML)
              </button>
              <button onClick={() => handleExport('edl')} className="px-4 py-2 text-xs text-zinc-300 hover:bg-zinc-800 text-left flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></span> CMX 3600 (EDL)
              </button>
            </div>
          )}
        </div>
      </div>

      {scenes.length === 0 && (
        <div className="h-full flex flex-col items-center justify-center text-zinc-600">
          <Film size={48} strokeWidth={1} className="mb-4 opacity-20" />
          <p>暂无场次。请在左侧解析剧本。</p>
        </div>
      )}

      <div className="flex flex-col gap-10 max-w-[1600px] mx-auto">
        {scenes.map((scene, sceneIdx) => (
          <div key={scene.id} className="animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards" style={{ animationDelay: `${sceneIdx * 50}ms` }}>
            <div className="flex items-center gap-3 mb-4 sticky top-0 z-20 bg-zinc-950/90 backdrop-blur-sm py-2 border-b border-zinc-800/50 justify-between pr-4">
              <div className="flex items-center gap-3">
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

              {/* Search Action */}
              <button
                onClick={() => {
                  if (scene.beats.length > 0) {
                    onSelectBeat(scene.beats[0].id);
                    handleSearch(scene.title, scene.beats[0].content || "");
                  }
                }}
                className="px-3 py-1 bg-zinc-900 border border-zinc-700 rounded text-[10px] text-zinc-400 hover:text-white hover:border-indigo-500 transition-colors flex items-center gap-2"
              >
                <Film size={12} />
                <span>AI 搜素材</span>
              </button>
            </div>

            {/* Shot Container */}
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

              {/* Add Shot Ghost Card */}
              <div className="w-[220px] aspect-video border border-dashed border-zinc-800 rounded-md flex items-center justify-center text-zinc-700 hover:border-zinc-600 hover:bg-zinc-900 transition-colors cursor-pointer group">
                <span className="text-2xl font-light group-hover:scale-110 transition-transform">+</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {pickerOpen && (
        <React.Suspense fallback={null}>
          {/* Dynamic import handled by component definition usually, but here we can just render if imported at top */}
          <AssetPickerModal
            query={searchQuery}
            results={searchResults}
            isLoading={isSearching}
            onClose={() => setPickerOpen(false)}
            onApply={handleApplyAsset}
          />
        </React.Suspense>
      )}
    </div>
  );
};



