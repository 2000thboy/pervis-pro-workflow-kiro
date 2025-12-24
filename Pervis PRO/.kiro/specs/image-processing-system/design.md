# 图片识别和RAG系统 - 设计文档

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                 │
├─────────────────────────────────────────────────────────────┤
│  ImageUploader  │  ImageGallery  │  ImagePreview  │  Search  │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP API
┌─────────────────────────────────────────────────────────────┐
│                        API层                                  │
├─────────────────────────────────────────────────────────────┤
│  /api/images/*  │  /api/search/images  │  /api/multimodal/* │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        服务层                                 │
├─────────────────────────────────────────────────────────────┤
│  ImageProcessor  │  ImageAnalyzer  │  ImageSearchEngine     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        AI模型层                               │
├─────────────────────────────────────────────────────────────┤
│  Gemini Vision  │  CLIP Model  │  sentence-transformers     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      存储和数据层                             │
├─────────────────────────────────────────────────────────────┤
│  File Storage  │  PostgreSQL  │  Vector Database           │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. ImageProcessor (图片处理服务)

负责图片的基础处理操作，包括格式转换、缩略图生成、元数据提取等。

```python
class ImageProcessor:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.thumbnail_size = (320, 240)
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'gif']
    
    async def process_image(self, file_path: str, project_id: str) -> ImageAsset:
        """处理上传的图片"""
        # 1. 验证图片格式和大小
        # 2. 生成唯一ID和存储路径
        # 3. 保存原始图片
        # 4. 生成缩略图
        # 5. 提取元数据（尺寸、大小、格式）
        # 6. 创建数据库记录
        
    def generate_thumbnail(self, image_path: str) -> str:
        """生成缩略图"""
        
    def extract_metadata(self, image_path: str) -> dict:
        """提取图片元数据"""
        
    def validate_image(self, file_path: str) -> bool:
        """验证图片格式和完整性"""
```

### 2. ImageAnalyzer (图片分析服务)

使用AI模型分析图片内容，生成描述和标签。

```python
class ImageAnalyzer:
    def __init__(self, gemini_client, clip_model):
        self.gemini_client = gemini_client
        self.clip_model = clip_model
    
    async def analyze_image(self, image_path: str) -> AnalysisResult:
        """分析图片内容"""
        # 1. 使用Gemini Vision分析图片
        # 2. 生成详细描述
        # 3. 提取标签（物体、场景、情绪、风格）
        # 4. 分析色彩和构图
        # 5. 使用CLIP生成特征向量
        
    async def generate_description(self, image_path: str) -> str:
        """生成图片描述"""
        
    async def extract_tags(self, image_path: str) -> dict:
        """提取图片标签"""
        
    async def generate_clip_vector(self, image_path: str) -> np.ndarray:
        """生成CLIP特征向量"""
        
    def analyze_colors(self, image_path: str) -> dict:
        """分析主要色彩"""
```

### 3. ImageSearchEngine (图片搜索引擎)

实现图片的语义搜索和相似度搜索。

```python
class ImageSearchEngine:
    def __init__(self, db: Session, vector_db):
        self.db = db
        self.vector_db = vector_db
        self.clip_model = load_clip_model()
    
    async def search_by_text(self, query: str, project_id: str, limit: int = 10) -> List[SearchResult]:
        """基于文本查询搜索图片"""
        # 1. 将查询文本向量化
        # 2. 在向量数据库中搜索相似图片
        # 3. 计算相似度评分
        # 4. 生成匹配理由
        # 5. 按相关度排序返回
        
    async def search_by_image(self, image_path: str, project_id: str, limit: int = 10) -> List[SearchResult]:
        """基于图片搜索相似图片"""
        # 1. 提取查询图片的CLIP向量
        # 2. 计算与数据库中图片的相似度
        # 3. 返回最相似的图片
        
    async def search_by_tags(self, tags: List[str], project_id: str) -> List[SearchResult]:
        """基于标签搜索图片"""
        
    def calculate_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算向量相似度"""
        
    async def generate_match_reason(self, query: str, image: ImageAsset) -> str:
        """生成匹配理由"""
```

### 4. MultimodalSearchEngine (多模态搜索引擎扩展)

扩展现有的多模态搜索，支持图片搜索。

```python
class MultimodalSearchEngine:
    def __init__(self, video_search, image_search):
        self.video_search = video_search
        self.image_search = image_search
        self.weights = {
            'video': 0.6,
            'image': 0.4
        }
    
    async def search_all_media(self, query: str, project_id: str) -> List[SearchResult]:
        """搜索所有媒体类型"""
        # 1. 并行搜索视频和图片
        # 2. 合并搜索结果
        # 3. 按相关度重新排序
        # 4. 返回混合结果
        
    def merge_results(self, video_results: List, image_results: List) -> List[SearchResult]:
        """合并不同类型的搜索结果"""
        
    def calculate_unified_score(self, result: SearchResult) -> float:
        """计算统一的相关度评分"""
```

## 数据模型设计

### ImageAsset (图片资产)

```python
class ImageAsset(Base):
    __tablename__ = "image_assets"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"))
    filename = Column(String(255), nullable=False)
    original_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500))
    
    # 文件信息
    mime_type = Column(String(100))
    file_size = Column(Integer)  # 字节
    width = Column(Integer)
    height = Column(Integer)
    
    # AI分析结果
    description = Column(Text)
    tags = Column(JSON)  # {"objects": [], "scenes": [], "emotions": [], "styles": []}
    color_palette = Column(JSON)  # {"dominant": "#FF0000", "palette": ["#FF0000", ...]}
    
    # 处理状态
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Float, default=0.0)
    error_message = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="image_assets")
    vectors = relationship("ImageVector", back_populates="image_asset")
```

### ImageVector (图片向量)

```python
class ImageVector(Base):
    __tablename__ = "image_vectors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image_id = Column(String(36), ForeignKey("image_assets.id"))
    
    # 向量信息
    vector_type = Column(String(50))  # 'clip', 'description'
    vector_data = Column(Vector(512))  # CLIP向量维度
    content_text = Column(Text)  # 对应的文本内容
    
    # 元数据
    model_version = Column(String(100))  # 使用的模型版本
    confidence_score = Column(Float)  # 置信度评分
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    image_asset = relationship("ImageAsset", back_populates="vectors")
```

### SearchResult (搜索结果)

```python
@dataclass
class SearchResult:
    id: str
    type: str  # 'image' or 'video'
    title: str
    description: str
    thumbnail_url: str
    file_url: str
    similarity_score: float
    match_reason: str
    tags: List[str]
    metadata: dict
```

## API接口设计

### 1. 图片上传API

```python
@router.post("/upload")
async def upload_images(
    files: List[UploadFile] = File(...),
    project_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """上传图片"""
    results = []
    
    for file in files:
        # 验证文件格式
        if not is_valid_image(file):
            results.append({"filename": file.filename, "status": "error", "message": "不支持的格式"})
            continue
            
        # 保存文件
        image_asset = await image_processor.process_image(file, project_id)
        
        # 启动后台分析任务
        background_tasks.add_task(analyze_image_task, image_asset.id)
        
        results.append({
            "id": image_asset.id,
            "filename": image_asset.filename,
            "status": "uploaded",
            "thumbnail_url": image_asset.thumbnail_path
        })
    
    return {"results": results}
```

### 2. 图片搜索API

```python
@router.post("/search")
async def search_images(
    request: ImageSearchRequest,
    db: Session = Depends(get_db)
):
    """搜索图片"""
    search_engine = ImageSearchEngine(db)
    
    results = await search_engine.search_by_text(
        query=request.query,
        project_id=request.project_id,
        limit=request.limit
    )
    
    return {
        "query": request.query,
        "results": [result.to_dict() for result in results],
        "total": len(results)
    }
```

### 3. 相似图片搜索API

```python
@router.post("/similar")
async def find_similar_images(
    image: UploadFile = File(...),
    project_id: str = Form(...),
    limit: int = Form(10),
    db: Session = Depends(get_db)
):
    """查找相似图片"""
    # 保存临时文件
    temp_path = save_temp_file(image)
    
    try:
        search_engine = ImageSearchEngine(db)
        results = await search_engine.search_by_image(temp_path, project_id, limit)
        
        return {
            "results": [result.to_dict() for result in results],
            "total": len(results)
        }
    finally:
        # 清理临时文件
        os.remove(temp_path)
```

### 4. 多模态搜索API扩展

```python
@router.post("/multimodal/search")
async def multimodal_search(
    request: MultimodalSearchRequest,
    db: Session = Depends(get_db)
):
    """多模态搜索（视频+图片）"""
    search_engine = MultimodalSearchEngine(video_search, image_search)
    
    results = await search_engine.search_all_media(
        query=request.query,
        project_id=request.project_id,
        media_types=request.media_types,  # ['video', 'image']
        limit=request.limit
    )
    
    return {
        "query": request.query,
        "results": [result.to_dict() for result in results],
        "total": len(results),
        "media_types": request.media_types
    }
```

## 前端组件设计

### 1. ImageUploader组件

```typescript
interface ImageUploaderProps {
    projectId: string;
    onUploadComplete: (images: ImageAsset[]) => void;
    maxFiles?: number;
    maxSizePerFile?: number; // MB
}

const ImageUploader: React.FC<ImageUploaderProps> = ({
    projectId,
    onUploadComplete,
    maxFiles = 10,
    maxSizePerFile = 50
}) => {
    const [dragActive, setDragActive] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
    
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const files = Array.from(e.dataTransfer.files);
        uploadImages(files);
    };
    
    const uploadImages = async (files: File[]) => {
        setUploading(true);
        
        const formData = new FormData();
        formData.append('project_id', projectId);
        
        files.forEach(file => {
            formData.append('files', file);
        });
        
        try {
            const response = await apiClient.post('/api/images/upload', formData, {
                onUploadProgress: (progressEvent) => {
                    const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
                }
            });
            
            onUploadComplete(response.data.results);
        } catch (error) {
            console.error('Upload failed:', error);
        } finally {
            setUploading(false);
        }
    };
    
    return (
        <div 
            className={`upload-area ${dragActive ? 'drag-active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
        >
            {uploading ? (
                <UploadProgress progress={uploadProgress} />
            ) : (
                <UploadPrompt maxFiles={maxFiles} maxSize={maxSizePerFile} />
            )}
        </div>
    );
};
```

### 2. ImageGallery组件

```typescript
interface ImageGalleryProps {
    projectId: string;
    images: ImageAsset[];
    onImageSelect: (image: ImageAsset) => void;
    onImageDelete: (imageId: string) => void;
    selectionMode?: boolean;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({
    projectId,
    images,
    onImageSelect,
    onImageDelete,
    selectionMode = false
}) => {
    const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    
    const handleImageClick = (image: ImageAsset) => {
        if (selectionMode) {
            const newSelected = new Set(selectedImages);
            if (newSelected.has(image.id)) {
                newSelected.delete(image.id);
            } else {
                newSelected.add(image.id);
            }
            setSelectedImages(newSelected);
        } else {
            onImageSelect(image);
        }
    };
    
    return (
        <div className="image-gallery">
            <div className="gallery-header">
                <div className="view-controls">
                    <button 
                        className={viewMode === 'grid' ? 'active' : ''}
                        onClick={() => setViewMode('grid')}
                    >
                        网格视图
                    </button>
                    <button 
                        className={viewMode === 'list' ? 'active' : ''}
                        onClick={() => setViewMode('list')}
                    >
                        列表视图
                    </button>
                </div>
                
                {selectionMode && selectedImages.size > 0 && (
                    <div className="selection-actions">
                        <button onClick={() => handleBatchDelete(Array.from(selectedImages))}>
                            删除选中 ({selectedImages.size})
                        </button>
                    </div>
                )}
            </div>
            
            <div className={`gallery-content ${viewMode}`}>
                {images.map(image => (
                    <ImageCard
                        key={image.id}
                        image={image}
                        selected={selectedImages.has(image.id)}
                        onClick={() => handleImageClick(image)}
                        onDelete={() => onImageDelete(image.id)}
                        viewMode={viewMode}
                    />
                ))}
            </div>
        </div>
    );
};
```

### 3. ImageSearch组件

```typescript
interface ImageSearchProps {
    projectId: string;
    onSearchResults: (results: SearchResult[]) => void;
}

const ImageSearch: React.FC<ImageSearchProps> = ({ projectId, onSearchResults }) => {
    const [query, setQuery] = useState('');
    const [searchMode, setSearchMode] = useState<'text' | 'image'>('text');
    const [loading, setLoading] = useState(false);
    const [referenceImage, setReferenceImage] = useState<File | null>(null);
    
    const handleTextSearch = async () => {
        if (!query.trim()) return;
        
        setLoading(true);
        try {
            const response = await apiClient.post('/api/images/search', {
                query,
                project_id: projectId,
                limit: 20
            });
            
            onSearchResults(response.data.results);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setLoading(false);
        }
    };
    
    const handleImageSearch = async () => {
        if (!referenceImage) return;
        
        setLoading(true);
        const formData = new FormData();
        formData.append('image', referenceImage);
        formData.append('project_id', projectId);
        formData.append('limit', '20');
        
        try {
            const response = await apiClient.post('/api/images/similar', formData);
            onSearchResults(response.data.results);
        } catch (error) {
            console.error('Similar search failed:', error);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <div className="image-search">
            <div className="search-mode-tabs">
                <button 
                    className={searchMode === 'text' ? 'active' : ''}
                    onClick={() => setSearchMode('text')}
                >
                    文本搜索
                </button>
                <button 
                    className={searchMode === 'image' ? 'active' : ''}
                    onClick={() => setSearchMode('image')}
                >
                    相似图片
                </button>
            </div>
            
            {searchMode === 'text' ? (
                <div className="text-search">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="描述你要找的图片..."
                        onKeyPress={(e) => e.key === 'Enter' && handleTextSearch()}
                    />
                    <button onClick={handleTextSearch} disabled={loading}>
                        {loading ? '搜索中...' : '搜索'}
                    </button>
                </div>
            ) : (
                <div className="image-search">
                    <input
                        type="file"
                        accept="image/*"
                        onChange={(e) => setReferenceImage(e.target.files?.[0] || null)}
                    />
                    <button onClick={handleImageSearch} disabled={!referenceImage || loading}>
                        {loading ? '搜索中...' : '查找相似'}
                    </button>
                </div>
            )}
        </div>
    );
};
```

## 集成策略

### 1. 与现有多模态搜索的集成

扩展现有的`multimodal_search.py`服务：

```python
class EnhancedMultimodalSearch:
    def __init__(self, video_search, image_search, text_search):
        self.video_search = video_search
        self.image_search = image_search
        self.text_search = text_search
    
    async def unified_search(self, query: str, project_id: str, media_types: List[str]) -> List[SearchResult]:
        """统一搜索接口"""
        tasks = []
        
        if 'video' in media_types:
            tasks.append(self.video_search.search(query, project_id))
        if 'image' in media_types:
            tasks.append(self.image_search.search_by_text(query, project_id))
        if 'text' in media_types:
            tasks.append(self.text_search.search(query, project_id))
        
        # 并行执行搜索
        results = await asyncio.gather(*tasks)
        
        # 合并和排序结果
        return self.merge_and_rank_results(results)
```

### 2. 与BeatBoard的集成

在BeatBoard中显示图片推荐：

```typescript
// 扩展现有的BeatBoard组件
const EnhancedBeatBoard: React.FC<BeatBoardProps> = ({ beats, onBeatSelect }) => {
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [selectedMediaTypes, setSelectedMediaTypes] = useState<string[]>(['video', 'image']);
    
    const handleBeatClick = async (beat: Beat) => {
        // 搜索相关的视频和图片
        const results = await apiClient.post('/api/multimodal/search', {
            query: beat.content,
            project_id: beat.project_id,
            media_types: selectedMediaTypes,
            limit: 10
        });
        
        setSearchResults(results.data.results);
        onBeatSelect(beat);
    };
    
    return (
        <div className="enhanced-beatboard">
            <div className="media-type-filter">
                <label>
                    <input 
                        type="checkbox" 
                        checked={selectedMediaTypes.includes('video')}
                        onChange={(e) => toggleMediaType('video', e.target.checked)}
                    />
                    视频
                </label>
                <label>
                    <input 
                        type="checkbox" 
                        checked={selectedMediaTypes.includes('image')}
                        onChange={(e) => toggleMediaType('image', e.target.checked)}
                    />
                    图片
                </label>
            </div>
            
            <div className="beats-and-results">
                <div className="beats-panel">
                    {beats.map(beat => (
                        <BeatCard 
                            key={beat.id} 
                            beat={beat} 
                            onClick={() => handleBeatClick(beat)}
                        />
                    ))}
                </div>
                
                <div className="results-panel">
                    <MediaResults results={searchResults} />
                </div>
            </div>
        </div>
    );
};
```

## 性能优化策略

### 1. 图片处理优化

```python
class OptimizedImageProcessor:
    def __init__(self):
        self.thumbnail_cache = {}
        self.processing_queue = asyncio.Queue(maxsize=100)
    
    async def process_with_cache(self, image_path: str) -> str:
        """带缓存的图片处理"""
        cache_key = f"{image_path}_{os.path.getmtime(image_path)}"
        
        if cache_key in self.thumbnail_cache:
            return self.thumbnail_cache[cache_key]
        
        thumbnail_path = await self.generate_thumbnail(image_path)
        self.thumbnail_cache[cache_key] = thumbnail_path
        
        return thumbnail_path
    
    async def batch_process(self, image_paths: List[str]) -> List[str]:
        """批量处理图片"""
        tasks = [self.process_with_cache(path) for path in image_paths]
        return await asyncio.gather(*tasks)
```

### 2. 向量搜索优化

```python
class OptimizedVectorSearch:
    def __init__(self, vector_db):
        self.vector_db = vector_db
        self.search_cache = TTLCache(maxsize=1000, ttl=300)  # 5分钟缓存
    
    async def search_with_cache(self, query_vector: np.ndarray, limit: int) -> List[SearchResult]:
        """带缓存的向量搜索"""
        cache_key = hashlib.md5(query_vector.tobytes()).hexdigest()
        
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        results = await self.vector_db.search(query_vector, limit)
        self.search_cache[cache_key] = results
        
        return results
```

### 3. 前端性能优化

```typescript
// 虚拟滚动优化大量图片展示
const VirtualizedImageGallery: React.FC<ImageGalleryProps> = ({ images }) => {
    const [visibleRange, setVisibleRange] = useState({ start: 0, end: 20 });
    const containerRef = useRef<HTMLDivElement>(null);
    
    const handleScroll = useCallback(
        throttle(() => {
            if (!containerRef.current) return;
            
            const { scrollTop, clientHeight } = containerRef.current;
            const itemHeight = 200; // 假设每个图片卡片高度
            
            const start = Math.floor(scrollTop / itemHeight);
            const end = Math.min(start + Math.ceil(clientHeight / itemHeight) + 5, images.length);
            
            setVisibleRange({ start, end });
        }, 100),
        [images.length]
    );
    
    const visibleImages = images.slice(visibleRange.start, visibleRange.end);
    
    return (
        <div ref={containerRef} className="virtualized-gallery" onScroll={handleScroll}>
            <div style={{ height: images.length * 200 }}>
                <div style={{ transform: `translateY(${visibleRange.start * 200}px)` }}>
                    {visibleImages.map(image => (
                        <ImageCard key={image.id} image={image} />
                    ))}
                </div>
            </div>
        </div>
    );
};
```

## 测试策略

### 1. 单元测试

```python
class TestImageProcessor:
    def test_image_validation(self):
        """测试图片格式验证"""
        processor = ImageProcessor()
        
        assert processor.validate_image("test.jpg") == True
        assert processor.validate_image("test.png") == True
        assert processor.validate_image("test.txt") == False
    
    def test_thumbnail_generation(self):
        """测试缩略图生成"""
        processor = ImageProcessor()
        
        thumbnail_path = processor.generate_thumbnail("test_image.jpg")
        assert os.path.exists(thumbnail_path)
        
        # 验证缩略图尺寸
        with Image.open(thumbnail_path) as img:
            assert img.size == (320, 240)
```

### 2. 集成测试

```python
class TestImageSearchIntegration:
    async def test_upload_and_search_workflow(self):
        """测试完整的上传和搜索流程"""
        # 1. 上传图片
        image_asset = await image_processor.process_image("test.jpg", "project_1")
        
        # 2. 分析图片
        analysis = await image_analyzer.analyze_image(image_asset.original_path)
        
        # 3. 搜索图片
        results = await image_search.search_by_text("蓝色天空", "project_1")
        
        assert len(results) > 0
        assert any(r.id == image_asset.id for r in results)
```

### 3. 性能测试

```python
class TestImagePerformance:
    async def test_batch_upload_performance(self):
        """测试批量上传性能"""
        start_time = time.time()
        
        # 模拟上传100张图片
        tasks = [upload_image(f"test_{i}.jpg") for i in range(100)]
        await asyncio.gather(*tasks)
        
        end_time = time.time()
        
        # 验证平均处理时间 < 5秒/张
        avg_time = (end_time - start_time) / 100
        assert avg_time < 5.0
    
    async def test_search_response_time(self):
        """测试搜索响应时间"""
        start_time = time.time()
        
        results = await image_search.search_by_text("城市夜景", "project_1")
        
        end_time = time.time()
        
        # 验证搜索时间 < 500ms
        assert (end_time - start_time) < 0.5
```

这个设计文档提供了完整的图片识别和RAG系统的技术架构，包括核心组件、数据模型、API接口、前端组件和性能优化策略。系统设计考虑了与现有系统的集成，确保无缝扩展PreVis PRO的功能。