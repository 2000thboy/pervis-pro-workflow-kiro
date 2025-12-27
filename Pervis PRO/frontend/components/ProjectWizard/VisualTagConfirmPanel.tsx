/**
 * 视觉标签确认面板
 * Phase 9 Task 9.6: 前端标签确认 UI
 * 
 * 显示 AI 生成的视觉标签，供用户确认或修改
 */

import React, { useState, useEffect } from 'react';
import {
  Eye,
  Check,
  X,
  Edit2,
  Loader2,
  AlertCircle,
  Image,
  Palette,
  Tag,
  RefreshCw
} from 'lucide-react';
import { wizardApi } from './api';

// 角色视觉标签
interface CharacterVisualTag {
  character_id: string;
  image_path: string;
  tags: {
    appearance?: {
      hair?: string;
      skin?: string;
      build?: string;
      face?: string;
      age_appearance?: string;
    };
    clothing_style?: string;
    color_palette?: string[];
    accessories?: string[];
    distinctive_features?: string;
    summary?: string;
  };
  confidence: number;
  confirmed: boolean;
}

// 场景视觉标签
interface SceneVisualTag {
  scene_id: string;
  image_path: string;
  tags: {
    scene_type?: string;
    time_of_day?: string;
    lighting?: string;
    mood?: string;
    environment?: string[];
    architecture_style?: string;
    color_tone?: string;
    summary?: string;
  };
  confidence: number;
  confirmed: boolean;
}

interface VisualTagConfirmPanelProps {
  draftId: string;
  type: 'character' | 'scene';
  entityId: string;
  entityName: string;
  imagePath?: string;
  onConfirm?: (tags: Record<string, any>) => void;
  onCancel?: () => void;
}

