import React, { useState, useCallback, useMemo } from 'react';
import { 
  Grid, 
  List, 
  Search, 
  Filter, 
  MoreVertical, 
  Eye, 
  Download, 
  Trash2, 
  Tag,
  Calendar,
  Image as ImageIcon,
  Loader2
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
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
}

export interface ImageGalleryProps {
  projectId: string;
  images: ImageAsset[];
  loading?: boolean;
  onImageSelect?: (image: ImageAsset) => void;
  onImageDelete?: (imageId: string) => void;
  onImagesDelete?: (imageIds: string[]) => void;
  onRefresh?: () => void;
  selectionMode?: boolean;
  className?: string;
}

type ViewMode = 'grid' | 'list';
type SortBy = 'name' | 'date' | 'size' | 'status';
type FilterBy = 'all' | 'completed' | 'processing' | 'failed';

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  projectId,
  images,
  loading = false,
  onImageSelect,
  onImageDelete,
  onImagesDelete,
  onRefresh,
  selectionMode = false,
  className = ''
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortBy>('date');
  const [filterBy, setFilterBy] = useState<FilterBy>('all');
  const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
  const [showFilters, setShowFilters] = useState(false);

  // 过滤和排序图片
  const filteredAndSortedImages = useMemo(() => {
    let filtered = images;

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(image => 
        image.filename.toLowerCase().includes(query) ||
        image.description?.toLowerCase().includes(query) ||
        Object.values(image.tags || {}).flat().some(tag => 
          tag.toLowerCase().includes(query)
        )
      );
    }

    // 状态过滤
    if (filterBy !== 'all') {
      filtered = filtered.filter(image => image.processing_status === filterBy);
    }

    // 排序
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.filename.localeCompare(b.filename);
        case 'date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'size':
          return b.metadata.file_size - a.metadata.file_size;
        case 'status':
          return a.processing_status.localeCompare(b.processing_status);
        default:
          return 0;
      }
    });

    return filtered;
  }, [images, searchQuery, sortBy, filterBy]);

  // 选择处理
  const handleImageClick = useCallback((image: ImageAsset) => {
    if (selectionMode) {
      const newSelected = new Set(selectedImages);
      if (newSelected.has(image.id)) {
        newSelected.delete(image.id);
      } else {
        newSelected.add(image.id);
      }
      setSelectedImages(newSelected);
    } else {
      onImageSelect?.(image);
    }
  }, [selectionMode, selectedImages, onImageSelect]);

  // 全选/取消全选
  const handleSelectAll = useCallback(() => {
    if (selectedImages.size === filteredAndSortedImages.length) {
      setSelectedImages(new Set());
    } else {
      setSelectedImages(new Set(filteredAndSortedImages.map(img => img.id)));
    }
  }, [selectedImages.size, filteredAndSortedImages]);

  // 批量删除
  const handleBatchDelete = useCallback(() => {
    if (selectedImages.size > 0 && onImagesDelete) {
      onImagesDelete(Array.from(selectedImages));
      setSelectedImages(new Set());
    }
  }, [selectedImages, onImagesDelete]);

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
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-emerald-400';
      case 'processing': return 'text-amber-400';
      case 'failed': return 'text-red-400';
      default: return 'text-zinc-400';
    }
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'processing': return '处理中';
      case 'failed': return '失败';
      case 'pending': return '等待中';
      default: return status;
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 工具栏 */}
      <Card padding="md">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* 搜索 */}
          <div className="flex-1">
            <Input
              placeholder="搜索图片..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={Search}
              size="sm"
            />
          </div>

          {/* 控制按钮 */}
          <div className="flex items-center gap-2">
            {/* 视图模式 */}
            <div className="flex rounded-lg border border-zinc-700 overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`
                  px-3 py-2 text-sm transition-colors
                  ${viewMode === 'grid' 
                    ? 'bg-amber-500 text-black' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                  }
                `}
              >
                <Grid size={16} />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`
                  px-3 py-2 text-sm transition-colors
                  ${viewMode === 'list' 
                    ? 'bg-amber-500 text-black' 
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-800'
                  }
                `}
              >
                <List size={16} />
              </button>
            </div>

            {/* 过滤器 */}
            <Button
              variant="ghost"
              size="sm"
              icon={Filter}
              onClick={() => setShowFilters(!showFilters)}
            >
              过滤
            </Button>

            {/* 刷新 */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              loading={loading}
            >
              刷新
            </Button>
          </div>
        </div>

        {/* 过滤器面板 */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-zinc-800 flex flex-wrap gap-4">
            <div>
              <label className="block text-xs text-zinc-400 mb-1">排序方式</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortBy)}
                className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1 text-sm text-white"
              >
                <option value="date">按日期</option>
                <option value="name">按名称</option>
                <option value="size">按大小</option>
                <option value="status">按状态</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-zinc-400 mb-1">状态过滤</label>
              <select
                value={filterBy}
                onChange={(e) => setFilterBy(e.target.value as FilterBy)}
                className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1 text-sm text-white"
              >
                <option value="all">全部</option>
                <option value="completed">已完成</option>
                <option value="processing">处理中</option>
                <option value="failed">失败</option>
              </select>
            </div>
          </div>
        )}

        {/* 选择模式工具栏 */}
        {selectionMode && (
          <div className="mt-4 pt-4 border-t border-zinc-800 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleSelectAll}
              >
                {selectedImages.size === filteredAndSortedImages.length ? '取消全选' : '全选'}
              </Button>
              
              {selectedImages.size > 0 && (
                <span className="text-sm text-zinc-400">
                  已选择 {selectedImages.size} 个图片
                </span>
              )}
            </div>

            {selectedImages.size > 0 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="danger"
                  size="sm"
                  icon={Trash2}
                  onClick={handleBatchDelete}
                >
                  删除选中
                </Button>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* 图片列表 */}
      <Card padding="md">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={32} className="animate-spin text-amber-500" />
            <span className="ml-3 text-zinc-400">加载中...</span>
          </div>
        ) : filteredAndSortedImages.length === 0 ? (
          <div className="text-center py-12">
            <ImageIcon size={48} className="mx-auto text-zinc-600 mb-4" />
            <h3 className="text-lg font-medium text-zinc-400 mb-2">
              {searchQuery ? '没有找到匹配的图片' : '还没有图片'}
            </h3>
            <p className="text-zinc-500">
              {searchQuery ? '尝试调整搜索条件' : '上传一些图片开始使用'}
            </p>
          </div>
        ) : (
          <div className={
            viewMode === 'grid' 
              ? 'grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4'
              : 'space-y-2'
          }>
            {filteredAndSortedImages.map((image) => (
              <div
                key={image.id}
                className={`
                  group cursor-pointer transition-all duration-200
                  ${viewMode === 'grid' ? 'aspect-square' : ''}
                  ${selectedImages.has(image.id) ? 'ring-2 ring-amber-500' : ''}
                `}
                onClick={() => handleImageClick(image)}
              >
                {viewMode === 'grid' ? (
                  // 网格视图
                  <div className="relative h-full rounded-lg overflow-hidden bg-zinc-800 border border-zinc-700 hover:border-zinc-600">
                    <img
                      src={image.thumbnail_url || image.original_url}
                      alt={image.filename}
                      className="w-full h-full object-cover"
                      loading="lazy"
                    />
                    
                    {/* 状态指示器 */}
                    <div className="absolute top-2 left-2">
                      <div className={`
                        w-2 h-2 rounded-full
                        ${image.processing_status === 'completed' ? 'bg-emerald-400' : ''}
                        ${image.processing_status === 'processing' ? 'bg-amber-400 animate-pulse' : ''}
                        ${image.processing_status === 'failed' ? 'bg-red-400' : ''}
                        ${image.processing_status === 'pending' ? 'bg-zinc-400' : ''}
                      `} />
                    </div>

                    {/* 选择指示器 */}
                    {selectionMode && (
                      <div className="absolute top-2 right-2">
                        <div className={`
                          w-5 h-5 rounded-full border-2 flex items-center justify-center
                          ${selectedImages.has(image.id) 
                            ? 'bg-amber-500 border-amber-500' 
                            : 'border-white/50 bg-black/30'
                          }
                        `}>
                          {selectedImages.has(image.id) && (
                            <div className="w-2 h-2 bg-black rounded-full" />
                          )}
                        </div>
                      </div>
                    )}

                    {/* 悬停信息 */}
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-end">
                      <div className="p-3 w-full">
                        <p className="text-white text-sm font-medium truncate">
                          {image.filename}
                        </p>
                        <p className="text-zinc-300 text-xs">
                          {image.metadata.width}×{image.metadata.height} • {formatFileSize(image.metadata.file_size)}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  // 列表视图
                  <div className="flex items-center gap-4 p-3 rounded-lg bg-zinc-900/50 hover:bg-zinc-900/70 border border-zinc-800 hover:border-zinc-700">
                    <div className="w-16 h-16 rounded-lg overflow-hidden bg-zinc-800 flex-shrink-0">
                      <img
                        src={image.thumbnail_url || image.original_url}
                        alt={image.filename}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-white truncate">
                          {image.filename}
                        </h3>
                        <span className={`text-xs px-2 py-1 rounded ${getStatusColor(image.processing_status)}`}>
                          {getStatusText(image.processing_status)}
                        </span>
                      </div>
                      
                      <p className="text-sm text-zinc-400 mb-1">
                        {image.metadata.width}×{image.metadata.height} • {formatFileSize(image.metadata.file_size)}
                      </p>
                      
                      <p className="text-xs text-zinc-500">
                        {formatDate(image.created_at)}
                      </p>
                    </div>

                    {/* 操作按钮 */}
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Eye}
                        onClick={(e) => {
                          e.stopPropagation();
                          onImageSelect?.(image);
                        }}
                      />
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={Trash2}
                        onClick={(e) => {
                          e.stopPropagation();
                          onImageDelete?.(image.id);
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 统计信息 */}
      {filteredAndSortedImages.length > 0 && (
        <div className="text-center text-sm text-zinc-500">
          显示 {filteredAndSortedImages.length} / {images.length} 个图片
          {selectedImages.size > 0 && ` • 已选择 ${selectedImages.size} 个`}
        </div>
      )}
    </div>
  );
};

export default ImageGallery;