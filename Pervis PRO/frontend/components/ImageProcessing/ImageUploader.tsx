import React, { useState, useCallback, useRef } from 'react';
import { Upload, X, Image as ImageIcon, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';

export interface ImageFile {
  id: string;
  file: File;
  preview: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

export interface ImageUploaderProps {
  projectId: string;
  onUploadComplete?: (images: any[]) => void;
  onUploadProgress?: (progress: Record<string, number>) => void;
  maxFiles?: number;
  maxSizePerFile?: number; // MB
  acceptedTypes?: string[];
  className?: string;
}

const ACCEPTED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  projectId,
  onUploadComplete,
  onUploadProgress,
  maxFiles = 10,
  maxSizePerFile = 50,
  acceptedTypes = ACCEPTED_TYPES,
  className = ''
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [images, setImages] = useState<ImageFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 验证文件
  const validateFile = (file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return `不支持的文件格式: ${file.type}`;
    }
    
    if (file.size > maxSizePerFile * 1024 * 1024) {
      return `文件过大: ${(file.size / 1024 / 1024).toFixed(1)}MB (最大${maxSizePerFile}MB)`;
    }
    
    return null;
  };

  // 处理文件选择
  const handleFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    
    if (images.length + fileArray.length > maxFiles) {
      alert(`最多只能上传 ${maxFiles} 个文件`);
      return;
    }

    const newImages: ImageFile[] = [];
    
    fileArray.forEach((file) => {
      const error = validateFile(file);
      
      const imageFile: ImageFile = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        preview: URL.createObjectURL(file),
        status: error ? 'error' : 'pending',
        progress: 0,
        error
      };
      
      newImages.push(imageFile);
    });

    setImages(prev => [...prev, ...newImages]);
  }, [images.length, maxFiles, maxSizePerFile, acceptedTypes]);

  // 拖拽处理
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  // 文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  // 移除图片
  const removeImage = useCallback((id: string) => {
    setImages(prev => {
      const updated = prev.filter(img => img.id !== id);
      // 清理预览URL
      const removed = prev.find(img => img.id === id);
      if (removed) {
        URL.revokeObjectURL(removed.preview);
      }
      return updated;
    });
  }, []);

  // 上传图片
  const uploadImages = useCallback(async () => {
    const pendingImages = images.filter(img => img.status === 'pending');
    
    if (pendingImages.length === 0) {
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('project_id', projectId);
      
      pendingImages.forEach(img => {
        formData.append('files', img.file);
      });

      // 更新状态为上传中
      setImages(prev => prev.map(img => 
        pendingImages.some(p => p.id === img.id) 
          ? { ...img, status: 'uploading' as const, progress: 0 }
          : img
      ));

      const response = await fetch('/api/images/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`);
      }

      const results = await response.json();
      
      // 更新上传结果
      setImages(prev => prev.map(img => {
        const pendingIndex = pendingImages.findIndex(p => p.id === img.id);
        if (pendingIndex >= 0 && results[pendingIndex]) {
          const result = results[pendingIndex];
          return {
            ...img,
            status: result.status === 'uploaded' ? 'success' as const : 'error' as const,
            progress: 100,
            error: result.error
          };
        }
        return img;
      }));

      // 通知上传完成
      const successResults = results.filter((r: any) => r.status === 'uploaded');
      if (successResults.length > 0) {
        onUploadComplete?.(successResults);
      }

    } catch (error) {
      console.error('Upload failed:', error);
      
      // 更新错误状态
      setImages(prev => prev.map(img => 
        pendingImages.some(p => p.id === img.id)
          ? { ...img, status: 'error' as const, error: String(error) }
          : img
      ));
    } finally {
      setUploading(false);
    }
  }, [images, projectId, onUploadComplete]);

  // 清空所有
  const clearAll = useCallback(() => {
    images.forEach(img => URL.revokeObjectURL(img.preview));
    setImages([]);
  }, [images]);

  const pendingCount = images.filter(img => img.status === 'pending').length;
  const successCount = images.filter(img => img.status === 'success').length;
  const errorCount = images.filter(img => img.status === 'error').length;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 上传区域 */}
      <Card
        className={`
          relative border-2 border-dashed transition-all duration-300
          ${dragActive 
            ? 'border-amber-500 bg-amber-500/5 scale-[1.02]' 
            : 'border-zinc-700 hover:border-zinc-600'
          }
          ${images.length > 0 ? 'border-solid' : ''}
        `}
        padding="lg"
        onDragEnter={handleDragIn}
        onDragLeave={handleDragOut}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <div className={`
            mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4
            ${dragActive ? 'bg-amber-500/20 text-amber-400' : 'bg-zinc-800 text-zinc-400'}
            transition-all duration-300
          `}>
            <Upload size={24} />
          </div>
          
          <h3 className="text-lg font-semibold text-white mb-2">
            {dragActive ? '释放文件开始上传' : '上传图片'}
          </h3>
          
          <p className="text-zinc-400 mb-4">
            拖拽图片到此处，或点击选择文件
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Button
              variant="primary"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              icon={ImageIcon}
            >
              选择图片
            </Button>
            
            {images.length > 0 && (
              <Button
                variant="ghost"
                onClick={clearAll}
                disabled={uploading}
                icon={X}
                size="sm"
              >
                清空所有
              </Button>
            )}
          </div>
          
          <p className="text-xs text-zinc-500 mt-3">
            支持 JPG, PNG, WebP, GIF 格式，单个文件最大 {maxSizePerFile}MB，最多 {maxFiles} 个文件
          </p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />
      </Card>

      {/* 图片预览列表 */}
      {images.length > 0 && (
        <Card title="图片预览" padding="md">
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {images.map((image) => (
              <div key={image.id} className="relative group">
                <div className="aspect-square rounded-lg overflow-hidden bg-zinc-800 border border-zinc-700">
                  <img
                    src={image.preview}
                    alt={image.file.name}
                    className="w-full h-full object-cover"
                  />
                  
                  {/* 状态遮罩 */}
                  <div className={`
                    absolute inset-0 flex items-center justify-center
                    ${image.status === 'uploading' ? 'bg-black/50' : ''}
                    ${image.status === 'success' ? 'bg-emerald-500/20' : ''}
                    ${image.status === 'error' ? 'bg-red-500/20' : ''}
                  `}>
                    {image.status === 'uploading' && (
                      <Loader2 size={24} className="text-white animate-spin" />
                    )}
                    {image.status === 'success' && (
                      <CheckCircle size={24} className="text-emerald-400" />
                    )}
                    {image.status === 'error' && (
                      <AlertCircle size={24} className="text-red-400" />
                    )}
                  </div>
                  
                  {/* 删除按钮 */}
                  <button
                    onClick={() => removeImage(image.id)}
                    className="
                      absolute top-2 right-2 w-6 h-6 rounded-full
                      bg-black/50 hover:bg-black/70 text-white
                      flex items-center justify-center
                      opacity-0 group-hover:opacity-100 transition-opacity
                    "
                  >
                    <X size={14} />
                  </button>
                </div>
                
                {/* 文件信息 */}
                <div className="mt-2">
                  <p className="text-xs text-zinc-300 truncate" title={image.file.name}>
                    {image.file.name}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {(image.file.size / 1024 / 1024).toFixed(1)} MB
                  </p>
                  
                  {image.error && (
                    <p className="text-xs text-red-400 mt-1" title={image.error}>
                      {image.error}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {/* 上传按钮和统计 */}
          <div className="flex items-center justify-between mt-6 pt-4 border-t border-zinc-800">
            <div className="text-sm text-zinc-400">
              {images.length > 0 && (
                <span>
                  总计: {images.length} 个文件
                  {successCount > 0 && <span className="text-emerald-400 ml-2">✓ {successCount}</span>}
                  {errorCount > 0 && <span className="text-red-400 ml-2">✗ {errorCount}</span>}
                </span>
              )}
            </div>
            
            {pendingCount > 0 && (
              <Button
                variant="primary"
                onClick={uploadImages}
                loading={uploading}
                icon={Upload}
              >
                上传 {pendingCount} 个文件
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
};

export default ImageUploader;