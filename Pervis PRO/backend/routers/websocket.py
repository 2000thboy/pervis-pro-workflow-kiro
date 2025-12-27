"""
WebSocket 路由 - 实时事件推送

提供 WebSocket 端点用于前端接收实时事件。
"""

import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.event_service import event_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket 事件端点
    
    客户端连接后可以接收以下类型的事件:
    - task.started / task.progress / task.completed / task.failed
    - agent.working / agent.reviewing / agent.completed / agent.failed
    - system.warning / system.error / system.info
    - health.check
    
    客户端可以发送 "ping" 消息，服务端会回复 "pong"
    """
    await event_service.connect(websocket)
    
    try:
        while True:
            # 接收客户端消息（心跳检测）
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 60秒超时
                )
                
                if data == "ping":
                    await websocket.send_text("pong")
                    logger.debug("收到心跳 ping，已回复 pong")
                    
            except asyncio.TimeoutError:
                # 超时后发送心跳检测
                try:
                    await websocket.send_text("heartbeat")
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        logger.info("WebSocket 客户端主动断开连接")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        await event_service.disconnect(websocket)


@router.get("/ws/status")
async def websocket_status():
    """
    获取 WebSocket 连接状态
    
    Returns:
        连接数和状态信息
    """
    return {
        "connection_count": event_service.connection_count,
        "is_connected": event_service.is_connected
    }
