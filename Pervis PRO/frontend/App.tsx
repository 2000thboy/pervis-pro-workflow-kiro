import React, { useState, useEffect } from 'react';
import { ScriptIngestion } from './ScriptIngestion';
import { ProjectWizard } from './components/ProjectWizard';
import { Project, Beat, WorkflowStage, SceneGroup, ProjectSpecs, Character } from './types';
import { useLanguage } from './components/LanguageContext';
import { api } from './services/api';
import {
    Sun,
    Settings,
    ShieldCheck,
    Share2,
    Plus,
    FileText,
    LayoutDashboard,
    Film,
    ChevronRight,
    Image as ImageIcon,
    Video,
    ArrowRight,
    Sparkles,
    Zap,
    Layers,
    HardDrive,
    Server,
    Database,
    Clock,
    LogOut,
    FolderOpen,
    ChevronDown,
    Languages,
    Trash2,
    Loader2
} from 'lucide-react';

// Stage Components
import { StepAnalysis } from './components/StepAnalysis';
import { StepBeatBoard } from './components/StepBeatBoard';
import { StepTimeline } from './components/StepTimeline';
import { StepLibrary } from './components/StepLibrary';
import { SettingsModal } from './components/SettingsModal';
import { AdminConsole } from './components/AdminConsole';

// System Agent
import { SystemAgentProvider, SystemAgentUI, NotificationToast } from './components/SystemAgent';

// --- Landing Page Components ---

