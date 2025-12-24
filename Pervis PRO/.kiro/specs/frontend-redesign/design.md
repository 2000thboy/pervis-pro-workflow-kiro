# 前端界面重新设计文档

## 概述

本设计文档旨在彻底重新设计Pervis PRO的前端界面，创建一个真正专业、美观、模块化的导演工作台。新设计将摒弃当前"难看"的界面，打造一个具有电影级视觉质感的专业工具。

## 架构

### 整体布局架构

```
┌─────────────────────────────────────────────────────────────┐
│                    顶部导航栏 (Header)                        │
├─────────────┬───────────────────────────────┬─────────────────┤
│             │                               │                 │
│   侧边栏     │         主工作区               │    属性面板      │
│ (Sidebar)   │      (Main Workspace)        │ (Properties)    │
│             │                               │                 │
│  - 项目管理  │   - 剧本分析                   │  - 详细信息      │
│  - 工具导航  │   - Beat看板                  │  - 预览窗口      │
│  - 资源库   │   - 时间线编辑                 │  - 参数调整      │
│  - 系统状态  │   - 素材管理                   │  - 操作面板      │
│             │                               │                 │
├─────────────┴───────────────────────────────┴─────────────────┤
│                    底部时间线 (Timeline)                       │
└─────────────────────────────────────────────────────────────┘
```

### 组件层次结构

```
App
├── GlobalHeader (全局顶部栏)
├── MainLayout
│   ├── Sidebar (侧边栏)
│   │   ├── ProjectSelector (项目选择器)
│   │   ├── NavigationMenu (导航菜单)
│   │   ├── ResourceLibrary (资源库)
│   │   └── SystemStatus (系统状态)
│   ├── Workspace (主工作区)
│   │   ├── ScriptAnalysis (剧本分析)
│   │   ├── BeatBoard (Beat看板)
│   │   ├── TimelineEditor (时间线编辑)
│   │   └── AssetManager (素材管理)
│   └── PropertiesPanel (属性面板)
│       ├── Inspector (检查器)
│       ├── PreviewWindow (预览窗口)
│       └── ControlPanel (控制面板)
└── GlobalModals (全局模态框)
```

## 组件和接口

### 1. 全局主题系统

#### 色彩方案
```typescript
const theme = {
  colors: {
    // 主色调 - 深色专业主题
    background: {
      primary: '#0a0a0a',      // 主背景 - 纯黑
      secondary: '#1a1a1a',    // 次级背景 - 深灰
      tertiary: '#2a2a2a',     // 三级背景 - 中灰
      elevated: '#1f1f1f',     // 悬浮元素背景
    },
    
    // 品牌色 - 金黄色系
    brand: {
      primary: '#f59e0b',      // 主品牌色 - 琥珀色
      secondary: '#fbbf24',    // 次品牌色 - 亮黄
      accent: '#92400e',       // 强调色 - 深琥珀
      gradient: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)',
    },
    
    // 功能色
    semantic: {
      success: '#10b981',      // 成功 - 绿色
      warning: '#f59e0b',      // 警告 - 橙色
      error: '#ef4444',        // 错误 - 红色
      info: '#3b82f6',         // 信息 - 蓝色
    },
    
    // 文本色
    text: {
      primary: '#ffffff',      // 主文本 - 白色
      secondary: '#d1d5db',    // 次文本 - 浅灰
      tertiary: '#9ca3af',     // 三级文本 - 中灰
      disabled: '#6b7280',     // 禁用文本 - 深灰
    },
    
    // 边框色
    border: {
      primary: '#374151',      // 主边框
      secondary: '#4b5563',    // 次边框
      accent: '#f59e0b',       // 强调边框
    }
  },
  
  // 阴影系统
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    glow: '0 0 20px rgba(245, 158, 11, 0.3)',
  },
  
  // 动画系统
  animations: {
    fast: '150ms ease-out',
    normal: '300ms ease-out',
    slow: '500ms ease-out',
  }
}
```

