import React, { useState, useCallback, useRef } from 'react';
import { 
  Upload, 
  X, 
  Play, 
  Pause, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  Zap,
  Settings
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';

// 批量上传任务类型
export interface BatchUploadTask {
  id: string;
  file: File;
  filename: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'failed';
  progress: number;
  taskId?: string;
  error?: string;
  result?: any;
  estimatedTime?: number;
  startTime?: number;
  endTime?: number;
}

// 批量上传配置
export interface BatchUploadConfig {
  projectId: string;
  priority: 'low' | 'normal' | 'high' | 'urgent';
  enableTranscription: boolean;
  enableVisualAnalysis: boolean;
  maxConcurrentUploads: number;
}

// 组件属性
export interface BatchUploadPanelProps {
  projectId: string;
  onUploadComplete?: (results: BatchUploadTask[]) => void;
  onTaskUpdate?: (task: BatchUploadTask) => void;
  className?: string;
}

export const BatchUploadPanel: React.FC<BatchUploadPanelProps> = ({
  projectId,
  onUploadComplete,
  onTaskUpdate,
  className = ''
}) => {
  // 状态管理
  const [tasks, setTasks] = useState<BatchUploadTask[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [config, setConfig] = useState<BatchUploadConfig>({
    projectId,
    priority: 'normal',
    enableTranscription: true,
    enableVisualAnalysis: true,
    maxConcurrentUploads: 3
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);
  const [isDragging, setIsDragging] = useState(false);

  // 文件选择处理
  const handleFileSelect = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(file => {
      // 验证文件类型
      const validTypes = [
        'video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv',
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp',
        'audio/mp3', 'audio/wav', 'audio/aac', 'audio/flac'
      ];
      return validTypes.includes(file.type) || file.name.match(/\.(mp4|avi|mov|wmv|flv|jpg|jpeg|png|gif|bmp|mp3|wav|aac|flac)$/i);
    });

    const newTasks: BatchUploadTask[] = validFiles.map(file => ({
      id: `task-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
      file,
      filename: file.name,
      size: file.size,
      type: file.type || 'unknown',
      status: 'pending',
      progress: 0
    }));

    setTasks(prev => [...prev, ...newTasks]);
  }, []);

  // 文件输入处理
  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      handleFileSelect(files);
    }
    // 清空input以允许重复选择同一文件
    event.target.value = '';
  };

  // 拖拽处理
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;

    const files = e.dataTransfer.files;
    if (files) {
      handleFileSelect(files);
    }
  };

  // 移除任务
  const removeTask = (taskId: string) => {
    setTasks(prev => prev.filter(task => task.id !== taskId));
  };

  // 清空所有任务
  const clearAllTasks = () => {
    setTasks([]);
  };

  // 开始批量上传
  const startBatchUpload = async () => {
    if (tasks.length === 0) return;

    setIsUploading(true);

    try {
      // 准备FormData
      const formData = new FormData();
      
      // 添加文件
      tasks.forEach(task => {
        formData.append('files', task.file);
      });
      
      // 添加配置参数
      formData.append('project_id', config.projectId);
      formData.append('priority', config.priority);
      formData.append('enable_transcription', config.enableTranscription.toString());
      formData.append('enable_visual_analysis', config.enableVisualAnalysis.toString());

      // 更新任务状态为上传中
      setTasks(prev => prev.map(task => ({
        ...task,
        status: 'uploading' as const,
        startTime: Date.now()
      })));

      // 发送批量上传请求
      const response = await fetch('/api/batch/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`);
      }

      const result = await response.json();
      
      // 更新任务状态和任务ID
      setTasks(prev => prev.map((task, index) => ({
        ...task,
        status: 'processing' as const,
        taskId: result.task_ids[index],
        estimatedTime: result.estimated_processing_time / result.total_files
      })));

      // 开始监控任务进度
      monitorTaskProgress(result.task_ids);

    } catch (error) {
      console.error('批量上传失败:', error);
      
      // 更新任务状态为失败
      setTasks(prev => prev.map(task => ({
        ...task,
        status: 'failed' as const,
        error: error instanceof Error ? error.message : '上传失败'
      })));
    } finally {
      setIsUploading(false);
    }
  };

  // 监控任务进度
  const monitorTaskProgress = async (taskIds: string[]) => {
    const checkInterval = 2000; // 2秒检查一次
    const maxChecks = 300; // 最多检查10分钟
    let checkCount = 0;

    const checkProgress = async () => {
      if (checkCount >= maxChecks) {
        console.warn('任务监控超时');
        return;
      }

      try {
        const statusPromises = taskIds.map(taskId => 
          fetch(`/api/batch/task/${taskId}`).then(res => res.json())
        );
        
        const statuses = await Promise.all(statusPromises);
        
        // 更新任务状态
        setTasks(prev => prev.map((task, index) => {
          const status = statuses[index];
          if (!status || status.error) {
            return {
              ...task,
              status: 'failed' as const,
              error: status?.error || '状态查询失败'
            };
          }

          const newTask = {
            ...task,
            progress: status.progress * 100,
            result: status.result
          };

          // 更新状态
          if (status.status === 'completed') {
            newTask.status = 'completed';
            newTask.endTime = Date.now();
            onTaskUpdate?.(newTask);
          } else if (status.status === 'failed') {
            newTask.status = 'failed';
            newTask.error = status.error || '处理失败';
          } else {
            newTask.status = 'processing';
          }

          return newTask;
        }));

        // 检查是否所有任务都完成
        const allCompleted = statuses.every(status => 
          status.status === 'completed' || status.status === 'failed'
        );

        if (allCompleted) {
          const completedTasks = tasks.filter(task => task.status === 'completed');
          onUploadComplete?.(completedTasks);
        } else {
          // 继续监控
          checkCount++;
          setTimeout(checkProgress, checkInterval);
        }

      } catch (error) {
        console.error('任务状态检查失败:', error);
        setTimeout(checkProgress, checkInterval);
      }
    };

    // 开始检查
    setTimeout(checkProgress, checkInterval);
  };

  // 暂停/恢复上传
  const toggleUpload = () => {
    // TODO: 实现暂停/恢复逻辑
    console.log('Toggle upload');
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  // 格式化时间
  const formatTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: BatchUploadTask['status']) => {
    switch (status) {
      case 'pending':
        return <Clock size={16} className="text-zinc-400" />;
      case 'uploading':
      case 'processing':
        return <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />;
      case 'completed':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-400" />;
      default:
        return <Clock size={16} className="text-zinc-400" />;
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: BatchUploadTask['status']) => {
    switch (status) {
      case 'pending':
        return 'text-zinc-400';
      case 'uploading':
      case 'processing':
        return 'text-blue-400';
      case 'completed':
        return 'text-green-400';
      case 'failed':
        return 'text-red-400';
      default:
        return 'text-zinc-400';
    }
  };

  // 计算总体统计
  const stats = {
    total: tasks.length,
    pending: tasks.filter(t => t.status === 'pending').length,
    processing: tasks.filter(t => t.status === 'uploading' || t.status === 'processing').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
    totalSize: tasks.reduce((sum, task) => sum + task.size, 0)
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 上传区域 */}
      <Card title="批量上传" variant="elevated">
        <div className="space-y-4">
          {/* 拖拽上传区域 */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
              isDragging 
                ? 'border-amber-400 bg-amber-500/10' 
                : 'border-zinc-600 hover:border-zinc-500'
            }`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <Upload size={48} className={`mx-auto mb-4 ${isDragging ? 'text-amber-400' : 'text-zinc-500'}`} />
            <h3 className="text-lg font-medium text-white mb-2">
              {isDragging ? '释放文件开始上传' : '拖拽文件到此处'}
            </h3>
            <p className="text-zinc-400 mb-4">
              支持视频、图片、音频文件，最多50个文件
            </p>
            
            <div className="flex items-center justify-center gap-3">
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
              >
                选择文件
              </Button>
              
              <Button
                variant="ghost"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <Settings size={16} className="mr-2" />
                高级设置
              </Button>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="video/*,image/*,audio/*"
              onChange={handleFileInputChange}
              className="hidden"
            />
          </div>
          
          {/* 高级设置 */}
          {showAdvanced && (
            <div className="p-4 bg-zinc-800/30 rounded-lg space-y-4">
              <h4 className="font-medium text-white">上传配置</h4>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">优先级</label>
                  <select
                    value={config.priority}
                    onChange={(e) => setConfig(prev => ({ ...prev, priority: e.target.value as any }))}
                    className="w-full px-3 py-2 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value="low">低</option>
                    <option value="normal">普通</option>
                    <option value="high">高</option>
                    <option value="urgent">紧急</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm text-zinc-400 mb-2">并发数</label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    value={config.maxConcurrentUploads}
                    onChange={(e) => setConfig(prev => ({ 
                      ...prev, 
                      maxConcurrentUploads: parseInt(e.target.value) || 3 
                    }))}
                  />
                </div>
                
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm text-zinc-400">
                    <input
                      type="checkbox"
                      checked={config.enableTranscription}
                      onChange={(e) => setConfig(prev => ({ 
                        ...prev, 
                        enableTranscription: e.target.checked 
                      }))}
                      className="rounded"
                    />
                    音频转录
                  </label>
                </div>
                
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-sm text-zinc-400">
                    <input
                      type="checkbox"
                      checked={config.enableVisualAnalysis}
                      onChange={(e) => setConfig(prev => ({ 
                        ...prev, 
                        enableVisualAnalysis: e.target.checked 
                      }))}
                      className="rounded"
                    />
                    视觉分析
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* 任务列表 */}
      {tasks.length > 0 && (
        <Card title={`上传队列 (${stats.total})`} variant="elevated">
          <div className="space-y-4">
            {/* 统计信息 */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                <div className="text-lg font-bold text-white">{stats.total}</div>
                <div className="text-xs text-zinc-400">总文件</div>
              </div>
              <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                <div className="text-lg font-bold text-blue-400">{stats.processing}</div>
                <div className="text-xs text-zinc-400">处理中</div>
              </div>
              <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                <div className="text-lg font-bold text-green-400">{stats.completed}</div>
                <div className="text-xs text-zinc-400">已完成</div>
              </div>
              <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                <div className="text-lg font-bold text-red-400">{stats.failed}</div>
                <div className="text-xs text-zinc-400">失败</div>
              </div>
              <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
                <div className="text-lg font-bold text-amber-400">{formatFileSize(stats.totalSize)}</div>
                <div className="text-xs text-zinc-400">总大小</div>
              </div>
            </div>
            
            {/* 控制按钮 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  onClick={startBatchUpload}
                  disabled={isUploading || stats.total === 0}
                  loading={isUploading}
                >
                  <Zap size={16} className="mr-2" />
                  开始处理
                </Button>
                
                <Button
                  variant="ghost"
                  onClick={toggleUpload}
                  disabled={!isUploading}
                >
                  {isUploading ? <Pause size={16} className="mr-2" /> : <Play size={16} className="mr-2" />}
                  {isUploading ? '暂停' : '继续'}
                </Button>
              </div>
              
              <Button
                variant="ghost"
                onClick={clearAllTasks}
                disabled={isUploading}
              >
                清空队列
              </Button>
            </div>
            
            {/* 任务列表 */}
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center gap-3 p-3 bg-zinc-800/30 rounded-lg"
                >
                  {/* 状态图标 */}
                  <div className="flex-shrink-0">
                    {getStatusIcon(task.status)}
                  </div>
                  
                  {/* 文件信息 */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-white truncate">
                        {task.filename}
                      </h4>
                      <span className={`text-xs ${getStatusColor(task.status)}`}>
                        {task.status === 'pending' && '等待中'}
                        {task.status === 'uploading' && '上传中'}
                        {task.status === 'processing' && '处理中'}
                        {task.status === 'completed' && '已完成'}
                        {task.status === 'failed' && '失败'}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-zinc-400">
                      <span>{formatFileSize(task.size)}</span>
                      {task.startTime && task.endTime && (
                        <span>用时: {formatTime(task.endTime - task.startTime)}</span>
                      )}
                      {task.estimatedTime && task.status === 'processing' && (
                        <span>预计: {formatTime(task.estimatedTime * 1000)}</span>
                      )}
                    </div>
                    
                    {/* 进度条 */}
                    {(task.status === 'uploading' || task.status === 'processing') && (
                      <div className="mt-2">
                        <div className="w-full bg-zinc-700 rounded-full h-1.5">
                          <div
                            className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${task.progress}%` }}
                          />
                        </div>
                        <div className="text-xs text-zinc-400 mt-1">
                          {task.progress.toFixed(0)}%
                        </div>
                      </div>
                    )}
                    
                    {/* 错误信息 */}
                    {task.error && (
                      <div className="mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-400">
                        {task.error}
                      </div>
                    )}
                  </div>
                  
                  {/* 操作按钮 */}
                  <div className="flex-shrink-0">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeTask(task.id)}
                      disabled={task.status === 'uploading' || task.status === 'processing'}
                    >
                      <X size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default BatchUploadPanel;