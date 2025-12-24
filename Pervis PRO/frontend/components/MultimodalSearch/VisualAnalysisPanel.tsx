import React, { useState, useEffect, useCallback } from 'react';
import { 
  Eye, 
  Play, 
  Pause, 
  RefreshCw, 
  Download, 
  Settings,
  Clock,
  Image as ImageIcon,
  Palette,
  Tag,
  BarChart3,
  Zap,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

// 视觉分析数据类型
export interface VisualAnalysisData {
  duration: number;
  keyframes_count: number;
  sample_interval: number;
  visual_description: {
    visual_summary: {
      dominant_colors: string[];
      scene_types: string[];
      objects: string[];
      composition: string[];
      lighting: string[];
      camera_work: string[];
    };
    overall_description: string;
  };
  keyframes: Array<{
    timestamp: number;
    frame_path: string;
    description: string;
    objects: string[];
    colors: string[];
    composition: string;
    lighting: string;
    visual_features: number[];
  }>;
  color_analysis: {
    dominant_palette: string[];
    color_distribution: Record<string, number>;
    mood_colors: string[];
  };
  scene_analysis: {
    scene_changes: number[];
    scene_types: Record<string, number>;
    average_scene_duration: number;
  };
}

// 视觉分析状态
export interface VisualAnalysisStatus {
  status: 'not_analyzed' | 'processing' | 'completed' | 'failed';
  has_visual_analysis: boolean;
  duration?: number;
  keyframes_count?: number;
  sample_interval?: number;
  visual_summary?: any;
  error_message?: string;
}

// 组件属性
export interface VisualAnalysisPanelProps {
  assetId: string;
  assetFilename?: string;
  onAnalysisComplete?: (data: VisualAnalysisData) => void;
  className?: string;
}

export const VisualAnalysisPanel: React.FC<VisualAnalysisPanelProps> = ({
  assetId,
  assetFilename,
  onAnalysisComplete,
  className = ''
}) => {
  // 状态管理
  const [status, setStatus] = useState<VisualAnalysisStatus | null>(null);
  const [analysisData, setAnalysisData] = useState<VisualAnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showKeyframes, setShowKeyframes] = useState(false);
  const [selectedKeyframe, setSelectedKeyframe] = useState<number | null>(null);
  
  // 分析配置
  const [analysisConfig, setAnalysisConfig] = useState({
    sample_interval: 2.0,
    force_reanalyze: false
  });

  // 加载分析状态
  useEffect(() => {
    loadAnalysisStatus();
  }, [assetId]);

  const loadAnalysisStatus = async () => {
    try {
      const response = await fetch(`/api/multimodal/visual/status/${assetId}`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
        
        // 如果已有分析数据，加载完整数据
        if (data.has_visual_analysis) {
          loadAnalysisData();
        }
      }
    } catch (error) {
      console.error('Failed to load analysis status:', error);
      setError('加载分析状态失败');
    }
  };

  const loadAnalysisData = async (includeKeyframes = false) => {
    try {
      const response = await fetch(
        `/api/multimodal/visual/data/${assetId}?include_keyframes=${includeKeyframes}`
      );
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setAnalysisData(data.visual_analysis);
          onAnalysisComplete?.(data.visual_analysis);
        }
      }
    } catch (error) {
      console.error('Failed to load analysis data:', error);
      setError('加载分析数据失败');
    }
  };

  // 开始视觉分析
  const startAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/multimodal/analyze/visual/${assetId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(analysisConfig)
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.status === 'success') {
        setAnalysisData(data.visual_analysis);
        setStatus({
          status: 'completed',
          has_visual_analysis: true,
          ...data.visual_analysis
        });
        onAnalysisComplete?.(data.visual_analysis);
      } else {
        throw new Error(data.message || '分析失败');
      }

    } catch (err) {
      console.error('Visual analysis failed:', err);
      setError(`视觉分析失败: ${err}`);
      setStatus(prev => prev ? { ...prev, status: 'failed', error_message: String(err) } : null);
    } finally {
      setLoading(false);
    }
  };

  // 格式化时长
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 格式化时间戳
  const formatTimestamp = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  // 渲染状态指示器
  const renderStatusIndicator = () => {
    if (!status) return null;

    const statusConfig = {
      not_analyzed: {
        icon: AlertCircle,
        color: 'text-zinc-400',
        bg: 'bg-zinc-700/30',
        text: '未分析'
      },
      processing: {
        icon: Loader2,
        color: 'text-blue-400',
        bg: 'bg-blue-500/10',
        text: '分析中...',
        animate: 'animate-spin'
      },
      completed: {
        icon: CheckCircle,
        color: 'text-green-400',
        bg: 'bg-green-500/10',
        text: '分析完成'
      },
      failed: {
        icon: AlertCircle,
        color: 'text-red-400',
        bg: 'bg-red-500/10',
        text: '分析失败'
      }
    };

    const config = statusConfig[status.status];
    const Icon = config.icon;

    return (
      <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${config.bg}`}>
        <Icon size={16} className={`${config.color} ${config.animate || ''}`} />
        <span className={`text-sm ${config.color}`}>{config.text}</span>
        {status.status === 'completed' && status.keyframes_count && (
          <span className="text-xs text-zinc-400">
            ({status.keyframes_count} 关键帧)
          </span>
        )}
      </div>
    );
  };

  // 渲染视觉摘要
  const renderVisualSummary = () => {
    if (!analysisData?.visual_description?.visual_summary) return null;

    const summary = analysisData.visual_description.visual_summary;

    return (
      <div className="space-y-4">
        <h4 className="font-medium text-white">视觉特征摘要</h4>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {/* 主要颜色 */}
          {summary.dominant_colors && summary.dominant_colors.length > 0 && (
            <div>
              <h5 className="text-sm text-zinc-400 mb-2 flex items-center gap-1">
                <Palette size={14} />
                主要颜色
              </h5>
              <div className="flex flex-wrap gap-1">
                {summary.dominant_colors.slice(0, 6).map((color, index) => (
                  <div
                    key={index}
                    className="w-6 h-6 rounded border border-zinc-600"
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
          )}
          
          {/* 场景类型 */}
          {summary.scene_types && summary.scene_types.length > 0 && (
            <div>
              <h5 className="text-sm text-zinc-400 mb-2 flex items-center gap-1">
                <Eye size={14} />
                场景类型
              </h5>
              <div className="flex flex-wrap gap-1">
                {summary.scene_types.slice(0, 4).map((scene, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-zinc-700/50 text-xs text-zinc-300 rounded"
                  >
                    {scene}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* 物体识别 */}
          {summary.objects && summary.objects.length > 0 && (
            <div>
              <h5 className="text-sm text-zinc-400 mb-2 flex items-center gap-1">
                <Tag size={14} />
                识别物体
              </h5>
              <div className="flex flex-wrap gap-1">
                {summary.objects.slice(0, 4).map((object, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-zinc-700/50 text-xs text-zinc-300 rounded"
                  >
                    {object}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* 构图特点 */}
          {summary.composition && summary.composition.length > 0 && (
            <div>
              <h5 className="text-sm text-zinc-400 mb-2">构图特点</h5>
              <div className="flex flex-wrap gap-1">
                {summary.composition.slice(0, 3).map((comp, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-amber-500/10 text-xs text-amber-400 rounded"
                  >
                    {comp}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* 光线特点 */}
          {summary.lighting && summary.lighting.length > 0 && (
            <div>
              <h5 className="text-sm text-zinc-400 mb-2">光线特点</h5>
              <div className="flex flex-wrap gap-1">
                {summary.lighting.slice(0, 3).map((light, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-500/10 text-xs text-blue-400 rounded"
                  >
                    {light}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* 摄影技法 */}
          {summary.camera_work && summary.camera_work.length > 0 && (
            <div>
              <h5 className="text-sm text-zinc-400 mb-2">摄影技法</h5>
              <div className="flex flex-wrap gap-1">
                {summary.camera_work.slice(0, 3).map((camera, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-green-500/10 text-xs text-green-400 rounded"
                  >
                    {camera}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {/* 整体描述 */}
        {analysisData.visual_description.overall_description && (
          <div className="p-3 bg-zinc-800/30 rounded-lg">
            <h5 className="text-sm text-zinc-400 mb-2">整体描述</h5>
            <p className="text-sm text-zinc-300">
              {analysisData.visual_description.overall_description}
            </p>
          </div>
        )}
      </div>
    );
  };

  // 渲染关键帧
  const renderKeyframes = () => {
    if (!analysisData?.keyframes || analysisData.keyframes.length === 0) return null;

    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-white">关键帧分析</h4>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowKeyframes(!showKeyframes)}
          >
            {showKeyframes ? '收起' : '展开'} ({analysisData.keyframes.length})
          </Button>
        </div>
        
        {showKeyframes && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {analysisData.keyframes.map((keyframe, index) => (
              <div
                key={index}
                className={`relative cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                  selectedKeyframe === index 
                    ? 'border-amber-500 shadow-lg shadow-amber-500/20' 
                    : 'border-zinc-700 hover:border-zinc-600'
                }`}
                onClick={() => setSelectedKeyframe(selectedKeyframe === index ? null : index)}
              >
                {/* 关键帧图片 */}
                <div className="aspect-video bg-zinc-800 flex items-center justify-center">
                  {keyframe.frame_path ? (
                    <img
                      src={keyframe.frame_path}
                      alt={`关键帧 ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <ImageIcon size={24} className="text-zinc-500" />
                  )}
                </div>
                
                {/* 时间戳 */}
                <div className="absolute top-1 left-1 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-xs text-white">
                  {formatTimestamp(keyframe.timestamp)}
                </div>
                
                {/* 选中指示器 */}
                {selectedKeyframe === index && (
                  <div className="absolute inset-0 bg-amber-500/20 flex items-center justify-center">
                    <div className="w-8 h-8 bg-amber-500 rounded-full flex items-center justify-center">
                      <Eye size={16} className="text-black" />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {/* 选中关键帧的详细信息 */}
        {selectedKeyframe !== null && analysisData.keyframes[selectedKeyframe] && (
          <Card variant="outlined" className="mt-4">
            <div className="space-y-3">
              <h5 className="font-medium text-white">
                关键帧 {selectedKeyframe + 1} - {formatTimestamp(analysisData.keyframes[selectedKeyframe].timestamp)}
              </h5>
              
              <p className="text-sm text-zinc-300">
                {analysisData.keyframes[selectedKeyframe].description}
              </p>
              
              <div className="grid grid-cols-2 gap-4">
                {/* 识别物体 */}
                {analysisData.keyframes[selectedKeyframe].objects.length > 0 && (
                  <div>
                    <h6 className="text-xs text-zinc-400 mb-1">识别物体</h6>
                    <div className="flex flex-wrap gap-1">
                      {analysisData.keyframes[selectedKeyframe].objects.map((obj, idx) => (
                        <span key={idx} className="px-2 py-1 bg-zinc-700/50 text-xs text-zinc-300 rounded">
                          {obj}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* 颜色分析 */}
                {analysisData.keyframes[selectedKeyframe].colors.length > 0 && (
                  <div>
                    <h6 className="text-xs text-zinc-400 mb-1">主要颜色</h6>
                    <div className="flex gap-1">
                      {analysisData.keyframes[selectedKeyframe].colors.slice(0, 6).map((color, idx) => (
                        <div
                          key={idx}
                          className="w-4 h-4 rounded border border-zinc-600"
                          style={{ backgroundColor: color }}
                          title={color}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              {/* 构图和光线 */}
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-zinc-400">构图: </span>
                  <span className="text-zinc-300">{analysisData.keyframes[selectedKeyframe].composition}</span>
                </div>
                <div>
                  <span className="text-zinc-400">光线: </span>
                  <span className="text-zinc-300">{analysisData.keyframes[selectedKeyframe].lighting}</span>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    );
  };

  // 渲染统计信息
  const renderStatistics = () => {
    if (!analysisData) return null;

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <Clock size={20} className="mx-auto mb-1 text-blue-400" />
          <div className="text-sm font-medium text-white">
            {formatDuration(analysisData.duration)}
          </div>
          <div className="text-xs text-zinc-400">总时长</div>
        </div>
        
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <ImageIcon size={20} className="mx-auto mb-1 text-green-400" />
          <div className="text-sm font-medium text-white">
            {analysisData.keyframes_count}
          </div>
          <div className="text-xs text-zinc-400">关键帧</div>
        </div>
        
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <BarChart3 size={20} className="mx-auto mb-1 text-amber-400" />
          <div className="text-sm font-medium text-white">
            {analysisData.sample_interval}s
          </div>
          <div className="text-xs text-zinc-400">采样间隔</div>
        </div>
        
        <div className="text-center p-3 bg-zinc-800/30 rounded-lg">
          <Palette size={20} className="mx-auto mb-1 text-purple-400" />
          <div className="text-sm font-medium text-white">
            {analysisData.color_analysis?.dominant_palette?.length || 0}
          </div>
          <div className="text-xs text-zinc-400">主要颜色</div>
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 头部控制区域 */}
      <Card title={`视觉分析 - ${assetFilename || assetId}`} variant="elevated">
        <div className="space-y-4">
          {/* 状态和控制 */}
          <div className="flex items-center justify-between">
            {renderStatusIndicator()}
            
            <div className="flex items-center gap-2">
              {status?.status === 'not_analyzed' && (
                <Button
                  onClick={startAnalysis}
                  loading={loading}
                  icon={Zap}
                >
                  开始分析
                </Button>
              )}
              
              {status?.status === 'completed' && (
                <Button
                  variant="ghost"
                  onClick={() => setAnalysisConfig(prev => ({ ...prev, force_reanalyze: true }))}
                  icon={RefreshCw}
                >
                  重新分析
                </Button>
              )}
              
              <Button
                variant="ghost"
                onClick={loadAnalysisStatus}
                icon={RefreshCw}
              >
                刷新
              </Button>
            </div>
          </div>
          
          {/* 分析配置 */}
          {status?.status === 'not_analyzed' && (
            <div className="p-3 bg-zinc-800/30 rounded-lg">
              <h4 className="text-sm font-medium text-white mb-3">分析配置</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-zinc-400 mb-1">采样间隔 (秒)</label>
                  <select
                    value={analysisConfig.sample_interval}
                    onChange={(e) => setAnalysisConfig(prev => ({
                      ...prev,
                      sample_interval: parseFloat(e.target.value)
                    }))}
                    className="w-full px-2 py-1 bg-zinc-700 border border-zinc-600 rounded text-sm text-white"
                  >
                    <option value={1.0}>1.0s (高精度)</option>
                    <option value={2.0}>2.0s (标准)</option>
                    <option value={5.0}>5.0s (快速)</option>
                    <option value={10.0}>10.0s (粗略)</option>
                  </select>
                </div>
                
                <div className="flex items-end">
                  <label className="flex items-center gap-2 text-xs text-zinc-400">
                    <input
                      type="checkbox"
                      checked={analysisConfig.force_reanalyze}
                      onChange={(e) => setAnalysisConfig(prev => ({
                        ...prev,
                        force_reanalyze: e.target.checked
                      }))}
                      className="rounded"
                    />
                    强制重新分析
                  </label>
                </div>
              </div>
            </div>
          )}
          
          {/* 错误信息 */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>
      </Card>
      
      {/* 统计信息 */}
      {analysisData && (
        <Card title="分析统计" variant="elevated">
          {renderStatistics()}
        </Card>
      )}
      
      {/* 视觉摘要 */}
      {analysisData && (
        <Card title="视觉特征" variant="elevated">
          {renderVisualSummary()}
        </Card>
      )}
      
      {/* 关键帧分析 */}
      {analysisData && (
        <Card title="关键帧" variant="elevated">
          {renderKeyframes()}
        </Card>
      )}
    </div>
  );
};

export default VisualAnalysisPanel;