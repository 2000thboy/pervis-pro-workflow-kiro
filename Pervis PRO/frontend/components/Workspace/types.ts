// Workspace 类型定义

export type TabType = 'info' | 'beatboard' | 'preview';

export interface TabConfig {
  id: TabType;
  labelKey: string;
  icon: string;
  shortcut: string;
}

export const TABS: TabConfig[] = [
  { id: 'info', labelKey: 'workspace.tab.info', icon: 'FileText', shortcut: 'Ctrl+1' },
  { id: 'beatboard', labelKey: 'workspace.tab.beatboard', icon: 'LayoutDashboard', shortcut: 'Ctrl+2' },
  { id: 'preview', labelKey: 'workspace.tab.preview', icon: 'Play', shortcut: 'Ctrl+3' },
];

export interface WorkspaceState {
  activeTab: TabType;
  isEditing: boolean;
  sidebarCollapsed: boolean;
}
