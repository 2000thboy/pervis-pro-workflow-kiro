import asyncio
import json
import os
from typing import Iterable, Mapping, Optional

import aiohttp
from fastapi import APIRouter, Request, Response

# 本地 fallback 缓存
_local_fallback_cache = {
    "dam_available": None,  # None=未检测, True=可用, False=不可用
    "last_check": 0,
    "check_interval": 30,  # 30秒检测一次 DAM 状态
}


def _filter_hop_by_hop_headers(headers: Mapping[str, str]) -> dict[str, str]:
    excluded = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",
        "content-length",
    }
    return {k: v for k, v in headers.items() if k.lower() not in excluded}


async def _get_local_fallback(prefix: str, path: str = "") -> Optional[Response]:
    """
    当 DAM 服务不可用时，返回本地数据
    
    支持的端点:
    - /api/assets/list -> 返回本地数据库中的素材
    - /api/search -> 返回本地搜索结果
    - /api/tags -> 返回本地标签
    """
    import time
    from database import get_db, Asset
    
    full_path = f"{prefix}/{path}".rstrip("/") if path else prefix
    
    # /api/assets 或 /api/assets/list
    if full_path in ["/api/assets", "/api/assets/list"]:
        try:
            db = next(get_db())
            assets = db.query(Asset).limit(100).all()
            result = {
                "items": [
                    {
                        "id": a.id,
                        "filename": a.filename,
                        "mime_type": a.mime_type,
                        "source": a.source or "local",
                        "file_path": a.file_path,
                        "thumbnail_path": a.thumbnail_path,
                        "tags": a.tags or [],
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                    }
                    for a in assets
                ],
                "total": len(assets),
                "source": "local_fallback",
            }
            return Response(
                content=json.dumps(result, ensure_ascii=False),
                status_code=200,
                headers={"content-type": "application/json"},
            )
        except Exception:
            pass
    
    # /api/search
    if full_path == "/api/search":
        return Response(
            content=json.dumps({
                "results": [],
                "total": 0,
                "source": "local_fallback",
                "message": "DAM 服务不可用，请使用本地搜索功能"
            }, ensure_ascii=False),
            status_code=200,
            headers={"content-type": "application/json"},
        )
    
    # /api/tags
    if full_path in ["/api/tags", "/api/tags/list"]:
        return Response(
            content=json.dumps({
                "tags": [],
                "source": "local_fallback",
            }, ensure_ascii=False),
            status_code=200,
            headers={"content-type": "application/json"},
        )
    
    return None


async def _check_dam_available(dam_base_url: str) -> bool:
    """快速检测 DAM 服务是否可用"""
    import time
    
    now = time.time()
    # 使用缓存避免频繁检测
    if (_local_fallback_cache["dam_available"] is not None and 
        now - _local_fallback_cache["last_check"] < _local_fallback_cache["check_interval"]):
        return _local_fallback_cache["dam_available"]
    
    # 快速检测（500ms 超时）
    timeout = aiohttp.ClientTimeout(total=0.5, connect=0.3)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{dam_base_url}/health") as resp:
                available = resp.status == 200
                _local_fallback_cache["dam_available"] = available
                _local_fallback_cache["last_check"] = now
                return available
    except:
        _local_fallback_cache["dam_available"] = False
        _local_fallback_cache["last_check"] = now
        return False


async def _proxy_request(
    request: Request,
    target_base_url: str,
    target_path: str,
    allowed_response_headers: Optional[Iterable[str]] = None,
) -> Response:
    # 先检测 DAM 是否可用
    dam_available = await _check_dam_available(target_base_url)
    
    if not dam_available:
        # DAM 不可用，尝试本地 fallback
        fallback = await _get_local_fallback(target_path)
        if fallback:
            return fallback
        # 没有 fallback，返回服务不可用
        return Response(
            content=json.dumps({
                "error": "DAM service unavailable",
                "source": "local_fallback",
                "message": "DAM 服务不可用，且无本地数据"
            }, ensure_ascii=False),
            status_code=503,
            headers={"content-type": "application/json"},
        )
    
    method = request.method.upper()
    query = request.url.query
    target_url = f"{target_base_url.rstrip('/')}/{target_path.lstrip('/')}"
    if query:
        target_url = f"{target_url}?{query}"

    headers = _filter_hop_by_hop_headers(dict(request.headers))
    body = await request.body()

    # 使用较短的超时时间，避免长时间等待
    timeout = aiohttp.ClientTimeout(total=5, connect=2)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, target_url, data=body, headers=headers) as resp:
                resp_body = await resp.read()
                resp_headers = dict(resp.headers)
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        # DAM 服务不可用时，标记并尝试 fallback
        _local_fallback_cache["dam_available"] = False
        _local_fallback_cache["last_check"] = __import__("time").time()
        
        fallback = await _get_local_fallback(target_path)
        if fallback:
            return fallback
        
        return Response(
            content=json.dumps({
                "error": "DAM service unavailable",
                "detail": str(e)
            }, ensure_ascii=False),
            status_code=503,
            headers={"content-type": "application/json"},
        )

    if allowed_response_headers is None:
        forwarded_headers = _filter_hop_by_hop_headers(resp_headers)
    else:
        allow = {h.lower() for h in allowed_response_headers}
        forwarded_headers = {
            k: v for k, v in resp_headers.items() if k.lower() in allow
        }

    content_type = resp_headers.get("content-type")
    if content_type:
        forwarded_headers.setdefault("content-type", content_type)

    return Response(
        content=resp_body,
        status_code=resp.status,
        headers=forwarded_headers,
    )


def create_dam_proxy_router(prefix: str) -> APIRouter:
    dam_base_url = os.getenv("DAM_BASE_URL", "http://localhost:8001")
    router = APIRouter(prefix=prefix)

    @router.api_route(
        "",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def proxy_root(request: Request) -> Response:
        return await _proxy_request(request, dam_base_url, prefix)

    @router.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def proxy_path(path: str, request: Request) -> Response:
        return await _proxy_request(request, dam_base_url, f"{prefix}/{path}")

    return router

