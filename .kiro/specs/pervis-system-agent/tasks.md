# Implementation Plan: Pervis PRO 系统 Agent

## Overview

本实现计划将系统 Agent 分为以下几个阶段：
1. 后端事件服务（EventService、WebSocket）
2. 后端健康检查（HealthChecker）
3. 前端 SystemAgentProvider 和 Hook
4. 前端 SystemAgentUI 悬浮组件
5. 集成测试

## Tasks

- [x] 1. 后端事件服务

  - [x] 1.1 创建 EventService 事件服务
    - 创建 `backend/services/event_service.py`
    - 实现 WebSocket 连接管理
    - 实现 `emit()` 事件发送方法
    - 实现 `emit_task_progress()`、`emit_agent_status()`、`emit_system_warning()`
    - _Requirements: 6.1, 6.2_

  - [x] 1.2 创建 WebSocket 端点
    - 创建 `backend/routers/websocket.py`
    - 实现 `/ws/events` WebSocket 端点
    - 实现心跳检测和自动重连
    - _Requirements: 6.3, 6.4_

  - [x] 1.3 创建 SystemNotification 数据模型
    - 创建 `backend/models/system_notification.py`
    - 创建数据库迁移脚本 `migrations/008_add_system_agent_tables.py`
    - _Requirements: 5.1_

  - [x] 1.4 创建 BackgroundTask 数据模型
    - 创建 `backend/models/background_task.py`
    - 创建数据库迁移脚本 `migrations/008_add_system_agent_tables.py`
    - _Requirements: 1.1_


- [x] 2. 后端健康检查

  - [x] 2.1 创建 HealthChecker 健康检查器
    - 创建 `backend/services/health_checker.py`
    - 实现 `check_all()` 完整健康检查
    - 实现各项检查：API、数据库、FFmpeg、AI 服务、存储、缓存
    - _Requirements: 8.2_

  - [x] 2.2 创建健康检查 API
    - 在 `backend/routers/system.py` 添加 `/api/system/health`
    - 实现启动时自动健康检查
    - 实现定时后台健康检查（每 5 分钟）
    - _Requirements: 8.1, 8.4, 8.5_

  - [x] 2.3 创建通知管理 API
    - 实现 `GET /api/system/notifications` - 获取通知历史
    - 实现 `POST /api/system/notifications/{id}/read` - 标记已读
    - 实现 `DELETE /api/system/notifications/{id}` - 删除通知
    - 实现 `POST /api/system/notifications/clear` - 清空所有
    - _Requirements: 5.2, 5.3, 5.4_

  - [x] 2.4 创建操作执行 API
    - 实现 `POST /api/system/actions/clean-cache` - 清理缓存
    - 实现 `POST /api/system/actions/retry-task/{task_id}` - 重试任务（框架）
    - 实现 `POST /api/system/actions/relink-asset` - 重新链接素材（框架）
    - _Requirements: 3.2_

- [x] 3. 集成事件发送到现有服务

  - [x] 3.1 集成到 AgentService
    - 修改 `backend/services/agent_service.py`
    - 在 Agent 任务开始/完成时发送事件
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 3.2 集成到 ExportService
    - ✅ 修改 `backend/services/render_service_enhanced.py` - 已集成 EventService
    - ✅ 修改 `backend/services/audio_exporter.py` - 已创建并集成
    - 在导出任务进度更新时发送事件
    - _Requirements: 1.2, 1.3, 1.4_

  - [x] 3.3 集成到 RenderService
    - 修改 `backend/services/render_service.py`
    - 在渲染进度更新时发送事件
    - _Requirements: 1.2, 1.3, 1.4_

- [x] 4. Checkpoint - 后端功能验证
  - ✅ WebSocket 连接正常（EventService 测试通过）
  - ✅ 事件能够正确发送（emit 方法测试通过）
  - ✅ 健康检查 API 正常（HealthChecker 测试通过）
  - ✅ 数据模型正常（SystemNotification、BackgroundTask）
  - ✅ 路由导入正常（websocket、system）
  - ✅ 数据库表已创建

- [x] 5. 前端 SystemAgentProvider

  - [x] 5.1 创建 SystemAgentContext
    - 创建 `frontend/components/SystemAgent/SystemAgentContext.tsx`
    - 实现状态管理（notifications、activeTasks、activeAgents）
    - 实现 WebSocket 连接和事件处理
    - _Requirements: 6.1, 6.3_

  - [x] 5.2 创建 useSystemAgent Hook
    - 在 `SystemAgentContext.tsx` 中导出 `useSystemAgent`
    - 暴露状态和方法
    - _Requirements: 4.1_

  - [x] 5.3 实现 WebSocket 重连逻辑
    - 实现自动重连（指数退避）
    - 实现降级到轮询模式
    - _Requirements: 6.3, 6.4_

