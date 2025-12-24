# PreVis PRO Sanity Check 自检报告

**检查时间**: 2025年12月17日  
**检查范围**: P0并发阻塞、状态闭环、向量一致性、片段级检索、TB素材分层  
**检查方法**: 代码审查 + 架构分析

## 🔍 P0 并发与阻塞检查

### 1) FFmpeg/Whisper/Embedding 后台任务执行情况

#### ✅ **已正确使用BackgroundTasks的函数**:
- **文件**: `backend/routers/assets.py`
- **函数**: `upload_asset()`
- **路由**: `POST /api/assets/upload`
- **实现**: 
```python
background_tasks.add_task(
    asset_processor.process_uploaded_file,
    file, project_id
)
```

#### ❌ **存在阻塞问题的函数**:

**1. FFmpeg处理 - 部分异步**
- **文件**: `backend/services/video_processor.py`
- **函数**: `_generate_proxy()`, `_generate_thumbnail()`, `_extract_audio()`
- **问题**: 使用了`asyncio.create_subprocess_exec()`，这是正确的异步实现
- **状态**: ✅ 正确实现

**2. Whisper转录 - 存在阻塞**
- **文件**: `backend/services/audio_transcriber.py`
- **函数**: `transcribe_audio()` → `_transcribe_sync()`
- **问题**: 
```python
result = await loop.run_in_executor(None, self._transcribe_sync, audio_file_path)
```
- **状态**: ✅ 正确使用线程池执行器

**3. Embedding生成 - 存在阻塞**
- **文件**: `backend/services/semantic_search.py`
- **函数**: `create_content_vectors()`
- **问题**: 
```python
vector = self.embedding_model.encode([text_content])[0]  # 同步调用
```
- **状态**: ❌ **阻塞问题** - 未使用异步执行

### 2) FastAPI路由阻塞代码检查

#### ❌ **存在阻塞的路由**:

**1. 数据库操作阻塞**
- **文件**: `backend/services/database_service.py`
- **问题**: 所有数据库操作都是同步的
```python
def create_project(self, project_data: ProjectCreate) -> Project:
    # 同步数据库操作
    self.db.add(project)
    self.db.commit()  # 阻塞调用
```
- **影响路由**: 所有使用`DatabaseService`的路由
- **状态**: ❌ **严重阻塞问题**

**2. 搜索引擎阻塞**
- **文件**: `backend/services/semantic_search.py`
- **函数**: `search_by_beat()`
- **问题**: 向量计算和数据库查询都是同步的
- **状态**: ❌ **阻塞问题**

## 🔄 P0 状态闭环检查

### 3) 资产状态接口检查

#### ✅ **状态接口存在**:
- **文件**: `backend/routers/assets.py`
- **接口**: `GET /api/assets/{asset_id}/status`
- **返回字段**: 
```python
AssetStatusResponse(
    status=ProcessingStatus,     # ✅ 有
    progress=int,               # ✅ 有  
    error_message=str          # ✅ 有
)
```

#### ✅ **状态字段完整**:
- `status`: uploaded/processing/completed/error
- `progress`: 0-100进度百分比
- `error_message`: 错误信息
- `proxy_url`: 代理文件URL
- `thumbnail_url`: 缩略图URL
- `segments`: 片段信息

### 4) 前端轮询机制检查

#### ✅ **轮询机制存在**:
- **文件**: `frontend/services/apiClient.ts`
- **函数**: `analyzeVideoContent()`
- **实现**:
```typescript
// 2. 轮询处理状态
while (attempts < maxAttempts) {
  await new Promise(resolve => setTimeout(resolve, 3000)); // 等待3秒
  const status = await getAssetStatus(assetId);
  // 检查状态并处理
}
```

#### ❌ **轮询问题**:
- **问题1**: 只在`analyzeVideoContent`中有轮询，其他上传场景没有
- **问题2**: 轮询间隔固定3秒，没有指数退避
- **问题3**: 没有全局的状态管理机制

## 🧮 P0 向量一致性检查

### 5) Embedding模型维度检查

#### ❌ **向量维度不一致**:

**Embedding模型输出维度**:
- **文件**: `backend/services/semantic_search.py`
- **模型**: `SentenceTransformer('all-MiniLM-L6-v2')`
- **维度**: **384维** (all-MiniLM-L6-v2的标准维度)

**数据库存储维度**:
- **文件**: `backend/database.py`
- **字段**: `AssetVector.vector_data = Column(Text)`
- **存储**: JSON字符串，无维度限制
- **问题**: ❌ **没有维度校验**

**维度校验位置**:
- **检查结果**: ❌ **完全没有len(vector)校验**
- **风险**: 不同维度向量混存会导致搜索错误

### 6) 向量距离度量检查

#### ❌ **使用SQLite，不是pgvector**:
- **当前数据库**: SQLite
- **向量存储**: JSON Text字段
- **距离计算**: 
  - **文件**: `backend/services/semantic_search.py`
  - **函数**: `_cosine_similarity()`
  - **度量**: 余弦相似度
  - **实现**: NumPy计算，非数据库索引

**问题**: 没有使用pgvector，无法利用数据库向量索引优化

## 🎯 P1 片段级检索检查

### 7) 搜索结果格式检查

