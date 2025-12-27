# -*- coding: utf-8 -*-
"""
素材库管理 API 路由

扩展现有 DAM 系统，提供素材库的 REST API：
- GET /api/libraries - 列出所有素材库
- POST /api/libraries - 创建素材库
- GET /api/libraries/{id} - 获取素材库详情
- PUT /api/libraries/{id} - 更新素材库
- DELETE /api/libraries/{id} - 删除素材库
- POST /api/libraries/{id}/scan - 扫描素材库
- POST /api/libraries/{id}/toggle - 切换激活状态
- POST /api/libraries/{id}/sync - 同步统计信息
- GET /api/libraries/validate-path - 验证路径
- GET /api/libraries/env-config - 获取环境配置
- POST /api/libraries/import-env - 从环境变量导入
- GET /api/projects/{project_id}/libraries - 获取项目素材库
- POST /api/projects/{project_id}/libraries - 分配素材库到项目

Requirements: 素材库管理系统
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/libraries", tags=["素材库管理"])


# ========================================
# 请求/响应模型
# ========================================

class CreateLibraryRequest(BaseModel):
    """创建素材库请求"""
    name: str = Field(..., min_length=1, max_length=100, description="库名称")
    path: str = Field(..., min_length=1, description="库路径")
    description: Optional[str] = Field(None, description="描述")
    path_type: str = Field("local", description="路径类型: local/network/smb/nfs")
    network_host: Optional[str] = Field(None, description="网络主机")
    network_share: Optional[str] = Field(None, description="共享名称")
    is_default: bool = Field(False, description="是否为默认库")
    scan_subdirs: bool = Field(True, description="是否扫描子目录")
    file_extensions: Optional[List[str]] = Field(None, description="支持的文件扩展名")
    tags: Optional[List[str]] = Field(None, description="库标签")


class UpdateLibraryRequest(BaseModel):
    """更新素材库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    path: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    path_type: Optional[str] = None
    network_host: Optional[str] = None
    network_share: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None
    scan_subdirs: Optional[bool] = None
    file_extensions: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class AssignLibraryRequest(BaseModel):
    """分配素材库到项目请求"""
    library_id: int = Field(..., description="素材库ID")
    is_primary: bool = Field(False, description="是否为主库")
    priority: int = Field(0, description="优先级")


# ========================================
# 依赖注入
# ========================================

def get_library_service(db: Session = Depends(get_db)):
    """获取素材库服务"""
    from services.asset_library_service import get_asset_library_service
    return get_asset_library_service(db)


# ========================================
# 素材库 CRUD API
# ========================================

@router.get("")
async def list_libraries(
    active_only: bool = Query(False, description="只返回激活的库"),
    service = Depends(get_library_service)
):
    """列出所有素材库"""
    libraries = service.list_libraries(active_only=active_only)
    return {"libraries": libraries, "total": len(libraries)}


@router.post("")
async def create_library(
    request: CreateLibraryRequest,
    service = Depends(get_library_service)
):
    """创建素材库"""
    result = service.create_library(
        name=request.name,
        path=request.path,
        description=request.description,
        path_type=request.path_type,
        network_host=request.network_host,
        network_share=request.network_share,
        is_default=request.is_default,
        scan_subdirs=request.scan_subdirs,
        file_extensions=request.file_extensions,
        tags=request.tags
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/env-config")
async def get_env_config(service = Depends(get_library_service)):
    """获取当前环境配置"""
    return service.get_env_config()


@router.post("/import-env")
async def import_from_env(service = Depends(get_library_service)):
    """从环境变量导入素材库配置"""
    result = service.import_from_env()
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/validate-path")
async def validate_path(
    path: str = Query(..., description="要验证的路径"),
    path_type: str = Query("local", description="路径类型"),
    service = Depends(get_library_service)
):
    """验证路径是否有效"""
    is_valid, error = service.validate_path(path, path_type)
    return {
        "path": path,
        "path_type": path_type,
        "is_valid": is_valid,
        "error": error if not is_valid else None,
        "is_accessible": service.check_path_accessible(path)
    }


@router.get("/{library_id}")
async def get_library(
    library_id: int,
    service = Depends(get_library_service)
):
    """获取素材库详情"""
    library = service.get_library(library_id)
    
    if not library:
        raise HTTPException(status_code=404, detail="素材库不存在")
    
    # 添加素材统计
    library["asset_count"] = service.count_library_assets(library_id)
    library["is_accessible"] = service.check_path_accessible(library["path"])
    
    return library


@router.put("/{library_id}")
async def update_library(
    library_id: int,
    request: UpdateLibraryRequest,
    service = Depends(get_library_service)
):
    """更新素材库"""
    update_data = request.dict(exclude_unset=True)
    result = service.update_library(library_id, **update_data)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.delete("/{library_id}")
async def delete_library(
    library_id: int,
    service = Depends(get_library_service)
):
    """删除素材库"""
    result = service.delete_library(library_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/{library_id}/scan")
async def scan_library(
    library_id: int,
    max_files: Optional[int] = Query(None, description="最大扫描文件数"),
    service = Depends(get_library_service)
):
    """扫描素材库"""
    result = service.scan_library(library_id, max_files=max_files)
    
    if result.errors:
        return {
            "success": False,
            "errors": result.errors,
            "partial_result": result.to_dict()
        }
    
    return {
        "success": True,
        "result": result.to_dict()
    }


@router.post("/{library_id}/toggle")
async def toggle_library(
    library_id: int,
    service = Depends(get_library_service)
):
    """切换素材库激活状态"""
    result = service.toggle_library_active(library_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.post("/{library_id}/sync")
async def sync_library_stats(
    library_id: int,
    service = Depends(get_library_service)
):
    """同步素材库统计信息"""
    result = service.sync_library_stats(library_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/{library_id}/assets")
async def get_library_assets(
    library_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service = Depends(get_library_service)
):
    """获取素材库中的素材"""
    assets = service.get_library_assets(library_id, limit=limit, offset=offset)
    total = service.count_library_assets(library_id)
    
    return {
        "assets": assets,
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ========================================
# 项目关联 API
# ========================================

project_router = APIRouter(prefix="/api/projects", tags=["项目素材库"])


@project_router.get("/{project_id}/libraries")
async def get_project_libraries(
    project_id: str,
    service = Depends(get_library_service)
):
    """获取项目关联的素材库"""
    libraries = service.get_project_libraries(project_id)
    return {"libraries": libraries, "total": len(libraries)}


@project_router.post("/{project_id}/libraries")
async def assign_library_to_project(
    project_id: str,
    request: AssignLibraryRequest,
    service = Depends(get_library_service)
):
    """分配素材库到项目"""
    result = service.assign_library_to_project(
        project_id=project_id,
        library_id=request.library_id,
        is_primary=request.is_primary,
        priority=request.priority
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@project_router.delete("/{project_id}/libraries/{library_id}")
async def remove_library_from_project(
    project_id: str,
    library_id: int,
    service = Depends(get_library_service)
):
    """从项目移除素材库"""
    result = service.remove_library_from_project(project_id, library_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


# ========================================
# 搜索 API
# ========================================

@router.post("/search")
async def search_in_libraries(
    query: str = Query(..., description="搜索查询"),
    library_ids: Optional[List[int]] = Query(None, description="指定素材库ID"),
    project_id: Optional[str] = Query(None, description="项目ID"),
    limit: int = Query(20, ge=1, le=100),
    service = Depends(get_library_service)
):
    """在素材库中搜索"""
    results = service.search_in_libraries(
        query=query,
        library_ids=library_ids,
        project_id=project_id,
        limit=limit
    )
    
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }
