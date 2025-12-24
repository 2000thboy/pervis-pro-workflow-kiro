import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  Download, 
  Clock, 
  HardDrive, 
  Cpu, 
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';
import { ErrorDisplay, UserFriendlyError } from './ErrorDisplay';

export interface RenderTask {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  estimated_duration?: number;
  estimated_size_mb?: number;
  output_path?: string;
  error?: UserFriendlyError;
  created_at: string;
  updated_at: string;
}

interface RenderStatusProps {
  task: RenderTask;
  onCancel?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  onDownload?: (taskId: string, outputPath: string) => void;
  className?: string;
}

export const RenderStatusComponent: React.FC<RenderStatusProps> = ({
  task,
  onCancel,
  onRetry,
  onDownload,
  className = ''
}) => {
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (task.status === 'processing') {
      const startTime = new Date(task.created_at).getTime();
      const interval = setInterval(() => {
        const now = Date.now();
        setElapsedTime(Math.floor((now - startTime) / 1000));
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [task.status, task.created_at]);

  const getStatusIcon = () => {
    switch (task.status) {
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'processing':
        return <Play className="w-5 h-5 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'cancelled':
        return <Square className="w-5 h-5 text-gray-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusText = () => {
    switch (task.status) {
      case 'pending':
        return '等待中';
      case 'processing':
        return '渲染中';
      case 'completed':
        return '已完成';
      case 'failed':
        return '失败';
      case 'cancelled':
        return '已取消';
      default:
        return '未知状态';
    }
  };

  const getStatusColor = () => {
    switch (task.status) {
      case 'pending':
        return 'border-yellow-200 bg-yellow-50';
      case 'processing':
        return 'border-blue-200 bg-blue-50';
      case 'completed':
        return 'border-green-200 bg-green-50';
      case 'failed':
        return 'border-red-200 bg-red-50';
      case 'cancelled':
        return 'border-gray-200 bg-gray-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatFileSize = (sizeInMB: number) => {
    if (sizeInMB < 1024) {
      return `${sizeInMB.toFixed(1)} MB`;
    }
    return `${(sizeInMB / 1024).toFixed(1)} GB`;
  };

  const getEstimatedTimeRemaining = () => {
    if (task.status !== 'processing' || task.progress <= 0) return null;
    
    const progressRate = task.progress / elapsedTime; // progress per second
    const remainingProgress = 100 - task.progress;
    const estimatedSeconds = remainingProgress / progressRate;
    
    return Math.max(0, Math.floor(estimatedSeconds));
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <Card className={`p-4 ${getStatusColor()}`}>
        <div className="space-y-4">
          {/* 状态标题 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <div>
                <h3 className="font-medium text-gray-900">
                  {getStatusText()}
                </h3>
                <p className="text-sm text-gray-600">
                  任务 ID: {task.id}
                </p>
              </div>
            </div>
            
            <div className="flex space-x-2">
              {task.status === 'processing' && onCancel && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onCancel(task.id)}
                >
                  <Square className="w-4 h-4 mr-2" />
                  取消
                </Button>
              )}
              
              {task.status === 'failed' && onRetry && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onRetry(task.id)}
                >
                  重试
                </Button>
              )}
              
              {task.status === 'completed' && task.output_path && onDownload && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onDownload(task.id, task.output_path!)}
                >
                  <Download className="w-4 h-4 mr-2" />
                  下载
                </Button>
              )}
            </div>
          </div>

          {/* 进度条 */}
          {(task.status === 'processing' || task.status === 'completed') && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>进度</span>
                <span>{task.progress.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(100, Math.max(0, task.progress))}%` }}
                />
              </div>
            </div>
          )}

          {/* 详细信息 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {task.status === 'processing' && (
              <>
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <div>
                    <p className="text-gray-600">已用时间</p>
                    <p className="font-medium">{formatTime(elapsedTime)}</p>
                  </div>
                </div>
                
                {getEstimatedTimeRemaining() !== null && (
                  <div className="flex items-center space-x-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <div>
                      <p className="text-gray-600">预计剩余</p>
                      <p className="font-medium">{formatTime(getEstimatedTimeRemaining()!)}</p>
                    </div>
                  </div>
                )}
              </>
            )}
            
            {task.estimated_duration && (
              <div className="flex items-center space-x-2">
                <Cpu className="w-4 h-4 text-gray-500" />
                <div>
                  <p className="text-gray-600">预计时长</p>
                  <p className="font-medium">{formatTime(task.estimated_duration)}</p>
                </div>
              </div>
            )}
            
            {task.estimated_size_mb && (
              <div className="flex items-center space-x-2">
                <HardDrive className="w-4 h-4 text-gray-500" />
                <div>
                  <p className="text-gray-600">预计大小</p>
                  <p className="font-medium">{formatFileSize(task.estimated_size_mb)}</p>
                </div>
              </div>
            )}
          </div>

          {/* 输出路径 */}
          {task.output_path && (
            <div className="bg-gray-100 rounded-lg p-3">
              <p className="text-sm text-gray-600 mb-1">输出文件:</p>
              <p className="font-mono text-sm text-gray-900 break-all">
                {task.output_path}
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* 错误信息 */}
      {task.error && (
        <ErrorDisplay
          error={task.error}
          onRetry={() => onRetry?.(task.id)}
        />
      )}
    </div>
  );
};

// 渲染队列组件
interface RenderQueueProps {
  tasks: RenderTask[];
  onCancel?: (taskId: string) => void;
  onRetry?: (taskId: string) => void;
  onDownload?: (taskId: string, outputPath: string) => void;
  className?: string;
}

export const RenderQueue: React.FC<RenderQueueProps> = ({
  tasks,
  onCancel,
  onRetry,
  onDownload,
  className = ''
}) => {
  if (tasks.length === 0) {
    return (
      <Card className={`p-8 text-center ${className}`}>
        <div className="text-gray-500">
          <Cpu className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>暂无渲染任务</p>
        </div>
      </Card>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900">
        渲染队列 ({tasks.length})
      </h3>
      
      {tasks.map((task) => (
        <RenderStatusComponent
          key={task.id}
          task={task}
          onCancel={onCancel}
          onRetry={onRetry}
          onDownload={onDownload}
        />
      ))}
    </div>
  );
};

export default RenderStatusComponent;