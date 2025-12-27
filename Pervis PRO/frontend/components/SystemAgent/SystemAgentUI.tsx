/**
 * SystemAgentUI - 系统 Agent 悬浮 UI 组件
 * 
 * 功能:
 * - 悬浮图标显示系统状态
 * - 展开面板显示任务和通知
 * - 支持拖拽调整位置
 */

import React, { useState, useRef, useEffect } from 'react';
import { useSystemAgent } from './SystemAgentContext';
import { TaskList } from './TaskList';
import { NotificationList } from './NotificationList';
import {
  Activity,
  Bell,
  X,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  Loader2,
  Wifi,
  WifiOff,
  Settings,
  Trash2
} from 'lucide-react';

interface SystemAgentUIProps {
  defaultPosition?: { x: number; y: number };
  defaultExpanded?: boolean;
}

export function SystemAgentUI({ 
  defaultPosition = { x: 20, y: 20 },
  defaultExpanded = false 
}: SystemAgentUIProps) {
  const {
    notifications,
    activeTasks,
    activeAgents,
    systemStatus,
    isConnected,
    unreadCount,
    clearAllNotifications,
    markAllAsRead,
    runHealthCheck
  } = useSystemAgent();

  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [activeTab, setActiveTab] = useState<'tasks' | 'notifications'>('tasks');
  const [position, setPosition] = useState(defaultPosition);
  const [isDragging, setIsDragging] = useState(false);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  
  const dragRef = useRef<{ startX: number; startY: number; startPosX: number; startPosY: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 拖拽处理
  const handleMouseDown = (e: React.MouseEvent) => {
    if (isExpanded) return;
    e.preventDefault();
    setIsDragging(true);
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startPosX: position.x,
      startPosY: position.y
    };
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging || !dragRef.current) return;
      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;
      setPosition({
        x: Math.max(0, dragRef.current.startPosX + dx),
        y: Math.max(0, dragRef.current.startPosY + dy)
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      dragRef.current = null;
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging]);

  // 获取状态图标和颜色
  const getStatusIcon = () => {
    if (!isConnected) return <WifiOff size={16} className="text-zinc-500" />;
    
    switch (systemStatus) {
      case 'working':
        return <Loader2 size={16} className="text-blue-400 animate-spin" />;
      case 'warning':
        return <AlertTriangle size={16} className="text-yellow-400" />;
      case 'error':
        return <AlertCircle size={16} className="text-red-400" />;
      default:
        return <CheckCircle size={16} className="text-green-400" />;
    }
  };

  const getStatusColor = () => {
    if (!isConnected) return 'bg-zinc-600';
    switch (systemStatus) {
      case 'working': return 'bg-blue-500';
      case 'warning': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-green-500';
    }
  };

  // 健康检查
  const handleHealthCheck = async () => {
    setHealthStatus('checking');
    try {
      const result = await runHealthCheck();
      setHealthStatus(result.status);
      setTimeout(() => setHealthStatus(null), 3000);
    } catch {
      setHealthStatus('error');
      setTimeout(() => setHealthStatus(null), 3000);
    }
  };

  // 悬浮图标
  const FloatingIcon = () => (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onClick={() => !isDragging && setIsExpanded(true)}
      className={`
        w-12 h-12 rounded-full shadow-lg cursor-pointer
        flex items-center justify-center relative
        transition-all duration-200 hover:scale-110
        ${getStatusColor()} bg-opacity-20 backdrop-blur-md
        border border-white/10
      `}
      style={{ 
        position: 'fixed',
        right: position.x,
        bottom: position.y,
        zIndex: 9999
      }}
    >
      {getStatusIcon()}
      
      {/* 未读徽章 */}
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-[10px] text-white font-bold flex items-center justify-center">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
      
      {/* 任务进度指示器 */}
      {activeTasks.length > 0 && systemStatus === 'working' && (
        <svg className="absolute inset-0 w-full h-full -rotate-90">
          <circle
            cx="24"
            cy="24"
            r="22"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-blue-500/30"
          />
          <circle
            cx="24"
            cy="24"
            r="22"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeDasharray={`${(activeTasks[0]?.progress || 0) * 1.38} 138`}
            className="text-blue-500 transition-all duration-300"
          />
        </svg>
      )}
    </div>
  );

  // 展开面板
  const ExpandedPanel = () => (
    <div
      className="fixed bg-zinc-900/95 backdrop-blur-xl rounded-xl shadow-2xl border border-zinc-800 overflow-hidden"
      style={{
        right: 20,
        bottom: 20,
        width: 380,
        maxHeight: 500,
        zIndex: 9999
      }}
    >
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800 bg-zinc-900">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
          <span className="text-sm font-bold text-white">系统状态</span>
          {!isConnected && (
            <span className="text-[10px] text-zinc-500 flex items-center gap-1">
              <WifiOff size={10} /> 离线
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleHealthCheck}
            className="p-1.5 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors"
            title="健康检查"
          >
            {healthStatus === 'checking' ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Activity size={14} />
            )}
          </button>
          <button
            onClick={() => setIsExpanded(false)}
            className="p-1.5 hover:bg-zinc-800 rounded text-zinc-400 hover:text-white transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* 健康状态提示 */}
      {healthStatus && healthStatus !== 'checking' && (
        <div className={`px-4 py-2 text-xs ${
          healthStatus === 'healthy' ? 'bg-green-500/10 text-green-400' :
          healthStatus === 'degraded' ? 'bg-yellow-500/10 text-yellow-400' :
          'bg-red-500/10 text-red-400'
        }`}>
          系统状态: {healthStatus === 'healthy' ? '健康' : healthStatus === 'degraded' ? '部分异常' : '异常'}
        </div>
      )}

      {/* 标签页 */}
      <div className="flex border-b border-zinc-800">
        <button
          onClick={() => setActiveTab('tasks')}
          className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors flex items-center justify-center gap-2 ${
            activeTab === 'tasks'
              ? 'text-white border-b-2 border-yellow-500 bg-zinc-800/50'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          <Loader2 size={12} className={activeTasks.length > 0 ? 'animate-spin' : ''} />
          任务 {activeTasks.length > 0 && `(${activeTasks.length})`}
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors flex items-center justify-center gap-2 ${
            activeTab === 'notifications'
              ? 'text-white border-b-2 border-yellow-500 bg-zinc-800/50'
              : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >
          <Bell size={12} />
          通知 {unreadCount > 0 && `(${unreadCount})`}
        </button>
      </div>

      {/* 内容区域 */}
      <div className="max-h-[350px] overflow-y-auto">
        {activeTab === 'tasks' ? (
          <TaskList tasks={activeTasks} agents={activeAgents} />
        ) : (
          <NotificationList notifications={notifications} />
        )}
      </div>

      {/* 底部操作 */}
      {activeTab === 'notifications' && notifications.length > 0 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-zinc-800 bg-zinc-900/50">
          <button
            onClick={markAllAsRead}
            className="text-[10px] text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            全部已读
          </button>
          <button
            onClick={clearAllNotifications}
            className="text-[10px] text-red-500/70 hover:text-red-400 transition-colors flex items-center gap-1"
          >
            <Trash2 size={10} />
            清空
          </button>
        </div>
      )}
    </div>
  );

  return isExpanded ? <ExpandedPanel /> : <FloatingIcon />;
}
