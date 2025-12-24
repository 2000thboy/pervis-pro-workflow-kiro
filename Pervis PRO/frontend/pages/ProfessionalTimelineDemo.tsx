import React, { useState } from 'react';
import { 
  Play, 
  Settings, 
  Info, 
  Download, 
  Upload,
  Layers,
  Clock,
  Zap,
  Target,
  Scissors,
  Move
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import ProfessionalTimelineEditor from '../components/VideoEditor/ProfessionalTimelineEditor';

const ProfessionalTimelineDemo: React.FC = () => {
  const [selectedDemo, setSelectedDemo] = useState<'basic' | 'advanced' | 'professional'>('professional');
  const [showFeatures, setShowFeatures] = useState(true);

  // 演示项目数据
  const demoProject = {
    id: 'demo-project-timeline',
    name: '专业时间轴演示项目',
    description: '展示专业级时间线编辑功能'
  };

  const renderFeatureHighlights = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card title="磁性吸附" variant="elevated" className="p-4">
        <div className="space-y-3">
          <Target size={32} className="text-amber-400" />
          <p className="text-sm text-zinc-400">
            智能磁性吸附功能，自动对齐到片段边界、播放头和标记点，提供精确的编辑体验。
          </p>
          <div className="flex flex-wrap gap-1">
            <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-xs rounded">片段对齐</span>
            <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-xs rounded">播放头吸附</span>
            <span className="px-2 py-1 bg-amber-500/10 text-amber-400 text-xs rounded">标记点对齐</span>
          </div>
        </div>
      </Card>

      <Card title="帧精确控制" variant="elevated" className="p-4">
        <div className="space-y-3">
          <Clock size={32} className="text-blue-400" />
          <p className="text-sm text-zinc-400">
            支持多种帧率的帧精确编辑，提供专业级的时间控制和精确的in/out点调整。
          </p>
          <div className="flex flex-wrap gap-1">
            <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded">30fps</span>
            <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded">24fps</span>
            <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded">帧步进</span>
          </div>
        </div>
      </Card>

      <Card title="专业工具" variant="elevated" className="p-4">
        <div className="space-y-3">
          <Scissors size={32} className="text-green-400" />
          <p className="text-sm text-zinc-400">
            完整的专业编辑工具集，包括剃刀工具、滑移工具、多轨道编辑和高级选择功能。
          </p>
          <div className="flex flex-wrap gap-1">
            <span className="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded">剃刀工具</span>
            <span className="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded">滑移编辑</span>
            <span className="px-2 py-1 bg-green-500/10 text-green-400 text-xs rounded">多选</span>
          </div>
        </div>
      </Card>

      <Card title="多轨道支持" variant="elevated" className="p-4">
        <div className="space-y-3">
          <Layers size={32} className="text-purple-400" />
          <p className="text-sm text-zinc-400">
            支持多视频轨道和音频轨道，每个轨道可独立控制可见性、锁定状态和音频设置。
          </p>
          <div className="flex flex-wrap gap-1">
            <span className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded">视频轨道</span>
            <span className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded">音频轨道</span>
            <span className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded">轨道锁定</span>
          </div>
        </div>
      </Card>

      <Card title="智能素材集成" variant="elevated" className="p-4">
        <div className="space-y-3">
          <Zap size={32} className="text-yellow-400" />
          <p className="text-sm text-zinc-400">
            集成AssetPickerModal，支持语义搜索和智能推荐，快速找到合适的素材添加到时间轴。
          </p>
          <div className="flex flex-wrap gap-1">
            <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 text-xs rounded">语义搜索</span>
            <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 text-xs rounded">智能推荐</span>
            <span className="px-2 py-1 bg-yellow-500/10 text-yellow-400 text-xs rounded">拖拽添加</span>
          </div>
        </div>
      </Card>

      <Card title="专业导出" variant="elevated" className="p-4">
        <div className="space-y-3">
          <Download size={32} className="text-red-400" />
          <p className="text-sm text-zinc-400">
            支持导出Premiere Pro XML和EDL格式，与专业后期制作软件无缝对接。
          </p>
          <div className="flex flex-wrap gap-1">
            <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded">Premiere XML</span>
            <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded">EDL格式</span>
            <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded">媒体引用</span>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderUsageGuide = () => (
    <Card title="使用指南" variant="outlined">
      <div className="space-y-6">
        <div>
          <h4 className="font-medium text-white mb-3">基础操作</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h5 className="text-amber-400 mb-2">播放控制</h5>
              <ul className="space-y-1 text-zinc-400">
                <li>• 空格键 - 播放/暂停</li>
                <li>• 左/右箭头 - 帧步进</li>
                <li>• Home/End - 跳转到开始/结束</li>
                <li>• J/K/L - 倒放/暂停/播放</li>
              </ul>
            </div>
            <div>
              <h5 className="text-blue-400 mb-2">选择和编辑</h5>
              <ul className="space-y-1 text-zinc-400">
                <li>• 点击 - 选择片段</li>
                <li>• Ctrl+点击 - 多选</li>
                <li>• 拖拽 - 移动片段</li>
                <li>• 拖拽边缘 - 调整时长</li>
              </ul>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-white mb-3">专业功能</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <h5 className="text-green-400 mb-2">工具使用</h5>
              <ul className="space-y-1 text-zinc-400">
                <li>• V - 选择工具</li>
                <li>• C - 剃刀工具</li>
                <li>• S - 滑移工具</li>
                <li>• Ctrl+K - 在播放头处分割</li>
              </ul>
            </div>
            <div>
              <h5 className="text-purple-400 mb-2">高级编辑</h5>
              <ul className="space-y-1 text-zinc-400">
                <li>• 磁性吸附 - 自动对齐</li>
                <li>• 帧精确调整 - 精确控制</li>
                <li>• 多轨道编辑 - 复杂项目</li>
                <li>• 标记点 - 重要位置标记</li>
              </ul>
            </div>
          </div>
        </div>

        <div>
          <h4 className="font-medium text-white mb-3">导出流程</h4>
          <div className="space-y-2 text-sm text-zinc-400">
            <p>1. 完成时间轴编辑后，点击工具栏中的导出按钮</p>
            <p>2. 选择导出格式：XML（Premiere Pro）或 EDL（通用）</p>
            <p>3. 系统会自动包含媒体文件引用和时间码信息</p>
            <p>4. 下载的文件可直接导入到专业后期制作软件中</p>
          </div>
        </div>
      </div>
    </Card>
  );

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      {/* 头部 */}
      <div className="border-b border-zinc-800 bg-zinc-900/95 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">专业时间轴编辑器</h1>
              <p className="text-zinc-400 mt-1">
                体验专业级的时间线编辑功能，包括磁性吸附、帧精确控制和多轨道编辑
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                onClick={() => setShowFeatures(!showFeatures)}
              >
                <Info size={16} className="mr-2" />
                {showFeatures ? '隐藏' : '显示'}功能介绍
              </Button>
              <Button variant="ghost">
                <Settings size={16} className="mr-2" />
                设置
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* 功能亮点 */}
        {showFeatures && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-white mb-2">专业功能亮点</h2>
              <p className="text-zinc-400">
                为导演和编辑师提供专业级的时间线编辑体验
              </p>
            </div>
            
            {renderFeatureHighlights()}
          </div>
        )}

        {/* 演示模式选择 */}
        <Card title="演示模式" variant="elevated">
          <div className="flex items-center gap-3">
            <Button
              variant={selectedDemo === 'basic' ? 'primary' : 'ghost'}
              onClick={() => setSelectedDemo('basic')}
            >
              基础模式
            </Button>
            <Button
              variant={selectedDemo === 'advanced' ? 'primary' : 'ghost'}
              onClick={() => setSelectedDemo('advanced')}
            >
              高级模式
            </Button>
            <Button
              variant={selectedDemo === 'professional' ? 'primary' : 'ghost'}
              onClick={() => setSelectedDemo('professional')}
            >
              专业模式
            </Button>
            
            <div className="ml-auto text-sm text-zinc-400">
              当前项目: {demoProject.name}
            </div>
          </div>
        </Card>

        {/* 专业时间轴编辑器 */}
        <Card title="时间轴编辑器" variant="elevated" className="p-0">
          <ProfessionalTimelineEditor
            projectId={demoProject.id}
            onSave={(timeline) => {
              console.log('Timeline saved:', timeline);
            }}
            onExport={(format) => {
              console.log('Timeline exported as:', format);
            }}
          />
        </Card>

        {/* 使用指南 */}
        {renderUsageGuide()}

        {/* 技术特性 */}
        <Card title="技术特性" variant="outlined">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-white mb-3">核心技术</h4>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full" />
                  React 18 + TypeScript - 现代化前端架构
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full" />
                  Canvas渲染 - 高性能时间轴绘制
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-400 rounded-full" />
                  Web Audio API - 音频波形分析
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-400 rounded-full" />
                  拖拽API - 原生拖拽支持
                </li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-white mb-3">专业特性</h4>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-amber-400 rounded-full" />
                  磁性吸附算法 - 智能对齐检测
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-400 rounded-full" />
                  帧精确计算 - 多帧率支持
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-indigo-400 rounded-full" />
                  实时预览 - 代理文件播放
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-pink-400 rounded-full" />
                  专业导出 - XML/EDL格式
                </li>
              </ul>
            </div>
          </div>
        </Card>

        {/* 性能指标 */}
        <Card title="性能指标" variant="outlined">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-zinc-800/30 rounded-lg">
              <div className="text-2xl font-bold text-green-400 mb-1">60fps</div>
              <div className="text-xs text-zinc-400">时间轴刷新率</div>
            </div>
            <div className="text-center p-4 bg-zinc-800/30 rounded-lg">
              <div className="text-2xl font-bold text-blue-400 mb-1">&lt;5ms</div>
              <div className="text-xs text-zinc-400">磁性吸附延迟</div>
            </div>
            <div className="text-center p-4 bg-zinc-800/30 rounded-lg">
              <div className="text-2xl font-bold text-purple-400 mb-1">1000+</div>
              <div className="text-xs text-zinc-400">支持片段数量</div>
            </div>
            <div className="text-center p-4 bg-zinc-800/30 rounded-lg">
              <div className="text-2xl font-bold text-yellow-400 mb-1">16</div>
              <div className="text-xs text-zinc-400">最大轨道数</div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ProfessionalTimelineDemo;