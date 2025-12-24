import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Eye, 
  Mic, 
  BarChart3,
  Settings,
  RefreshCw,
  Download,
  Share2,
  Layers,
  Zap,
  Info,
  TrendingUp
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import MultimodalSearchPanel, { MultimodalSearchResult } from './MultimodalSearchPanel';
import VisualAnalysisPanel, { VisualAnalysisData } from './VisualAnalysisPanel';
import AudioTranscriptionPanel, { TranscriptionData, TranscriptionSegment } from './AudioTranscriptionPanel';

// 分析模式
type AnalysisMode = 'search' | 'visual' | 'audio' | 'dashboard';

// 综合分析数据
export interface MultimodalAnalysisData {
  asset_id: string;
  filename: string;
  visual_analysis?: VisualAnalysisData;
  transcription?: TranscriptionData;
  search_results?: MultimodalSearchResult[];
  analysis_summary?: {
    dominant_themes: string[];
    key_moments: Array<{
      timestamp: number;
      description: string;
      confidence: number;
      modalities: string[];
    }>;
    content_tags: Record<string, string[]>;
    quality_scores: {
      visual_quality: number;
      audio_quality: number;
      content_richness: number;
    };
  };
}

// 组件属性
export interface MultimodalAnalysisDashboardProps {
  assetId: string;
  assetFilename?: string;
  projectId?: string;
  onAnalysisComplete?: (data: MultimodalAnalysisData) => void;
  className?: string;
}

