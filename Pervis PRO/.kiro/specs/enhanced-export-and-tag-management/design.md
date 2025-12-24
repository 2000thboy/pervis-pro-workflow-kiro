# PreVis PRO 增强导出和标签管理系统 - 设计文档

## 概述

本设计文档描述了PreVis PRO增强导出和标签管理系统的技术架构、组件设计和实现方案。系统将提供专业的文档导出、BeatBoard可视化导出、以及智能标签管理功能。

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (Frontend)                        │
├─────────────────────────────────────────────────────────────┤
│  启动器 (Launcher)          │    Web界面 (React)            │
│  - 导出快捷按钮              │    - 导出页面                 │
│  - 标签管理入口              │    - BeatBoard导出            │
│                             │    - 标签管理界面              │
│                             │    - 向量可视化               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     API层 (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│  /api/export/script         │  /api/export/beatboard        │
│  /api/tags/manage           │  /api/tags/visualize          │
│  /api/search/test           │  /api/vector/similarity       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   服务层 (Services)                          │
├─────────────────────────────────────────────────────────────┤
│  DocumentExporter           │  ImageExporter                │
│  - generate_docx()          │  - render_beatboard()         │
│  - generate_pdf()           │  - export_png()               │
│                             │                               │
│  TagManager                 │  VectorAnalyzer               │
│  - update_hierarchy()       │  - calculate_similarity()     │
│  - adjust_weights()         │  - visualize_space()          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   数据层 (Database)                          │
├─────────────────────────────────────────────────────────────┤
│  Projects  │  Beats  │  Tags  │  TagWeights  │  Vectors    │
└─────────────────────────────────────────────────────────────┘
```

## 组件和接口

### 1. 文档导出服务 (DocumentExporter)

#### 接口定义

```python
class DocumentExporter:
    """剧本文档导出服务"""
    
    async def export_script_docx(
        self, 
        project_id: str,
        include_beats: bool = True,
        include_tags: bool = True,
        include_metadata: bool = True
    ) -> bytes:
        """导出剧本为DOCX格式"""
        pass
    
    async def export_script_pdf(
        self, 
        project_id: str,
        template: str = "professional",
        include_beats: bool = True,
        include_tags: bool = True
    ) -> bytes:
        """导出剧本为PDF格式"""
        pass
```

#### 实现细节

**DOCX导出流程**:
1. 从数据库加载项目、剧本和Beat数据
2. 使用python-docx创建文档对象
3. 添加文档头部（标题、元数据）
4. 遍历Beat，添加格式化内容
5. 添加标签表格和统计信息
6. 生成字节流返回

**PDF导出流程**:
1. 从数据库加载项目数据
2. 使用Jinja2模板渲染HTML
3. 使用WeasyPrint将HTML转换为PDF
4. 应用专业样式（字体、间距、页眉页脚）
5. 生成字节流返回

#### 数据模型

```python
class ExportRequest(BaseModel):
    project_id: str
    format: Literal["docx", "pdf"]
    options: ExportOptions

class ExportOptions(BaseModel):
    include_beats: bool = True
    include_tags: bool = True
    include_metadata: bool = True
    template: str = "professional"
    
class ExportResponse(BaseModel):
    status: str
    file_url: str
    file_size: int
    generated_at: datetime
```

### 2. 图片导出服务 (ImageExporter)

#### 接口定义

```python
class ImageExporter:
    """BeatBoard图片导出服务"""
    
    async def export_beatboard_image(
        self,
        project_id: str,
        format: Literal["png", "jpg"],
        width: int = 1920,
        height: int = 1080,
        quality: int = 95,
        beat_ids: Optional[List[str]] = None
    ) -> bytes:
        """导出BeatBoard为图片"""
        pass
    
    async def render_beatboard_html(
        self,
        project_id: str,
        beat_ids: Optional[List[str]] = None
    ) -> str:
        """渲染BeatBoard为HTML（用于转换为图片）"""
        pass
```

#### 实现细节

**图片导出流程**:
1. 从数据库加载Beat数据
2. 使用React组件渲染BeatBoard HTML
3. 使用Playwright或Puppeteer截图
4. 使用Pillow调整尺寸和质量
5. 生成字节流返回

**替代方案（服务端渲染）**:
1. 使用Python的matplotlib或plotly生成可视化
2. 直接生成PNG/JPG图片
3. 优点：不需要浏览器，性能更好
4. 缺点：样式可能与Web界面不一致

#### 数据模型

```python
class ImageExportRequest(BaseModel):
    project_id: str
    format: Literal["png", "jpg"]
    width: int = 1920
    height: int = 1080
    quality: int = 95
    beat_ids: Optional[List[str]] = None
    
class ImageExportResponse(BaseModel):
    status: str
    image_url: str
    width: int
    height: int
    file_size: int
```

### 3. 标签管理服务 (TagManager)

#### 接口定义

```python
class TagManager:
    """视频标签管理服务"""
    
    async def get_video_tags(
        self,
        asset_id: str
    ) -> VideoTagsResponse:
        """获取视频的所有标签及其层级关系"""
        pass
    
    async def update_tag_hierarchy(
        self,
        asset_id: str,
        tag_id: str,
        parent_tag_id: Optional[str],
        order: int
    ) -> TagUpdateResponse:
        """更新标签的层级关系和顺序"""
        pass
    
    async def update_tag_weight(
        self,
        asset_id: str,
        tag_id: str,
        weight: float
    ) -> TagUpdateResponse:
        """更新标签的关联度权重"""
        pass
    
    async def batch_update_tags(
        self,
        asset_id: str,
        updates: List[TagUpdate]
    ) -> BatchUpdateResponse:
        """批量更新标签"""
        pass
```

#### 实现细节

**标签层级管理**:
1. 使用邻接表模型存储标签层级
2. 支持多级嵌套（场景 > 城市 > 夜景 > 霓虹灯）
3. 使用递归查询获取完整层级树
4. 支持拖拽重新组织层级

**权重调整**:
1. 权重范围：0.0 - 1.0
2. 权重影响搜索排序和向量计算
3. 调整权重后自动重新计算向量索引
4. 支持批量调整多个标签权重

#### 数据模型

```python
class TagHierarchy(BaseModel):
    tag_id: str
    tag_name: str
    parent_id: Optional[str]
    children: List['TagHierarchy']
    weight: float
    order: int
    
class VideoTagsResponse(BaseModel):
    asset_id: str
    tags: List[TagHierarchy]
    total_tags: int
    
class TagUpdate(BaseModel):
    tag_id: str
    parent_id: Optional[str] = None
    weight: Optional[float] = None
    order: Optional[int] = None
```

### 4. 向量分析服务 (VectorAnalyzer)

#### 接口定义

```python
class VectorAnalyzer:
    """向量关联度分析服务"""
    
    async def calculate_similarity(
        self,
        query: str,
        asset_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> SimilarityResponse:
        """计算查询与视频的相似度"""
        pass
    
    async def visualize_vector_space(
        self,
        asset_ids: List[str],
        method: Literal["tsne", "pca"] = "tsne"
    ) -> VectorVisualization:
        """可视化向量空间"""
        pass
    
    async def explain_match(
        self,
        query: str,
        asset_id: str
    ) -> MatchExplanation:
        """解释匹配结果"""
        pass
```

#### 实现细节

**相似度计算**:
1. 使用Gemini Embedding API生成查询向量
2. 从数据库加载视频向量
3. 计算余弦相似度
4. 考虑标签权重调整最终分数
5. 返回Top-K结果

**向量空间可视化**:
1. 使用t-SNE或PCA降维到2D/3D
2. 使用D3.js或Plotly渲染交互式图表
3. 支持缩放、平移、点击查看详情
4. 颜色编码表示不同类别或相似度

**匹配解释**:
1. 分析查询中的关键词
2. 匹配视频的标签
3. 计算每个标签的贡献度
4. 生成可读的解释文本

#### 数据模型

```python
class SimilarityResult(BaseModel):
    asset_id: str
    score: float
    matched_tags: List[str]
    tag_contributions: Dict[str, float]
    
class SimilarityResponse(BaseModel):
    query: str
    results: List[SimilarityResult]
    total_results: int
    
class VectorVisualization(BaseModel):
    points: List[VectorPoint]
    method: str
    explained_variance: Optional[float]
    
class VectorPoint(BaseModel):
    asset_id: str
    x: float
    y: float
    z: Optional[float]
    label: str
    
class MatchExplanation(BaseModel):
    query: str
    asset_id: str
    overall_score: float
    matched_keywords: List[str]
    tag_matches: List[TagMatch]
    explanation_text: str
    
class TagMatch(BaseModel):
    tag_name: str
    tag_weight: float
    contribution: float
    reason: str
```

## 数据模型

### 数据库Schema扩展

```sql
-- 标签层级表
CREATE TABLE tag_hierarchy (
    id TEXT PRIMARY KEY,
    tag_name TEXT NOT NULL,
    parent_id TEXT,
    level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES tag_hierarchy(id)
);

-- 资产标签关联表（扩展）
CREATE TABLE asset_tags (
    id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (tag_id) REFERENCES tag_hierarchy(id),
    UNIQUE(asset_id, tag_id)
);

-- 导出历史表
CREATE TABLE export_history (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    export_type TEXT NOT NULL, -- 'script_docx', 'script_pdf', 'beatboard_image'
    file_path TEXT NOT NULL,
    file_size INTEGER,
    options JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 搜索测试案例表
CREATE TABLE search_test_cases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    query TEXT NOT NULL,
    expected_results JSON,
    actual_results JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 错误处理

### 错误类型

1. **导出错误**
   - `EXPORT_TEMPLATE_NOT_FOUND`: 模板文件不存在
   - `EXPORT_GENERATION_FAILED`: 文档生成失败
   - `EXPORT_FILE_TOO_LARGE`: 生成的文件过大

2. **标签管理错误**
   - `TAG_NOT_FOUND`: 标签不存在
   - `TAG_HIERARCHY_CYCLE`: 标签层级形成循环
   - `TAG_WEIGHT_INVALID`: 权重值无效

3. **向量分析错误**
   - `VECTOR_NOT_FOUND`: 向量不存在
   - `EMBEDDING_API_ERROR`: Embedding API调用失败
   - `VISUALIZATION_FAILED`: 可视化生成失败

### 错误响应格式

```python
class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]]
    trace_id: str
```

## 测试策略

### 单元测试

1. **DocumentExporter测试**
   - 测试DOCX生成的格式正确性
   - 测试PDF生成的样式一致性
   - 测试不同选项组合的输出

2. **ImageExporter测试**
   - 测试图片尺寸和质量
   - 测试不同格式的输出
   - 测试单个和批量Beat导出

3. **TagManager测试**
   - 测试标签层级的CRUD操作
   - 测试权重调整的正确性
   - 测试批量更新的事务性

4. **VectorAnalyzer测试**
   - 测试相似度计算的准确性
   - 测试向量空间可视化
   - 测试匹配解释的可读性

### 集成测试

1. **端到端导出流程**
   - 创建项目 → 添加Beat → 导出DOCX → 验证内容
   - 创建项目 → 添加Beat → 导出PDF → 验证格式
   - 创建项目 → 添加Beat → 导出图片 → 验证质量

2. **标签管理流程**
   - 上传视频 → 自动生成标签 → 调整层级 → 验证搜索结果
   - 调整权重 → 重新搜索 → 验证排序变化

3. **向量搜索流程**
   - 输入查询 → 计算相似度 → 返回结果 → 验证准确性
   - 调整标签 → 重新搜索 → 验证结果变化

### 性能测试

1. **导出性能**
   - 测试100页剧本的DOCX导出时间（目标<10秒）
   - 测试20个Beat的图片导出时间（目标<5秒）

2. **标签管理性能**
   - 测试1000个标签的加载时间（目标<2秒）
   - 测试批量更新100个标签的时间（目标<3秒）

3. **向量搜索性能**
   - 测试1000个视频的搜索时间（目标<1秒）
   - 测试向量空间可视化的渲染时间（目标<3秒）

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 导出文档完整性

*对于任何*项目和导出选项，导出的文档应包含所有选中的内容元素，且内容与数据库中的数据一致。

**验证**: 需求 1.2, 1.3, 1.5

### 属性 2: 图片导出质量保证

*对于任何*BeatBoard和导出设置，生成的图片分辨率应不低于指定值，且所有Beat信息应清晰可见。

**验证**: 需求 2.3, 2.4, 2.5

### 属性 3: 标签层级无循环

*对于任何*标签层级调整操作，调整后的标签树应不包含循环引用（即标签不能是自己的祖先）。

**验证**: 需求 3.6

### 属性 4: 权重调整一致性

*对于任何*标签权重调整，调整后的搜索结果排序应反映新的权重值，且权重值应在0-1范围内。

**验证**: 需求 3.8, 3.9

### 属性 5: 向量相似度对称性

*对于任何*两个视频A和B，相似度(A, B)应等于相似度(B, A)。

**验证**: 需求 4.2

### 属性 6: 搜索结果单调性

*对于任何*查询，如果标签X的权重增加，则包含标签X的视频的排名应不降低（假设其他条件不变）。

**验证**: 需求 4.4

## 实现计划

### Phase 1: 文档导出（1周）

1. 实现DocumentExporter服务
2. 添加DOCX导出功能
3. 添加PDF导出功能
4. 创建导出API端点
5. 在启动器中添加导出按钮
6. 在Web界面添加导出页面

### Phase 2: 图片导出（1周）

1. 实现ImageExporter服务
2. 添加BeatBoard HTML渲染
3. 添加截图和图片生成功能
4. 创建图片导出API端点
5. 在BeatBoard页面添加导出按钮

### Phase 3: 标签管理（2周）

1. 扩展数据库Schema
2. 实现TagManager服务
3. 创建标签管理API端点
4. 实现标签管理前端界面
5. 添加拖拽和权重调整功能
6. 集成到启动器和Web界面

### Phase 4: 向量分析（2周）

1. 实现VectorAnalyzer服务
2. 添加相似度计算功能
3. 添加向量空间可视化
4. 添加匹配解释功能
5. 创建搜索测试界面
6. 优化性能和准确性

### Phase 5: 测试和优化（1周）

1. 编写单元测试
2. 编写集成测试
3. 进行性能测试
4. 修复Bug和优化
5. 编写用户文档

## 部署和维护

### 部署要求

1. 安装依赖包：python-docx, WeasyPrint, Pillow, Playwright
2. 配置文件存储路径
3. 配置Gemini API密钥
4. 初始化数据库Schema

### 监控指标

1. 导出成功率和失败率
2. 导出平均耗时
3. 标签调整频率
4. 搜索查询量和准确率
5. API响应时间

### 维护计划

1. 每周检查导出文件质量
2. 每月优化向量索引
3. 定期备份标签配置
4. 收集用户反馈并改进
