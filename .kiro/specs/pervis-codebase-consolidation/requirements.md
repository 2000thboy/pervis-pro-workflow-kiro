# 代码库整合需求文档

## 介绍

本文档定义了将 `multi-agent-workflow` 代码库整合到 `Pervis PRO` 的需求。目标是消除冗余代码，建立清晰的项目结构，便于后续 IDE 迁移和代码审计。

## 术语表

- **Pervis_PRO**: 主项目目录，包含完整的视频制作系统
- **multi-agent-workflow**: 原始 Agent 框架代码库，核心已整合到 Pervis PRO
- **core 模块**: Agent 框架核心组件（MessageBus、BaseAgent、CommunicationProtocol）
- **属性测试**: 使用 Hypothesis 库的基于属性的测试

## 需求

### 需求 1: 代码迁移验证

**用户故事:** 作为开发者，我希望确认所有必要代码已迁移到 Pervis PRO，以便安全删除冗余目录。

#### 验收标准

1. WHEN 检查 core 模块时 THEN 系统 SHALL 确认 MessageBus、BaseAgent、CommunicationProtocol 已存在于 Pervis PRO/backend/core/
2. WHEN 检查 Agent 实现时 THEN 系统 SHALL 确认所有 Agent 已存在于 Pervis PRO/backend/services/agents/
3. WHEN 检查测试文件时 THEN 系统 SHALL 识别需要迁移的属性测试文件

### 需求 2: 测试文件迁移

**用户故事:** 作为开发者，我希望保留有价值的属性测试，以便维护测试覆盖率。

#### 验收标准

1. WHEN 迁移测试文件时 THEN 系统 SHALL 将属性测试复制到 Pervis PRO/backend/tests/
2. WHEN 测试文件迁移后 THEN 系统 SHALL 更新导入路径以匹配新结构
3. WHEN 测试迁移完成时 THEN 系统 SHALL 验证测试可以正常运行

### 需求 3: 架构文档创建

**用户故事:** 作为开发者，我希望有清晰的架构文档，以便理解 Agent 框架的设计和使用方式。

#### 验收标准

1. WHEN 创建架构文档时 THEN 系统 SHALL 在 Pervis PRO/docs/ 创建 MULTI_AGENT_ARCHITECTURE.md
2. WHEN 文档创建后 THEN 文档 SHALL 包含系统架构图、组件说明、使用指南
3. WHEN 文档创建后 THEN 文档 SHALL 包含 Agent 协作流程的 Mermaid 图示

### 需求 4: 冗余目录清理

**用户故事:** 作为开发者，我希望删除冗余的 multi-agent-workflow 目录，以便保持代码库整洁。

#### 验收标准

1. WHEN 删除目录前 THEN 系统 SHALL 确认所有必要内容已迁移
2. WHEN 删除目录时 THEN 系统 SHALL 删除 multi-agent-workflow/ 整个目录
3. WHEN 删除完成后 THEN 系统 SHALL 更新 .kiro/steering/global-rules.md 移除对该目录的引用

### 需求 5: Spec 文档更新

**用户故事:** 作为开发者，我希望更新相关 Spec 文档，以便反映整合后的状态。

#### 验收标准

1. WHEN 更新 Spec 时 THEN 系统 SHALL 在 multi-agent-workflow-core spec 中标记为已整合
2. WHEN 更新完成后 THEN Spec 文档 SHALL 指向 Pervis PRO 中的实际代码位置
