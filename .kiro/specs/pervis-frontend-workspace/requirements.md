# Requirements Document: 前端工作台目录页

## Introduction

本文档定义 Pervis PRO 前端工作台的目录页功能。用户完成项目向导后，进入工作台界面，通过 Tab 导航访问不同的功能模块。

## 用户流程

```
[首页] → [向导 6步] → [工作台] → [目录页 Tab]
   │          │            │           ├── 立项信息 (Project Info)
   /       Modal        /workspace     ├── Beatboard (故事板)
                                       └── 预演模式 (Preview Mode)
```

## Glossary

- **Workspace**: 工作台，项目的主要工作界面
- **Directory Page**: 目录页，工作台的 Tab 导航页面
- **Project Info Tab**: 立项信息标签页，显示和编辑项目基本信息
- **Beatboard Tab**: 故事板标签页，可视化编辑故事节拍
- **Preview Mode Tab**: 预演模式标签页，预览和播放时间线

## Requirements

### Requirement 1: 工作台布局

**User Story:** As a 导演, I want to 在完成项目向导后进入统一的工作台界面, so that 我可以在一个界面中管理项目的所有内容。

#### Acceptance Criteria

1. WHEN 用户完成项目向导 THEN THE 系统 SHALL 跳转到工作台界面
2. THE 工作台 SHALL 包含以下布局元素：
   - 顶部：项目标题和全局操作按钮
   - 中部：Tab 导航栏
   - 主体：当前 Tab 的内容区域
   - 侧边栏：可选的辅助面板（素材库、AI 助手等）
3. THE 工作台 SHALL 保持项目上下文，用户刷新页面后恢复到之前的 Tab

### Requirement 2: Tab 导航系统

**User Story:** As a 用户, I want to 通过 Tab 切换不同的功能模块, so that 我可以快速访问需要的功能。

#### Acceptance Criteria

1. THE 目录页 SHALL 提供以下 Tab：
   - 立项信息 (Project Info)
   - Beatboard (故事板)
   - 预演模式 (Preview Mode)
2. THE Tab 导航 SHALL 显示当前激活的 Tab
3. THE Tab 切换 SHALL 保持各 Tab 的状态（不重新加载）
4. THE Tab 导航 SHALL 支持键盘快捷键切换（Ctrl+1/2/3）

### Requirement 3: 立项信息 Tab

**User Story:** As a 导演, I want to 查看和编辑项目的立项信息, so that 我可以随时调整项目设置。

#### Acceptance Criteria

1. THE 立项信息 Tab SHALL 显示以下内容：
   - 项目基本信息（标题、类型、时长、画幅、帧率）
   - Logline 和 Synopsis
   - 角色列表（可展开查看详情）
   - 场次列表（可展开查看详情）
   - 参考资料预览
2. THE 立项信息 Tab SHALL 支持编辑模式
3. WHEN 用户编辑信息 THEN THE 系统 SHALL 自动保存
4. THE 立项信息 Tab SHALL 显示项目完成度和状态

### Requirement 4: Beatboard Tab

**User Story:** As a 导演, I want to 在故事板上可视化编辑故事节拍, so that 我可以直观地组织故事结构。

#### Acceptance Criteria

1. THE Beatboard Tab SHALL 复用现有的 StepBeatBoard 组件
2. THE Beatboard Tab SHALL 显示所有场景和节拍
3. THE Beatboard Tab SHALL 支持拖拽排序
4. THE Beatboard Tab SHALL 支持素材关联和预览
5. THE Beatboard Tab SHALL 与立项信息 Tab 的场次数据同步

### Requirement 5: 预演模式 Tab

**User Story:** As a 导演, I want to 预览项目的时间线效果, so that 我可以在正式渲染前检查效果。

#### Acceptance Criteria

1. THE 预演模式 Tab SHALL 提供时间线预览播放器
2. THE 预演模式 Tab SHALL 支持播放/暂停/跳转控制
3. THE 预演模式 Tab SHALL 显示当前播放位置和总时长
4. THE 预演模式 Tab SHALL 支持全屏预览
5. THE 预演模式 Tab SHALL 复用现有的 StepTimeline 组件的预览功能
6. THE 预演模式 Tab SHALL 提供导出按钮（跳转到渲染流程）

### Requirement 6: 侧边栏集成

**User Story:** As a 用户, I want to 在工作台中快速访问素材库和 AI 助手, so that 我可以高效地完成工作。

#### Acceptance Criteria

1. THE 工作台 SHALL 保留现有的侧边栏导航
2. THE 侧边栏 SHALL 包含：
   - 素材库入口
   - AI 助手状态
   - 设置入口
3. THE 侧边栏 SHALL 可折叠以获得更大的工作区域

### Requirement 7: 与现有系统集成

**User Story:** As a 开发者, I want to 工作台与现有系统无缝集成, so that 不需要重写现有功能。

#### Acceptance Criteria

1. THE 工作台 SHALL 复用现有的组件：
   - StepAnalysis → 立项信息 Tab 的数据源
   - StepBeatBoard → Beatboard Tab
   - StepTimeline → 预演模式 Tab
   - StepLibrary → 侧边栏素材库
2. THE 工作台 SHALL 使用现有的 API 和数据模型
3. THE 工作台 SHALL 保持与 ProjectWizard 的数据一致性

## 技术约束

1. 使用 React + TypeScript
2. 复用现有的 UI 组件和样式（Tailwind CSS）
3. 保持与现有 API 的兼容性
4. 支持中英文国际化

## 优先级

| 需求 | 优先级 | 说明 |
|------|--------|------|
| Req 1 工作台布局 | P0 | 基础架构 |
| Req 2 Tab 导航 | P0 | 核心功能 |
| Req 3 立项信息 | P0 | 用户核心需求 |
| Req 4 Beatboard | P1 | 复用现有组件 |
| Req 5 预演模式 | P1 | 复用现有组件 |
| Req 6 侧边栏 | P2 | 增强功能 |
| Req 7 系统集成 | P0 | 技术要求 |
