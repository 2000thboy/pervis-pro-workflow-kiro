"""
向量分析API路由
支持相似度计算和搜索测试
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database import get_db
from services.vector_analyzer import VectorAnalyzer

router = APIRouter()


# 请求模型
class SimilarityRequest(BaseModel):
    query: str
    asset_ids: Optional[List[str]] = None
    top_k: int = 10


class MatchExplanationRequest(BaseModel):
    query: str
    asset_id: str


class SaveTestCaseRequest(BaseModel):
    name: str
    query: str
    expected_results: List[str]


# API端点
@router.post("/similarity")
async def calculate_similarity(request: SimilarityRequest, db: Session = Depends(get_db)):
    """计算相似度"""
    analyzer = VectorAnalyzer(db)
    result = await analyzer.calculate_similarity(
        query=request.query,
        asset_ids=request.asset_ids,
        top_k=request.top_k
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/explain")
async def explain_match(request: MatchExplanationRequest, db: Session = Depends(get_db)):
    """解释匹配结果"""
    analyzer = VectorAnalyzer(db)
    result = await analyzer.explain_match(
        query=request.query,
        asset_id=request.asset_id
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.post("/test-case")
async def save_test_case(request: SaveTestCaseRequest, db: Session = Depends(get_db)):
    """保存搜索测试案例"""
    analyzer = VectorAnalyzer(db)
    result = await analyzer.save_test_case(
        name=request.name,
        query=request.query,
        expected_results=request.expected_results
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    
    return result


@router.get("/test-cases")
async def get_test_cases(db: Session = Depends(get_db)):
    """获取所有测试案例"""
    from database import SearchTestCase
    
    test_cases = db.query(SearchTestCase).order_by(
        SearchTestCase.created_at.desc()
    ).all()
    
    return {
        "status": "success",
        "test_cases": [
            {
                "id": tc.id,
                "name": tc.name,
                "query": tc.query,
                "status": tc.status,
                "expected_count": len(tc.expected_results) if tc.expected_results else 0,
                "actual_count": len(tc.actual_results) if tc.actual_results else 0,
                "created_at": tc.created_at
            }
            for tc in test_cases
        ]
    }
