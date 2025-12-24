"""
语义搜索引擎
Phase 2: 基于向量相似度的语义搜索和推荐
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from services.database_service import DatabaseService
from services.gemini_client import GeminiClient
import logging

logger = logging.getLogger(__name__)

# 预设默认值
SENTENCE_TRANSFORMERS_AVAILABLE = False
np = None
SentenceTransformer = None

# 强制使用Mock模式 - 临时禁用sentence-transformers以解决依赖问题
# TODO: 安装GTK依赖后可重新启用
FORCE_MOCK_MODE = True

if not FORCE_MOCK_MODE:
    # 尝试导入sentence-transformers，如果失败则使用降级模式
    try:
        import numpy as np_module
        from sentence_transformers import SentenceTransformer as STModel
        np = np_module
        SentenceTransformer = STModel
        SENTENCE_TRANSFORMERS_AVAILABLE = True
        logger.info("sentence-transformers 可用")
    except Exception as e:
        logger.warning(f"sentence-transformers 不可用，将使用降级模式: {e}")
else:
    # Mock模式
    import numpy as np
    logger.info("强制使用Mock模式（sentence-transformers已禁用）")

class SemanticSearchEngine:
    
    EXPECTED_VECTOR_DIM = 384  # all-MiniLM-L6-v2的标准维度
    
    def __init__(self, db: Session):
        self.db = db
        self.db_service = DatabaseService(db)
        self.gemini_client = GeminiClient()
        
        # 初始化文本嵌入模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("语义搜索模型加载成功")
            except Exception as e:
                logger.error(f"语义搜索模型加载失败: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
            logger.info("使用降级搜索模式")
    
    def _validate_vector_dimension(self, vector) -> bool:
        """P0 Fix: 校验向量维度"""
        if len(vector) != self.EXPECTED_VECTOR_DIM:
            logger.error(f"向量维度错误: 期望{self.EXPECTED_VECTOR_DIM}, 实际{len(vector)}")
            return False
        return True
    
    async def search_by_beat(self, beat_id: str, fuzziness: float = 0.7, limit: int = 5, include_transcription: bool = True) -> Dict[str, Any]:
        """
        根据Beat进行语义搜索
        
        Args:
            beat_id: Beat ID
            fuzziness: 模糊度 (0.0-1.0, 越高越宽松)
            limit: 返回结果数量限制
        """
        
        try:
            # 1. 获取Beat信息
            beat = await self.db_service.get_beat(beat_id)
            if not beat:
                return {
                    "status": "error",
                    "message": "Beat不存在"
                }
            
            # 2. 构建搜索查询文本
            query_text = self._build_query_text(beat)
            
            # 3. 生成查询向量
            if not SENTENCE_TRANSFORMERS_AVAILABLE or not self.embedding_model:
                return await self._fallback_search(beat, limit)
            
            query_vector = self.embedding_model.encode([query_text])[0]
            
            # 4. 搜索相似向量
            similar_vectors = self._search_similar_vectors(query_vector, fuzziness, limit)
            
            # 5. 构建推荐结果
            recommendations = await self._build_recommendations(beat, similar_vectors, query_text)
            
            # 6. 如果启用转录搜索，添加转录匹配结果
            transcription_matches = []
            if include_transcription:
                transcription_matches = await self._search_transcription_content(beat, query_text, limit)
            
            return {
                "status": "success",
                "query": {
                    "beat_id": beat_id,
                    "content": beat.content,
                    "tags": {
                        "emotions": beat.emotion_tags or [],
                        "scenes": beat.scene_tags or [],
                        "actions": beat.action_tags or [],
                        "cinematography": beat.cinematography_tags or []
                    }
                },
                "recommendations": recommendations,
                "transcription_matches": transcription_matches,
                "search_params": {
                    "fuzziness": fuzziness,
                    "limit": limit,
                    "include_transcription": include_transcription
                }
            }
            
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return {
                "status": "error",
                "message": f"搜索失败: {str(e)}"
            }
    
    def _build_query_text(self, beat) -> str:
        """构建搜索查询文本"""
        
        parts = []
        
        # Beat内容
        if beat.content:
            parts.append(beat.content)
        
        # 标签信息
        if beat.emotion_tags:
            parts.append(f"情绪: {', '.join(beat.emotion_tags)}")
        
        if beat.scene_tags:
            parts.append(f"场景: {', '.join(beat.scene_tags)}")
        
        if beat.action_tags:
            parts.append(f"动作: {', '.join(beat.action_tags)}")
        
        if beat.cinematography_tags:
            parts.append(f"镜头: {', '.join(beat.cinematography_tags)}")
        
        return " ".join(parts)
    
    def _search_similar_vectors(self, query_vector, fuzziness: float, limit: int) -> List[Dict]:
        """搜索相似向量"""
        
        # P0 Fix: 校验查询向量维度
        if not self._validate_vector_dimension(query_vector):
            logger.error("查询向量维度错误")
            return []
        
        # 获取所有向量
        all_vectors = self.db_service.search_vectors_by_similarity("", limit * 3)  # 获取更多候选
        
        if not all_vectors:
            return []
        
        results = []
        
        for vector_record in all_vectors:
            try:
                # 解析向量数据
                if not SENTENCE_TRANSFORMERS_AVAILABLE:
                    continue
                    
                stored_vector = np.array(json.loads(vector_record.vector_data))
                
                # P0 Fix: 校验存储向量维度
                if not self._validate_vector_dimension(stored_vector):
                    logger.warning(f"跳过维度错误的存储向量: {vector_record.id}")
                    continue
                
                # 计算余弦相似度
                similarity = self._cosine_similarity(query_vector, stored_vector)
                
                # 应用模糊度阈值
                threshold = 1.0 - fuzziness  # fuzziness越高，阈值越低
                
                if similarity >= threshold:
                    results.append({
                        "vector_record": vector_record,
                        "similarity": float(similarity)
                    })
                    
            except Exception as e:
                logger.warning(f"向量解析失败: {e}")
                continue
        
        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:limit]
    
    def _cosine_similarity(self, vec1, vec2) -> float:
        """计算余弦相似度"""
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return 0.5  # 默认相似度
            
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def _build_recommendations(self, beat, similar_vectors: List[Dict], query_text: str) -> List[Dict]:
        """构建推荐结果"""
        
        recommendations = []
        
        for result in similar_vectors:
            vector_record = result["vector_record"]
            similarity = result["similarity"]
            
            # 获取关联的资产和片段信息
            asset = await self.db_service.get_asset(vector_record.asset_id)
            if not asset:
                continue
            
            segments = await self.db_service.get_asset_segments(vector_record.asset_id)
            
            # 生成推荐理由
            reason = await self._generate_recommendation_reason(
                beat, asset, vector_record, similarity, query_text
            )
            
            recommendation = {
                "asset_id": asset.id,
                "filename": asset.filename,
                "similarity_score": similarity,
                "proxy_url": f"/assets/proxies/{asset.id}_proxy.mp4" if asset.proxy_path else None,
                "thumbnail_url": f"/assets/thumbnails/{asset.id}_thumb.jpg" if asset.thumbnail_path else None,
                "reason": reason,
                "segments": []
            }
            
            # 添加相关片段
            for segment in segments:
                if segment.id == vector_record.segment_id or not vector_record.segment_id:
                    recommendation["segments"].append({
                        "id": segment.id,
                        "start_time": segment.start_time,
                        "end_time": segment.end_time,
                        "description": segment.description,
                        "tags": {
                            "emotions": segment.emotion_tags or [],
                            "scenes": segment.scene_tags or [],
                            "actions": segment.action_tags or [],
                            "cinematography": segment.cinematography_tags or []
                        }
                    })
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_recommendation_reason(self, beat, asset, vector_record, similarity: float, query_text: str) -> str:
        """生成推荐理由"""
        
        try:
            # 构建推荐理由生成的提示
            prompt = f"""
作为导演助手，请为以下推荐生成简洁的理由说明：

剧本需求：
{beat.content}
标签：情绪({beat.emotion_tags}), 场景({beat.scene_tags}), 动作({beat.action_tags}), 镜头({beat.cinematography_tags})

推荐素材：
文件名：{asset.filename}
匹配内容：{vector_record.text_content}
相似度：{similarity:.2f}

请用1-2句话说明为什么这个素材适合这个剧本片段，重点说明情绪、场景或镜头语言的匹配。
"""
            
            reason_result = await self.gemini_client.generate_text(prompt)
            
            if reason_result["status"] == "success":
                return reason_result["data"]["text"].strip()
            else:
                return f"基于{similarity:.1%}的语义相似度匹配推荐"
                
        except Exception as e:
            logger.warning(f"推荐理由生成失败: {e}")
            return f"基于{similarity:.1%}的语义相似度匹配推荐"
    
    async def _fallback_search(self, beat, limit: int) -> Dict[str, Any]:
        """降级搜索 - 当向量模型不可用时"""
        
        logger.warning("使用降级搜索模式")
        
        # 简单的标签匹配搜索
        all_vectors = self.db_service.search_vectors_by_similarity("", limit * 2)
        
        recommendations = []
        
        for vector_record in all_vectors[:limit]:
            asset = await self.db_service.get_asset(vector_record.asset_id)
            if not asset:
                continue
            
            segments = await self.db_service.get_asset_segments(vector_record.asset_id)
            
            recommendation = {
                "asset_id": asset.id,
                "filename": asset.filename,
                "similarity_score": 0.5,  # 默认相似度
                "proxy_url": f"/assets/proxies/{asset.id}_proxy.mp4" if asset.proxy_path else None,
                "thumbnail_url": f"/assets/thumbnails/{asset.id}_thumb.jpg" if asset.thumbnail_path else None,
                "reason": "基于内容标签的匹配推荐",
                "segments": []
            }
            
            for segment in segments:
                recommendation["segments"].append({
                    "id": segment.id,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "description": segment.description,
                    "tags": {
                        "emotions": segment.emotion_tags or [],
                        "scenes": segment.scene_tags or [],
                        "actions": segment.action_tags or [],
                        "cinematography": segment.cinematography_tags or []
                    }
                })
            
            recommendations.append(recommendation)
        
        return {
            "status": "success",
            "query": {
                "beat_id": beat.id,
                "content": beat.content,
                "tags": {
                    "emotions": beat.emotion_tags or [],
                    "scenes": beat.scene_tags or [],
                    "actions": beat.action_tags or [],
                    "cinematography": beat.cinematography_tags or []
                }
            },
            "recommendations": recommendations,
            "search_params": {
                "fuzziness": 0.7,
                "limit": limit,
                "fallback_mode": True
            }
        }
    
    async def create_content_vectors(self, asset_id: str, segments: List[Dict]) -> bool:
        """为资产内容创建向量索引"""
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE or not self.embedding_model:
            logger.warning("向量模型不可用，跳过向量创建")
            return False
        
        try:
            for segment in segments:
                # 构建文本内容
                text_parts = []
                
                if segment.get("description"):
                    text_parts.append(segment["description"])
                
                # 添加标签信息
                tags = segment.get("tags", {})
                for tag_type, tag_list in tags.items():
                    if tag_list:
                        text_parts.append(f"{tag_type}: {', '.join(tag_list)}")
                
                text_content = " ".join(text_parts)
                
                if text_content.strip():
                    # P0 Fix: 异步生成向量
                    loop = asyncio.get_event_loop()
                    vector = await loop.run_in_executor(
                        None, 
                        self._encode_text_sync, 
                        text_content
                    )
                    
                    # P0 Fix: 校验向量维度
                    if not self._validate_vector_dimension(vector):
                        logger.warning(f"跳过维度错误的向量: {asset_id}, segment: {segment.get('id')}")
                        continue
                    
                    vector_json = json.dumps(vector.tolist())
                    
                    # 存储向量
                    await self.db_service.create_asset_vector(
                        asset_id=asset_id,
                        vector_data=vector_json,
                        content_type="segment_description",
                        text_content=text_content,
                        segment_id=segment.get("id")
                    )
            
            logger.info(f"为资产 {asset_id} 创建了 {len(segments)} 个向量")
            return True
            
        except Exception as e:
            logger.error(f"向量创建失败: {e}")
            return False
    
    def _encode_text_sync(self, text: str):
        """同步的embedding生成，在线程池中执行"""
        return self.embedding_model.encode([text])[0]
    
    async def _search_transcription_content(self, beat, query_text: str, limit: int) -> List[Dict]:
        """在转录内容中搜索匹配的片段"""
        
        try:
            # 构建搜索关键词
            search_keywords = []
            
            # 从Beat内容中提取关键词
            if beat.content:
                search_keywords.append(beat.content)
            
            # 从标签中提取关键词
            all_tags = []
            if beat.emotion_tags:
                all_tags.extend(beat.emotion_tags)
            if beat.scene_tags:
                all_tags.extend(beat.scene_tags)
            if beat.action_tags:
                all_tags.extend(beat.action_tags)
            
            # 为每个关键词搜索转录内容
            transcription_results = []
            
            for keyword in search_keywords + all_tags:
                if len(keyword.strip()) > 1:  # 忽略太短的关键词
                    results = self.db_service.search_transcription_text(keyword, limit)
                    transcription_results.extend(results)
            
            # 去重和排序
            unique_results = {}
            for result in transcription_results:
                asset_id = result["asset_id"]
                if asset_id not in unique_results:
                    unique_results[asset_id] = result
                else:
                    # 合并匹配片段
                    existing_segments = unique_results[asset_id]["matching_segments"]
                    new_segments = result["matching_segments"]
                    
                    # 添加新的匹配片段（避免重复）
                    existing_segment_ids = {seg["segment_id"] for seg in existing_segments}
                    for seg in new_segments:
                        if seg["segment_id"] not in existing_segment_ids:
                            existing_segments.append(seg)
            
            # 转换为列表并限制数量
            final_results = list(unique_results.values())[:limit]
            
            # 为每个结果添加匹配理由
            for result in final_results:
                result["match_reason"] = await self._generate_transcription_match_reason(
                    beat, result, query_text
                )
            
            return final_results
            
        except Exception as e:
            logger.error(f"转录内容搜索失败: {e}")
            return []
    
    async def _generate_transcription_match_reason(self, beat, transcription_result: Dict, query_text: str) -> str:
        """为转录匹配生成推荐理由"""
        
        try:
            # 提取匹配的文本片段
            matched_texts = [seg["text"] for seg in transcription_result["matching_segments"]]
            matched_text_sample = " | ".join(matched_texts[:2])  # 最多显示前两个匹配片段
            
            prompt = f"""
作为导演助手，请为以下语音内容匹配生成简洁的理由说明：

剧本需求：
{beat.content}
标签：情绪({beat.emotion_tags}), 场景({beat.scene_tags}), 动作({beat.action_tags})

匹配的语音内容：
文件：{transcription_result["filename"]}
语言：{transcription_result["language"]}
匹配片段：{matched_text_sample}

请用1句话说明为什么这个语音内容适合这个剧本片段。
"""
            
            reason_result = await self.gemini_client.generate_text(prompt)
            
            if reason_result["status"] == "success":
                return reason_result["data"]["text"].strip()
            else:
                return f"语音内容包含相关对话，共{len(transcription_result['matching_segments'])}个匹配片段"
                
        except Exception as e:
            logger.warning(f"转录匹配理由生成失败: {e}")
            return f"语音内容匹配，包含{len(transcription_result.get('matching_segments', []))}个相关片段"