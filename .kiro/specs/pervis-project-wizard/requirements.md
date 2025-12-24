# Requirements Document

## Introduction

Pervis PRO 项目立项向导系统需求文档。本系统为导演工作台提供智能化的项目建档功能，支持从脚本或多个相关文件自动生成完整的项目立项内容，并在信息不完整时提供多种补全方式。

**MVP 策略**：为了快速验证产品价值，本 spec 采用简化版 Agent 集成方案，将 AI 功能直接集成到 Pervis PRO 后端，而非依赖独立的 multi-agent-workflow 项目。后续产品验证后可迁移到独立 Agent 服务架构。

## Glossary

- **Project_Wizard**: 项目立项向导，引导用户完成项目建档的智能系统
- **Project_Info**: 项目信息，包含项目基本信息、剧本、角色、场次等所有立项内容
- **Placeholder**: 占位符，用于标记待补充的内容
- **Script**: 剧本文件，项目的核心输入
- **Synopsis**: 故事概要，项目的简短描述
- **Logline**: 一句话概括，项目的核心卖点
- **Script_Agent**: 编剧 Agent，负责剧本解析、大纲生成、人物小传、时长估算
- **Art_Agent**: 美术 Agent，负责视觉风格分析、标签生成
- **Director_Agent**: 导演 Agent，负责审核其他 Agent 的输出结果，具有项目记忆，了解项目规格和历史决策
- **PM_Agent**: 项目管理 Agent（隐藏），负责管理项目规格、版本记录，MVP 阶段只做基础功能
- **Project_Context**: 项目上下文，包含项目规格（时长、画幅）、艺术风格、对标项目、历史版本等信息
- **AgentService**: Agent 服务层，封装各 Agent 的 LLM 调用，管理 Agent 工作流程

## Requirements

### Requirement 1: 项目信息完整展示

**User Story:** As a 导演/制片人, I want to 在项目建档时看到所有需要填写的项目信息, so that 我可以清楚了解需要准备哪些内容。

#### Acceptance Criteria

1. WHEN 用户进入项目建档页面 THEN THE Project_Wizard SHALL 展示完整的项目信息表单
2. THE Project_Wizard SHALL 展示以下项目信息字段：
   - 项目基本信息（标题、类型、时长、画幅比例、帧率）
   - Logline（一句话概括）
   - Synopsis（故事概要）
   - 完整剧本
   - 角色列表（名称、描述、重要性、人物小传）
   - 场次大纲（场次号、场景、时长、描述）
   - 参考资料（风格参考、视觉参考）
   - 制作信息（预算范围、制作周期、团队规模）
3. THE Project_Wizard SHALL 对每个字段显示填写状态（已填写/未填写/AI生成/处理中）
4. THE Project_Wizard SHALL 显示整体完成度百分比
5. THE Project_Wizard SHALL 显示当前 AI 处理状态

### Requirement 2: 脚本导入与解析

**User Story:** As a 导演, I want to 导入剧本文件并自动解析, so that 系统可以自动提取项目信息。

#### Acceptance Criteria

1. WHEN 用户上传剧本文件 THEN THE Project_Wizard SHALL 支持以下格式：TXT、PDF、DOCX、FDX（Final Draft）
2. WHEN 剧本上传成功 THEN THE Script_Agent SHALL 自动解析并提取：
   - 场次信息（场景标题、INT/EXT、日/夜）
   - 角色名称（从对话中提取）
   - 动作描述
   - 对话内容
3. WHEN Script_Agent 解析完成 THEN THE Director_Agent SHALL 审核解析结果
4. WHEN Director_Agent 审核通过 THEN THE Project_Wizard SHALL 自动填充相关字段
5. IF 解析失败 THEN THE Project_Wizard SHALL 显示错误信息并提供手动输入选项
6. WHEN 剧本解析完成 THEN THE Script_Agent SHALL 生成剧本结构分析报告

### Requirement 3: 多文件批量导入

**User Story:** As a 制片人, I want to 批量导入多个项目相关文件, so that 系统可以从多个来源整合项目信息。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 支持批量导入以下文件类型：
   - 剧本文件（TXT、PDF、DOCX、FDX）
   - 参考图片（JPG、PNG）
   - 参考视频（MP4、MOV）
   - 项目文档（PDF、DOCX）
   - 预算表格（XLSX、CSV）
2. WHEN 用户批量上传文件 THEN THE Art_Agent SHALL 自动识别文件类型并分类
3. WHEN 文件分类完成 THEN THE Project_Wizard SHALL 从各类文件中提取相关信息
4. THE Project_Wizard SHALL 显示文件导入进度和处理状态
5. WHEN 参考图片/视频上传 THEN THE Art_Agent SHALL 分析视觉风格并生成标签

### Requirement 4: 缺失内容处理

**User Story:** As a 用户, I want to 在项目信息不完整时选择如何处理缺失内容, so that 我可以灵活地完成项目建档。

#### Acceptance Criteria

1. WHEN 用户尝试保存项目且存在缺失字段 THEN THE Project_Wizard SHALL 弹出缺失内容处理对话框
2. THE Project_Wizard SHALL 对每个缺失字段提供三种处理选项：
   - 使用占位符（标记为"待补充"）
   - 使用 Agent 生成参考内容
   - 手动上传/填写
3. WHEN 用户选择"使用占位符" THEN THE Project_Wizard SHALL 在该字段填入占位文本并标记状态
4. WHEN 用户选择"Agent 生成" THEN THE 对应 Agent SHALL 生成内容并由 Director_Agent 审核
5. WHEN 用户选择"手动上传" THEN THE Project_Wizard SHALL 打开对应的上传/编辑界面
6. THE Project_Wizard SHALL 允许用户批量选择处理方式（如"全部使用 Agent 生成"）

### Requirement 5: Agent 协作内容生成

**User Story:** As a 导演, I want to 使用专业 Agent 自动生成缺失的项目内容, so that 我可以获得专业的内容建议并了解每个 Agent 的工作状态。

#### Acceptance Criteria

1. WHEN 需要生成剧本相关内容 THEN THE Script_Agent SHALL 负责：
   - Logline 生成（基于剧本生成一句话概括）
   - Synopsis 生成（基于剧本生成故事概要）
   - 剧本大纲生成（基于完整剧本提炼大纲）
   - 人物小传生成（基于角色行为和对话生成）
   - 场次时长估算（基于场次内容估算）
2. WHEN 需要生成视觉相关内容 THEN THE Art_Agent SHALL 负责：
   - 视觉风格分析（基于参考资料分析）
   - 素材标签生成（内容、风格、技术标签）
   - 角色视觉描述（基于人物小传生成）
   - 场景视觉描述（基于场次描述生成）
3. WHEN Script_Agent 或 Art_Agent 完成工作 THEN THE Director_Agent SHALL 审核输出结果
4. WHEN Director_Agent 审核时 SHALL 参考 Project_Context（项目规格、艺术风格、历史版本）
5. WHEN Director_Agent 审核通过 THEN THE Project_Wizard SHALL 显示生成结果
6. THE Project_Wizard SHALL 允许用户编辑 Agent 生成的内容
7. THE Project_Wizard SHALL 标记内容来源（用户输入/Script_Agent/Art_Agent）

### Requirement 5.1: Director_Agent 审核机制

**User Story:** As a 导演, I want to Director_Agent 能够记住项目的基本属性和历史决策, so that 审核时不会出现前后矛盾的建议。

#### Acceptance Criteria

1. THE Director_Agent SHALL 在审核时执行以下检查：
   - 规则校验（内容不为空、字数合理、格式正确）
   - 项目规格一致性（时长、画幅、帧率是否符合项目设定）
   - 艺术风格一致性（是否符合已确定的视觉风格）
   - 历史版本对比（避免改回之前被否决的版本）
2. THE Director_Agent SHALL 具有项目记忆，包括：
   - 项目基本规格（时长、画幅、帧率）
   - 已确定的艺术风格和对标项目
   - 之前的生成版本和用户反馈
   - 用户的修改历史
3. WHEN 审核发现问题 THEN THE Director_Agent SHALL 返回具体的改进建议
4. WHEN 审核通过 THEN THE Director_Agent SHALL 返回"审核通过"状态
5. THE Director_Agent SHALL 不会建议与之前已确认内容矛盾的修改

### Requirement 5.2: PM_Agent 项目管理（隐藏）

**User Story:** As a 系统, I want to PM_Agent 在后台管理项目规格和版本记录, so that 其他 Agent 可以获取准确的项目上下文。

#### Acceptance Criteria

1. THE PM_Agent SHALL 在后台运行，用户不可见
2. THE PM_Agent SHALL 管理以下项目信息（MVP 阶段）：
   - 项目规格（时长、画幅、帧率、分辨率）
   - 版本记录（每次 Agent 生成的内容版本）
   - 用户确认记录（用户接受/拒绝的历史）
3. WHEN 其他 Agent 需要项目上下文 THEN THE PM_Agent SHALL 提供 Project_Context
4. WHEN 用户确认内容 THEN THE PM_Agent SHALL 记录版本和决策
5. THE PM_Agent SHALL 为 Director_Agent 提供历史版本对比数据

### Requirement 6: 项目信息验证

**User Story:** As a 系统, I want to 验证项目信息的完整性和有效性, so that 可以确保项目建档质量。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 验证必填字段是否已填写：
   - 项目标题（必填）
   - 项目类型（必填）
   - 剧本或故事概要（至少一项）
2. THE Project_Wizard SHALL 验证字段格式：
   - 时长为正整数（秒）
   - 画幅比例为有效格式（如 16:9、4:3）
   - 帧率为有效值（如 24、25、30）
3. IF 验证失败 THEN THE Project_Wizard SHALL 显示具体的错误信息
4. WHEN 验证通过 THEN THE Project_Wizard SHALL 允许保存项目

### Requirement 7: 项目建档流程

**User Story:** As a 用户, I want to 通过清晰的步骤完成项目建档, so that 我可以有序地准备项目信息。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 提供分步骤的建档流程：
   - 步骤 1：基本信息（标题、类型、时长、画幅）
   - 步骤 2：剧本导入（上传或粘贴剧本）→ Script_Agent 解析 → Director_Agent 审核
   - 步骤 3：角色设定（角色列表和人物小传）→ Script_Agent 生成 → Director_Agent 审核
   - 步骤 4：场次规划（场次大纲和时长）→ Script_Agent 评估 → Director_Agent 审核
   - 步骤 5：参考资料（风格和视觉参考）→ Art_Agent 分析 → Director_Agent 审核
   - 步骤 6：确认提交（预览和最终确认）
2. THE Project_Wizard SHALL 在每个步骤显示当前 Agent 的状态（工作中/审核中/完成）
3. THE Project_Wizard SHALL 允许用户在步骤间自由跳转
4. THE Project_Wizard SHALL 保存用户在每个步骤的进度
5. WHEN 用户完成所有步骤 THEN THE Project_Wizard SHALL 显示项目预览页面
6. WHEN 用户确认提交 THEN THE Project_Wizard SHALL 创建项目并进入下一阶段

### Requirement 8: 项目模板

**User Story:** As a 用户, I want to 使用项目模板快速开始, so that 我可以节省重复填写的时间。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 提供预设项目模板：
   - 短片模板（5-30分钟）
   - 广告模板（15-60秒）
   - MV 模板（3-5分钟）
   - 长片模板（90-120分钟）
   - 自定义模板
2. WHEN 用户选择模板 THEN THE Project_Wizard SHALL 预填充模板默认值
3. THE Project_Wizard SHALL 允许用户保存当前项目为模板
4. THE Project_Wizard SHALL 允许用户管理（编辑/删除）自定义模板

### Requirement 9: Agent 状态展示与交互

**User Story:** As a 用户, I want to 看到每个 Agent 的工作状态和审核流程, so that 我可以了解 AI 辅助的进度和结果。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 在界面上显示当前活跃的 Agent 列表（Script_Agent、Art_Agent、Director_Agent）
2. WHEN Script_Agent 正在处理任务 THEN THE Project_Wizard SHALL 显示"编剧 Agent 正在工作..."
3. WHEN Art_Agent 正在处理任务 THEN THE Project_Wizard SHALL 显示"美术 Agent 正在工作..."
4. WHEN Agent 完成任务并提交审核 THEN THE Project_Wizard SHALL 显示"导演 Agent 审核中..."
5. WHEN Director_Agent 审核通过 THEN THE Project_Wizard SHALL 显示结果摘要
6. THE Project_Wizard SHALL 允许用户查看 Agent 的详细建议
7. THE Project_Wizard SHALL 允许用户接受或拒绝 Agent 的建议
8. IF Agent 处理失败 THEN THE Project_Wizard SHALL 显示错误信息并提供重试选项
9. THE Project_Wizard SHALL 显示 Agent 工作流程图示：
   - Script_Agent/Art_Agent 工作 → Director_Agent 审核 → 用户确认

### Requirement 10: 前端与现有系统集成

**User Story:** As a 开发者, I want to 将立项向导与现有前端系统集成, so that 用户可以无缝使用新功能。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 集成到现有的 Pervis PRO 前端应用
2. THE Project_Wizard SHALL 复用现有的 UI 组件和样式
3. THE Project_Wizard SHALL 通过 REST API 与后端 AgentService 通信
4. THE Project_Wizard SHALL 使用轮询接收 Agent 处理状态更新
5. WHEN 项目创建完成 THEN THE Project_Wizard SHALL 跳转到 Analysis 阶段页面

### Requirement 11: 素材处理与 Beatboard 集成

**User Story:** As a 导演, I want to 上传的参考素材能够自动处理并在 Beatboard 中匹配使用, so that 我可以快速找到合适的参考。

#### Acceptance Criteria

1. WHEN 用户上传参考图片/视频 THEN THE Art_Agent SHALL：
   - 生成缩略图和代理文件
   - 提取元数据（分辨率、时长、颜色信息）
   - 使用 AI 生成描述标签
   - 存储到素材库
2. WHEN 项目立项完成 THEN THE Project_Wizard SHALL 将所有项目信息打包传递给 Beatboard 阶段
3. THE Beatboard 阶段 SHALL 基于项目信息（角色、场次、风格）从素材库中召回匹配的参考
4. THE Art_Agent SHALL 支持以下标签类型：
   - 内容标签（人物、场景、物品）
   - 风格标签（色调、构图、氛围）
   - 技术标签（分辨率、格式、时长）

## Architecture Notes (MVP 简化版)

### Agent 工作流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent 协作流程                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户触发任务（如：生成人物小传）                                   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────┐                                                │
│  │  Script_Agent   │  ← 显示"编剧 Agent 正在工作..."               │
│  │  (编剧 Agent)   │                                                │
│  └────────┬────────┘                                                │
│           │ 完成                                                     │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │ Director_Agent  │  ← 显示"导演 Agent 审核中..."                 │
│  │  (导演 Agent)   │                                                │
│  └────────┬────────┘                                                │
│           │ 审核通过                                                 │
│           ▼                                                          │
│  ┌─────────────────┐                                                │
│  │   用户确认      │  ← 显示结果，用户可接受/拒绝/编辑              │
│  └─────────────────┘                                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 与 multi-agent-workflow 的关系

multi-agent-workflow 项目定义了完整的 Agent 协作架构（消息总线通信），但目前：
- ✅ 后端 Agent 已实现
- ❌ 没有 REST API 暴露给前端
- ❌ 没有与 Pervis PRO 前端集成

### MVP 策略

为了快速验证产品价值，本 spec 采用简化方案：

1. **AgentService（Agent 服务层）**
   - 直接集成到 Pervis PRO 后端
   - 封装 Script_Agent、Art_Agent、Director_Agent 的 LLM 调用
   - 管理 Agent 工作流程（执行 → 审核 → 返回）
   - 通过 REST API 暴露给前端

2. **前端 Agent 状态显示**
   - 显示当前工作的 Agent 名称和状态
   - 显示 Agent 工作流程进度
   - 显示 Director_Agent 审核状态

3. **后续迁移路径**
   - 产品验证后，可将 AgentService 迁移到独立的 Agent 服务
   - 添加 WebSocket 实时通信
   - 集成完整的 multi-agent-workflow 架构（消息总线）
