"""
Agent类型和状态枚举定义

这些枚举定义独立于数据库模型，可以在不初始化数据库的情况下使用。
"""
from enum import Enum


class AgentState(Enum):
    """Agent工作状态枚举"""
    IDLE = "idle"           # 空闲
    WORKING = "working"     # 工作中
    WAITING = "waiting"     # 等待中
    REVIEWING = "reviewing" # 审核中 (Pervis PRO 特有)
    ERROR = "error"         # 错误
    OFFLINE = "offline"     # 离线


class AgentType(Enum):
    """Agent类型枚举"""
    # 核心 Agent
    DIRECTOR = "director"       # 导演 Agent - 总协调
    SYSTEM = "system"           # 系统 Agent - 健康检查、通知
    
    # 创作 Agent
    SCRIPT = "script"           # 剧本 Agent - 剧本分析、场次拆分
    ART = "art"                 # 美术 Agent - 视觉风格、参考图
    STORYBOARD = "storyboard"   # 故事板 Agent - Beat 生成
    
    # 业务 Agent
    PM = "pm"                   # 项目经理 Agent - 进度管理
    MARKET = "market"           # 市场 Agent - 市场分析
    
    # 技术 Agent
    DAM = "dam"                 # 数字资产管理 Agent
    BACKEND = "backend"         # 后端 Agent - 技术支持
