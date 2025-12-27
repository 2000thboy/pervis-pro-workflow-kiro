/**
 * NotificationList - 通知列表组件
 * 
 * 显示系统通知，支持操作按钮
 */

import React from 'react';
import { useSystemAgent } from './SystemAgentContext';
import type { Notification } from './types';
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  X,
  ExternalLink,
  RefreshCw
} from 'lucide-react';

interface NotificationListProps {
  notifications: Notification[];
}

// 通知图标
const getNotificationIcon = (type: string, level: string) => {
  if (level === 'critical' || type === 'error') {
    return <AlertCircle size={14} className="text-red-400" />;
  }
  if (level === 'warning' || type === 'warning') {
    return <AlertTriangle size={14} className="text-yellow-400" />;
  }
  if (type === 'task') {
    return <CheckCircle size={14} className="text-green-400" />;
  }
  return <Info size={14} className="text-blue-400" />;
};

// 时间格式化
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  return date.toLocaleDateString();
};

// 单个通知项
function NotificationItem({ notification }: { notification: Notification }) {
  const { markAsRead, clearNotification, executeAction } = useSystemAgent();
  
  const handleClick = () => {
    if (!notification.isRead) {
      markAsRead(notification.id);
    }
  };

  const handleAction = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (notification.action) {
      executeAction(notification.action);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    clearNotification(notification.id);
  };

  return (
    <div
      onClick={handleClick}
      className={`
        px-4 py-3 border-b border-zinc-800/50 last:border-0 
        hover:bg-zinc-800/30 transition-colors cursor-pointer
        ${!notification.isRead ? 'bg-zinc-800/20' : ''}
      `}
    >
      <div className="flex items-start gap-3">
        {/* 图标 */}
        <div className="mt-0.5">
          {getNotificationIcon(notification.type, notification.level)}
        </div>
        
        {/* 内容 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className={`text-xs font-medium ${notification.isRead ? 'text-zinc-400' : 'text-white'}`}>
              {notification.title}
            </span>
            <div className="flex items-center gap-1">
              <span className="text-[10px] text-zinc-500 whitespace-nowrap">
                {formatTime(notification.timestamp)}
              </span>
              <button
                onClick={handleDelete}
                className="p-1 hover:bg-zinc-700 rounded opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <X size={10} className="text-zinc-500 hover:text-zinc-300" />
              </button>
            </div>
          </div>
          
          <p className={`text-[11px] mt-1 ${notification.isRead ? 'text-zinc-500' : 'text-zinc-400'}`}>
            {notification.message}
          </p>
          
          {/* 未读指示器 */}
          {!notification.isRead && (
            <div className="absolute left-1 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-blue-500 rounded-full" />
          )}
          
          {/* 操作按钮 */}
          {notification.action && (
            <button
              onClick={handleAction}
              className="mt-2 px-3 py-1.5 text-[10px] font-medium rounded
                bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white
                transition-colors flex items-center gap-1.5"
            >
              {notification.action.type === 'link' ? (
                <ExternalLink size={10} />
              ) : notification.action.action === 'retry_task' ? (
                <RefreshCw size={10} />
              ) : null}
              {notification.action.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function NotificationList({ notifications }: NotificationListProps) {
  if (notifications.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
        <Bell size={32} className="mb-3 opacity-30" />
        <span className="text-xs">暂无通知</span>
        <span className="text-[10px] opacity-50 mt-1">系统运行正常</span>
      </div>
    );
  }

  return (
    <div className="relative">
      {notifications.map(notification => (
        <div key={notification.id} className="relative group">
          <NotificationItem notification={notification} />
        </div>
      ))}
    </div>
  );
}
