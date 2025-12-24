import React, { useState, useRef } from 'react';
import { 
  Play, 
  Pause, 
  SkipBack, 
  SkipForward,
  Download,
  Upload,
  Search,
  Film,
  Scissors,
  Eye,
  Share2,
  CheckCircle,
  ArrowRight,
  Zap
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { AssetPickerModal } from '../components/AssetPicker/AssetPickerModal';
import { TimelineEditor } from '../components/VideoEditor/TimelineEditor';
import { VideoPlayer } from '../components/VideoEditor/VideoPlayer';
import PreviewPlayer from '../components/VideoEditor/PreviewPlayer';
import RenderProgress from '../components/VideoEditor/RenderProgress';

/**
 * MVP完整工作流演示页面
 * 实现从剧本到成片的完整闭环
 */

interface Beat {
  id: string;
  content: string;
  order_index: number;
  emotion_tags: string[];
  scene_tags: string[];
  duration?: number;
}

interface Asset {
  id: string;
  filename: string;
  mime_type: string;
  thumbnail_path?: string;
  duration?: number;
}

interface SearchResult {
  id: string;
  filename: string;
  mime_type: string;
  thumbnail_path?: string;
  duration?: number;
  score?: number;
}

interface TimelineClip {
  id: string;
  asset: Asset;
  beat: Beat;
  start_time: number;
  end_time: number;
  trim_start: number;
  trim_end: number;
}

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'active' | 'completed';
  icon: React.ComponentType<any>;
}

const MVPWorkflowDemo: React.FC = () => {
  // 工作流状态
  const [currentStep, setCurrentStep] = useState(0);
  const [projectId, setProjectId] = useState<string>('');
  
  // 剧本和Beat数据
  const [script, setScript] = useState('');
  const [beats, setBeats] = useState<Beat[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // 素材搜索
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showAssetPicker, setShowAssetPicker] = useState(false);
  const [selectedBeat, setSelectedBeat] = useState<Beat | null>(null);
  
  // 时间轴编辑
  const [timelineClips, setTimelineClips] = useState<TimelineClip[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // 导出状态
  const [isExporting, setIsExporting] = useState(false);
  const [exportTaskId, setExportTaskId] = useState<string>('');
  const [exportResult, setExportResult] = useState<string>('');
  
  // 引用
  const videoRef = useRef<HTMLVideoElement>(null);
  const timelineRef = useRef<HTMLDivElement>(null);

  // 工作流步骤定义
  const workflowSteps: WorkflowStep[] = [
    {
      id: 'script',
      title: '剧本输入',
      description: '输入剧本内容，AI自动分析',
      status: currentStep === 0 ? 'active' : currentStep > 0 ? 'completed' : 'pending',
      icon: Upload
    },
    {
      id: 'beats',
      title: 'Beat分析',
      description: '提取故事节拍和情感标签',
      status: currentStep === 1 ? 'active' : currentStep > 1 ? 'completed' : 'pending',
      icon: Zap
    },
    {
      id: 'search',
      title: '素材搜索',
      description: '智能匹配合适的视频素材',
      status: currentStep === 2 ? 'active' : currentStep > 2 ? 'completed' : 'pending',
      icon: Search
    },
    {
      id: 'timeline',
      title: '时间轴编辑',
      description: '拖拽编辑，精确剪辑',
      status: currentStep === 3 ? 'active' : currentStep > 3 ? 'completed' : 'pending',
      icon: Scissors
    },
    {
      id: 'preview',
      title: '预览播放',
      description: '实时预览编辑效果',
      status: currentStep === 4 ? 'active' : currentStep > 4 ? 'completed' : 'pending',
      icon: Eye
    },
    {
      id: 'export',
      title: '导出分享',
      description: '渲染输出最终视频',
      status: currentStep === 5 ? 'active' : currentStep > 5 ? 'completed' : 'pending',
      icon: Share2
    }
  ];

  // 剧本分析
  const analyzeScript = async () => {
    if (!script.trim()) return;
    
    setIsAnalyzing(true);
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'MVP演示项目',
          script_raw: script,
          logline: '演示项目'
        })
      });
      
      if (response.ok) {
        const project = await response.json();
        setProjectId(project.id);
        
        // 获取生成的Beats
        const beatsResponse = await fetch(`/api/projects/${project.id}/beats`);
        if (beatsResponse.ok) {
          const beatsData = await beatsResponse.json();
          setBeats(beatsData.beats || []);
          setCurrentStep(1);
        }
      }
    } catch (error) {
      console.error('剧本分析失败:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 素材搜索
  const searchAssets = async (query: string) => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      const response = await fetch('/api/multimodal/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          search_modes: ['semantic', 'visual'],
          limit: 10
        })
      });
      
      if (response.ok) {
        const results = await response.json();
        setSearchResults(results.results || []);
      }
    } catch (error) {
      console.error('素材搜索失败:', error);
    } finally {
      setIsSearching(false);
    }
  };

  // 添加素材到时间轴
  const addAssetToTimeline = (asset: Asset | SearchResult, beat: Beat) => {
    // 转换SearchResult为Asset格式
    const assetData: Asset = {
      id: asset.id,
      filename: asset.filename,
      mime_type: asset.mime_type,
      thumbnail_path: asset.thumbnail_path,
      duration: asset.duration
    };
    
    const newClip: TimelineClip = {
      id: `clip-${Date.now()}`,
      asset: assetData,
      beat,
      start_time: totalDuration,
      end_time: totalDuration + (beat.duration || 5),
      trim_start: 0,
      trim_end: assetData.duration || 5
    };
    
    setTimelineClips(prev => [...prev, newClip]);
    setTotalDuration(prev => prev + (beat.duration || 5));
    
    if (currentStep < 3) setCurrentStep(3);
  };

  // 播放控制
  const togglePlayback = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
    
    if (currentStep < 4) setCurrentStep(4);
  };

  // 导出视频 - 使用AutoCut Orchestrator决策中枢
  const exportVideo = async () => {
    if (beats.length === 0) {
      alert('请先分析剧本生成Beat');
      return;
    }
    
    setIsExporting(true);
    
    try {
      console.log('🚀 开始MVP自动剪辑流程...');
      
      // 第一步：调用AutoCut Orchestrator生成智能时间轴
      const beatIds = beats.map(beat => beat.id);
      const autocutResponse = await fetch('/api/autocut/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          beat_ids: beatIds
        })
      });
      
      if (!autocutResponse.ok) {
        const error = await autocutResponse.json();
        throw new Error(error.detail || 'AutoCut智能分析失败');
      }
      
      const autocutResult = await autocutResponse.json();
      console.log('✅ AutoCut决策完成:', autocutResult);
      
      // 第二步：使用AutoCut决策创建时间轴
      const timelineResponse = await fetch('/api/timeline/create-from-autocut', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId,
          autocut_timeline: autocutResult.timeline,
          name: 'MVP智能剪辑时间轴'
        })
      });
      
      if (!timelineResponse.ok) {
        const error = await timelineResponse.json();
        throw new Error(error.detail || '创建智能时间轴失败');
      }
      
      const timelineResult = await timelineResponse.json();
      const timelineId = timelineResult.id;
      console.log('✅ 智能时间轴创建完成:', timelineId);
      
      // 第三步：开始FFmpeg渲染
      const renderResponse = await fetch('/api/render/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timeline_id: timelineId,
          format: 'mp4',
          resolution: '1080p',
          quality: 'high',
          framerate: 30
        })
      });
      
      if (renderResponse.ok) {
        const result = await renderResponse.json();
        setExportTaskId(result.task_id);
        setCurrentStep(5);
        console.log('🎬 FFmpeg渲染任务已创建:', result.task_id);
      } else {
        const error = await renderResponse.json();
        throw new Error(error.detail || '启动FFmpeg渲染失败');
      }
    } catch (error) {
      console.error('❌ MVP自动剪辑失败:', error);
      alert(`自动剪辑失败: ${error.message}`);
      setIsExporting(false);
    }
  };
  
  // 渲染完成回调
  const handleRenderComplete = (outputPath: string) => {
    setExportResult(outputPath);
    setIsExporting(false);
  };
  
  // 渲染错误回调
  const handleRenderError = (error: string) => {
    console.error('渲染失败:', error);
    setIsExporting(false);
  };

  // 时间轴拖拽处理
  const handleTimelineClick = (e: React.MouseEvent) => {
    if (timelineRef.current && totalDuration > 0) {
      const rect = timelineRef.current.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const newTime = (clickX / rect.width) * totalDuration;
      setCurrentTime(Math.max(0, Math.min(newTime, totalDuration)));
    }
  };

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      {/* 页面头部 */}
      <div className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">MVP完整工作流</h1>
              <p className="text-zinc-400 mt-1">
                从剧本到成片的完整制作流程演示
              </p>
            </div>
            
            <div className="flex items-center gap-2">
              <div className="text-sm text-zinc-400">
                步骤 {currentStep + 1} / {workflowSteps.length}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 工作流步骤指示器 */}
        <Card title="工作流程" variant="elevated" className="mb-8">
          <div className="flex items-center justify-between">
            {workflowSteps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={step.id} className="flex items-center">
                  <div className={`flex flex-col items-center ${
                    step.status === 'completed' ? 'text-green-400' :
                    step.status === 'active' ? 'text-amber-400' : 'text-zinc-500'
                  }`}>
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 ${
                      step.status === 'completed' ? 'bg-green-500/20 border-2 border-green-400' :
                      step.status === 'active' ? 'bg-amber-500/20 border-2 border-amber-400' :
                      'bg-zinc-800 border-2 border-zinc-600'
                    }`}>
                      {step.status === 'completed' ? (
                        <CheckCircle size={20} />
                      ) : (
                        <Icon size={20} />
                      )}
                    </div>
                    <div className="text-xs font-medium text-center">
                      {step.title}
                    </div>
                  </div>
                  
                  {index < workflowSteps.length - 1 && (
                    <ArrowRight size={16} className="mx-4 text-zinc-600" />
                  )}
                </div>
              );
            })}
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左侧：输入和控制 */}
          <div className="space-y-6">
            {/* 步骤1: 剧本输入 */}
            <Card title="1. 剧本输入" variant="elevated">
              <div className="space-y-4">
                <textarea
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  placeholder="请输入剧本内容..."
                  className="w-full h-32 px-3 py-2 bg-zinc-800 border border-zinc-600 rounded-lg text-white resize-none"
                />
                <Button
                  onClick={analyzeScript}
                  loading={isAnalyzing}
                  disabled={!script.trim()}
                  className="w-full"
                >
                  <Upload size={16} className="mr-2" />
                  {isAnalyzing ? '分析中...' : '分析剧本'}
                </Button>
              </div>
            </Card>

            {/* 步骤2: Beat展示 */}
            {beats.length > 0 && (
              <Card title="2. 故事节拍" variant="elevated">
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {beats.map((beat, index) => (
                    <div
                      key={beat.id}
                      className="p-3 bg-zinc-800/50 rounded-lg border border-zinc-700"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="text-sm font-medium text-white mb-1">
                            Beat {index + 1}
                          </div>
                          <div className="text-xs text-zinc-400 mb-2">
                            {beat.content}
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {beat.emotion_tags?.map(tag => (
                              <span key={tag} className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded">
                                {tag}
                              </span>
                            ))}
                            {beat.scene_tags?.map(tag => (
                              <span key={tag} className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setSelectedBeat(beat);
                            setSearchQuery(beat.content);
                            setShowAssetPicker(true);
                            if (currentStep < 2) setCurrentStep(2);
                          }}
                        >
                          <Search size={14} />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* 步骤3: 素材搜索 */}
            <Card title="3. 素材搜索" variant="elevated">
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="搜索素材..."
                    className="flex-1"
                  />
                  <Button
                    onClick={() => searchAssets(searchQuery)}
                    loading={isSearching}
                    disabled={!searchQuery.trim()}
                  >
                    <Search size={16} />
                  </Button>
                </div>
                
                {searchResults.length > 0 && (
                  <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                    {searchResults.map((asset) => (
                      <div
                        key={asset.id}
                        className="p-2 bg-zinc-800/50 rounded border border-zinc-700 cursor-pointer hover:border-amber-400"
                        onClick={() => selectedBeat && addAssetToTimeline(asset, selectedBeat)}
                      >
                        <div className="text-xs font-medium text-white truncate">
                          {asset.filename}
                        </div>
                        <div className="text-xs text-zinc-400">
                          {asset.mime_type}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* 右侧：时间轴和预览 */}
          <div className="space-y-6">
            {/* 步骤4: 时间轴编辑 */}
            <Card title="4. 时间轴编辑" variant="elevated">
              <TimelineEditor
                projectId={projectId}
                clips={timelineClips.map(clip => ({
                  id: clip.id,
                  timeline_id: 'mvp-timeline',
                  asset_id: clip.asset.id,
                  asset: clip.asset,
                  start_time: clip.start_time,
                  end_time: clip.end_time,
                  trim_start: clip.trim_start,
                  trim_end: clip.trim_end,
                  volume: 1.0,
                  is_muted: 0,
                  audio_fade_in: 0,
                  audio_fade_out: 0,
                  transition_type: null,
                  transition_duration: 0,
                  order_index: 0,
                  clip_metadata: {}
                }))}
                onTimeUpdate={(time) => setCurrentTime(time)}
                onPlayStateChange={(playing) => setIsPlaying(playing)}
              />
            </Card>

            {/* 步骤5: 预览播放 */}
            <Card title="5. 预览播放" variant="elevated">
              <PreviewPlayer
                timelineClips={timelineClips}
                currentTime={currentTime}
                isPlaying={isPlaying}
                totalDuration={totalDuration}
                onTimeUpdate={(time) => setCurrentTime(time)}
                onPlayStateChange={(playing) => setIsPlaying(playing)}
              />
            </Card>

            {/* 步骤6: 导出分享 */}
            {isExporting || exportTaskId ? (
              <RenderProgress
                taskId={exportTaskId}
                onComplete={handleRenderComplete}
                onError={handleRenderError}
              />
            ) : exportResult ? (
              <Card title="6. 导出完成" variant="elevated">
                <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <div className="flex items-center gap-3">
                    <CheckCircle size={20} className="text-green-400" />
                    <div>
                      <div className="text-sm font-medium text-green-400">视频导出成功</div>
                      <div className="text-xs text-zinc-400 mt-1">{exportResult}</div>
                    </div>
                  </div>
                </div>
              </Card>
            ) : (
              <Card title="6. 导出分享" variant="elevated">
                <div className="space-y-4">
                  <div className="text-sm text-zinc-400 mb-4">
                    将时间轴渲染为最终视频文件
                  </div>
                  <Button
                    onClick={exportVideo}
                    disabled={timelineClips.length === 0}
                    className="w-full"
                  >
                    <Download size={16} className="mr-2" />
                    开始渲染
                  </Button>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* 素材选择器模态窗口 */}
      {showAssetPicker && selectedBeat && (
        <AssetPickerModal
          isOpen={showAssetPicker}
          onClose={() => setShowAssetPicker(false)}
          onSelect={(asset) => {
            addAssetToTimeline(asset, selectedBeat);
            setShowAssetPicker(false);
          }}
          projectId={projectId}
          mode="single"
        />
      )}
    </div>
  );
};

export default MVPWorkflowDemo;