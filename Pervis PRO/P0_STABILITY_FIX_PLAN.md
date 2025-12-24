# P0 工程稳定性修复计划

**修复模式**: P0 Only - 工程稳定性 Sprint  
**原则**: 最小修改，不引入新框架，不更换技术栈  
**目标**: 解决阻塞问题，确保系统稳定运行

## 🎯 P0 问题清单与修复方案

### P0-1: 数据库同步阻塞问题

#### **问题定位**
- **文件名**: `backend/services/database_service.py`
- **类名**: `DatabaseService`
- **函数名**: 所有数据库操作函数
- **问题**: 所有数据库操作都是同步的，会阻塞FastAPI事件循环

#### **修改前问题**
```python
def create_project(self, project_data: ProjectCreate) -> Project:
    project = Project(...)
    self.db.add(project)
    self.db.commit()  # 同步阻塞调用
    self.db.refresh(project)
    return project
```

#### **修改后代码**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class DatabaseService:
    def __init__(self, db: Session):
        self.db = db
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def create_project(self, project_data: ProjectCreate) -> Project:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self._create_project_sync, 
            project_data
        )
    
    def _create_project_sync(self, project_data: ProjectCreate) -> Project:
        project = Project(...)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
```

#### **影响现有接口**: 否
- 保持相同的函数签名，只是改为async
- 调用方需要添加await关键字

---

### P0-2: Embedding生成阻塞问题

#### **问题定位**
- **文件名**: `backend/services/semantic_search.py`
- **类名**: `SemanticSearchEngine`
- **函数名**: `create_content_vectors()`
- **问题**: sentence-transformers的encode()是同步调用，会阻塞

#### **修改前问题**
```python
async def create_content_vectors(self, asset_id: str, segments: List[Dict]) -> bool:
    for segment in segments:
        # 同步阻塞调用
        vector = self.embedding_model.encode([text_content])[0]
        vector_json = json.dumps(vector.tolist())
```

#### **修改后代码**
```python
async def create_content_vectors(self, asset_id: str, segments: List[Dict]) -> bool:
    for segment in segments:
        text_content = self._build_segment_text(segment)
        if text_content.strip():
            # 异步执行embedding生成
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(
                None, 
                self._encode_text_sync, 
                text_content
            )
            vector_json = json.dumps(vector.tolist())
            # 存储向量...

def _encode_text_sync(self, text: str):
    """同步的embedding生成，在线程池中执行"""
    return self.embedding_model.encode([text])[0]
```

#### **影响现有接口**: 否
- 函数签名保持不变
- 内部实现改为异步，不影响外部调用

---

### P0-3: 向量维度不校验问题

#### **问题定位**
- **文件名**: `backend/services/semantic_search.py`
- **类名**: `SemanticSearchEngine`
- **函数名**: `create_content_vectors()`, `_search_similar_vectors()`
- **问题**: 没有校验向量维度，可能导致维度不一致错误

#### **修改前问题**
```python
# 生成向量时没有维度校验
vector = self.embedding_model.encode([text_content])[0]
vector_json = json.dumps(vector.tolist())

# 搜索时没有维度校验
stored_vector = np.array(json.loads(vector_record.vector_data))
similarity = self._cosine_similarity(query_vector, stored_vector)
```

#### **修改后代码**
```python
class SemanticSearchEngine:
    EXPECTED_VECTOR_DIM = 384  # all-MiniLM-L6-v2的标准维度
    
    def _validate_vector_dimension(self, vector) -> bool:
        """校验向量维度"""
        if len(vector) != self.EXPECTED_VECTOR_DIM:
            logger.error(f"向量维度错误: 期望{self.EXPECTED_VECTOR_DIM}, 实际{len(vector)}")
            return False
        return True
    
    async def create_content_vectors(self, asset_id: str, segments: List[Dict]) -> bool:
        for segment in segments:
            # ... 生成向量 ...
            vector = await loop.run_in_executor(None, self._encode_text_sync, text_content)
            
            # 校验维度
            if not self._validate_vector_dimension(vector):
                logger.warning(f"跳过维度错误的向量: {asset_id}")
                continue
                
            vector_json = json.dumps(vector.tolist())
            # ... 存储向量 ...
    
    def _search_similar_vectors(self, query_vector, fuzziness: float, limit: int):
        # 校验查询向量维度
        if not self._validate_vector_dimension(query_vector):
            logger.error("查询向量维度错误")
            return []
            
        for vector_record in all_vectors:
            try:
                stored_vector = np.array(json.loads(vector_record.vector_data))
                
                # 校验存储向量维度
                if not self._validate_vector_dimension(stored_vector):
                    logger.warning(f"跳过维度错误的存储向量: {vector_record.id}")
                    continue
                    
                similarity = self._cosine_similarity(query_vector, stored_vector)
                # ... 处理相似度 ...
```

#### **影响现有接口**: 否
- 只是内部添加校验逻辑
- 对外接口保持不变

---

### P0-4: 轮询机制不统一问题

#### **问题定位**
- **文件名**: `frontend/services/apiClient.ts`
- **函数名**: `analyzeVideoContent()`, 需要新增统一轮询函数
- **问题**: 轮询逻辑分散，没有统一管理，缺少指数退避

#### **修改前问题**
```typescript
// 只在analyzeVideoContent中有轮询，逻辑分散
while (attempts < maxAttempts) {
  await new Promise(resolve => setTimeout(resolve, 3000)); // 固定3秒
  const status = await getAssetStatus(assetId);
  // ... 处理状态 ...
}
```

#### **修改后代码**
```typescript
// 在apiClient.ts中添加统一轮询函数
interface PollingOptions {
  maxAttempts?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
}