#### 排版系统
```typescript
const typography = {
  fonts: {
    primary: '"Inter", -apple-system, BlinkMacSystemFont, sans-serif',
    mono: '"JetBrains Mono", "Fira Code", monospace',
    serif: '"Playfair Display", Georgia, serif',
  },
  
  sizes: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
  },
  
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    black: 900,
  }
}
```

### 2. 侧边栏组件 (Sidebar)

#### 项目选择器 (ProjectSelector)
```typescript
interface ProjectSelectorProps {
  currentProject: Project | null;
  recentProjects: Project[];
  onProjectSelect: (project: Project) => void;
  onNewProject: () => void;
}

const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  currentProject,
  recentProjects,
  onProjectSelect,
  onNewProject
}) => {
  return (
    <div className="project-selector">
      {/* 当前项目显示 */}
      <div className="current-project-card">
        <div className="project-avatar">
          {currentProject?.title.charAt(0)}
        </div>
        <div className="project-info">
          <h3>{currentProject?.title}</h3>
          <p>Draft v0.1</p>
        </div>
        <ChevronDown className="dropdown-icon" />
      </div>
      
      {/* 项目下拉列表 */}
      <div className="project-dropdown">
        {recentProjects.map(project => (
          <ProjectItem 
            key={project.id}
            project={project}
            isActive={project.id === currentProject?.id}
            onClick={() => onProjectSelect(project)}
          />
        ))}
        <div className="new-project-button" onClick={onNewProject}>
          <Plus size={16} />
          新建项目
        </div>
      </div>
    </div>
  );
};
```

#### 导航菜单 (NavigationMenu)
```typescript
interface NavigationItem {
  id: string;
  label: string;
  icon: React.ComponentType;
  isActive: boolean;
  badge?: string | number;
  onClick: () => void;
}

const NavigationMenu: React.FC<{
  items: NavigationItem[];
  title: string;
}> = ({ items, title }) => {
  return (
    <nav className="navigation-menu">
      <h4 className="menu-title">{title}</h4>
      <ul className="menu-items">
        {items.map(item => (
          <li key={item.id}>
            <button 
              className={`menu-item ${item.isActive ? 'active' : ''}`}
              onClick={item.onClick}
            >
              <item.icon className="menu-icon" />
              <span className="menu-label">{item.label}</span>
              {item.badge && (
                <span className="menu-badge">{item.badge}</span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};
```

### 3. 主工作区组件 (Workspace)

#### Beat看板 (BeatBoard)
```typescript
interface BeatBoardProps {
  beats: Beat[];
  scenes: SceneGroup[];
  onBeatSelect: (beat: Beat) => void;
  onBeatUpdate: (beat: Beat) => void;
  onSceneReorder: (scenes: SceneGroup[]) => void;
}

const BeatBoard: React.FC<BeatBoardProps> = ({
  beats,
  scenes,
  onBeatSelect,
  onBeatUpdate,
  onSceneReorder
}) => {
  return (
    <div className="beat-board">
      <div className="board-header">
        <h2>故事板</h2>
        <div className="board-controls">
          <ViewToggle />
          <FilterControls />
          <SortControls />
        </div>
      </div>
      
      <div className="board-content">
        {scenes.map(scene => (
          <SceneColumn 
            key={scene.id}
            scene={scene}
            onBeatSelect={onBeatSelect}
            onBeatUpdate={onBeatUpdate}
          />
        ))}
      </div>
    </div>
  );
};
```

