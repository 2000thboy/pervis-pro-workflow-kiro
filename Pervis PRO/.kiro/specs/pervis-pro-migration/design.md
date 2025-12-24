# Pervis PRO Migration Design Document

## Overview

Pervis PRO是一个专业的导演工作台系统，为导演提供从剧本到粗剪的完整创作流程支持。系统集成AI能力，通过理解剧本内容和素材特征，为导演提供智能化的创作辅助和素材推荐。

**导演工作台核心功能：**
- **剧本工作台** - 剧本导入、AI分析、Beat生成、角色管理
- **素材工作台** - 视频上传、AI标签、预处理管道、库管理  
- **创意工作台** - Beat可视化、素材关联、氛围构思、风格探索
- **预览工作台** - 粗剪时间线、效果验证、节奏调整、导出预览

**核心设计原则：**
- Beat和Segment都是"语义单元"，时间信息仅用于预览
- 推荐系统目标是"导演启发"，提供创意灵感而非确定答案
- 不做镜头级精确剪辑，不做AI自动成片，专注导演决策支持

**技术架构：**
- 前端：保持现有React UI设计，三个工作台界面无缝切换
- 后端：FastAPI + 4个核心模块，支持导演工作流的各个环节
- AI服务：Gemini Pro用于内容理解、创意启发、推荐解释
- 存储：PostgreSQL + pgvector，支持大规模素材的语义搜索

## Architecture

### 导演工作台系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                导演工作台前端 (React - 保持现有UI)                │
├─────────────────────────────────────────────────────────────────┤
│  剧本工作台          │  BeatBoard工作台     │  Timeline工作台      │
│  - 剧本导入分析      │  - Beat可视化组织    │  - 粗剪时间线        │
│  - Beat生成管理      │  - 素材关联构思      │  - 效果预览验证      │
│  - 角色场景提取      │  - 创意灵感探索      │  - 节奏调整优化      │
│  - AI分析结果       │  - 推荐素材展示      │  - 导出预览文件      │
└─────────────────────────────────────────────────────────────────┘
                                │
                         HTTP API (替换geminiService)
                                │
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  剧本处理模块        │  素材预处理模块      │  语义搜索模块        │
│  - Gemini剧本分析   │  - FFmpeg代理生成    │  - 向量相似度计算    │
│  - Beat语义提取     │  - Whisper音频转录   │  - 推荐结果排序      │
│  - 情绪标签生成     │  - Gemini视频标签    │  - 自然语言解释      │
├─────────────────────────────────────────────────────────────────┤
│  反馈收集模块        │  数据存储层          │  文件管理层          │
│  - 接受/拒绝记录    │  - PostgreSQL        │  - 原始视频存储      │
│  - 偏好学习预留     │  - pgvector向量库    │  - 代理文件生成      │
│  - 简单计数统计     │  - 标签元数据        │  - 本地文件组织      │
└─────────────────────────────────────────────────────────────────┘
                                │
                         AI服务调用 (仅后端)
                                │
┌─────────────────────────────────────────────────────────────────┐
│     Gemini Pro      │     FFmpeg        │   sentence-transformers │
│   - 剧本理解分析     │   - 视频代理生成   │   - 文本向量化          │
│   - 视频内容标签     │   - 音频提取      │   - 相似度搜索          │
│   - 推荐理由生成     │   - Whisper转录   │   - 语义匹配计算        │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Script Processing**: Frontend → API → AI Service → Database → Frontend
2. **Asset Upload**: Frontend → API → Background Tasks → FFmpeg/Whisper → Storage → Database
3. **Semantic Search**: Frontend → API → Vector DB → Ranking → Frontend
4. **Multi-Workbench Sync**: Frontend ↔ WebSocket ↔ API ↔ Database ↔ Other Clients

## 核心模块接口设计

### 1. 剧本处理模块 (ScriptProcessor)

```python
POST /api/script/analyze
输入: {
  "script_text": "主角在雨夜街头奔跑逃命",
  "mode": "parse",
  "title": "夜晚追逐戏"
}
输出: {
  "status": "success",
  "beats": [
    {
      "id": "beat_001",
      "content": "主角在雨夜街头奔跑逃命",
      "emotion_tags": ["紧张", "恐惧", "急迫"],
      "scene_tags": ["夜晚", "街道", "雨天"],
      "action_tags": ["奔跑", "逃跑", "追逐"],
      "cinematography_tags": ["手持摄影", "快速移动"]
    }
  ],
  "processing_time": 2.3
}
```

### 2. 素材预处理模块 (AssetProcessor)

