# 多Agent协作工作流核心系统

基于多Agent协作的智能视频制作系统，通过8个专业Agent的协作实现从项目立项到最终交付的全流程自动化管理。

## 项目结构

```
multi-agent-workflow/
├── backend/                 # FastAPI后端服务
│   ├── app/                # 应用核心代码
│   │   ├── agents/         # Agent实现
│   │   ├── core/           # 核心服务
│   │   ├── models/         # 数据模型
│   │   ├── workflows/      # 工作流引擎
│   │   └── api/            # API路由
│   ├── tests/              # 后端测试
│   ├── requirements.txt    # Python依赖
│   └── main.py            # 应用入口
├── frontend/               # React前端界面
│   ├── src/               # 前端源码
│   ├── public/            # 静态资源
│   └── package.json       # 前端依赖
├── launcher/              # CustomTkinter桌面启动器
│   ├── src/               # 启动器源码
│   └── requirements.txt   # 启动器依赖
├── config/                # 配置文件
├── data/                  # 数据存储
└── docs/                  # 文档
```

## 技术栈

- **后端**: FastAPI + Python 3.9+
- **前端**: React + TypeScript
- **桌面启动器**: CustomTkinter
- **数据库**: PostgreSQL + ChromaDB
- **消息总线**: Redis + WebSocket
- **LLM集成**: 支持本地模型、Gemini、OpenAI

## 快速开始

1. 安装依赖
2. 配置数据库
3. 启动后端服务
4. 启动前端界面
5. 运行桌面启动器

详细说明请参考各模块的README文件。