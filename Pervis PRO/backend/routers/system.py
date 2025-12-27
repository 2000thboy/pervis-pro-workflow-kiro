"""
系统路由 - 健康检查、通知管理、系统操作

提供系统级别的 API 端点。
"""

import os
import uuid
import shutil
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.health_checker import health_checker
from services.event_service import event_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Pydantic 模型 ============

class NotificationResponse(BaseModel):
    """通知响应"""
    id: str
    type: str
    level: str
    title: str
    message: str
    action: Optional[dict] = None
    is_read: bool
    task_id: Optional[str] = None
    agent_type: Optional[str] = None
    created_at: str
    read_at: Optional[str] = None


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    checks: dict
    timestamp: str


class ActionResponse(BaseModel):
    """操作响应"""
    success: bool
    message: str
    details: Optional[dict] = None


# ============ 健康检查 API ============

@router.get("/health", response_model=HealthCheckResponse)
async def get_health():
    """
    执行系统健康检查
    
    检查项目:
    - API 服务状态
    - 数据库连接
    - FFmpeg 可用性
    - AI 服务 (Ollama)
    - 存储空间
    - 缓存状态
    
    Returns:
        健康检查结果
    """
    result = await health_checker.check_all()
    return result.to_dict()


@router.get("/health/quick")
async def get_health_quick():
    """
    快速健康检查（仅检查 API 状态）
    
    Returns:
        简单的健康状态
    """
    return {
        "status": "healthy",
        "service": "pervis-pro",
        "timestamp": datetime.now().isoformat()
    }


# ============ 通知管理 API ============

# 内存中的通知存储（生产环境应使用数据库）
_notifications: List[dict] = []


def _get_notification_by_id(notification_id: str) -> Optional[dict]:
    """根据 ID 获取通知"""
    for n in _notifications:
        if n["id"] == notification_id:
            return n
    return None


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    type: Optional[str] = Query(None, description="通知类型: task, warning, error, info"),
    level: Optional[str] = Query(None, description="通知级别: critical, warning, info"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取通知列表
    
    Args:
        type: 按类型筛选
        level: 按级别筛选
        is_read: 按已读状态筛选
        limit: 返回数量
        offset: 偏移量
    
    Returns:
        通知列表
    """
    filtered = _notifications.copy()
    
    # 筛选
    if type:
        filtered = [n for n in filtered if n["type"] == type]
    if level:
        filtered = [n for n in filtered if n["level"] == level]
    if is_read is not None:
        filtered = [n for n in filtered if n["is_read"] == is_read]
    
    # 按时间倒序
    filtered.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 分页
    total = len(filtered)
    paginated = filtered[offset:offset + limit]
    
    # 统计未读数
    unread_count = len([n for n in _notifications if not n["is_read"]])
    
    return NotificationListResponse(
        notifications=paginated,
        total=total,
        unread_count=unread_count
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """
    标记通知为已读
    
    Args:
        notification_id: 通知 ID
    
    Returns:
        操作结果
    """
    notification = _get_notification_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    notification["is_read"] = True
    notification["read_at"] = datetime.now().isoformat()
    
    return {"success": True, "message": "已标记为已读"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str):
    """
    删除通知
    
    Args:
        notification_id: 通知 ID
    
    Returns:
        操作结果
    """
    global _notifications
    
    notification = _get_notification_by_id(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="通知不存在")
    
    _notifications = [n for n in _notifications if n["id"] != notification_id]
    
    return {"success": True, "message": "通知已删除"}


@router.post("/notifications/clear")
async def clear_notifications(
    type: Optional[str] = Query(None, description="只清除指定类型"),
    before_days: int = Query(7, description="清除多少天前的通知")
):
    """
    清空通知
    
    Args:
        type: 只清除指定类型
        before_days: 清除多少天前的通知
    
    Returns:
        操作结果
    """
    global _notifications
    
    cutoff = datetime.now() - timedelta(days=before_days)
    cutoff_str = cutoff.isoformat()
    
    original_count = len(_notifications)
    
    if type:
        _notifications = [
            n for n in _notifications 
            if n["type"] != type or n["created_at"] > cutoff_str
        ]
    else:
        _notifications = [
            n for n in _notifications 
            if n["created_at"] > cutoff_str
        ]
    
    cleared_count = original_count - len(_notifications)
    
    return {
        "success": True, 
        "message": f"已清除 {cleared_count} 条通知",
        "details": {"cleared_count": cleared_count}
    }


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read():
    """
    标记所有通知为已读
    
    Returns:
        操作结果
    """
    now = datetime.now().isoformat()
    count = 0
    
    for n in _notifications:
        if not n["is_read"]:
            n["is_read"] = True
            n["read_at"] = now
            count += 1
    
    return {
        "success": True,
        "message": f"已标记 {count} 条通知为已读"
    }


# ============ 系统操作 API ============

@router.post("/actions/clean-cache", response_model=ActionResponse)
async def clean_cache():
    """
    清理系统缓存
    
    清理项目:
    - 临时文件
    - 缩略图缓存
    - 代理文件缓存
    
    Returns:
        操作结果
    """
    try:
        cache_dirs = [
            os.getenv("CACHE_DIR", "./data/cache"),
            "./data/temp",
            "./temp"
        ]
        
        total_freed = 0
        files_deleted = 0
        
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                for item in os.listdir(cache_dir):
                    item_path = os.path.join(cache_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            os.remove(item_path)
                            total_freed += size
                            files_deleted += 1
                        elif os.path.isdir(item_path):
                            size = sum(
                                os.path.getsize(os.path.join(dp, f))
                                for dp, dn, fn in os.walk(item_path)
                                for f in fn
                            )
                            shutil.rmtree(item_path)
                            total_freed += size
                            files_deleted += 1
                    except Exception as e:
                        logger.warning(f"清理失败: {item_path}, {e}")
        
        freed_mb = total_freed / (1024 ** 2)
        
        # 发送系统信息事件
        await event_service.emit_system_info(
            f"缓存清理完成，释放 {freed_mb:.1f} MB",
            {"freed_mb": freed_mb, "files_deleted": files_deleted}
        )
        
        return ActionResponse(
            success=True,
            message=f"缓存清理完成，释放 {freed_mb:.1f} MB",
            details={"freed_mb": round(freed_mb, 2), "files_deleted": files_deleted}
        )
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        return ActionResponse(
            success=False,
            message=f"清理缓存失败: {str(e)}"
        )


@router.post("/actions/retry-task/{task_id}", response_model=ActionResponse)
async def retry_task(task_id: str):
    """
    重试失败的任务
    
    Args:
        task_id: 任务 ID
    
    Returns:
        操作结果
    """
    # TODO: 实现任务重试逻辑
    # 需要根据任务类型调用相应的服务
    
    return ActionResponse(
        success=False,
        message="任务重试功能尚未实现",
        details={"task_id": task_id}
    )


@router.post("/actions/relink-asset", response_model=ActionResponse)
async def relink_asset(
    asset_id: str = Query(..., description="素材 ID"),
    new_path: str = Query(..., description="新路径")
):
    """
    重新链接素材文件
    
    当素材文件移动位置后，使用此接口更新路径。
    
    Args:
        asset_id: 素材 ID
        new_path: 新的文件路径
    
    Returns:
        操作结果
    """
    # 验证新路径是否存在
    if not os.path.exists(new_path):
        return ActionResponse(
            success=False,
            message=f"文件不存在: {new_path}"
        )
    
    # TODO: 更新数据库中的素材路径
    
    return ActionResponse(
        success=False,
        message="素材重新链接功能尚未实现",
        details={"asset_id": asset_id, "new_path": new_path}
    )


# ============ 内部函数：添加通知 ============

def add_notification(
    type: str,
    level: str,
    title: str,
    message: str,
    action: Optional[dict] = None,
    task_id: Optional[str] = None,
    agent_type: Optional[str] = None
) -> dict:
    """
    添加新通知（内部使用）
    
    Args:
        type: 通知类型
        level: 通知级别
        title: 标题
        message: 消息
        action: 操作建议
        task_id: 关联任务 ID
        agent_type: 关联 Agent 类型
    
    Returns:
        创建的通知
    """
    notification = {
        "id": str(uuid.uuid4()),
        "type": type,
        "level": level,
        "title": title,
        "message": message,
        "action": action,
        "is_read": False,
        "task_id": task_id,
        "agent_type": agent_type,
        "created_at": datetime.now().isoformat(),
        "read_at": None
    }
    
    _notifications.append(notification)
    
    # 限制通知数量（保留最近 500 条）
    if len(_notifications) > 500:
        _notifications.sort(key=lambda x: x["created_at"], reverse=True)
        _notifications[:] = _notifications[:500]
    
    return notification
