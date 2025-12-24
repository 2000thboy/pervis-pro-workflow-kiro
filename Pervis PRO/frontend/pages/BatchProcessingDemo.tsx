import React, { useState } from 'react';
import { BatchUploadPanel, BatchQueueMonitor } from '../components/BatchProcessing';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  Upload, 
  Activity, 
  BarChart3, 
  Settings,
  RefreshCw,
  Zap
} from 'lucide-react';

/**
 * 批量处理功能演示页面
 * 
 * 展示批量上传和队列监控功能
 */
const BatchProcessingDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'monitor'>('upload');
  const [refreshKey, setRefreshKey] = useState(0);

  // 模拟项目ID
  const projectId = 'demo-project-001';

  // 处理上传完成
  const handleUploadComplete = (results: any[]) => {
    console.log('批量上传完成:', results);
    // 切换到监控页面查看结果
    setActiveTab('monitor');
    // 刷新监控数据
    setRefreshKey(prev => prev + 1);
  };

  // 处理任务更新
  const handleTaskUpdate = (task: any) => {
    console.log('任务状态更新:', task);
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      {/* 页面头部 */}
      <div className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">批量处理管理</h1>
              <p className="text-zinc-400 mt-1">
                批量上传素材文件，监控处理队列状态
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                onClick={() => setRefreshKey(prev => prev + 1)}
                icon={RefreshCw}
              >
                刷新数据
              </Button>
              
              <div className="flex items-center gap-1 bg-zinc-800 rounded-lg p-1">
                <Button
                  size="sm"
                  variant={activeTab === 'upload' ? 'primary' : 'ghost'}
                  onClick={() => setActiveTab('upload')}
                  icon={Upload}
                >
                  批量上传
                </Button>
                <Button
                  size="sm"
                  variant={activeTab === 'monitor' ? 'primary' : 'ghost'}
                  onClick={() => setActiveTab('monitor')}
                  icon={Activity}
                >
                  队列监控
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 功能介绍 */}
        <Card title="功能说明" variant="elevated" className="mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Upload size={24} className="text-amber-400" />
                <h3 className="text-lg font-medium text-white">批量上传</h3>
              </div>
              <ul className="text-sm text-zinc-400 space-y-1 ml-9">
                <li>• 支持拖拽上传多个文件</li>
                <li>• 自动队列管理和进度跟踪</li>
                <li>• 可配置处理优先级和参数</li>
                <li>• 支持音频转录和视觉分析</li>
                <li>• 实时显示上传和处理状态</li>
              </ul>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Activity size={24} className="text-blue-400" />
                <h3 className="text-lg font-medium text-white">队列监控</h3>
              </div>
              <ul className="text-sm text-zinc-400 space-y-1 ml-9">
                <li>• 实时监控处理队列状态</li>
                <li>• 显示系统资源使用情况</li>
                <li>• 查看任务历史和统计信息</li>
                <li>• 支持任务管理和清理操作</li>
                <li>• 自动刷新和错误处理</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* 标签页内容 */}
        {activeTab === 'upload' && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <Zap size={24} className="text-amber-400" />
              <h2 className="text-xl font-semibold text-white">批量上传管理</h2>
            </div>
            
            <BatchUploadPanel
              projectId={projectId}
              onUploadComplete={handleUploadComplete}
              onTaskUpdate={handleTaskUpdate}
            />
          </div>
        )}

        {activeTab === 'monitor' && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-6">
              <BarChart3 size={24} className="text-blue-400" />
              <h2 className="text-xl font-semibold text-white">队列监控面板</h2>
            </div>
            
            <BatchQueueMonitor
              key={refreshKey}
              refreshInterval={5000}
            />
          </div>
        )}

        {/* 使用提示 */}
        <Card title="使用提示" variant="elevated" className="mt-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <h4 className="font-medium text-white flex items-center gap-2">
                <Upload size={16} className="text-amber-400" />
                上传建议
              </h4>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• 单次最多上传50个文件</li>
                <li>• 支持视频、图片、音频格式</li>
                <li>• 建议文件大小不超过2GB</li>
                <li>• 可设置处理优先级</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium text-white flex items-center gap-2">
                <Activity size={16} className="text-blue-400" />
                监控说明
              </h4>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• 队列状态每5秒自动刷新</li>
                <li>• 可手动暂停/恢复自动刷新</li>
                <li>• 支持清理24小时前的旧任务</li>
                <li>• 显示系统资源使用情况</li>
              </ul>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-medium text-white flex items-center gap-2">
                <Settings size={16} className="text-green-400" />
                高级配置
              </h4>
              <ul className="text-sm text-zinc-400 space-y-1">
                <li>• 可调整并发处理数量</li>
                <li>• 支持启用/禁用音频转录</li>
                <li>• 支持启用/禁用视觉分析</li>
                <li>• 可设置任务优先级</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* API状态指示 */}
        <div className="mt-8 p-4 bg-zinc-800/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm text-zinc-400">
                后端API状态: 已连接 (批量处理服务运行中)
              </span>
            </div>
            
            <div className="text-xs text-zinc-500">
              项目ID: {projectId}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchProcessingDemo;