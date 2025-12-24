# Pervis PRO 项目重启指南

## 项目重新定义

基于最新需求分析，Pervis PRO 将重构为**多Agent协作的智能视频制作系统**，实现从立项到交付的全流程自动化。

## 新项目结构

```
Pervis PRO/
├── .kiro/
│   └── specs/                          # 功能规格文档
│       ├── multi-agent-workflow-core/  # 核心工作流SPEC
│       ├── director-agent/             # 导演Agent SPEC
│       ├── dam-agent/                  # DAM系统Agent SPEC
│       ├── script-agent/               # 编剧Agent SPEC
│       ├── art-agent/                  # 美术Agent SPEC
│       ├── market-agent/               # 市场Agent SPEC
│       ├── system-agent/               # 系统Agent SPEC
│       ├── pm-agent/                   # 项目管理Agent SPEC
│       └── backend-agent/              # 后端监控Agent SPEC
├── core/                               # 核心系统
│   ├── agents/                         # Agent实现
│   │   ├── director/                   # 导演Agent
│   │   ├── dam/                        # DAM Agent
│   │   ├── script/                     # 编剧Agent
│   │   ├── art/                        # 美术Agent
│   │   ├── market/                     # 市场Agent
│   │   ├── system/                     # 系统Agent
│   │   ├── pm/                         # 项目管理Agent
│   │   └── backend/                    # 后端Agent
│   ├── workflow/                       # 工作流引擎
│   │   ├── project_setup/              # 立项工作流
│   │   ├── beatboard/                  # 故事板工作流
│   │   └── preview_edit/               # 预演剪辑工作流
│   ├── communication/                  # Agent间通信
│   └── state_management/               # 状态管理
├── frontend/                           # 前端界面
│   ├── components/                     # UI组件
│   │   ├── agent_panels/               # Agent交互面板
│   │   ├── workflow_views/             # 工作流视图
│   │   └── project_management/         # 项目管理界面
│   └── services/                       # 前端服务
├── backend/                            # 后端API
│   ├── api/                            # API接口
│   ├── models/                         # 数据模型
│   └── services/                       # 业务服务
├── storage/                            # 数据存储
│   ├── projects/                       # 项目文件
│   ├── assets/                         # 素材库
│   └── templates/                      # 模板库
└── tests/                              # 测试文件
    ├── unit/                           # 单元测试
    ├── integration/                    # 集成测试
    └── e2e/                            # 端到端测试
```

## 核心工作流定义

### 1. 立项阶段 (Project Setup)
```
上传/输入 → LLM补全 → 人工审核 → 建档成功 → Agent调配
```

**涉及Agent:**
- 系统Agent: 接收输入，LLM协助
- PM Agent: 项目建档和文件整理
- 导演Agent: 总体协调和决策
- 编剧Agent: 剧本分析和人物设定
- 美术Agent: 视觉设计协助
- 市场Agent: 竞品分析和参考
- 后端Agent: API接口监控

### 2. Beatboard阶段 (Storyboard Assembly)
```
场次分析 → 时长评估 → 向量搜索 → 素材匹配 → 故事板装配
```

**涉及Agent:**
- 故事板Agent: 场次分析和故事板生成
- 编剧Agent: 时长评估协助
- 导演Agent: 确认和决策
- DAM Agent: 素材标签匹配
- 系统Agent: 向量搜索和格式验证

### 3. 预演剪辑阶段 (Preview & Edit)
```
预演生成 → 多端同步 → 资产检查 → 文件打包 → 最终审阅
```

**涉及Agent:**
- 全局Agent: 多端同步协调
- 分析Agent: 资产情况检查
- 装配Agent: 文件打包处理
- 审阅Agent: 最终质量控制

## 技术架构要点

### Agent通信机制
- **消息总线**: 统一的Agent间通信协议
- **状态同步**: 实时的Agent状态管理
- **冲突解决**: 导演Agent作为最终决策者

### 数据流管理
- **项目数据**: 统一的项目信息模型
- **素材管理**: DAM系统的标签化管理
- **版本控制**: 完整的项目版本追踪

### AI集成策略
- **LLM辅助**: 所有文字内容的AI生成支持
- **向量搜索**: 智能的素材匹配算法
- **质量验证**: AI辅助的内容质量检查

## 开发优先级

### Phase 1: 核心架构 (高优先级)
1. Agent通信框架
2. 工作流引擎
3. 状态管理系统
4. 基础UI框架

### Phase 2: 核心Agent (高优先级)
1. 导演Agent (总控)
2. 系统Agent (基础交互)
3. DAM Agent (素材管理)
4. PM Agent (项目管理)

### Phase 3: 专业Agent (中优先级)
1. 编剧Agent
2. 美术Agent
3. 市场Agent
4. 后端Agent

### Phase 4: 高级功能 (低优先级)
1. 多端同步
2. 高级AI功能
3. 性能优化
4. 用户体验优化

## 启动检查清单

- [x] 确认Python环境正常 (已修复)
- [x] 检查依赖包安装状态 (已安装)
- [ ] 验证数据库连接
- [ ] 测试基础API接口
- [ ] 确认前端构建环境
- [ ] 验证AI服务连接

## 下一步行动

1. **立即**: ✅ 已修复启动器Python环境问题
2. **本周**: ✅ 已完成核心工作流SPEC文档
3. **下周**: 开始Agent架构设计和实现
4. **本月**: 完成MVP版本的核心功能

## 快速启动

### 启动现有启动器
```bash
# 方法1: 使用批处理文件
Pervis PRO/start_launcher.bat

# 方法2: 直接运行Python
cd "Pervis PRO"
py launcher/main.py
```

### 开始开发新架构
1. 查看SPEC文档: `.kiro/specs/multi-agent-workflow-core/`
2. 开始第一个任务: "建立项目基础架构"
3. 按照tasks.md中的任务列表逐步实现

---

*本指南将随着项目进展持续更新*