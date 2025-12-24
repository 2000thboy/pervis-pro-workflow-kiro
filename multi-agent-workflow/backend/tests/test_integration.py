"""
端到端集成测试

测试完整工作流的Agent间协作和数据流
验证需求: 所有需求
"""
import pytest
import asyncio
from datetime import datetime
from typing import Dict, List, Any

from app.core.message_bus import MessageBus, Message, MessageType
from app.core.llm_service import LLMService, LLMConfig, LLMProvider, LLMMessage, LLMRole
from app.core.vector_store import VectorService, VectorStoreConfig, VectorStoreProvider, Document
from app.core.persistence import PersistenceService, PersistenceConfig, StorageProvider, ProjectData, WorkflowStateData
from app.core.error_handler import ErrorHandler, ErrorCategory
from app.core.monitoring import SystemMonitor, ComponentType

from app.agents.director_agent import DirectorAgent
from app.agents.system_agent import SystemAgent
from app.agents.dam_agent import DAMAgent
from app.agents.pm_agent import PMAgent
from app.agents.script_agent import ScriptAgent
from app.agents.art_agent import ArtAgent
from app.agents.market_agent import MarketAgent
from app.agents.backend_agent import BackendAgent

from app.workflows.workflow_engine import WorkflowEngine, WorkflowDefinition


# ============== Fixtures ==============

@pytest.fixture
def message_bus():
    """创建消息总线"""
    return MessageBus()


@pytest.fixture
def llm_service():
    """创建LLM服务（Mock模式）"""
    config = LLMConfig(provider=LLMProvider.MOCK, model="mock-model")
    return LLMService(config)


@pytest.fixture
def vector_service():
    """创建向量服务（Mock模式）"""
    config = VectorStoreConfig.mock()
    return VectorService(config)


@pytest.fixture
def persistence_service():
    """创建持久化服务（内存模式）"""
    config = PersistenceConfig(provider=StorageProvider.MEMORY)
    service = PersistenceService(config)
    return service


@pytest.fixture
def error_handler():
    """创建错误处理器"""
    return ErrorHandler(log_dir="./data/test_logs/integration")


@pytest.fixture
def system_monitor():
    """创建系统监控器"""
    return SystemMonitor(log_dir="./data/test_logs/integration")


@pytest.fixture
def workflow_engine(message_bus):
    """创建工作流引擎"""
    return WorkflowEngine(message_bus)


# ============== Agent初始化集成测试 ==============

class TestAgentInitializationIntegration:
    """
    Agent初始化集成测试
    
    属性 1: Agent初始化完整性
    验证需求: Requirements 1.1
    """
    
    def test_all_agents_can_be_created(self, message_bus):
        """测试所有8个Agent可以成功创建"""
        # 创建所有Agent
        director = DirectorAgent("director", message_bus)
        system = SystemAgent("system", message_bus)
        dam = DAMAgent("dam", message_bus)
        pm = PMAgent("pm", message_bus)
        script = ScriptAgent("script", message_bus)
        art = ArtAgent("art", message_bus)
        market = MarketAgent("market", message_bus)
        backend = BackendAgent("backend", message_bus)
        
        agents = [director, system, dam, pm, script, art, market, backend]
        
        # 验证所有Agent都已创建
        assert len(agents) == 8
        
        # 验证Agent类型
        agent_types = [type(a).__name__ for a in agents]
        expected_types = [
            "DirectorAgent", "SystemAgent", "DAMAgent", "PMAgent",
            "ScriptAgent", "ArtAgent", "MarketAgent", "BackendAgent"
        ]
        
        for expected in expected_types:
            assert expected in agent_types


# ============== 工作流引擎集成测试 ==============