/**
 * 统一的状态轮询函数
 */
export const pollAssetStatus = async (
  assetId: string,
  options: PollingOptions = {}
): Promise<AssetStatus> => {
  const {
    maxAttempts = 20,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 1.5
  } = options;

  let attempts = 0;
  let delay = initialDelay;

  while (attempts < maxAttempts) {
    try {
      const status = await getAssetStatus(assetId);
      
      // 如果处理完成或出错，直接返回
      if (status.status === 'completed' || status.status === 'error') {
        return status;
      }
      
      // 如果还在处理中，等待后继续轮询
      if (attempts < maxAttempts - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // 指数退避，但不超过最大延迟
        delay = Math.min(delay * backoffFactor, maxDelay);
      }
      
      attempts++;
      
    } catch (error) {
      console.error(`轮询第${attempts + 1}次失败:`, error);
      attempts++;
      
      if (attempts >= maxAttempts) {
        throw new Error(`轮询失败，已重试${maxAttempts}次`);
      }
      
      // 出错时也要等待
      await new Promise(resolve => setTimeout(resolve, delay));
      delay = Math.min(delay * backoffFactor, maxDelay);
    }
  }
  
  throw new Error(`轮询超时，已尝试${maxAttempts}次`);
};

// 修改analyzeVideoContent使用统一轮询
export const analyzeVideoContent = async (
  fileBlob: Blob, 
  filename: string
): Promise<VideoMetadata> => {
  try {
    // 1. 上传文件
    const file = new File([fileBlob], filename, { type: fileBlob.type });
    const uploadResponse = await uploadFile(file);
    
    if (!uploadResponse.asset_id) {
      throw new Error('文件上传失败');
    }

    // 2. 使用统一轮询函数
    const finalStatus = await pollAssetStatus(uploadResponse.asset_id, {
      maxAttempts: 30,
      initialDelay: 2000,
      maxDelay: 8000,
      backoffFactor: 1.3
    });

    if (finalStatus.status === 'error') {
      throw new Error(finalStatus.error_message || '处理失败');
    }

    // 3. 返回处理结果
    return {
      // ... 构建VideoMetadata ...
    };

  } catch (error) {
    console.error('视频分析失败:', error);
    throw error;
  }
};
```

#### **影响现有接口**: 否
- 新增统一轮询函数，不影响现有接口
- 现有函数内部使用新的轮询逻辑，外部调用不变

---

## 📋 P0 修复 Task List

### Task 1: 修复数据库同步阻塞
- **文件**: `backend/services/database_service.py`
- **操作**: 将所有数据库操作函数改为async，使用ThreadPoolExecutor
- **预计时间**: 2小时
- **验证**: 所有API响应时间<100ms

### Task 2: 修复Embedding生成阻塞  
- **文件**: `backend/services/semantic_search.py`
- **操作**: 将embedding生成改为异步执行
- **预计时间**: 1小时
- **验证**: 向量生成不阻塞API响应

### Task 3: 添加向量维度校验
- **文件**: `backend/services/semantic_search.py`
- **操作**: 添加384维度校验逻辑
- **预计时间**: 1小时
- **验证**: 维度错误时有日志警告，不会崩溃

### Task 4: 统一轮询机制
- **文件**: `frontend/services/apiClient.ts`
- **操作**: 添加统一轮询函数，实现指数退避
- **预计时间**: 1.5小时
- **验证**: 轮询间隔递增，减少API调用次数

### Task 5: 更新函数调用
- **文件**: 所有调用DatabaseService的文件
- **操作**: 添加await关键字
- **预计时间**: 1小时
- **验证**: 所有API正常工作

---

## 🎯 修复完成后的重新Sanity Check预期结果

### P0 并发与阻塞
- ✅ **数据库操作**: 全部异步化，不再阻塞事件循环
- ✅ **Embedding生成**: 异步执行，不阻塞API响应
- ✅ **FFmpeg/Whisper**: 保持现有正确的异步实现

### P0 状态闭环
- ✅ **状态接口**: 保持现有完整实现
- ✅ **轮询机制**: 统一管理，指数退避，减少API压力

### P0 向量一致性
- ✅ **维度校验**: 384维度强制校验，错误时跳过并记录日志
- ✅ **数据一致性**: 避免维度不匹配导致的计算错误

### P1 片段级检索
- ✅ **保持现有**: 不修改，已经正确实现

### TB 素材分层
- ✅ **保持现有**: 不修改，已经正确实现

### 预期Sanity Check结果
- **结论**: ✅ **PASS**
- **P0问题**: 全部解决
- **系统稳定性**: 生产就绪
- **性能**: API响应时间显著改善
- **可靠性**: 向量处理更加稳定

---

**修复原则**: 最小化修改，保持接口兼容，专注稳定性  
**总预计时间**: 6.5小时  
**验证标准**: 所有P0问题解决，系统通过Sanity Check