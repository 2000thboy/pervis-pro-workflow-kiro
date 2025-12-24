# Requirements Document: Pervis PRO 系统 Agent

## Introduction

Pervis PRO 系统 Agent 需求文档。系统 Agent 是一个常驻的智能助手，负责监控后台任务状态、处理系统问题、提供解决建议，并调度用户交互。

**定位**：系统 Agent 是用户与系统之间的桥梁，让用户随时了解系统状态，及时处理问题，无需主动查看。

## Glossary

- **System_Agent**: 系统 Agent，常驻运行的智能助手
- **BackgroundTask**: 后台任务，如导出、渲染、AI 生成等
- **SystemEvent**: 系统事件，包括任务进度、警告、错误等
- **Notification**: 通知，向用户展示的消息
- **ActionSuggestion**: 操作建议，系统 Agent 提供的解决方案

## Requirements

### Requirement 1: 后台任务监控

**User Story:** As a 用户, I want to 实时了解后台任务的执行状态, so that 我可以知道任务进度而不需要一直等待。

#### Acceptance Criteria

1. THE System_Agent SHALL 监控以下类型的后台任务：
   - 导出任务（视频、音频、文档、故事板）
   - 渲染任务（预览渲染、最终渲染）
   - AI 生成任务（Script_Agent、Art_Agent 的任务）
   - 素材处理任务（缩略图生成、代理文件生成、标签生成）
2. WHEN 后台任务开始 THEN THE System_Agent SHALL 显示任务开始通知
3. WHEN 后台任务进度更新 THEN THE System_Agent SHALL 更新进度显示
4. WHEN 后台任务完成 THEN THE System_Agent SHALL 显示完成通知
5. THE System_Agent SHALL 支持同时监控多个后台任务
6. THE System_Agent SHALL 显示任务队列和预计完成时间

### Requirement 2: 系统问题检测与提示

**User Story:** As a 用户, I want to 及时收到系统问题的提示, so that 我可以快速处理问题而不影响工作。

#### Acceptance Criteria

1. THE System_Agent SHALL 检测并提示以下类型的问题：
   - 存储空间不足（磁盘空间 < 1GB）
   - 素材文件缺失（原始文件被移动/删除）
   - 缓存文件损坏
   - 网络连接问题（API 调用失败）
   - AI 服务不可用（LLM 服务超时）
   - 渲染失败（FFmpeg 错误）
2. WHEN 检测到问题 THEN THE System_Agent SHALL 立即显示问题通知
3. THE System_Agent SHALL 对问题进行分级：
   - 🔴 严重（阻塞工作流程）
   - 🟡 警告（可能影响工作）
   - 🔵 信息（建议关注）
4. THE System_Agent SHALL 显示问题的详细描述和影响范围

### Requirement 3: 问题解决建议

**User Story:** As a 用户, I want to 收到问题的解决建议, so that 我可以快速解决问题而不需要查找文档。

#### Acceptance Criteria

1. WHEN 检测到问题 THEN THE System_Agent SHALL 提供至少一个解决建议
2. THE System_Agent SHALL 提供以下类型的解决建议：
   - 一键操作（如"清理缓存"、"重试任务"）
   - 手动操作指引（如"请检查文件路径"）
   - 跳转链接（如"打开设置页面"）
3. THE System_Agent SHALL 对解决建议进行优先级排序（推荐方案在前）
4. WHEN 用户执行解决建议 THEN THE System_Agent SHALL 显示执行结果
5. IF 问题无法自动解决 THEN THE System_Agent SHALL 提供联系支持的选项

### Requirement 4: 悬浮 UI 助手

**User Story:** As a 用户, I want to 在任何页面都能看到系统状态, so that 我可以随时了解系统情况。

#### Acceptance Criteria

1. THE System_Agent SHALL 以悬浮 UI 的形式常驻在界面右下角
2. THE System_Agent SHALL 显示以下状态指示：
   - 🟢 正常（无问题，无任务）
   - 🔵 工作中（有后台任务运行）
   - 🟡 警告（有警告级别问题）
   - 🔴 错误（有严重问题）
3. WHEN 用户点击悬浮图标 THEN THE System_Agent SHALL 展开详细面板
4. THE System_Agent SHALL 支持最小化和展开两种状态
5. THE System_Agent SHALL 在有新通知时显示未读数量徽章
6. THE System_Agent SHALL 支持拖拽调整位置

### Requirement 5: 通知管理

**User Story:** As a 用户, I want to 管理系统通知, so that 我可以查看历史通知和清除已处理的通知。

#### Acceptance Criteria

1. THE System_Agent SHALL 保存最近 100 条通知历史
2. THE System_Agent SHALL 支持按类型筛选通知（任务/警告/错误/信息）
3. THE System_Agent SHALL 支持标记通知为已读
4. THE System_Agent SHALL 支持清除单条或全部通知
5. THE System_Agent SHALL 支持通知免打扰模式（静音）
6. WHEN 通知超过 7 天 THEN THE System_Agent SHALL 自动清理

### Requirement 6: 实时事件推送

**User Story:** As a 开发者, I want to 系统事件能够实时推送到前端, so that 用户可以及时收到通知。

#### Acceptance Criteria

1. THE System_Agent SHALL 使用 WebSocket 接收后端事件
2. THE System_Agent SHALL 支持以下事件类型：
   - `task.started` - 任务开始
   - `task.progress` - 任务进度更新
   - `task.completed` - 任务完成
   - `task.failed` - 任务失败
   - `system.warning` - 系统警告
   - `system.error` - 系统错误
   - `asset.missing` - 素材缺失
   - `storage.low` - 存储空间不足
3. IF WebSocket 连接断开 THEN THE System_Agent SHALL 自动重连
4. IF WebSocket 不可用 THEN THE System_Agent SHALL 降级为轮询模式

### Requirement 7: 与其他 Agent 协作

**User Story:** As a 用户, I want to 系统 Agent 能够展示其他 Agent 的工作状态, so that 我可以了解 AI 辅助的进度。

#### Acceptance Criteria

1. WHEN Script_Agent 正在工作 THEN THE System_Agent SHALL 显示"编剧 Agent 正在工作..."
2. WHEN Art_Agent 正在工作 THEN THE System_Agent SHALL 显示"美术 Agent 正在工作..."
3. WHEN Director_Agent 正在审核 THEN THE System_Agent SHALL 显示"导演 Agent 审核中..."
4. WHEN Agent 任务完成 THEN THE System_Agent SHALL 显示完成通知和结果摘要
5. WHEN Agent 任务失败 THEN THE System_Agent SHALL 显示错误信息和重试选项
6. THE System_Agent SHALL 在悬浮 UI 中显示当前活跃的 Agent 列表

### Requirement 8: 系统健康检查

**User Story:** As a 用户, I want to 定期检查系统健康状态, so that 我可以提前发现潜在问题。

#### Acceptance Criteria

1. THE System_Agent SHALL 在应用启动时执行健康检查
2. THE System_Agent SHALL 检查以下项目：
   - 后端 API 连接状态
   - 数据库连接状态
   - FFmpeg 可用性
   - AI 服务可用性
   - 存储空间状态
   - 缓存目录状态
3. WHEN 健康检查发现问题 THEN THE System_Agent SHALL 显示问题列表
4. THE System_Agent SHALL 支持手动触发健康检查
5. THE System_Agent SHALL 定期（每 5 分钟）执行后台健康检查

## Architecture Notes

### 系统 Agent 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    SystemAgentUI                             │   │
│  │                                                              │   │
│  │  ┌─────────────┐  ┌─────────────────────────────────────┐  │   │
│  │  │ 悬浮图标    │  │ 展开面板                            │  │   │
│  │  │             │  │                                      │  │   │
│  │  │  🔵 (2)    │→│ ┌─────────────────────────────────┐ │  │   │
│  │  │             │  │ │ 当前任务                        │ │  │   │
│  │  │             │  │ │ • 导出视频 45%                  │ │  │   │
│  │  │             │  │ │ • 编剧 Agent 工作中             │ │  │   │
│  │  │             │  │ ├─────────────────────────────────┤ │  │   │
│  │  │             │  │ │ 通知                            │ │  │   │
│  │  │             │  │ │ 🟡 存储空间不足 [清理]          │ │  │   │
│  │  │             │  │ │ 🔵 渲染完成                     │ │  │   │
│  │  │             │  │ └─────────────────────────────────┘ │  │   │
│  │  └─────────────┘  └─────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              │ WebSocket                            │
│                              ▼                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    EventService                              │   │
│  │                                                              │   │
│  │  • emit_event(event_type, data)                             │   │
│  │  • WebSocket 连接管理                                        │   │
│  │  • 事件队列                                                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                │
│         ▼                    ▼                    ▼                │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│  │ ExportService│    │ AgentService│    │HealthChecker│          │
│  │             │     │             │     │             │          │
│  │ emit:       │     │ emit:       │     │ emit:       │          │
│  │ task.*      │     │ agent.*     │     │ system.*    │          │
│  └─────────────┘     └─────────────┘     └─────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 事件类型定义

```python
class SystemEventType(Enum):
    # 任务事件
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    
    # Agent 事件
    AGENT_WORKING = "agent.working"
    AGENT_REVIEWING = "agent.reviewing"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    # 系统事件
    SYSTEM_WARNING = "system.warning"
    SYSTEM_ERROR = "system.error"
    SYSTEM_INFO = "system.info"
    
    # 资源事件
    STORAGE_LOW = "storage.low"
    ASSET_MISSING = "asset.missing"
    CACHE_CORRUPTED = "cache.corrupted"
```