const RecentProjectCard: React.FC<{
    project: Project,
    onClick: () => void,
    onDelete: (e: React.MouseEvent) => void
}> = ({
    project,
    onClick,
    onDelete
}) => {
        // Calculate rough progress based on stage
        let progress = 10;
        if (project.currentStage === WorkflowStage.ANALYSIS) progress = 25;
        if (project.currentStage === WorkflowStage.BOARD) progress = 50;
        if (project.currentStage === WorkflowStage.TIMELINE) progress = 75;

        // Format date
        const dateStr = new Date(project.createdAt).toLocaleDateString();

        // Find a thumbnail if available (first asset)
        const thumbnailBeat = project.beats.find(b => b.mainAssetId);
        let thumbnailUrl = null;
        if (thumbnailBeat && thumbnailBeat.assets) {
            const asset = thumbnailBeat.assets.find(a => a.id === thumbnailBeat.mainAssetId);
            if (asset) thumbnailUrl = asset.thumbnailUrl;
        }

        return (
            <div
                onClick={onClick}
                className="group relative w-full h-40 bg-zinc-900/40 backdrop-blur-md border border-zinc-800 hover:border-yellow-500/50 rounded-xl overflow-hidden cursor-pointer transition-all hover:scale-[1.02] hover:shadow-2xl flex-shrink-0"
            >
                {thumbnailUrl ? (
                    <img src={thumbnailUrl} className="absolute inset-0 w-full h-full object-cover opacity-40 group-hover:opacity-60 transition-opacity" alt={project.title} />
                ) : (
                    <div className="absolute inset-0 bg-gradient-to-br from-zinc-800 to-zinc-950 opacity-50"></div>
                )}

                {/* Delete Button (Hidden by default, visible on hover) */}
                <button
                    onClick={onDelete}
                    className="absolute top-2 right-2 p-2 bg-black/50 hover:bg-red-900/80 rounded-full text-zinc-400 hover:text-red-200 opacity-0 group-hover:opacity-100 transition-opacity z-20"
                    title="删除项目"
                >
                    <Trash2 size={12} />
                </button>

                <div className="absolute inset-0 p-5 flex flex-col justify-end">
                    <div className="flex justify-between items-end">
                        <div>
                            <h3 className="text-white font-bold text-sm mb-1 group-hover:text-yellow-400 transition-colors truncate max-w-[150px]">{project.title}</h3>
                            <div className="flex items-center gap-2 text-[10px] text-zinc-400">
                                <Clock size={10} />
                                <span>{dateStr}</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <span className="text-[10px] font-mono text-yellow-600 block mb-1">{progress}%</span>
                            <div className="w-16 h-1 bg-zinc-700 rounded-full overflow-hidden">
                                <div className="h-full bg-yellow-600" style={{ width: `${progress}%` }}></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

const LandingPage: React.FC<{
    onStart: () => void;
    recentProjects: Project[];
    onOpenProject: (p: Project) => void;
    onDeleteProject: (id: string) => void;
    isLoading: boolean;
}> = ({ onStart, recentProjects, onOpenProject, onDeleteProject, isLoading }) => {
    const { t } = useLanguage();
    return (
        <div className="relative w-full h-full flex overflow-hidden bg-black">

            {/* Background Image (Fixed) */}
            <div className="absolute inset-0 z-0">
                <img
                    src="https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?q=80&w=2000&auto=format&fit=crop"
                    className="w-full h-full object-cover opacity-30"
                    alt="Cinema Background"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-transparent" />
            </div>

            {/* Main Content Grid */}
            <div className="relative z-10 w-full h-full grid grid-cols-12 p-12 gap-12">

                {/* Left Column: Recent Projects (Real Data) */}
                <div className="col-span-5 flex flex-col justify-center gap-6 animate-in slide-in-from-left-8 duration-700">
                    <div className="flex items-center gap-2 mb-2">
                        <Clock size={16} className="text-yellow-500" />
                        <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">{t('landing.recent')}</span>
                    </div>

                    {isLoading ? (
                        <div className="flex items-center gap-2 text-zinc-500 text-sm">
                            <Loader2 className="animate-spin" size={16} /> 加载项目中...
                        </div>
                    ) : recentProjects.length > 0 ? (
                        <div className="grid grid-cols-2 gap-4 max-h-[500px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-zinc-800">
                            {recentProjects.map(project => (
                                <RecentProjectCard
                                    key={project.id}
                                    project={project}
                                    onClick={() => onOpenProject(project)}
                                    onDelete={(e) => {
                                        e.stopPropagation();
                                        if (confirm(`确认删除项目 "${project.title}" 吗？此操作不可恢复。`)) {
                                            onDeleteProject(project.id);
                                        }
                                    }}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="w-full h-40 border border-dashed border-zinc-800 rounded-xl flex flex-col items-center justify-center text-zinc-600 bg-zinc-900/20">
                            <FolderOpen size={24} className="mb-2 opacity-50" />
                            <span className="text-xs">暂无最近项目</span>
                            <span className="text-[10px] opacity-50">您的项目将自动保存在这里</span>
                        </div>
                    )}
                </div>

                {/* Right Column: Hero Title & Actions */}
                <div className="col-span-7 flex flex-col justify-center items-start pl-12 animate-in slide-in-from-right-8 duration-700 delay-100">

                    <div className="mb-6">
                        <span className="px-3 py-1 rounded-sm border border-yellow-500/30 bg-yellow-500/10 text-yellow-500 text-[10px] font-bold uppercase tracking-widest">
                            v6.5 Industrial Workstation
                        </span>
                    </div>

                    <h1 className="text-7xl lg:text-8xl font-black text-white mb-6 font-serif tracking-tighter drop-shadow-2xl leading-[0.9]">
                        PreVis <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-yellow-600">Pro</span>
                    </h1>

                    <p className="text-lg text-zinc-400 mb-12 max-w-xl font-light leading-relaxed border-l-2 border-zinc-700 pl-6 whitespace-pre-line">
                        {t('landing.subtitle')}
                    </p>

                    <button
                        onClick={onStart}
                        className="group relative px-12 py-5 bg-yellow-600 hover:bg-yellow-500 text-black font-bold text-sm rounded-full transition-all hover:scale-105 hover:shadow-[0_0_50px_rgba(234,179,8,0.3)] flex items-center gap-4 overflow-hidden"
                    >
                        <div className="absolute inset-0 bg-white/40 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500 skew-x-12"></div>
                        <Plus size={20} strokeWidth={3} />
                        <span className="tracking-wide text-base">{t('landing.start')}</span>
                        <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            </div>

            {/* Bottom: Workflow Steps */}
            <div className="absolute bottom-0 w-full h-20 border-t border-zinc-800/50 bg-black/40 backdrop-blur flex items-center justify-center gap-16 z-20">
                <div className="flex items-center gap-3 opacity-50">
                    <span className="w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-[10px]">1</span>
                    <span className="text-xs font-bold text-zinc-300">{t('landing.step1')}</span>
                </div>
                <div className="flex items-center gap-3 opacity-50">
                    <span className="w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-[10px]">2</span>
                    <span className="text-xs font-bold text-zinc-300">{t('landing.step2')}</span>
                </div>
                <div className="flex items-center gap-3 opacity-50">
                    <span className="w-6 h-6 rounded bg-zinc-800 flex items-center justify-center text-[10px]">3</span>
                    <span className="text-xs font-bold text-zinc-300">{t('landing.step3')}</span>
                </div>
            </div>
        </div>
    );
}

// --- Main App Content ---

function App() {
    const [project, setProject] = useState<Project | null>(null);
    const [currentStage, setCurrentStage] = useState<WorkflowStage>(WorkflowStage.SETUP);
    const { t, language, toggleLanguage } = useLanguage();

    // Real Data State
    const [recentProjects, setRecentProjects] = useState<Project[]>([]);
    const [loadingProjects, setLoadingProjects] = useState(true);

    // UI Modal States
    const [showIngestion, setShowIngestion] = useState(false);
    const [showWizard, setShowWizard] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [showAdmin, setShowAdmin] = useState(false);
    const [projectListOpen, setProjectListOpen] = useState(false);

    // Load projects on mount
    const refreshProjects = async () => {
        setLoadingProjects(true);
        try {
            const loaded = await api.getProjects();
            setRecentProjects(loaded);
        } catch (e) {
            console.error(e);
        } finally {
            setLoadingProjects(false);
        }
    };

    useEffect(() => {
        refreshProjects();
    }, []);

    // --- Handlers ---

    const handleProjectCreated = async (beats: Beat[], scriptRaw: string, meta: { title: string, logline?: string, synopsis?: string }, specs: ProjectSpecs, characters: Character[]) => {
        const newProject: Project = {
            id: crypto.randomUUID(),
            title: meta.title,
            logline: meta.logline,
            synopsis: meta.synopsis,
            scriptRaw,
            beats,
            characters: characters || [],
            library: [],
            specs,
            createdAt: Date.now(),
            currentStage: WorkflowStage.ANALYSIS
        };

        // Save to Persistence via API
        await api.createProject(newProject);
        await refreshProjects();

        setProject(newProject);
        setCurrentStage(WorkflowStage.ANALYSIS);
        setShowIngestion(false);
    };

    const updateBeats = async (newBeats: Beat[]) => {
        if (!project) return;
        const updatedProject = { ...project, beats: newBeats };
        setProject(updatedProject); // Optimistic UI update
        // Async Save
        await api.updateProject(project.id, { beats: newBeats });
    };

    const handleProjectUpdate = async (updates: Partial<Project>) => {
        if (!project) return;
        const updatedProject = { ...project, ...updates };
        setProject(updatedProject);
        await api.updateProject(project.id, updates);
    };

    const handleStageChange = async (newStage: WorkflowStage) => {
        if (!project) return;
        const updatedProject = { ...project, currentStage: newStage };
        setProject(updatedProject);
        setCurrentStage(newStage);
        await api.updateProject(project.id, { currentStage: newStage });
    };

    const handleOpenProject = (p: Project) => {
        setProject(p);
        setCurrentStage(p.currentStage || WorkflowStage.ANALYSIS);
        setProjectListOpen(false); // close dropdown if open
    };

    const handleDeleteProject = async (id: string) => {
        await api.deleteProject(id);
        await refreshProjects();
        // If deleting current project, go home
        if (project && project.id === id) {
            setProject(null);
        }
    };

    const resetToHome = () => {
        setProject(null);
        setCurrentStage(WorkflowStage.SETUP);
        refreshProjects();
    };

    // Helper: Group beats into scenes for Board/Timeline
    const getScenes = (): SceneGroup[] => {
        if (!project) return [];
        const scenes: SceneGroup[] = [];
        let currentScene: SceneGroup | null = null;
        let time = 0;
        project.beats.forEach((beat, idx) => {
            const slug = beat.tags?.scene_slug || "SCENE 1";
            if (!currentScene || currentScene.title !== slug) {
                if (currentScene) scenes.push(currentScene);
                currentScene = { id: `s-${idx}`, title: slug, beats: [], startTime: time, duration: 0 };
            }
            currentScene.beats.push(beat);
            currentScene.duration += beat.duration;
            time += beat.duration;
        });
        if (currentScene) scenes.push(currentScene);
        return scenes;
    };

    // --- Context-Aware Export & Nav Logic ---
    const getExportButton = () => {
        if (!project) return null;

        const buttonBase = "flex items-center gap-2 px-6 py-2 bg-yellow-600 hover:bg-yellow-500 text-black text-xs font-bold rounded transition-colors shadow-[0_0_15px_rgba(234,179,8,0.3)]";

        // Navigation Action Button based on stage
        let navButton = null;

        if (currentStage === WorkflowStage.ANALYSIS) {
            navButton = (
                <button
                    onClick={() => handleStageChange(WorkflowStage.BOARD)}
                    className={buttonBase}
                >
                    <span>{t('common.next')}: {t('stage.board')}</span>
                    <ArrowRight size={14} />
                </button>
            );
        } else if (currentStage === WorkflowStage.BOARD) {
            navButton = (
                <button
                    onClick={() => handleStageChange(WorkflowStage.TIMELINE)}
                    className={buttonBase}
                >
                    <span>{t('common.next')}: {t('stage.timeline')}</span>
                    <ArrowRight size={14} />
                </button>
            );
        } else if (currentStage === WorkflowStage.TIMELINE) {
            navButton = (
                <button
                    className={buttonBase}
                >
                    <Video size={14} />
                    <span>{t('timeline.export')}</span>
                </button>
            );
        }

        return navButton;
    };

    // --- Router Renderer ---
    const renderContent = () => {
        if (!project) {
            return (
                <LandingPage
                    onStart={() => setShowWizard(true)}
                    recentProjects={recentProjects}
                    onOpenProject={handleOpenProject}
                    onDeleteProject={handleDeleteProject}
                    isLoading={loadingProjects}
                />
            );
        }

        switch (currentStage) {
            case WorkflowStage.ANALYSIS:
                return (
                    <StepAnalysis
                        project={project}
                        onUpdateBeats={updateBeats}
                        onUpdateProject={handleProjectUpdate}
                        onNext={() => handleStageChange(WorkflowStage.BOARD)}
                    />
                );
            case WorkflowStage.BOARD:
                return (
                    <StepBeatBoard
                        scenes={getScenes()}
                        beats={project.beats}
                        projectId={project.id}
                        onUpdateBeat={(updatedBeat) => {
                            const newBeats = project.beats.map(b => b.id === updatedBeat.id ? updatedBeat : b);
                            updateBeats(newBeats);
                        }}
                        onNext={() => handleStageChange(WorkflowStage.TIMELINE)}
                    />
                );
            case WorkflowStage.TIMELINE:
                return (
                    <StepTimeline
                        project={project}
                        scenes={getScenes()}
                        onUpdateBeats={updateBeats}
                    />
                );
            case WorkflowStage.LIBRARY:
                return (
                    <StepLibrary
                        project={project}
                        onUpdateProject={handleProjectUpdate}
                    />
                );
            default:
                return null;
        }
    };

    const SidebarItem = ({ icon: Icon, label, active, onClick, className }: { icon: any, label: string, active: boolean, onClick: () => void, className?: string }) => (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-6 py-3.5 transition-all duration-200 border-l-[3px] group ${active
                    ? 'border-yellow-500 bg-zinc-900 text-white'
                    : 'border-transparent text-zinc-500 hover:text-zinc-200 hover:bg-zinc-900/50'
                } ${className}`}
        >
            <Icon size={18} className={`transition-colors ${active ? 'text-yellow-500' : 'text-zinc-500 group-hover:text-zinc-300'}`} />
            <span className="text-xs font-bold tracking-wide">{label}</span>
        </button>
    );

    if (!project) {
        return (
            <div className="flex h-screen w-full bg-zinc-950 font-sans">
                <LandingPage
                    onStart={() => setShowWizard(true)}
                    recentProjects={recentProjects}
                    onOpenProject={handleOpenProject}
                    onDeleteProject={handleDeleteProject}
                    isLoading={loadingProjects}
                />
                {showIngestion && (
                    <ScriptIngestion
                        onProcessComplete={handleProjectCreated}
                        onClose={() => setShowIngestion(false)}
                    />
                )}
                {showWizard && (
                    <ProjectWizard
                        onClose={() => setShowWizard(false)}
                        onComplete={async (projectId) => {
                            setShowWizard(false);
                            // 刷新项目列表并自动打开新创建的项目
                            await refreshProjects();
                            // 获取新创建的项目并打开
                            try {
                                const newProject = await api.getProject(projectId);
                                if (newProject) {
                                    setProject(newProject);
                                    setCurrentStage(newProject.currentStage || WorkflowStage.ANALYSIS);
                                }
                            } catch (e) {
                                console.error('加载新项目失败:', e);
                            }
                        }}
                    />
                )}
                {/* System Agent UI */}
                <SystemAgentUI />
                <NotificationToast />
            </div>
        );
    }

    return (
        <div className="flex h-screen w-full bg-zinc-950 text-zinc-200 font-sans overflow-hidden selection:bg-yellow-500/30">

            {/* --- GLOBAL SIDEBAR --- */}
            <aside className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col z-50 flex-shrink-0 relative">

                {/* 1. Header: Logo & Brand */}
                <div
                    onClick={resetToHome}
                    className="h-16 flex items-center px-6 border-b border-zinc-800/50 cursor-pointer group select-none hover:bg-zinc-900/30 transition-colors"
                >
                    <h1 className="text-lg font-black text-white font-serif tracking-tight flex items-center gap-2">
                        PreVis Pro
                    </h1>
                </div>

                {/* 2. Project Selector (The "First Row") */}
                <div className="px-4 py-4 border-b border-zinc-800/30 relative">
                    <div className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider mb-2 px-2">{t('sidebar.current_project')}</div>
                    <button
                        onClick={() => setProjectListOpen(!projectListOpen)}
                        className="w-full bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg p-3 flex items-center justify-between group transition-all shadow-sm"
                    >
                        <div className="flex items-center gap-3 overflow-hidden">
                            <div className="w-8 h-8 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-serif font-bold text-xs flex-shrink-0 shadow-inner">
                                {project.title.substring(0, 1)}
                            </div>
                            <div className="flex flex-col items-start overflow-hidden">
                                <span className="text-xs font-bold text-zinc-200 truncate w-full group-hover:text-white transition-colors">{project.title}</span>
                                <span className="text-[9px] text-zinc-500 truncate w-full">Draft v0.1</span>
                            </div>
                        </div>
                        <ChevronDown size={14} className={`text-zinc-600 group-hover:text-zinc-400 transition-transform ${projectListOpen ? 'rotate-180' : ''}`} />
                    </button>

                    {/* Dropdown for Switching Projects */}
                    {projectListOpen && (
                        <div className="absolute top-full left-4 right-4 mt-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto">
                            {recentProjects.map(p => (
                                <div
                                    key={p.id}
                                    onClick={() => handleOpenProject(p)}
                                    className={`p-3 text-xs border-b border-zinc-800 last:border-0 hover:bg-zinc-800 cursor-pointer flex items-center gap-2 ${p.id === project.id ? 'bg-zinc-800' : ''}`}
                                >
                                    <div className={`w-2 h-2 rounded-full ${p.id === project.id ? 'bg-yellow-500' : 'bg-zinc-600'}`}></div>
                                    <span className={`truncate ${p.id === project.id ? 'text-white font-bold' : 'text-zinc-400'}`}>{p.title}</span>
                                </div>
                            ))}
                            <div
                                onClick={() => {
                                    setProjectListOpen(false);
                                    setProject(null); // Go to landing
                                }}
                                className="p-3 text-xs text-yellow-500 hover:bg-zinc-800 cursor-pointer flex items-center gap-2 font-bold border-t border-zinc-800"
                            >
                                <Plus size={12} /> {t('landing.start')}
                            </div>
                        </div>
                    )}
                </div>

                {/* 3. Navigation: Tools (Left Top Only) */}
                <nav className="flex-1 py-4 space-y-1 overflow-y-auto">
                    <div className="px-6 mb-2 mt-2 text-[10px] font-bold text-zinc-600 uppercase tracking-wider">{t('sidebar.tools')}</div>
                    <SidebarItem
                        icon={FileText}
                        label={t('sidebar.script')}
                        active={currentStage === WorkflowStage.ANALYSIS}
                        onClick={() => handleStageChange(WorkflowStage.ANALYSIS)}
                    />
                    <SidebarItem
                        icon={LayoutDashboard}
                        label={t('sidebar.board')}
                        active={currentStage === WorkflowStage.BOARD}
                        onClick={() => handleStageChange(WorkflowStage.BOARD)}
                    />
                    <SidebarItem
                        icon={Film}
                        label={t('sidebar.timeline')}
                        active={currentStage === WorkflowStage.TIMELINE}
                        onClick={() => handleStageChange(WorkflowStage.TIMELINE)}
                    />
                </nav>

                {/* 4. Bottom Section: Library & System */}
                <div className="flex-shrink-0 border-t border-zinc-800 bg-zinc-950/50">

                    {/* Asset Library (Moved to Bottom) */}
                    <div className="py-2">
                        <div className="px-6 mb-1 mt-2 text-[10px] font-bold text-zinc-600 uppercase tracking-wider">{t('sidebar.resources')}</div>
                        <SidebarItem
                            icon={FolderOpen}
                            label={t('sidebar.assets')}
                            active={currentStage === WorkflowStage.LIBRARY}
                            onClick={() => handleStageChange(WorkflowStage.LIBRARY)}
                        />
                    </div>

                    {/* System Actions */}
                    <div className="p-4 space-y-2 border-t border-zinc-800/50">
                        <button
                            onClick={() => setShowAdmin(true)}
                            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-zinc-500 hover:text-white rounded hover:bg-zinc-900 transition-colors"
                        >
                            <div className="relative">
                                <Server size={14} />
                                <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 bg-green-500 rounded-full border border-zinc-950"></span>
                            </div>
                            <span>{t('sidebar.ai_ready')}</span>
                        </button>

                        <button
                            onClick={() => setShowSettings(true)}
                            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-zinc-500 hover:text-white rounded hover:bg-zinc-900 transition-colors"
                        >
                            <Settings size={14} />
                            <span>{t('sidebar.settings')}</span>
                        </button>

                        {/* Language Toggle */}
                        <button
                            onClick={toggleLanguage}
                            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-zinc-500 hover:text-white rounded hover:bg-zinc-900 transition-colors"
                        >
                            <Languages size={14} />
                            <span>Language: {language === 'zh' ? '中文' : 'English'}</span>
                        </button>

                        <button
                            onClick={resetToHome}
                            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-red-500/70 hover:text-red-400 rounded hover:bg-red-950/20 transition-colors"
                        >
                            <LogOut size={14} />
                            <span>{t('sidebar.exit')}</span>
                        </button>
                    </div>
                </div>
            </aside>

            {/* --- MAIN CONTENT AREA --- */}
            <div className="flex-1 flex flex-col overflow-hidden relative min-w-0 bg-zinc-950">

                {/* Top Header (Page Level Actions) */}
                <header className="h-14 border-b border-zinc-800 bg-zinc-950 flex items-center justify-between px-6 flex-shrink-0">
                    <div className="flex items-center gap-4">
                        {/* Breadcrumb / Title */}
                        <span className="text-zinc-500 text-xs">Project / {project.title} /</span>
                        <h2 className="text-sm font-bold text-white">
                            {currentStage === WorkflowStage.ANALYSIS && t('stage.analysis')}
                            {currentStage === WorkflowStage.BOARD && t('stage.board')}
                            {currentStage === WorkflowStage.TIMELINE && t('stage.timeline')}
                            {currentStage === WorkflowStage.LIBRARY && t('stage.library')}
                        </h2>
                    </div>

                    <div className="flex items-center gap-4">
                        {getExportButton()}
                    </div>
                </header>

                {/* Workspace Content */}
                <main className="flex-1 overflow-hidden relative">
                    {renderContent()}
                </main>
            </div>

            {/* --- Modals --- */}
            {showIngestion && (
                <ScriptIngestion
                    onProcessComplete={handleProjectCreated}
                    onClose={() => setShowIngestion(false)}
                />
            )}
            {showWizard && (
                <ProjectWizard
                    onClose={() => setShowWizard(false)}
                    onComplete={async (projectId) => {
                        setShowWizard(false);
                        // 刷新项目列表并自动打开新创建的项目
                        await refreshProjects();
                        // 获取新创建的项目并打开
                        try {
                            const newProject = await api.getProject(projectId);
                            if (newProject) {
                                setProject(newProject);
                                setCurrentStage(newProject.currentStage || WorkflowStage.ANALYSIS);
                            }
                        } catch (e) {
                            console.error('加载新项目失败:', e);
                        }
                    }}
                />
            )}
            {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
            {showAdmin && <AdminConsole onClose={() => setShowAdmin(false)} />}
            
            {/* System Agent UI */}
            <SystemAgentUI />
            <NotificationToast />
        </div>
    );
}

// 包装 App 组件以提供 SystemAgentProvider
function AppWithProviders() {
    return (
        <SystemAgentProvider>
            <App />
        </SystemAgentProvider>
    );
}

export default AppWithProviders;