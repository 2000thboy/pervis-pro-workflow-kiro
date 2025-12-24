import React, { useState, useCallback, useEffect } from 'react';
import { 
  X, 
  Download, 
  Trash2, 
  Edit3, 
  ZoomIn, 
  ZoomOut, 
  RotateCw, 
  Share2,
  Tag,
  Palette,
  Info,
  Search,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';

export interface ImageAsset {
  id: string;
  filename: string;
  description?: string;
  thumbnail_url?: string;
  original_url: string;
  tags?: Record<string, string[]>;
  color_palette?: Record<string, any>;
  metadata: {
    width: number;
    height: number;
    file_size: number;
    mime_type?: string;
  };
  processing_status: string;
  created_at: string;
}

export interface ImagePreviewProps {
  image: ImageAsset | null;
  images?: ImageAsset[];
  onClose: () => void;
  onDelete?: (imageId: string) => void;
  onUpdate?: (imageId: string, updates: Partial<ImageAsset>) => void;
  onFindSimilar?: (image: ImageAsset) => void;
  onNavigate?: (direction: 'prev' | 'next') => void;
  className?: string;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  image,
  images = [],
  onClose,
  onDelete,
  onUpdate,
  onFindSimilar,
  onNavigate,
  className = ''
}) => {
  const [zoom, setZoom] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [showInfo, setShowInfo] = useState(true);
  const [editingDescription, setEditingDescription] = useState(false);
  const [description, setDescription] = useState('');
  const [editingTags, setEditingTags] = useState(false);
  const [newTag, setNewTag] = useState('');

  // 重置状态
  useEffect(() => {
    if (image) {
      setZoom(1);
      setRotation(0);
      setDescription(image.description || '');
    }
  }, [image]);

  // 键盘导航
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!image) return;

      switch (e.key) {
        case 'Escape':
          onClose();
          break;
        case 'ArrowLeft':
          onNavigate?.('prev');
          break;
        case 'ArrowRight':
          onNavigate?.('next');
          break;
        case '+':
        case '=':
          setZoom(prev => Math.min(prev * 1.2, 5));
          break;
        case '-':
          setZoom(prev => Math.max(prev / 1.2, 0.1));
          break;
        case '0':
          setZoom(1);
          setRotation(0);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [image, onClose, onNavigate]);

  // 保存描述
  const saveDescription = useCallback(async () => {
    if (!image || !onUpdate) return;

    try {
      await onUpdate(image.id, { description });
      setEditingDescription(false);
    } catch (error) {
      console.error('Failed to update description:', error);
    }
  }, [image, description, onUpdate]);

  // 添加标签
  const addTag = useCallback(async (category: string, tag: string) => {
    if (!image || !onUpdate || !tag.trim()) return;

    const updatedTags = { ...image.tags };
    if (!updatedTags[category]) {
      updatedTags[category] = [];
    }
    if (!updatedTags[category].includes(tag.trim())) {
      updatedTags[category].push(tag.trim());
    }

    try {
      await onUpdate(image.id, { tags: updatedTags });
      setNewTag('');
    } catch (error) {
      console.error('Failed to add tag:', error);
    }
  }, [image, onUpdate]);

  // 移除标签
  const removeTag = useCallback(async (category: string, tag: string) => {
    if (!image || !onUpdate) return;

    const updatedTags = { ...image.tags };
    if (updatedTags[category]) {
      updatedTags[category] = updatedTags[category].filter(t => t !== tag);
      if (updatedTags[category].length === 0) {
        delete updatedTags[category];
      }
    }

    try {
      await onUpdate(image.id, { tags: updatedTags });
    } catch (error) {
      console.error('Failed to remove tag:', error);
    }
  }, [image, onUpdate]);

  // 下载图片
  const downloadImage = useCallback(() => {
    if (!image) return;

    const link = document.createElement('a');
    link.href = image.original_url;
    link.download = image.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [image]);

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!image) return null;

  const currentIndex = images.findIndex(img => img.id === image.id);
  const canNavigate = images.length > 1;

  return (
    <div className={`fixed inset-0 z-50 bg-black/90 backdrop-blur-sm ${className}`}>
      <div className="flex h-full">
        {/* 主图片区域 */}
        <div className="flex-1 flex items-center justify-center relative">
          {/* 导航按钮 */}
          {canNavigate && (
            <>
              <button
                onClick={() => onNavigate?.('prev')}
                className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center text-white transition-colors z-10"
                disabled={currentIndex <= 0}
              >
                <ChevronLeft size={24} />
              </button>
              
              <button
                onClick={() => onNavigate?.('next')}
                className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center text-white transition-colors z-10"
                disabled={currentIndex >= images.length - 1}
              >
                <ChevronRight size={24} />
              </button>
            </>
          )}

          {/* 图片 */}
          <div className="max-w-full max-h-full overflow-hidden">
            <img
              src={image.original_url}
              alt={image.filename}
              className="max-w-full max-h-full object-contain transition-transform duration-300"
              style={{
                transform: `scale(${zoom}) rotate(${rotation}deg)`
              }}
            />
          </div>

          {/* 顶部工具栏 */}
          <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                icon={ZoomOut}
                onClick={() => setZoom(prev => Math.max(prev / 1.2, 0.1))}
                className="bg-black/50 hover:bg-black/70"
              />
              
              <span className="text-white text-sm bg-black/50 px-2 py-1 rounded">
                {Math.round(zoom * 100)}%
              </span>
              
              <Button
                variant="ghost"
                size="sm"
                icon={ZoomIn}
                onClick={() => setZoom(prev => Math.min(prev * 1.2, 5))}
                className="bg-black/50 hover:bg-black/70"
              />
              
              <Button
                variant="ghost"
                size="sm"
                icon={RotateCw}
                onClick={() => setRotation(prev => prev + 90)}
                className="bg-black/50 hover:bg-black/70"
              />
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                icon={Info}
                onClick={() => setShowInfo(!showInfo)}
                className="bg-black/50 hover:bg-black/70"
              />
              
              <Button
                variant="ghost"
                size="sm"
                icon={X}
                onClick={onClose}
                className="bg-black/50 hover:bg-black/70"
              />
            </div>
          </div>

          {/* 底部信息栏 */}
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-black/70 backdrop-blur-sm rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-semibold text-lg mb-1">
                    {image.filename}
                  </h3>
                  <p className="text-zinc-300 text-sm">
                    {image.metadata.width} × {image.metadata.height} • {formatFileSize(image.metadata.file_size)}
                  </p>
                  {canNavigate && (
                    <p className="text-zinc-400 text-xs mt-1">
                      {currentIndex + 1} / {images.length}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Search}
                    onClick={() => onFindSimilar?.(image)}
                  >
                    相似图片
                  </Button>
                  
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Download}
                    onClick={downloadImage}
                  >
                    下载
                  </Button>
                  
                  {onDelete && (
                    <Button
                      variant="danger"
                      size="sm"
                      icon={Trash2}
                      onClick={() => onDelete(image.id)}
                    >
                      删除
                    </Button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 侧边信息面板 */}
        {showInfo && (
          <div className="w-80 bg-zinc-900 border-l border-zinc-800 overflow-y-auto">
            <div className="p-4 space-y-4">
              {/* 基本信息 */}
              <Card title="基本信息" padding="sm">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-zinc-400">文件名:</span>
                    <span className="text-white">{image.filename}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">尺寸:</span>
                    <span className="text-white">{image.metadata.width} × {image.metadata.height}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">大小:</span>
                    <span className="text-white">{formatFileSize(image.metadata.file_size)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">格式:</span>
                    <span className="text-white">{image.metadata.mime_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-zinc-400">创建时间:</span>
                    <span className="text-white">{formatDate(image.created_at)}</span>
                  </div>
                </div>
              </Card>

              {/* 描述 */}
              <Card title="描述" padding="sm">
                {editingDescription ? (
                  <div className="space-y-2">
                    <textarea
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      className="w-full h-20 bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-white text-sm resize-none"
                      placeholder="添加图片描述..."
                    />
                    <div className="flex gap-2">
                      <Button
                        variant="primary"
                        size="xs"
                        onClick={saveDescription}
                      >
                        保存
                      </Button>
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() => {
                          setEditingDescription(false);
                          setDescription(image.description || '');
                        }}
                      >
                        取消
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="text-zinc-300 text-sm mb-2">
                      {image.description || '暂无描述'}
                    </p>
                    <Button
                      variant="ghost"
                      size="xs"
                      icon={Edit3}
                      onClick={() => setEditingDescription(true)}
                    >
                      编辑
                    </Button>
                  </div>
                )}
              </Card>

              {/* 标签 */}
              <Card title="标签" padding="sm">
                <div className="space-y-3">
                  {image.tags && Object.entries(image.tags).map(([category, tags]) => (
                    <div key={category}>
                      <h4 className="text-xs text-zinc-400 uppercase mb-2">{category}</h4>
                      <div className="flex flex-wrap gap-1">
                        {tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center gap-1 px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs"
                          >
                            {tag}
                            {onUpdate && (
                              <button
                                onClick={() => removeTag(category, tag)}
                                className="hover:text-amber-300"
                              >
                                <X size={10} />
                              </button>
                            )}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}

                  {onUpdate && (
                    <div className="pt-2 border-t border-zinc-800">
                      <div className="flex gap-2">
                        <Input
                          placeholder="添加标签..."
                          value={newTag}
                          onChange={(e) => setNewTag(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              addTag('custom', newTag);
                            }
                          }}
                          size="sm"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={Tag}
                          onClick={() => addTag('custom', newTag)}
                          disabled={!newTag.trim()}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              {/* 色彩信息 */}
              {image.color_palette && (
                <Card title="色彩分析" padding="sm">
                  <div className="space-y-3">
                    {image.color_palette.palette && (
                      <div>
                        <h4 className="text-xs text-zinc-400 mb-2">调色板</h4>
                        <div className="flex gap-2">
                          {image.color_palette.palette.slice(0, 5).map((color: any, index: number) => (
                            <div
                              key={index}
                              className="w-8 h-8 rounded border border-zinc-700"
                              style={{ backgroundColor: color.hex }}
                              title={`${color.hex} (${color.percentage?.toFixed(1)}%)`}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {image.color_palette.tone && (
                      <div className="text-sm">
                        <span className="text-zinc-400">主色调: </span>
                        <span className="text-white">{image.color_palette.tone}</span>
                      </div>
                    )}

                    {image.color_palette.brightness && (
                      <div className="text-sm">
                        <span className="text-zinc-400">明度: </span>
                        <span className="text-white">{image.color_palette.brightness}</span>
                      </div>
                    )}
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImagePreview;