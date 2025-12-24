# PreVis PRO 素材存储架构完整文档

**更新时间**: 2025年12月17日  
**数据库版本**: SQLite 3.x  
**存储架构**: 混合本地存储系统

## 📊 当前存储状态概览

### 数据库统计 (backend/pervis_director.db)
- **文件大小**: 327KB
- **表结构**: 6个核心表
- **总记录数**: 269条记录

| 表名 | 记录数 | 用途 |
|------|--------|------|
| projects | 19 | 项目基础信息 |
| beats | 34 | 剧本分解片段 |
| assets | 53 | 素材文件记录 |
| asset_segments | 110 | 素材时间片段 |
| asset_vectors | 50 | 向量化数据 |
| feedback_logs | 3 | 用户反馈日志 |

### 文件存储统计
- **原始视频**: 30个MP4文件 (【免费更新+V Lingshao2605】系列 + video_011-030)
- **处理后素材**: 53个资产记录
- **音频文件**: 50个WAV文件 (已提取)
- **代理文件**: 49个代理MP4文件 (已生成)
- **缩略图**: 50个JPG缩略图 (已生成)

## 🗂️ 存储架构详解

### 1. 数据库存储 (SQLite)
**位置**: `backend/pervis_director.db`

#### 核心表结构:
```sql
-- 项目表
CREATE TABLE projects (
    id VARCHAR PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    logline TEXT,
    synopsis TEXT,
    script_raw TEXT,
    characters JSON,
    specs JSON,
    created_at DATETIME,
    current_stage VARCHAR(50)
);

-- 素材表 (核心)
CREATE TABLE assets (
    id VARCHAR PRIMARY KEY,
    project_id VARCHAR NOT NULL,
    filename VARCHAR(255),
    mime_type VARCHAR(100),
    source VARCHAR(50),      -- upload, external, generated, local
    file_path VARCHAR(500),  -- 原始文件路径
    proxy_path VARCHAR(500), -- 代理文件路径
    thumbnail_path VARCHAR(500), -- 缩略图路径
    processing_status VARCHAR(50), -- uploaded, processing, completed, error
    processing_progress INTEGER DEFAULT 0,
    tags JSON,
    processing_metadata JSON,
    created_at DATETIME
);

-- 素材片段表
CREATE TABLE asset_segments (
    id VARCHAR PRIMARY KEY,
    asset_id VARCHAR NOT NULL,
    start_time FLOAT,
    end_time FLOAT,
    description TEXT,
    emotion_tags JSON,
    scene_tags JSON,
    action_tags JSON,
    cinematography_tags JSON
);

-- 向量数据表
CREATE TABLE asset_vectors (
    id VARCHAR PRIMARY KEY,
    asset_id VARCHAR NOT NULL,
    segment_id VARCHAR,
    vector_data TEXT,        -- JSON存储向量数据
    content_type VARCHAR(50), -- transcript, description, tags
    text_content TEXT,
    created_at DATETIME
);
```

### 2. 文件系统存储
**根目录**: `backend/assets/`

```
backend/assets/
├── 【免费更新+V Lingshao2605】01.mp4  # 原始视频文件 (30个)
├── 【免费更新+V Lingshao2605】02.mp4
├── ...
├── video_011.mp4 到 video_030.mp4
├── originals/          # 原始文件存储 (53个文件)
│   ├── asset_[id].mp4  # 原始视频文件
│   ├── asset_[id].txt  # 文本描述文件
│   └── asset_[id].jpg  # 原始图片文件
├── proxies/            # 代理文件 (49个)
│   └── asset_[id]_proxy.mp4  # 压缩后的代理视频
├── thumbnails/         # 缩略图 (50个)
│   └── asset_[id]_thumb.jpg  # 视频缩略图
└── audio/              # 音频文件 (50个)
    └── asset_[id].wav  # 提取的音频文件
```

## 🔧 配置参数位置

### 后端配置文件
**文件**: `backend/.env`
```env
# 数据库配置
DATABASE_URL=sqlite:///./pervis_director.db

# 素材存储配置
ASSET_ROOT=./assets
UPLOAD_MAX_SIZE=200MB
PROXY_QUALITY=720p
THUMBNAIL_SIZE=320x180

# AI服务配置 (可选)
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### 前端配置文件
**文件**: `frontend/.env`
```env
# API连接配置
VITE_API_URL=http://localhost:8000

# 上传限制配置
VITE_MAX_FILE_SIZE=200MB
VITE_SUPPORTED_FORMATS=mp4,mov,avi,mkv,txt,jpg,png
```

### 数据库连接配置
**文件**: `backend/database.py`
```python
# 数据库URL配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")

# SQLite连接配置
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
```

## 📁 素材处理流程

### 1. 上传流程
```
用户上传 → 临时存储 → 生成asset_id → 移动到originals/ → 更新数据库
```

### 2. 处理流程
```
原始文件 → 音频提取(audio/) → 代理生成(proxies/) → 缩略图生成(thumbnails/) → 向量化处理
```

### 3. 存储路径规则
- **原始文件**: `backend/assets/originals/asset_{id}.{ext}`
- **代理文件**: `backend/assets/proxies/asset_{id}_proxy.mp4`
- **缩略图**: `backend/assets/thumbnails/asset_{id}_thumb.jpg`
- **音频文件**: `backend/assets/audio/asset_{id}.wav`

## 🎯 素材访问API

### 获取素材列表
```http
GET /api/assets?project_id={project_id}
```

### 获取素材详情
```http
GET /api/assets/{asset_id}
```

### 上传新素材
```http
POST /api/assets/upload
Content-Type: multipart/form-data
```

### 获取素材文件
```http
GET /api/assets/{asset_id}/file/{type}
# type: original, proxy, thumbnail, audio
```

## 💾 存储容量分析

### 当前使用情况
- **数据库**: 327KB (元数据)
- **原始视频**: ~1.5GB (估算30个视频文件)
- **代理文件**: ~500MB (720p压缩)
- **音频文件**: ~150MB (WAV格式)
- **缩略图**: ~5MB (JPG格式)
- **总计**: ~2.2GB

### 扩展性考虑
- **单项目限制**: 建议<10GB
- **总系统容量**: 建议<100GB
- **数据库性能**: SQLite适用于<1万条记录
- **文件系统**: 支持无限扩展

## 🔍 数据查询示例

### 查看项目所有素材
```sql
SELECT a.id, a.filename, a.processing_status, a.created_at
FROM assets a 
WHERE a.project_id = 'your_project_id'
ORDER BY a.created_at DESC;
```

### 查看素材处理状态
```sql
SELECT 
    processing_status,
    COUNT(*) as count
FROM assets 
GROUP BY processing_status;
```

### 查看向量化进度
```sql
SELECT 
    a.filename,
    v.content_type,
    LENGTH(v.vector_data) as vector_size
FROM assets a
LEFT JOIN asset_vectors v ON a.id = v.asset_id
WHERE a.processing_status = 'completed';
```

## 🚀 性能优化建议

### 数据库优化
1. **索引优化**: 为project_id, asset_id添加索引
2. **查询优化**: 使用分页查询大量素材
3. **连接池**: 配置合适的连接池大小

### 文件系统优化
1. **目录结构**: 按日期或项目分层存储
2. **清理策略**: 定期清理临时文件
3. **备份策略**: 重要项目数据定期备份

### 缓存策略
1. **缩略图缓存**: 前端缓存常用缩略图
2. **元数据缓存**: Redis缓存热点查询
3. **代理文件**: CDN分发代理文件

## 📋 维护检查清单

### 日常维护
- [ ] 检查数据库文件大小
- [ ] 清理临时上传文件
- [ ] 验证文件完整性
- [ ] 监控存储空间使用

### 定期维护
- [ ] 数据库VACUUM操作
- [ ] 孤立文件清理
- [ ] 备份重要项目数据
- [ ] 性能指标分析

---

**文档版本**: v1.0  
**最后更新**: 2025-12-17  
**维护人员**: PreVis PRO开发团队