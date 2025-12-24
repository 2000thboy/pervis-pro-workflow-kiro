# 图片识别和RAG系统 - 需求文档

## 概述

PreVis PRO图片识别和RAG系统扩展了现有的视频RAG能力，支持静态图片的上传、分析、标签生成和语义搜索。系统使用Gemini Vision API进行图片内容分析，CLIP模型进行特征提取，为导演提供更丰富的创作素材。

## 核心需求

### 需求1: 图片上传和存储
**用户故事**: 作为导演，我希望能够上传静态图片到素材库，这样我可以使用图片作为创作参考。

**验收标准**:
- 支持JPG, PNG, WebP, GIF格式
- 支持单张和批量上传
- 自动生成缩略图
- 文件大小限制：单张最大50MB
- 存储路径：`storage/images/`

### 需求2: 图片内容分析
**用户故事**: 作为导演，我希望AI能够理解图片内容，这样我可以基于内容进行搜索。

**验收标准**:
- 使用Gemini Vision API分析图片内容
- 生成详细的图片描述
- 提取物体、场景、情绪标签
- 识别色彩、构图、风格特征
- 支持中文和英文描述

### 需求3: 图片向量化和索引
**用户故事**: 作为导演，我希望系统能够建立图片的语义索引，这样我可以进行相似图片搜索。

**验收标准**:
- 使用CLIP模型生成图片特征向量
- 向量维度：512维（CLIP ViT-B/32）
- 存储到向量数据库
- 支持余弦相似度搜索
- 建立图片-文本跨模态索引

### 需求4: 图片语义搜索
**用户故事**: 作为导演，我希望能够使用自然语言搜索图片，这样我可以快速找到符合创意需求的图片。

**验收标准**:
- 支持自然语言查询："蓝色调的城市夜景"
- 支持相似图片搜索：上传图片找相似
- 支持标签过滤搜索
- 返回相关度评分和匹配理由
- 搜索响应时间<500ms

### 需求5: 图片RAG集成
**用户故事**: 作为导演，我希望图片搜索能够与现有的视频RAG系统集成，这样我可以在同一个界面搜索所有素材。

**验收标准**:
- 集成到现有的多模态搜索API
- 在BeatBoard中显示图片推荐
- 支持图片和视频的混合搜索结果
- 统一的搜索结果排序算法
- 保持现有UI设计风格

### 需求6: 图片预览和管理
**用户故事**: 作为导演，我希望能够预览和管理图片素材，这样我可以组织我的创作资源。

**验收标准**:
- 图片缩略图网格展示
- 支持图片放大预览
- 显示图片元数据（尺寸、大小、格式）
- 支持图片删除和重命名
- 支持图片标签编辑

## 技术规格

### 支持的图片格式
- **JPG/JPEG**: 最常用的图片格式
- **PNG**: 支持透明背景
- **WebP**: 现代高效格式
- **GIF**: 支持动图（取第一帧分析）

### AI模型集成
- **Gemini Vision API**: 图片内容理解和描述生成
- **CLIP ViT-B/32**: 图片特征向量提取
- **sentence-transformers**: 文本向量化（用于跨模态搜索）

### 性能要求
- 图片上传响应时间: <5秒
- 图片分析时间: <10秒
- 搜索响应时间: <500ms
- 并发上传支持: 5张图片
- 缩略图生成: <2秒

### 存储要求
- 原始图片存储: `storage/images/originals/`
- 缩略图存储: `storage/images/thumbnails/`
- 向量数据: 数据库表 `image_vectors`
- 元数据: 数据库表 `image_assets`

## 数据模型

### ImageAsset表
```sql
CREATE TABLE image_assets (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36) REFERENCES projects(id),
    filename VARCHAR(255) NOT NULL,
    original_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    mime_type VARCHAR(100),
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    description TEXT,
    tags JSONB,
    color_palette JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### ImageVector表
```sql
CREATE TABLE image_vectors (
    id VARCHAR(36) PRIMARY KEY,
    image_id VARCHAR(36) REFERENCES image_assets(id),
    vector_type VARCHAR(50), -- 'clip', 'description'
    vector_data VECTOR(512), -- CLIP向量维度
    content_text TEXT, -- 对应的文本内容
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API设计

### 图片上传API
```http
POST /api/images/upload
Content-Type: multipart/form-data

Form Data:
- files: File[] (图片文件)
- project_id: string
```

### 图片搜索API
```http
POST /api/images/search
Content-Type: application/json

{
    "query": "蓝色调的城市夜景",
    "project_id": "string",
    "limit": 10,
    "similarity_threshold": 0.7
}
```

### 相似图片搜索API
```http
POST /api/images/similar
Content-Type: multipart/form-data

Form Data:
- image: File (参考图片)
- project_id: string
- limit: 10
```

### 图片详情API
```http
GET /api/images/{image_id}
```

### 图片删除API
```http
DELETE /api/images/{image_id}
```

## 前端组件设计

### ImageUploader组件
- 拖拽上传界面
- 批量上传支持
- 上传进度显示
- 预览功能

### ImageGallery组件
- 网格布局展示
- 懒加载优化
- 搜索过滤
- 选择模式

### ImagePreview组件
- 全屏预览
- 元数据显示
- 标签编辑
- 相似图片推荐

### ImageSearch组件
- 自然语言搜索框
- 相似图片搜索
- 搜索结果展示
- 过滤选项

## 集成点

### 与现有系统的集成
1. **多模态搜索**: 扩展现有的`multimodal_search.py`
2. **BeatBoard**: 在推荐结果中显示图片
3. **素材库**: 统一的素材管理界面
4. **项目管理**: 图片与项目的关联

### 数据库集成
- 扩展现有的`assets`表或创建新的`image_assets`表
- 复用现有的向量搜索基础设施
- 集成到现有的项目数据模型

## 测试策略

### 单元测试
- 图片上传和存储
- 图片分析和标签生成
- 向量化和相似度计算
- 搜索算法准确性

### 集成测试
- 端到端图片处理流程
- 与视频RAG的集成
- 多模态搜索功能
- 前端组件交互

### 性能测试
- 大批量图片上传
- 搜索响应时间
- 并发处理能力
- 内存使用优化

## 部署考虑

### 依赖安装
```bash
pip install pillow opencv-python clip-by-openai
```

### 配置参数
```python
IMAGE_UPLOAD_DIR = "storage/images"
MAX_IMAGE_SIZE_MB = 50
THUMBNAIL_SIZE = (320, 240)
SUPPORTED_FORMATS = ['jpg', 'jpeg', 'png', 'webp', 'gif']
```

### 存储空间规划
- 原始图片: 用户上传大小
- 缩略图: 约50KB/张
- 向量数据: 2KB/张
- 建议预留: 10GB起步

## 成功标准

### 功能完整性
- [ ] 支持4种主要图片格式
- [ ] 完整的上传-分析-搜索流程
- [ ] 与现有系统无缝集成
- [ ] 用户界面友好直观

### 性能指标
- [ ] 图片上传成功率 >95%
- [ ] 分析准确率 >80%
- [ ] 搜索响应时间 <500ms
- [ ] 系统稳定性 >99%

### 用户体验
- [ ] 操作流程直观
- [ ] 错误提示清晰
- [ ] 加载状态明确
- [ ] 搜索结果相关

这个图片识别和RAG系统将显著扩展PreVis PRO的素材处理能力，为导演提供更丰富的创作资源和更强大的搜索功能。