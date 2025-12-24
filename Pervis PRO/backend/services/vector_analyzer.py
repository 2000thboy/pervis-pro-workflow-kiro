"""
向量分析服务
支持相似度计算和向量空间可视化
"""

from typing import Optional, Dict, Any, List
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import Asset, AssetVector, AssetTag, TagHierarchy, SearchTestCase
from services.gemini_client import GeminiClient
import uuid
from datetime import datetime


class VectorAnalyzer:
    """向量分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gemini_client = GeminiClient()
    
    async def calculate_similarity(
        self,
        query: str,
        asset_ids: Optional[List[str]] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """计算查询与视频的相似度"""
        try:
            # 生成查询向量
            query_embedding = await self.gemini_client.generate_embedding(query)
            if not query_embedding:
                return {"status": "error", "message": "生成查询向量失败"}
            
            # 获取资产向量
            if asset_ids:
                asset_vectors = self.db.query(AssetVector).filter(
                    AssetVector.asset_id.in_(asset_ids)
                ).all()
            else:
                asset_vectors = self.db.query(AssetVector).all()
            
            # 计算相似度
            results = []
            for asset_vector in asset_vectors:
                # 解析向量数据
                import json
                vector_data = json.loads(asset_vector.vector_data)
                asset_embedding = vector_data.get("embedding", [])
                
                if not asset_embedding:
                    continue
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(query_embedding, asset_embedding)
                
                # 获取资产信息
                asset = self.db.query(Asset).filter(Asset.id == asset_vector.asset_id).first()
                if not asset:
                    continue
                
                # 获取标签贡献度
                tag_contributions = await self._calculate_tag_contributions(
                    query, asset_vector.asset_id
                )
                
                # 调整相似度（考虑标签权重）
                adjusted_similarity = self._adjust_similarity_with_weights(
                    similarity, tag_contributions
                )
                
                results.append({
                    "asset_id": asset_vector.asset_id,
                    "filename": asset.filename,
                    "score": adjusted_similarity,
                    "raw_score": similarity,
                    "matched_tags": [t["tag_name"] for t in tag_contributions],
                    "tag_contributions": tag_contributions
                })
            
            # 排序并返回Top-K
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:top_k]
            
            return {
                "status": "success",
                "query": query,
                "results": results,
                "total_results": len(results)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"相似度计算失败: {str(e)}"
            }
    
    async def explain_match(
        self,
        query: str,
        asset_id: str
    ) -> Dict[str, Any]:
        """解释匹配结果"""
        try:
            # 获取资产信息
            asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                return {"status": "error", "message": "资产不存在"}
            
            # 计算相似度
            similarity_result = await self.calculate_similarity(query, [asset_id], 1)
            if similarity_result["status"] != "success" or not similarity_result["results"]:
                return {"status": "error", "message": "无法计算相似度"}
            
            result = similarity_result["results"][0]
            
            # 分析查询关键词
            query_keywords = query.split()
            
            # 获取匹配的标签
            matched_tags = result["tag_contributions"]
            
            # 生成解释文本
            explanation_parts = []
            explanation_parts.append(f"查询 \"{query}\" 与资产 \"{asset.filename}\" 的匹配分析：")
            explanation_parts.append(f"\n总体相似度: {result['score']:.2f}")
            explanation_parts.append(f"原始向量相似度: {result['raw_score']:.2f}")
            
            if matched_tags:
                explanation_parts.append(f"\n匹配的标签 ({len(matched_tags)}个):")
                for tag in matched_tags[:5]:  # 只显示前5个
                    explanation_parts.append(
                        f"  - {tag['tag_name']}: 权重 {tag['weight']:.2f}, "
                        f"贡献度 {tag['contribution']:.2f}"
                    )
            
            explanation_text = "\n".join(explanation_parts)
            
            return {
                "status": "success",
                "query": query,
                "asset_id": asset_id,
                "overall_score": result["score"],
                "matched_keywords": query_keywords,
                "tag_matches": matched_tags,
                "explanation_text": explanation_text
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"生成匹配解释失败: {str(e)}"
            }
    
    async def save_test_case(
        self,
        name: str,
        query: str,
        expected_results: List[str]
    ) -> Dict[str, Any]:
        """保存搜索测试案例"""
        try:
            # 执行搜索
            search_result = await self.calculate_similarity(query, top_k=10)
            
            if search_result["status"] != "success":
                return {"status": "error", "message": "搜索失败"}
            
            actual_results = [r["asset_id"] for r in search_result["results"]]
            
            # 计算测试状态
            status = "passed" if set(expected_results).issubset(set(actual_results[:len(expected_results)])) else "failed"
            
            # 保存测试案例
            test_case = SearchTestCase(
                id=str(uuid.uuid4()),
                name=name,
                query=query,
                expected_results=expected_results,
                actual_results=actual_results,
                similarity_scores={r["asset_id"]: r["score"] for r in search_result["results"]},
                tag_contributions={r["asset_id"]: r["tag_contributions"] for r in search_result["results"]},
                status=status,
                created_at=datetime.now()
            )
            
            self.db.add(test_case)
            self.db.commit()
            
            return {
                "status": "success",
                "test_case_id": test_case.id,
                "test_status": status,
                "expected_count": len(expected_results),
                "actual_count": len(actual_results)
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"保存测试案例失败: {str(e)}"
            }
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    async def _calculate_tag_contributions(
        self,
        query: str,
        asset_id: str
    ) -> List[Dict[str, Any]]:
        """计算标签贡献度"""
        contributions = []
        
        # 获取资产的所有标签
        asset_tags = self.db.query(AssetTag).filter(
            AssetTag.asset_id == asset_id
        ).all()
        
        query_lower = query.lower()
        
        for asset_tag in asset_tags:
            tag = self.db.query(TagHierarchy).filter(
                TagHierarchy.id == asset_tag.tag_id
            ).first()
            
            if not tag:
                continue
            
            # 简单的关键词匹配
            tag_name_lower = tag.tag_name.lower()
            if tag_name_lower in query_lower or query_lower in tag_name_lower:
                contribution = asset_tag.weight * 0.5  # 基础贡献度
                contributions.append({
                    "tag_id": tag.id,
                    "tag_name": tag.tag_name,
                    "weight": asset_tag.weight,
                    "contribution": contribution
                })
        
        return contributions
    
    def _adjust_similarity_with_weights(
        self,
        base_similarity: float,
        tag_contributions: List[Dict[str, Any]]
    ) -> float:
        """根据标签权重调整相似度"""
        if not tag_contributions:
            return base_similarity
        
        # 计算标签贡献的总和
        total_contribution = sum(t["contribution"] for t in tag_contributions)
        
        # 调整相似度（最多增加20%）
        adjustment = min(total_contribution, 0.2)
        adjusted = base_similarity + adjustment
        
        return min(adjusted, 1.0)  # 确保不超过1.0
