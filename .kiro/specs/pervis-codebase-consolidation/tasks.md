# 代码库整合实现计划

## 概述

本实现计划将 multi-agent-workflow 代码库整合到 Pervis PRO，消除冗余代码，建立清晰的项目结构。

## 任务列表

- [x] 1. 验证代码迁移完整性
  - [x] 1.1 检查 core 模块完整性
    - 确认 MessageBus、BaseAgent、CommunicationProtocol、AgentTypes 存在
    - 验证模块可以正常导入
    - _需求: 1.1_

  - [x] 1.2 检查 Agent 实现完整性
    - 确认所有 7 个 Agent 存在于 Pervis PRO/backend/services/agents/
    - 验证 Agent 可以正常实例化
    - _需求: 1.2_

- [x] 2. 迁移有价值的测试文件
  - [x] 2.1 迁移消息总线属性测试
    - 复制 test_message_bus_properties.py 到 Pervis PRO/backend/tests/
    - 更新导入路径
    - _需求: 2.1, 2.2_

  - [x] 2.2 迁移 Agent 初始化属性测试
    - 复制 test_agent_initialization_properties.py
    - 更新导入路径
    - _需求: 2.1, 2.2_

  - [x] 2.3 运行迁移后的测试验证
    - 执行 `py -m pytest tests/test_message_bus_properties.py -v`
    - 执行 `py -m pytest tests/test_agent_initialization_properties.py -v`
    - 所有测试通过
    - _需求: 2.3_

- [x] 3. 检查点 - 确保测试迁移成功
  - 所有迁移的测试通过

- [x] 4. 创建架构文档
  - [x] 4.1 创建 MULTI_AGENT_ARCHITECTURE.md
    - 在 Pervis PRO/docs/ 创建架构说明文档
    - 包含系统架构图、组件说明、使用指南
    - 包含 Agent 协作流程的 Mermaid 图示
    - _需求: 3.1, 3.2, 3.3_

- [x] 5. 清理冗余目录
  - [x] 5.1 备份确认
    - Git 有未提交更改，建议用户手动提交
    - 所有必要内容已迁移到 Pervis PRO
    - _需求: 4.1_

  - [ ] 5.2 删除 multi-agent-workflow 目录
    - 等待用户确认后删除
    - _需求: 4.2_

  - [x] 5.3 更新 steering 文件
    - 更新 .kiro/steering/global-rules.md 移除对 multi-agent-workflow 的引用
    - _需求: 4.3_

- [x] 6. 更新 Spec 文档
  - [x] 6.1 更新 multi-agent-workflow-core spec
    - 在 requirements.md 顶部添加整合说明
    - 标记为已整合到 Pervis PRO
    - _需求: 5.1, 5.2_

- [ ] 7. 最终检查点
  - 确保所有测试通过
  - 确认项目结构清晰
  - 如有问题请询问用户

## 注意事项

- 每个任务都引用了具体的需求编号以确保可追溯性
- 检查点任务确保增量验证和质量控制
- 标记 `*` 的任务为可选任务
- 删除操作不可逆，务必确认备份
