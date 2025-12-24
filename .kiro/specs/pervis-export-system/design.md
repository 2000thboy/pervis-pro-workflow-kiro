# Design Document: Pervis PRO 导出系统

## Overview

本设计文档描述 Pervis PRO 导出系统的完整架构，覆盖三个工作流阶段的导出功能：
1. **Analysis 阶段** - 项目文档导出（PDF/DOCX）
2. **Board 阶段** - 故事板序列图片导出（PNG/JPG）
3. **Timeline 阶段** - 视频/音频导出（FFmpeg）+ NLE 工程导出（XML/EDL）

系统基于现有的后端服务架构进行扩展，复用 `DocumentExporter`、`ImageExporter`、`NLEExporter` 和 `RenderService`。

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                             │
├─────────────────────────────────────────────────────────────────────┤
│  StepAnalysis.tsx    StepBeatBoard.tsx    StepTimeline.tsx          │
│       │                    │                    │                    │
│  ExportDialog ─────────────┴────────────────────┘                   │
│  (统一导出对话框组件)                                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │ API Calls
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────┤
│  /api/export/project     - 项目文档导出                              │
│  /api/export/beatboard   - 故事板序列导出                            │
│  /api/export/timeline    - 时间线视频导出                            │
│  /api/export/nle         - NLE 工程导出                              │
│  /api/export/history     - 导出历史                                  │
│  /api/export/download    - 文件下载                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Services Layer                                  │
├─────────────────────────────────────────────────────────────────────┤
│  DocumentExporter    ImageExporter    RenderService    NLEExporter  │
│  (PDF/DOCX)          (PNG/JPG)        (FFmpeg)         (XML/EDL)    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Storage & Database                              │
├─────────────────────────────────────────────────────────────────────┤
│  exports/              - 导出文件存储目录                            │
│  ExportHistory         - 导出历史记录表                              │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. 前端组件

#### 1.1 ExportDialog 组件

统一的导出对话框组件，根据当前阶段显示不同的导出选项。

```typescript
interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  stage: 'analysis' | 'board' | 'timeline';
  projectId: string;
  scenes?: SceneGroup[];  // Board 阶段需要
  timelineId?: string;    // Timeline 阶段需要
}

interface ExportOptions {
  // Analysis 阶段
  projectExport?: {
    format: 'pdf' | 'docx';
    includeScript: boolean;
    includeCharacters: boolean;
    includeSceneOutline: boolean;
    includeBeatBreakdown: boolean;
    includeAIAnalysis: boolean;
  };
  
  // Board 阶段
  beatboardExport?: {
    format: 'png' | 'jpg';
    resolution: '1080p' | '4k' | 'custom';
    customWidth?: number;
    customHeight?: number;
    exportMode: 'all' | 'scenes' | 'beats';
    selectedSceneIds?: string[];
    selectedBeatIds?: string[];
    includeContactSheet: boolean;
    overlayInfo: boolean;
  };
  
  // Timeline 阶段
  timelineExport?: {
    type: 'video' | 'audio' | 'nle';
    // 视频选项
    videoFormat?: 'mp4' | 'mov' | 'webm';
    resolution?: '720p' | '1080p' | '2k' | '4k';
    framerate?: number;
    quality?: 'low' | 'medium' | 'high' | 'ultra';
    // 音频选项
    audioFormat?: 'wav' | 'mp3';
    audioBitrate?: number;
    // NLE 选项
    nleFormat?: 'xml' | 'edl';
  };
}
```

#### 1.2 ExportProgress 组件

显示导出进度的组件。

```typescript
interface ExportProgressProps {
  taskId: string;
  onComplete: (result: ExportResult) => void;
  onError: (error: string) => void;
}

interface ExportResult {
  exportId: string;
  filePath: string;
  fileSize: number;
  downloadUrl: string;
}
```

### 2. 后端 API 接口

#### 2.1 项目文档导出 API

```python
# POST /api/export/project
class ProjectExportRequest(BaseModel):
    project_id: str
    format: str  # pdf, docx
    include_script: bool = True
    include_characters: bool = True
    include_scene_outline: bool = True
    include_beat_breakdown: bool = True
    include_ai_analysis: bool = True
    include_metadata: bool = True

class ExportResponse(BaseModel):
    status: str
    export_id: str
    file_path: str
    file_size: int
    download_url: str
```

#### 2.2 故事板序列导出 API

```python
# POST /api/export/beatboard/sequence
class BeatboardSequenceExportRequest(BaseModel):
    project_id: str
    format: str  # png, jpg
    resolution: str  # 1080p, 4k, custom
    custom_width: Optional[int] = None
    custom_height: Optional[int] = None
    export_mode: str  # all, scenes, beats
    scene_ids: Optional[List[str]] = None
    beat_ids: Optional[List[str]] = None
    overlay_info: bool = True
    include_contact_sheet: bool = False

class BeatboardSequenceExportResponse(BaseModel):
    status: str
    export_id: str
    file_count: int
    total_size: int
    download_url: str  # ZIP 文件下载链接
```

#### 2.3 时间线视频导出 API

```python
# POST /api/export/timeline/video
class TimelineVideoExportRequest(BaseModel):
    timeline_id: str
    format: str  # mp4, mov, webm
    resolution: str  # 720p, 1080p, 2k, 4k
    framerate: int = 24
    quality: str = "high"
    bitrate: Optional[int] = None

# POST /api/export/timeline/audio
class TimelineAudioExportRequest(BaseModel):
    timeline_id: str
    format: str  # wav, mp3
    bitrate: int = 192
    sample_rate: int = 48000
```

#### 2.4 NLE 工程导出 API

```python
# POST /api/export/nle
class NLEExportRequest(BaseModel):
    project_id: str
    timeline_id: str
    format: str  # xml, edl
    frame_rate: str = "24"
    include_markers: bool = True
```

### 3. 服务层增强

#### 3.1 DocumentExporter 增强

扩展现有的 `DocumentExporter` 以支持完整项目文档导出：

```python
class DocumentExporter:
    async def export_project_document(
        self,
        project_id: str,
        format: str,
        options: ProjectExportOptions
    ) -> Dict[str, Any]:
        """导出完整项目文档"""
        # 1. 加载项目数据
        # 2. 加载角色数据
        # 3. 按场次组织 Beat 数据
        # 4. 生成 AI 分析报告
        # 5. 根据格式生成文档
        pass
```

#### 3.2 ImageExporter 增强

扩展现有的 `ImageExporter` 以支持按场次导出序列图片：

```python
class ImageExporter:
    async def export_beatboard_sequence(
        self,
        project_id: str,
        options: BeatboardExportOptions
    ) -> Dict[str, Any]:
        """按场次导出故事板序列"""
        # 1. 按场次分组 Beat
        # 2. 为每个 Beat 生成图片
        # 3. 叠加镜头信息
        # 4. 按场次创建文件夹
        # 5. 打包为 ZIP
        pass
    
    async def export_contact_sheet(
        self,
        project_id: str,
        options: ContactSheetOptions
    ) -> Dict[str, Any]:
        """导出联系表"""
        # 生成包含所有镜头缩略图的单页概览图
        pass
```

#### 3.3 RenderService 增强

扩展现有的 `RenderService` 以支持音频导出：

```python
class RenderService:
    async def export_audio(
        self,
        timeline_id: str,
        format: str,
        bitrate: int,
        sample_rate: int
    ) -> str:
        """导出时间线音频"""
        # 使用 FFmpeg 提取/合成音频
        pass
```

## 素材显示与渲染流程

### 素材存储架构

```
assets/
├── originals/          # 原始素材文件（高质量）
│   └── {asset_id}.{ext}
├── proxies/            # 代理文件（低分辨率，用于预览）
│   └── {asset_id}_proxy.mp4
└── thumbnails/         # 缩略图（用于列表显示）
    └── {asset_id}_thumb.jpg
```

### 存储位置策略（用户无感）

为了让用户无感使用，系统采用以下存储策略：

