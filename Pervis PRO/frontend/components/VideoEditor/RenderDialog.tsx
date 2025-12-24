import React, { useState, useEffect } from 'react';
import { X, Play, Download, AlertCircle, CheckCircle, Clock, Settings } from 'lucide-react';

interface RenderOptions {
  format: string;
  resolution: string;
  framerate: number;
  quality: string;
  bitrate?: number;
  audio_bitrate: number;
  use_proxy: boolean;
}

interface RenderStatus {
  id: string;
  timeline_id: string;
  status: string;
  progress: number;
  error_message?: string;
  output_path?: string;
  file_size?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

interface RenderDialogProps {
  timelineId: string;
  timelineName: string;
  isOpen: boolean;
  onClose: () => void;
  onRenderComplete?: (result: any) => void;
}

const RenderDialog: React.FC<RenderDialogProps> = ({
  timelineId,
  timelineName,
  isOpen,
  onClose,
  onRenderComplete
}) => {
  const [options, setOptions] = useState<RenderOptions>({
    format: 'mp4',
    resolution: '1080p',
    framerate: 30,
    quality: 'high',
    audio_bitrate: 192,
    use_proxy: false
  });
  
  const [isRendering, setIsRendering] = useState<boolean>(false);
  const [renderStatus, setRenderStatus] = useState<RenderStatus | null>(null);
  const [renderRequirements, setRenderRequirements] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState<boolean>(false);
  
  // 预设配置
  const qualityPresets = {
    'low': { name: '低质量 (快速)', bitrate: 1000 },
    'medium': { name: '中等质量', bitrate: 3000 },
    'high': { name: '高质量', bitrate: 8000 },
    'ultra': { name: '超高质量 (慢)', bitrate: 15000 }
  };
  
  const resolutionOptions = [
    { value: '720p', name: '720p (1280x720)' },
    { value: '1080p', name: '1080p (1920x1080)' },
    { value: '4k', name: '4K (3840x2160)' }
  ];
  
  const framerateOptions = [24, 30, 60];
  
  // 检查渲染前置条件
  useEffect(() => {
    if (isOpen && timelineId) {
      checkRenderRequirements();
    }
  }, [isOpen, timelineId]);
  
  const checkRenderRequirements = async () => {
    try {
      const response = await fetch(`/api/render/${timelineId}/check`);
      if (response.ok) {
        const data = await response.json();
        setRenderRequirements(data);
      }
    } catch (error) {
      console.error('Failed to check render requirements:', error);
    }
  };
  
  // 启动渲染
  const handleStartRender = async () => {
    try {
      setIsRendering(true);
      
      const response = await fetch('/api/render/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          timeline_id: timelineId,
          ...options
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        pollRenderStatus(data.task_id);
      } else {
        const error = await response.json();
        throw new Error(error.detail?.message || 'Render failed to start');
      }
    } catch (error) {
      console.error('Failed to start render:', error);
      setIsRendering(false);
    }
  };
  
  // 轮询渲染状态
  const pollRenderStatus = async (taskId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/render/${taskId}/status`);
        if (response.ok) {
          const status = await response.json();
          setRenderStatus(status);
          
          if (status.status === 'completed') {
            setIsRendering(false);
            onRenderComplete?.(status);
          } else if (status.status === 'failed') {
            setIsRendering(false);
          } else if (status.status === 'processing') {
            setTimeout(poll, 1000); // 每秒轮询一次
          }
        }
      } catch (error) {
        console.error('Failed to poll render status:', error);
        setIsRendering(false);
      }
    };
    
    poll();
  };
  
  // 取消渲染
  const handleCancelRender = async () => {
    if (renderStatus?.id) {
      try {
        await fetch(`/api/render/${renderStatus.id}/cancel`, {
          method: 'POST'
        });
        setIsRendering(false);
        setRenderStatus(null);
      } catch (error) {
        console.error('Failed to cancel render:', error);
      }
    }
  };
  
  // 下载渲染结果
  const handleDownload = () => {
    if (renderStatus?.id) {
      window.open(`/api/render/${renderStatus.id}/download`, '_blank');
    }
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
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}分${secs}秒`;
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-zinc-900 rounded-lg w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* 标题栏 */}
        <div className="flex items-center justify-between p-6 border-b border-zinc-700">
          <div>
            <h2 className="text-xl font-semibold text-white">渲染视频</h2>
            <p className="text-sm text-zinc-400 mt-1">{timelineName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>
        
        {/* 内容区域 */}
        <div className="p-6">
          {/* 渲染前置检查 */}
          {renderRequirements && (
            <div className="mb-6">
              {renderRequirements.can_render ? (
                <div className="flex items-center gap-2 text-green-400 bg-green-400/10 p-3 rounded-lg">
                  <CheckCircle size={16} />
                  <span className="text-sm">时间轴验证通过，可以开始渲染</span>
                </div>
              ) : (
                <div className="bg-red-400/10 border border-red-400/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-red-400 mb-2">
                    <AlertCircle size={16} />
                    <span className="font-medium">无法渲染</span>
                  </div>
                  <ul className="text-sm text-red-300 space-y-1">
                    {renderRequirements.errors?.map((error: string, index: number) => (
                      <li key={index}>• {error}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {renderRequirements.estimated_duration && (
                <div className="mt-3 text-sm text-zinc-400">
                  <div className="flex items-center gap-4">
                    <span>预计渲染时间: {formatDuration(renderRequirements.estimated_duration)}</span>
                    <span>预计文件大小: {formatFileSize(renderRequirements.estimated_size_mb * 1024 * 1024)}</span>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* 渲染进度 */}
          {isRendering && renderStatus && (
            <div className="mb-6 bg-zinc-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="animate-spin w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full" />
                  <span className="text-white font-medium">
                    {renderStatus.status === 'processing' ? '正在渲染...' : '准备中...'}
                  </span>
                </div>
                <button
                  onClick={handleCancelRender}
                  className="text-red-400 hover:text-red-300 text-sm transition-colors"
                >
                  取消
                </button>
              </div>
              
              <div className="w-full bg-zinc-700 rounded-full h-2 mb-2">
                <div 
                  className="bg-amber-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${renderStatus.progress}%` }}
                />
              </div>
              
              <div className="text-sm text-zinc-400">
                进度: {renderStatus.progress.toFixed(1)}%
              </div>
            </div>
          )}
          
          {/* 渲染完成 */}
          {renderStatus?.status === 'completed' && (
            <div className="mb-6 bg-green-400/10 border border-green-400/20 rounded-lg p-4">
              <div className="flex items-center gap-2 text-green-400 mb-3">
                <CheckCircle size={16} />
                <span className="font-medium">渲染完成</span>
              </div>
              
              <div className="text-sm text-zinc-300 space-y-1 mb-4">
                <div>文件大小: {renderStatus.file_size ? formatFileSize(renderStatus.file_size) : '未知'}</div>
                <div>完成时间: {renderStatus.completed_at ? new Date(renderStatus.completed_at).toLocaleString() : '未知'}</div>
              </div>
              
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                <Download size={16} />
                下载视频
              </button>
            </div>
          )}
          
          {/* 渲染失败 */}
          {renderStatus?.status === 'failed' && (
            <div className="mb-6 bg-red-400/10 border border-red-400/20 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-400 mb-2">
                <AlertCircle size={16} />
                <span className="font-medium">渲染失败</span>
              </div>
              <div className="text-sm text-red-300">
                {renderStatus.error_message || '未知错误'}
              </div>
            </div>
          )}
          
          {/* 渲染设置 */}
          {!isRendering && (
            <div className="space-y-6">
              {/* 基础设置 */}
              <div>
                <h3 className="text-lg font-medium text-white mb-4">输出设置</h3>
                
                <div className="grid grid-cols-2 gap-4">
                  {/* 格式 */}
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">
                      输出格式
                    </label>
                    <select
                      value={options.format}
                      onChange={(e) => setOptions(prev => ({ ...prev, format: e.target.value }))}
                      className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                    >
                      <option value="mp4">MP4</option>
                      <option value="mov">MOV</option>
                    </select>
                  </div>
                  
                  {/* 分辨率 */}
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">
                      分辨率
                    </label>
                    <select
                      value={options.resolution}
                      onChange={(e) => setOptions(prev => ({ ...prev, resolution: e.target.value }))}
                      className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                    >
                      {resolutionOptions.map(res => (
                        <option key={res.value} value={res.value}>
                          {res.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* 帧率 */}
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">
                      帧率 (fps)
                    </label>
                    <select
                      value={options.framerate}
                      onChange={(e) => setOptions(prev => ({ ...prev, framerate: parseInt(e.target.value) }))}
                      className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                    >
                      {framerateOptions.map(fps => (
                        <option key={fps} value={fps}>
                          {fps} fps
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  {/* 质量 */}
                  <div>
                    <label className="block text-sm font-medium text-zinc-300 mb-2">
                      质量预设
                    </label>
                    <select
                      value={options.quality}
                      onChange={(e) => setOptions(prev => ({ ...prev, quality: e.target.value }))}
                      className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                    >
                      {Object.entries(qualityPresets).map(([key, preset]) => (
                        <option key={key} value={key}>
                          {preset.name}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
              
              {/* 高级设置 */}
              <div>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-amber-400 hover:text-amber-300 transition-colors"
                >
                  <Settings size={16} />
                  高级设置
                </button>
                
                {showAdvanced && (
                  <div className="mt-4 space-y-4 bg-zinc-800/50 rounded-lg p-4">
                    {/* 使用代理文件 */}
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium text-zinc-300">
                          使用代理文件编辑
                        </label>
                        <p className="text-xs text-zinc-500 mt-1">
                          使用低分辨率代理文件进行编辑，渲染时使用原始文件
                        </p>
                      </div>
                      <input
                        type="checkbox"
                        checked={options.use_proxy}
                        onChange={(e) => setOptions(prev => ({ ...prev, use_proxy: e.target.checked }))}
                        className="w-4 h-4 text-amber-500 bg-zinc-700 border-zinc-600 rounded focus:ring-amber-500"
                      />
                    </div>
                    
                    {/* 自定义比特率 */}
                    <div>
                      <label className="block text-sm font-medium text-zinc-300 mb-2">
                        视频比特率 (kbps)
                      </label>
                      <input
                        type="number"
                        value={options.bitrate || qualityPresets[options.quality as keyof typeof qualityPresets].bitrate}
                        onChange={(e) => setOptions(prev => ({ ...prev, bitrate: parseInt(e.target.value) }))}
                        className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                        min="500"
                        max="50000"
                      />
                    </div>
                    
                    {/* 音频比特率 */}
                    <div>
                      <label className="block text-sm font-medium text-zinc-300 mb-2">
                        音频比特率 (kbps)
                      </label>
                      <select
                        value={options.audio_bitrate}
                        onChange={(e) => setOptions(prev => ({ ...prev, audio_bitrate: parseInt(e.target.value) }))}
                        className="w-full bg-zinc-800 border border-zinc-600 rounded-lg px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                      >
                        <option value="128">128 kbps</option>
                        <option value="192">192 kbps</option>
                        <option value="256">256 kbps</option>
                        <option value="320">320 kbps</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* 底部按钮 */}
        {!isRendering && renderStatus?.status !== 'completed' && (
          <div className="flex items-center justify-end gap-3 p-6 border-t border-zinc-700">
            <button
              onClick={onClose}
              className="px-4 py-2 text-zinc-400 hover:text-white transition-colors"
            >
              取消
            </button>
            
            <button
              onClick={handleStartRender}
              disabled={!renderRequirements?.can_render}
              className="flex items-center gap-2 bg-amber-500 hover:bg-amber-600 disabled:bg-zinc-600 disabled:cursor-not-allowed text-white px-6 py-2 rounded-lg transition-colors"
            >
              <Play size={16} />
              开始渲染
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RenderDialog;