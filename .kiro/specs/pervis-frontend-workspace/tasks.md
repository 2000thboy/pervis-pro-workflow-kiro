# Implementation Plan: 前端工作台目录页

## Overview

本实现计划将现有的侧边栏导航改造为 Tab 导航的工作台目录页，复用现有组件，最小化代码改动。

## 预计工时

| 阶段 | 工时 | 说明 |
|------|------|------|
| Phase 1 基础架构 | 2小时 | 创建 Workspace 组件 |
| Phase 2 立项信息 Tab | 3小时 | 新增核心功能 |
| Phase 3 复用组件 | 1小时 | 包装现有组件 |
| Phase 4 集成测试 | 1小时 | 测试和优化 |
| **总计** | **7小时** | |

---

## Tasks

### Phase 1: 基础架构

- [x] 1.1 创建 Workspace 组件目录
  - 创建 `frontend/components/Workspace/` 目录
  - 创建 `types.ts` 定义类型
  - _Requirements: 1.1, 1.2_

- [x] 1.2 创建 WorkspaceContext
  - 创建 `frontend/components/Workspace/WorkspaceContext.tsx`
  - 定义 WorkspaceState 接口
  - 实现 Tab 状态管理
  - 实现 localStorage 持久化
  - ✅ 集成到 index.tsx 中
  - _Requirements: 1.3, 2.3_

- [x] 1.3 创建 TabNavigation 组件
  - 创建 `frontend/components/Workspace/TabNavigation.tsx`
  - 实现 Tab 切换 UI
  - 实现激活状态样式
  - 支持图标和标签
  - _Requirements: 2.1, 2.2_

- [x] 1.4 创建 Workspace 主组件
  - 创建 `frontend/components/Workspace/index.tsx`
  - 集成 TabNavigation
  - 实现 Tab 内容切换
  - 保留顶部项目信息
  - _Requirements: 1.1, 1.2_

- [x] 1.5 修改 App.tsx 集成 Workspace
  - 导入 Workspace 组件
  - 替换现有的 stage 切换逻辑
  - 保持向导和首页逻辑不变
  - _Requirements: 7.1, 7.2_

### Phase 2: 立项信息 Tab

- [x] 2.1 创建 ProjectInfoTab 主组件
  - 创建 `frontend/components/Workspace/ProjectInfoTab.tsx`
  - 实现整体布局
  - 实现编辑/查看模式切换
  - ✅ 包含所有 Section 组件
  - _Requirements: 3.1, 3.2_

- [x] 2.2 创建 BasicInfoSection
  - ✅ 集成到 ProjectInfoTab.tsx
  - 显示项目标题、类型、时长、画幅、帧率
  - 支持编辑
  - _Requirements: 3.1_

- [x] 2.3 创建 ScriptSection
  - ✅ 集成到 ProjectInfoTab.tsx
  - 显示 Logline 和 Synopsis
  - 支持编辑
  - _Requirements: 3.1_

- [x] 2.4 创建 CharactersSection
  - ✅ 集成到 ProjectInfoTab.tsx
  - 显示角色列表
  - 支持展开查看详情
  - 支持编辑
  - _Requirements: 3.1_

- [x] 2.5 创建 ScenesSection
  - ✅ 集成到 ProjectInfoTab.tsx
  - 显示场次列表
  - 支持展开查看详情
  - 支持编辑
  - _Requirements: 3.1_

- [x] 2.6 创建 ReferencesSection
  - ✅ 集成到 ProjectInfoTab.tsx
  - 显示参考资料预览
  - 支持查看大图
  - _Requirements: 3.1_

- [x] 2.7 实现自动保存
  - ✅ 通过 onUpdate 回调实现
  - 显示保存状态指示器
  - _Requirements: 3.3_

### Phase 3: 复用现有组件

- [x] 3.1 创建 BeatboardTab 包装组件
  - 创建 `frontend/components/Workspace/BeatboardTab.tsx`
  - 包装 StepBeatBoard 组件
  - 适配 Tab 接口
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 3.2 创建 PreviewTab 包装组件
  - 创建 `frontend/components/Workspace/PreviewTab.tsx`
  - 包装 StepTimeline 组件
  - 添加导出按钮
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 3.3 数据同步
  - ✅ 通过 props 传递实现
  - 确保 Tab 间数据同步
  - 测试 Beatboard 和立项信息的场次同步
  - _Requirements: 4.5, 7.3_

### Phase 4: 优化和测试

- [x] 4.1 添加键盘快捷键
  - ✅ 实现 Ctrl+1/2/3 切换 Tab
  - 添加快捷键提示
  - _Requirements: 2.4_

- [x] 4.2 侧边栏集成
  - ✅ 保留素材库入口
  - ✅ 保留 AI 助手状态
  - ✅ 保留设置入口
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 4.3 完成度显示
  - ✅ 在立项信息 Tab 显示项目完成度
  - 显示各部分填写状态
  - _Requirements: 3.4_

- [x] 4.4 集成测试
  - ✅ TypeScript 编译通过
  - 测试完整用户流程
  - 测试 Tab 切换
  - 测试数据保存
  - 测试与向导的衔接

### Checkpoint - 功能验证