export const MultimodalAnalysisDashboard: React.FC<MultimodalAnalysisDashboardProps> = ({
  assetId,
  assetFilename,
  projectId,
  onAnalysisComplete,
  className = ''
}) => {
  // 状态管理
  const [activeMode, setActiveMode] = useState<AnalysisMode>('dashboard');
  const [analysisData, setAnalysisData] = useState<MultimodalAnalysisData>({
    asset_id: assetId,
    filename: assetFilename || assetId
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 处理视觉分析完成
  const handleVisualAnalysisComplete = useCallback((data: VisualAnalysisData) => {
    setAnalysisData(prev => ({
      ...prev,
      visual_analysis: data
    }));
  }, []);

  // 处理音频转录完成
  const handleTranscriptionComplete = useCallback((data: TranscriptionData) => {
    setAnalysisData(prev => ({
      ...prev,
      transcription: data
    }));
  }, []);

  // 处理搜索结果更新
  const handleSearchResultsChange = useCallback((results: MultimodalSearchResult[]) => {
    setAnalysisData(prev => ({
      ...prev,
      search_results: results
    }));
  }, []);

  // 处理片段选择
  const handleSegmentSelect = useCallback((segment: TranscriptionSegment) => {
    console.log('Selected transcription segment:', segment);
    // TODO: 可以在这里实现跳转到对应时间点的功能
  }, []);

  // 生成分析摘要
  const generateAnalysisSummary = useCallback(async () => {
    if (!analysisData.visual_analysis && !analysisData.transcription) return;

    setLoading(true);
    try {
      const response = await fetch('/api/multimodal/analyze/summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          asset_id: assetId,
          visual_analysis: analysisData.visual_analysis,
          transcription: analysisData.transcription
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          const updatedData = {
            ...analysisData,
            analysis_summary: data.summary
          };
          setAnalysisData(updatedData);
          onAnalysisComplete?.(updatedData);
        }
      }
    } catch (error) {
      console.error('Failed to generate analysis summary:', error);
      setError('生成分析摘要失败');
    } finally {
      setLoading(false);
    }
  }, [assetId, analysisData, onAnalysisComplete]);

  // 导出分析报告
  const exportAnalysisReport = useCallback(async () => {
    try {
      const response = await fetch('/api/multimodal/export/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          asset_id: assetId,
          analysis_data: analysisData,
          format: 'json'
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `multimodal_analysis_${assetId}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to export report:', error);
      setError('导出报告失败');
    }
  }, [assetId, analysisData]);

  // 渲染模式切换器
  const renderModeSelector = () => (
    <div className="flex items-center gap-2 p-1 bg-zinc-800/50 rounded-lg">
      {[
        { key: 'dashboard', label: '仪表板', icon: BarChart3 },
        { key: 'search', label: '多模态搜索', icon: Search },
        { key: 'visual', label: '视觉分析', icon: Eye },
        { key: 'audio', label: '音频转录', icon: Mic }
      ].map(mode => (
        <Button
          key={mode.key}
          size="sm"
          variant={activeMode === mode.key ? 'primary' : 'ghost'}
          onClick={() => setActiveMode(mode.key as AnalysisMode)}
          icon={mode.icon}
        >
          {mode.label}
        </Button>
      ))}
    </div>
  );

  // 渲染分析概览
  const renderAnalysisOverview = () => {
    const hasVisual = !!analysisData.visual_analysis;
    const hasAudio = !!analysisData.transcription;
    const hasSearch = !!analysisData.search_results?.length;

    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 视觉分析状态 */}
        <Card
          title="视觉分析"
          variant="elevated"
          className={`cursor-pointer transition-all ${hasVisual ? 'border-green-500/30' : 'border-zinc-700'}`}
          onClick={() => setActiveMode('visual')}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Eye size={24} className={hasVisual ? 'text-green-400' : 'text-zinc-500'} />
              <span className={`text-sm ${hasVisual ? 'text-green-400' : 'text-zinc-500'}`}>
                {hasVisual ? '已完成' : '未分析'}
              </span>
            </div>
            
            {hasVisual && analysisData.visual_analysis && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-400">关键帧:</span>
                  <span className="text-white">{analysisData.visual_analysis.keyframes_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">时长:</span>
                  <span className="text-white">
                    {Math.floor(analysisData.visual_analysis.duration / 60)}:
                    {Math.floor(analysisData.visual_analysis.duration % 60).toString().padStart(2, '0')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">主要颜色:</span>
                  <span className="text-white">
                    {analysisData.visual_analysis.color_analysis?.dominant_palette?.length || 0}
                  </span>
                </div>
              </div>
            )}
            
            {!hasVisual && (
              <p className="text-xs text-zinc-500">点击开始视觉特征分析</p>
            )}
          </div>
        </Card>

        {/* 音频转录状态 */}
        <Card
          title="音频转录"
          variant="elevated"
          className={`cursor-pointer transition-all ${hasAudio ? 'border-blue-500/30' : 'border-zinc-700'}`}
          onClick={() => setActiveMode('audio')}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Mic size={24} className={hasAudio ? 'text-blue-400' : 'text-zinc-500'} />
              <span className={`text-sm ${hasAudio ? 'text-blue-400' : 'text-zinc-500'}`}>
                {hasAudio ? '已完成' : '未转录'}
              </span>
            </div>
            
            {hasAudio && analysisData.transcription && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-400">词数:</span>
                  <span className="text-white">{analysisData.transcription.word_count}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">语言:</span>
                  <span className="text-white">{analysisData.transcription.language}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">置信度:</span>
                  <span className="text-white">
                    {(analysisData.transcription.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
            
            {!hasAudio && (
              <p className="text-xs text-zinc-500">点击开始音频转录</p>
            )}
          </div>
        </Card>

        {/* 搜索结果状态 */}
        <Card
          title="搜索结果"
          variant="elevated"
          className={`cursor-pointer transition-all ${hasSearch ? 'border-amber-500/30' : 'border-zinc-700'}`}
          onClick={() => setActiveMode('search')}
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Search size={24} className={hasSearch ? 'text-amber-400' : 'text-zinc-500'} />
              <span className={`text-sm ${hasSearch ? 'text-amber-400' : 'text-zinc-500'}`}>
                {hasSearch ? `${analysisData.search_results?.length} 结果` : '无搜索'}
              </span>
            </div>
            
            {hasSearch && analysisData.search_results && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-zinc-400">视频:</span>
                  <span className="text-white">
                    {analysisData.search_results.filter(r => r.type === 'video').length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">图片:</span>
                  <span className="text-white">
                    {analysisData.search_results.filter(r => r.type === 'image').length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-400">平均相似度:</span>
                  <span className="text-white">
                    {analysisData.search_results.length > 0 
                      ? (analysisData.search_results.reduce((sum, r) => sum + r.similarity_score, 0) / analysisData.search_results.length * 100).toFixed(0) + '%'
                      : '0%'
                    }
                  </span>
                </div>
              </div>
            )}
            
            {!hasSearch && (
              <p className="text-xs text-zinc-500">点击开始多模态搜索</p>
            )}
          </div>
        </Card>
      </div>
    );
  };

  // 渲染分析摘要
  const renderAnalysisSummary = () => {
    if (!analysisData.analysis_summary) return null;

    const summary = analysisData.analysis_summary;

    return (
      <Card title="分析摘要" variant="elevated">
        <div className="space-y-6">
          {/* 主要主题 */}
          {summary.dominant_themes && summary.dominant_themes.length > 0 && (
            <div>
              <h4 className="font-medium text-white mb-3 flex items-center gap-2">
                <TrendingUp size={16} />
                主要主题
              </h4>
              <div className="flex flex-wrap gap-2">
                {summary.dominant_themes.map((theme, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-amber-500/10 text-amber-400 rounded-full text-sm"
                  >
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 关键时刻 */}
          {summary.key_moments && summary.key_moments.length > 0 && (
            <div>
              <h4 className="font-medium text-white mb-3 flex items-center gap-2">
                <Zap size={16} />
                关键时刻
              </h4>
              <div className="space-y-3">
                {summary.key_moments.slice(0, 5).map((moment, index) => (
                  <div key={index} className="p-3 bg-zinc-800/30 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">
                        {Math.floor(moment.timestamp / 60)}:
                        {Math.floor(moment.timestamp % 60).toString().padStart(2, '0')}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-zinc-400">
                          置信度: {(moment.confidence * 100).toFixed(0)}%
                        </span>
                        <div className="flex gap-1">
                          {moment.modalities.map((modality, idx) => (
                            <div
                              key={idx}
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor: modality === 'visual' ? '#f59e0b' : 
                                               modality === 'audio' ? '#3b82f6' : '#10b981'
                              }}
                              title={modality}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                    <p className="text-sm text-zinc-300">{moment.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 质量评分 */}
          {summary.quality_scores && (
            <div>
              <h4 className="font-medium text-white mb-3 flex items-center gap-2">
                <BarChart3 size={16} />
                质量评分
              </h4>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(summary.quality_scores).map(([key, score]) => (
                  <div key={key} className="text-center">
                    <div className="text-2xl font-bold text-white mb-1">
                      {(score * 100).toFixed(0)}
                    </div>
                    <div className="text-xs text-zinc-400">
                      {key === 'visual_quality' ? '视觉质量' :
                       key === 'audio_quality' ? '音频质量' : '内容丰富度'}
                    </div>
                    <div className="w-full bg-zinc-700 rounded-full h-2 mt-2">
                      <div
                        className="bg-gradient-to-r from-amber-500 to-yellow-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 头部控制区域 */}
      <Card title={`多模态分析 - ${assetFilename || assetId}`} variant="elevated">
        <div className="space-y-4">
          {/* 模式选择器 */}
          <div className="flex items-center justify-between">
            {renderModeSelector()}
            
            <div className="flex items-center gap-2">
              {(analysisData.visual_analysis || analysisData.transcription) && (
                <Button
                  onClick={generateAnalysisSummary}
                  loading={loading}
                  icon={TrendingUp}
                  size="sm"
                >
                  生成摘要
                </Button>
              )}
              
              <Button
                onClick={exportAnalysisReport}
                icon={Download}
                size="sm"
                variant="ghost"
              >
                导出报告
              </Button>
              
              <Button
                onClick={() => window.location.reload()}
                icon={RefreshCw}
                size="sm"
                variant="ghost"
              >
                刷新
              </Button>
            </div>
          </div>
          
          {/* 错误信息 */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
        </div>
      </Card>

      {/* 主要内容区域 */}
      {activeMode === 'dashboard' && (
        <div className="space-y-6">
          {/* 分析概览 */}
          {renderAnalysisOverview()}
          
          {/* 分析摘要 */}
          {renderAnalysisSummary()}
        </div>
      )}

      {activeMode === 'search' && (
        <MultimodalSearchPanel
          projectId={projectId}
          onResultsChange={handleSearchResultsChange}
        />
      )}

      {activeMode === 'visual' && (
        <VisualAnalysisPanel
          assetId={assetId}
          assetFilename={assetFilename}
          onAnalysisComplete={handleVisualAnalysisComplete}
        />
      )}

      {activeMode === 'audio' && (
        <AudioTranscriptionPanel
          assetId={assetId}
          assetFilename={assetFilename}
          onTranscriptionComplete={handleTranscriptionComplete}
          onSegmentSelect={handleSegmentSelect}
        />
      )}
    </div>
  );
};

export default MultimodalAnalysisDashboard;