```
┌─────────────────────────────────────────────────────────────────────┐
│                      存储位置架构                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户可见目录（项目目录）                                            │
│  └── {project_folder}/                                               │
│      ├── exports/              # 用户导出的最终文件                  │
│      │   ├── documents/        # 项目文档                            │
│      │   ├── beatboards/       # 故事板图片                          │
│      │   └── videos/           # 渲染视频                            │
│      └── assets/               # 用户导入的原始素材                  │
│          └── {original_files}                                        │
│                                                                      │
│  系统隐藏目录（应用数据目录）                                        │
│  └── {app_data}/.pervis/                                             │
│      ├── cache/                # 缓存目录                            │
│      │   ├── thumbnails/       # 缩略图缓存                          │
│      │   └── proxies/          # 代理文件缓存                        │
│      ├── temp/                 # 临时文件（渲染中间产物）            │
│      │   └── render_{task_id}/ # 每个渲染任务的临时目录              │
│      └── db/                   # 数据库文件                          │
│          └── pervis.db         # SQLite 数据库                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 存储路径配置

```python
import os
from pathlib import Path

class StorageConfig:
    """存储配置 - 用户无感"""
    
    @staticmethod
    def get_app_data_dir() -> Path:
        """获取应用数据目录（隐藏）"""
        if os.name == 'nt':  # Windows
            base = Path(os.environ.get('LOCALAPPDATA', '~'))
        else:  # macOS/Linux
            base = Path.home() / '.local' / 'share'
        return base / '.pervis'
    
    @staticmethod
    def get_cache_dir() -> Path:
        """缓存目录 - 可安全删除"""
        return StorageConfig.get_app_data_dir() / 'cache'
    
    @staticmethod
    def get_temp_dir() -> Path:
        """临时目录 - 自动清理"""
        return StorageConfig.get_app_data_dir() / 'temp'
    
    @staticmethod
    def get_thumbnail_dir() -> Path:
        """缩略图目录"""
        return StorageConfig.get_cache_dir() / 'thumbnails'
    
    @staticmethod
    def get_proxy_dir() -> Path:
        """代理文件目录"""
        return StorageConfig.get_cache_dir() / 'proxies'
    
    @staticmethod
    def get_export_dir(project_path: str) -> Path:
        """导出目录 - 用户可见"""
        return Path(project_path) / 'exports'
```

### 元数据存储

```python
# 数据库表结构 - 存储素材元数据
class AssetMetadata(Base):
    __tablename__ = "asset_metadata"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, ForeignKey("assets.id"), unique=True)
    
    # 原始文件信息
    original_path = Column(String)           # 用户导入的原始路径
    original_hash = Column(String)           # 文件哈希（用于检测变更）
    
    # 缓存文件路径（相对于 cache 目录）
    thumbnail_path = Column(String)          # 缩略图相对路径
    proxy_path = Column(String)              # 代理文件相对路径
    
    # 缓存状态
    thumbnail_generated = Column(Boolean, default=False)
    proxy_generated = Column(Boolean, default=False)
    cache_version = Column(Integer, default=1)  # 缓存版本号
    
    # 时间戳
    created_at = Column(DateTime)
    last_accessed = Column(DateTime)         # 用于 LRU 清理
```

### 潜在问题与解决方案

| 问题 | 风险等级 | 解决方案 |
|------|---------|---------|
| **磁盘空间不足** | 高 | 1. 启动时检查可用空间<br>2. 缓存 LRU 自动清理<br>3. 导出前预估文件大小并提示 |
| **原始文件被移动/删除** | 高 | 1. 使用文件哈希检测变更<br>2. 提供"重新链接素材"功能<br>3. 导出前验证所有素材可用性 |
| **缓存文件损坏** | 中 | 1. 缓存版本号机制<br>2. 自动重新生成损坏的缓存<br>3. 提供"清除缓存"选项 |
| **并发渲染冲突** | 中 | 1. 每个任务使用独立临时目录<br>2. 文件锁机制<br>3. 任务队列管理 |
| **临时文件残留** | 低 | 1. 渲染完成后自动清理<br>2. 启动时清理孤立临时文件<br>3. 定期清理超过 24 小时的临时文件 |
| **跨平台路径问题** | 中 | 1. 使用 pathlib 处理路径<br>2. 数据库存储相对路径<br>3. 运行时动态拼接完整路径 |
| **网络盘/外部存储断开** | 高 | 1. 导入时复制到本地（可选）<br>2. 检测存储可用性<br>3. 提供离线模式提示 |

### 缓存管理策略

```python
class CacheManager:
    """缓存管理器"""
    
    MAX_CACHE_SIZE_GB = 10  # 最大缓存大小
    MAX_CACHE_AGE_DAYS = 30  # 最大缓存保留天数
    
    async def ensure_thumbnail(self, asset_id: str) -> str:
        """确保缩略图存在，不存在则生成"""
        metadata = self.get_metadata(asset_id)
        
        if metadata.thumbnail_generated:
            thumb_path = self.get_thumbnail_path(asset_id)
            if thumb_path.exists():
                # 更新访问时间
                self.update_last_accessed(asset_id)
                return str(thumb_path)
        
        # 生成缩略图
        return await self.generate_thumbnail(asset_id)
    
    async def ensure_proxy(self, asset_id: str) -> str:
        """确保代理文件存在，不存在则生成"""
        # 类似逻辑...
        pass
    
    async def cleanup_cache(self):
        """清理缓存 - LRU 策略"""
        # 1. 删除超过 MAX_CACHE_AGE_DAYS 未访问的文件
        # 2. 如果仍超过 MAX_CACHE_SIZE_GB，按 LRU 删除
        pass
    
    async def verify_asset_availability(self, asset_ids: List[str]) -> Dict[str, bool]:
        """验证素材可用性"""
        results = {}
        for asset_id in asset_ids:
            metadata = self.get_metadata(asset_id)
            if metadata and metadata.original_path:
                results[asset_id] = Path(metadata.original_path).exists()
            else:
                results[asset_id] = False
        return results
```

### 用户无感体验设计

1. **自动缓存生成**
   - 素材导入时自动在后台生成缩略图和代理文件
   - 使用任务队列，不阻塞用户操作

2. **智能预加载**
   - 预测用户可能访问的素材，提前生成缓存
   - 基于项目结构和用户行为模式

3. **透明的路径处理**
   - 前端只使用 URL（如 `/api/assets/{id}/thumbnail`）
   - 后端自动处理路径映射和缓存逻辑

4. **优雅的错误处理**
   - 缓存缺失时显示占位图，后台重新生成
   - 原始文件缺失时提供友好的重新链接界面

5. **存储空间提示**
   - 缓存占用超过阈值时提示用户
   - 提供一键清理缓存功能

## 系统 Agent 设计

### 概述

系统 Agent 是一个常驻前端的智能助手，负责：
1. 监控后台任务状态
2. 处理和展示系统问题
3. 提供问题解决建议
4. 调度用户交互

```
┌─────────────────────────────────────────────────────────────────────┐
│                      系统 Agent 架构                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    前端 SystemAgent                           │  │
│  │                                                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │ TaskMonitor │  │ IssueHandler│  │ Notification│          │  │
│  │  │  任务监控    │  │  问题处理   │  │   通知管理  │          │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │  │
│  │         │                │                │                   │  │
│  │         └────────────────┼────────────────┘                   │  │
│  │                          │                                     │  │
│  │                    ┌─────▼─────┐                              │  │
│  │                    │ AgentUI   │                              │  │
│  │                    │ 悬浮助手  │                              │  │
│  │                    └───────────┘                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                          │                                          │
│                          │ WebSocket / Polling                      │
│                          ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    后端 Event System                          │  │
│  │                                                                │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │ TaskEvents  │  │ SystemEvents│  │ ErrorEvents │          │  │
│  │  │  任务事件   │  │  系统事件   │  │  错误事件   │          │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### SystemAgent 组件

