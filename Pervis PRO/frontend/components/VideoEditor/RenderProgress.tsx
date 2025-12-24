import React, { useState, useEffect } from 'react';
import { Download, CheckCircle, AlertCircle, Clock, X } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

interface RenderTask {
  id: string;
  timeline_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  error_message?: string;
  output_path?: string;
  file_size?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

interface RenderProgressProps {
  taskId?: string;
  onComplete?: (outputPath: string) => void;
  onError?: (error: string) => void;
}

const RenderProgress: React.FC<RenderProgressProps> = ({
  taskId,
  onComplete,
  onError
}) => {
  const [task, setTask] = useState<RenderTask | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  
  // 轮询任务状态
  useEffect(() => {
    if (!taskId) return;
    
    setIsPolling(true);
    
    const pollStatus = async () => {
      try {
        const response = await fetch(`/api/render/${taskId}/status`);
        if (response.ok) {
          const taskData = await response.json();
          setTask(taskData);
          
          // 检查是否完成
          if (taskData.status === 'completed') {
            setIsPolling(false);
            onComplete?.(taskData.output_path);
          } else if (taskData.status === 'failed') {
            setIsPolling(false);
            onError?.(taskData.error_message || '渲染失败');
          } else if (taskData.status === 'cancelled') {
            setIsPolling(false);
          }
        }
      } catch (error) {
        console.error('获取渲染状态失败:', error);
        setIsPolling(false);
        onError?.('获取渲染状态失败');
      }
    };
    
    // 立即执行一次
    pollStatus();
    
    // 设置轮询
    const interval = setInterval(pollStatus, 2000);
    
    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, [taskId, onComplete, onError]);
  
  // 取消渲染
  const handleCancel = async () => {
    if (!taskId) return;
    
    try {
      const response = await fetch(`/api/render/${taskId}/cancel`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setTask(prev => prev ? { ...prev, status: 'cancelled' } : null);
        setIsPolling(false);
      }
    } catch (error) {
      console.error('取消渲染失败:', error);
    }
  };
  
  // 下载文件
  const handleDownload = async () => {
    if (!taskId || !task?.output_path) return;
    
    try {
      const response = await fetch(`/api/render/${taskId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `render-${taskId}.mp4`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('下载失败:', error);
    }
  };
  
  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // 格式化时间
  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };
  
  // 计算预估剩余时间
  const getEstimatedTimeRemaining = (): string => {
    if (!task || task.status !== 'processing' || task.progress === 0) {
      return '计算中...';
    }
    
    const startTime = task.started_at ? new Date(task.started_at).getTime() : Date.now();
    const elapsed = Date.now() - startTime;
    const progressRate = task.progress / elapsed;
    const remaining = (100 - task.progress) / progressRate;
    
    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);
    
    if (minutes > 0) {
      return `约 ${minutes} 分 ${seconds} 秒`;
    } else {
      return `约 ${seconds} 秒`;
    }
  };
  
  if (!task) {
    return (
      <Card title="渲染状态" variant="elevated">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full" />
          <span className="ml-3 text-zinc-400">初始化渲染任务...</span>
        </div>
      </Card>
    );
  }
  
  return (
    <Card title="渲染进度" variant="elevated">
      <div className="space-y-4">
        {/* 状态指示器 */}
        <div className="flex items-center gap-3">
          {task.status === 'pending' && (
            <>
              <Clock size={20} className="text-yellow-400" />
              <span className="text-yellow-400">等待开始</span>
            </>
          )}
          {task.status === 'processing' && (
            <>
              <div className="animate-spin w-5 h-5 border-2 border-blue-400 border-t-transparent rounded-full" />
              <span className="text-blue-400">正在渲染</span>
            </>
          )}
          {task.status === 'completed' && (
            <>
              <CheckCircle size={20} className="text-green-400" />
              <span className="text-green-400">渲染完成</span>
            </>
          )}
          {task.status === 'failed' && (
            <>
              <AlertCircle size={20} className="text-red-400" />
              <span className="text-red-400">渲染失败</span>
            </>
          )}
          {task.status === 'cancelled' && (
            <>
              <X size={20} className="text-zinc-400" />
              <span className="text-zinc-400">已取消</span>
            </>
          )}
        </div>
        
        {/* 进度条 */}
        {(task.status === 'processing' || task.status === 'completed') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>进度</span>
              <span>{task.progress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-zinc-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-300 ${
                  task.status === 'completed' ? 'bg-green-500' : 'bg-blue-500'
                }`}
                style={{ width: `${task.progress}%` }}
              />
            </div>
          </div>
        )}
        
        {/* 详细信息 */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-zinc-400">任务ID</div>
            <div className="font-mono text-xs">{task.id.slice(0, 8)}...</div>
          </div>
          
          <div>
            <div className="text-zinc-400">创建时间</div>
            <div>{formatTime(task.created_at)}</div>
          </div>
          
          {task.started_at && (
            <div>
              <div className="text-zinc-400">开始时间</div>
              <div>{formatTime(task.started_at)}</div>
            </div>
          )}
          
          {task.completed_at && (
            <div>
              <div className="text-zinc-400">完成时间</div>
              <div>{formatTime(task.completed_at)}</div>
            </div>
          )}
          
          {task.file_size && (
            <div>
              <div className="text-zinc-400">文件大小</div>
              <div>{formatFileSize(task.file_size)}</div>
            </div>
          )}
          
          {task.status === 'processing' && (
            <div>
              <div className="text-zinc-400">预估剩余</div>
              <div>{getEstimatedTimeRemaining()}</div>
            </div>
          )}
        </div>
        
        {/* 错误信息 */}
        {task.status === 'failed' && task.error_message && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <div className="text-red-400 text-sm font-medium mb-1">错误详情</div>
            <div className="text-red-300 text-sm">{task.error_message}</div>
          </div>
        )}
        
        {/* 操作按钮 */}
        <div className="flex items-center gap-3 pt-2">
          {task.status === 'completed' && task.output_path && (
            <Button onClick={handleDownload} className="flex-1">
              <Download size={16} className="mr-2" />
              下载视频
            </Button>
          )}
          
          {(task.status === 'pending' || task.status === 'processing') && (
            <Button
              variant="ghost"
              onClick={handleCancel}
              className="text-red-400 hover:text-red-300"
            >
              <X size={16} className="mr-2" />
              取消渲染
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
};

export default RenderProgress;