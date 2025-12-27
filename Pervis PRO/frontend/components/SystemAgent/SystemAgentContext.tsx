/**
 * SystemAgentContext - 系统 Agent 状态管理
 * 
 * 提供:
 * - WebSocket 连接管理
 * - 通知状态管理
 * - 任务状态管理
 * - Agent 状态管理
 */

import React, { createContext, useContext, useEffect, useReducer, useCallback, useRef } from 'react';
import type {
  SystemAgentContextType,
  SystemAgentState,
  Notification,
  BackgroundTask,
  AgentStatus,
  SystemStatus,
  SystemEvent,
  HealthCheckResult,
  ActionSuggestion
} from './types';

// API 基础 URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_URL = API_BASE.replace('http', 'ws') + '/ws/events';

// 初始状态
const initialState: SystemAgentState = {
  notifications: [],
  activeTasks: [],
  activeAgents: [],
  systemStatus: 'normal',
  isConnected: false,
  unreadCount: 0
};

// Action 类型
type Action =
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'ADD_NOTIFICATION'; payload: Notification }
  | { type: 'UPDATE_NOTIFICATION'; payload: { id: string; updates: Partial<Notification> } }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'SET_NOTIFICATIONS'; payload: Notification[] }
  | { type: 'CLEAR_NOTIFICATIONS' }
  | { type: 'ADD_TASK'; payload: BackgroundTask }
  | { type: 'UPDATE_TASK'; payload: { id: string; updates: Partial<BackgroundTask> } }
  | { type: 'REMOVE_TASK'; payload: string }
  | { type: 'UPDATE_AGENT'; payload: AgentStatus }
  | { type: 'REMOVE_AGENT'; payload: string }
  | { type: 'SET_SYSTEM_STATUS'; payload: SystemStatus };

// Reducer
function reducer(state: SystemAgentState, action: Action): SystemAgentState {
  switch (action.type) {
    case 'SET_CONNECTED':
      return { ...state, isConnected: action.payload };

    case 'ADD_NOTIFICATION': {
      const notifications = [action.payload, ...state.notifications].slice(0, 100);
      return {
        ...state,
        notifications,
        unreadCount: notifications.filter(n => !n.isRead).length
      };
    }

    case 'UPDATE_NOTIFICATION': {
      const notifications = state.notifications.map(n =>
        n.id === action.payload.id ? { ...n, ...action.payload.updates } : n
      );
      return {
        ...state,
        notifications,
        unreadCount: notifications.filter(n => !n.isRead).length
      };
    }

    case 'REMOVE_NOTIFICATION': {
      const notifications = state.notifications.filter(n => n.id !== action.payload);
      return {
        ...state,
        notifications,
        unreadCount: notifications.filter(n => !n.isRead).length
      };
    }

    case 'SET_NOTIFICATIONS':
      return {
        ...state,
        notifications: action.payload,
        unreadCount: action.payload.filter(n => !n.isRead).length
      };

    case 'CLEAR_NOTIFICATIONS':
      return { ...state, notifications: [], unreadCount: 0 };

    case 'ADD_TASK':
      return {
        ...state,
        activeTasks: [...state.activeTasks.filter(t => t.id !== action.payload.id), action.payload],
        systemStatus: 'working'
      };

    case 'UPDATE_TASK': {
      const activeTasks = state.activeTasks.map(t =>
        t.id === action.payload.id ? { ...t, ...action.payload.updates } : t
      );
      const hasRunning = activeTasks.some(t => t.status === 'running');
      return {
        ...state,
        activeTasks,
        systemStatus: hasRunning ? 'working' : state.systemStatus === 'working' ? 'normal' : state.systemStatus
      };
    }

    case 'REMOVE_TASK': {
      const activeTasks = state.activeTasks.filter(t => t.id !== action.payload);
      const hasRunning = activeTasks.some(t => t.status === 'running');
      return {
        ...state,
        activeTasks,
        systemStatus: hasRunning ? 'working' : 'normal'
      };
    }

    case 'UPDATE_AGENT': {
      const existing = state.activeAgents.findIndex(a => a.agentType === action.payload.agentType);
      let activeAgents: AgentStatus[];
      if (existing >= 0) {
        activeAgents = state.activeAgents.map((a, i) => i === existing ? action.payload : a);
      } else {
        activeAgents = [...state.activeAgents, action.payload];
      }
      // 移除已完成的 Agent
      if (action.payload.status === 'completed' || action.payload.status === 'failed') {
        setTimeout(() => {
          // 延迟移除，让用户看到完成状态
        }, 3000);
      }
      return { ...state, activeAgents };
    }

    case 'REMOVE_AGENT':
      return {
        ...state,
        activeAgents: state.activeAgents.filter(a => a.agentType !== action.payload)
      };

    case 'SET_SYSTEM_STATUS':
      return { ...state, systemStatus: action.payload };

    default:
      return state;
  }
}