- [x] 验证项目向导完成后正确进入工作台
- [x] 验证 Tab 切换正常工作
- [x] 验证立项信息显示和编辑正常
- [x] 验证 Beatboard 功能正常
- [x] 验证预演模式功能正常
- [x] 验证数据保存和同步正常
- 验证日期: 2025-12-28
- **Spec 状态: 完成 ✅**

---

## Notes

- 本 spec 主要是前端改造，不涉及后端 API 变更
- 复用现有组件，最小化代码改动
- 保持与现有系统的兼容性
- 支持中英文国际化

## 文件清单

```
实际实现文件：
- frontend/components/Workspace/index.tsx        ✅ (含状态管理，无需单独 Context)
- frontend/components/Workspace/types.ts         ✅
- frontend/components/Workspace/TabNavigation.tsx ✅
- frontend/components/Workspace/ProjectInfoTab.tsx ✅ (单文件实现，含所有 Section)
- frontend/components/Workspace/BeatboardTab.tsx  ✅
- frontend/components/Workspace/PreviewTab.tsx    ✅

修改文件：
- frontend/App.tsx (集成 Workspace) ✅
```

## 实现说明

- `WorkspaceContext.tsx` 未单独创建，状态管理直接集成在 `index.tsx` 中使用 `useState` + `localStorage`
- `ProjectInfoTab` 采用单文件实现，所有 Section（BasicInfo、Script、Characters、Scenes、References）内联在同一文件中
- 这种简化实现满足所有功能需求，代码更紧凑

---

## Phase 5: 预演模式增强（新增 2025-12-29）

> **需求来源**: Requirement 5.1-5.5
> **预计工时**: 8-10 小时

### 5.1 预演模式数据隔离

- [ ] 5.1.1 创建预演 Beatboard 状态管理
  - 在 `PreviewTab.tsx` 中添加独立的预演数据状态
  - 实现 `initPreviewData()` - 从主 Beatboard 复制数据
  - 实现 `syncToMain()` - 同步预演数据到主 Beatboard
  - 实现 `discardPreviewChanges()` - 丢弃预演修改
  - _Requirements: 5.1.1, 5.1.2, 5.1.3, 5.1.4_

- [ ] 5.1.2 添加数据来源标识 UI
  - 在预演模式顶部显示当前数据来源（预演数据/主数据）
  - 添加"同步到主 Beatboard"按钮
  - 添加未同步修改提示
  - _Requirements: 5.1.5_

### 5.2 真实音频轨道

- [ ] 5.2.1 创建音频轨道组件
  - 创建 `frontend/components/Timeline/AudioTrack.tsx`
  - 实现波形显示（使用 wavesurfer.js 或 canvas）
  - 支持 4 种轨道类型：原声、BGM、音效、对白
  - _Requirements: 5.2.1, 5.2.2_

- [ ] 5.2.2 实现音频轨道控制
  - 添加音量滑块控制
  - 添加静音/取消静音按钮
  - 添加独奏按钮
  - 显示音频时长
  - _Requirements: 5.2.3, 5.2.4, 5.2.5_

- [ ] 5.2.3 后端波形生成服务
  - 创建 `backend/services/waveform_generator.py`
  - 使用 FFmpeg 提取音频数据
  - 生成波形数据数组
  - 缓存波形数据
  - _Requirements: 5.2.5_

### 5.3 音视频分离功能

- [ ] 5.3.1 后端音视频分离 API
  - 创建 `POST /api/timeline/split-audio-video` 端点
  - 使用 FFmpeg 分离音视频
  - 返回分离后的文件路径和波形数据
  - _Requirements: 5.3.1, 5.3.2_

- [ ] 5.3.2 后端音视频合并 API
  - 创建 `POST /api/timeline/merge-audio-video` 端点
  - 使用 FFmpeg 合并音视频
  - _Requirements: 5.3.5_

- [ ] 5.3.3 前端分离/合并 UI
  - 在时间轴片段上添加"一键切开音视频"按钮
  - 分离后显示独立的音频轨道
  - 支持重新关联（合并）操作
  - _Requirements: 5.3.1, 5.3.3, 5.3.4_

### 5.4 Beatboard 只选取视频功能

- [ ] 5.4.1 添加发送选项
  - 在 Beatboard 发送到时间轴时添加选项弹窗
  - 提供"保留原声"和"只选取视频（静音）"选项
  - 默认为"保留原声"
  - _Requirements: 5.4.1, 5.4.2, 5.4.3, 5.4.4_

### 5.5 Beatboard 重新分析功能

- [ ] 5.5.1 后端重新分析 API
  - 创建 `POST /api/beatboard/reanalyze` 端点
  - 支持单场次和全局分析模式
  - 基于最新资产库重新搜索匹配素材
  - 返回与之前结果的差异
  - _Requirements: 5.5.1, 5.5.2, 5.5.3_

- [ ] 5.5.2 前端重新分析 UI
  - 在 Beatboard 添加"重新分析"按钮
  - 显示分析模式选择对话框
  - 显示分析进度
  - 显示分析结果差异
  - _Requirements: 5.5.4, 5.5.5_

### Phase 5 Checkpoint

- [ ] 验证预演模式数据隔离正常工作
- [ ] 验证音频轨道波形显示正确
- [ ] 验证音视频分离/合并功能正常
- [ ] 验证 Beatboard 静音发送功能正常
- [ ] 验证重新分析功能正常
- 验证日期: 待定
- **Phase 5 状态: 待开始**