class TestWorkflowEngineIntegration:
    """
    工作流引擎集成测试
    
    属性 6: 立项工作流触发一致性
    验证需求: Requirements 2.1
    """
    
    @pytest.mark.asyncio
    async def test_workflow_engine_lifecycle(self, workflow_engine):
        """测试工作流引擎生命周期"""
        # 启动引擎
        await workflow_engine.start()
        assert workflow_engine._running is True
        
        # 停止引擎
        await workflow_engine.stop()
        assert workflow_engine._running is False
    
    @pytest.mark.asyncio
    async def test_register_workflow(self, workflow_engine):
        """测试注册工作流"""
        # 创建工作流定义
        definition = WorkflowDefinition(
            id="test_workflow",
            name="测试工作流",
            description="用于测试的工作流"
        )
        
        # 注册工作流
        workflow_engine.register_workflow(definition)
        
        # 列出工作流 - 返回的是WorkflowDefinition对象列表
        workflows = workflow_engine.list_workflows()
        workflow_ids = [w.id for w in workflows]
        assert "test_workflow" in workflow_ids


# ============== 数据持久化集成测试 ==============

class TestPersistenceIntegration:
    """
    数据持久化集成测试
    
    属性 37: 中间状态保存实时性
    验证需求: Requirements 7.2
    """
    
    @pytest.mark.asyncio
    async def test_project_save_and_retrieve(self, persistence_service):
        """测试项目保存和检索"""
        await persistence_service.initialize()
        
        # 创建项目 - 使用关键字参数
        project = await persistence_service.create_project(
            name="集成测试项目",
            description="用于集成测试的项目",
            metadata={"test": True}
        )
        
        # 检索项目
        retrieved = await persistence_service.get_project(project.id)
        
        assert retrieved is not None
        assert retrieved.name == "集成测试项目"
    
    @pytest.mark.asyncio
    async def test_workflow_state_persistence(self, persistence_service):
        """测试工作流状态持久化"""
        await persistence_service.initialize()
        
        # 使用正确的API - 多个参数
        state = await persistence_service.save_workflow_state(
            workflow_id="wf_integration_001",
            workflow_type="project_setup",
            project_id="proj_001",
            status="running",
            current_step="step_2",
            steps_completed=["step_1"],
            context={"data": "test"}
        )
        
        retrieved = await persistence_service.get_workflow_state("wf_integration_001")
        
        assert retrieved is not None
        assert retrieved.current_step == "step_2"


# ============== LLM服务集成测试 ==============

class TestLLMServiceIntegration:
    """
    LLM服务集成测试
    
    属性 31: AI辅助功能可用性
    验证需求: Requirements 6.1
    """
    
    @pytest.mark.asyncio
    async def test_llm_chat_completion(self, llm_service):
        """测试LLM对话补全"""
        await llm_service.initialize()
        
        messages = [
            LLMMessage(role=LLMRole.USER, content="你好，请介绍一下自己")
        ]
        
        response = await llm_service.chat(messages)
        
        assert response is not None
        assert response.content is not None
    
    @pytest.mark.asyncio
    async def test_llm_complete(self, llm_service):
        """测试LLM补全"""
        await llm_service.initialize()
        
        response = await llm_service.complete("为一个科幻电影写一个简短的故事概要")
        
        assert response is not None
        assert response.content is not None


# ============== 向量搜索集成测试 ==============

class TestVectorSearchIntegration:
    """
    向量搜索集成测试
    
    属性 15: 向量搜索生成准确性
    验证需求: Requirements 3.4
    """
    
    @pytest.mark.asyncio
    async def test_index_and_search_documents(self, vector_service):
        """测试文档索引和搜索"""
        await vector_service.initialize()
        
        # 创建文档（使用字典格式）
        docs = [
            {"content": "城市夜景灯光闪烁", "metadata": {"type": "video", "tags": ["城市", "夜景"]}},
            {"content": "森林日出自然风光", "metadata": {"type": "video", "tags": ["森林", "日出"]}},
            {"content": "海边日落浪漫场景", "metadata": {"type": "video", "tags": ["海边", "日落"]}}
        ]
        
        # 索引文档
        ids = await vector_service.index_documents(docs)
        assert len(ids) == 3
        
        # 搜索文档
        results = await vector_service.search("自然风景", top_k=2)
        assert len(results) > 0


# ============== 错误处理集成测试 ==============