export const VisualTagConfirmPanel: React.FC<VisualTagConfirmPanelProps> = ({
  draftId,
  type,
  entityId,
  entityName,
  imagePath,
  onConfirm,
  onCancel
}) => {
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tags, setTags] = useState<Record<string, any>>({});
  const [confidence, setConfidence] = useState(0);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTags, setEditedTags] = useState<Record<string, any>>({});

  // 加载已有标签
  useEffect(() => {
    loadSuggestedTags();
  }, [draftId, entityId]);

  const loadSuggestedTags = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await wizardApi.getSuggestedTags(draftId);
      
      if (result.status === 'not_found') {
        // 没有标签数据，需要先分析
        setTags({});
        return;
      }

      if (type === 'character') {
        const charTag = result.character_tags.find(t => t.character_id === entityId);
        if (charTag) {
          setTags(charTag.tags);
          setConfidence(charTag.confidence);
          setEditedTags(charTag.tags);
        }
      } else {
        const sceneTag = result.scene_tags.find(t => t.scene_id === entityId);
        if (sceneTag) {
          setTags(sceneTag.tags);
          setConfidence(sceneTag.confidence);
          setEditedTags(sceneTag.tags);
        }
      }
    } catch (err: any) {
      setError(err.message || '加载标签失败');
    } finally {
      setLoading(false);
    }
  };

  // 触发图像分析
  const handleAnalyze = async () => {
    if (!imagePath) {
      setError('请先上传参考图像');
      return;
    }

    setAnalyzing(true);
    setError(null);
    try {
      const result = await wizardApi.analyzeImages({
        draft_id: draftId,
        images: [{
          image_id: `img_${entityId}`,
          image_path: imagePath,
          image_type: type,
          related_id: entityId
        }]
      });

      // 轮询任务状态
      await wizardApi.pollTaskStatus(result.task_id, {
        maxAttempts: 120,
        interval: 2000,
        onProgress: (status) => {
          console.log('分析进度:', status.progress, status.message);
        }
      });

      // 重新加载标签
      await loadSuggestedTags();
    } catch (err: any) {
      setError(err.message || '图像分析失败');
    } finally {
      setAnalyzing(false);
    }
  };

  // 确认标签
  const handleConfirm = async () => {
    try {
      const tagsToConfirm = isEditing ? editedTags : tags;
      
      const request = type === 'character' 
        ? {
            character_tags: [{
              entity_id: entityId,
              image_path: imagePath || '',
              tags: tagsToConfirm,
              confirmed: true
            }],
            scene_tags: []
          }
        : {
            character_tags: [],
            scene_tags: [{
              entity_id: entityId,
              image_path: imagePath || '',
              tags: tagsToConfirm,
              confirmed: true
            }]
          };

      const result = await wizardApi.confirmTags(draftId, request);
      
      if (result.success) {
        onConfirm?.(tagsToConfirm);
      } else {
        setError(result.error || '确认失败');
      }
    } catch (err: any) {
      setError(err.message || '确认标签失败');
    }
  };

  // 渲染角色标签
  const renderCharacterTags = () => {
    const t = isEditing ? editedTags : tags;
    const appearance = t.appearance || {};

    return (
      <div className="space-y-4">
        {/* 外观特征 */}
        <div className="space-y-2">
          <div className="text-xs font-medium text-zinc-400 flex items-center gap-1">
            <Eye size={12} />
            外观特征
          </div>
          <div className="grid grid-cols-2 gap-2">
            {['hair', 'skin', 'build', 'face', 'age_appearance'].map(key => (
              <div key={key} className="flex flex-col">
                <span className="text-xs text-zinc-500">{getAppearanceLabel(key)}</span>
                {isEditing ? (
                  <input
                    type="text"
                    value={appearance[key] || ''}
                    onChange={(e) => setEditedTags({
                      ...editedTags,
                      appearance: { ...appearance, [key]: e.target.value }
                    })}
                    className="px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-xs text-white"
                  />
                ) : (
                  <span className="text-sm text-white">{appearance[key] || '-'}</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 服装风格 */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-zinc-400">服装风格</div>
          {isEditing ? (
            <input
              type="text"
              value={t.clothing_style || ''}
              onChange={(e) => setEditedTags({ ...editedTags, clothing_style: e.target.value })}
              className="w-full px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-xs text-white"
            />
          ) : (
            <span className="text-sm text-white">{t.clothing_style || '-'}</span>
          )}
        </div>

        {/* 配色 */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-zinc-400 flex items-center gap-1">
            <Palette size={12} />
            配色
          </div>
          <div className="flex flex-wrap gap-1">
            {(t.color_palette || []).map((color: string, i: number) => (
              <span key={i} className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-300">
                {color}
              </span>
            ))}
            {(!t.color_palette || t.color_palette.length === 0) && (
              <span className="text-xs text-zinc-500">暂无配色信息</span>
            )}
          </div>
        </div>

        {/* 配饰 */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-zinc-400 flex items-center gap-1">
            <Tag size={12} />
            配饰/道具
          </div>
          <div className="flex flex-wrap gap-1">
            {(t.accessories || []).map((acc: string, i: number) => (
              <span key={i} className="px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded text-xs">
                {acc}
              </span>
            ))}
            {(!t.accessories || t.accessories.length === 0) && (
              <span className="text-xs text-zinc-500">暂无配饰信息</span>
            )}
          </div>
        </div>
      </div>
    );
  };

  // 渲染场景标签
  const renderSceneTags = () => {
    const t = isEditing ? editedTags : tags;

    return (
      <div className="space-y-4">
        {/* 基础信息 */}
        <div className="grid grid-cols-2 gap-3">
          {[
            { key: 'scene_type', label: '场景类型' },
            { key: 'time_of_day', label: '时间' },
            { key: 'lighting', label: '光线' },
            { key: 'mood', label: '氛围' }
          ].map(({ key, label }) => (
            <div key={key} className="space-y-1">
              <span className="text-xs text-zinc-500">{label}</span>
              {isEditing ? (
                <input
                  type="text"
                  value={t[key] || ''}
                  onChange={(e) => setEditedTags({ ...editedTags, [key]: e.target.value })}
                  className="w-full px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-xs text-white"
                />
              ) : (
                <span className="text-sm text-white">{t[key] || '-'}</span>
              )}
            </div>
          ))}
        </div>

        {/* 环境元素 */}
        <div className="space-y-1">
          <div className="text-xs font-medium text-zinc-400">环境元素</div>
          <div className="flex flex-wrap gap-1">
            {(t.environment || []).map((env: string, i: number) => (
              <span key={i} className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 rounded text-xs">
                {env}
              </span>
            ))}
            {(!t.environment || t.environment.length === 0) && (
              <span className="text-xs text-zinc-500">暂无环境信息</span>
            )}
          </div>
        </div>

        {/* 建筑风格 */}
        <div className="space-y-1">
          <span className="text-xs text-zinc-500">建筑风格</span>
          {isEditing ? (
            <input
              type="text"
              value={t.architecture_style || ''}
              onChange={(e) => setEditedTags({ ...editedTags, architecture_style: e.target.value })}
              className="w-full px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-xs text-white"
            />
          ) : (
            <span className="text-sm text-white">{t.architecture_style || '-'}</span>
          )}
        </div>
      </div>
    );
  };

  const getAppearanceLabel = (key: string): string => {
    const labels: Record<string, string> = {
      hair: '发型/发色',
      skin: '肤色',
      build: '体型',
      face: '面部特征',
      age_appearance: '外观年龄'
    };
    return labels[key] || key;
  };

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-xl overflow-hidden">
      {/* 头部 */}
      <div className="px-4 py-3 bg-zinc-800/50 border-b border-zinc-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Image size={16} className="text-purple-400" />
          <span className="text-sm font-medium text-white">
            {type === 'character' ? '角色' : '场景'}视觉标签 - {entityName}
          </span>
        </div>
        {confidence > 0 && (
          <span className="text-xs text-zinc-500">
            置信度: {(confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* 内容 */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="animate-spin text-zinc-500" size={24} />
            <span className="ml-2 text-sm text-zinc-500">加载中...</span>
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <AlertCircle size={16} className="text-red-400" />
            <span className="text-sm text-red-400">{error}</span>
          </div>
        ) : Object.keys(tags).length === 0 ? (
          <div className="text-center py-8">
            <Image className="mx-auto text-zinc-700 mb-3" size={40} />
            <p className="text-sm text-zinc-500 mb-4">暂无视觉标签</p>
            {imagePath && (
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="px-4 py-2 bg-purple-500 hover:bg-purple-400 text-white text-sm font-medium rounded-lg disabled:opacity-50 flex items-center gap-2 mx-auto"
              >
                {analyzing ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    分析中...
                  </>
                ) : (
                  <>
                    <Eye size={14} />
                    AI 分析图像
                  </>
                )}
              </button>
            )}
          </div>
        ) : (
          <>
            {type === 'character' ? renderCharacterTags() : renderSceneTags()}

            {/* 摘要 */}
            {(tags.summary || editedTags.summary) && (
              <div className="mt-4 p-3 bg-zinc-800/50 rounded-lg">
                <div className="text-xs text-zinc-500 mb-1">AI 摘要</div>
                <p className="text-sm text-zinc-300">
                  {isEditing ? editedTags.summary : tags.summary}
                </p>
              </div>
            )}
          </>
        )}
      </div>

      {/* 底部操作 */}
      {Object.keys(tags).length > 0 && (
        <div className="px-4 py-3 bg-zinc-800/30 border-t border-zinc-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                if (isEditing) {
                  setEditedTags(tags);
                }
                setIsEditing(!isEditing);
              }}
              className="px-3 py-1.5 text-xs text-zinc-400 hover:text-white flex items-center gap-1"
            >
              <Edit2 size={12} />
              {isEditing ? '取消编辑' : '编辑标签'}
            </button>
            <button
              onClick={handleAnalyze}
              disabled={analyzing || !imagePath}
              className="px-3 py-1.5 text-xs text-zinc-400 hover:text-purple-400 flex items-center gap-1 disabled:opacity-50"
            >
              <RefreshCw size={12} className={analyzing ? 'animate-spin' : ''} />
              重新分析
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onCancel}
              className="px-3 py-1.5 text-xs text-zinc-400 hover:text-white"
            >
              取消
            </button>
            <button
              onClick={handleConfirm}
              className="px-4 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-white text-xs font-medium rounded-lg flex items-center gap-1"
            >
              <Check size={12} />
              确认标签
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VisualTagConfirmPanel;
