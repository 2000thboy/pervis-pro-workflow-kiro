import React, { useState, useCallback, useEffect } from 'react';
import { 
  Upload, 
  Search, 
  Grid, 
  Plus,
  RefreshCw,
  Settings,
  Filter
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import ImageUploader from './ImageUploader';
import ImageGallery, { ImageAsset } from './ImageGallery';
import ImageSearch, { SearchResult } from './ImageSearch';
import ImagePreview from './ImagePreview';

export interface ImageManagerProps {
  projectId: string;
  className?: string;
}

type ViewMode = 'gallery' | 'upload' | 'search';

export const ImageManager: React.FC<ImageManagerProps> = ({
  projectId,
  className = ''
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('gallery');
  const [images, setImages] = useState<ImageAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedImage, setSelectedImage] = useState<ImageAsset | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [showPreview, setShowPreview] = useState(false);

  // 加载图片列表
  const loadImages = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/images/project/${projectId}`);
      if (!response.ok) {
        throw new Error(`Failed to load images: ${response.statusText}`);
      }
      
      const data = await response.json();
      setImages(data.images || []);
    } catch (error) {
      console.error('Failed to load images:', error);
      alert(`加载图片失败: ${error}`);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // 初始加载
  useEffect(() => {
    loadImages();
  }, [loadImages]);

  // 处理上传完成
  const handleUploadComplete = useCallback((uploadedImages: any[]) => {
    // 刷新图片列表
    loadImages();
    
    // 切换到图片库视图
    setViewMode('gallery');
    
    console.log('Upload completed:', uploadedImages);
  }, [loadImages]);

  // 处理图片选择
  const handleImageSelect = useCallback((image: ImageAsset) => {
    setSelectedImage(image);
    setShowPreview(true);
  }, []);

  // 处理图片删除
  const handleImageDelete = useCallback(async (imageId: string) => {
    if (!confirm('确定要删除这张图片吗？')) {
      return;
    }

    try {
      const response = await fetch(`/api/images/${imageId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`Failed to delete image: ${response.statusText}`);
      }

      // 从列表中移除
      setImages(prev => prev.filter(img => img.id !== imageId));
      
      // 如果当前预览的是被删除的图片，关闭预览
      if (selectedImage?.id === imageId) {
        setShowPreview(false);
        setSelectedImage(null);
      }

      console.log('Image deleted:', imageId);
    } catch (error) {
      console.error('Failed to delete image:', error);
      alert(`删除失败: ${error}`);
    }
  }, [selectedImage]);

  // 处理批量删除
  const handleImagesDelete = useCallback(async (imageIds: string[]) => {
    if (!confirm(`确定要删除这 ${imageIds.length} 张图片吗？`)) {
      return;
    }

    try {
      const deletePromises = imageIds.map(id => 
        fetch(`/api/images/${id}`, { method: 'DELETE' })
      );

      const results = await Promise.allSettled(deletePromises);
      
      // 检查结果
      const failed = results.filter(result => result.status === 'rejected').length;
      if (failed > 0) {
        alert(`${failed} 张图片删除失败`);
      }

      // 刷新列表
      loadImages();
      
      console.log('Batch delete completed:', imageIds);
    } catch (error) {
      console.error('Failed to delete images:', error);
      alert(`批量删除失败: ${error}`);
    }
  }, [loadImages]);

  // 处理图片更新
  const handleImageUpdate = useCallback(async (imageId: string, updates: Partial<ImageAsset>) => {
    try {
      // 这里应该调用更新API，目前先本地更新
      setImages(prev => prev.map(img => 
        img.id === imageId ? { ...img, ...updates } : img
      ));

      if (selectedImage?.id === imageId) {
        setSelectedImage(prev => prev ? { ...prev, ...updates } : null);
      }

      console.log('Image updated:', imageId, updates);
    } catch (error) {
      console.error('Failed to update image:', error);
      alert(`更新失败: ${error}`);
    }
  }, [selectedImage]);

  // 处理搜索结果
  const handleSearchResults = useCallback((results: SearchResult[]) => {
    setSearchResults(results);
  }, []);

  // 处理搜索结果选择
  const handleSearchResultSelect = useCallback((result: SearchResult) => {
    // 将搜索结果转换为ImageAsset格式
    const imageAsset: ImageAsset = {
      id: result.id,
      filename: result.filename,
      description: result.description,
      thumbnail_url: result.thumbnail_url,
      original_url: result.original_url,
      tags: result.tags,
      color_palette: result.color_palette,
      metadata: result.metadata,
      processing_status: 'completed',
      created_at: new Date().toISOString()
    };

    setSelectedImage(imageAsset);
    setShowPreview(true);
  }, []);

  // 查找相似图片
  const handleFindSimilar = useCallback(async (image: ImageAsset) => {
    try {
      // 创建临时文件用于搜索
      const response = await fetch(image.original_url);
      const blob = await response.blob();
      const file = new File([blob], image.filename, { type: blob.type });

      const formData = new FormData();
      formData.append('image', file);
      formData.append('project_id', projectId);
      formData.append('limit', '10');

      const searchResponse = await fetch('/api/images/similar', {
        method: 'POST',
        body: formData
      });

      if (!searchResponse.ok) {
        throw new Error(`Search failed: ${searchResponse.statusText}`);
      }

      const results = await searchResponse.json();
      setSearchResults(results);
      setViewMode('search');
      
      console.log('Similar images found:', results);
    } catch (error) {
      console.error('Failed to find similar images:', error);
      alert(`查找相似图片失败: ${error}`);
    }
  }, [projectId]);

  // 预览导航
  const handlePreviewNavigate = useCallback((direction: 'prev' | 'next') => {
    if (!selectedImage) return;

    const currentIndex = images.findIndex(img => img.id === selectedImage.id);
    let newIndex;

    if (direction === 'prev') {
      newIndex = currentIndex > 0 ? currentIndex - 1 : images.length - 1;
    } else {
      newIndex = currentIndex < images.length - 1 ? currentIndex + 1 : 0;
    }

    setSelectedImage(images[newIndex]);
  }, [selectedImage, images]);

  // 统计信息
  const stats = {
    total: images.length,
    completed: images.filter(img => img.processing_status === 'completed').length,
    processing: images.filter(img => img.processing_status === 'processing').length,
    failed: images.filter(img => img.processing_status === 'failed').length
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 头部工具栏 */}
      <Card padding="md">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-white mb-2">图片管理</h2>
            <div className="flex items-center gap-4 text-sm text-zinc-400">
              <span>总计: {stats.total}</span>
              <span className="text-emerald-400">已完成: {stats.completed}</span>
              {stats.processing > 0 && (
                <span className="text-amber-400">处理中: {stats.processing}</span>
              )}
              {stats.failed > 0 && (
                <span className="text-red-400">失败: {stats.failed}</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* 视图切换 */}
            <div className="flex rounded-lg border border-zinc-700 overflow-hidden">
              <button
                onClick={() => setViewMode('gallery')}
                className={`
                  flex items-center gap-2 px-4 py-2 text-sm transition-colors
                  ${viewMode === 'gallery' 
                    ? 'bg-amber-500 text-black' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                  }
                `}
              >
                <Grid size={16} />
                图片库
              </button>
              
              <button
                onClick={() => setViewMode('upload')}
                className={`
                  flex items-center gap-2 px-4 py-2 text-sm transition-colors
                  ${viewMode === 'upload' 
                    ? 'bg-amber-500 text-black' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                  }
                `}
              >
                <Upload size={16} />
                上传
              </button>
              
              <button
                onClick={() => setViewMode('search')}
                className={`
                  flex items-center gap-2 px-4 py-2 text-sm transition-colors
                  ${viewMode === 'search' 
                    ? 'bg-amber-500 text-black' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                  }
                `}
              >
                <Search size={16} />
                搜索
              </button>
            </div>

            {/* 刷新按钮 */}
            <Button
              variant="ghost"
              size="sm"
              icon={RefreshCw}
              onClick={loadImages}
              loading={loading}
            >
              刷新
            </Button>
          </div>
        </div>
      </Card>

      {/* 主内容区域 */}
      <div className="min-h-[600px]">
        {viewMode === 'gallery' && (
          <ImageGallery
            projectId={projectId}
            images={images}
            loading={loading}
            onImageSelect={handleImageSelect}
            onImageDelete={handleImageDelete}
            onImagesDelete={handleImagesDelete}
            onRefresh={loadImages}
          />
        )}

        {viewMode === 'upload' && (
          <ImageUploader
            projectId={projectId}
            onUploadComplete={handleUploadComplete}
            maxFiles={20}
            maxSizePerFile={50}
          />
        )}

        {viewMode === 'search' && (
          <div className="space-y-6">
            <ImageSearch
              projectId={projectId}
              onSearchResults={handleSearchResults}
              onResultSelect={handleSearchResultSelect}
            />
            
            {searchResults.length > 0 && (
              <Card title={`搜索结果 (${searchResults.length})`} padding="md">
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                  {searchResults.map((result) => (
                    <div
                      key={result.id}
                      className="group cursor-pointer"
                      onClick={() => handleSearchResultSelect(result)}
                    >
                      <div className="aspect-square rounded-lg overflow-hidden bg-zinc-800 border border-zinc-700 hover:border-amber-500/50 transition-colors">
                        <img
                          src={result.thumbnail_url || result.original_url}
                          alt={result.filename}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        
                        {/* 相似度评分 */}
                        <div className="absolute top-2 left-2">
                          <span className="px-2 py-1 bg-black/70 text-white text-xs rounded">
                            {Math.round(result.similarity_score * 100)}%
                          </span>
                        </div>
                      </div>

                      <div className="mt-2">
                        <p className="text-sm text-white truncate" title={result.filename}>
                          {result.filename}
                        </p>
                        <p className="text-xs text-zinc-400 truncate" title={result.match_reason}>
                          {result.match_reason}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>

      {/* 图片预览模态框 */}
      {showPreview && selectedImage && (
        <ImagePreview
          image={selectedImage}
          images={images}
          onClose={() => {
            setShowPreview(false);
            setSelectedImage(null);
          }}
          onDelete={handleImageDelete}
          onUpdate={handleImageUpdate}
          onFindSimilar={handleFindSimilar}
          onNavigate={handlePreviewNavigate}
        />
      )}
    </div>
  );
};

export default ImageManager;