```python
POST /api/assets/upload
输入: multipart/form-data (video file)
输出: {
  "asset_id": "asset_001",
  "status": "uploaded",
  "estimated_processing_time": 120
}

GET /api/assets/{asset_id}/status
输出: {
  "status": "completed",
  "progress": 100,
  "proxy_url": "/assets/proxies/asset_001_proxy.mp4",
  "segments": [
    {
      "id": "seg_001",
      "start_time": 0,
      "end_time": 15.5,
      "description": "紧张的城市夜景追逐",
      "tags": {
        "emotions": ["紧张", "刺激"],
        "scenes": ["城市", "夜晚", "街道"],
        "actions": ["追逐", "奔跑"],
        "cinematography": ["手持", "快速剪切"]
      }
    }
  ]
}
```

### 3. 语义搜索模块 (SemanticSearchEngine)

```python
POST /api/search/semantic
输入: {
  "beat_id": "beat_001",
  "query_tags": {
    "emotions": ["紧张", "恐惧"],
    "scenes": ["夜晚", "街道"],
    "actions": ["奔跑", "追逐"]
  },
  "fuzziness": 0.7,
  "limit": 5
}
输出: {
  "results": [
    {
      "asset_id": "asset_001",
      "segment_id": "seg_001",
      "match_score": 0.89,
      "match_reason": "该片段包含紧张的夜晚追逐氛围，与您的剧本Beat高度匹配",
      "preview_url": "/assets/proxies/asset_001_proxy.mp4#t=0,15.5",
      "tags_matched": ["紧张", "夜晚", "追逐", "奔跑"]
    }
  ],
  "total_matches": 3,
  "search_time": 0.45
}
```

### 4. 反馈收集模块 (FeedbackCollector)

```python
POST /api/feedback/record
输入: {
  "beat_id": "beat_001",
  "asset_id": "asset_001",
  "segment_id": "seg_001",
  "action": "accept",
  "context": "完美匹配了紧张追逐的氛围"
}
输出: {
  "status": "recorded",
  "feedback_id": "fb_001"
}
```

### 前端组件更新

#### 替换geminiService.ts → apiClient.ts
```typescript
// 新的API客户端，完全替换前端AI调用
class ApiClient {
  async analyzeScript(scriptData: ScriptRequest): Promise<ScriptResponse>
  async uploadAsset(file: File): Promise<UploadResponse>
  async getAssetStatus(assetId: string): Promise<AssetStatus>
  async searchSemantic(query: SearchQuery): Promise<SearchResults>
  async recordFeedback(feedback: FeedbackData): Promise<void>
}
```

#### 核心UI组件（保持现有设计）
- **ScriptIngestion**: 剧本上传，调用/api/script/analyze
- **BeatCard**: 显示Beat和标签，点击触发搜索
- **SearchResults**: 显示推荐视频，包含匹配理由
- **VideoPreview**: 播放代理文件，接受/拒绝按钮

## Data Models

### Core Entities

```typescript
interface Project {
  id: string;
  title: string;
  logline?: string;
  synopsis?: string;
  scriptRaw: string;
  beats: Beat[];
  characters: Character[];
  library: ProjectAsset[];
  specs: ProjectSpecs;
  createdAt: number;
  currentStage: WorkflowStage;
}

interface Beat {
  id: string;
  order: number;
  content: string;
  tags: TagSchema;
  candidates: Asset[];
  mainAssetId?: string;
  duration: number;
  userNotes?: string;
  assets: Asset[];
}

interface ProjectAsset {
  id: string;
  projectId: string;
  mediaUrl: string;
  thumbnailUrl: string;
  filename: string;
  mimeType: string;
  source: 'upload' | 'external' | 'generated' | 'local';
  tags?: Record<string, any>;
  metadata?: VideoMetadata;
  createdAt: number;
}

interface VideoMetadata {
  processingStatus: ProcessingStatus;
  globalTags?: VideoGlobalTags;
  timeLog?: VideoLogEntry[];
  assetTrustScore: number;
  feedbackHistory: FeedbackRecord[];
}
```

### Database Schema

