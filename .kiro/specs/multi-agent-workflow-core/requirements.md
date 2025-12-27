# 多Agent协作工作流核心系统需求文档

> ⚠️ **整合说明**: 本 Spec 的核心代码已整合到 `Pervis PRO/backend/core/` 目录。
> 
> - 消息总线: `Pervis PRO/backend/core/message_bus.py`
> - Agent 基类: `Pervis PRO/backend/core/base_agent.py`
> - 通信协议: `Pervis PRO/backend/core/communication_protocol.py`
> - Agent 类型: `Pervis PRO/backend/core/agent_types.py`
> - Agent 实现: `Pervis PRO/backend/services/agents/`
> - 架构文档: `Pervis PRO/docs/MULTI_AGENT_ARCHITECTURE.md`
>
> 整合日期: 2025-12-27

## 介绍

本文档定义了一个基于多Agent协作的智能视频制作系统的核心工作流需求。该系统通过8个专业Agent的协作，实现从项目立项到最终交付的全流程自动化管理。

## 术语表

- **导演Agent**: 项目总控和决策中心，负责协调所有其他Agent
- **系统Agent**: 提供基础对话和检索功能的Agent
- **DAM_Agent**: 数字资产管理Agent，负责标签管理和素材匹配
- **PM_Agent**: 项目管理Agent，负责项目归档和文件整理
- **编剧Agent**: 负责剧本分析、拆解和角色设定
- **美术Agent**: 负责视觉设计辅助，包括角色设计等
- **市场Agent**: 负责调用LLM和联网MCP进行豆瓣电影标签匹配、向量对比和市场参考数据获取
- **后端Agent**: 负责API监控和系统维护
- **故事板Agent**: 负责故事板生成和场次分析
- **立项阶段**: 从项目上传到建档完成的工作阶段
- **Beatboard阶段**: 故事板生成和素材装配的工作阶段
- **预演剪辑阶段**: 预览生成和多端同步的工作阶段

## 需求

### 需求 1: 多Agent协作架构

**用户故事:** 作为系统架构师，我希望建立一个多Agent协作框架，以便各个专业Agent能够有序协作完成复杂的视频制作任务。

#### 验收标准

1. WHEN 系统启动时 THEN 系统 SHALL 初始化所有8个Agent并建立通信连接
2. WHEN Agent间需要数据交换时 THEN 系统 SHALL 通过统一的消息总线进行通信
3. WHEN 发生Agent冲突时 THEN 导演Agent SHALL 作为最终决策者解决冲突
4. WHEN Agent执行任务时 THEN 系统 SHALL 记录所有Agent的状态和操作日志
5. WHEN 用户查询系统状态时 THEN 系统Agent SHALL 提供实时的Agent状态信息

### 需求 2: 立项工作流管理

**用户故事:** 作为项目管理者，我希望通过自动化的立项流程，快速完成项目信息收集和建档工作。

#### 验收标准

1. WHEN 用户上传项目文件或输入项目信息时 THEN 系统 SHALL 启动立项工作流
2. WHEN 项目信息不完整时 THEN 系统 SHALL 提示LLM协助补全必要信息
3. WHEN 项目信息补全后 THEN 系统 SHALL 生成包含建档信息、画幅宽度、时长、故事概要的项目档案
4. WHEN 项目档案生成后 THEN 系统 SHALL 要求人工审核确认
5. WHEN 人工审核通过后 THEN 导演Agent SHALL 调配所有工作台开始协作
6. WHEN 立项完成时 THEN PM_Agent SHALL 完成项目归档和文件整理

### 需求 3: Beatboard工作流管理

**用户故事:** 作为内容创作者，我希望通过智能化的故事板生成流程，快速完成场景规划和素材装配。

#### 验收标准

1. WHEN 立项完成后 THEN 故事板Agent SHALL 分析立项信息并拆解场次时长
2. WHEN 场次拆解完成后 THEN 编剧Agent SHALL 协助评估时长合理性
3. WHEN 导演Agent确认时长后 THEN 系统 SHALL 等待用户最终确认
4. WHEN 用户确认场次时长后 THEN 系统 SHALL 生成向量搜索词条和相似度匹配索引
5. WHEN 向量搜索完成后 THEN DAM_Agent SHALL 寻找匹配的标签素材
6. WHEN 素材匹配完成后 THEN 系统 SHALL 将素材装配到故事板中
7. WHEN 故事板装配完成后 THEN 系统 SHALL 要求用户确认素材信息

### 需求 4: 预演剪辑工作流管理

**用户故事:** 作为视频编辑者，我希望通过预演功能验证剪辑效果，并支持多端同步分发。

#### 验收标准

1. WHEN Beatboard通过确认后 THEN 系统 SHALL 启动预演剪辑模式
2. WHEN 预演模式启动时 THEN 系统 SHALL 保持beatboard和剪辑台信息一致
3. WHEN 预演成功后 THEN 系统 SHALL 询问是否同步多端
4. WHEN 用户选择同步多端时 THEN 全局Agent SHALL 调用多端同步功能
5. WHEN 多端同步完成后 THEN 分析Agent SHALL 检查所有资产情况
6. WHEN 资产检查通过后 THEN 装配Agent SHALL 进行文件打包处理
7. WHEN 文件打包完成后 THEN 审阅Agent SHALL 审阅所有代码和多媒体素材

### 需求 5: Agent状态监控和错误处理

**用户故事:** 作为系统管理员，我希望能够监控所有Agent的运行状态，并在出现问题时及时处理。

#### 验收标准

1. WHEN 任何Agent出现异常时 THEN 后端Agent SHALL 检测并记录错误信息
2. WHEN 系统检测到API接口问题时 THEN 后端Agent SHALL 生成报错日志
3. WHEN 素材格式不符合规范时 THEN 系统Agent SHALL 强制接管并提示修复
4. WHEN 标签命名不符合规则时 THEN 系统 SHALL 返回错误提示要求修复
5. WHEN 文件路径存在问题时 THEN 系统 SHALL 在系统日志中记录并提示修复

### 需求 6: LLM集成和AI辅助功能

**用户故事:** 作为内容创作者，我希望在所有文字类内容创作中都能获得AI辅助，提高创作效率和质量。

#### 验收标准

1. WHEN 用户进行文字内容创作时 THEN 系统 SHALL 提供LLM AI生成辅助
2. WHEN AI生成内容后 THEN 系统 SHALL 提供辅助验证功能
3. WHEN 用户需要内容建议时 THEN 相关Agent SHALL 调用LLM提供专业建议
4. WHEN 系统需要内容分析时 THEN 对应Agent SHALL 使用AI进行智能分析
5. WHEN AI辅助完成后 THEN 系统 SHALL 记录AI使用情况用于MVP验证

### 需求 7: 数据持久化和项目管理

**用户故事:** 作为项目管理者，我希望所有项目数据都能被妥善保存和管理，支持项目的长期维护。

#### 验收标准

1. WHEN 项目创建时 THEN PM_Agent SHALL 建立完整的项目文件结构
2. WHEN 工作流进行中时 THEN 系统 SHALL 实时保存所有中间状态
3. WHEN Agent产生数据时 THEN 系统 SHALL 按照统一规范存储数据
4. WHEN 项目完成时 THEN PM_Agent SHALL 生成完整的项目归档
5. WHEN 用户查询历史项目时 THEN 系统 SHALL 提供完整的项目检索功能

### 需求 8: 用户界面和交互体验

**用户故事:** 作为最终用户，我希望通过直观的界面与多个Agent进行交互，获得流畅的使用体验。

#### 验收标准

1. WHEN 用户需要与Agent交互时 THEN 系统Agent SHALL 在界面上提供对话框
2. WHEN Agent需要用户确认时 THEN 系统 SHALL 显示清晰的确认界面
3. WHEN 工作流进行中时 THEN 系统 SHALL 显示当前进度和状态
4. WHEN 出现错误时 THEN 系统 SHALL 通过控制面板显示错误信息
5. WHEN 用户需要检索信息时 THEN 系统Agent SHALL 提供智能搜索功能