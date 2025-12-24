"""
语义搜索路由
Phase 2: 集成语义搜索引擎进行真实搜索
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.semantic_search import SemanticSearchEngine
from models.base import SearchQuery, SearchResponse, SearchResult
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(query: SearchQuery, db: Session = Depends(get_db)):
    """
    语义搜索接口
    Phase 2: 基于Beat进行真实的语义搜索
    前端集成修复：支持不存在的Beat ID
    """
    
    start_time = time.time()
    
    try:
        # 创建语义搜索引擎
        search_engine = SemanticSearchEngine(db)
        
        # 检查Beat是否存在，如果不存在则使用默认处理
        beat_id = query.beat_id
        if beat_id and beat_id != "default_beat":
            from sqlalchemy import text
            beat_exists = db.execute(
                text("SELECT 1 FROM beats WHERE id = :beat_id"),
                {"beat_id": beat_id}
            ).fetchone()
            
            if not beat_exists:
                # Beat不存在时使用默认beat_id
                beat_id = "default_beat"
        
        # 执行搜索
        search_result = await search_engine.search_by_beat(
            beat_id=beat_id,
            fuzziness=query.fuzziness,
            limit=query.limit
        )
        
        if search_result["status"] != "success":
            # 如果搜索失败，返回空结果而不是错误
            logger.warning(f"搜索失败但返回空结果: {search_result.get('message', '未知错误')}")
            return SearchResponse(
                results=[],
                total_matches=0,
                search_time=time.time() - start_time,
                query_info={
                    "beat_id": query.beat_id,
                    "fuzziness": query.fuzziness,
                    "fallback_mode": True,
                    "error": search_result.get("message", "搜索失败")
                }
            )
        
        # 转换搜索结果格式
        results = []
        for rec in search_result["recommendations"]:
            # 为每个segment创建一个搜索结果
            for segment in rec["segments"]:
                result = SearchResult(
                    asset_id=rec["asset_id"],
                    segment_id=segment["id"],
                    match_score=rec["similarity_score"],
                    match_reason=rec["reason"],
                    preview_url=f"{rec['proxy_url']}#t={segment['start_time']},{segment['end_time']}" if rec["proxy_url"] else None,
                    thumbnail_url=rec["thumbnail_url"],
                    tags_matched=_extract_matched_tags(segment["tags"], query.query_tags)
                )
                results.append(result)
        
        search_time = time.time() - start_time
        
        return SearchResponse(
            results=results,
            total_matches=len(results),
            search_time=search_time,
            query_info={
                "beat_id": query.beat_id,
                "fuzziness": query.fuzziness,
                "fallback_mode": search_result.get("search_params", {}).get("fallback_mode", False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"语义搜索失败: {e}")
        # 返回空结果而不是抛出错误，保持前端稳定
        return SearchResponse(
            results=[],
            total_matches=0,
            search_time=time.time() - start_time,
            query_info={
                "beat_id": query.beat_id,
                "fuzziness": query.fuzziness,
                "fallback_mode": True,
                "error": str(e)
            }
        )

def _extract_matched_tags(segment_tags: dict, query_tags: dict) -> list:
    """提取匹配的标签"""
    
    matched = []
    
    for tag_type in ["emotions", "scenes", "actions", "cinematography"]:
        segment_list = segment_tags.get(tag_type, [])
        query_list = query_tags.get(tag_type, [])
        
        # 找到交集
        common_tags = set(segment_list) & set(query_list)
        matched.extend(list(common_tags))
    
    return matched[:5]  # 限制返回数量