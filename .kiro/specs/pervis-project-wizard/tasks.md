# Implementation Plan: Pervis PRO 项目立项向导系统

## Overview

本实现计划采用 MVP 简化方案，将 Agent 功能直接集成到 Pervis PRO 后端，保留 Agent 概念和状态显示。

**Agent 工作流程**：
1. Script_Agent / Art_Agent 执行任务
2. Director_Agent 审核输出
3. 返回结果给用户确认

**实现顺序**：
1. 后端 AgentService 层（Script_Agent、Art_Agent、Director_Agent）
2. 后端 API 端点
3. 前端向导组件（含 Agent 状态显示）
4. 前端与后端集成

## Tasks

- [ ] 1. 后端 AgentService 层

  - [ ] 1.1 创建 AgentService 基础架构
    - 创建 `backend/services/agent_service.py`
    - 实现 Agent 任务调度和状态管理
    - 实现 Agent 工作流程（执行 → 审核 → 返回）
    - _Requirements: 5.3, 5.4, 9.1_

  - [ ] 1.2 实现 Script_Agent（编剧 Agent）
    - 创建 `backend/services/agents/script_agent.py`
    - 实现 `parse_script()` - 剧本解析
    - 实现 `generate_logline()` - Logline 生成
    - 实现 `generate_synopsis()` - Synopsis 生成
    - 实现 `generate_character_bio()` - 人物小传生成
    - 实现 `estimate_scene_duration()` - 时长估算
    - _Requirements: 2.2, 5.1_

  - [ ] 1.3 实现 Art_Agent（美术 Agent）
    - 创建 `backend/services/agents/art_agent.py`
    - 实现 `classify_file()` - 文件分类
    - 实现 `extract_metadata()` - 元数据提取
    - 实现 `generate_tags()` - 标签生成
    - 实现 `create_thumbnail()` - 缩略图生成
    - _Requirements: 3.2, 5.2, 11.1_

  - [ ] 1.4 实现 Director_Agent（导演 Agent）- 有项目记忆
    - 创建 `backend/services/agents/director_agent.py`
    - 实现 `review()` - 审核其他 Agent 输出
    - 实现 `_check_rules()` - 规则校验（内容不为空、字数合理、格式正确）
    - 实现 `_check_project_specs()` - 项目规格一致性检查
    - 实现 `_check_style_consistency()` - 艺术风格一致性检查（LLM）
    - 实现 `_compare_with_history()` - 历史版本对比（避免改回被否决版本）
    - _Requirements: 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.1.5_

  - [ ] 1.5 实现 PM_Agent（项目管理 Agent）- 隐藏
    - 创建 `backend/services/agents/pm_agent.py`
    - 实现 `get_project_context()` - 获取项目上下文
    - 实现 `record_version()` - 记录版本
    - 实现 `record_decision()` - 记录用户决策
    - _Requirements: 5.2.1, 5.2.2, 5.2.3, 5.2.4, 5.2.5_


- [ ] 2. 后端数据模型

  - [ ] 2.1 创建 ProjectWizardDraft 模型
    - 创建 `backend/models/wizard_draft.py`
    - 保存用户建档进度
    - _Requirements: 7.4_

  - [ ] 2.2 创建 ProjectTemplate 模型
    - 创建 `backend/models/project_template.py`
    - 支持系统预设和用户自定义模板
    - _Requirements: 8.1, 8.3_

  - [ ] 2.3 创建 AgentTask 模型
    - 创建 `backend/models/agent_task.py`
    - 记录 Agent 任务状态（agent_type, task_type, status, current_step）
    - _Requirements: 9.1, 9.2_

  - [ ] 2.4 创建 ProjectContext 相关模型（PM_Agent 使用）
    - 创建 `backend/models/project_context.py`
    - ProjectSpecs 表（项目规格：时长、画幅、帧率、分辨率）
    - StyleContext 表（艺术风格：描述、对标项目、色彩、情绪）
    - ContentVersion 表（版本历史：内容类型、内容、Agent、时间）
    - UserDecision 表（用户决策：版本ID、决策、反馈）
    - _Requirements: 5.1.2, 5.2.2_

  - [ ] 2.5 创建数据库迁移脚本
    - 添加新表到数据库
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 3. 后端 API 端点

  - [ ] 3.1 创建 Wizard API 路由
    - 创建 `backend/routers/wizard.py`
    - 实现 `POST /api/wizard/parse-script` (Script_Agent)
    - 实现 `POST /api/wizard/generate-content` (Script_Agent/Art_Agent)
    - _Requirements: 2.1, 5.1_

  - [ ] 3.2 实现素材处理 API
    - 实现 `POST /api/wizard/process-assets` (Art_Agent)
    - 实现批量文件上传处理
    - _Requirements: 3.1, 3.2, 11.1_

  - [ ] 3.3 实现项目创建 API
    - 实现 `POST /api/wizard/create-project`
    - 实现 `GET /api/wizard/templates`
    - 实现 `POST /api/wizard/templates` (保存自定义模板)
    - _Requirements: 7.6, 8.1_

  - [ ] 3.4 实现 Agent 任务状态 API
    - 实现 `GET /api/wizard/task-status/{task_id}`
    - 返回 agent_type, status, current_step（如"编剧 Agent 正在工作..."）
    - 实现 `GET /api/wizard/draft/{draft_id}`
    - 实现 `PUT /api/wizard/draft/{draft_id}`
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 4. Checkpoint - 后端功能验证
  - 确保所有后端 API 可正常调用
  - 确保 Agent 工作流程正常（执行 → 审核 → 返回）
  - 确保 Agent 状态正确返回
  - 如有问题请询问用户

