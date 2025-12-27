/**
 * NotificationToast - 通知 Toast 组件
 * 
 * 显示新通知的弹出提示
 */

import React, { useEffect, useState } from 'react';
import { useSystemAgent } from './SystemAgentContext';
import type { Notification } from './types';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  X
} from 'lucide-react';

interface ToastItem {
  notification: Notification;
  isExiting: boolean;
}

// 通知图标
const getNotificationIcon = (type: string, level: string) => {
  if (level === 'critical' || type === 'error') {
    return <AlertCircle size={16} className="text-red-400" />;
  }
  if (level === 'warning' || type === 'warning') {
    return <AlertTriangle size={16} className="text-yellow-400" />;
  }
  if (type === 'task') {
    return <CheckCircle size={16} className="text-green-400" />;
  }
  return <Info size={16} className="text-blue-400" />;
};

// 背景颜色
const getBackgroundColor = (type: string, level: string) => {
  if (level === 'critical' || type === 'error') {
    return 'bg-red-500/10 border-red-500/30';
  }
  if (level === 'warning' || type === 'warning') {
    return 'bg-yellow-500/10 border-yellow-500/30';
  }
  if (type === 'task') {
    return 'bg-green-500/10 border-green-500/30';
  }
  return 'bg-blue-500/10 border-blue-500/30';
};

export function NotificationToast() {
  const { notifications, markAsRead } = useSystemAgent();
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [seenIds, setSeenIds] = useState<Set<string>>(new Set());

  // 监听新通知
  useEffect(() => {
    const newNotifications = notifications.filter(
      n => !n.isRead && !seenIds.has(n.id)
    );

    if (newNotifications.length > 0) {
      // 添加新 toast
      const newToasts = newNotifications.map(n => ({
        notification: n,
        isExiting: false
      }));
      
      setToasts(prev => [...newToasts, ...prev].slice(0, 5));
      setSeenIds(prev => {
        const next = new Set(prev);
        newNotifications.forEach(n => next.add(n.id));
        return next;
      });

      // 自动移除
      newNotifications.forEach(n => {
        setTimeout(() => {
          setToasts(prev => 
            prev.map(t => 
              t.notification.id === n.id ? { ...t, isExiting: true } : t
            )
          );
          setTimeout(() => {
            setToasts(prev => prev.filter(t => t.notification.id !== n.id));
          }, 300);
        }, 5000);
      });
    }
  }, [notifications, seenIds]);

  const handleDismiss = (id: string) => {
    setToasts(prev => 
      prev.map(t => 
        t.notification.id === id ? { ...t, isExiting: true } : t
      )
    );
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.notification.id !== id));
    }, 300);
    markAsRead(id);
  };

  if (toasts.length === 0) return null;

  return (
    <div 
      className="fixed top-4 right-4 z-[10000] flex flex-col gap-2"
      style={{ maxWidth: 360 }}
    >
      {toasts.map(({ notification, isExiting }) => (
        <div
          key={notification.id}
          className={`
            flex items-start gap-3 p-4 rounded-lg border backdrop-blur-xl
            shadow-lg transition-all duration-300
            ${getBackgroundColor(notification.type, notification.level)}
            ${isExiting 
              ? 'opacity-0 translate-x-full' 
              : 'opacity-100 translate-x-0 animate-in slide-in-from-right-5'
            }
          `}
        >
          {/* 图标 */}
          <div className="mt-0.5">
            {getNotificationIcon(notification.type, notification.level)}
          </div>
          
          {/* 内容 */}
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white">
              {notification.title}
            </div>
            <div className="text-xs text-zinc-400 mt-1 line-clamp-2">
              {notification.message}
            </div>
          </div>
          
          {/* 关闭按钮 */}
          <button
            onClick={() => handleDismiss(notification.id)}
            className="p-1 hover:bg-white/10 rounded transition-colors"
          >
            <X size={14} className="text-zinc-400 hover:text-white" />
          </button>
        </div>
      ))}
    </div>
  );
}
