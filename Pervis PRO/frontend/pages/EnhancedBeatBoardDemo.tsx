import React, { useState, useEffect } from 'react';
import EnhancedBeatBoard from '../components/BeatBoard/EnhancedBeatBoard';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Play, Pause, RotateCcw, Settings } from 'lucide-react';

// 模拟Beat数据
const mockBeats = [
  {
    id: 'beat-1',
    order_index: 0,
    content: '一个神秘的蓝色夜景城市，霓虹灯闪烁，雨水反射着光芒',
    duration: 5,
    emotion_tags: ['神秘', '紧张'],
    scene_tags: ['城市', '夜晚', '雨天'],
    action_tags: ['静态', '氛围']
  },
  {
    id: 'beat-2',
    order_index: 1,
    content: '主角在昏暗的街道上快速奔跑，追逐着什么',
    duration: 4,
    emotion_tags: ['紧张', '急迫'],
    scene_tags: ['街道', '夜晚'],
    action_tags: ['奔跑', '追逐']
  },
  {
    id: 'beat-3',
    order_index: 2,
    content: '温暖的室内场景，橙色灯光，人物对话',
    duration: 6,
    emotion_tags: ['温暖', '亲密'],
    scene_tags: ['室内', '家庭'],
    action_tags: ['对话', '静坐']
  },
  {
    id: 'beat-4',
    order_index: 3,
    content: '激烈的动作场面，快速剪切，红色调',
    duration: 3,
    emotion_tags: ['激烈', '愤怒'],
    scene_tags: ['战斗', '室内'],
    action_tags: ['打斗', '快速移动']
  },
  {
    id: 'beat-5',
    order_index: 4,
    content: '平静的结尾，绿色自然场景，阳光透过树叶',
    duration: 7,
    emotion_tags: ['平静', '希望'],
    scene_tags: ['自然', '白天', '森林'],
    action_tags: ['静态', '沉思']
  }
];

const EnhancedBeatBoardDemo: React.FC = () => {
  const [selectedBeat, setSelectedBeat] = useState<number>(0);
  const [enableImageRecommendations, setEnableImageRecommendations] = useState<boolean>(true);
  const [projectId] = useState<string>('demo-project');

  const handleBeatSelect = (beatIndex: number) => {
    setSelectedBeat(beatIndex);
    console.log('Selected beat:', beatIndex, mockBeats[beatIndex]);
  };

  const resetDemo = () => {
    setSelectedBeat(0);
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        {/* 头部 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            Enhanced BeatBoard Demo
          </h1>
          <p className="text-zinc-400 mb-4">
            集成图片推荐功能的增强版BeatBoard演示
          </p>

          {/* 控制面板 */}
          <Card padding="md" className="mb-6">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-400">当前Beat:</span>
                  <span className="text-amber-400 font-semibold">
                    {selectedBeat + 1} / {mockBeats.length}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-zinc-400">内容:</span>
                  <span className="text-white text-sm max-w-md truncate">
                    {mockBeats[selectedBeat]?.content}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {/* 图片推荐开关 */}
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={enableImageRecommendations}
                    onChange={(e) => setEnableImageRecommendations(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-zinc-300">图片推荐</span>
                </label>

                {/* 重置按钮 */}
                <Button
                  variant="ghost"
                  size="sm"
                  icon={RotateCcw}
                  onClick={resetDemo}
                >
                  重置
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Enhanced BeatBoard */}
        <EnhancedBeatBoard
          projectId={projectId}
          beats={mockBeats}
          onBeatSelect={handleBeatSelect}
          enableImageRecommendations={enableImageRecommendations}
          className="mb-8"
        />

        {/* 功能说明 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card title="多模态搜索" padding="md">
            <p className="text-zinc-400 text-sm mb-3">
              基于Beat内容自动搜索相关的视频和图片素材
            </p>
            <ul className="text-xs text-zinc-500 space-y-1">
              <li>• 语义内容匹配</li>
              <li>• 情绪标签匹配</li>
              <li>• 场景标签匹配</li>
              <li>• 视觉特征匹配</li>
            </ul>
          </Card>

          <Card title="智能推荐" padding="md">
            <p className="text-zinc-400 text-sm mb-3">
              AI驱动的媒体推荐，提供相关度评分和匹配理由
            </p>
            <ul className="text-xs text-zinc-500 space-y-1">
              <li>• 实时推荐更新</li>
              <li>• 相似度评分</li>
              <li>• 匹配理由说明</li>
              <li>• 媒体类型过滤</li>
            </ul>
          </Card>

          <Card title="交互功能" padding="md">
            <p className="text-zinc-400 text-sm mb-3">
              丰富的交互功能，提升创作效率
            </p>
            <ul className="text-xs text-zinc-500 space-y-1">
              <li>• 媒体预览</li>
              <li>• 一键下载</li>
              <li>• 网格/列表视图</li>
              <li>• 同步播放控制</li>
            </ul>
          </Card>
        </div>

        {/* 使用说明 */}
        <Card title="使用说明" padding="md" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="text-white font-semibold mb-2">基本操作</h4>
              <ul className="text-zinc-400 space-y-1">
                <li>• 点击Beat卡片切换当前Beat</li>
                <li>• 使用播放按钮控制播放状态</li>
                <li>• 右侧面板显示相关媒体推荐</li>
                <li>• 点击推荐媒体进行预览或下载</li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-white font-semibold mb-2">高级功能</h4>
              <ul className="text-zinc-400 space-y-1">
                <li>• 按媒体类型过滤推荐结果</li>
                <li>• 切换网格和列表视图模式</li>
                <li>• 查看相似度评分和匹配理由</li>
                <li>• 隐藏/显示推荐面板</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* 技术特性 */}
        <Card title="技术特性" padding="md" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div>
              <h4 className="text-amber-400 font-semibold mb-2">后端集成</h4>
              <ul className="text-zinc-400 space-y-1">
                <li>• 多模态搜索API</li>
                <li>• 图片处理系统</li>
                <li>• 智能推荐算法</li>
                <li>• 实时数据同步</li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-amber-400 font-semibold mb-2">前端优化</h4>
              <ul className="text-zinc-400 space-y-1">
                <li>• 响应式设计</li>
                <li>• 懒加载优化</li>
                <li>• 流畅动画效果</li>
                <li>• 键盘快捷键</li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-amber-400 font-semibold mb-2">用户体验</h4>
              <ul className="text-zinc-400 space-y-1">
                <li>• 直观的操作界面</li>
                <li>• 实时反馈</li>
                <li>• 错误处理</li>
                <li>• 无障碍支持</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedBeatBoardDemo;