/**
 * 向导步骤3 - 角色设定
 * 显示解析出的角色列表，支持编辑和添加标签
 * 支持 AI 生成人设图
 * 支持视觉标签确认（Phase 9）
 */

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Plus, 
  Trash2, 
  Edit2, 
  Check, 
  X,
  Sparkles,
  MessageSquare,
  Image,
  Loader2,
  Eye,
  Tag
} from 'lucide-react';
import { useWizard } from './WizardContext';
import { CharacterInfo } from './types';
import { wizardApi } from './api';
import { VisualTagConfirmPanel } from './VisualTagConfirmPanel';

export const WizardStep3_Characters: React.FC = () => {
  const { state, updateCharacters, setAgentStatus } = useWizard();
  const { characters, script } = state;
  
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<Partial<CharacterInfo>>({});
  const [isGeneratingBio, setIsGeneratingBio] = useState<string | null>(null);
  const [isGeneratingImage, setIsGeneratingImage] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCharacter, setNewCharacter] = useState({ name: '', tags: {} as Record<string, string> });
  const [imageServiceAvailable, setImageServiceAvailable] = useState(false);
  
  // Phase 9: 视觉标签确认状态
  const [showVisualTagPanel, setShowVisualTagPanel] = useState<string | null>(null);
  const [draftId, setDraftId] = useState<string>('');

  // 检查图片生成服务状态
  useEffect(() => {
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

  // 开始编辑
  const handleEdit = (char: CharacterInfo) => {
    setEditingId(char.id);
    setEditForm({ ...char });
  };

  // 保存编辑
  const handleSave = () => {
    if (!editingId || !editForm.name) return;
    updateCharacters(
      characters.map(c => c.id === editingId ? { ...c, ...editForm } as CharacterInfo : c)
    );
    setEditingId(null);
    setEditForm({});
  };

  // 取消编辑
  const handleCancel = () => {
    setEditingId(null);
    setEditForm({});
  };

  // 删除角色
  const handleDelete = (id: string) => {
    if (confirm('确定要删除这个角色吗？')) {
      updateCharacters(characters.filter(c => c.id !== id));
    }
  };

  // 添加新角色
  const handleAddCharacter = () => {
    if (!newCharacter.name.trim()) return;
    const newChar: CharacterInfo = {
      id: `char_${Date.now()}`,
      name: newCharacter.name.trim(),
      dialogueCount: 0,
      firstAppearance: 1,
      tags: newCharacter.tags
    };
    updateCharacters([...characters, newChar]);
    setNewCharacter({ name: '', tags: {} });
    setShowAddForm(false);
  };

  // AI 生成人物小传
  const handleGenerateBio = async (char: CharacterInfo) => {
    if (!script.content) {
      alert('请先在上一步导入剧本');
      return;
    }
    setIsGeneratingBio(char.id);
    setAgentStatus('Script_Agent', { status: 'working', message: `正在生成 ${char.name} 的人物小传...`, progress: 50 });
    try {
      const result = await wizardApi.generateContent({
        project_id: state.projectId || 'temp',
        content_type: 'character_bio',
        context: { script_content: script.content },
        entity_name: char.name
      });
      if (result.status === 'completed' && result.content) {
        updateCharacters(
          characters.map(c => c.id === char.id ? { ...c, bio: result.content.bio || result.content } : c)
        );
      }
      setAgentStatus('Script_Agent', { status: 'completed', message: '生成完成', progress: 100 });
    } catch (error) {
      console.error('生成人物小传失败:', error);
      setAgentStatus('Script_Agent', { status: 'failed', message: '生成失败', progress: 0 });
    } finally {
      setIsGeneratingBio(null);
    }
  };

  // AI 生成人设图
  const handleGenerateImage = async (char: CharacterInfo) => {
    if (!imageServiceAvailable) {
      alert('图片生成服务未配置，请在后端设置 REPLICATE_API_TOKEN');
      return;
    }
    setIsGeneratingImage(char.id);
    setAgentStatus('Art_Agent', { status: 'working', message: `正在生成 ${char.name} 的人设图...`, progress: 30 });
    try {
      const result = await wizardApi.generateCharacterImage({
        character_name: char.name,
        character_bio: char.bio || '',
        tags: char.tags || {},
        style: 'cinematic',
        character_id: char.id
      });
      if (result.status === 'completed' && result.image_url) {
        updateCharacters(
          characters.map(c => c.id === char.id ? { 
            ...c, 
            generatedImage: result.image_url,
            thumbnailImage: result.thumbnail_path 
          } : c)
        );
        setAgentStatus('Art_Agent', { status: 'completed', message: '人设图生成完成', progress: 100 });
      } else if (result.status === 'failed') {
        throw new Error(result.error || '生成失败');
      }
    } catch (error: any) {
      console.error('生成人设图失败:', error);
      // 解析错误消息
      let errorMessage = '生成失败';
      if (error.response?.status === 402 || error.message?.includes('402') || error.message?.includes('余额不足') || error.message?.includes('Insufficient credit')) {
        errorMessage = 'Replicate API 余额不足，请前往 replicate.com 充值后重试';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      setAgentStatus('Art_Agent', { status: 'failed', message: errorMessage, progress: 0 });
      alert(`生成失败: ${errorMessage}`);
    } finally {
      setIsGeneratingImage(null);
    }
  };

  // Phase 9: 打开视觉标签确认面板
  const handleOpenVisualTags = (char: CharacterInfo) => {
    if (!char.generatedImage && !char.thumbnailImage) {
      alert('请先生成或上传人设图');
      return;
    }
    setShowVisualTagPanel(char.id);
  };

  // Phase 9: 视觉标签确认回调
  const handleVisualTagConfirm = (charId: string, tags: Record<string, any>) => {
    // 将视觉标签合并到角色标签中
    updateCharacters(
      characters.map(c => c.id === charId ? {
        ...c,
        tags: {
          ...c.tags,
          ...tags.appearance,
          clothing_style: tags.clothing_style,
        },
        visualTags: tags  // 保存完整的视觉标签
      } : c)
    );
    setShowVisualTagPanel(null);
    setAgentStatus('Script_Agent', { status: 'completed', message: '视觉标签已确认', progress: 100 });
  };

  // 预设标签选项
  const TAG_OPTIONS = {
    role: ['主角', '配角', '反派', '导师', '爱人', '朋友'],
    age: ['儿童', '青年', '中年', '老年'],
    gender: ['男', '女', '其他'],
    personality: ['内向', '外向', '冷静', '冲动', '善良', '狡猾']
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Users className="text-amber-500" size={20} />
            角色列表
          </h2>
          <p className="text-sm text-zinc-500 mt-1">
            {characters.length > 0 
              ? `共 ${characters.length} 个角色，可编辑或添加标签`
              : '暂无角色，请手动添加或返回上一步解析剧本'}
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors"
        >
          <Plus size={16} />
          <span>添加角色</span>
        </button>
      </div>

      {/* 添加角色表单 */}
      {showAddForm && (
        <div className="p-4 bg-zinc-900 border border-zinc-700 rounded-xl space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-zinc-300">添加新角色</span>
            <button onClick={() => setShowAddForm(false)} className="text-zinc-500 hover:text-white">
              <X size={16} />
            </button>
          </div>
          <input
            type="text"
            value={newCharacter.name}
            onChange={(e) => setNewCharacter({ ...newCharacter, name: e.target.value })}
            placeholder="角色名称"
            className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 outline-none"
          />
          <div className="flex justify-end gap-2">
            <button onClick={() => setShowAddForm(false)} className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white">
              取消
            </button>
            <button
              onClick={handleAddCharacter}
              disabled={!newCharacter.name.trim()}
              className="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-black text-sm font-medium rounded-lg disabled:opacity-50"
            >
              添加
            </button>
          </div>
        </div>
      )}

      {/* 角色列表 */}
      <div className="space-y-3">
        {characters.map((char) => (
          <div key={char.id} className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors">
            {editingId === char.id ? (
              <div className="space-y-4">
                <input
                  type="text"
                  value={editForm.name || ''}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none"
                />
                <div className="space-y-2">
                  <div className="text-xs text-zinc-500">角色标签</div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(TAG_OPTIONS).map(([category, options]) => (
                      <select
                        key={category}
                        value={editForm.tags?.[category] || ''}
                        onChange={(e) => setEditForm({
                          ...editForm,
                          tags: { ...editForm.tags, [category]: e.target.value }
                        })}
                        className="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-xs text-zinc-300 focus:border-amber-500 outline-none"
                      >
                        <option value="">{category}</option>
                        {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                      </select>
                    ))}
                  </div>
                </div>
                <div className="flex justify-end gap-2">
                  <button onClick={handleCancel} className="px-3 py-1.5 text-sm text-zinc-400 hover:text-white"><X size={14} /></button>
                  <button onClick={handleSave} className="px-3 py-1.5 text-sm text-emerald-400 hover:text-emerald-300"><Check size={14} /></button>
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-amber-500/20 to-yellow-500/20 rounded-lg flex items-center justify-center text-lg font-bold text-amber-400 flex-shrink-0 overflow-hidden">
                  {char.generatedImage ? (
                    <img 
                      src={char.generatedImage.startsWith('http') ? char.generatedImage : `http://127.0.0.1:8000${char.generatedImage}`} 
                      alt={char.name} 
                      className="w-full h-full object-cover" 
                      onError={(e) => {
                        // 图片加载失败时显示首字母
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  ) : (
                    char.name.charAt(0)
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-base font-medium text-white">{char.name}</h3>
                    {char.dialogueCount > 0 && (
                      <span className="flex items-center gap-1 text-xs text-zinc-500">
                        <MessageSquare size={12} />
                        {char.dialogueCount} 句对话
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {Object.entries(char.tags || {}).map(([key, value]) => (
                      value && <span key={key} className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">{value}</span>
                    ))}
                    {Object.keys(char.tags || {}).length === 0 && <span className="text-xs text-zinc-600">暂无标签</span>}
                  </div>
                  {char.bio && <div className="text-sm text-zinc-400 mt-2 p-2 bg-zinc-800/50 rounded">{char.bio}</div>}
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  <button
                    onClick={() => handleOpenVisualTags(char)}
                    disabled={!char.generatedImage && !char.thumbnailImage}
                    className={`p-2 rounded-lg transition-colors ${(char.generatedImage || char.thumbnailImage) ? 'text-zinc-500 hover:text-cyan-400 hover:bg-zinc-800' : 'text-zinc-700 cursor-not-allowed'}`}
                    title="AI 分析视觉标签"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => handleGenerateImage(char)}
                    disabled={isGeneratingImage === char.id || !imageServiceAvailable}
                    className={`p-2 rounded-lg transition-colors ${imageServiceAvailable ? 'text-zinc-500 hover:text-purple-400 hover:bg-zinc-800' : 'text-zinc-700 cursor-not-allowed'} disabled:opacity-50`}
                    title={imageServiceAvailable ? 'AI 生成人设图' : '图片生成服务未配置'}
                  >
                    {isGeneratingImage === char.id ? <Loader2 size={16} className="animate-spin text-purple-500" /> : <Image size={16} />}
                  </button>
                  <button
                    onClick={() => handleGenerateBio(char)}
                    disabled={isGeneratingBio === char.id}
                    className="p-2 text-zinc-500 hover:text-amber-400 hover:bg-zinc-800 rounded-lg transition-colors disabled:opacity-50"
                    title="AI 生成人物小传"
                  >
                    {isGeneratingBio === char.id ? <div className="w-4 h-4 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" /> : <Sparkles size={16} />}
                  </button>
                  <button onClick={() => handleEdit(char)} className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors" title="编辑"><Edit2 size={16} /></button>
                  <button onClick={() => handleDelete(char.id)} className="p-2 text-zinc-500 hover:text-red-400 hover:bg-zinc-800 rounded-lg transition-colors" title="删除"><Trash2 size={16} /></button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {characters.length === 0 && !showAddForm && (
        <div className="text-center py-12">
          <Users className="mx-auto text-zinc-700 mb-4" size={48} />
          <div className="text-zinc-500 mb-4">暂无角色</div>
          <button onClick={() => setShowAddForm(true)} className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black font-medium rounded-lg transition-colors">
            添加第一个角色
          </button>
        </div>
      )}

      {characters.length > 0 && (
        <div className="p-4 bg-zinc-900/30 border border-zinc-800 rounded-xl">
          <div className="text-sm text-zinc-400 mb-2">💡 提示</div>
          <ul className="text-xs text-zinc-500 space-y-1">
            <li>• 点击 <Sparkles size={12} className="inline text-amber-500" /> 可以让 AI 生成人物小传</li>
            <li>• 点击 <Image size={12} className="inline text-purple-500" /> 可以让 AI 生成人设图{!imageServiceAvailable && <span className="text-red-400">（需配置 REPLICATE_API_TOKEN）</span>}</li>
            <li>• 点击 <Eye size={12} className="inline text-cyan-500" /> 可以让 AI 分析人设图生成视觉标签</li>
            <li>• 角色标签会用于后续的素材匹配和搜索</li>
          </ul>
        </div>
      )}

      {/* Phase 9: 视觉标签确认面板 */}
      {showVisualTagPanel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="w-full max-w-lg">
            <VisualTagConfirmPanel
              draftId={draftId}
              type="character"
              entityId={showVisualTagPanel}
              entityName={characters.find(c => c.id === showVisualTagPanel)?.name || ''}
              imagePath={characters.find(c => c.id === showVisualTagPanel)?.generatedImage || 
                        characters.find(c => c.id === showVisualTagPanel)?.thumbnailImage}
              onConfirm={(tags) => handleVisualTagConfirm(showVisualTagPanel, tags)}
              onCancel={() => setShowVisualTagPanel(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default WizardStep3_Characters;
