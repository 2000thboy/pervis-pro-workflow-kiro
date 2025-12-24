# -*- coding: utf-8 -*-
"""
Workflow Engine - 工作流引擎核心

实现工作流定义、执行和状态管理
"""
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepType(Enum):
    """步骤类型"""
    TASK = "task"           # 普通任务
    DECISION = "decision"   # 决策节点
    PARALLEL = "parallel"   # 并行执行
    WAIT = "wait"           # 等待用户输入
    AGENT_CALL = "agent_call"  # 调用Agent


@dataclass
class WorkflowStep:
    """工作流步骤定义"""
    id: str
    name: str
    step_type: StepType
    handler: Optional[Callable] = None
    agent_type: Optional[str] = None
    next_steps: List[str] = field(default_factory=list)
    condition: Optional[Callable] = None  # 用于决策节点
    timeout_seconds: int = 300
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "step_type": self.step_type.value,
            "agent_type": self.agent_type,
            "next_steps": self.next_steps,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }


@dataclass
class StepExecution:
    """步骤执行记录"""
    step_id: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
            "retry_attempts": self.retry_attempts,
        }


@dataclass
class WorkflowDefinition:
    """工作流定义"""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: Dict[str, WorkflowStep] = field(default_factory=dict)
    start_step: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: WorkflowStep) -> None:
        """添加步骤"""
        self.steps[step.id] = step
        if self.start_step is None:
            self.start_step = step.id
    
    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """获取步骤"""
        return self.steps.get(step_id)
    
    def get_next_steps(self, step_id: str) -> List[str]:
        """获取下一步骤"""
        step = self.steps.get(step_id)
        return step.next_steps if step else []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "start_step": self.start_step,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowInstance:
    """工作流实例"""
    id: str
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    step_executions: Dict[str, StepExecution] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    def get_step_execution(self, step_id: str) -> Optional[StepExecution]:
        """获取步骤执行记录"""
        return self.step_executions.get(step_id)
    
    def set_step_execution(self, step_id: str, execution: StepExecution) -> None:
        """设置步骤执行记录"""
        self.step_executions[step_id] = execution
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_step": self.current_step,
            "context": self.context,
            "step_executions": {k: v.to_dict() for k, v in self.step_executions.items()},
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, message_bus=None):
        self.message_bus = message_bus
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._instances: Dict[str, WorkflowInstance] = {}
        self._running = False
        self._listeners: List[Callable] = []
        self._agent_handlers: Dict[str, Callable] = {}
    
    async def start(self) -> None:
        """启动引擎"""
        self._running = True
    
    async def stop(self) -> None:
        """停止引擎"""
        self._running = False
    
    @property
    def is_running(self) -> bool:
        return self._running
    
    # 工作流定义管理
    def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """注册工作流定义"""
        self._workflows[workflow.id] = workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self) -> List[WorkflowDefinition]:
        """列出所有工作流"""
        return list(self._workflows.values())
    
    def unregister_workflow(self, workflow_id: str) -> bool:
        """注销工作流定义"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    
    # Agent处理器注册
    def register_agent_handler(self, agent_type: str, handler: Callable) -> None:
        """注册Agent处理器"""
        self._agent_handlers[agent_type] = handler
    
    def get_agent_handler(self, agent_type: str) -> Optional[Callable]:
        """获取Agent处理器"""
        return self._agent_handlers.get(agent_type)
    
    # 工作流实例管理
    async def create_instance(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowInstance]:
        """创建工作流实例"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        instance = WorkflowInstance(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            context=context or {},
        )
        self._instances[instance.id] = instance
        await self._notify_listeners("instance_created", instance)
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """获取工作流实例"""
        return self._instances.get(instance_id)
    
    def list_instances(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None
    ) -> List[WorkflowInstance]:
        """列出工作流实例"""
        instances = list(self._instances.values())
        if workflow_id:
            instances = [i for i in instances if i.workflow_id == workflow_id]
        if status:
            instances = [i for i in instances if i.status == status]
        return instances
    
    # 工作流执行
    async def start_instance(self, instance_id: str) -> bool:
        """启动工作流实例"""
        instance = self.get_instance(instance_id)
        if not instance:
            return False
        
        workflow = self.get_workflow(instance.workflow_id)
        if not workflow or not workflow.start_step:
            return False
        
        instance.status = WorkflowStatus.RUNNING
        instance.started_at = datetime.now()
        instance.current_step = workflow.start_step
        
        await self._notify_listeners("instance_started", instance)
        
        # 开始执行第一个步骤
        await self._execute_step(instance, workflow.start_step)
        return True
    
    async def _execute_step(self, instance: WorkflowInstance, step_id: str) -> None:
        """执行步骤"""
        workflow = self.get_workflow(instance.workflow_id)
        if not workflow:
            return
        
        step = workflow.get_step(step_id)
        if not step:
            return
        
        # 创建执行记录
        execution = StepExecution(
            step_id=step_id,
            status=StepStatus.RUNNING,
            started_at=datetime.now(),
        )
        instance.set_step_execution(step_id, execution)
        instance.current_step = step_id
        
        await self._notify_listeners("step_started", instance, step_id)
        
        try:
            result = None
            
            if step.step_type == StepType.AGENT_CALL and step.agent_type:
                # 调用Agent
                handler = self.get_agent_handler(step.agent_type)
                if handler:
                    result = await handler(instance.context, step.metadata)
            elif step.handler:
                # 执行自定义处理器
                if asyncio.iscoroutinefunction(step.handler):
                    result = await step.handler(instance.context, step.metadata)
                else:
                    result = step.handler(instance.context, step.metadata)
            
            # 更新执行记录
            execution.status = StepStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.result = result
            
            # 更新上下文
            if result and isinstance(result, dict):
                instance.context.update(result)
            
            await self._notify_listeners("step_completed", instance, step_id)
            
            # 执行下一步
            await self._proceed_to_next(instance, step)
            
        except Exception as e:
            execution.status = StepStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error = str(e)
            
            # 检查是否需要重试
            if execution.retry_attempts < step.retry_count:
                execution.retry_attempts += 1
                execution.status = StepStatus.PENDING
                await self._execute_step(instance, step_id)
            else:
                instance.status = WorkflowStatus.FAILED
                instance.error = str(e)
                instance.completed_at = datetime.now()
                await self._notify_listeners("instance_failed", instance)

    
    async def _proceed_to_next(self, instance: WorkflowInstance, step: WorkflowStep) -> None:
        """进入下一步"""
        next_steps = step.next_steps
        
        if not next_steps:
            # 没有下一步，工作流完成
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now()
            instance.current_step = None
            await self._notify_listeners("instance_completed", instance)
            return
        
        if step.step_type == StepType.DECISION and step.condition:
            # 决策节点，根据条件选择下一步
            next_step_id = step.condition(instance.context)
            if next_step_id and next_step_id in next_steps:
                await self._execute_step(instance, next_step_id)
            else:
                # 默认选择第一个
                await self._execute_step(instance, next_steps[0])
        elif step.step_type == StepType.PARALLEL:
            # 并行执行所有下一步
            tasks = [self._execute_step(instance, ns) for ns in next_steps]
            await asyncio.gather(*tasks)
        elif step.step_type == StepType.WAIT:
            # 等待用户输入，暂停工作流
            instance.status = WorkflowStatus.PAUSED
            await self._notify_listeners("instance_paused", instance)
        else:
            # 顺序执行第一个下一步
            await self._execute_step(instance, next_steps[0])
    
    async def resume_instance(
        self,
        instance_id: str,
        user_input: Optional[Dict[str, Any]] = None
    ) -> bool:
        """恢复暂停的工作流"""
        instance = self.get_instance(instance_id)
        if not instance or instance.status != WorkflowStatus.PAUSED:
            return False
        
        workflow = self.get_workflow(instance.workflow_id)
        if not workflow or not instance.current_step:
            return False
        
        # 更新上下文
        if user_input:
            instance.context.update(user_input)
        
        instance.status = WorkflowStatus.RUNNING
        await self._notify_listeners("instance_resumed", instance)
        
        # 获取当前步骤并继续到下一步
        step = workflow.get_step(instance.current_step)
        if step and step.next_steps:
            # 直接执行下一步，跳过当前的WAIT步骤
            await self._execute_step(instance, step.next_steps[0])
        elif step:
            # 没有下一步，工作流完成
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now()
            instance.current_step = None
            await self._notify_listeners("instance_completed", instance)
        
        return True
    
    async def cancel_instance(self, instance_id: str) -> bool:
        """取消工作流实例"""
        instance = self.get_instance(instance_id)
        if not instance:
            return False
        
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED]:
            return False
        
        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.now()
        await self._notify_listeners("instance_cancelled", instance)
        return True
    
    # 事件监听
    def add_listener(self, listener: Callable) -> None:
        """添加事件监听器"""
        self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable) -> None:
        """移除事件监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def _notify_listeners(self, event: str, instance: WorkflowInstance, step_id: Optional[str] = None) -> None:
        """通知监听器"""
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event, instance, step_id)
                else:
                    listener(event, instance, step_id)
            except Exception:
                pass  # 忽略监听器错误
    
    # 统计信息
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        instances = list(self._instances.values())
        return {
            "total_workflows": len(self._workflows),
            "total_instances": len(instances),
            "running_instances": len([i for i in instances if i.status == WorkflowStatus.RUNNING]),
            "completed_instances": len([i for i in instances if i.status == WorkflowStatus.COMPLETED]),
            "failed_instances": len([i for i in instances if i.status == WorkflowStatus.FAILED]),
            "paused_instances": len([i for i in instances if i.status == WorkflowStatus.PAUSED]),
        }
