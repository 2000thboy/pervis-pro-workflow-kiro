# Multi-Agent Workflow 系统 MVP 启动指南

## 系统概述

Multi-Agent Workflow 是一个多Agent协作工作流系统，专为影视/视频制作设计。系统包含8个专业Agent，支持项目立项、故事板创建、预演剪辑等完整工作流。

## 测试状态

✅ **442个测试全部通过** (2024-12-24)

- 消息总线和通信协议测试
- 8个Agent单元测试和属性测试
- 4个工作流测试
- LLM服务、向量存储、持久化服务测试
- 错误处理和监控测试
- 端到端集成测试

## 快速启动 (推荐)

### 方式1: 一键启动 (Windows)

双击运行 `start_mvp.bat` 即可启动MVP演示服务。

### 方式2: 命令行启动

```bash
# 进入后端目录
cd multi-agent-workflow/backend

# 安装依赖 (首次运行)
pip install -r requirements.txt

# 启动MVP服务 (不需要Redis/PostgreSQL)
py start_mvp.py
```

服务启动后访问:
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **Agent列表**: http://localhost:8000/api/agents
- **工作流列表**: http://localhost:8000/api/workflows
- **系统统计**: http://localhost:8000/api/statistics

### 方式3: 完整服务启动 (需要Redis)

```bash
cd multi-agent-workflow/backend
py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 运行测试验证

```bash
# 运行所有测试
cd multi-agent-workflow/backend
py -m pytest tests/ -v

# 只运行集成测试
py -m pytest tests/test_integration.py -v

# 运行MVP验证测试
py -m pytest tests/test_integration.py::TestMVPValidation -v
```

## 核心组件

### Agent系统 (8个Agent)

| Agent | 职责 |
|-------|------|
| DirectorAgent | 总调度，冲突解决 |
| SystemAgent | 用户交互，状态查询 |
| DAMAgent | 数字资产管理 |
| PMAgent | 项目管理 |
| ScriptAgent | 剧本分析 |
| ArtAgent | 美术设计 |
| MarketAgent | 市场分析 |
| BackendAgent | 系统监控 |

### 工作流

1. **立项工作流** (ProjectSetupWorkflow) - 项目创建和信息补全
2. **Beatboard工作流** (BeatboardWorkflow) - 故事板和场次分析
3. **预演剪辑工作流** (PreviewEditWorkflow) - 预演生成和同步
4. **打包审阅工作流** (PackageReviewWorkflow) - 文件打包和质量审阅

### 核心服务

- **MessageBus** - Agent间通信
- **LLMService** - AI大模型集成 (支持Ollama/OpenAI/Gemini)
- **VectorService** - 向量搜索 (ChromaDB)
- **PersistenceService** - 数据持久化
- **ErrorHandler** - 错误处理
- **SystemMonitor** - 系统监控

## API端点

### 项目管理
- `POST /api/projects` - 创建项目
- `GET /api/projects` - 列出项目
- `GET /api/projects/{id}` - 获取项目详情

### 工作流
- `POST /api/workflows/start` - 启动工作流
- `GET /api/workflows/{id}/status` - 获取工作流状态

### 系统
- `GET /health` - 健康检查
- `GET /api/agents/status` - Agent状态

## 配置

### LLM配置 (支持本地Ollama)

```python
from app.core.llm_service import LLMService, LLMConfig, LLMProvider

# 使用Ollama本地模型
config = LLMConfig(
    provider=LLMProvider.OLLAMA,
    model="llama2",
    base_url="http://localhost:11434"
)
llm = LLMService(config)
```

### 向量存储配置

```python
from app.core.vector_store import VectorService, VectorStoreConfig

# 使用ChromaDB
config = VectorStoreConfig.chroma(
    persist_directory="./data/chroma"
)
vector = VectorService(config)
```

## 目录结构

```
multi-agent-workflow/
├── backend/
│   ├── app/
│   │   ├── agents/      # 8个Agent实现
│   │   ├── core/        # 核心组件
│   │   └── workflows/   # 工作流实现
│   ├── tests/           # 测试文件 (442个测试)
│   └── main.py          # FastAPI入口
├── frontend/            # React前端 (待完善)
└── launcher/            # 桌面启动器 (待完善)
```

## 下一步开发

- [ ] 完善Web前端界面
- [ ] 优化桌面启动器
- [ ] 性能优化和调优
- [ ] 生产环境部署配置

## 常见问题

### Q: 如何切换LLM提供商?
修改 `LLMConfig` 的 `provider` 参数，支持 `OLLAMA`, `OPENAI`, `GEMINI`, `MOCK`

### Q: 测试失败怎么办?
确保已安装所有依赖: `pip install -r requirements.txt`

### Q: 如何查看API文档?
启动服务后访问 http://localhost:8000/docs
