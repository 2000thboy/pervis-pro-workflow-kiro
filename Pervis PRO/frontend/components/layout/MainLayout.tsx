import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react';

export interface LayoutState {
  sidebarCollapsed: boolean;
  propertiesPanelCollapsed: boolean;
  timelineCollapsed: boolean;
  fullscreen: boolean;
}

export interface MainLayoutProps {
  // 布局区域内容
  sidebar: React.ReactNode;
  header: React.ReactNode;
  workspace: React.ReactNode;
  propertiesPanel: React.ReactNode;
  timeline: React.ReactNode;
  
  // 布局控制
  layoutState?: Partial<LayoutState>;
  onLayoutChange?: (state: LayoutState) => void;
  
  // 样式定制
  className?: string;
}

const SIDEBAR_WIDTH = 280;
const PROPERTIES_WIDTH = 360;
const TIMELINE_HEIGHT = 280;
const HEADER_HEIGHT = 56;

export const MainLayout: React.FC<MainLayoutProps> = ({
  sidebar,
  header,
  workspace,
  propertiesPanel,
  timeline,
  layoutState = {},
  onLayoutChange,
  className = ''
}) => {
  const [layout, setLayout] = useState<LayoutState>({
    sidebarCollapsed: false,
    propertiesPanelCollapsed: false,
    timelineCollapsed: false,
    fullscreen: false,
    ...layoutState
  });

  // 更新布局状态
  const updateLayout = (updates: Partial<LayoutState>) => {
    const newLayout = { ...layout, ...updates };
    setLayout(newLayout);
    onLayoutChange?.(newLayout);
  };

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 'b':
            e.preventDefault();
            updateLayout({ sidebarCollapsed: !layout.sidebarCollapsed });
            break;
          case 'i':
            e.preventDefault();
            updateLayout({ propertiesPanelCollapsed: !layout.propertiesPanelCollapsed });
            break;
          case 't':
            e.preventDefault();
            updateLayout({ timelineCollapsed: !layout.timelineCollapsed });
            break;
          case 'f':
            e.preventDefault();
            updateLayout({ fullscreen: !layout.fullscreen });
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [layout]);

  // 计算布局尺寸
  const sidebarWidth = layout.sidebarCollapsed ? 60 : SIDEBAR_WIDTH;
  const propertiesWidth = layout.propertiesPanelCollapsed ? 0 : PROPERTIES_WIDTH;
  const timelineHeight = layout.timelineCollapsed ? 0 : TIMELINE_HEIGHT;
  const headerHeight = layout.fullscreen ? 0 : HEADER_HEIGHT;

  return (
    <div className={`
      flex flex-col h-screen w-full bg-zinc-950 text-zinc-200 
      font-sans overflow-hidden selection:bg-amber-500/30
      ${layout.fullscreen ? 'fixed inset-0 z-50' : ''}
      ${className}
    `}>
      
      {/* 全局头部 */}
      {!layout.fullscreen && (
        <header 
          className="flex-shrink-0 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur-sm z-40"
          style={{ height: headerHeight }}
        >
          {header}
        </header>
      )}

      {/* 主要内容区域 */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* 侧边栏 */}
        <aside 
          className={`
            flex-shrink-0 bg-zinc-950 border-r border-zinc-800 
            transition-all duration-300 ease-out relative z-30
            ${layout.sidebarCollapsed ? 'shadow-none' : 'shadow-xl shadow-black/20'}
          `}
          style={{ width: sidebarWidth }}
        >
          {/* 侧边栏内容 */}
          <div className="h-full overflow-hidden">
            {sidebar}
          </div>
          
          {/* 侧边栏折叠按钮 */}
          <button
            onClick={() => updateLayout({ sidebarCollapsed: !layout.sidebarCollapsed })}
            className={`
              absolute top-1/2 -translate-y-1/2 -right-3 z-40
              w-6 h-6 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700
              rounded-full flex items-center justify-center
              text-zinc-400 hover:text-zinc-200 transition-all duration-200
              shadow-lg hover:shadow-xl
            `}
            title={layout.sidebarCollapsed ? '展开侧边栏 (Ctrl+B)' : '收起侧边栏 (Ctrl+B)'}
          >
            {layout.sidebarCollapsed ? (
              <ChevronRight size={12} />
            ) : (
              <ChevronLeft size={12} />
            )}
          </button>
        </aside>

        {/* 中央工作区域 */}
        <main className="flex-1 flex flex-col overflow-hidden relative min-w-0">
          
          {/* 工作区内容 */}
          <div className="flex-1 flex overflow-hidden">
            
            {/* 主工作空间 */}
            <div className="flex-1 bg-zinc-950 overflow-hidden relative">
              {workspace}
            </div>

            {/* 属性面板 */}
            {!layout.propertiesPanelCollapsed && (
              <aside 
                className="flex-shrink-0 bg-zinc-900 border-l border-zinc-800 shadow-xl shadow-black/30 relative z-20"
                style={{ width: propertiesWidth }}
              >
                {propertiesPanel}
                
                {/* 属性面板折叠按钮 */}
                <button
                  onClick={() => updateLayout({ propertiesPanelCollapsed: true })}
                  className={`
                    absolute top-1/2 -translate-y-1/2 -left-3 z-30
                    w-6 h-6 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700
                    rounded-full flex items-center justify-center
                    text-zinc-400 hover:text-zinc-200 transition-all duration-200
                    shadow-lg hover:shadow-xl
                  `}
                  title="收起属性面板 (Ctrl+I)"
                >
                  <ChevronRight size={12} />
                </button>
              </aside>
            )}
            
            {/* 属性面板展开按钮 */}
            {layout.propertiesPanelCollapsed && (
              <button
                onClick={() => updateLayout({ propertiesPanelCollapsed: false })}
                className={`
                  absolute top-1/2 -translate-y-1/2 right-4 z-30
                  w-8 h-8 bg-zinc-800/90 hover:bg-zinc-700 border border-zinc-700
                  rounded-lg flex items-center justify-center
                  text-zinc-400 hover:text-zinc-200 transition-all duration-200
                  shadow-lg hover:shadow-xl backdrop-blur-sm
                `}
                title="展开属性面板 (Ctrl+I)"
              >
                <ChevronLeft size={14} />
              </button>
            )}
          </div>

          {/* 时间线区域 */}
          {!layout.timelineCollapsed && (
            <div 
              className="flex-shrink-0 border-t border-zinc-800 bg-zinc-900 relative z-10 shadow-2xl shadow-black/40"
              style={{ height: timelineHeight }}
            >
              {timeline}
              
              {/* 时间线折叠按钮 */}
              <button
                onClick={() => updateLayout({ timelineCollapsed: true })}
                className={`
                  absolute top-2 right-4 z-20
                  w-6 h-6 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700
                  rounded-full flex items-center justify-center
                  text-zinc-400 hover:text-zinc-200 transition-all duration-200
                  shadow-lg hover:shadow-xl
                `}
                title="收起时间线 (Ctrl+T)"
              >
                <ChevronLeft size={12} className="rotate-90" />
              </button>
            </div>
          )}
          
          {/* 时间线展开按钮 */}
          {layout.timelineCollapsed && (
            <button
              onClick={() => updateLayout({ timelineCollapsed: false })}
              className={`
                absolute bottom-4 right-4 z-30
                w-8 h-8 bg-zinc-800/90 hover:bg-zinc-700 border border-zinc-700
                rounded-lg flex items-center justify-center
                text-zinc-400 hover:text-zinc-200 transition-all duration-200
                shadow-lg hover:shadow-xl backdrop-blur-sm
              `}
              title="展开时间线 (Ctrl+T)"
            >
              <ChevronRight size={14} className="rotate-90" />
            </button>
          )}
        </main>
      </div>

      {/* 全屏切换按钮 */}
      <button
        onClick={() => updateLayout({ fullscreen: !layout.fullscreen })}
        className={`
          fixed top-4 right-4 z-50
          w-8 h-8 bg-zinc-800/90 hover:bg-zinc-700 border border-zinc-700
          rounded-lg flex items-center justify-center
          text-zinc-400 hover:text-zinc-200 transition-all duration-200
          shadow-lg hover:shadow-xl backdrop-blur-sm
          ${layout.fullscreen ? 'opacity-100' : 'opacity-0 hover:opacity-100'}
        `}
        title={layout.fullscreen ? '退出全屏 (Ctrl+F)' : '进入全屏 (Ctrl+F)'}
      >
        {layout.fullscreen ? (
          <Minimize2 size={14} />
        ) : (
          <Maximize2 size={14} />
        )}
      </button>

      {/* 布局状态指示器 */}
      <div className="fixed bottom-4 left-4 z-40 flex items-center gap-2 opacity-0 hover:opacity-100 transition-opacity">
        <div className="bg-zinc-900/90 backdrop-blur-sm border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-500">
          <div className="flex items-center gap-3">
            <span className={layout.sidebarCollapsed ? 'text-zinc-600' : 'text-amber-500'}>
              侧边栏
            </span>
            <span className={layout.propertiesPanelCollapsed ? 'text-zinc-600' : 'text-amber-500'}>
              属性
            </span>
            <span className={layout.timelineCollapsed ? 'text-zinc-600' : 'text-amber-500'}>
              时间线
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

// 布局上下文
export const LayoutContext = React.createContext<{
  layout: LayoutState;
  updateLayout: (updates: Partial<LayoutState>) => void;
} | null>(null);

// 布局Hook
export const useLayout = () => {
  const context = React.useContext(LayoutContext);
  if (!context) {
    throw new Error('useLayout must be used within a LayoutProvider');
  }
  return context;
};

// 布局提供者组件
export const LayoutProvider: React.FC<{
  children: React.ReactNode;
  initialState?: Partial<LayoutState>;
}> = ({ children, initialState = {} }) => {
  const [layout, setLayout] = useState<LayoutState>({
    sidebarCollapsed: false,
    propertiesPanelCollapsed: false,
    timelineCollapsed: false,
    fullscreen: false,
    ...initialState
  });

  const updateLayout = (updates: Partial<LayoutState>) => {
    setLayout(prev => ({ ...prev, ...updates }));
  };

  return (
    <LayoutContext.Provider value={{ layout, updateLayout }}>
      {children}
    </LayoutContext.Provider>
  );
};

export default MainLayout;