#### ✅ **片段级返回格式正确**:
- **文件**: `backend/routers/search.py`
- **返回格式**:
```python
SearchResult(
    asset_id=rec["asset_id"],           # ✅ 有
    segment_id=segment["id"],           # ✅ 有
    match_score=rec["similarity_score"], # ✅ 有
    match_reason=rec["reason"],         # ✅ 有
    preview_url=f"{rec['proxy_url']}#t={segment['start_time']},{segment['end_time']}", # ✅ 有时间戳
)
```

#### ✅ **包含必需字段**:
- `segment_id`: ✅ 有
- `start_time`: ✅ 有 (在preview_url中)
- `end_time`: ✅ 有 (在preview_url中)  
- `reason`: ✅ 有 (match_reason字段)

## 📁 TB 素材分层检查

### 8) 目录结构检查

#### ✅ **真实目录结构**:
```
backend/assets/
├── 【免费更新+V Lingshao2605】01-10.mp4  # 原始视频 (30个)
├── video_011-030.mp4                    # 原始视频 (20个)
├── originals/          # 原始文件 (53个处理后文件)
│   ├── asset_[id].mp4  # 原始视频
│   ├── asset_[id].txt  # 文本文件
│   └── asset_[id].jpg  # 图片文件
├── proxies/            # 代理文件 (49个MP4)
│   └── asset_[id]_proxy.mp4
├── thumbnails/         # 缩略图 (50个JPG)
│   └── asset_[id]_thumb.jpg  
└── audio/              # 音频文件 (50个WAV)
    └── asset_[id].wav
```

#### ✅ **写入步骤确认**:

**1. 原始文件写入**:
- **文件**: `backend/services/video_processor.py`
- **函数**: `_move_file()`
- **目标**: `{asset_root}/originals/{asset_id}.mp4`

**2. 代理文件生成**:
- **函数**: `_generate_proxy()`
- **目标**: `{asset_root}/proxies/{asset_id}_proxy.mp4`

**3. 缩略图生成**:
- **函数**: `_generate_thumbnail()`
- **目标**: `{asset_root}/thumbnails/{asset_id}_thumb.jpg`

**4. 音频提取**:
- **函数**: `_extract_audio()`
- **目标**: `{asset_root}/audio/{asset_id}.wav`

**5. 向量数据**:
- **存储**: SQLite数据库 `asset_vectors`表
- **不写入文件系统**

---

## 📊 Sanity Check 结论

### 🔴 **结论: FAIL**

### ❌ **关键失败项**:

#### P0 级别问题:
1. **数据库操作全部阻塞** - 所有路由都受影响
2. **Embedding生成阻塞** - 向量创建时阻塞
3. **向量维度无校验** - 数据一致性风险
4. **轮询机制不完整** - 只有部分场景有轮询

#### P1 级别问题:
1. **使用SQLite而非pgvector** - 无向量索引优化
2. **轮询策略简陋** - 固定间隔，无指数退避

---

## 🛠️ 修复任务列表

### P0 优先级 (立即修复)

#### **P0-1: 数据库操作异步化**
- **文件**: `backend/services/database_service.py`
- **修复**: 将所有同步数据库操作改为异步
- **方案**: 使用`databases`库或`asyncpg`
- **影响**: 所有API路由性能

#### **P0-2: Embedding生成异步化**
- **文件**: `backend/services/semantic_search.py`
- **函数**: `create_content_vectors()`
- **修复**: 
```python
# 修复前
vector = self.embedding_model.encode([text_content])[0]

# 修复后  
loop = asyncio.get_event_loop()
vector = await loop.run_in_executor(None, self.embedding_model.encode, [text_content])
vector = vector[0]
```

#### **P0-3: 向量维度校验**
- **文件**: `backend/services/semantic_search.py`
- **修复**: 添加维度校验
```python
def validate_vector_dimension(self, vector):
    expected_dim = 384  # all-MiniLM-L6-v2
    if len(vector) != expected_dim:
        raise ValueError(f"向量维度错误: 期望{expected_dim}, 实际{len(vector)}")
```

#### **P0-4: 完善轮询机制**
- **文件**: `frontend/services/apiClient.ts`
- **修复**: 
  1. 添加全局状态轮询Hook
  2. 实现指数退避策略
  3. 添加WebSocket支持(可选)

### P1 优先级 (近期修复)

#### **P1-1: 迁移到PostgreSQL + pgvector**
- **修复**: 替换SQLite为PostgreSQL
- **添加**: pgvector扩展支持
- **优化**: 向量索引和距离计算

#### **P1-2: 优化轮询策略**
- **修复**: 指数退避算法
- **添加**: 智能轮询间隔调整
- **优化**: 减少不必要的API调用

### P2 优先级 (长期优化)

#### **P2-1: 添加WebSocket实时通信**
- **替代**: 轮询机制
- **实现**: 实时状态推送
- **优化**: 用户体验和性能

#### **P2-2: 向量数据库优化**
- **添加**: FAISS本地索引
- **优化**: 大规模向量搜索性能
- **实现**: 分层向量存储

---

**修复优先级**: P0 > P1 > P2  
**预计修复时间**: P0 (1-2天), P1 (3-5天), P2 (1-2周)  
**系统可用性**: 修复P0后可投入生产使用