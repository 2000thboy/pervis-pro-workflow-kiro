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
- **PM_Agent**: 项目助理（用户可见），负责管理项目规格、版本记录、版本命名，MVP 阶段只做基础功能
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
   - 【MVP 阶段不需要预算相关字段】
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

### Requirement 3: 多文件批量导入与智能分类

**User Story:** As a 制片人, I want to 批量导入多个项目相关文件, so that 系统可以从多个来源整合项目信息并智能分类到对应界面。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 支持批量导入以下文件类型：
   - 剧本文件（TXT、PDF、DOCX、FDX）
   - 人物小传文档（TXT、PDF、DOCX）
   - 人设美术资料（JPG、PNG、PSD）
   - 场景描述文档（TXT、PDF、DOCX）
   - 场景参考图片（JPG、PNG）
   - 参考视频（MP4、MOV、AVI）
   - 项目文档（PDF、DOCX）
   - 其他多媒体文件（音频、图片等）
2. WHEN 用户批量上传文件 THEN THE Art_Agent SHALL 自动识别文件类型并智能分类：
   - 角色相关内容 → 角色界面
   - 场景相关内容 → 场景界面
   - 无法识别的参考图 → 参考界面（等待用户手动分类）
3. WHEN Art_Agent 无法分类参考内容 THEN THE Project_Wizard SHALL：
   - 显示在参考界面中
   - 要求用户修改命名并打好"参考"标签
   - 提供手动分类到角色参考或场景参考的选项
4. THE Project_Wizard SHALL 显示文件导入进度和处理状态
5. WHEN 参考图片/视频上传 THEN THE Art_Agent SHALL 分析视觉风格并生成标签
6. THE Art_Agent SHALL 识别图像特征并生成对应标签，但角色基础属性优先使用 Script_Agent 解析结果

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

### Requirement 5: Agent 协作内容生成与智能分类

**User Story:** As a 导演, I want to 使用专业 Agent 自动生成缺失的项目内容并智能分类到对应界面, so that 我可以获得专业的内容建议并了解每个 Agent 的工作状态。

#### Acceptance Criteria

1. WHEN 需要生成剧本相关内容 THEN THE Script_Agent SHALL 负责：
   - Logline 生成（基于剧本生成一句话概括）
   - Synopsis 生成（基于剧本生成故事概要）
   - 剧本大纲生成（基于完整剧本提炼大纲）
   - 人物小传生成（基于角色行为和对话生成）
   - 角色基础标签生成（包括所有基础属性：外观描述、性别、身高等）
   - 场次时长估算（基于场次内容估算）
2. WHEN Script_Agent 生成角色基础标签 THEN THE Project_Wizard SHALL：
   - 返回用户确认，列出所有基础属性
   - 提供滑动选择界面方便用户选择
   - 角色基础属性优先使用 Script_Agent 结果，不被 Art_Agent 覆盖
3. WHEN 需要生成视觉相关内容 THEN THE Art_Agent SHALL 负责：
   - 视觉风格分析（基于参考资料分析）
   - 素材标签生成（内容、风格、技术标签）
   - 角色视觉描述（基于人物小传生成，但不覆盖 Script_Agent 的基础属性）
   - 场景视觉描述（基于场次描述生成）
   - 参考资料智能分类（识别并分类到角色、场景、参考界面）
4. WHEN Art_Agent 处理参考资料 THEN THE Project_Wizard SHALL：
   - 可选择生成或隐藏 Art_Agent 功能
   - 只显示上传图片，尽量不使用图像生成式 AI
   - 需要用户确认 Art_Agent 的分类结果
5. WHEN Script_Agent 或 Art_Agent 完成工作 THEN THE Director_Agent SHALL 审核输出结果
6. WHEN Director_Agent 审核时 SHALL 参考 Project_Context（项目规格、艺术风格、历史版本）
7. WHEN Director_Agent 审核通过 THEN THE Project_Wizard SHALL 显示生成结果
8. THE Project_Wizard SHALL 允许用户编辑 Agent 生成的内容
9. THE Project_Wizard SHALL 标记内容来源（用户输入/Script_Agent/Art_Agent）

### Requirement 5.1: Director_Agent 审核机制与全程建议模式

**User Story:** As a 导演, I want to Director_Agent 能够记住项目的基本属性和历史决策，并全程只输出审核建议, so that 审核时不会出现前后矛盾的建议，且我能清晰看到内容和意见。

#### Acceptance Criteria

1. THE Director_Agent SHALL 全程只输出审核建议，需要用户进行确认
2. WHEN Director_Agent 提供建议 THEN THE Project_Wizard SHALL：
   - 清晰展示内容以及 Agent 的意见
   - 方便用户审阅和做出决策
   - 显示建议的具体原因和改进方向
3. THE Director_Agent SHALL 在审核时执行以下检查：
   - 规则校验（内容不为空、字数合理、格式正确）
   - 项目规格一致性（时长、画幅、帧率是否符合项目设定）
   - 艺术风格一致性（是否符合已确定的视觉风格）
   - 历史版本对比（避免改回之前被否决的版本）
4. THE Director_Agent SHALL 具有项目记忆，包括：
   - 项目基本规格（时长、画幅、帧率）
   - 已确定的艺术风格和对标项目
   - 之前的生成版本和用户反馈
   - 用户的修改历史
5. WHEN 审核发现问题 THEN THE Director_Agent SHALL 返回具体的改进建议
6. WHEN 审核通过 THEN THE Director_Agent SHALL 返回"审核通过"状态
7. THE Director_Agent SHALL 不会建议与之前已确认内容矛盾的修改

### Requirement 5.1.8: Script_Agent 视觉分析能力（人设/参考图标签生成）

**User Story:** As a 导演, I want to Script_Agent 能够分析上传的人设图和参考图并生成对应标签, so that 我可以在剧本环节就为角色和场景建立完整的视觉标签体系。

#### Acceptance Criteria

1. THE Script_Agent SHALL 具备调用视觉模型的能力（通过 `ollama_vision.py`）
2. WHEN 用户上传人设图或角色参考图 THEN THE Script_Agent SHALL：
   - 调用视觉模型分析图像内容
   - 识别角色的视觉特征（外观、服装、配饰等）
   - 生成角色视觉标签（与剧本中的角色关联）
3. WHEN 用户上传场景参考图 THEN THE Script_Agent SHALL：
   - 调用视觉模型分析场景内容
   - 识别场景类型（室内/室外）、时间（日/夜）、环境特征
   - 生成场景视觉标签（与剧本中的场次关联）
4. THE Script_Agent 生成的视觉标签 SHALL 包括：
   - 角色标签：外观描述、服装风格、配色、特征道具
   - 场景标签：场景类型、光线、氛围、环境元素
5. WHEN Script_Agent 完成视觉分析 THEN THE Project_Wizard SHALL：
   - 返回用户确认，展示识别出的标签
   - 提供标签编辑界面，允许用户修改或补充
   - 显示原图与标签的对应关系
6. WHEN 用户确认标签 THEN THE Script_Agent SHALL：
   - 将标签与对应的角色/场景关联
   - 将确认后的标签发送到资产管理模块
   - 更新资产库中的标签索引
7. THE 视觉模型 SHALL 作为必选依赖，因为：
   - 导入内容是多模态的（文本+图像）
   - 需要根据人设参考生成对应标签
   - 标签用于后续的素材召回和匹配
8. THE Script_Agent 视觉分析 SHALL 在剧本环节触发，而非资产管理环节
9. THE 以图搜图功能 SHALL 暂不启用，仅使用视觉模型进行标签生成

### Requirement 5.2: PM_Agent 项目助理（用户可见）

**User Story:** As a 用户, I want to 看到项目的版本历史和修改记录, so that 我可以了解项目的迭代过程并随时恢复到之前的版本。

#### Acceptance Criteria

1. THE PM_Agent SHALL 在界面上显示版本信息，用户可见
2. THE PM_Agent SHALL 管理以下项目信息（MVP 阶段）：
   - 项目规格（时长、画幅、帧率、分辨率）
   - 版本记录（每次 Agent 生成的内容版本）
   - 用户确认记录（用户接受/拒绝的历史）
   - 艺术风格（已确定的视觉风格、对标项目）
3. THE PM_Agent SHALL 自动写入版本号到文件名：
   - 格式：`{内容类型}_{名称}_v{版本号}.{扩展名}`
   - 示例：`角色_张三_v1.json` → `角色_张三_v2.json` → `角色_张三_v3.json`
4. THE PM_Agent SHALL 在界面上显示：
   - 当前版本号
   - 最后修改时间
   - 修改历史列表（版本号、修改内容、修改来源）
   - 恢复到历史版本的选项
5. WHEN 其他 Agent 需要项目上下文 THEN THE PM_Agent SHALL 提供 Project_Context
6. WHEN 用户确认内容 THEN THE PM_Agent SHALL 记录版本和决策
7. THE PM_Agent SHALL 为 Director_Agent 提供历史版本对比数据

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

### Requirement 7: 项目建档流程优化

**User Story:** As a 用户, I want to 通过清晰的步骤完成项目建档, so that 我可以有序地准备项目信息，且系统能自动处理已上传的内容。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 提供分步骤的建档流程：
   - 步骤 1：基本信息（标题、类型、时长、画幅）
   - 步骤 2：剧本导入与自动处理（用户已上传剧本，系统直接处理）→ Script_Agent 解析 → Director_Agent 审核
   - 步骤 3：角色设定与场景设定
     - 3A：角色设定（角色列表和人物小传）→ Script_Agent 生成基础标签 → Director_Agent 审核
     - 3B：场景设定（场景描述和场景图/参考图）→ Script_Agent 处理 → Director_Agent 审核
   - 步骤 4：与步骤 2 合并执行（自动前冲后续步骤的基础数据）
   - 步骤 5：参考资料智能分类（Art_Agent 识别分类到角色界面、场景界面、参考界面）→ Director_Agent 审核
   - 步骤 6：项目预览与校验（System_Agent 检查标签一致性）→ Director_Agent 全文审核 → 确认提交
2. WHEN 步骤 2 执行时 THEN THE Project_Wizard SHALL：
   - 不需要用户重复上传剧本文件
   - 系统直接按照步骤处理已上传的剧本和其他基本信息
   - 自动前冲后续步骤的基础数据（角色列表、场次信息等）
3. WHEN 步骤 3A Script_Agent 处理时 THEN THE Project_Wizard SHALL：
   - 生成角色的基础标签（包括所有基础属性）
   - 返回用户确认，列出所有属性供用户选择滑动
4. WHEN 步骤 5 Art_Agent 处理时 THEN THE Project_Wizard SHALL：
   - 可选择生成或隐藏 Art_Agent 功能
   - 只显示上传图片，尽量不使用图像生成式 AI
   - 需要用户确认分类结果
5. WHEN 步骤 6 项目预览时 THEN THE Project_Wizard SHALL：
   - 通过整合展示前端页面的方式预览项目
   - 引入 Director_Agent 进行全文审核
   - 检查标签内容不符（如角色又男又女、又高又瘦等矛盾）
   - 检查剧本和美术冲突的标签
6. THE Project_Wizard SHALL 在每个步骤显示当前 Agent 的状态（工作中/审核中/完成）
7. THE Project_Wizard SHALL 允许用户在步骤间自由跳转
8. THE Project_Wizard SHALL 保存用户在每个步骤的进度
9. WHEN 用户完成所有步骤 THEN THE Project_Wizard SHALL 显示项目预览页面
10. WHEN 用户确认提交 THEN THE Project_Wizard SHALL 创建项目并进入下一阶段

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

### Requirement 11: Market_Agent 市场分析功能

