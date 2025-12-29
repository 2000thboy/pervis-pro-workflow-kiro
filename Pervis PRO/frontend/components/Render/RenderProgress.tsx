/**
 * 渲染进度组件
 * 
 * Phase 2 Task 2.1: 视频渲染完善
 * - SSE 实时进度显示
 * - 进度条动画
 * - 取消/重试功能
 */

import React, { useEffect, useState, useCallback } from 'react';

interface RenderProgressData {
  task_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  message: string;
  current_stage: string;
  elapsed_time: number;
  estimated_remaining: number;
  output_path?: string;
  file_size?: number;
  error?: string;
  timestamp: string;
}

interface RenderProgressProps {
  taskId: string;
  onComplete?: (data: RenderProgressData) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
  showDownload?: boolean;
}

const formatTime = (seconds: number): string => {
  if (seconds < 60) return `${Math.round(seconds)}秒`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}分${secs}秒`;
};

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
};

export const RenderProgress: React.FC<RenderProgressProps> = ({
  taskId,
  onComplete,
  onError,
  onCancel,
  showDownload = true
}) => {
  const [progress, setProgress] = useState<RenderProgressData | null>(null);
  const [usePolling, setUsePolling] = useState(false);

  // SSE 连接
  useEffect(() => {
    if (!taskId) return;

    let eventSource: EventSource | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    const connectSSE = () => {
      try {
        eventSource = new EventSource(`/api/render/progress/stream/${taskId}`);
        
        eventSource.onmessage = (event) => {
          if (event.data.startsWith(':')) return; // 心跳
          
          try {
            const data: RenderProgressData = JSON.parse(event.data);
            setProgress(data);
            
            if (data.status === 'completed') {
              onComplete?.(data);
              eventSource?.close();
            } else if (data.status === 'failed') {
              onError?.(data.error || '渲染失败');
              eventSource?.close();
            } else if (data.status === 'cancelled') {
              eventSource?.close();
            }
          } catch (e) {
            console.error('解析 SSE 数据失败:', e);
          }
        };

        eventSource.onerror = () => {
          console.warn('SSE 连接失败，切换到轮询模式');
          eventSource?.close();
          setUsePolling(true);
        };
      } catch (e) {
        console.warn('SSE 不支持，使用轮询模式');
        setUsePolling(true);
      }
    };

    const startPolling = () => {
      const poll = async () => {
        try {
          const response = await fetch(`/api/render/progress/${taskId}`);
          const result = await response.json();
          
          if (result.status === 'success' && result.progress) {
            const data = result.progress as RenderProgressData;
            setProgress(data);
            
            if (data.status === 'completed') {
              onComplete?.(data);
              if (pollInterval) clearInterval(pollInterval);
            } else if (data.status === 'failed') {
              onError?.(data.error || '渲染失败');
              if (pollInterval) clearInterval(pollInterval);
            } else if (data.status === 'cancelled') {
              if (pollInterval) clearInterval(pollInterval);
            }
          }
        } catch (e) {
          console.error('轮询失败:', e);
        }
      };

      poll();
      pollInterval = setInterval(poll, 2000);
    };

    if (usePolling) {
      startPolling();
    } else {
      connectSSE();
    }

    return () => {
      eventSource?.close();
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [taskId, usePolling, onComplete, onError]);

  const handleCancel = useCallback(async () => {
    try {
      const response = await fetch(`/api/render/cancel/${taskId}`, {
        method: 'POST'
      });
      if (response.ok) {
        onCancel?.();
      }
    } catch (e) {
      console.error('取消失败:', e);
    }
  }, [taskId, onCancel]);

  const handleDownload = useCallback(() => {
    window.open(`/api/render/download/${taskId}`, '_blank');
  }, [taskId]);

  if (!progress) {
    return (
      <div className="render-progress render-progress--loading">
        <div className="render-progress__spinner" />
        <span>连接中...</span>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    pending: '#6b7280',
    processing: '#3b82f6',
    completed: '#10b981',
    failed: '#ef4444',
    cancelled: '#f59e0b'
  };

  const statusLabels: Record<string, string> = {
    pending: '等待中',
    processing: '渲染中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  };

  return (
    <div className="render-progress">
      {/* 状态标签 */}
      <div className="render-progress__header">
        <span 
          className="render-progress__status"
          style={{ backgroundColor: statusColors[progress.status] }}
        >
          {statusLabels[progress.status]}
        </span>
        <span className="render-progress__stage">
          {progress.current_stage || progress.message}
        </span>
      </div>

      {/* 进度条 */}
      <div className="render-progress__bar-container">
        <div 
          className="render-progress__bar"
          style={{ 
            width: `${progress.progress}%`,
            backgroundColor: statusColors[progress.status]
          }}
        />
        <span className="render-progress__percentage">
          {progress.progress.toFixed(1)}%
        </span>
      </div>

      {/* 时间信息 */}
      {progress.status === 'processing' && (
        <div className="render-progress__time">
          <span>已用时: {formatTime(progress.elapsed_time)}</span>
          {progress.estimated_remaining > 0 && (
            <span>预计剩余: {formatTime(progress.estimated_remaining)}</span>
          )}
        </div>
      )}

      {/* 完成信息 */}
      {progress.status === 'completed' && progress.file_size && (
        <div className="render-progress__result">
          <span>文件大小: {formatFileSize(progress.file_size)}</span>
          <span>总用时: {formatTime(progress.elapsed_time)}</span>
        </div>
      )}

      {/* 错误信息 */}
      {progress.status === 'failed' && progress.error && (
        <div className="render-progress__error">
          {progress.error}
        </div>
      )}

      {/* 操作按钮 */}
      <div className="render-progress__actions">
        {progress.status === 'processing' && (
          <button 
            className="render-progress__btn render-progress__btn--cancel"
            onClick={handleCancel}
          >
            取消
          </button>
        )}
        
        {progress.status === 'completed' && showDownload && (
          <button 
            className="render-progress__btn render-progress__btn--download"
            onClick={handleDownload}
          >
            下载视频
          </button>
        )}
      </div>

      <style>{`
        .render-progress {
          padding: 16px;
          background: #1f2937;
          border-radius: 8px;
          color: #e5e7eb;
        }
        
        .render-progress--loading {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #9ca3af;
        }
        
        .render-progress__spinner {
          width: 16px;
          height: 16px;
          border: 2px solid #4b5563;
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        
        .render-progress__header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 12px;
        }
        
        .render-progress__status {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          color: white;
        }
        
        .render-progress__stage {
          color: #9ca3af;
          font-size: 14px;
        }
        
        .render-progress__bar-container {
          position: relative;
          height: 8px;
          background: #374151;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 8px;
        }
        
        .render-progress__bar {
          height: 100%;
          transition: width 0.3s ease;
        }
        
        .render-progress__percentage {
          position: absolute;
          right: 0;
          top: -20px;
          font-size: 12px;
          color: #9ca3af;
        }
        
        .render-progress__time,
        .render-progress__result {
          display: flex;
          justify-content: space-between;
          font-size: 12px;
          color: #6b7280;
          margin-top: 8px;
        }
        
        .render-progress__error {
          margin-top: 8px;
          padding: 8px;
          background: #7f1d1d;
          border-radius: 4px;
          font-size: 12px;
          color: #fca5a5;
        }
        
        .render-progress__actions {
          display: flex;
          gap: 8px;
          margin-top: 12px;
        }
        
        .render-progress__btn {
          padding: 8px 16px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        
        .render-progress__btn:hover {
          opacity: 0.9;
        }
        
        .render-progress__btn--cancel {
          background: #4b5563;
          color: white;
        }
        
        .render-progress__btn--download {
          background: #10b981;
          color: white;
        }
      `}</style>
    </div>
  );
};

export default RenderProgress;
