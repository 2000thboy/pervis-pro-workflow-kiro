import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Pause, 
  Play,
  RefreshCw,
  Trash2,
  BarChart3,
  Cpu,
  HardDrive,
  Zap,
  Users,
  Server
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

// 队列状态类型
export interface QueueStatus {
  is_running: boolean;
  queue_size: number;
  running_tasks: number;
  active_workers: number;
  stats: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    average_processing_time: number;
  };
}

// 系统统计类型
export interface SystemStats {
  cpu_percent: number;
  memory_percent: number;
  disk_usage: number;
  load_average: number[];
}

// 任务历史类型
export interface TaskHistory {
  id: string;
  task_type: string;
  asset_id: string;
  status: string;
  created_at: string;
  completed_at?: string;
  processing_time: number;
  error?: string;
}

// 组件属性
export interface BatchQueueMonitorProps {
  refreshInterval?: number;
  className?: string;
}

export const BatchQueueMonitor: React.FC<BatchQueueMonitorProps> = ({
  refreshInterval = 5000,
  className = ''
}) => {
  // 状态管理
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [taskHistory, setTaskHistory] = useState<TaskHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 加载队列状态
  const loadQueueStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/batch/queue/status');
      if (response.ok) {
        const data = await response.json();
        setQueueStatus(data.queue_status);
      } else {
        throw new Error(`状态查询失败: ${response.statusText}`);
      }
    } catch (err) {
      console.error('Failed to load queue status:', err);
      setError(err instanceof Error ? err.message : '状态查询失败');
    }
  }, []);

  // 加载系统统计
  const loadSystemStats = useCallback(async () => {
    try {
      const response = await fetch('/api/batch/stats');
      if (response.ok) {
        const data = await response.json();
        setSystemStats(data.system_stats);
      }
    } catch (err) {
      console.error('Failed to load system stats:', err);
    }
  }, []);

  // 加载任务历史
  const loadTaskHistory = useCallback(async () => {
    try {
      const response = await fetch('/api/batch/tasks/history?limit=50');
      if (response.ok) {
        const data = await response.json();
        setTaskHistory(data.tasks || []);
      }
    } catch (err) {
      console.error('Failed to load task history:', err);
    }
  }, []);

  // 刷新所有数据
  const refreshData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        loadQueueStatus(),
        loadSystemStats(),
        loadTaskHistory()
      ]);
    } catch (err) {
      setError('数据刷新失败');
    } finally {
      setLoading(false);
    }
  }, [loadQueueStatus, loadSystemStats, loadTaskHistory]);

  // 清理旧任务
  const cleanupOldTasks = async () => {
    try {
      const response = await fetch('/api/batch/queue/cleanup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_age_hours: 24 })
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`已清理 ${data.cleaned_count} 个旧任务`);
        refreshData();
      }
    } catch (error) {
      console.error('Failed to cleanup tasks:', error);
      alert('清理任务失败');
    }
  };

  // 自动刷新
  useEffect(() => {
    refreshData();
    
    if (autoRefresh) {
      const interval = setInterval(refreshData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [refreshData, autoRefresh, refreshInterval]);

  // 格式化时间
  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}秒`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)}分${Math.floor(seconds % 60)}秒`;
    } else {
      return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分`;
    }
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  };

  // 获取任务状态颜色
  const getTaskStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      case 'running':
        return 'text-blue-400';
      case 'pending':
        return 'text-yellow-400';
      default:
        return 'text-zinc-400';
    }
  };

  // 获取任务状态图标
  const getTaskStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-400" />;
      case 'running':
        return <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />;
      case 'pending':
        return <Clock size={16} className="text-yellow-400" />;
      default:
        return <Clock size={16} className="text-zinc-400" />;
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 控制面板 */}
      <Card title="队列监控" variant="elevated">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
              queueStatus?.is_running 
                ? 'bg-green-500/10 text-green-400' 
                : 'bg-red-500/10 text-red-400'
            }`}>
              <Activity size={16} />
              <span className="text-sm font-medium">
                {queueStatus?.is_running ? '运行中' : '已停止'}
              </span>
            </div>
            
            <div className="flex items-center gap-2 text-sm text-zinc-400">
              <span>队列: {queueStatus?.queue_size || 0}</span>
              <span>•</span>
              <span>运行: {queueStatus?.running_tasks || 0}</span>
              <span>•</span>
              <span>工作线程: {queueStatus?.active_workers || 0}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={autoRefresh ? 'primary' : 'ghost'}
              onClick={() => setAutoRefresh(!autoRefresh)}
              icon={autoRefresh ? Pause : Play}
            >
              {autoRefresh ? '暂停' : '开始'}自动刷新
            </Button>
            
            <Button
              size="sm"
              variant="ghost"
              onClick={refreshData}
              loading={loading}
              icon={RefreshCw}
            >
              刷新
            </Button>
            
            <Button
              size="sm"
              variant="ghost"
              onClick={cleanupOldTasks}
              icon={Trash2}
            >
              清理
            </Button>
          </div>
        </div>
        
        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}
      </Card>

      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 任务统计 */}
        <Card title="任务统计" variant="elevated">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">总任务数</span>
              <span className="text-lg font-bold text-white">
                {queueStatus?.stats.total_tasks || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">已完成</span>
              <span className="text-lg font-bold text-green-400">
                {queueStatus?.stats.completed_tasks || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">失败</span>
              <span className="text-lg font-bold text-red-400">
                {queueStatus?.stats.failed_tasks || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-zinc-400">平均用时</span>
              <span className="text-sm font-medium text-amber-400">
                {queueStatus?.stats.average_processing_time 
                  ? formatTime(queueStatus.stats.average_processing_time)
                  : '0秒'
                }
              </span>
            </div>
          </div>
        </Card>

        {/* CPU使用率 */}
        <Card title="CPU使用率" variant="elevated">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Cpu size={24} className="text-blue-400" />
              <div className="flex-1">
                <div className="text-2xl font-bold text-white">
                  {systemStats?.cpu_percent?.toFixed(1) || '0.0'}%
                </div>
                <div className="text-xs text-zinc-400">处理器占用</div>
              </div>
            </div>
            <div className="w-full bg-zinc-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${systemStats?.cpu_percent || 0}%` }}
              />
            </div>
            {systemStats?.load_average && (
              <div className="text-xs text-zinc-400">
                负载: {systemStats.load_average.map(l => l.toFixed(2)).join(', ')}
              </div>
            )}
          </div>
        </Card>

        {/* 内存使用率 */}
        <Card title="内存使用率" variant="elevated">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <Server size={24} className="text-green-400" />
              <div className="flex-1">
                <div className="text-2xl font-bold text-white">
                  {systemStats?.memory_percent?.toFixed(1) || '0.0'}%
                </div>
                <div className="text-xs text-zinc-400">内存占用</div>
              </div>
            </div>
            <div className="w-full bg-zinc-700 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${systemStats?.memory_percent || 0}%` }}
              />
            </div>
          </div>
        </Card>

        {/* 磁盘使用率 */}
        <Card title="磁盘使用率" variant="elevated">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <HardDrive size={24} className="text-purple-400" />
              <div className="flex-1">
                <div className="text-2xl font-bold text-white">
                  {systemStats?.disk_usage?.toFixed(1) || '0.0'}%
                </div>
                <div className="text-xs text-zinc-400">磁盘占用</div>
              </div>
            </div>
            <div className="w-full bg-zinc-700 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${systemStats?.disk_usage || 0}%` }}
              />
            </div>
          </div>
        </Card>
      </div>

      {/* 任务历史 */}
      <Card title="任务历史" variant="elevated">
        <div className="space-y-4">
          {taskHistory.length === 0 ? (
            <div className="text-center py-8 text-zinc-500">
              <BarChart3 size={48} className="mx-auto mb-3 opacity-50" />
              <p>暂无任务历史</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {taskHistory.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center gap-3 p-3 bg-zinc-800/30 rounded-lg hover:bg-zinc-800/50 transition-colors"
                >
                  {/* 状态图标 */}
                  <div className="flex-shrink-0">
                    {getTaskStatusIcon(task.status)}
                  </div>
                  
                  {/* 任务信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">
                          {task.task_type}
                        </span>
                        <span className="text-xs text-zinc-500">
                          #{task.asset_id.slice(0, 8)}
                        </span>
                      </div>
                      <span className={`text-xs font-medium ${getTaskStatusColor(task.status)}`}>
                        {task.status.toUpperCase()}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span>创建: {formatDate(task.created_at)}</span>
                      {task.completed_at && (
                        <span>完成: {formatDate(task.completed_at)}</span>
                      )}
                      <span>用时: {formatTime(task.processing_time)}</span>
                    </div>
                    
                    {/* 错误信息 */}
                    {task.error && (
                      <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
                        {task.error}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default BatchQueueMonitor;