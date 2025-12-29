import React, { useState, useEffect, useCallback } from 'react';
import { Project, Beat } from '../../types';
import { TabNavigation } from './TabNavigation';
import { ProjectInfoTab } from './ProjectInfoTab';
import { BeatboardTab } from './BeatboardTab';
import { PreviewTab } from './PreviewTab';
import { TabType } from './types';
import { 
  Settings, LogOut, FolderOpen, Server, Languages,
  ChevronDown, Plus
} from 'lucide-react';
import { useLanguage } from '../LanguageContext';

interface WorkspaceProps {
  project: Project;
  recentProjects: Project[];
  onUpdateProject: (updates: Partial<Project>) => void;
  onUpdateBeats: (beats: Beat[]) => void;
  onExit: () => void;
  onOpenProject: (project: Project) => void;
  onShowSettings: () => void;
  onShowAdmin: () => void;
}

// 从 localStorage 读取上次的 Tab
const getInitialTab = (): TabType => {
  try {
    const saved = localStorage.getItem('workspace_active_tab');
    if (saved && ['info', 'beatboard', 'preview'].includes(saved)) {
      return saved as TabType;
    }
  } catch {}
  return 'info';
};

export const Workspace: React.FC<WorkspaceProps> = ({
  project,
  recentProjects,
  onUpdateProject,
  onUpdateBeats,
  onExit,
  onOpenProject,
  onShowSettings,
  onShowAdmin,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab);
  const [projectListOpen, setProjectListOpen] = useState(false);
  const { language, toggleLanguage } = useLanguage();

  // 保存 Tab 状态到 localStorage
  useEffect(() => {
    localStorage.setItem('workspace_active_tab', activeTab);
  }, [activeTab]);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case '1':
            e.preventDefault();
            setActiveTab('info');
            break;
          case '2':
            e.preventDefault();
            setActiveTab('beatboard');
            break;
          case '3':
            e.preventDefault();
            setActiveTab('preview');
            break;
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 渲染当前 Tab 内容
  const renderTabContent = () => {
    switch (activeTab) {
      case 'info':
        return <ProjectInfoTab project={project} onUpdate={onUpdateProject} />;
      case 'beatboard':
        return <BeatboardTab project={project} onUpdateBeats={onUpdateBeats} />;
      case 'preview':
        return <PreviewTab project={project} onUpdateBeats={onUpdateBeats} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen w-full bg-zinc-950 text-zinc-200 font-sans overflow-hidden">
      {/* 侧边栏 */}
      <aside className="w-64 bg-zinc-950 border-r border-zinc-800 flex flex-col flex-shrink-0">
        {/* Logo */}
        <div
          onClick={onExit}
          className="h-16 flex items-center px-6 border-b border-zinc-800/50 cursor-pointer hover:bg-zinc-900/30 transition-colors"
        >
          <h1 className="text-lg font-black text-white font-serif tracking-tight">
            PreVis Pro
          </h1>
        </div>

        {/* 项目选择器 */}
        <div className="px-4 py-4 border-b border-zinc-800/30 relative">
          <div className="text-[10px] font-bold text-zinc-600 uppercase tracking-wider mb-2 px-2">
            当前项目
          </div>
          <button
            onClick={() => setProjectListOpen(!projectListOpen)}
            className="w-full bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 hover:border-zinc-700 rounded-lg p-3 flex items-center justify-between group transition-all"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-serif font-bold text-xs flex-shrink-0">
                {project.title.substring(0, 1)}
              </div>
              <div className="flex flex-col items-start overflow-hidden">
                <span className="text-xs font-bold text-zinc-200 truncate w-full">{project.title}</span>
                <span className="text-[9px] text-zinc-500">Draft v0.1</span>
              </div>
            </div>
            <ChevronDown size={14} className={`text-zinc-600 transition-transform ${projectListOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* 项目下拉列表 */}
          {projectListOpen && (
            <div className="absolute top-full left-4 right-4 mt-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto">
              {recentProjects.map(p => (
                <div
                  key={p.id}
                  onClick={() => {
                    onOpenProject(p);
                    setProjectListOpen(false);
                  }}
                  className={`p-3 text-xs border-b border-zinc-800 last:border-0 hover:bg-zinc-800 cursor-pointer flex items-center gap-2 ${p.id === project.id ? 'bg-zinc-800' : ''}`}
                >
                  <div className={`w-2 h-2 rounded-full ${p.id === project.id ? 'bg-yellow-500' : 'bg-zinc-600'}`} />
                  <span className={`truncate ${p.id === project.id ? 'text-white font-bold' : 'text-zinc-400'}`}>{p.title}</span>
                </div>
              ))}
              <div
                onClick={() => {
                  setProjectListOpen(false);
                  onExit();
                }}
                className="p-3 text-xs text-yellow-500 hover:bg-zinc-800 cursor-pointer flex items-center gap-2 font-bold border-t border-zinc-800"
              >
                <Plus size={12} /> 新建项目
              </div>
            </div>
          )}
        </div>

        {/* 素材库入口 */}
        <div className="flex-1 py-4">
          <div className="px-6 mb-2 text-[10px] font-bold text-zinc-600 uppercase tracking-wider">资源</div>
          <button className="w-full flex items-center gap-3 px-6 py-3 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-900/50 transition-colors">
            <FolderOpen size={18} />
            <span className="text-xs font-bold">素材库</span>
          </button>
        </div>

        {/* 底部操作 */}
        <div className="flex-shrink-0 border-t border-zinc-800 p-4 space-y-2">
          <button
            onClick={onShowAdmin}
            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-zinc-500 hover:text-white rounded hover:bg-zinc-900 transition-colors"
          >
            <Server size={14} />
            <span>AI 服务状态</span>
          </button>
          <button
            onClick={onShowSettings}
            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-zinc-500 hover:text-white rounded hover:bg-zinc-900 transition-colors"
          >
            <Settings size={14} />
            <span>设置</span>
          </button>
          <button
            onClick={toggleLanguage}
            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-zinc-500 hover:text-white rounded hover:bg-zinc-900 transition-colors"
          >
            <Languages size={14} />
            <span>Language: {language === 'zh' ? '中文' : 'English'}</span>
          </button>
          <button
            onClick={onExit}
            className="w-full flex items-center gap-3 px-3 py-2 text-xs text-red-500/70 hover:text-red-400 rounded hover:bg-red-950/20 transition-colors"
          >
            <LogOut size={14} />
            <span>退出项目</span>
          </button>
        </div>
      </aside>

      {/* 主内容区 */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 顶部栏 */}
        <header className="h-14 border-b border-zinc-800 bg-zinc-950 flex items-center justify-between px-6 flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-zinc-500 text-xs">Project /</span>
            <span className="text-white text-sm font-medium">{project.title}</span>
          </div>
        </header>

        {/* Tab 导航 */}
        <TabNavigation activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Tab 内容 */}
        <main className="flex-1 overflow-hidden">
          {renderTabContent()}
        </main>
      </div>
    </div>
  );
};

export default Workspace;
