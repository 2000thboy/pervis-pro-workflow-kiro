# 设计文档

## 概述

本设计文档描述如何修复 Pervis PRO 前端中所有返回 Mock 数据的 AI 功能，将其替换为真实的后端 AI API 调用。系统采用双后端架构，支持 Gemini API（云端）和 Ollama（本地）两种 AI 服务。

## 架构

### 整体架构图

```mermaid
graph TB
    subgraph Frontend["前端 (React)"]
        GS[geminiService.ts]
        AC[apiClient.ts]
        UI[UI Components]
    end
    
    subgraph Backend["后端 (FastAPI)"]
        API[API Routes]
        LP[LLMProvider]
        GC[GeminiClient]
        OP[OllamaProvider]
    end
    
    subgraph External["外部服务"]
        GEMINI[Gemini API]
        OLLAMA[Ollama Server]
    end
    
    UI --> GS
    GS --> AC
    AC -->|HTTP| API
    API --> LP
    LP -->|gemini| GC
    LP -->|local| OP
    GC --> GEMINI
    OP --> OLLAMA
```

### 数据流

```mermaid
sequenceDiagram
    participant UI as 前端UI
    participant GS as geminiService
    participant AC as apiClient
    participant API as 后端API
    participant LP as LLMProvider
    participant AI as AI服务(Gemini/Ollama)
    
    UI->>GS: 调用AI功能
    GS->>AC: 转发请求
    AC->>API: HTTP POST
    API->>LP: 获取Provider
    LP->>AI: 调用AI
    AI-->>LP: AI响应
    LP-->>API: 处理结果
    API-->>AC: JSON响应
    AC-->>GS: 解析数据
    GS-->>UI: 返回结果
```

## 组件和接口

### 1. 环境配置 (.env)

```properties
# AI 服务配置
GEMINI_API_KEY=AIzaSyD1wZksttq-FEA24vKFC5p-rjnzsPIttfc
LLM_PROVIDER=gemini  # 可选: gemini, local

# Ollama 本地模型配置 (当 LLM_PROVIDER=local 时使用)
OLLAMA_BASE_URL=http://localhost:11434/v1
LOCAL_MODEL_NAME=qwen2.5:14b
```

### 2. 后端 LLM Provider 接口

```python
class LLMProvider(ABC):
    """LLM 提供者抽象基类"""
    
    @abstractmethod
    async def analyze_script(self, script_text: str, mode: str) -> Dict[str, Any]:
        """剧本分析"""
        pass
    
    @abstractmethod
    async def generate_visual_tags(self, visual_keywords: List[str]) -> Dict[str, List[str]]:
        """生成视觉标签"""
        pass
    
    @abstractmethod
    async def generate_beat_tags(self, content: str) -> Dict[str, Any]:
        """生成 Beat 标签"""
        pass
    
    @abstractmethod
    async def generate_asset_description(self, filename: str, metadata: Dict) -> str:
        """生成资产描述"""
        pass
    
    @abstractmethod
    async def analyze_rough_cut(self, script_content: str, video_tags: Dict) -> Dict[str, Any]:
        """AI 粗剪分析"""
        pass
```

### 3. 前端 API 客户端接口

```typescript
// apiClient.ts 新增/修改的接口

/**
 * 重新生成 Beat 标签 - 调用真实 AI
 */
export const regenerateBeatTags = async (content: string): Promise<TagSchema> => {
  return await apiRequest<TagSchema>('/api/ai/generate-tags', {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
};

/**
 * 生成资产描述 - 调用真实 AI
 */
export const generateAssetDescription = async (
  assetId: string,
  filename: string
): Promise<string> => {
  const response = await apiRequest<{ description: string }>(
    '/api/ai/generate-description',
    {
      method: 'POST',
      body: JSON.stringify({ asset_id: assetId, filename }),
    }
  );
  return response.description;
};

/**
 * AI 粗剪分析 - 调用真实 AI
 */
export const performAIRoughCut = async (
  scriptContent: string,
  videoTags: VideoMetadata
): Promise<RoughCutResult> => {
  return await apiRequest<RoughCutResult>('/api/ai/rough-cut', {
    method: 'POST',
    body: JSON.stringify({
      script_content: scriptContent,
      video_tags: videoTags,
    }),
  });
};
```

### 4. 后端 API 路由

```python
# 新增 AI 相关路由

@router.post("/api/ai/generate-tags")
async def generate_tags(request: GenerateTagsRequest):
    """生成 Beat 标签"""
    provider = get_llm_provider()
    result = await provider.generate_beat_tags(request.content)
    return result

@router.post("/api/ai/generate-description")
async def generate_description(request: GenerateDescriptionRequest):
    """生成资产描述"""
    provider = get_llm_provider()
    description = await provider.generate_asset_description(
        request.filename, 
        request.metadata
    )
    return {"description": description}

@router.post("/api/ai/rough-cut")
async def rough_cut_analysis(request: RoughCutRequest):
    """AI 粗剪分析"""
    provider = get_llm_provider()
    result = await provider.analyze_rough_cut(
        request.script_content,
        request.video_tags
    )
    return result
```

## 数据模型

### TagSchema (标签结构)

```typescript
interface TagSchema {
  scene_slug: string;      // 场景标识 (如 "INT. OFFICE - DAY")
  location_type: string;   // 位置类型 (INT/EXT)
  time_of_day: string;     // 时间 (DAY/NIGHT/DAWN/DUSK)
  primary_emotion: string; // 主要情绪
  key_action: string;      // 关键动作
  visual_notes: string;    // 视觉备注
  shot_type: string;       // 镜头类型 (WIDE/MEDIUM/CLOSE)
}
```

### RoughCutResult (粗剪结果)

```typescript
interface RoughCutResult {
  inPoint: number;     // 入点时间 (秒)
  outPoint: number;    // 出点时间 (秒)
  confidence: number;  // 置信度 (0-1)
  reason: string;      // AI 生成的匹配理由
}
```

### FeedbackRecord (反馈记录)

```typescript
interface FeedbackRecord {
  beat_id: string;
  asset_id: string;
  segment_id: string;
  action: 'accept' | 'reject';
  context: string;
  timestamp: string;
}
```

## 正确性属性

*正确性属性是系统在所有有效执行中应保持为真的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*

### Property 1: 无 Mock 数据返回

*对于任何* AI 功能调用（analyzeVideoContent、regenerateBeatTags、generateAssetDescription、performAIRoughCut），多次使用不同输入调用时，返回值应该有所不同，证明不是硬编码的 Mock 数据。

**Validates: Requirements 2.3, 3.3, 6.2**

### Property 2: API Key 配置验证

*对于任何* LLM_PROVIDER 配置为 "gemini" 的情况，如果 GEMINI_API_KEY 未设置或为空，系统应抛出 ValueError 异常。

**Validates: Requirements 1.3**

### Property 3: AI 粗剪输出完整性

*对于任何* AI 粗剪请求，返回结果必须包含 inPoint、outPoint、confidence 和 reason 四个字段，且 confidence 值在 0-1 范围内，inPoint < outPoint。

**Validates: Requirements 6.4, 6.5, 6.6**

### Property 4: 标签生成内容相关性

*对于任何* 两个不同的 Beat 内容输入，regenerateBeatTags 返回的标签应该有所不同，证明标签是基于内容生成的。

**Validates: Requirements 3.2**

### Property 5: 反馈记录持久化

*对于任何* 反馈记录请求，调用 recordAssetFeedback 后，后端数据库应包含该反馈记录。

**Validates: Requirements 5.2**

### Property 6: LLM Provider 切换

*对于任何* LLM_PROVIDER 配置值，系统应返回对应的 Provider 实例（gemini 返回 GeminiProvider，local 返回 OllamaProvider）。

**Validates: Requirements 7.1**

## 错误处理

### 错误类型

| 错误代码 | 描述 | 处理方式 |
|---------|------|---------|
| `CONFIG_ERROR` | API Key 未配置 | 抛出 ValueError，提示配置 |
| `CONNECTION_FAILED` | AI 服务连接失败 | 返回错误信息，建议检查网络 |
| `JSON_PARSE_ERROR` | AI 返回格式错误 | 重试最多 3 次 |
| `AI_SERVICE_ERROR` | AI 服务内部错误 | 返回错误信息，支持重试 |

### 错误响应格式

```json
{
  "status": "error",
  "error_code": "CONNECTION_FAILED",
  "message": "无法连接到 AI 服务",
  "details": "Connection refused",
  "retryable": true,
  "retry": {
    "supported": true,
    "suggested_after_seconds": 2,
    "max_attempts": 3
  }
}
```

## 测试策略

### 单元测试

- 测试 LLM Provider 工厂函数的配置切换
- 测试错误处理逻辑
- 测试数据格式转换

### 属性测试

- 使用 Hypothesis 库进行属性测试
- 每个属性测试配置 `@settings(max_examples=100, deadline=None)`
- 验证无 Mock 数据、输出完整性等属性

### 集成测试

- 测试前端到后端的完整调用链
- 测试 Gemini API 连接（需要真实 API Key）
- 测试 Ollama 本地模型连接（需要 Ollama 服务运行）

### 测试配置

```python
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
```
