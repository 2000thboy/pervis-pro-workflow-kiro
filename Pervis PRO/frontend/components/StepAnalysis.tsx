
import React, { useState, useEffect, useRef } from 'react';
import { Project, Beat, SceneGroup, TagSchema, Character } from '../types';
import { regenerateBeatTags } from '../services/apiClient';
import { 
  ArrowRight, 
  Tag, 
  AlertCircle, 
  Sparkles, 
  Loader2, 
  LayoutList, 
  Users, 
  Settings2, 
  BarChart3, 
  Clock, 
  Edit3,
  CheckCircle2,
  ChevronRight,
  MousePointer2,
  AlertTriangle,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Download
} from 'lucide-react';
import { ExportDialog } from './Export';

interface Props {
  project: Project;
  onUpdateBeats: (beats: Beat[]) => void;
  onUpdateProject?: (project: Partial<Project>) => void;
  onNext: () => void;
}

// --- Sub-components ---

const AIAnalysisPanel = () => {
  const scores = [
    { label: "剧情架构", score: 75, color: "bg-emerald-500" },
    { label: "人物塑造", score: 80, color: "bg-blue-500" },
    { label: "商业潜力", score: 85, color: "bg-yellow-500" },
    { label: "节奏把控", score: 80, color: "bg-purple-500" },
  ];

  return (
    <div className="bg-zinc-900/50 rounded-xl p-5 border border-zinc-800">
        <h3 className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <BarChart3 size={14} /> AI 剧本评估
        </h3>
        <div className="space-y-4">
            {scores.map((s) => (
                <div key={s.label} className="space-y-1">
                    <div className="flex justify-between text-[10px] text-zinc-400 font-bold">
                        <span>{s.label}</span>
                        <span className={s.color.replace('bg-', 'text-')}>{s.score}/100</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div 
                            className={`h-full ${s.color} transition-all duration-1000`} 
                            style={{ width: `${s.score}%` }}
                        />
                    </div>
                </div>
            ))}
        </div>
        <div className="mt-4 p-3 bg-zinc-900 border border-zinc-800 rounded text-[10px] text-zinc-500 leading-relaxed italic">
            "剧本大纲结构完整，主人公键太的成长弧线清晰。末日背景下，地铁作为‘地下堡垒’的真相互相结合，具备较强的商业潜力和类型片吸引力..."
        </div>
    </div>
  );
};

const ProjectConfigPanel = ({ project }: { project: Project }) => {
    return (
        <div className="space-y-6">
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">一句话故事 (Logline)</label>
                <div className="text-xs text-zinc-300 bg-zinc-900 p-3 rounded border border-zinc-800 leading-relaxed">
                    {project.logline || "暂无 Logline..."}
                </div>
            </div>
            <div className="space-y-2">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">故事梗概 (Synopsis)</label>
                <div className="text-xs text-zinc-300 bg-zinc-900 p-3 rounded border border-zinc-800 leading-relaxed h-32 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-700">
                    {project.synopsis || "暂无梗概..."}
                </div>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-zinc-800">
                 <div className="bg-zinc-900 p-2 rounded border border-zinc-800">
                     <span className="text-[9px] text-zinc-500 block uppercase">Canvas</span>
                     <span className="text-xs font-mono text-zinc-300">{project.specs?.aspectRatio || '16:9'}</span>
                 </div>
                 <div className="bg-zinc-900 p-2 rounded border border-zinc-800">
                     <span className="text-[9px] text-zinc-500 block uppercase">FPS</span>
                     <span className="text-xs font-mono text-zinc-300">{project.specs?.fps || 24} fps</span>
                 </div>
            </div>
        </div>
    );
};