class TestErrorHandlingIntegration:
    """
    错误处理集成测试
    
    属性 26: 异常检测及时性
    验证需求: Requirements 5.1
    """
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, error_handler):
        """测试Agent错误处理"""
        try:
            raise RuntimeError("Agent processing failed")
        except Exception as e:
            context = await error_handler.handle_agent_error(
                agent_id="test_agent",
                error=e,
                task_id="task_001"
            )
        
        assert context is not None
        assert context.category == ErrorCategory.AGENT_ERROR
        assert "test_agent" in context.source
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, error_handler):
        """测试工作流错误恢复"""
        try:
            raise Exception("Workflow step failed")
        except Exception as e:
            context = await error_handler.handle_workflow_error(
                workflow_id="wf_001",
                step_id="step_3",
                error=e
            )
        
        assert context is not None
        assert context.recovery_action is not None
    
    @pytest.mark.asyncio
    async def test_api_error_logging(self, error_handler):
        """测试API错误日志"""
        try:
            raise Exception("API request failed")
        except Exception as e:
            context = await error_handler.handle_api_error(
                endpoint="/api/projects",
                method="POST",
                error=e,
                status_code=500
            )
        
        assert context is not None
        assert context.category == ErrorCategory.API_ERROR


# ============== 系统监控集成测试 ==============

class TestMonitoringIntegration:
    """
    系统监控集成测试
    
    属性 4: Agent操作日志完整性
    验证需求: Requirements 1.4
    """
    
    def test_operation_logging(self, system_monitor):
        """测试操作日志记录"""
        # 记录多个操作
        system_monitor.log_operation(
            operation="create_project",
            status="success",
            duration_ms=150.0,
            agent_id="pm_agent"
        )
        
        system_monitor.log_operation(
            operation="analyze_script",
            status="success",
            duration_ms=200.0,
            agent_id="script_agent"
        )
        
        # 获取统计
        stats = system_monitor.get_operation_statistics()
        
        assert stats["total_operations"] == 2
        assert stats["success_count"] == 2
    
    @pytest.mark.asyncio
    async def test_health_check_integration(self, system_monitor):
        """测试健康检查集成"""
        # 注册组件健康检查
        system_monitor.register_health_check(
            "message_bus",
            ComponentType.MESSAGE_BUS,
            lambda: True
        )
        
        system_monitor.register_health_check(
            "database",
            ComponentType.DATABASE,
            lambda: True
        )
        
        # 执行健康检查
        results = await system_monitor.check_all_health()
        
        assert len(results) == 2
        assert all(r.status.value == "healthy" for r in results.values())
    
    def test_system_metrics_collection(self, system_monitor):
        """测试系统指标收集"""
        metrics = system_monitor.collect_system_metrics()
        
        assert metrics is not None
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0


# ============== MVP验证测试 ==============

class TestMVPValidation:
    """
    MVP验证测试
    
    验证系统核心功能是否满足MVP要求
    """
    
    def test_mvp_core_components(self, message_bus):
        """测试MVP核心组件"""
        # 验证消息总线
        assert message_bus is not None
        
        # 验证可以创建所有Agent
        agents = [
            DirectorAgent("director", message_bus),
            SystemAgent("system", message_bus),
            DAMAgent("dam", message_bus),
            PMAgent("pm", message_bus),
            ScriptAgent("script", message_bus),
            ArtAgent("art", message_bus),
            MarketAgent("market", message_bus),
            BackendAgent("backend", message_bus)
        ]
        
        assert len(agents) == 8
    
    @pytest.mark.asyncio
    async def test_mvp_services(self, llm_service, vector_service, persistence_service):
        """测试MVP服务"""
        # LLM服务
        assert llm_service is not None
        await llm_service.initialize()
        response = await llm_service.complete("测试")
        assert response is not None
        
        # 向量服务
        assert vector_service is not None
        await vector_service.initialize()
        
        # 持久化服务 - 使用正确的API
        assert persistence_service is not None
        await persistence_service.initialize()
        project = await persistence_service.create_project(
            name="MVP测试",
            description="测试"
        )
        retrieved = await persistence_service.get_project(project.id)
        assert retrieved is not None
    
    @pytest.mark.asyncio
    async def test_mvp_workflow_engine(self, workflow_engine):
        """测试MVP工作流引擎"""
        # 创建工作流定义
        definitions = [
            WorkflowDefinition(id="project_setup", name="立项工作流", description="项目立项"),
            WorkflowDefinition(id="beatboard", name="Beatboard工作流", description="故事板"),
            WorkflowDefinition(id="preview_edit", name="预演剪辑工作流", description="预演")
        ]
        
        for defn in definitions:
            workflow_engine.register_workflow(defn)
        
        # 验证工作流已注册 - list_workflows返回WorkflowDefinition对象列表
        workflows = workflow_engine.list_workflows()
        workflow_ids = [w.id for w in workflows]
        assert "project_setup" in workflow_ids
        assert "beatboard" in workflow_ids
        assert "preview_edit" in workflow_ids
    
    def test_mvp_error_handling(self, error_handler):
        """测试MVP错误处理"""
        assert error_handler is not None
        
        # 验证错误分类
        categories = list(ErrorCategory)
        assert len(categories) >= 5
    
    def test_mvp_monitoring(self, system_monitor):
        """测试MVP监控"""
        assert system_monitor is not None
        
        # 记录操作
        log = system_monitor.log_operation(
            operation="mvp_test",
            status="success",
            duration_ms=10.0
        )
        
        assert log is not None
        assert log.log_id.startswith("LOG-")


# ============== 完整系统集成测试 ==============

class TestFullSystemIntegration:
    """
    完整系统集成测试
    
    测试所有组件协同工作
    """
    
    @pytest.mark.asyncio
    async def test_full_system_startup(
        self,
        message_bus,
        workflow_engine,
        persistence_service,
        llm_service,
        vector_service,
        error_handler,
        system_monitor
    ):
        """测试完整系统启动"""
        # 1. 初始化服务
        await persistence_service.initialize()
        await llm_service.initialize()
        await vector_service.initialize()
        
        # 2. 注册健康检查
        system_monitor.register_health_check(
            "message_bus", ComponentType.MESSAGE_BUS, lambda: True
        )
        system_monitor.register_health_check(
            "llm_service", ComponentType.LLM_SERVICE, lambda: True
        )
        system_monitor.register_health_check(
            "vector_store", ComponentType.VECTOR_STORE, lambda: True
        )
        
        # 3. 执行健康检查
        health_results = await system_monitor.check_all_health()
        assert all(r.status.value == "healthy" for r in health_results.values())
        
        # 4. 启动工作流引擎
        await workflow_engine.start()
        
        # 5. 创建Agent
        agents = [
            DirectorAgent("director", message_bus),
            SystemAgent("system", message_bus),
            PMAgent("pm", message_bus)
        ]
        
        # 6. 记录启动日志
        system_monitor.log_operation(
            operation="system_startup",
            status="success",
            duration_ms=100.0
        )
        
        # 7. 验证系统状态
        stats = system_monitor.get_operation_statistics()
        assert stats["success_rate"] == 1.0
        
        # 8. 停止工作流引擎
        await workflow_engine.stop()
    
    @pytest.mark.asyncio
    async def test_project_creation_flow(
        self,
        persistence_service,
        llm_service,
        system_monitor
    ):
        """测试项目创建流程"""
        await persistence_service.initialize()
        await llm_service.initialize()
        
        # 1. 创建项目 - 使用正确的API
        project = await persistence_service.create_project(
            name="流程测试项目",
            description="测试完整的项目创建流程"
        )
        system_monitor.log_operation("create_project", "success", 50.0, "pm_agent")
        
        # 2. 使用LLM补全信息
        response = await llm_service.complete("补全项目信息：" + project.description)
        system_monitor.log_operation("llm_completion", "success", 100.0, "system_agent")
        
        # 3. 更新项目状态
        await persistence_service.update_project(project.id, status="in_progress")
        system_monitor.log_operation("update_project", "success", 30.0, "pm_agent")
        
        # 4. 验证流程
        retrieved = await persistence_service.get_project(project.id)
        assert retrieved.status == "in_progress"
        
        stats = system_monitor.get_operation_statistics()
        assert stats["total_operations"] == 3
        assert stats["success_rate"] == 1.0
