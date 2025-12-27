/**
 * 向导步骤5 - 参考资料
 * 支持批量文件上传，显示 Art_Agent 分类结果
 */

import React, { useState, useCallback } from 'react';
import { 
  Image, 
  Upload, 
  Trash2, 
  Tag,
  Loader2,
  CheckCircle,
  AlertCircle,
  FolderOpen,
  User,
  MapPin,
  FileQuestion
} from 'lucide-react';
import { useWizard } from './WizardContext';
import { ReferenceAsset } from './types';
import { wizardApi } from './api';

export const WizardStep5_References: React.FC = () => {
  const { state, addReference, removeReference, updateReference, setAgentStatus } = useWizard();
  const { references } = state;
  
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  // 分类图标
  const CategoryIcon = ({ category }: { category: string }) => {
    switch (category) {
      case 'character':
        return <User size={14} className="text-blue-400" />;
      case 'scene':
        return <MapPin size={14} className="text-green-400" />;
      default:
        return <FileQuestion size={14} className="text-zinc-400" />;
    }
  };

  // 分类标签
  const categoryLabels: Record<string, string> = {
    character: '角色参考',
    scene: '场景参考',
    reference: '其他参考'
  };

  // 处理文件上传
  const handleFileUpload = useCallback(async (files: FileList) => {
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const validFiles = Array.from(files).filter(f => validTypes.includes(f.type));

    if (validFiles.length === 0) {
      alert('请上传图片文件 (JPG, PNG, GIF, WebP)');
      return;
    }

    // 添加到列表（pending 状态）
    const newAssets: ReferenceAsset[] = validFiles.map(file => ({
      id: `ref_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      path: URL.createObjectURL(file),
      filename: file.name,
      category: 'reference',
      confidence: 0,
      tags: [],
      thumbnailUrl: URL.createObjectURL(file),
      uploadStatus: 'pending'
    }));

    newAssets.forEach(asset => addReference(asset));

    // 调用 Art_Agent 分类
    setIsProcessing(true);
    setAgentStatus('Art_Agent', { status: 'working', message: '正在分类参考资料...', progress: 0 });

    try {
      const result = await wizardApi.processAssets({
        project_id: state.projectId || 'temp',
        asset_paths: validFiles.map(f => f.name),
        auto_classify: true
      });

      // 更新分类结果
      result.results.forEach((r, i) => {
        if (newAssets[i]) {
          updateReference(newAssets[i].id, {
            category: r.category as 'character' | 'scene' | 'reference',
            confidence: r.confidence,
            tags: r.tags,
            uploadStatus: r.error ? 'error' : 'done',
            error: r.error
          });
        }
      });

      setAgentStatus('Art_Agent', { 
        status: 'completed', 
        message: `已分类 ${result.success_count} 个文件`, 
        progress: 100 
      });
    } catch (error) {
      console.error('分类失败:', error);
      newAssets.forEach(asset => {
        updateReference(asset.id, { uploadStatus: 'done', category: 'reference' });
      });
      setAgentStatus('Art_Agent', { status: 'failed', message: '分类失败', progress: 0 });
    } finally {
      setIsProcessing(false);
    }
  }, [addReference, updateReference, setAgentStatus, state.projectId]);

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  // 手动更改分类
  const handleCategoryChange = (id: string, category: 'character' | 'scene' | 'reference') => {
    updateReference(id, { category });
  };

  // 按分类分组
  const groupedReferences = {
    character: references.filter(r => r.category === 'character'),
    scene: references.filter(r => r.category === 'scene'),
    reference: references.filter(r => r.category === 'reference')
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 上传区域 */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? 'border-amber-500 bg-amber-500/10'
            : 'border-zinc-700 hover:border-zinc-600'
        }`}
      >
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <Upload className={`mx-auto mb-4 ${isDragging ? 'text-amber-500' : 'text-zinc-500'}`} size={40} />
        <div className="text-zinc-300 mb-2">拖拽图片到此处，或点击上传</div>
        <div className="text-xs text-zinc-500">支持 JPG、PNG、GIF、WebP 格式，可批量上传</div>
      </div>

      {/* 处理状态 */}
      {isProcessing && (
        <div className="flex items-center gap-3 p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <Loader2 className="text-amber-500 animate-spin" size={20} />
          <span className="text-sm text-amber-400">Art_Agent 正在分析和分类图片...</span>
        </div>
      )}

      {/* 分类展示 */}
      {references.length > 0 && (
        <div className="space-y-6">
          {/* 角色参考 */}
          {groupedReferences.character.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-3">
                <User size={16} className="text-blue-400" />
                角色参考 ({groupedReferences.character.length})
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {groupedReferences.character.map(asset => (
                  <AssetCard
                    key={asset.id}
                    asset={asset}
                    onRemove={() => removeReference(asset.id)}
                    onCategoryChange={(cat) => handleCategoryChange(asset.id, cat)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 场景参考 */}
          {groupedReferences.scene.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-3">
                <MapPin size={16} className="text-green-400" />
                场景参考 ({groupedReferences.scene.length})
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {groupedReferences.scene.map(asset => (
                  <AssetCard
                    key={asset.id}
                    asset={asset}
                    onRemove={() => removeReference(asset.id)}
                    onCategoryChange={(cat) => handleCategoryChange(asset.id, cat)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 其他参考 */}
          {groupedReferences.reference.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 text-sm font-medium text-zinc-300 mb-3">
                <FolderOpen size={16} className="text-zinc-400" />
                其他参考 ({groupedReferences.reference.length})
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {groupedReferences.reference.map(asset => (
                  <AssetCard
                    key={asset.id}
                    asset={asset}
                    onRemove={() => removeReference(asset.id)}
                    onCategoryChange={(cat) => handleCategoryChange(asset.id, cat)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 空状态 */}
      {references.length === 0 && (
        <div className="text-center py-12">
          <Image className="mx-auto text-zinc-700 mb-4" size={48} />
          <div className="text-zinc-500 mb-2">暂无参考资料</div>
          <div className="text-xs text-zinc-600">上传角色设计、场景参考等图片，AI 会自动分类</div>
        </div>
      )}

      {/* 提示 */}
      <div className="p-4 bg-zinc-900/30 border border-zinc-800 rounded-xl">
        <div className="text-sm text-zinc-400 mb-2">💡 提示</div>
        <ul className="text-xs text-zinc-500 space-y-1">
          <li>• Art_Agent 会自动识别图片内容并分类</li>
          <li>• 可以手动调整分类，点击图片下方的分类标签</li>
          <li>• 参考资料可选，跳过此步骤也可以创建项目</li>
        </ul>
      </div>
    </div>
  );
};

// 素材卡片组件
const AssetCard: React.FC<{
  asset: ReferenceAsset;
  onRemove: () => void;
  onCategoryChange: (category: 'character' | 'scene' | 'reference') => void;
}> = ({ asset, onRemove, onCategoryChange }) => {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <div className="group relative bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
      {/* 图片 */}
      <div className="aspect-square relative">
        <img
          src={asset.thumbnailUrl || asset.path}
          alt={asset.filename}
          className="w-full h-full object-cover"
        />
        
        {/* 状态覆盖 */}
        {asset.uploadStatus === 'pending' && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <Loader2 className="text-white animate-spin" size={24} />
          </div>
        )}
        
        {asset.uploadStatus === 'error' && (
          <div className="absolute inset-0 bg-red-500/20 flex items-center justify-center">
            <AlertCircle className="text-red-400" size={24} />
          </div>
        )}

        {/* 删除按钮 */}
        <button
          onClick={onRemove}
          className="absolute top-2 right-2 p-1.5 bg-black/50 hover:bg-red-500/80 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash2 size={12} />
        </button>

        {/* 置信度 */}
        {asset.confidence > 0 && (
          <div className="absolute bottom-2 right-2 px-1.5 py-0.5 bg-black/50 rounded text-[10px] text-white">
            {Math.round(asset.confidence * 100)}%
          </div>
        )}
      </div>

      {/* 信息 */}
      <div className="p-2">
        <div className="text-xs text-zinc-400 truncate mb-1">{asset.filename}</div>
        
        {/* 分类选择 */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className={`w-full px-2 py-1 rounded text-xs flex items-center gap-1 ${
              asset.category === 'character' ? 'bg-blue-500/20 text-blue-400' :
              asset.category === 'scene' ? 'bg-green-500/20 text-green-400' :
              'bg-zinc-800 text-zinc-400'
            }`}
          >
            {asset.category === 'character' && <User size={12} />}
            {asset.category === 'scene' && <MapPin size={12} />}
            {asset.category === 'reference' && <Tag size={12} />}
            <span>
              {asset.category === 'character' ? '角色' :
               asset.category === 'scene' ? '场景' : '其他'}
            </span>
          </button>

          {showMenu && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-zinc-800 border border-zinc-700 rounded-lg overflow-hidden z-10">
              {(['character', 'scene', 'reference'] as const).map(cat => (
                <button
                  key={cat}
                  onClick={() => {
                    onCategoryChange(cat);
                    setShowMenu(false);
                  }}
                  className={`w-full px-2 py-1.5 text-xs text-left hover:bg-zinc-700 flex items-center gap-2 ${
                    asset.category === cat ? 'text-amber-400' : 'text-zinc-300'
                  }`}
                >
                  {cat === 'character' && <User size={12} />}
                  {cat === 'scene' && <MapPin size={12} />}
                  {cat === 'reference' && <Tag size={12} />}
                  {cat === 'character' ? '角色参考' :
                   cat === 'scene' ? '场景参考' : '其他参考'}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 标签 */}
        {asset.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {asset.tags.slice(0, 3).map((tag, i) => (
              <span key={i} className="px-1 py-0.5 bg-zinc-800 rounded text-[10px] text-zinc-500">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WizardStep5_References;