**User Story:** As a 制片人, I want to 获得专业的市场分析和建议, so that 我可以了解项目的市场前景和定位。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 集成 Market_Agent 市场分析功能
2. THE Market_Agent SHALL 提供独立的分析界面和展示功能
3. WHEN 项目基本信息完成 THEN THE Market_Agent SHALL 分析：
   - 目标受众分析
   - 市场定位建议
   - 竞品分析
   - 发行渠道建议
4. THE Market_Agent SHALL 基于项目类型、时长、风格提供专业建议
5. THE Project_Wizard SHALL 在独立界面中展示市场分析结果
6. THE Market_Agent 分析结果 SHALL 作为项目档案的一部分保存
7. THE Market_Agent 分析环节 SHALL 使用动态数据，不能是静态数据案例

### Requirement 12: System_Agent 导出前校验

**User Story:** As a 系统, I want to 在导出前进行全面校验, so that 确保项目数据的完整性和一致性。

#### Acceptance Criteria

1. THE System_Agent SHALL 在项目导出前执行全面校验
2. THE System_Agent SHALL 检查以下内容：
   - 所有标签是否一致（避免矛盾标签）
   - 预搜索当前标签与视频素材 TAG 的匹配百分比
   - 前后接口的 API 是否正常
   - 展示页面是否有 bug 或报错
3. WHEN System_Agent 校验未通过 THEN THE Project_Wizard SHALL：
   - 阻止导出操作
   - 显示具体的问题列表
   - 提供修复建议
4. WHEN System_Agent 校验通过 THEN THE Project_Wizard SHALL 允许导出
5. THE 美术图导出 SHALL 保持原图质量
6. THE 视频渲染质量 SHALL 提供可选设置

### Requirement 13: 素材召回机制

**User Story:** As a 用户, I want to 系统能从我上传的参考素材中智能匹配内容, so that 我可以重复利用已有的参考资料。

#### Acceptance Criteria

1. THE Project_Wizard SHALL 从用户上传的参考素材中匹配内容
2. WHEN 无匹配素材时 THEN THE Project_Wizard SHALL 显示占位符
3. THE Project_Wizard SHALL 不依赖外部素材库或网络资源
4. THE 素材召回 SHALL 基于 Art_Agent 生成的标签进行匹配
5. THE Project_Wizard SHALL 允许用户手动替换召回的素材

### Requirement 14: 数据标注规范

**User Story:** As a 开发者, I want to 明确区分静态数据案例和动态数据, so that 系统在不同阶段使用正确的数据类型。

#### Acceptance Criteria

1. THE 前期立项环节 MAY 使用静态数据案例（模板、示例）
2. THE 后期分析环节 SHALL 使用动态数据，不能是静态数据案例
3. THE Market_Agent 分析 SHALL 基于实际项目数据进行动态分析
4. THE System_Agent 校验 SHALL 基于实际项目数据进行检查
5. THE Project_Wizard SHALL 在界面中明确标注哪些是静态案例，哪些是动态数据

### Requirement 15: Storyboard_Agent 素材召回与候选管理

**User Story:** As a 导演, I want to 系统能智能召回匹配的素材并提供多个候选, so that 我可以快速选择合适的素材进行故事板制作。

#### Acceptance Criteria

1. THE Storyboard_Agent SHALL 基于场次描述和标签召回匹配素材
2. WHEN 召回素材时 THEN THE Storyboard_Agent SHALL 返回 Top 5 候选
3. THE Storyboard_Agent SHALL 缓存 5 个候选，支持用户丝滑切换
4. WHEN 用户切换候选 THEN THE Project_Wizard SHALL 立即显示新素材（无需重新搜索）
5. THE Storyboard_Agent SHALL 支持以下召回方式：
   - 标签匹配（Jaccard 相似度）
   - 向量搜索（语义相似度）
   - 混合排序（标签 + 向量）
6. THE Storyboard_Agent SHALL 支持粗剪功能（FFmpeg 切割）
7. WHEN 无匹配素材时 THEN THE Storyboard_Agent SHALL 返回空列表并显示占位符

### Requirement 16: 素材预处理管道

**User Story:** As a 系统, I want to 在素材上传时自动执行预处理, so that 后续的素材召回可以快速进行。

#### Acceptance Criteria

1. WHEN 视频素材上传 THEN THE 预处理管道 SHALL 自动执行以下步骤：
   - 镜头分割（PySceneDetect，确保每片段 ≤10秒）
   - 视频标签生成（Gemini 2.5 Flash API）
   - 向量生成（sentence-transformers）
   - 向量存储（Milvus）
2. THE 预处理管道 SHALL 支持批量处理，避免 API 限流
3. THE 预处理管道 SHALL 显示处理进度和状态
4. IF 预处理失败 THEN THE 系统 SHALL 记录错误并允许重试
5. THE 预处理结果 SHALL 存储到 Milvus 向量数据库
6. THE 预处理管道 SHALL 生成以下标签：
   - scene_type（室内/室外/城市/自然）
   - time（白天/夜晚/黄昏/黎明）
   - shot_type（全景/中景/特写/过肩）
   - mood（紧张/浪漫/悲伤/欢乐/悬疑）
   - action（对话/追逐/打斗/静态）
   - characters（单人/双人/群戏/无人）
   - free_tags（自由标签列表）
   - summary（一句话描述）

### Requirement 17: Milvus 向量存储

**User Story:** As a 系统, I want to 使用 Milvus 存储视频片段向量, so that 可以支持大规模素材的快速检索。

#### Acceptance Criteria

1. THE 系统 SHALL 使用 Milvus Standalone 作为向量存储
2. THE Milvus 集合 SHALL 包含以下字段：
   - video_path（视频路径）
   - segment_index（片段索引）
   - start_time（开始时间）
   - end_time（结束时间）
   - tags_json（标签 JSON）
   - embedding（768维向量）
3. THE Milvus SHALL 使用 IVF_FLAT 索引和 COSINE 相似度
4. THE 系统 SHALL 支持向量搜索和标签搜索两种方式
5. THE Milvus SHALL 通过 Docker 部署，支持自托管

---

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

## 技术选型（成熟开源方案）

### 核心技术栈

| 功能模块 | 技术方案 | 安装方式 | 成熟度 |
|----------|----------|----------|--------|
| **镜头分割** | PySceneDetect | `pip install scenedetect[opencv]` | ⭐⭐⭐⭐⭐ |
| **视频标签** | Gemini 2.5 Flash API | `pip install google-generativeai` | ⭐⭐⭐⭐⭐ |
| **向量存储** | Milvus Standalone | `docker compose up -d` | ⭐⭐⭐⭐⭐ |
| **向量生成** | sentence-transformers | `pip install sentence-transformers` | ⭐⭐⭐⭐⭐ |
| **视频处理** | FFmpeg (已有) | 已集成 | ⭐⭐⭐⭐⭐ |
| **Agent 架构** | BaseAgent (已有) | 已实现 | ⭐⭐⭐⭐ |
| **消息总线** | MessageBus (已有) | 已实现 | ⭐⭐⭐⭐ |
| **标签匹配** | Market_Agent (已有) | 已实现 Jaccard | ⭐⭐⭐⭐ |

### 成本估算

| 项目 | 成本 | 说明 |
|------|------|------|
| Gemini 视频标签 | ~$18-35 / 500GB | 一次性预处理 |
| Milvus | $0 | 自托管 Docker |
| PySceneDetect | $0 | 开源 |
| sentence-transformers | $0 | 本地运行 |
| **新素材增量** | ~$0.05/小时视频 | 持续成本 |

### 开发时间对比

| 方案 | 开发时间 | 说明 |
|------|----------|------|
| 从头开发 | ~38天 | 自研所有模块 |
| 本方案 | ~14天 | 使用成熟开源 |
| **节省** | **63%** | - |