const BeatEditorPanel = ({ beat, onUpdate, onRegenerate, isRegenerating }: { beat: Beat, onUpdate: (b: Beat) => void, onRegenerate: () => void, isRegenerating: boolean }) => {
    return (
        <div className="bg-zinc-900/80 rounded-xl p-5 border border-indigo-500/30 shadow-[0_0_30px_rgba(79,70,229,0.1)] relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
            
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                    <Edit3 size={14} /> 镜头属性编辑
                </h3>
                <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded text-zinc-400 font-mono">
                    {beat.duration}s
                </span>
            </div>

            <div className="space-y-4">
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-zinc-500">原文内容</label>
                    <textarea 
                        className="w-full h-20 bg-black/40 border border-zinc-800 rounded p-2 text-xs text-zinc-300 resize-none focus:border-indigo-500 focus:outline-none"
                        value={beat.content}
                        onChange={(e) => onUpdate({...beat, content: e.target.value})}
                    />
                </div>

                <div className="space-y-1.5">
                    <div className="flex justify-between items-center">
                         <label className="text-[10px] font-bold text-yellow-600">视觉提示词 (Visual Query)</label>
                         <button 
                            onClick={onRegenerate}
                            disabled={isRegenerating}
                            className="text-[9px] flex items-center gap-1 text-indigo-400 hover:text-white transition-colors"
                         >
                             {isRegenerating ? <Loader2 size={10} className="animate-spin"/> : <Sparkles size={10}/>}
                             AI 重写
                         </button>
                    </div>
                    <textarea 
                        className="w-full h-24 bg-zinc-800 border border-zinc-700/50 rounded p-2 text-xs text-yellow-500/90 resize-none focus:border-yellow-500 focus:outline-none leading-relaxed"
                        value={beat.tags?.visual_notes || ''}
                        onChange={(e) => {
                             const tags = beat.tags || {};
                             onUpdate({...beat, tags: { ...tags, visual_notes: e.target.value }});
                        }}
                    />
                </div>

                <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-500">情绪 (Mood)</label>
                        <input 
                            type="text" 
                            className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
                            value={beat.tags?.primary_emotion || ''}
                            onChange={(e) => {
                                 const tags = beat.tags || {};
                                 onUpdate({...beat, tags: { ...tags, primary_emotion: e.target.value }});
                            }}
                        />
                    </div>
                    <div className="space-y-1">
                        <label className="text-[10px] font-bold text-zinc-500">景别 (Shot)</label>
                        <input 
                            type="text" 
                            className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
                            value={beat.tags?.shot_type || ''}
                            onChange={(e) => {
                                 const tags = beat.tags || {};
                                 onUpdate({...beat, tags: { ...tags, shot_type: e.target.value }});
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}

const CharactersPanel = ({ characters, onUpdate }: { characters: Character[], onUpdate: (chars: Character[]) => void }) => {
    // A simple character editor placeholder
    return (
        <div className="space-y-4">
             <div className="flex justify-between items-center mb-2">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">角色列表 ({characters.length})</span>
                <button 
                    onClick={() => {
                        const newChar: Character = { 
                            id: `c-${Date.now()}`, 
                            name: "New Character", 
                            role: 'Supporting', 
                            description: "Description...", 
                            traits: [] 
                        };
                        onUpdate([...characters, newChar]);
                    }}
                    className="p-1 text-zinc-400 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded"
                >
                    <Plus size={12} />
                </button>
             </div>
             
             <div className="space-y-3">
                 {characters.map((char, idx) => (
                     <div key={char.id} className="bg-zinc-900 border border-zinc-800 rounded p-3 group hover:border-zinc-600 transition-colors">
                         <div className="flex justify-between items-start mb-2">
                             <div>
                                 <input 
                                     className="bg-transparent border-none text-xs font-bold text-zinc-200 focus:outline-none focus:ring-0 p-0"
                                     value={char.name}
                                     onChange={(e) => {
                                         const updated = [...characters];
                                         updated[idx].name = e.target.value;
                                         onUpdate(updated);
                                     }}
                                 />
                                 <div className="flex gap-1 mt-1">
                                    <span className={`text-[9px] px-1 rounded ${char.role === 'Protagonist' ? 'bg-yellow-900/40 text-yellow-500' : 'bg-zinc-800 text-zinc-500'}`}>
                                        {char.role}
                                    </span>
                                 </div>
                             </div>
                             <button 
                                onClick={() => {
                                    if(confirm("Delete character?")) {
                                        onUpdate(characters.filter(c => c.id !== char.id));
                                    }
                                }}
                                className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 p-1"
                             >
                                 <X size={12} />
                             </button>
                         </div>
                         <textarea 
                             className="w-full bg-black/20 text-[10px] text-zinc-400 border border-transparent hover:border-zinc-700 rounded p-1.5 resize-none focus:outline-none focus:border-indigo-500"
                             rows={2}
                             value={char.description}
                             onChange={(e) => {
                                 const updated = [...characters];
                                 updated[idx].description = e.target.value;
                                 onUpdate(updated);
                             }}
                         />
                     </div>
                 ))}
                 {characters.length === 0 && (
                     <div className="text-center py-8 text-zinc-600 text-xs">
                         暂无角色，请手动添加或等待 AI 提取。
                     </div>
                 )}
             </div>
        </div>
    );
}

// --- Main Component ---

export const StepAnalysis: React.FC<Props> = ({ project, onUpdateBeats, onUpdateProject, onNext }) => {
  const [activeTab, setActiveTab] = useState<'outline' | 'chars'>('outline');
  const [selectedBeatId, setSelectedBeatId] = useState<string | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const scriptContainerRef = useRef<HTMLDivElement>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);

  // Edit Duration States
  const [isEditingDuration, setIsEditingDuration] = useState(false);
  const [tempDuration, setTempDuration] = useState(0);

  // Keyboard shortcut for sidebar toggle
  useEffect(() => {
      const handleKeyDown = (e: KeyboardEvent) => {
          if (e.key === 'Tab' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement).tagName)) {
              e.preventDefault();
              setIsSidebarOpen(prev => !prev);
          }
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Group beats into scenes for Outline
  const scenes = React.useMemo(() => {
      const groups: { title: string, id: string, beatCount: number }[] = [];
      let currentGroup = null;
      project.beats.forEach((b, idx) => {
          const title = b.tags?.scene_slug || `SCENE ${groups.length + 1}`;
          if (!currentGroup || currentGroup.title !== title) {
              currentGroup = { title, id: b.id, beatCount: 0 };
              groups.push(currentGroup);
          }
          currentGroup.beatCount++;
      });
      return groups;
  }, [project.beats]);

  const handleBeatUpdate = (updatedBeat: Beat) => {
      const newBeats = project.beats.map(b => b.id === updatedBeat.id ? updatedBeat : b);
      onUpdateBeats(newBeats);
  };

  const handleRegenerateTags = async (beat: Beat) => {
      setRegeneratingId(beat.id);
      try {
          const newTags = await regenerateBeatTags(beat.content);
          handleBeatUpdate({ ...beat, tags: newTags });
      } catch (e) {
          console.error("Failed to regen", e);
      } finally {
          setRegeneratingId(null);
      }
  };

  const handleDurationClick = () => {
      setTempDuration(project.specs?.totalDuration || 120);
      setIsEditingDuration(true);
  };

  const confirmDurationChange = () => {
      if (onUpdateProject && project.specs) {
          onUpdateProject({ 
              specs: { ...project.specs, totalDuration: tempDuration } 
          });
      }
      setIsEditingDuration(false);
  };

  const handleCharactersUpdate = (newChars: Character[]) => {
      if (onUpdateProject) {
          onUpdateProject({ characters: newChars });
      }
  };

  const selectedBeat = project.beats.find(b => b.id === selectedBeatId);

  const scrollToBeat = (beatId: string) => {
      setSelectedBeatId(beatId);
      // Optional: scroll into view logic for the script or timeline strip
  };

  const currentTotal = project.beats.reduce((a,b)=>a+b.duration,0);

  return (
    <div className="flex flex-col h-full bg-zinc-950 text-zinc-200 overflow-hidden relative">
        
        {/* Main Workspace Grid */}
        <div className="flex-1 flex overflow-hidden">
            
            {/* 1. LEFT SIDEBAR: OUTLINE & CHARACTERS (Collapsible) */}
            <div 
                className={`flex-shrink-0 bg-zinc-900/30 border-r border-zinc-800 flex flex-col transition-all duration-300 ease-in-out relative ${isSidebarOpen ? 'w-64' : 'w-12'}`}
            >
                {/* Toggle Button (Hover Area) */}
                <button 
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-12 bg-zinc-900 border border-zinc-700 rounded-full flex items-center justify-center z-50 text-zinc-500 hover:text-white hover:border-yellow-500 shadow-lg cursor-pointer opacity-0 hover:opacity-100 transition-opacity"
                    title="Toggle Sidebar (Tab)"
                >
                    {isSidebarOpen ? <PanelLeftClose size={12} /> : <PanelLeftOpen size={12} />}
                </button>

                {/* Tabs */}
                <div className={`flex border-b border-zinc-800 ${isSidebarOpen ? '' : 'flex-col'}`}>
                    <button 
                        onClick={() => { setActiveTab('outline'); if(!isSidebarOpen) setIsSidebarOpen(true); }}
                        className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors ${activeTab === 'outline' ? 'text-yellow-500 border-b-2 border-yellow-500 bg-zinc-800/50' : 'text-zinc-500 hover:text-zinc-300'} ${!isSidebarOpen && activeTab !== 'outline' ? 'border-b-0' : ''}`}
                        title="Outline"
                    >
                        <LayoutList size={14} /> {isSidebarOpen && "故事大纲"}
                    </button>
                    <button 
                        onClick={() => { setActiveTab('chars'); if(!isSidebarOpen) setIsSidebarOpen(true); }}
                        className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition-colors ${activeTab === 'chars' ? 'text-yellow-500 border-b-2 border-yellow-500 bg-zinc-800/50' : 'text-zinc-500 hover:text-zinc-300'} ${!isSidebarOpen && activeTab !== 'chars' ? 'border-b-0' : ''}`}
                        title="Characters"
                    >
                        <Users size={14} /> {isSidebarOpen && "角色管理"}
                    </button>
                </div>

                {/* Content */}
                {isSidebarOpen && (
                    <div className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-thumb-zinc-800 animate-in fade-in duration-300">
                        {activeTab === 'outline' ? (
                            <div className="space-y-2">
                                {scenes.map((scene, idx) => (
                                    <div 
                                        key={scene.id} 
                                        className="p-3 rounded border border-zinc-800 hover:bg-zinc-800/50 cursor-pointer group transition-all"
                                        onClick={() => scrollToBeat(scene.id)}
                                    >
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-[10px] font-bold text-zinc-500 group-hover:text-yellow-500 transition-colors">SCENE {idx + 1}</span>
                                            <span className="text-[9px] bg-zinc-900 px-1.5 rounded text-zinc-600">{scene.beatCount} beats</span>
                                        </div>
                                        <div className="text-xs font-bold text-zinc-300 line-clamp-2 leading-tight" title={scene.title}>
                                            {scene.title}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <CharactersPanel characters={project.characters || []} onUpdate={handleCharactersUpdate} />
                        )}
                    </div>
                )}
                
                {isSidebarOpen && (
                    <div className="p-4 border-t border-zinc-800">
                        <button 
                            onClick={() => setShowExportDialog(true)}
                            className="w-full py-2 bg-yellow-600 hover:bg-yellow-500 text-black text-xs font-bold rounded border border-yellow-500 transition-colors flex items-center justify-center gap-2 mb-2"
                        >
                            <Download size={12} /> 导出项目文档
                        </button>
                        <button className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 hover:text-white text-xs font-bold rounded border border-zinc-700 transition-colors flex items-center justify-center gap-2">
                            <Sparkles size={12} /> 生成人物关系图
                        </button>
                    </div>
                )}
            </div>

            {/* 2. CENTER: SCRIPT EDITOR */}
            <div className="flex-1 bg-zinc-950 flex flex-col relative">
                {/* Script Toolbar */}
                <div className="h-10 border-b border-zinc-800 flex items-center justify-between px-4 bg-zinc-900/50">
                    <span className="text-xs font-bold text-zinc-500">{project.title || "Untitled Script"}</span>
                    <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1 text-[10px] text-zinc-500">
                            <CheckCircle2 size={12} className="text-green-500"/> 已保存
                        </span>
                    </div>
                </div>

                {/* Script Content */}
                <div className="flex-1 overflow-y-auto p-8 flex justify-center bg-zinc-950 custom-scrollbar" ref={scriptContainerRef}>
                    <div className="max-w-3xl w-full">
                        {/* Render Script nicely */}
                        <div className="font-mono text-sm text-zinc-300 leading-loose whitespace-pre-wrap selection:bg-yellow-900/50 selection:text-yellow-100">
                            {project.scriptRaw}
                        </div>
                        <div className="h-32"></div> {/* Padding at bottom */}
                    </div>
                </div>
            </div>

            {/* 3. RIGHT SIDEBAR: CONFIG & AI */}
            <div className="w-[320px] flex-shrink-0 bg-zinc-950 border-l border-zinc-800 flex flex-col relative">
                {/* Cyberpunk Curve Decoration */}
                <svg className="absolute top-0 left-[-20px] h-full w-[20px] pointer-events-none z-10 hidden md:block" viewBox="0 0 20 1000" preserveAspectRatio="none">
                    <path d="M20,0 C10,50 0,100 0,150 L0,850 C0,900 10,950 20,1000" fill="none" stroke="#27272a" strokeWidth="1" />
                    <path d="M20,100 C15,120 5,140 5,160 L5,300" fill="none" stroke="#eab308" strokeWidth="2" strokeOpacity="0.3" />
                </svg>

                {/* Header */}
                <div className="h-10 border-b border-zinc-800 flex items-center px-6 bg-zinc-900">
                    <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                        {selectedBeat ? <><Edit3 size={14} className="text-indigo-500"/> 镜头编辑</> : <><Settings2 size={14} className="text-zinc-500"/> 项目配置</>}
                    </h2>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-thin scrollbar-thumb-zinc-800">
                    {selectedBeat ? (
                        <>
                            <BeatEditorPanel 
                                beat={selectedBeat} 
                                onUpdate={handleBeatUpdate}
                                onRegenerate={() => handleRegenerateTags(selectedBeat)}
                                isRegenerating={regeneratingId === selectedBeat.id}
                            />
                            <div className="pt-4 border-t border-zinc-800">
                                <button onClick={() => setSelectedBeatId(null)} className="text-xs text-zinc-500 hover:text-zinc-300 underline">返回项目概览</button>
                            </div>
                        </>
                    ) : (
                        <>
                            <ProjectConfigPanel project={project} />
                            <AIAnalysisPanel />
                        </>
                    )}
                </div>
            </div>

        </div>

        {/* 4. BOTTOM: TIMELINE PREVIEW */}
        <div className="h-20 bg-zinc-900 border-t border-zinc-800 flex flex-col flex-shrink-0 relative z-20">
            <div className="h-6 flex items-center px-4 bg-zinc-950 border-b border-zinc-800">
                 <span className="text-[10px] font-bold text-yellow-600 flex items-center gap-2">
                    <Clock size={12} /> TIMELINE PREVIEW
                 </span>
                 
                 {/* Editable Duration Footer */}
                 <div className="ml-auto flex items-center gap-3">
                    <div className="text-[10px] text-zinc-600">
                        Current: {currentTotal.toFixed(1)}s
                    </div>
                    <button 
                        onClick={handleDurationClick}
                        className="group flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 px-2 py-0.5 rounded transition-colors"
                        title="点击修改目标时长"
                    >
                         <span className="text-[10px] text-zinc-400 group-hover:text-white">Target: {project.specs?.totalDuration || 0}s</span>
                         <Edit3 size={10} className="text-zinc-600 group-hover:text-indigo-400" />
                    </button>
                 </div>
            </div>
            
            {/* Timeline Strip */}
            <div className="flex-1 overflow-x-auto overflow-y-hidden whitespace-nowrap scrollbar-thin scrollbar-thumb-zinc-700 bg-zinc-950 p-2 relative">
                <div className="flex gap-1 h-full min-w-full">
                    {project.beats.map((beat, idx) => {
                        const isSelected = selectedBeatId === beat.id;
                        return (
                            <div 
                                key={beat.id}
                                onClick={() => setSelectedBeatId(beat.id)}
                                className={`h-full min-w-[60px] rounded cursor-pointer relative group transition-all duration-200 border ${
                                    isSelected 
                                    ? 'bg-indigo-900/60 border-indigo-500 z-10 scale-105' 
                                    : 'bg-zinc-800 border-zinc-700 hover:bg-zinc-700 hover:border-zinc-500'
                                }`}
                                style={{ width: `${Math.max(40, beat.duration * 10)}px` }}
                                title={`${beat.content.substring(0, 50)}...`}
                            >
                                {beat.tags?.scene_slug && (
                                    <div className="absolute top-0 left-0 bg-yellow-600 text-black text-[8px] px-1 font-bold rounded-br opacity-80">
                                        {idx + 1}
                                    </div>
                                )}
                                <div className="p-1 pt-3 text-[8px] text-zinc-400 truncate w-full px-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    {beat.content}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>

        {/* Warning Modal for Duration Change */}
        {isEditingDuration && (
            <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                <div className="w-[400px] bg-zinc-950 border border-red-900/50 rounded-lg shadow-2xl p-6 relative">
                    <button 
                        onClick={() => setIsEditingDuration(false)}
                        className="absolute top-4 right-4 text-zinc-500 hover:text-white"
                    >
                        <X size={16} />
                    </button>

                    <div className="flex flex-col items-center text-center mb-6">
                        <div className="w-12 h-12 bg-red-900/20 rounded-full flex items-center justify-center mb-4 text-red-500">
                            <AlertTriangle size={24} />
                        </div>
                        <h3 className="text-lg font-bold text-white mb-2">修改项目时长?</h3>
                        <p className="text-xs text-zinc-400 leading-relaxed max-w-[280px]">
                            警告：修改总时长可能会影响现有的镜头排序和节奏结构。请确认是否继续。
                        </p>
                    </div>

                    <div className="bg-zinc-900 p-4 rounded border border-zinc-800 mb-6">
                        <label className="text-[10px] font-bold text-zinc-500 uppercase block mb-2">新目标时长 (秒)</label>
                        <input 
                            type="number"
                            className="w-full bg-black border border-zinc-700 rounded px-3 py-2 text-zinc-200 focus:border-red-500 outline-none font-mono text-lg"
                            value={tempDuration}
                            onChange={(e) => setTempDuration(parseInt(e.target.value) || 0)}
                        />
                    </div>

                    <div className="flex gap-3">
                        <button 
                            onClick={() => setIsEditingDuration(false)}
                            className="flex-1 py-2 text-xs font-bold text-zinc-400 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded transition-colors"
                        >
                            取消
                        </button>
                        <button 
                            onClick={confirmDurationChange}
                            className="flex-1 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-500 rounded transition-colors shadow-[0_0_15px_rgba(220,38,38,0.4)]"
                        >
                            确认修改
                        </button>
                    </div>
                </div>
            </div>
        )}

        {/* Export Dialog */}
        <ExportDialog
            isOpen={showExportDialog}
            onClose={() => setShowExportDialog(false)}
            mode="analysis"
            projectId={project.id}
            beats={project.beats.map(b => ({ id: b.id, title: b.content.substring(0, 30) }))}
        />

    </div>
  );
};