```typescript
// frontend/services/SystemAgent.ts

interface SystemEvent {
  id: string;
  type: 'task_progress' | 'task_complete' | 'task_error' | 
        'storage_warning' | 'asset_missing' | 'system_error';
  severity: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  data?: any;
  actions?: AgentAction[];
}

interface AgentAction {
  id: string;
  label: string;
  type: 'primary' | 'secondary' | 'danger';
  handler: () => void | Promise<void>;
}

class SystemAgent {
  private eventQueue: SystemEvent[] = [];
  private listeners: Map<string, Function[]> = new Map();
  private wsConnection: WebSocket | null = null;
  
  // 启动 Agent
  async start() {
    // 1. 建立 WebSocket 连接
    this.connectWebSocket();
    
    // 2. 启动定期健康检查
    this.startHealthCheck();
    
    // 3. 恢复未完成的任务监控
    await this.recoverPendingTasks();
  }
  
  // 监控导出任务
  async monitorExportTask(taskId: string) {
    // 轮询任务状态
    const checkStatus = async () => {
      const status = await api.getExportStatus(taskId);
      
      if (status.status === 'completed') {
        this.emit({
          type: 'task_complete',
          severity: 'info',
          title: '导出完成',
          message: `文件已准备好下载`,
          actions: [
            { label: '下载', type: 'primary', handler: () => api.downloadExport(taskId) },
            { label: '打开文件夹', type: 'secondary', handler: () => api.openExportFolder(taskId) }
          ]
        });
      } else if (status.status === 'failed') {
        this.emit({
          type: 'task_error',
          severity: 'error',
          title: '导出失败',
          message: status.error_message,
          actions: [
            { label: '重试', type: 'primary', handler: () => this.retryExport(taskId) },
            { label: '查看详情', type: 'secondary', handler: () => this.showErrorDetails(status) }
          ]
        });
      } else {
        // 继续监控
        setTimeout(checkStatus, 2000);
      }
    };
    
    checkStatus();
  }
  
  // 处理存储空间警告
  handleStorageWarning(availableSpace: number, requiredSpace: number) {
    this.emit({
      type: 'storage_warning',
      severity: 'warning',
      title: '存储空间不足',
      message: `需要 ${formatSize(requiredSpace)}，当前可用 ${formatSize(availableSpace)}`,
      actions: [
        { label: '清理缓存', type: 'primary', handler: () => this.cleanupCache() },
        { label: '选择其他位置', type: 'secondary', handler: () => this.selectExportPath() }
      ]
    });
  }
  
  // 处理素材缺失
  handleAssetMissing(assetIds: string[]) {
    this.emit({
      type: 'asset_missing',
      severity: 'error',
      title: '素材文件缺失',
      message: `${assetIds.length} 个素材文件无法找到`,
      actions: [
        { label: '重新链接', type: 'primary', handler: () => this.relinkAssets(assetIds) },
        { label: '跳过缺失', type: 'secondary', handler: () => this.skipMissingAssets(assetIds) }
      ]
    });
  }
}
```

### AgentUI 悬浮助手组件

```typescript
// frontend/components/AgentUI.tsx

interface AgentUIProps {
  agent: SystemAgent;
}

const AgentUI: React.FC<AgentUIProps> = ({ agent }) => {
  const [events, setEvents] = useState<SystemEvent[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);
  
  useEffect(() => {
    // 订阅 Agent 事件
    const unsubscribe = agent.subscribe((event) => {
      setEvents(prev => [event, ...prev].slice(0, 50));
      setHasUnread(true);
      
      // 重要事件自动展开
      if (event.severity === 'error') {
        setIsExpanded(true);
      }
    });
    
    return unsubscribe;
  }, [agent]);
  
  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* 悬浮按钮 */}
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="relative w-12 h-12 bg-indigo-600 rounded-full shadow-lg"
      >
        <BotIcon />
        {hasUnread && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full" />
        )}
      </button>
      
      {/* 展开面板 */}
      {isExpanded && (
        <div className="absolute bottom-16 right-0 w-80 bg-zinc-900 rounded-lg shadow-xl">
          <div className="p-4 border-b border-zinc-800">
            <h3 className="font-bold">系统助手</h3>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {events.map(event => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

### 后端事件系统

```python
# backend/services/event_system.py

from typing import Dict, Any, List, Callable
from enum import Enum
import asyncio
import json

class EventType(Enum):
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    STORAGE_WARNING = "storage_warning"
    ASSET_MISSING = "asset_missing"
    SYSTEM_ERROR = "system_error"

class EventSystem:
    """后端事件系统 - 用于向前端推送系统事件"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
    
    async def emit(self, event_type: EventType, data: Dict[str, Any]):
        """发送事件"""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type.value,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        await self.event_queue.put(event)
        
        # 通知所有订阅者
        for callback in self.subscribers.get(event_type.value, []):
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")
    
    async def emit_task_progress(self, task_id: str, progress: float, message: str):
        """发送任务进度事件"""
        await self.emit(EventType.TASK_PROGRESS, {
            "task_id": task_id,
            "progress": progress,
            "message": message
        })
    
    async def emit_storage_warning(self, available: int, required: int):
        """发送存储空间警告"""
        await self.emit(EventType.STORAGE_WARNING, {
            "severity": "warning",
            "available_space": available,
            "required_space": required
        })
    
    async def emit_asset_missing(self, asset_ids: List[str]):
        """发送素材缺失事件"""
        await self.emit(EventType.ASSET_MISSING, {
            "severity": "error",
            "asset_ids": asset_ids
        })

# 全局事件系统实例
event_system = EventSystem()
```

### WebSocket 端点

```python
# backend/routers/events.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.event_system import event_system

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # 订阅事件系统
    async def on_event(event):
        await manager.broadcast(event)
    
    event_system.subscribe("*", on_event)
    
    try:
        while True:
            # 保持连接，接收客户端消息
            data = await websocket.receive_text()
            # 处理客户端请求...
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### 问题处理流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      问题处理流程                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 问题检测                                                        │
│     ├── 后台任务失败 → 发送 task_error 事件                         │
│     ├── 存储空间不足 → 发送 storage_warning 事件                    │
│     ├── 素材文件缺失 → 发送 asset_missing 事件                      │
│     └── 系统异常 → 发送 system_error 事件                           │
│                                                                      │
│  2. 前端接收                                                        │
│     └── SystemAgent 通过 WebSocket 接收事件                         │
│                                                                      │
│  3. 用户通知                                                        │
│     ├── info → 悬浮提示，自动消失                                   │
│     ├── warning → 悬浮提示 + 徽章，需用户确认                       │
│     └── error → 自动展开面板，显示操作按钮                          │
│                                                                      │
│  4. 用户操作                                                        │
│     ├── 重试 → 重新执行失败的任务                                   │
│     ├── 清理缓存 → 释放存储空间                                     │
│     ├── 重新链接 → 打开素材重新链接对话框                           │
│     └── 查看详情 → 显示详细错误信息                                 │
│                                                                      │
│  5. 问题解决                                                        │
│     └── 更新事件状态，从队列中移除                                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 前端素材显示流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      前端素材显示流程                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 列表/看板视图                                                    │
│     └── 使用 thumbnailUrl (缩略图)                                   │
│         - 快速加载                                                   │
│         - 低带宽消耗                                                 │
│         - 格式: JPG, 尺寸: 320x180                                   │
│                                                                      │
│  2. 预览/编辑视图                                                    │
│     └── 使用 proxyUrl (代理文件)                                     │
│         - 流畅播放                                                   │
│         - 中等质量                                                   │
│         - 格式: MP4 (H.264), 分辨率: 720p                            │
│                                                                      │
│  3. 最终渲染                                                         │
│     └── 使用 originalPath (原始文件)                                 │
│         - 最高质量                                                   │
│         - 后端处理                                                   │
│         - 格式: 原始格式                                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 素材数据结构

```typescript
interface Asset {
  id: string;
  name: string;
  type: 'image' | 'video' | 'audio';
  
  // 显示用 URL（前端直接使用）
  thumbnailUrl: string;    // 缩略图 URL，用于列表显示
  proxyUrl?: string;       // 代理文件 URL，用于预览播放
  
  // 后端存储路径（渲染时使用）
  originalPath: string;    // 原始文件路径
  proxyPath?: string;      // 代理文件路径
  thumbnailPath: string;   // 缩略图路径
  
  // 元数据
  duration?: number;       // 视频/音频时长
  width?: number;          // 图片/视频宽度
  height?: number;         // 图片/视频高度
  fileSize: number;        // 文件大小
  mimeType: string;        // MIME 类型
}
```

### 渲染流程详解

```
┌─────────────────────────────────────────────────────────────────────┐
│                      导出渲染流程                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │   前端请求    │───▶│   后端 API   │───▶│  渲染服务    │          │
│  │  导出视频     │    │  创建任务    │    │  开始处理    │          │
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│                                                 │                    │
│                                                 ▼                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    渲染处理步骤                                │  │
│  │                                                                │  │
│  │  1. 获取时间轴数据                                             │  │
│  │     - 读取 clips 列表                                          │  │
│  │     - 按 order_index 排序                                      │  │
│  │                                                                │  │
│  │  2. 解析素材引用                                               │  │
│  │     - 通过 asset_id 查询数据库                                 │  │
│  │     - 获取 originalPath（原始文件路径）                        │  │
│  │     - 验证文件存在性                                           │  │
│  │                                                                │  │
│  │  3. 处理每个片段                                               │  │
│  │     - 读取原始素材文件                                         │  │
│  │     - 应用 trim_start/trim_end 裁剪                            │  │
│  │     - 生成临时片段文件                                         │  │
│  │                                                                │  │
│  │  4. 拼接与编码                                                 │  │
│  │     - 使用 FFmpeg concat 拼接片段                              │  │
│  │     - 应用输出参数（分辨率、帧率、编码）                       │  │
│  │     - 生成最终输出文件                                         │  │
│  │                                                                │  │
│  │  5. 清理与通知                                                 │  │
│  │     - 删除临时文件                                             │  │
│  │     - 更新任务状态                                             │  │
│  │     - 返回下载链接                                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 故事板图片导出流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    故事板序列导出流程                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. 获取 Beat 数据                                                  │
│     └── 按场次分组，获取每个 Beat 的 mainAssetId                    │
│                                                                      │
│  2. 生成高分辨率图片                                                │
│     ├── 图片素材: 直接读取原始文件，缩放到目标分辨率                │
│     └── 视频素材: 提取指定帧（默认第一帧），缩放到目标分辨率        │
│                                                                      │
│  3. 叠加镜头信息（可选）                                            │
│     └── 在图片上绘制: 场次号、镜头号、时长、描述                    │
│                                                                      │
│  4. 组织文件结构                                                    │
│     └── 按场次创建文件夹，图片命名: scene_001/beat_001.png          │
│                                                                      │
│  5. 打包输出                                                        │
│     └── 生成 ZIP 文件，包含所有场次文件夹                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 前端预览 vs 后端渲染对比

| 场景 | 使用的素材 | 说明 |
|------|-----------|------|
| 列表缩略图 | thumbnailUrl | 320x180 JPG，快速加载 |
| 看板预览 | thumbnailUrl / proxyUrl | 根据素材类型选择 |
| 时间轴预览 | proxyUrl | 720p 代理文件，流畅播放 |
| 导出渲染 | originalPath | 原始高质量文件 |
| 故事板导出 | originalPath | 原始文件生成高分辨率图片 |

## Data Models

### ExportHistory 表结构

```python
class ExportHistory(Base):
    __tablename__ = "export_history"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    timeline_id = Column(String, ForeignKey("timelines.id"), nullable=True)
    export_type = Column(String)  # project_doc, beatboard_seq, video, audio, nle
    file_format = Column(String)  # pdf, docx, png, jpg, mp4, mov, wav, mp3, xml, edl
    file_path = Column(String)
    file_size = Column(Integer)
    options = Column(JSON)  # 导出选项
    status = Column(String)  # pending, processing, completed, failed
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
```

### 导出文件存储结构

```
exports/
├── projects/
│   └── {project_id}/
│       ├── documents/
│       │   └── {project_id}_project_20241224_120000.pdf
│       └── beatboards/
│           ├── scene_001/
│           │   ├── beat_001.png
│           │   ├── beat_002.png
│           │   └── ...
│           ├── scene_002/
│           │   └── ...
│           └── contact_sheet.png
├── timelines/
│   └── {timeline_id}/
│       ├── video/
│       │   └── render_20241224_120000.mp4
│       ├── audio/
│       │   └── audio_20241224_120000.wav
│       └── nle/
│           ├── timeline_20241224_120000.xml
│           └── timeline_20241224_120000.edl
└── temp/
    └── ... (临时文件，定期清理)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: 项目文档导出完整性

*For any* 有效的项目数据，导出的文档应包含所有选中的内容模块（剧本、角色、场次、镜头、AI分析）

**Validates: Requirements 1.2**

### Property 2: 文档格式有效性

*For any* 导出请求，生成的 PDF 文件应是有效的 PDF 格式，DOCX 文件应是有效的 Office Open XML 格式

**Validates: Requirements 1.3, 1.4**

### Property 3: 故事板序列数量一致性

*For any* 场次导出请求，导出的图片数量应等于该场次中的镜头数量

**Validates: Requirements 2.3**

### Property 4: 图片分辨率一致性

*For any* 指定分辨率的导出请求，生成的图片实际分辨率应与请求的分辨率一致

**Validates: Requirements 2.5**

### Property 5: 文件夹结构正确性

*For any* 按场次导出的请求，生成的文件夹结构应按场次组织，每个场次一个文件夹

**Validates: Requirements 2.6**

### Property 6: 视频格式有效性

*For any* 视频导出请求，生成的视频文件应是有效的视频格式且可播放

**Validates: Requirements 3.3**

### Property 7: 视频参数一致性

*For any* 指定分辨率和帧率的导出请求，生成的视频实际参数应与请求一致

**Validates: Requirements 3.4, 3.5**

### Property 8: 音频导出有效性

*For any* 音频导出请求，生成的音频文件应是有效的音频格式且可播放

**Validates: Requirements 3.6**

### Property 9: NLE 工程文件有效性

*For any* NLE 导出请求，生成的 XML 应符合 FCPXML 规范，EDL 应符合 CMX3600 规范

**Validates: Requirements 4.1, 4.2**

### Property 10: NLE 片段信息完整性

*For any* NLE 导出请求，导出文件中的片段数量应等于时间轴中的片段数量，且每个片段的入出点信息应正确

**Validates: Requirements 4.3**

### Property 11: 导出历史记录完整性

*For any* 成功的导出操作，系统应在数据库中创建对应的历史记录

**Validates: Requirements 5.1**

### Property 12: 导出文件清理正确性

*For any* 超过 7 天的导出文件，系统应自动删除文件并更新历史记录状态

**Validates: Requirements 5.4**

## Error Handling

### 错误类型

1. **文件系统错误**
   - 磁盘空间不足
   - 文件写入权限不足
   - 文件路径过长

2. **数据错误**
   - 项目不存在
   - 时间轴为空
   - 素材文件缺失

3. **渲染错误**
   - FFmpeg 未安装或不可用
   - 视频编码失败
   - 内存不足

4. **格式错误**
   - 不支持的导出格式
   - 无效的分辨率参数

### 错误处理策略

```python
class ExportError(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

# 错误码定义
ERROR_CODES = {
    "PROJECT_NOT_FOUND": "项目不存在",
    "TIMELINE_EMPTY": "时间轴为空",
    "ASSET_MISSING": "素材文件缺失",
    "FFMPEG_NOT_AVAILABLE": "FFmpeg 不可用",
    "DISK_SPACE_INSUFFICIENT": "磁盘空间不足",
    "RENDER_FAILED": "渲染失败",
    "UNSUPPORTED_FORMAT": "不支持的格式"
}
```

## Testing Strategy

### 单元测试

- 测试各导出服务的核心方法
- 测试文件格式验证逻辑
- 测试错误处理逻辑

### 属性测试

使用 Hypothesis 进行属性测试：

```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100, deadline=None)
@given(
    project_title=st.text(min_size=1, max_size=100),
    beat_count=st.integers(min_value=1, max_value=50)
)
def test_project_export_completeness(project_title, beat_count):
    """Property 1: 项目文档导出完整性"""
    # 创建测试项目
    # 执行导出
    # 验证导出内容完整性
    pass

@settings(max_examples=100, deadline=None)
@given(
    resolution=st.sampled_from(['1080p', '4k']),
    format=st.sampled_from(['png', 'jpg'])
)
def test_image_resolution_consistency(resolution, format):
    """Property 4: 图片分辨率一致性"""
    # 执行导出
    # 验证图片分辨率
    pass
```

### 集成测试

- 测试完整的导出流程
- 测试前后端 API 集成
- 测试文件下载功能

### 端到端测试

- 测试用户完整的导出操作流程
- 测试导出进度显示
- 测试错误提示和重试功能
