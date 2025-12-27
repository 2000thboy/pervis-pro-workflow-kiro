/**
 * SystemAgent 类型定义
 */

// 通知类型
export type NotificationType = 'task' | 'warning' | 'error' | 'info';

// 通知级别
export type NotificationLevel = 'critical' | 'warning' | 'info';

// 系统状态
export type SystemStatus = 'normal' | 'working' | 'warning' | 'error';

// 任务状态
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

// Agent 状态
export type AgentStatusType = 'working' | 'reviewing' | 'completed' | 'failed';

// 操作建议
export interface ActionSuggestion {
  type: 'button' | 'link' | 'manual';
  label: string;
  action?: string;  // 'clean_cache' | 'retry_task' | 'relink_asset'
  url?: string;
  instructions?: string;
}

// 通知
export interface Notification {
  id: string;
  type: NotificationType;
  level: NotificationLevel;
  title: string;
  message: string;
  timestamp: string;
  isRead: boolean;
  action?: ActionSuggestion;
  taskId?: string;
  agentType?: string;
}

// 后台任务
export interface BackgroundTask {
  id: string;
  type: 'export' | 'render' | 'ai_generate' | 'asset_process';
  name: string;
  progress: number;
  status: TaskStatus;
  startedAt?: string;
  estimatedDuration?: number;
}

// Agent 状态
export interface AgentStatus {
  agentType: string;
  status: AgentStatusType;
  message: string;
  taskId?: string;
}

// 健康检查结果
export interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, {
    name: string;
    status: 'ok' | 'warning' | 'error' | 'unknown';
    message: string;
    details?: Record<string, any>;
  }>;
  timestamp: string;
}

// WebSocket 事件
export interface SystemEvent {
  id: string;
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

// Context 状态
export interface SystemAgentState {
  notifications: Notification[];
  activeTasks: BackgroundTask[];
  activeAgents: AgentStatus[];
  systemStatus: SystemStatus;
  isConnected: boolean;
  unreadCount: number;
}

// Context 方法
export interface SystemAgentActions {
  markAsRead: (notificationId: string) => Promise<void>;
  clearNotification: (notificationId: string) => Promise<void>;
  clearAllNotifications: () => Promise<void>;
  markAllAsRead: () => Promise<void>;
  executeAction: (action: ActionSuggestion) => Promise<void>;
  retryTask: (taskId: string) => Promise<void>;
  cancelTask: (taskId: string) => Promise<void>;
  runHealthCheck: () => Promise<HealthCheckResult>;
}

// 完整 Context 类型
export interface SystemAgentContextType extends SystemAgentState, SystemAgentActions {}
