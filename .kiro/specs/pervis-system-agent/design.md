# Design Document: Pervis PRO 系统 Agent

## Overview

本设计文档描述 Pervis PRO 系统 Agent 的架构设计。系统 Agent 是一个常驻的智能助手，通过 WebSocket 实时接收后端事件，向用户展示系统状态和问题通知。

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    SystemAgentProvider                       │   │
│  │                    (React Context)                           │   │
│  │                                                              │   │
│  │  State:                                                      │   │
│  │  • notifications: Notification[]                            │   │
│  │  • activeTasks: BackgroundTask[]                            │   │
│  │  • systemStatus: 'normal' | 'working' | 'warning' | 'error' │   │
│  │  • isConnected: boolean                                     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│              ┌──────────────┼──────────────┐                       │
│              ▼              ▼              ▼                       │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐            │
│  │SystemAgentUI  │ │useSystemAgent │ │NotificationToast│           │
│  │(悬浮组件)     │ │(Hook)         │ │(Toast 通知)    │           │
│  └───────────────┘ └───────────────┘ └───────────────┘            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────┤
│  /ws/events - WebSocket 端点                                        │
│  /api/system/health - 健康检查 API                                  │
│  /api/system/notifications - 通知历史 API                           │
└─────────────────────────────────────────────────────────────────────┘
```


## Components and Interfaces

### 1. 后端组件

#### 1.1 EventService（事件服务）

```python
class EventService:
    """事件服务 - 管理 WebSocket 连接和事件推送"""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
        self.event_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self, websocket: WebSocket):
        """建立 WebSocket 连接"""
        await websocket.accept()
        self.connections.append(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        self.connections.remove(websocket)
    
    async def emit(self, event_type: str, data: Dict):
        """发送事件到所有连接的客户端"""
        event = SystemEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            data=data,
            timestamp=datetime.now()
        )
        for connection in self.connections:
            await connection.send_json(event.dict())
    
    async def emit_task_progress(self, task_id: str, progress: int, message: str):
        """发送任务进度事件"""
        await self.emit("task.progress", {
            "task_id": task_id,
            "progress": progress,
            "message": message
        })
    
    async def emit_agent_status(self, agent_type: str, status: str, message: str):
        """发送 Agent 状态事件"""
        await self.emit(f"agent.{status}", {
            "agent_type": agent_type,
            "message": message
        })
    
    async def emit_system_warning(self, warning_type: str, message: str, suggestion: Dict):
        """发送系统警告事件"""
        await self.emit("system.warning", {
            "warning_type": warning_type,
            "message": message,
            "suggestion": suggestion
        })
```

#### 1.2 HealthChecker（健康检查器）

```python
class HealthChecker:
    """健康检查器 - 定期检查系统状态"""
    
    def __init__(self, event_service: EventService):
        self.event_service = event_service
    
    async def check_all(self) -> HealthCheckResult:
        """执行完整健康检查"""
        results = {
            "api": await self._check_api(),
            "database": await self._check_database(),
            "ffmpeg": await self._check_ffmpeg(),
            "ai_service": await self._check_ai_service(),
            "storage": await self._check_storage(),
            "cache": await self._check_cache()
        }
        return HealthCheckResult(
            status="healthy" if all(r.ok for r in results.values()) else "unhealthy",
            checks=results
        )
    
    async def _check_storage(self) -> CheckResult:
        """检查存储空间"""
        free_space = shutil.disk_usage("/").free
        if free_space < 1 * 1024 * 1024 * 1024:  # < 1GB
            await self.event_service.emit_system_warning(
                "storage.low",
                f"存储空间不足，剩余 {free_space // (1024*1024)} MB",
                {"action": "clean_cache", "label": "清理缓存"}
            )
            return CheckResult(ok=False, message="存储空间不足")
        return CheckResult(ok=True, message="存储空间正常")
```


### 2. 前端组件

#### 2.1 SystemAgentProvider（Context Provider）

```typescript
interface SystemAgentState {
  notifications: Notification[];
  activeTasks: BackgroundTask[];
  activeAgents: AgentStatus[];
  systemStatus: 'normal' | 'working' | 'warning' | 'error';
  isConnected: boolean;
  unreadCount: number;
}

interface Notification {
  id: string;
  type: 'task' | 'warning' | 'error' | 'info';
  level: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  isRead: boolean;
  action?: ActionSuggestion;
}

interface BackgroundTask {
  id: string;
  type: 'export' | 'render' | 'ai_generate' | 'asset_process';
  name: string;
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startedAt: Date;
  estimatedTime?: number;
}

interface AgentStatus {
  agentType: 'script_agent' | 'art_agent' | 'director_agent';
  status: 'working' | 'reviewing' | 'completed' | 'failed';
  message: string;
  taskId: string;
}

interface ActionSuggestion {
  type: 'button' | 'link' | 'manual';
  label: string;
  action?: string;  // 'clean_cache' | 'retry_task' | 'relink_asset'
  url?: string;
  instructions?: string;
}
```

#### 2.2 SystemAgentUI（悬浮 UI 组件）

```typescript
interface SystemAgentUIProps {
  defaultPosition?: { x: number; y: number };
  defaultExpanded?: boolean;
}

// 组件结构
// ┌─────────────────────────────────────────────────────────────┐
// │  SystemAgentUI                                              │
// │                                                             │
// │  ┌─────────────┐  ┌─────────────────────────────────────┐ │
// │  │ FloatingIcon│  │ ExpandedPanel                       │ │
// │  │             │  │                                      │ │
// │  │  状态图标   │  │ ┌─────────────────────────────────┐│ │
// │  │  未读徽章   │  │ │ TaskList (当前任务列表)         ││ │
// │  │             │  │ │ • 任务名称                       ││ │
// │  │             │  │ │ • 进度条                         ││ │
// │  │             │  │ │ • Agent 状态                     ││ │
// │  │             │  │ └─────────────────────────────────┘│ │
// │  │             │  │ ┌─────────────────────────────────┐│ │
// │  │             │  │ │ NotificationList (通知列表)     ││ │
// │  │             │  │ │ • 通知标题                       ││ │
// │  │             │  │ │ • 操作按钮                       ││ │
// │  │             │  │ └─────────────────────────────────┘│ │
// │  └─────────────┘  └─────────────────────────────────────┘ │
// └─────────────────────────────────────────────────────────────┘
```

#### 2.3 useSystemAgent Hook

```typescript
function useSystemAgent() {
  const context = useContext(SystemAgentContext);
  
  return {
    // 状态
    notifications: context.notifications,
    activeTasks: context.activeTasks,
    activeAgents: context.activeAgents,
    systemStatus: context.systemStatus,
    isConnected: context.isConnected,
    unreadCount: context.unreadCount,
    
    // 方法
    markAsRead: (notificationId: string) => void,
    clearNotification: (notificationId: string) => void,
    clearAllNotifications: () => void,
    executeAction: (action: ActionSuggestion) => Promise<void>,
    retryTask: (taskId: string) => Promise<void>,
    cancelTask: (taskId: string) => Promise<void>,
    runHealthCheck: () => Promise<HealthCheckResult>,
  };
}
```


### 3. API 接口

#### 3.1 WebSocket 端点

```python
# WebSocket 端点: /ws/events
@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await event_service.connect(websocket)
    try:
        while True:
            # 保持连接，接收客户端心跳
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await event_service.disconnect(websocket)
```

#### 3.2 REST API 端点

```python
# GET /api/system/health - 健康检查
class HealthCheckResponse(BaseModel):
    status: str  # healthy, unhealthy
    checks: Dict[str, CheckResult]
    timestamp: datetime

# GET /api/system/notifications - 获取通知历史
class NotificationListResponse(BaseModel):
    notifications: List[Notification]
    total: int
    unread_count: int

# POST /api/system/notifications/{id}/read - 标记已读
# DELETE /api/system/notifications/{id} - 删除通知
# POST /api/system/notifications/clear - 清空所有通知

