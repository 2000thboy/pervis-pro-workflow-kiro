import React, { useState } from 'react';
import { 
  Search, 
  Eye, 
  Mic, 
  BarChart3,
  Upload,
  Play,
  Settings,
  Info
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { 
  MultimodalSearchPanel,
  VisualAnalysisPanel,
  AudioTranscriptionPanel,
  MultimodalAnalysisDashboard,
  MultimodalSearchResult
} from '../components/MultimodalSearch';

// 演示模式
type DemoMode = 'search' | 'visual' | 'audio' | 'dashboard';

// 演示资产数据
const DEMO_ASSETS = [
  {
    id: 'demo-video-1',
    filename: 'cyberpunk_chase.mp4',
    type: 'video' as const,
    description: '赛博朋克风格的追逐场景，霓虹灯闪烁的城市夜景'
  },
  {
    id: 'demo-video-2', 
    filename: 'nature_documentary.mp4',
    type: 'video' as const,
    description: '自然纪录片片段，森林中的野生动物'
  },
  {
    id: 'demo-video-3',
    filename: 'dialogue_scene.mp4', 
    type: 'video' as const,
    description: '室内对话场景，两人在咖啡厅交谈'
  }
];

const MultimodalSearchDemo: React.FC = () => {
  const [activeMode, setActiveMode] = useState<DemoMode>('dashboard');
  const [selectedAsset, setSelectedAsset] = useState<string>(DEMO_ASSETS[0].id);
  const [searchResults, setSearchResults] = useState<MultimodalSearchResult[]>([]);

  // 处理搜索结果更新
  const handleSearchResultsChange = (results: MultimodalSearchResult[]) => {
    setSearchResults(results);
  };

  // 处理结果选择
  const handleResultSelect = (result: MultimodalSearchResult) => {
    console.log('Selected result:', result);
    // 可以在这里实现结果选择的逻辑，比如添加到时间线
  };

  // 渲染模式选择器
  const renderModeSelector = () => (
    <div className="flex items-center gap-2 p-1 bg-zinc-800/50 rounded-lg">
      {[
        { key: 'dashboard', label: '综合仪表板', icon: BarChart3 },
        { key: 'search', label: '多模态搜索', icon: Search },
        { key: 'visual', label: '视觉分析', icon: Eye },
        { key: 'audio', label: '音频转录', icon: Mic }
      ].map(mode => (
        <Button
          key={mode.key}
          size="sm"
          variant={activeMode === mode.key ? 'primary' : 'ghost'}
          onClick={() => setActiveMode(mode.key as DemoMode)}
          icon={mode.icon}
        >
          {mode.label}
        </Button>
      ))}
    </div>
  );

  // 渲染资产选择器
  const renderAssetSelector = () => (
    <Card title="演示资产" variant="outlined">
      <div className="space-y-3">
        <p className="text-sm text-zinc-400">
          选择一个演示资产来体验多模态分析功能
        </p>
        
        <div className="space-y-2">
          {DEMO_ASSETS.map(asset => (
            <div
              key={asset.id}
              className={`p-3 rounded-lg border-2 cursor-pointer transition-all ${
                selectedAsset === asset.id
                  ? 'border-amber-500 bg-amber-500/5'
                  : 'border-zinc-700 hover:border-zinc-600 bg-zinc-800/30'
              }`}
              onClick={() => setSelectedAsset(asset.id)}
            >
              <div className="flex items-center gap-3">
                <Play size={16} className="text-zinc-400" />
                <div className="flex-1">
                  <h4 className="font-medium text-white">{asset.filename}</h4>
                  <p className="text-xs text-zinc-400 mt-1">{asset.description}</p>
                </div>
                {selectedAsset === asset.id && (
                  <div className="w-2 h-2 bg-amber-500 rounded-full" />
                )}
              </div>
            </div>
          ))}
        </div>
        
        <div className="pt-3 border-t border-zinc-700">
          <Button
            size="sm"
            variant="ghost"
            icon={Upload}
            className="w-full"
          >
            上传自定义资产
          </Button>
        </div>
      </div>
    </Card>
  );

  // 渲染功能介绍
  const renderFeatureIntro = () => (
    <Card title="多模态搜索系统" variant="elevated">
      <div className="space-y-4">
        <p className="text-zinc-300">
          PreVis PRO 的多模态搜索系统融合了语义理解、视觉分析和音频转录技术，
          为导演提供智能化的素材发现和分析工具。
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-zinc-800/30 rounded-lg">
            <Search size={24} className="text-amber-400 mb-2" />
            <h4 className="font-medium text-white mb-2">智能搜索</h4>
            <p className="text-sm text-zinc-400">
              基于自然语言描述搜索视频内容，支持情绪、场景、动作等多维度查询
            </p>
          </div>
          
          <div className="p-4 bg-zinc-800/30 rounded-lg">
            <Eye size={24} className="text-blue-400 mb-2" />
            <h4 className="font-medium text-white mb-2">视觉分析</h4>
            <p className="text-sm text-zinc-400">
              自动提取关键帧、分析色彩构图、识别物体和场景类型
            </p>
          </div>
          
          <div className="p-4 bg-zinc-800/30 rounded-lg">
            <Mic size={24} className="text-green-400 mb-2" />
            <h4 className="font-medium text-white mb-2">音频转录</h4>
            <p className="text-sm text-zinc-400">
              高精度语音识别，支持多语言转录和说话人识别
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <Info size={16} className="text-blue-400" />
          <p className="text-sm text-blue-300">
            提示：选择不同的演示资产和功能模式来体验完整的多模态分析流程
          </p>
        </div>
      </div>
    </Card>
  );

  // 获取选中资产信息
  const selectedAssetInfo = DEMO_ASSETS.find(asset => asset.id === selectedAsset);

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      {/* 头部 */}
      <div className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">多模态搜索演示</h1>
              <p className="text-zinc-400 mt-1">
                体验 PreVis PRO 的智能素材分析和搜索功能
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button variant="ghost" icon={Settings}>
                设置
              </Button>
              <Button variant="ghost" icon={Info}>
                帮助
              </Button>
            </div>
          </div>
          
          <div className="mt-4">
            {renderModeSelector()}
          </div>
        </div>
      </div>

      {/* 主要内容 */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* 侧边栏 */}
          <div className="lg:col-span-1 space-y-6">
            {renderAssetSelector()}
            
            {/* 搜索结果摘要 */}
            {searchResults.length > 0 && (
              <Card title="搜索结果" variant="outlined">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">总结果:</span>
                    <span className="text-white">{searchResults.length}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">视频:</span>
                    <span className="text-white">
                      {searchResults.filter(r => r.type === 'video').length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">图片:</span>
                    <span className="text-white">
                      {searchResults.filter(r => r.type === 'image').length}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-400">平均相似度:</span>
                    <span className="text-white">
                      {searchResults.length > 0 
                        ? (searchResults.reduce((sum, r) => sum + r.similarity_score, 0) / searchResults.length * 100).toFixed(0) + '%'
                        : '0%'
                      }
                    </span>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* 主要内容区域 */}
          <div className="lg:col-span-3 space-y-6">
            {/* 功能介绍 */}
            {activeMode === 'dashboard' && !selectedAsset && renderFeatureIntro()}
            
            {/* 多模态分析仪表板 */}
            {activeMode === 'dashboard' && selectedAsset && (
              <MultimodalAnalysisDashboard
                assetId={selectedAsset}
                assetFilename={selectedAssetInfo?.filename}
                projectId="demo-project"
              />
            )}

            {/* 多模态搜索面板 */}
            {activeMode === 'search' && (
              <div className="space-y-6">
                {renderFeatureIntro()}
                <MultimodalSearchPanel
                  projectId="demo-project"
                  onResultSelect={handleResultSelect}
                  onResultsChange={handleSearchResultsChange}
                />
              </div>
            )}

            {/* 视觉分析面板 */}
            {activeMode === 'visual' && selectedAsset && (
              <VisualAnalysisPanel
                assetId={selectedAsset}
                assetFilename={selectedAssetInfo?.filename}
              />
            )}

            {/* 音频转录面板 */}
            {activeMode === 'audio' && selectedAsset && (
              <AudioTranscriptionPanel
                assetId={selectedAsset}
                assetFilename={selectedAssetInfo?.filename}
              />
            )}

            {/* 未选择资产时的提示 */}
            {(activeMode === 'visual' || activeMode === 'audio') && !selectedAsset && (
              <Card title="请选择资产" variant="outlined">
                <div className="text-center py-8">
                  <Upload size={48} className="mx-auto mb-3 opacity-50 text-zinc-500" />
                  <p className="text-zinc-400 mb-4">
                    请从左侧选择一个演示资产来开始{activeMode === 'visual' ? '视觉分析' : '音频转录'}
                  </p>
                  <Button
                    onClick={() => setSelectedAsset(DEMO_ASSETS[0].id)}
                    icon={Play}
                  >
                    选择演示资产
                  </Button>
                </div>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultimodalSearchDemo;