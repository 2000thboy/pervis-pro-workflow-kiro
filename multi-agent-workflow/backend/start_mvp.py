"""
MVP简化启动脚本

不依赖Redis和PostgreSQL，使用内存存储进行演示
"""
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# 导入核心组件
from app.core.message_bus import MessageBus
from app.core.llm_service import LLMService, LLMConfig, LLMProvider
from app.core.vector_store import VectorService, VectorStoreConfig
from app.core.persistence import PersistenceService, PersistenceConfig, StorageProvider
from app.core.monitoring import SystemMonitor, ComponentType
from app.core.error_handler import ErrorHandler

from app.agents.director_agent import DirectorAgent
from app.agents.system_agent import SystemAgent
from app.agents.dam_agent import DAMAgent
from app.agents.pm_agent import PMAgent
from app.agents.script_agent import ScriptAgent
from app.agents.art_agent import ArtAgent
from app.agents.market_agent import MarketAgent
from app.agents.backend_agent import BackendAgent

from app.workflows.workflow_engine import WorkflowEngine, WorkflowDefinition

# 全局组件
message_bus = None
workflow_engine = None
persistence_service = None
llm_service = None
vector_service = None
system_monitor = None
agents = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global message_bus, workflow_engine, persistence_service
    global llm_service, vector_service, system_monitor, agents
    
    print("=" * 50)
    print("Multi-Agent Workflow MVP 启动中...")
    print("=" * 50)
    
    # 1. 初始化消息总线
    message_bus = MessageBus()
    print("✓ 消息总线初始化完成")
    
    # 2. 初始化持久化服务 (内存模式)
    persistence_service = PersistenceService(
        PersistenceConfig(provider=StorageProvider.MEMORY)
    )
    await persistence_service.initialize()
    print("✓ 持久化服务初始化完成 (内存模式)")
    
    # 3. 初始化LLM服务 (Mock模式)
    llm_service = LLMService(
        LLMConfig(provider=LLMProvider.MOCK, model="mock-model")
    )
    await llm_service.initialize()
    print("✓ LLM服务初始化完成 (Mock模式)")
    
    # 4. 初始化向量服务 (Mock模式)
    vector_service = VectorService(VectorStoreConfig.mock())
    await vector_service.initialize()
    print("✓ 向量服务初始化完成 (Mock模式)")
    
    # 5. 初始化系统监控
    system_monitor = SystemMonitor(log_dir="./data/logs")
    print("✓ 系统监控初始化完成")
    
    # 6. 创建所有Agent
    agents = {
        "director": DirectorAgent("director", message_bus),
        "system": SystemAgent("system", message_bus),
        "dam": DAMAgent("dam", message_bus),
        "pm": PMAgent("pm", message_bus),
        "script": ScriptAgent("script", message_bus),
        "art": ArtAgent("art", message_bus),
        "market": MarketAgent("market", message_bus),
        "backend": BackendAgent("backend", message_bus),
    }
    print(f"✓ {len(agents)}个Agent创建完成")
    
    # 7. 初始化工作流引擎
    workflow_engine = WorkflowEngine(message_bus)
    
    # 注册工作流
    workflows = [
        WorkflowDefinition(id="project_setup", name="立项工作流", description="项目创建和信息补全"),
        WorkflowDefinition(id="beatboard", name="Beatboard工作流", description="故事板和场次分析"),
        WorkflowDefinition(id="preview_edit", name="预演剪辑工作流", description="预演生成和同步"),
        WorkflowDefinition(id="package_review", name="打包审阅工作流", description="文件打包和质量审阅"),
    ]
    for wf in workflows:
        workflow_engine.register_workflow(wf)
    
    await workflow_engine.start()
    print(f"✓ 工作流引擎启动完成 ({len(workflows)}个工作流)")
    
    # 8. 注册健康检查
    system_monitor.register_health_check("message_bus", ComponentType.MESSAGE_BUS, lambda: True)
    system_monitor.register_health_check("llm_service", ComponentType.LLM_SERVICE, lambda: True)
    system_monitor.register_health_check("vector_store", ComponentType.VECTOR_STORE, lambda: True)
    
    # 记录启动日志
    system_monitor.log_operation("system_startup", "success", 0.0)
    
    print("=" * 50)
    print("✓ MVP系统启动完成!")
    print("  API文档: http://localhost:8000/docs")
    print("  健康检查: http://localhost:8000/health")
    print("=" * 50)
    
    yield
    
    # 关闭
    print("正在关闭系统...")
    await workflow_engine.stop()
    print("系统已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Multi-Agent Workflow MVP",
    version="1.0.0",
    description="多Agent协作工作流系统 - MVP演示版",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Multi-Agent Workflow MVP",
        "version": "1.0.0",
        "status": "running",
        "agents": list(agents.keys()) if agents else [],
        "workflows": [w.id for w in workflow_engine.list_workflows()] if workflow_engine else []
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    health_results = {}
    if system_monitor:
        results = await system_monitor.check_all_health()
        health_results = {k: v.status.value for k, v in results.items()}
    
    return {
        "status": "healthy",
        "components": health_results,
        "agents_count": len(agents) if agents else 0
    }


@app.get("/api/agents")
async def list_agents():
    """列出所有Agent"""
    return {
        "agents": [
            {"id": agent_id, "type": type(agent).__name__}
            for agent_id, agent in agents.items()
        ]
    }


@app.get("/api/workflows")
async def list_workflows():
    """列出所有工作流"""
    if not workflow_engine:
        return {"workflows": []}
    
    return {
        "workflows": [
            {"id": w.id, "name": w.name, "description": w.description}
            for w in workflow_engine.list_workflows()
        ]
    }


@app.get("/api/statistics")
async def get_statistics():
    """获取系统统计"""
    stats = {}
    
    if system_monitor:
        stats["operations"] = system_monitor.get_operation_statistics()
        stats["metrics"] = {
            "cpu_percent": system_monitor.collect_system_metrics().cpu_percent,
            "memory_percent": system_monitor.collect_system_metrics().memory_percent
        }
    
    if workflow_engine:
        stats["workflows"] = workflow_engine.get_statistics()
    
    if persistence_service:
        stats["persistence"] = await persistence_service.get_statistics()
    
    return stats


@app.post("/api/projects")
async def create_project(name: str, description: str = ""):
    """创建项目"""
    if not persistence_service:
        return {"error": "服务未初始化"}
    
    project = await persistence_service.create_project(
        name=name,
        description=description
    )
    
    if system_monitor:
        system_monitor.log_operation("create_project", "success", 0.0, "pm_agent")
    
    return {"project": project.to_dict()}


@app.get("/api/projects")
async def list_projects():
    """列出项目"""
    if not persistence_service:
        return {"projects": []}
    
    projects = await persistence_service.list_projects()
    return {"projects": [p.to_dict() for p in projects]}


if __name__ == "__main__":
    import os
    os.makedirs("./data/logs", exist_ok=True)
    
    uvicorn.run(
        "start_mvp:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