- [x] 6. 前端 SystemAgentUI 组件

  - [x] 6.1 创建 SystemAgentUI 悬浮组件
    - 创建 `frontend/components/SystemAgent/SystemAgentUI.tsx`
    - 实现悬浮图标（状态指示、未读徽章）
    - 实现展开/收起动画
    - 实现拖拽调整位置
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 6.2 创建 TaskList 任务列表组件
    - 创建 `frontend/components/SystemAgent/TaskList.tsx`
    - 显示当前运行的任务
    - 显示进度条和预计时间
    - 显示 Agent 状态
    - _Requirements: 1.5, 1.6, 7.6_

  - [x] 6.3 创建 NotificationList 通知列表组件
    - 创建 `frontend/components/SystemAgent/NotificationList.tsx`
    - 显示通知列表（按类型筛选）
    - 显示操作按钮
    - 支持标记已读和删除
    - _Requirements: 5.2, 5.3, 5.4_

  - [x] 6.4 创建 NotificationToast 组件
    - 创建 `frontend/components/SystemAgent/NotificationToast.tsx`
    - 显示新通知的 Toast 提示
    - 支持点击跳转到详情
    - _Requirements: 2.2_

- [x] 7. 前端集成

  - [x] 7.1 集成 SystemAgentProvider 到 App
    - 修改 `frontend/App.tsx`
    - 包裹 SystemAgentProvider
    - _Requirements: 4.1_

  - [x] 7.2 集成 SystemAgentUI 到布局
    - 在主布局中添加 SystemAgentUI
    - 确保在所有页面可见
    - _Requirements: 4.1_

  - [x] 7.3 集成到 ProjectWizard
    - ProjectWizard 已有 AgentStatusPanel 组件
    - SystemAgentUI 全局显示，无需重复集成
    - _Requirements: 7.1, 7.2, 7.3_

- [x] 8. Final Checkpoint - 完整功能验证 ✅ (2025-12-27)
  - ✅ 后端 EventService 测试通过
  - ✅ 后端 HealthChecker 测试通过
  - ✅ 后端数据模型测试通过
  - ✅ 后端路由导入测试通过
  - ✅ 数据库表已创建
  - ✅ 前端组件代码无语法错误
  - ✅ App.tsx 集成完成
  - ✅ E2E API 验证测试 100% 通过 (12/12)
  - ✅ System Agent API 端点全部可用

## Notes

- 系统 Agent 是常驻组件，需要考虑性能影响
- WebSocket 断开时需要优雅降级到轮询模式
- 通知历史需要定期清理（超过 7 天自动删除）
- 与 ProjectWizard 的 Agent 状态显示需要协调，避免重复显示



---

## E2E 验证结果 (2025-12-27)

- ✅ `/api/system/health` - 系统健康检查通过
- ✅ `/api/system/notifications` - 通知列表查询通过
- ✅ `/api/system/health/quick` - 快速健康检查通过
- ✅ 路由前缀问题已修复（移除 `prefix="/api/system"`）
- **测试结果: 3/3 System Agent API 端点通过**

---

## 实际文件清单 (2025-12-29 同步)

```
前端组件：
- frontend/components/SystemAgent/index.ts           ✅ 导出入口
- frontend/components/SystemAgent/types.ts           ✅ 类型定义
- frontend/components/SystemAgent/SystemAgentContext.tsx ✅ 状态管理 + WebSocket
- frontend/components/SystemAgent/SystemAgentUI.tsx  ✅ 悬浮 UI 主组件
- frontend/components/SystemAgent/TaskList.tsx       ✅ 任务列表
- frontend/components/SystemAgent/NotificationList.tsx ✅ 通知列表
- frontend/components/SystemAgent/NotificationToast.tsx ✅ Toast 提示

后端服务：
- backend/services/event_service.py     ✅ 事件服务
- backend/services/health_checker.py    ✅ 健康检查
- backend/routers/system.py             ✅ API 路由
- backend/routers/websocket.py          ✅ WebSocket 端点
- backend/models/system_notification.py ✅ 通知模型
- backend/models/background_task.py     ✅ 任务模型
- backend/migrations/008_add_system_agent_tables.py ✅ 数据库迁移
```
