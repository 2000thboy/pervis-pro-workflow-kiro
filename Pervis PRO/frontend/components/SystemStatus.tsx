import React, { useState, useEffect } from 'react';
import { 
  Monitor, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  ArrowLeft,
  Settings,
  Download
} from 'lucide-react';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import SystemDiagnostics from './ui/SystemDiagnostics';
import { RenderQueue, RenderTask } from './ui/RenderStatus';
import { ErrorNotification, UserFriendlyError } from './ui/ErrorDisplay';

interface SystemStatusProps {
  onBack?: () => void;
  className?: string;
}

export const SystemStatus: React.FC<SystemStatusProps> = ({
  onBack,
  className = ''
}) => {
  const [renderTasks, setRenderTasks] = useState<RenderTask[]>([]);
  const [systemErrors, setSystemErrors] = useState<UserFriendlyError[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchRenderTasks = async () => {
    try {
      const response = await fetch('/api/render/tasks');
      const data = await response.json();
      setRenderTasks(data.tasks || []);
    } catch (error) {
      console.error('Failed to fetch render tasks:', error);
    }
  };

  const fetchSystemErrors = async () => {
    try {
      const response = await fetch('/api/system/errors');
      const data = await response.json();
      setSystemErrors(data.errors || []);
    } catch (error) {
      console.error('Failed to fetch system errors:', error);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchRenderTasks(), fetchSystemErrors()]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
    
    // 定期刷新数据
    const interval = setInterval(refreshData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCancelRender = async (taskId: string) => {
    try {
      await fetch(`/api/render/tasks/${taskId}/cancel`, {
        method: 'POST'
      });
      await fetchRenderTasks();
    } catch (error) {
      console.error('Failed to cancel render task:', error);
    }
  };

  const handleRetryRender = async (taskId: string) => {
    try {
      await fetch(`/api/render/tasks/${taskId}/retry`, {
        method: 'POST'
      });
      await fetchRenderTasks();
    } catch (error) {
      console.error('Failed to retry render task:', error);
    }
  };

  const handleDownloadRender = async (taskId: string, outputPath: string) => {
    try {
      const response = await fetch(`/api/render/tasks/${taskId}/download`);
      const blob = await response.blob();
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = outputPath.split('/').pop() || 'render_output.mp4';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download render:', error);
    }
  };

  const handleRetryError = async (errorCode: string) => {
    // 根据错误代码执行相应的重试逻辑
    console.log('Retrying error:', errorCode);
    await refreshData();
  };

  const handleDismissError = (errorCode: string) => {
    setSystemErrors(errors => errors.filter(e => e.error_code !== errorCode));
  };

  const getSystemStatusSummary = () => {
    const hasErrors = systemErrors.length > 0;
    const hasFailedTasks = renderTasks.some(task => task.status === 'failed');
    const hasProcessingTasks = renderTasks.some(task => task.status === 'processing');
    
    if (hasErrors || hasFailedTasks) {
      return {
        status: 'error',
        message: '系统存在问题需要处理',
        icon: AlertTriangle,
        color: 'text-red-500'
      };
    }
    
    if (hasProcessingTasks) {
      return {
        status: 'processing',
        message: '系统正在处理任务',
        icon: RefreshCw,
        color: 'text-blue-500'
      };
    }
    
    return {
      status: 'healthy',
      message: '系统运行正常',
      icon: CheckCircle,
      color: 'text-green-500'
    };
  };

  const statusSummary = getSystemStatusSummary();

  return (
    <div className={`min-h-screen bg-zinc-950 text-zinc-200 ${className}`}>
      {/* 标题栏 */}
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {onBack && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回
              </Button>
            )}
            <div className="flex items-center space-x-3">
              <Monitor className="w-6 h-6 text-blue-500" />
              <h1 className="text-xl font-semibold">系统状态</h1>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <statusSummary.icon className={`w-5 h-5 ${statusSummary.color} ${
                statusSummary.status === 'processing' ? 'animate-spin' : ''
              }`} />
              <span className="text-sm">{statusSummary.message}</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshData}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 系统错误通知 */}
        {systemErrors.length > 0 && (
          <ErrorNotification
            errors={systemErrors}
            onRetry={handleRetryError}
            onDismiss={handleDismissError}
          />
        )}

        {/* 系统诊断 */}
        <SystemDiagnostics autoRefresh={true} />

        {/* 渲染队列 */}
        <RenderQueue
          tasks={renderTasks}
          onCancel={handleCancelRender}
          onRetry={handleRetryRender}
          onDownload={handleDownloadRender}
        />

        {/* 快速操作 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">快速操作</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="flex items-center justify-center space-x-2 p-4"
              onClick={() => window.open('/api/system/logs', '_blank')}
            >
              <Download className="w-5 h-5" />
              <span>下载系统日志</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex items-center justify-center space-x-2 p-4"
              onClick={() => fetch('/api/system/cleanup', { method: 'POST' })}
            >
              <Settings className="w-5 h-5" />
              <span>清理临时文件</span>
            </Button>
            
            <Button
              variant="outline"
              className="flex items-center justify-center space-x-2 p-4"
              onClick={() => fetch('/api/system/restart', { method: 'POST' })}
            >
              <RefreshCw className="w-5 h-5" />
              <span>重启服务</span>
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SystemStatus;