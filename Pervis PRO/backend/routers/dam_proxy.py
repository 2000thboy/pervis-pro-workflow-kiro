import os
from typing import Iterable, Mapping, Optional

import aiohttp
from fastapi import APIRouter, Request, Response


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


async def _proxy_request(
    request: Request,
    target_base_url: str,
    target_path: str,
    allowed_response_headers: Optional[Iterable[str]] = None,
) -> Response:
    method = request.method.upper()
    query = request.url.query
    target_url = f"{target_base_url.rstrip('/')}/{target_path.lstrip('/')}"
    if query:
        target_url = f"{target_url}?{query}"

    headers = _filter_hop_by_hop_headers(dict(request.headers))
    body = await request.body()

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.request(method, target_url, data=body, headers=headers) as resp:
            resp_body = await resp.read()
            resp_headers = dict(resp.headers)

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

