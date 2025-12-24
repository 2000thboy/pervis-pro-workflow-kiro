# Core services and utilities
from .config import settings
from .error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorRecord,
    ErrorCategory,
    ErrorSeverity,
    RecoveryAction,
    PathValidationResult,
    APIMonitoringResult,
    get_error_handler,
    set_error_handler
)
from .monitoring import (
    SystemMonitor,
    HealthStatus,
    ComponentType,
    HealthCheckResult,
    SystemMetrics,
    OperationLog,
    get_system_monitor,
    set_system_monitor
)
from .message_bus import (
    MessageBus,
    Message,
    Response,
    MessageType,
    MessagePriority,
    Subscription,
    message_bus
)
from .communication_protocol import (
    AgentCommunicationProtocol,
    ProtocolMessage,
    ProtocolHeader,
    ProtocolPayload,
    ProtocolResponse,
    ProtocolMessageType,
    ProtocolStatus,
    ProtocolHandler,
    DefaultProtocolHandler,
    create_protocol_message,
    create_task_assignment,
    create_data_request
)
from .llm_service import (
    LLMService,
    LLMConfig,
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMRole,
    AIUsageRecord,
    BaseLLMClient,
    MockLLMClient,
    OllamaClient,
    OpenAIClient,
    GeminiClient,
    get_llm_service,
    set_llm_service
)
from .vector_store import (
    VectorService,
    VectorStoreConfig,
    VectorStoreProvider,
    Document,
    SearchResult,
    AssetMatch,
    BaseVectorStore,
    MockVectorStore,
    ChromaVectorStore,
    get_vector_service,
    set_vector_service
)
from .persistence import (
    PersistenceService,
    PersistenceConfig,
    StorageProvider,
    ProjectData,
    WorkflowStateData,
    AgentStateData,
    AssetData,
    BaseStorage,
    MemoryStorage,
    get_persistence_service,
    set_persistence_service
)

__all__ = [
    "settings",
    # Error Handler
    "ErrorHandler",
    "ErrorContext",
    "ErrorRecord",
    "ErrorCategory",
    "ErrorSeverity",
    "RecoveryAction",
    "PathValidationResult",
    "APIMonitoringResult",
    "get_error_handler",
    "set_error_handler",
    # Monitoring
    "SystemMonitor",
    "HealthStatus",
    "ComponentType",
    "HealthCheckResult",
    "SystemMetrics",
    "OperationLog",
    "get_system_monitor",
    "set_system_monitor",
    # Message Bus
    "MessageBus",
    "Message",
    "Response",
    "MessageType",
    "MessagePriority",
    "Subscription",
    "message_bus",
    # Communication Protocol
    "AgentCommunicationProtocol",
    "ProtocolMessage",
    "ProtocolHeader",
    "ProtocolPayload",
    "ProtocolResponse",
    "ProtocolMessageType",
    "ProtocolStatus",
    "ProtocolHandler",
    "DefaultProtocolHandler",
    "create_protocol_message",
    "create_task_assignment",
    "create_data_request",
    # LLM Service
    "LLMService",
    "LLMConfig",
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMRole",
    "AIUsageRecord",
    "BaseLLMClient",
    "MockLLMClient",
    "OllamaClient",
    "OpenAIClient",
    "GeminiClient",
    "get_llm_service",
    "set_llm_service",
    # Vector Store
    "VectorService",
    "VectorStoreConfig",
    "VectorStoreProvider",
    "Document",
    "SearchResult",
    "AssetMatch",
    "BaseVectorStore",
    "MockVectorStore",
    "ChromaVectorStore",
    "get_vector_service",
    "set_vector_service",
    # Persistence
    "PersistenceService",
    "PersistenceConfig",
    "StorageProvider",
    "ProjectData",
    "WorkflowStateData",
    "AgentStateData",
    "AssetData",
    "BaseStorage",
    "MemoryStorage",
    "get_persistence_service",
    "set_persistence_service"
]

# Optional imports that require additional dependencies
try:
    from .redis import redis_manager, RedisManager
    __all__.extend(["redis_manager", "RedisManager"])
except ImportError:
    pass