```sql
-- Projects and Beats
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  logline TEXT,
  synopsis TEXT,
  script_raw TEXT,
  characters JSONB,
  specs JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  current_stage VARCHAR(50)
);

CREATE TABLE beats (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  order_index INTEGER,
  content TEXT,
  tags JSONB,
  duration FLOAT,
  user_notes TEXT,
  main_asset_id UUID
);

-- Assets and Processing
CREATE TABLE project_assets (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  filename VARCHAR(255),
  mime_type VARCHAR(100),
  source VARCHAR(50),
  tags JSONB,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Vector Storage (pgvector)
CREATE TABLE asset_vectors (
  id UUID PRIMARY KEY,
  asset_id UUID REFERENCES project_assets(id),
  vector vector(384),  -- MiniLM-L6-v2 dimension
  content_type VARCHAR(50), -- 'transcript', 'description', 'tags'
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON asset_vectors USING ivfflat (vector vector_cosine_ops);
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: AI Processing Security
*For any* AI processing request, the system should route through backend APIs only, never exposing API keys in frontend code or browser environments
**Validates: Requirements 1.1, 1.5**

### Property 2: JSON Response Validity  
*For any* AI API response, the backend should return strictly valid JSON with proper error structures when parsing fails
**Validates: Requirements 1.2, 1.3**

### Property 3: Video Processing Pipeline Completeness
*For any* uploaded video file, the system should trigger all required preprocessing steps (proxy generation, frame extraction, transcription) and update status accordingly
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 4: Semantic Search Consistency
*For any* search query, the Video RAG system should return ranked results based on vector similarity with consistent scoring and time segment information
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: Multi-Workbench Synchronization
*For any* data modification in one workbench, all other workbenches should reflect the changes in real-time without data loss or conflicts
**Validates: Requirements 4.1, 4.2, 4.3**

### Property 6: Timeline Editing Precision
*For any* timeline operation (reordering, trimming, asset replacement), the system should maintain frame-accurate timing and proper asset references
**Validates: Requirements 5.1, 5.2, 5.4**

### Property 7: Export Format Compatibility
*For any* timeline export, the generated XML/EDL files should be valid and openable in Premiere Pro with correct media references
**Validates: Requirements 5.5**

### Property 8: UI Design Consistency
*For any* UI component or interaction, the visual styling should match existing dark theme, typography, and layout patterns
**Validates: Requirements 6.1, 6.2, 6.3**

### Property 9: Error Handling Robustness
*For any* system error (video processing, AI calls, database operations), the system should log detailed information and provide user-friendly error messages
**Validates: Requirements 8.1, 8.2, 8.3**

### Property 10: Performance Scalability
*For any* MVP-scale dataset (50-100 videos), the system should complete processing within specified time limits and maintain responsive search performance
**Validates: Requirements 9.1, 9.4, 9.5**

### Property 11: Model Configuration Flexibility
*For any* AI processing task, the system should support switching between cloud APIs and local LLM deployments without changing core functionality
**Validates: Requirements 10.1, 10.3, 10.4**

### Property 12: Frontend Migration Completeness
*For any* frontend AI operation, the system should route through backend APIs only, with no API keys or direct AI calls remaining in frontend code
**Validates: Requirements 11.1, 11.2, 11.5**

### Property 13: Audio Transcription Accuracy
*For any* uploaded video with audio content, the Whisper transcription should produce time-aligned text with measurable accuracy and confidence scores
**Validates: Requirements 12.1, 12.2, 12.5**

### Property 14: Multi-modal Search Consistency
*For any* search query combining text and visual elements, the system should return ranked results that match both semantic meaning and visual characteristics
**Validates: Requirements 13.3, 13.4, 13.5**

### Property 15: Batch Processing Scalability
*For any* batch upload operation, the system should maintain consistent processing speed and resource utilization regardless of queue size
**Validates: Requirements 14.1, 14.3, 14.5**

## Error Handling

### Error Classification

1. **User Errors**: Invalid input, missing files, configuration issues
2. **System Errors**: Database failures, network issues, resource exhaustion
3. **Processing Errors**: FFmpeg failures, AI API timeouts, transcription errors
4. **Integration Errors**: Model loading failures, external service unavailability

### Error Response Format

```typescript
interface ErrorResponse {
  status: 'error';
  error_code: string;
  message: string;
  details?: any;
  trace_id: string;
  timestamp: number;
  recovery_suggestions?: string[];
}
```

### Recovery Strategies

- **Retry Logic**: Exponential backoff for transient failures
- **Graceful Degradation**: Fallback to cached results or simplified processing
- **User Notification**: Clear error messages with actionable guidance
- **State Recovery**: Transaction rollback and data consistency maintenance

## Testing Strategy

### Unit Testing
- Component isolation testing for React workbenches
- API endpoint testing with mock dependencies
- Database operation testing with test fixtures
- Video processing pipeline testing with sample files

### Property-Based Testing
- JSON validation across all API responses
- Vector search consistency with random queries
- Multi-workbench sync with concurrent operations
- Timeline export validation with various configurations
- Error handling robustness with fault injection

### Integration Testing
- End-to-end workflow testing from script to export
- Multi-client synchronization testing
- Video processing pipeline with real media files
- AI model switching and fallback scenarios

### Performance Testing
- Load testing with MVP-scale datasets
- Memory usage monitoring during video processing
- Search response time validation
- Concurrent user simulation

### Testing Framework Selection
- **Frontend**: Jest + React Testing Library for component testing
- **Backend**: pytest for API and service testing
- **Property Testing**: Hypothesis (Python) for property-based tests
- **Integration**: Playwright for end-to-end testing
- **Performance**: Locust for load testing

The testing strategy ensures comprehensive coverage with property-based tests running minimum 100 iterations each, tagged with explicit references to design document properties using the format: **Feature: pervis-pro-migration, Property {number}: {property_text}**