# Design Document: 前端工作台目录页

## Overview

本设计文档描述 Pervis PRO 前端工作台目录页的技术实现方案。

## 架构设计

### 组件层次结构

```
App.tsx
├── LandingPage (首页)
├── ProjectWizard (向导 Modal)
└── Workspace (工作台) ← 新增
    ├── WorkspaceHeader (顶部栏)
    │   ├── ProjectTitle
    │   ├── TabNavigation ← 核心组件
    │   └── GlobalActions
    ├── WorkspaceContent (内容区)
    │   ├── ProjectInfoTab ← 新增
    │   ├── BeatboardTab (复用 StepBeatBoard)
    │   └── PreviewTab (复用 StepTimeline)
    └── WorkspaceSidebar (侧边栏)
        ├── AssetLibrary
        ├── AIAssistant
        └── Settings
```

### 状态管理

```typescript
// WorkspaceContext.tsx
interface WorkspaceState {
  activeTab: 'info' | 'beatboard' | 'preview';
  project: Project;
  isEditing: boolean;
  sidebarCollapsed: boolean;
}

// Tab 状态持久化
// 使用 localStorage 保存用户最后访问的 Tab
```

## 组件设计

### 1. Workspace 主组件

```typescript
// frontend/components/Workspace/index.tsx
interface WorkspaceProps {
  project: Project;
  onUpdateProject: (updates: Partial<Project>) => void;
  onExit: () => void;
}

// 职责：
// - 管理 Tab 状态
// - 协调子组件通信
// - 处理键盘快捷键
```

### 2. TabNavigation 组件

```typescript
// frontend/components/Workspace/TabNavigation.tsx
interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

type TabType = 'info' | 'beatboard' | 'preview';

// Tab 配置
const TABS = [
  { id: 'info', label: '立项信息', icon: FileText, shortcut: 'Ctrl+1' },
  { id: 'beatboard', label: 'Beatboard', icon: LayoutDashboard, shortcut: 'Ctrl+2' },
  { id: 'preview', label: '预演模式', icon: Play, shortcut: 'Ctrl+3' },
];
```

### 3. ProjectInfoTab 组件

```typescript
// frontend/components/Workspace/ProjectInfoTab.tsx
interface ProjectInfoTabProps {
  project: Project;
  onUpdate: (updates: Partial<Project>) => void;
}

// 子组件：
// - BasicInfoSection (基本信息)
// - ScriptSection (剧本/Logline/Synopsis)
// - CharactersSection (角色列表)
// - ScenesSection (场次列表)
// - ReferencesSection (参考资料)
```

### 4. BeatboardTab 组件

```typescript
// frontend/components/Workspace/BeatboardTab.tsx
// 包装 StepBeatBoard，适配 Tab 接口

interface BeatboardTabProps {
  project: Project;
  onUpdateBeats: (beats: Beat[]) => void;
}
```

### 5. PreviewTab 组件

```typescript
// frontend/components/Workspace/PreviewTab.tsx
// 包装 StepTimeline 的预览功能

interface PreviewTabProps {
  project: Project;
  onExport: () => void;
}
```

## 路由设计

### 当前路由（无变化）

```
/ → LandingPage
```

### 状态驱动的视图切换

```typescript
// App.tsx 中的状态
const [project, setProject] = useState<Project | null>(null);
const [workspaceTab, setWorkspaceTab] = useState<TabType>('info');

// 视图渲染逻辑
if (!project) {
  return <LandingPage />;
}
return <Workspace project={project} activeTab={workspaceTab} />;
```

## 数据流设计

```
┌─────────────────────────────────────────────────────────────┐
│                         App.tsx                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ project: Project                                     │    │
│  │ workspaceTab: TabType                               │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Workspace                         │    │
│  │  ┌─────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │ InfoTab │  │ BeatboardTab│  │ PreviewTab  │     │    │
│  │  └────┬────┘  └──────┬──────┘  └──────┬──────┘     │    │
│  │       │              │                │             │    │
│  │       └──────────────┼────────────────┘             │    │
│  │                      │                              │    │
│  │                      ▼                              │    │
│  │              onUpdateProject()                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## UI 设计

### 工作台布局

```
┌────────────────────────────────────────────────────────────────┐
│ [Logo] PreVis Pro    │ 项目名称 ▼ │        [设置] [导出]      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┬──────────────┬──────────────┐               │
│  │  立项信息    │  Beatboard   │  预演模式    │  ← Tab 导航   │
│  └──────────────┴──────────────┴──────────────┘               │
│                                                                │
│  ┌────────────────────────────────────────────────────────┐   │
│  │                                                        │   │
│  │                    Tab 内容区域                        │   │
│  │                                                        │   │
│  │                                                        │   │
│  │                                                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### Tab 样式

```css
/* Tab 导航样式 */
.tab-nav {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border-color);
}

.tab-item {
  padding: 12px 24px;
  border-bottom: 2px solid transparent;
  cursor: pointer;
}

.tab-item.active {
  border-bottom-color: var(--accent-color);
  color: var(--accent-color);
}
```

## 实现策略

### Phase 1: 基础架构 (2小时)
1. 创建 Workspace 组件目录结构
2. 实现 TabNavigation 组件
3. 修改 App.tsx 集成 Workspace

### Phase 2: 立项信息 Tab (3小时)
1. 创建 ProjectInfoTab 组件
2. 实现各个信息 Section
3. 实现编辑功能

### Phase 3: 复用现有组件 (1小时)
1. 创建 BeatboardTab 包装组件
2. 创建 PreviewTab 包装组件
3. 测试组件集成

### Phase 4: 优化和测试 (1小时)
1. 添加键盘快捷键
2. 添加状态持久化
3. 测试完整流程

## 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 现有组件耦合度高 | 难以复用 | 创建适配器组件 |
| 状态同步问题 | 数据不一致 | 使用统一的 Context |
| 性能问题 | Tab 切换卡顿 | 使用 React.memo 和懒加载 |

## 文件结构

```
frontend/components/Workspace/
├── index.tsx              # 主组件
├── WorkspaceContext.tsx   # 状态管理
├── TabNavigation.tsx      # Tab 导航
├── ProjectInfoTab/        # 立项信息 Tab
│   ├── index.tsx
│   ├── BasicInfoSection.tsx
│   ├── ScriptSection.tsx
│   ├── CharactersSection.tsx
│   ├── ScenesSection.tsx
│   └── ReferencesSection.tsx
├── BeatboardTab.tsx       # Beatboard Tab (包装器)
├── PreviewTab.tsx         # 预演模式 Tab (包装器)
└── types.ts               # 类型定义
```