- [ ] 5. 前端向导组件

  - [ ] 5.1 创建 ProjectWizard 主组件
    - 创建 `frontend/components/ProjectWizard/index.tsx`
    - 实现步骤导航
    - 实现进度显示
    - _Requirements: 1.3, 1.4, 7.1_

  - [ ] 5.2 实现 Step1 基本信息
    - 创建 `WizardStep1_BasicInfo.tsx`
    - 项目标题、类型、时长、画幅、帧率
    - _Requirements: 1.2_

  - [ ] 5.3 实现 Step2 剧本导入
    - 创建 `WizardStep2_Script.tsx`
    - 文件上传组件
    - 剧本文本编辑器
    - Agent 状态显示（"编剧 Agent 正在工作..." → "导演 Agent 审核中..."）
    - _Requirements: 2.1, 2.2, 2.3, 9.2, 9.4_

  - [ ] 5.4 实现 Step3 角色设定
    - 创建 `WizardStep3_Characters.tsx`
    - 角色列表编辑
    - 人物小传生成按钮（显示 Agent 状态）
    - _Requirements: 1.2, 5.1, 9.2_

  - [ ] 5.5 实现 Step4 场次规划
    - 创建 `WizardStep4_Scenes.tsx`
    - 场次列表编辑
    - 时长估算显示（显示 Agent 状态）
    - _Requirements: 1.2, 5.1, 9.2_

  - [ ] 5.6 实现 Step5 参考资料
    - 创建 `WizardStep5_References.tsx`
    - 批量文件上传
    - 素材预览和标签显示（显示 Art_Agent 状态）
    - _Requirements: 3.1, 11.1, 9.3_

  - [ ] 5.7 实现 Step6 确认提交
    - 创建 `WizardStep6_Confirm.tsx`
    - 项目预览
    - 验证和提交
    - _Requirements: 6.1, 7.5, 7.6_

- [ ] 6. 前端辅助组件

  - [ ] 6.1 创建 AgentStatusPanel
    - 创建 `frontend/components/AgentStatusPanel.tsx`
    - 显示当前 Agent 名称和状态
    - 显示工作流程进度（执行 → 审核 → 完成）
    - 显示进度条
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.9_

  - [ ] 6.2 创建 MissingContentDialog
    - 创建 `frontend/components/MissingContentDialog.tsx`
    - 缺失字段列表（显示负责的 Agent）
    - 三种处理选项
    - 批量操作
    - _Requirements: 4.1, 4.2, 4.6_

  - [ ] 6.3 创建 ProjectPreview
    - 创建 `frontend/components/ProjectPreview.tsx`
    - 完整项目信息预览
    - 字段状态标记（用户输入/Script_Agent/Art_Agent）
    - _Requirements: 1.3, 7.5, 5.6_

- [ ] 7. 前端 API 集成

  - [ ] 7.1 创建 Wizard API 客户端
    - 在 `frontend/services/apiClient.ts` 添加 wizard 相关 API
    - 实现 `parseScript()`
    - 实现 `generateContent()`
    - 实现 `processAssets()`
    - _Requirements: 10.3_

  - [ ] 7.2 实现 Agent 任务状态轮询
    - 实现 `getTaskStatus()` 轮询逻辑
    - 处理 Agent 状态变化（working → reviewing → completed）
    - 更新 AgentStatusPanel 显示
    - _Requirements: 10.4, 9.2, 9.4_

  - [ ] 7.3 实现草稿保存/恢复
    - 实现 `saveDraft()`
    - 实现 `loadDraft()`
    - _Requirements: 7.4_

- [ ] 8. 页面集成

  - [ ] 8.1 添加项目创建入口
    - 在首页添加"新建项目"按钮
    - 路由到 ProjectWizard 页面
    - _Requirements: 10.1_

  - [ ] 8.2 实现模板选择页面
    - 显示预设模板列表
    - 显示用户自定义模板
    - _Requirements: 8.1, 8.2_

  - [ ] 8.3 实现项目创建完成跳转
    - 创建项目后跳转到 Analysis 阶段
    - 传递项目 ID
    - _Requirements: 10.5_

- [ ] 9. Final Checkpoint - 完整功能验证
  - 确保完整建档流程可用
  - 确保 Agent 状态显示正确（"编剧 Agent 正在工作..." → "导演 Agent 审核中..."）
  - 确保素材处理和标签生成正常
  - 确保与 Beatboard 阶段数据衔接正常
  - 如有问题请询问用户

## Notes

- 本 spec 采用 MVP 简化方案，Agent 功能直接集成到 Pervis PRO 后端
- 保留 Agent 概念和状态显示（Script_Agent、Art_Agent、Director_Agent、PM_Agent）
- **Director_Agent 审核机制**：
  - 规则校验（内容不为空、字数合理、格式正确）
  - 项目规格一致性检查（时长、画幅、帧率）
  - 艺术风格一致性检查（使用 LLM）
  - 历史版本对比（避免改回被否决的版本）
- **PM_Agent（隐藏）**：
  - 管理项目规格和版本记录
  - 为 Director_Agent 提供项目上下文
  - MVP 阶段只做基础功能
- Agent 工作流程：执行 → Director_Agent 审核 → 返回结果
- 后续可迁移到独立 Agent 服务架构（消息总线通信）
- 素材处理结果将用于 Beatboard 阶段的素材召回
- multi-agent-workflow 项目的 Agent 架构保留作为后续参考
