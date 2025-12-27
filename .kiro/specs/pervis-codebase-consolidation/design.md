# 代码库整合设计文档

## 概述

本设计文档描述了将 `multi-agent-workflow` 代码库整合到 `Pervis PRO` 的技术方案。整合后，项目将只有一个主目录，结构清晰，便于代码审计和 IDE 迁移。

## 架构

### 整合前结构

```
workspace/
├── Pervis PRO/                    # 主项目
│   └── backend/
│       ├── core/                  # 已整合的 Agent 框架核心
│       └── services/agents/       # 已整合的 Agent 实现
├── multi-agent-workflow/          # 冗余目录 ❌
│   └── backend/
│       ├── app/agents/            # 重复的 Agent 代码
│       └── tests/                 # 有价值的属性测试
└── .kiro/specs/
    └── multi-agent-workflow-core/ # Spec 文档
```

### 整合后结构

```
workspace/
├── Pervis PRO/                    # 唯一主项目 ✅
│   ├── backend/
│   │   ├── core/                  # Agent 框架核心
│   │   ├── services/agents/       # Agent 实现
│   │   └── tests/                 # 包含迁移的属性测试
│   └── docs/
│       └── MULTI_AGENT_ARCHITECTURE.md  # 架构说明
└── .kiro/specs/
    ├── multi-agent-workflow-core/ # 保留作为设计参考
    └── pervis-codebase-consolidation/  # 整合记录
```

## 组件和接口

### 已整合的核心组件

| 组件 | 原位置 | 新位置 | 状态 |
|------|--------|--------|------|
| MessageBus | multi-agent-workflow/backend/app/core/ | Pervis PRO/backend/core/message_bus.py | ✅ 已整合 |
| BaseAgent | multi-agent-workflow/backend/app/core/ | Pervis PRO/backend/core/base_agent.py | ✅ 已整合 |
| CommunicationProtocol | multi-agent-workflow/backend/app/core/ | Pervis PRO/backend/core/communication_protocol.py | ✅ 已整合 |
| AgentTypes | multi-agent-workflow/backend/app/core/ | Pervis PRO/backend/core/agent_types.py | ✅ 已整合 |

### 已整合的 Agent 实现

| Agent | 原位置 | 新位置 | 状态 |
|-------|--------|--------|------|
| ScriptAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/script_agent.py | ✅ 已整合 |
| ArtAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/art_agent.py | ✅ 已整合 |
| DirectorAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/director_agent.py | ✅ 已整合 |
| MarketAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/market_agent.py | ✅ 已整合 |
| PMAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/pm_agent.py | ✅ 已整合 |
| StoryboardAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/storyboard_agent.py | ✅ 已整合 |
| SystemAgent | multi-agent-workflow/backend/app/agents/ | Pervis PRO/backend/services/agents/system_agent.py | ✅ 已整合 |

### 需要迁移的测试文件

以下属性测试文件需要迁移到 Pervis PRO：

| 测试文件 | 测试内容 | 优先级 |
|----------|----------|--------|
| test_message_bus_properties.py | 消息总线属性测试 | P0 |
| test_agent_initialization_properties.py | Agent 初始化属性测试 | P0 |
| test_director_agent_properties.py | 导演 Agent 属性测试 | P1 |
| test_system_agent_properties.py | 系统 Agent 属性测试 | P1 |

## 数据模型

无新增数据模型，整合工作不涉及数据结构变更。

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真。*

### 属性 1: 代码完整性
*对于任何* Pervis PRO 中的 Agent 功能调用，都应该能够正常执行，不依赖 multi-agent-workflow 目录
**验证需求: Requirements 1.1, 1.2**

### 属性 2: 测试可运行性
*对于任何* 迁移后的测试文件，都应该能够在 Pervis PRO/backend 目录下正常运行
**验证需求: Requirements 2.3**

### 属性 3: 导入路径正确性
*对于任何* 迁移后的测试文件中的导入语句，都应该正确指向 Pervis PRO 中的模块
**验证需求: Requirements 2.2**

## 错误处理

### 迁移风险

1. **导入路径错误**: 迁移测试文件后需要更新所有导入路径
2. **依赖缺失**: 确保 Pervis PRO 包含所有必要的依赖
3. **配置差异**: 检查环境变量和配置文件的差异

### 回滚策略

1. 在删除前备份 multi-agent-workflow 目录
2. 使用 Git 版本控制，可随时回滚
3. 分步执行，每步验证后再继续

## 测试策略

### 验证步骤

1. **迁移前验证**: 确认 Pervis PRO 中的 Agent 功能正常
2. **测试迁移验证**: 运行迁移后的测试，确保全部通过
3. **删除后验证**: 删除 multi-agent-workflow 后，再次运行所有测试

### 测试命令

```bash
# 从 Pervis PRO/backend 目录执行
py -m pytest tests/ -v --tb=short
```
