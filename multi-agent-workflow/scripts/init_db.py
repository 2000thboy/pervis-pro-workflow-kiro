#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import init_db, close_db
from app.core.config import settings
from app.models.project import Project
from app.models.agent import Agent, AgentType, AgentState
from app.models.workflow import WorkflowInstance
from app.models.asset import Asset


async def create_initial_agents():
    """创建初始Agent记录"""
    from app.core.database import AsyncSessionLocal
    
    agents_config = [
        {"agent_id": "director_001", "agent_type": AgentType.DIRECTOR, "capabilities": ["coordination", "decision_making"]},
        {"agent_id": "system_001", "agent_type": AgentType.SYSTEM, "capabilities": ["user_interface", "search"]},
        {"agent_id": "dam_001", "agent_type": AgentType.DAM, "capabilities": ["asset_management", "tagging"]},
        {"agent_id": "pm_001", "agent_type": AgentType.PM, "capabilities": ["project_management", "archiving"]},
        {"agent_id": "script_001", "agent_type": AgentType.SCRIPT, "capabilities": ["script_analysis", "duration_estimation"]},
        {"agent_id": "art_001", "agent_type": AgentType.ART, "capabilities": ["visual_design", "character_design"]},
        {"agent_id": "market_001", "agent_type": AgentType.MARKET, "capabilities": ["market_analysis", "competitor_research"]},
        {"agent_id": "backend_001", "agent_type": AgentType.BACKEND, "capabilities": ["monitoring", "error_detection"]},
    ]
    
    async with AsyncSessionLocal() as session:
        for agent_config in agents_config:
            agent = Agent(**agent_config)
            session.add(agent)
        
        await session.commit()
        print(f"已创建 {len(agents_config)} 个初始Agent")


async def main():
    """主函数"""
    print("初始化多Agent协作工作流数据库")
    print("=" * 50)
    
    try:
        # 初始化数据库
        print("正在初始化数据库...")
        await init_db()
        print("数据库初始化完成")
        
        # 创建初始Agent
        print("正在创建初始Agent...")
        await create_initial_agents()
        print("初始Agent创建完成")
        
        print("\n数据库初始化成功！")
        print(f"数据库URL: {settings.DATABASE_URL}")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)
    
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())