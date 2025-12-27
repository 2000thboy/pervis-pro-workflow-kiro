/**
 * 向导步骤4 - 场次规划
 * 显示解析出的场次列表，支持编辑时长和描述
 * 支持场景视觉标签确认（Phase 9）
 */

import React, { useState, useEffect } from 'react';
import { 
  Film, 
  Plus, 
  Trash2, 
  Edit2, 
  Check, 
  X,
  Clock,
  MapPin,
  Sun,
  Moon,
  Users,
  GripVertical,
  Eye,
  Image,
  Loader2
} from 'lucide-react';
import { useWizard } from './WizardContext';
import { SceneInfo } from './types';
import { wizardApi } from './api';
import { VisualTagConfirmPanel } from './VisualTagConfirmPanel';

export const WizardStep4_Scenes: React.FC = () => {
  const { state, updateScenes, setAgentStatus } = useWizard();
  const { scenes } = state;
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<SceneInfo>>({});
  const [showAddForm, setShowAddForm] = useState(false);
  const [newScene, setNewScene] = useState<Partial<SceneInfo>>({
    heading: '',
    location: '',
    timeOfDay: 'DAY',
    description: '',
    characters: [],
    estimatedDuration: 30
  });
  
  // Phase 9: 视觉标签状态
  const [showVisualTagPanel, setShowVisualTagPanel] = useState<string | null>(null);
  const [draftId, setDraftId] = useState<string>('');
  const [isGeneratingImage, setIsGeneratingImage] = useState<string | null>(null);
  const [imageServiceAvailable, setImageServiceAvailable] = useState(false);

  // 初始化
  useEffect(() => {
    // 检查图片生成服务
    wizardApi.getImageServiceStatus()
      .then(status => setImageServiceAvailable(status.configured))
      .catch(() => setImageServiceAvailable(false));
    
    // 获取或创建 draft ID
    if (state.projectId) {
      setDraftId(state.projectId);
    } else {
      setDraftId(`draft_${Date.now()}`);
    }
  }, [state.projectId]);

  // 计算总时长
  const totalDuration = scenes.reduce((sum, s) => sum + s.estimatedDuration, 0);
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}分${secs > 0 ? secs + '秒' : ''}` : `${secs}秒`;
  };

  // 开始编辑
  const handleEdit = (scene: SceneInfo) => {
    setEditingId(scene.sceneId);
    setEditForm({ ...scene });
  };

  // 保存编辑
  const handleSave = () => {
    if (!editingId) return;
    
    updateScenes(
      scenes.map(s => s.sceneId === editingId ? { ...s, ...editForm } as SceneInfo : s)
    );
    setEditingId(null);
    setEditForm({});
  };

  // 取消编辑
  const handleCancel = () => {
    setEditingId(null);
    setEditForm({});
  };

  // 删除场次
  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个场次吗？')) {
      updateScenes(scenes.filter(s => s.sceneId !== id));
    }
  };

  // 添加新场次
  const handleAddScene = () => {
    if (!newScene.heading?.trim()) return;
    
    const newSceneData: SceneInfo = {
      sceneId: `scene_${Date.now()}`,
      sceneNumber: scenes.length + 1,
      heading: newScene.heading || '',
      location: newScene.location || '',
      timeOfDay: newScene.timeOfDay || 'DAY',
      description: newScene.description || '',
      characters: newScene.characters || [],
      estimatedDuration: newScene.estimatedDuration || 30
    };
    
    updateScenes([...scenes, newSceneData]);
    setNewScene({
      heading: '',
      location: '',
      timeOfDay: 'DAY',
      description: '',
      characters: [],
      estimatedDuration: 30
    });
    setShowAddForm(false);
  };

  // 时间图标
  const TimeIcon = ({ time }: { time: string }) => {
    const isNight = time.toLowerCase().includes('night') || 
                    time.toLowerCase().includes('夜') ||
                    time.toLowerCase().includes('晚');
    return isNight ? <Moon size={14} className="text-indigo-400" /> : <Sun size={14} className="text-amber-400" />;
  };

  // Phase 9: 生成场景概念图
  const handleGenerateSceneImage = async (scene: SceneInfo) => {
    if (!imageServiceAvailable) {
      alert('图片生成服务未配置');
      return;
    }
    setIsGeneratingImage(scene.sceneId);
    setAgentStatus('Art_Agent', { status: 'working', message: `正在生成 ${scene.heading} 的概念图...`, progress: 30 });
    try {
      const result = await wizardApi.generateSceneImage({
        scene_name: scene.heading,
        scene_description: scene.description,
        time_of_day: scene.timeOfDay,
        style: 'cinematic',
        scene_id: scene.sceneId
      });
      if (result.status === 'completed' && result.image_url) {
        updateScenes(
          scenes.map(s => s.sceneId === scene.sceneId ? {
            ...s,
            referenceImage: result.image_url,
            thumbnailImage: result.thumbnail_path
          } as SceneInfo : s)
        );
        setAgentStatus('Art_Agent', { status: 'completed', message: '场景概念图生成完成', progress: 100 });
      } else if (result.status === 'failed') {
        throw new Error(result.error || '生成失败');
      }
    } catch (error: any) {
      console.error('生成场景图失败:', error);
      setAgentStatus('Art_Agent', { status: 'failed', message: error.message || '生成失败', progress: 0 });
    } finally {
      setIsGeneratingImage(null);
    }
  };

  // Phase 9: 打开视觉标签面板
  const handleOpenVisualTags = (scene: SceneInfo) => {
    const sceneWithImage = scene as any;
    if (!sceneWithImage.referenceImage && !sceneWithImage.thumbnailImage) {
      alert('请先生成或上传场景参考图');
      return;
    }
    setShowVisualTagPanel(scene.sceneId);
  };

  // Phase 9: 视觉标签确认回调
  const handleVisualTagConfirm = (sceneId: string, tags: Record<string, any>) => {
    updateScenes(
      scenes.map(s => s.sceneId === sceneId ? {
        ...s,
        visualTags: tags
      } as SceneInfo : s)
    );
    setShowVisualTagPanel(null);
    setAgentStatus('Script_Agent', { status: 'completed', message: '场景视觉标签已确认', progress: 100 });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 头部统计 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Film className="text-amber-500" size={20} />
            场次列表
          </h2>
          <p className="text-sm text-zinc-500 mt-1">
            共 {scenes.length} 个场次，预计总时长 {formatDuration(totalDuration)}
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors"
        >
          <Plus size={16} />
          <span>添加场次</span>
        </button>
      </div>

      {/* 时长进度条 */}
      {scenes.length > 0 && (
        <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-zinc-500">时长分布</span>
            <span className="text-xs text-zinc-400">{formatDuration(totalDuration)}</span>
          </div>
          <div className="h-4 bg-zinc-800 rounded-full overflow-hidden flex">
            {scenes.map((scene, i) => {
              const width = (scene.estimatedDuration / totalDuration) * 100;
              const colors = ['bg-amber-500', 'bg-yellow-500', 'bg-orange-500', 'bg-red-500', 'bg-pink-500', 'bg-purple-500', 'bg-indigo-500', 'bg-blue-500', 'bg-cyan-500', 'bg-teal-500'];
              return (
                <div
                  key={scene.sceneId}
                  className={`${colors[i % colors.length]} h-full transition-all`}
                  style={{ width: `${width}%` }}
                  title={`${scene.heading}: ${formatDuration(scene.estimatedDuration)}`}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* 添加场次表单 */}
      {showAddForm && (
        <div className="p-4 bg-zinc-900 border border-zinc-700 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-zinc-300">添加新场次</span>
            <button onClick={() => setShowAddForm(false)} className="text-zinc-500 hover:text-white">
              <X size={16} />
            </button>
          </div>
          
          <input
            type="text"
            value={newScene.heading || ''}
            onChange={(e) => setNewScene({ ...newScene, heading: e.target.value })}
            placeholder="场景标题 (如: INT. 咖啡馆 - 日)"
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 outline-none"
          />
          
          <div className="grid grid-cols-2 gap-4">
            <input
              type="text"
              value={newScene.location || ''}
              onChange={(e) => setNewScene({ ...newScene, location: e.target.value })}
              placeholder="地点"
              className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 outline-none"
            />
            <select
              value={newScene.timeOfDay || 'DAY'}
              onChange={(e) => setNewScene({ ...newScene, timeOfDay: e.target.value })}
              className="px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none"
            >
              <option value="DAY">日</option>
              <option value="NIGHT">夜</option>
              <option value="DAWN">黎明</option>
              <option value="DUSK">黄昏</option>
            </select>
          </div>

          <textarea
            value={newScene.description || ''}
            onChange={(e) => setNewScene({ ...newScene, description: e.target.value })}
            placeholder="场景描述..."
            rows={2}
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 outline-none resize-none"
          />

          <div className="flex items-center gap-4">
            <label className="text-sm text-zinc-400">预计时长:</label>
            <input
              type="number"
              min="1"
              max="600"
              value={newScene.estimatedDuration || 30}
              onChange={(e) => setNewScene({ ...newScene, estimatedDuration: parseInt(e.target.value) || 30 })}
              className="w-20 px-3 py-1 bg-zinc-800 border border-zinc-700 rounded text-white text-center focus:border-amber-500 outline-none"
            />
            <span className="text-sm text-zinc-500">秒</span>
          </div>

          <div className="flex justify-end gap-2">
            <button
              onClick={() => setShowAddForm(false)}
              className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white"
            >
              取消
            </button>
            <button
              onClick={handleAddScene}
              disabled={!newScene.heading?.trim()}
              className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-black text-sm font-medium rounded-lg disabled:opacity-50"
            >
              添加
            </button>
          </div>
        </div>
      )}

      {/* 场次列表 */}
      <div className="space-y-2">
        {scenes.map((scene, index) => (
          <div
            key={scene.sceneId}
            className="group p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors"
          >
            {editingId === scene.sceneId ? (
              // 编辑模式
              <div className="space-y-3">
                <input
                  type="text"
                  value={editForm.heading || ''}
                  onChange={(e) => setEditForm({ ...editForm, heading: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none"
                />
                <textarea
                  value={editForm.description || ''}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none resize-none"
                />
                <div className="flex items-center gap-4">
                  <input
                    type="number"
                    min="1"
                    value={editForm.estimatedDuration || 30}
                    onChange={(e) => setEditForm({ ...editForm, estimatedDuration: parseInt(e.target.value) || 30 })}
                    className="w-20 px-3 py-1 bg-zinc-800 border border-zinc-700 rounded text-white text-center focus:border-amber-500 outline-none"
                  />
                  <span className="text-sm text-zinc-500">秒</span>
                  <div className="flex-1" />
                  <button onClick={handleCancel} className="p-2 text-zinc-400 hover:text-white">
                    <X size={16} />
                  </button>
                  <button onClick={handleSave} className="p-2 text-emerald-400 hover:text-emerald-300">
                    <Check size={16} />
                  </button>
                </div>
              </div>
            ) : (
              // 显示模式
              <div className="flex items-start gap-4">
                {/* 序号 */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <GripVertical size={16} className="text-zinc-700 opacity-0 group-hover:opacity-100 cursor-grab" />
                  <div className="w-8 h-8 bg-zinc-800 rounded-lg flex items-center justify-center text-sm font-mono text-zinc-400">
                    {scene.sceneNumber || index + 1}
                  </div>
                </div>

                {/* 内容 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-white truncate">{scene.heading}</h3>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-3 text-xs text-zinc-500 mb-2">
                    <span className="flex items-center gap-1">
                      <MapPin size={12} />
                      {scene.location || '未知地点'}
                    </span>
                    <span className="flex items-center gap-1">
                      <TimeIcon time={scene.timeOfDay} />
                      {scene.timeOfDay}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={12} />
                      {formatDuration(scene.estimatedDuration)}
                    </span>
                    {scene.characters.length > 0 && (
                      <span className="flex items-center gap-1">
                        <Users size={12} />
                        {scene.characters.join(', ')}
                      </span>
                    )}
                  </div>

                  {scene.description && (
                    <p className="text-xs text-zinc-400 line-clamp-2">{scene.description}</p>
                  )}
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => handleOpenVisualTags(scene)}
                    disabled={!(scene as any).referenceImage && !(scene as any).thumbnailImage}
                    className={`p-2 rounded-lg transition-colors ${((scene as any).referenceImage || (scene as any).thumbnailImage) ? 'text-zinc-500 hover:text-cyan-400 hover:bg-zinc-800' : 'text-zinc-700 cursor-not-allowed'}`}
                    title="AI 分析视觉标签"
                  >
                    <Eye size={14} />
                  </button>
                  <button
                    onClick={() => handleGenerateSceneImage(scene)}
                    disabled={isGeneratingImage === scene.sceneId || !imageServiceAvailable}
                    className={`p-2 rounded-lg transition-colors ${imageServiceAvailable ? 'text-zinc-500 hover:text-purple-400 hover:bg-zinc-800' : 'text-zinc-700 cursor-not-allowed'} disabled:opacity-50`}
                    title={imageServiceAvailable ? 'AI 生成场景概念图' : '图片生成服务未配置'}
                  >
                    {isGeneratingImage === scene.sceneId ? <Loader2 size={14} className="animate-spin text-purple-500" /> : <Image size={14} />}
                  </button>
                  <button
                    onClick={() => handleEdit(scene)}
                    className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    onClick={() => handleDelete(scene.sceneId)}
                    className="p-2 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded-lg transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 空状态 */}
      {scenes.length === 0 && !showAddForm && (
        <div className="text-center py-12">
          <Film className="mx-auto text-zinc-700 mb-4" size={48} />
          <div className="text-zinc-500 mb-4">暂无场次</div>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black font-medium rounded-lg transition-colors"
          >
            添加第一个场次
          </button>
        </div>
      )}

      {/* 提示信息 */}
      {scenes.length > 0 && (
        <div className="p-4 bg-zinc-900/30 border border-zinc-800 rounded-xl">
          <div className="text-sm text-zinc-400 mb-2">💡 提示</div>
          <ul className="text-xs text-zinc-500 space-y-1">
            <li>• 点击 <Image size={12} className="inline text-purple-500" /> 可以让 AI 生成场景概念图{!imageServiceAvailable && <span className="text-red-400">（需配置 REPLICATE_API_TOKEN）</span>}</li>
            <li>• 点击 <Eye size={12} className="inline text-cyan-500" /> 可以让 AI 分析场景图生成视觉标签</li>
            <li>• 拖拽场次可以调整顺序</li>
          </ul>
        </div>
      )}

      {/* Phase 9: 视觉标签确认面板 */}
      {showVisualTagPanel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-lg">
            <VisualTagConfirmPanel
              draftId={draftId}
              type="scene"
              entityId={showVisualTagPanel}
              entityName={scenes.find(s => s.sceneId === showVisualTagPanel)?.heading || ''}
              imagePath={(scenes.find(s => s.sceneId === showVisualTagPanel) as any)?.referenceImage ||
                        (scenes.find(s => s.sceneId === showVisualTagPanel) as any)?.thumbnailImage}
              onConfirm={(tags) => handleVisualTagConfirm(showVisualTagPanel, tags)}
              onCancel={() => setShowVisualTagPanel(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default WizardStep4_Scenes;
