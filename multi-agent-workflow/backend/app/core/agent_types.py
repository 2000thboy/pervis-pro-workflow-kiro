"""
Agent类型和状态枚举定义

这些枚举定义独立于数据库模型，可以在不初始化数据库的情况下使用。
"""
from enum import Enum


class AgentState(Enum):
    """Agent工作状态枚举"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class AgentType(Enum):
    """Agent类型枚举"""
    DIRECTOR = "director"
    SYSTEM = "system"
    DAM = "dam"
    PM = "pm"
    SCRIPT = "script"
    ART = "art"
    MARKET = "market"
    BACKEND = "backend"
    STORYBOARD = "storyboard"  # 0-Fix.6: 故事板Agent