#### 增强的Beat卡片
```typescript
const BeatCard: React.FC<{
  beat: Beat;
  isSelected: boolean;
  onSelect: () => void;
  onUpdate: (beat: Beat) => void;
}> = ({ beat, isSelected, onSelect, onUpdate }) => {
  return (
    <div 
      className={`beat-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      {/* 缩略图区域 */}
      <div className="beat-thumbnail">
        {beat.thumbnailUrl ? (
          <img src={beat.thumbnailUrl} alt={beat.content} />
        ) : (
          <div className="placeholder-thumbnail">
            <Film size={24} />
          </div>
        )}
        <div className="thumbnail-overlay">
          <PlayButton size={16} />
        </div>
      </div>
      
      {/* 内容区域 */}
      <div className="beat-content">
        <h4 className="beat-title">{beat.content}</h4>
        <div className="beat-tags">
          {beat.emotionTags?.map(tag => (
            <span key={tag} className="tag emotion-tag">{tag}</span>
          ))}
          {beat.sceneTags?.map(tag => (
            <span key={tag} className="tag scene-tag">{tag}</span>
          ))}
        </div>
        <div className="beat-metadata">
          <span className="duration">{beat.duration}s</span>
          <span className="shot-type">{beat.shotType}</span>
        </div>
      </div>
      
      {/* 操作区域 */}
      <div className="beat-actions">
        <button className="action-button">
          <Edit size={14} />
        </button>
        <button className="action-button">
          <MoreVertical size={14} />
        </button>
      </div>
    </div>
  );
};
```

### 4. 属性面板组件 (PropertiesPanel)

#### 检查器 (Inspector)
```typescript
const Inspector: React.FC<{
  selectedItem: Beat | Asset | null;
  onUpdate: (updates: any) => void;
}> = ({ selectedItem, onUpdate }) => {
  if (!selectedItem) {
    return (
      <div className="inspector-empty">
        <div className="empty-state">
          <Search size={48} />
          <h3>选择一个元素</h3>
          <p>在左侧选择Beat或素材来查看详细信息</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="inspector">
      <div className="inspector-header">
        <h3>属性</h3>
        <div className="inspector-actions">
          <button className="icon-button">
            <Settings size={16} />
          </button>
        </div>
      </div>
      
      <div className="inspector-content">
        <PropertyGroup title="基本信息">
          <PropertyField 
            label="标题"
            value={selectedItem.title}
            onChange={(value) => onUpdate({ title: value })}
          />
          <PropertyField 
            label="描述"
            type="textarea"
            value={selectedItem.description}
            onChange={(value) => onUpdate({ description: value })}
          />
        </PropertyGroup>
        
        <PropertyGroup title="视觉属性">
          <PropertyField 
            label="镜头类型"
            type="select"
            options={shotTypes}
            value={selectedItem.shotType}
            onChange={(value) => onUpdate({ shotType: value })}
          />
          <PropertyField 
            label="时长"
            type="number"
            value={selectedItem.duration}
            onChange={(value) => onUpdate({ duration: value })}
          />
        </PropertyGroup>
      </div>
    </div>
  );
};
```

#### 预览窗口 (PreviewWindow)
```typescript
const PreviewWindow: React.FC<{
  asset: Asset | null;
  isPlaying: boolean;
  onPlay: () => void;
  onPause: () => void;
  onSeek: (time: number) => void;
}> = ({ asset, isPlaying, onPlay, onPause, onSeek }) => {
  return (
    <div className="preview-window">
      <div className="preview-header">
        <h3>预览</h3>
        <div className="preview-controls">
          <button className="icon-button">
            <Maximize size={16} />
          </button>
        </div>
      </div>
      
      <div className="preview-content">
        {asset ? (
          <div className="video-player">
            <video 
              src={asset.url}
              poster={asset.thumbnailUrl}
              controls={false}
            />
            <div className="player-overlay">
              <button 
                className="play-button"
                onClick={isPlaying ? onPause : onPlay}
              >
                {isPlaying ? <Pause size={24} /> : <Play size={24} />}
              </button>
            </div>
            <div className="player-controls">
              <ProgressBar 
                progress={0}
                onSeek={onSeek}
              />
              <div className="control-buttons">
                <button><SkipBack size={16} /></button>
                <button><SkipForward size={16} /></button>
                <VolumeControl />
              </div>
            </div>
          </div>
        ) : (
          <div className="preview-empty">
            <Monitor size={48} />
            <p>选择素材进行预览</p>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 5. 预设内容和快速启动系统

#### 预设剧本模板
```typescript
interface PresetScript {
  id: string;
  title: string;
  genre: string;
  description: string;
  thumbnailUrl: string;
  content: string;
  estimatedDuration: number;
  complexity: 'beginner' | 'intermediate' | 'advanced';
  tags: string[];
}

const PresetScripts: PresetScript[] = [
  {
    id: 'youth-campus',
    title: '青春校园物语',
    genre: '青春/校园',
    description: '一个关于青春、友情和成长的温馨校园故事，适合初学者体验完整工作流',
    thumbnailUrl: '/presets/youth-campus.jpg',
    content: `标题：青春校园物语

场景1：樱花飞舞的校园
春天的校园里，樱花瓣随风飘落。少女美咲背着书包，脸上带着淡淡的忧伤，缓缓走过樱花树下的小径。阳光透过花瓣洒在她的脸上，营造出温馨而略带忧郁的氛围。

场景2：热闹的教室
上课铃声响起，教室里充满了青春活力。同学们嬉笑打闹，美咲坐在窗边，望着窗外的蓝天白云，若有所思。老师走进教室，开始讲课，但美咲的心思似乎飘向了远方。

场景3：紧张的考试
期末考试来临，教室里气氛紧张。学生们埋头答题，只听见笔尖在纸上沙沙作响。美咲紧皱眉头，显得有些焦虑。时钟滴答作响，倒计时的压迫感让人窒息。

场景4：夕阳下的告白
放学后，夕阳西下，天空染成橙红色。在学校的天台上，男主角勇气十足地向美咲表白。美咲脸红心跳，既惊喜又紧张。远处的城市灯火开始点亮，浪漫的氛围达到高潮。`,
    estimatedDuration: 10,
    complexity: 'beginner',
    tags: ['青春', '校园', '浪漫', '成长']
  },
  {
    id: 'urban-thriller',
    title: '都市悬疑夜',
    genre: '悬疑/惊悚',
    description: '一个发生在现代都市的悬疑故事，包含复杂的情节转折和视觉效果',
    thumbnailUrl: '/presets/urban-thriller.jpg',
    content: `标题：都市悬疑夜

场景1：雨夜的街道
深夜的都市街道，霓虹灯在雨水中闪烁。侦探李明穿着风衣，独自走在空旷的街道上。他的脚步声在寂静的夜晚显得格外清晰，每一步都透露着紧张和不安。

场景2：神秘的咖啡厅
李明推开咖啡厅的门，里面昏暗的灯光营造出神秘的氛围。一个戴着帽子的陌生人坐在角落里，桌上放着一个牛皮纸袋。两人的目光在空中交汇，空气中弥漫着紧张的气息。

场景3：追逐戏
突然，陌生人起身逃跑。李明紧追不舍，两人在狭窄的巷子里展开激烈的追逐。镜头快速切换，脚步声、喘息声和心跳声交织在一起，营造出紧张刺激的氛围。

场景4：真相大白
在废弃的仓库里，李明终于抓住了逃犯。在昏暗的灯光下，真相逐渐浮出水面。原来这一切都是一个精心策划的阴谋，而李明也陷入了更大的危机之中。`,
    estimatedDuration: 15,
    complexity: 'intermediate',
    tags: ['悬疑', '都市', '追逐', '反转']
  },
  {
    id: 'sci-fi-future',
    title: '未来科幻纪元',
    genre: '科幻/未来',
    description: '一个设定在未来世界的科幻故事，包含复杂的视觉效果和世界观设定',
    thumbnailUrl: '/presets/sci-fi-future.jpg',
    content: `标题：未来科幻纪元

场景1：未来都市
2087年，巨大的都市在天空中漂浮。飞行器在建筑物之间穿梭，全息广告在空中闪烁。主角艾娃站在观景台上，俯瞰着这个充满科技感的世界，眼中既有向往也有忧虑。

场景2：实验室
在高科技实验室里，科学家们正在进行一项秘密实验。巨大的机器发出蓝色的光芒，各种数据在屏幕上快速滚动。艾娃作为项目负责人，紧张地监控着每一个数据变化。

场景3：危机爆发
突然，实验出现了意外。警报声响起，红色的警示灯闪烁不停。实验室里一片混乱，科学家们惊慌失措。艾娃必须在有限的时间内找到解决方案，否则整个城市都将面临灾难。

场景4：英雄时刻
在关键时刻，艾娃做出了艰难的决定。她冒着生命危险进入了反应堆核心，手动关闭了失控的系统。在耀眼的光芒中，危机得到了解除，但艾娃也为此付出了巨大的代价。`,
    estimatedDuration: 20,
    complexity: 'advanced',
    tags: ['科幻', '未来', '英雄', '牺牲']
  }
];
```

#### 预设选择界面
```typescript
const PresetSelector: React.FC<{
  onSelect: (preset: PresetScript) => void;
  onSkip: () => void;
}> = ({ onSelect, onSkip }) => {
  return (
    <div className="preset-selector">
      <div className="preset-header">
        <h2>选择预设剧本</h2>
        <p>快速开始体验 Pervis PRO 的完整功能</p>
      </div>
      
      <div className="preset-grid">
        {PresetScripts.map(preset => (
          <div 
            key={preset.id}
            className="preset-card"
            onClick={() => onSelect(preset)}
          >
            <div className="preset-thumbnail">
              <img src={preset.thumbnailUrl} alt={preset.title} />
              <div className="preset-overlay">
                <Play size={24} />
              </div>
            </div>
            
            <div className="preset-content">
              <div className="preset-header">
                <h3>{preset.title}</h3>
                <span className="preset-genre">{preset.genre}</span>
              </div>
              
              <p className="preset-description">{preset.description}</p>
              
              <div className="preset-metadata">
                <span className="duration">{preset.estimatedDuration}分钟</span>
                <span className={`complexity ${preset.complexity}`}>
                  {preset.complexity === 'beginner' ? '初级' : 
                   preset.complexity === 'intermediate' ? '中级' : '高级'}
                </span>
              </div>
              
              <div className="preset-tags">
                {preset.tags.map(tag => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="preset-actions">
        <Button variant="ghost" onClick={onSkip}>
          跳过，使用空白项目
        </Button>
        <Button variant="secondary" onClick={() => {}}>
          导入自定义剧本
        </Button>
      </div>
    </div>
  );
};
```

#### 示例素材库
```typescript
interface PresetAsset {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'image';
  category: string;
  thumbnailUrl: string;
  previewUrl: string;
  tags: string[];
  description: string;
}

const PresetAssets: PresetAsset[] = [
  {
    id: 'campus-cherry-blossoms',
    name: '校园樱花飞舞',
    type: 'video',
    category: '校园场景',
    thumbnailUrl: '/assets/cherry-blossoms-thumb.jpg',
    previewUrl: '/assets/cherry-blossoms.mp4',
    tags: ['樱花', '校园', '春天', '浪漫'],
    description: '春天校园里樱花飞舞的唯美场景'
  },
  {
    id: 'classroom-atmosphere',
    name: '教室氛围',
    type: 'video',
    category: '室内场景',
    thumbnailUrl: '/assets/classroom-thumb.jpg',
    previewUrl: '/assets/classroom.mp4',
    tags: ['教室', '学生', '青春', '学习'],
    description: '充满青春活力的教室场景'
  },
  {
    id: 'urban-night-rain',
    name: '都市雨夜',
    type: 'video',
    category: '都市场景',
    thumbnailUrl: '/assets/urban-rain-thumb.jpg',
    previewUrl: '/assets/urban-rain.mp4',
    tags: ['都市', '雨夜', '霓虹', '悬疑'],
    description: '雨夜中的都市街道，霓虹灯闪烁'
  },
  {
    id: 'future-city',
    name: '未来都市',
    type: 'video',
    category: '科幻场景',
    thumbnailUrl: '/assets/future-city-thumb.jpg',
    previewUrl: '/assets/future-city.mp4',
    tags: ['科幻', '未来', '都市', '飞行器'],
    description: '充满科技感的未来都市景观'
  }
];
```

### 6. 桌面启动器界面优化

#### 优化后的启动器主界面
```typescript
const EnhancedDesktopLauncher: React.FC = () => {
  return (
    <div className="desktop-launcher">
      {/* 顶部品牌区域 */}
      <header className="launcher-header">
        <div className="brand-section">
          <div className="brand-logo">
            <img src="/logo.svg" alt="Pervis PRO" />
          </div>
          <div className="brand-text">
            <h1>Pervis <span className="pro-badge">PRO</span></h1>
            <p className="version">v6.5 Industrial Workstation</p>
          </div>
        </div>
        
        <div className="header-actions">
          <Button variant="ghost" icon={Settings}>设置</Button>
          <Button variant="ghost" icon={HelpCircle}>帮助</Button>
        </div>
      </header>
      
      {/* 主内容区域 */}
      <main className="launcher-main">
        <div className="main-grid">
          {/* 快速开始区域 */}
          <section className="quick-start-section">
            <h2>快速开始</h2>
            <div className="quick-actions">
              <QuickActionCard
                icon={Plus}
                title="新建项目"
                description="从预设模板或空白项目开始"
                onClick={() => showPresetSelector()}
              />
              <QuickActionCard
                icon={Upload}
                title="导入项目"
                description="导入现有的项目文件"
                onClick={() => importProject()}
              />
              <QuickActionCard
                icon={Globe}
                title="打开Web版"
                description="在浏览器中使用完整功能"
                onClick={() => openWebInterface()}
              />
            </div>
          </section>
          
          {/* 最近项目区域 */}
          <section className="recent-projects-section">
            <div className="section-header">
              <h2>最近项目</h2>
              <Button variant="ghost" size="sm">查看全部</Button>
            </div>
            <div className="projects-grid">
              {recentProjects.map(project => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          </section>
        </div>
        
        {/* 侧边栏 */}
        <aside className="launcher-sidebar">
          <SystemStatusCard />
          <ResourcesCard />
          <TipsCard />
        </aside>
      </main>
      
      {/* 底部状态栏 */}
      <footer className="launcher-footer">
        <div className="status-indicators">
          <StatusIndicator 
            label="后端服务" 
            status={backendStatus} 
          />
          <StatusIndicator 
            label="前端服务" 
            status={frontendStatus} 
          />
        </div>
        <div className="footer-info">
          <span>© 2025 Pervis PRO</span>
        </div>
      </footer>
    </div>
  );
};
```

#### 增强的项目卡片
```typescript
const ProjectCard: React.FC<{ project: Project }> = ({ project }) => {
  return (
    <div className="project-card enhanced">
      <div className="project-thumbnail">
        {project.thumbnailUrl ? (
          <img src={project.thumbnailUrl} alt={project.title} />
        ) : (
          <div className="placeholder-thumbnail">
            <Film size={32} />
          </div>
        )}
        <div className="project-overlay">
          <Button variant="ghost" size="sm" icon={Play}>
            打开
          </Button>
        </div>
      </div>
      
      <div className="project-info">
        <h3 className="project-title">{project.title}</h3>
        <p className="project-description">{project.logline}</p>
        
        <div className="project-metadata">
          <span className="project-stage">{getStageLabel(project.stage)}</span>
          <span className="project-date">
            {formatDate(project.updatedAt)}
          </span>
        </div>
        
        <div className="project-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${project.progress}%` }}
            />
          </div>
          <span className="progress-text">{project.progress}%</span>
        </div>
      </div>
      
      <div className="project-actions">
        <Button variant="ghost" size="sm" icon={MoreHorizontal} />
      </div>
    </div>
  );
};
```

### 7. 增强的UI组件库

#### 按钮组件
```typescript
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'ghost' | 'danger';
  size: 'sm' | 'md' | 'lg';
  icon?: React.ComponentType;
  loading?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

const Button: React.FC<ButtonProps> = ({
  variant,
  size,
  icon: Icon,
  loading,
  children,
  onClick
}) => {
  const baseClasses = 'button';
  const variantClasses = {
    primary: 'button-primary',
    secondary: 'button-secondary', 
    ghost: 'button-ghost',
    danger: 'button-danger'
  };
  const sizeClasses = {
    sm: 'button-sm',
    md: 'button-md',
    lg: 'button-lg'
  };
  
  return (
    <button 
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]}`}
      onClick={onClick}
      disabled={loading}
    >
      {loading ? (
        <Loader2 className="animate-spin" size={16} />
      ) : Icon ? (
        <Icon size={16} />
      ) : null}
      <span>{children}</span>
    </button>
  );
};
```

#### 卡片组件
```typescript
const Card: React.FC<{
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}> = ({ title, subtitle, actions, children, className }) => {
  return (
    <div className={`card ${className || ''}`}>
      {(title || subtitle || actions) && (
        <div className="card-header">
          <div className="card-title-section">
            {title && <h3 className="card-title">{title}</h3>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {actions && (
            <div className="card-actions">{actions}</div>
          )}
        </div>
      )}
      <div className="card-content">
        {children}
      </div>
    </div>
  );
};
```

## 数据模型

### 界面状态管理
```typescript
interface UIState {
  // 布局状态
  sidebarCollapsed: boolean;
  propertiesPanelCollapsed: boolean;
  timelineCollapsed: boolean;
  
  // 选择状态
  selectedBeat: Beat | null;
  selectedAsset: Asset | null;
  selectedScene: SceneGroup | null;
  
  // 视图状态
  currentView: 'script' | 'board' | 'timeline' | 'library';
  boardViewMode: 'grid' | 'list' | 'timeline';
  
  // 过滤和排序
  filters: {
    emotionTags: string[];
    sceneTags: string[];
    shotTypes: string[];
  };
  sortBy: 'sequence' | 'duration' | 'created' | 'modified';
  
  // 模态框状态
  modals: {
    scriptIngestion: boolean;
    settings: boolean;
    assetUpload: boolean;
    export: boolean;
  };
}
```

### 主题配置
```typescript
interface ThemeConfig {
  mode: 'dark' | 'light';
  accentColor: string;
  fontSize: 'sm' | 'md' | 'lg';
  density: 'compact' | 'comfortable' | 'spacious';
  animations: boolean;
  reducedMotion: boolean;
}
```

## 错误处理

### 用户友好的错误显示
```typescript
const ErrorBoundary: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  return (
    <ErrorBoundaryProvider
      fallback={({ error, resetError }) => (
        <div className="error-boundary">
          <div className="error-content">
            <AlertTriangle size={48} className="error-icon" />
            <h2>出现了一些问题</h2>
            <p>应用遇到了意外错误，请尝试刷新页面。</p>
            <div className="error-actions">
              <Button variant="primary" onClick={resetError}>
                重试
              </Button>
              <Button variant="secondary" onClick={() => window.location.reload()}>
                刷新页面
              </Button>
            </div>
          </div>
        </div>
      )}
    >
      {children}
    </ErrorBoundaryProvider>
  );
};
```

### 加载状态管理
```typescript
const LoadingStates = {
  // 骨架屏组件
  BeatCardSkeleton: () => (
    <div className="beat-card-skeleton">
      <div className="skeleton-thumbnail" />
      <div className="skeleton-content">
        <div className="skeleton-title" />
        <div className="skeleton-tags" />
      </div>
    </div>
  ),
  
  // 全屏加载
  FullScreenLoader: ({ message }: { message: string }) => (
    <div className="fullscreen-loader">
      <div className="loader-content">
        <Loader2 className="animate-spin" size={48} />
        <p>{message}</p>
      </div>
    </div>
  )
};
```

## 测试策略

### 组件测试
- 每个UI组件都需要单元测试，验证渲染和交互行为
- 使用React Testing Library进行组件测试
- 测试不同props组合下的组件表现
- 测试用户交互和事件处理

### 视觉回归测试
- 使用Storybook展示所有组件的不同状态
- 截图对比测试确保视觉一致性
- 测试不同主题和屏幕尺寸下的表现

### 可访问性测试
- 确保所有交互元素都可以通过键盘访问
- 验证屏幕阅读器兼容性
- 检查颜色对比度符合WCAG标准
- 测试焦点管理和导航流程

### 性能测试
- 测试大量数据下的渲染性能
- 验证动画和过渡效果的流畅性
- 检查内存使用和组件卸载
- 测试懒加载和代码分割效果