// Context
const SystemAgentContext = createContext<SystemAgentContextType | null>(null);

// Provider Props
interface SystemAgentProviderProps {
  children: React.ReactNode;
}

// Provider 组件
export function SystemAgentProvider({ children }: SystemAgentProviderProps) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);

  // WebSocket 连接
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('[SystemAgent] WebSocket 已连接');
        dispatch({ type: 'SET_CONNECTED', payload: true });
        reconnectAttempts.current = 0;
      };

      ws.onclose = () => {
        console.log('[SystemAgent] WebSocket 已断开');
        dispatch({ type: 'SET_CONNECTED', payload: false });
        wsRef.current = null;

        // 指数退避重连
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;
        console.log(`[SystemAgent] ${delay}ms 后重连...`);
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      };

      ws.onerror = (error) => {
        console.error('[SystemAgent] WebSocket 错误:', error);
      };

      ws.onmessage = (event) => {
        try {
          // 处理心跳
          if (event.data === 'pong' || event.data === 'heartbeat') return;

          const data: SystemEvent = JSON.parse(event.data);
          handleEvent(data);
        } catch (e) {
          console.error('[SystemAgent] 解析消息失败:', e);
        }
      };

      wsRef.current = ws;

      // 心跳
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);

      ws.addEventListener('close', () => clearInterval(heartbeat));

    } catch (e) {
      console.error('[SystemAgent] 连接失败:', e);
    }
  }, []);

  // 处理 WebSocket 事件
  const handleEvent = useCallback((event: SystemEvent) => {
    const { type, data } = event;

    // 任务事件
    if (type === 'task.started') {
      dispatch({
        type: 'ADD_TASK',
        payload: {
          id: data.task_id,
          type: data.task_type,
          name: data.task_name,
          progress: 0,
          status: 'running',
          startedAt: event.timestamp,
          estimatedDuration: data.estimated_duration
        }
      });
    } else if (type === 'task.progress') {
      dispatch({
        type: 'UPDATE_TASK',
        payload: {
          id: data.task_id,
          updates: { progress: data.progress }
        }
      });
    } else if (type === 'task.completed') {
      dispatch({
        type: 'UPDATE_TASK',
        payload: {
          id: data.task_id,
          updates: { status: 'completed', progress: 100 }
        }
      });
      // 添加完成通知
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: event.id,
          type: 'task',
          level: 'info',
          title: '任务完成',
          message: `${data.task_name} 已完成`,
          timestamp: event.timestamp,
          isRead: false,
          taskId: data.task_id
        }
      });
    } else if (type === 'task.failed') {
      dispatch({
        type: 'UPDATE_TASK',
        payload: {
          id: data.task_id,
          updates: { status: 'failed' }
        }
      });
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: event.id,
          type: 'error',
          level: 'critical',
          title: '任务失败',
          message: data.error || `${data.task_name} 执行失败`,
          timestamp: event.timestamp,
          isRead: false,
          taskId: data.task_id,
          action: data.can_retry ? { type: 'button', label: '重试', action: 'retry_task' } : undefined
        }
      });
    }

    // Agent 事件
    else if (type.startsWith('agent.')) {
      const status = type.split('.')[1] as 'working' | 'reviewing' | 'completed' | 'failed';
      dispatch({
        type: 'UPDATE_AGENT',
        payload: {
          agentType: data.agent_type,
          status,
          message: data.message,
          taskId: data.task_id
        }
      });
    }

    // 系统事件
    else if (type === 'system.warning') {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: event.id,
          type: 'warning',
          level: 'warning',
          title: data.warning_type,
          message: data.message,
          timestamp: event.timestamp,
          isRead: false,
          action: data.suggestion
        }
      });
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: 'warning' });
    } else if (type === 'system.error') {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: event.id,
          type: 'error',
          level: 'critical',
          title: data.error_type,
          message: data.message,
          timestamp: event.timestamp,
          isRead: false
        }
      });
      dispatch({ type: 'SET_SYSTEM_STATUS', payload: 'error' });
    } else if (type === 'system.info') {
      dispatch({
        type: 'ADD_NOTIFICATION',
        payload: {
          id: event.id,
          type: 'info',
          level: 'info',
          title: '系统信息',
          message: data.message,
          timestamp: event.timestamp,
          isRead: false
        }
      });
    }
  }, []);

  // 初始化连接
  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  // API 方法
  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      await fetch(`${API_BASE}/api/system/notifications/${notificationId}/read`, { method: 'POST' });
      dispatch({ type: 'UPDATE_NOTIFICATION', payload: { id: notificationId, updates: { isRead: true } } });
    } catch (e) {
      console.error('标记已读失败:', e);
    }
  }, []);

  const clearNotification = useCallback(async (notificationId: string) => {
    try {
      await fetch(`${API_BASE}/api/system/notifications/${notificationId}`, { method: 'DELETE' });
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: notificationId });
    } catch (e) {
      console.error('删除通知失败:', e);
    }
  }, []);

  const clearAllNotifications = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/api/system/notifications/clear`, { method: 'POST' });
      dispatch({ type: 'CLEAR_NOTIFICATIONS' });
    } catch (e) {
      console.error('清空通知失败:', e);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/api/system/notifications/mark-all-read`, { method: 'POST' });
      const updated = state.notifications.map(n => ({ ...n, isRead: true }));
      dispatch({ type: 'SET_NOTIFICATIONS', payload: updated });
    } catch (e) {
      console.error('标记全部已读失败:', e);
    }
  }, [state.notifications]);

  const executeAction = useCallback(async (action: ActionSuggestion) => {
    if (action.type === 'link' && action.url) {
      window.open(action.url, '_blank');
      return;
    }
    if (action.action === 'clean_cache') {
      await fetch(`${API_BASE}/api/system/actions/clean-cache`, { method: 'POST' });
    }
  }, []);

  const retryTask = useCallback(async (taskId: string) => {
    await fetch(`${API_BASE}/api/system/actions/retry-task/${taskId}`, { method: 'POST' });
  }, []);

  const cancelTask = useCallback(async (taskId: string) => {
    dispatch({ type: 'REMOVE_TASK', payload: taskId });
  }, []);

  const runHealthCheck = useCallback(async (): Promise<HealthCheckResult> => {
    const res = await fetch(`${API_BASE}/api/system/health`);
    return res.json();
  }, []);

  const value: SystemAgentContextType = {
    ...state,
    markAsRead,
    clearNotification,
    clearAllNotifications,
    markAllAsRead,
    executeAction,
    retryTask,
    cancelTask,
    runHealthCheck
  };

  return (
    <SystemAgentContext.Provider value={value}>
      {children}
    </SystemAgentContext.Provider>
  );
}

// Hook
export function useSystemAgent(): SystemAgentContextType {
  const context = useContext(SystemAgentContext);
  if (!context) {
    throw new Error('useSystemAgent must be used within SystemAgentProvider');
  }
  return context;
}