# POST /api/system/actions/clean-cache - 清理缓存
# POST /api/system/actions/retry-task/{task_id} - 重试任务
# POST /api/system/actions/relink-asset - 重新链接素材
```

## Data Models

### SystemNotification 表

```python
class SystemNotification(Base):
    """系统通知"""
    __tablename__ = "system_notifications"
    
    id = Column(String, primary_key=True)
    type = Column(String)  # task, warning, error, info
    level = Column(String)  # critical, warning, info
    title = Column(String)
    message = Column(String)
    
    # 操作建议 (JSON)
    action = Column(JSON, nullable=True)
    
    # 状态
    is_read = Column(Boolean, default=False)
    
    # 关联
    task_id = Column(String, nullable=True)
    agent_type = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### BackgroundTask 表

```python
class BackgroundTask(Base):
    """后台任务"""
    __tablename__ = "background_tasks"
    
    id = Column(String, primary_key=True)
    type = Column(String)  # export, render, ai_generate, asset_process
    name = Column(String)
    
    # 进度
    progress = Column(Integer, default=0)
    status = Column(String)  # pending, running, completed, failed
    
    # 详情 (JSON)
    details = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    
    # 时间
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # 秒
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Event Flow

### 任务进度事件流

```
┌─────────────────────────────────────────────────────────────────────┐
│                      任务进度事件流                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户触发导出                                                        │
│       │                                                              │
│       ▼                                                              │
│  ExportService.export_video()                                       │
│       │                                                              │
│       ├── event_service.emit("task.started", {...})                 │
│       │       │                                                      │
│       │       ▼                                                      │
│       │   WebSocket → 前端 SystemAgentProvider                      │
│       │       │                                                      │
│       │       ▼                                                      │
│       │   更新 activeTasks, 显示任务开始通知                        │
│       │                                                              │
│       ├── FFmpeg 渲染中...                                          │
│       │       │                                                      │
│       │       ├── event_service.emit("task.progress", {progress: 25})│
│       │       ├── event_service.emit("task.progress", {progress: 50})│
│       │       ├── event_service.emit("task.progress", {progress: 75})│
│       │       │                                                      │
│       │       ▼                                                      │
│       │   前端实时更新进度条                                        │
│       │                                                              │
│       └── event_service.emit("task.completed", {...})               │
│               │                                                      │
│               ▼                                                      │
│           前端显示完成通知，提供下载链接                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Agent 状态事件流

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent 状态事件流                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户点击"生成人物小传"                                             │
│       │                                                              │
│       ▼                                                              │
│  AgentService.execute_task("generate_bio", {...})                   │
│       │                                                              │
│       ├── event_service.emit("agent.working", {                     │
│       │       agent_type: "script_agent",                           │
│       │       message: "编剧 Agent 正在工作..."                     │
│       │   })                                                         │
│       │       │                                                      │
│       │       ▼                                                      │
│       │   前端 SystemAgentUI 显示: "🖊️ 编剧 Agent 正在工作..."     │
│       │                                                              │
│       ├── Script_Agent 完成                                         │
│       │                                                              │
│       ├── event_service.emit("agent.reviewing", {                   │
│       │       agent_type: "director_agent",                         │
│       │       message: "导演 Agent 审核中..."                       │
│       │   })                                                         │
│       │       │                                                      │
│       │       ▼                                                      │
│       │   前端 SystemAgentUI 显示: "🎬 导演 Agent 审核中..."       │
│       │                                                              │
│       └── event_service.emit("agent.completed", {                   │
│               agent_type: "director_agent",                         │
│               message: "导演 Agent 审核通过",                       │
│               result: {...}                                          │
│           })                                                         │
│               │                                                      │
│               ▼                                                      │
│           前端显示结果，用户可接受/拒绝                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Error Handling

### 错误类型和处理策略

| 错误类型 | 级别 | 处理策略 | 操作建议 |
|---------|------|---------|---------|
| 存储空间不足 | warning | 提示用户 | 清理缓存 |
| 素材文件缺失 | critical | 阻止操作 | 重新链接 |
| AI 服务超时 | warning | 自动重试 | 重试/跳过 |
| 渲染失败 | critical | 记录日志 | 重试/查看日志 |
| WebSocket 断开 | info | 自动重连 | 无 |
| 数据库错误 | critical | 记录日志 | 联系支持 |

