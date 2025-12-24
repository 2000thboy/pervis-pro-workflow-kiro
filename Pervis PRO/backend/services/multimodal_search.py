"""
多模态搜索引擎
Phase 4: 融合文本、音频、视觉的综合搜索
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from services.database_service import DatabaseService
from services.semantic_search import SemanticSearchEngine
from services.gemini_client import GeminiClient
import logging

logger = logging.getLogger(__name__)

class MultimodalSearchEngine:
    
    def __init__(self, db: Session):
        self.db = db
        self.db_service = DatabaseService(db)
        self.semantic_search = SemanticSearchEngine(db)
        self.gemini_client = GeminiClient()
    
    async def multimodal_search(self, 
                               query: str,
                               beat_id: str = None,
                               search_modes: List[str] = None,
                               weights: Dict[str, float] = None,
                               fuzziness: float = 0.7,
                               limit: int = 10) -> Dict[str, Any]:
        """
        多模态综合搜索
        
        Args:
            query: 搜索查询文本
            beat_id: Beat ID (可选)
            search_modes: 搜索模式列表 ['semantic', 'transcription', 'visual']
            weights: 各模态权重 {'semantic': 0.4, 'transcription': 0.3, 'visual': 0.3}
            fuzziness: 模糊度
            limit: 结果数量限制
        """
        
        try:
            # 默认搜索模式和权重
            if search_modes is None:
                search_modes = ['semantic', 'transcription', 'visual']
            
            if weights is None:
                weights = {
                    'semantic': 0.4,
                    'transcription': 0.3,
                    'visual': 0.3
                }
            
            logger.info(f"开始多模态搜索: {query}, 模式: {search_modes}")
            
            # 解析查询意图
            query_intent = await self._parse_query_intent(query)
            
            # 并行执行各模态搜索
            search_results = {}
            
            if 'semantic' in search_modes:
                semantic_results = await self._search_semantic_content(
                    query, beat_id, fuzziness, limit
                )
                search_results['semantic'] = semantic_results
            
            if 'transcription' in search_modes:
                transcription_results = await self._search_transcription_content(
                    query, limit
                )
                search_results['transcription'] = transcription_results
            
            if 'visual' in search_modes:
                visual_results = await self._search_visual_content(
                    query, query_intent, limit
                )
                search_results['visual'] = visual_results
            
            # 融合搜索结果
            fused_results = await self._fuse_search_results(
                search_results, weights, query_intent, limit
            )
            
            # 生成综合推荐理由
            for result in fused_results:
                result["multimodal_reason"] = await self._generate_multimodal_reason(
                    result, query, query_intent
                )
            
            return {
                "status": "success",
                "query": query,
                "query_intent": query_intent,
                "search_modes": search_modes,
                "weights": weights,
                "results": fused_results,
                "total_matches": len(fused_results),
                "individual_results": {
                    mode: len(results) for mode, results in search_results.items()
                }
            }
            
        except Exception as e:
            logger.error(f"多模态搜索失败: {e}")
            return {
                "status": "error",
                "message": f"搜索失败: {str(e)}"
            }
    
    async def _parse_query_intent(self, query: str) -> Dict[str, Any]:
        """解析查询意图"""
        
        try:
            # 使用AI解析查询意图
            prompt = f"""
分析以下搜索查询的意图，提取关键信息：

查询: "{query}"

请分析并返回JSON格式的结果，包含：
1. primary_intent: 主要意图 (visual/audio/semantic/mixed)
2. visual_keywords: 视觉相关关键词
3. audio_keywords: 音频相关关键词  
4. emotion_keywords: 情绪相关关键词
5. scene_keywords: 场景相关关键词
6. action_keywords: 动作相关关键词
7. technical_keywords: 技术相关关键词 (镜头、光线等)

示例输出:
{{
  "primary_intent": "visual",
  "visual_keywords": ["蓝色", "夜景", "城市"],
  "audio_keywords": [],
  "emotion_keywords": ["紧张"],
  "scene_keywords": ["城市", "夜晚"],
  "action_keywords": ["追逐"],
  "technical_keywords": ["手持摄影"]
}}
"""
            
            result = await self.gemini_client.generate_text(prompt)
            
            if result["status"] == "success":
                try:
                    intent_data = json.loads(result["data"]["text"])
                    return intent_data
                except json.JSONDecodeError:
                    pass
            
            # 降级到简单关键词提取
            return self._simple_intent_extraction(query)
            
        except Exception as e:
            logger.warning(f"查询意图解析失败: {e}")
            return self._simple_intent_extraction(query)
    
    def _simple_intent_extraction(self, query: str) -> Dict[str, Any]:
        """简单的意图提取"""
        
        # 预定义关键词
        visual_keywords = ['蓝色', '红色', '绿色', '明亮', '昏暗', '夜景', '白天', '特写', '远景', '构图']
        audio_keywords = ['音乐', '对话', '声音', '安静', '嘈杂', '背景音', '音效']
        emotion_keywords = ['快乐', '悲伤', '紧张', '兴奋', '平静', '愤怒', '恐惧', '温馨']
        scene_keywords = ['室内', '室外', '城市', '乡村', '海边', '山区', '办公室', '家庭']
        action_keywords = ['跑步', '走路', '说话', '战斗', '拥抱', '工作', '睡觉', '追逐']
        technical_keywords = ['手持', '稳定', '推拉', '摇摆', '俯拍', '仰拍', '慢镜头']
        
        query_lower = query.lower()
        
        # 提取匹配的关键词
        visual_matches = [kw for kw in visual_keywords if kw in query_lower]
        audio_matches = [kw for kw in audio_keywords if kw in query_lower]
        emotion_matches = [kw for kw in emotion_keywords if kw in query_lower]
        scene_matches = [kw for kw in scene_keywords if kw in query_lower]
        action_matches = [kw for kw in action_keywords if kw in query_lower]
        technical_matches = [kw for kw in technical_keywords if kw in query_lower]
        
        # 确定主要意图
        intent_scores = {
            'visual': len(visual_matches) + len(technical_matches),
            'audio': len(audio_matches),
            'semantic': len(emotion_matches) + len(scene_matches) + len(action_matches),
            'mixed': 0
        }
        
        primary_intent = max(intent_scores, key=intent_scores.get)
        if sum(intent_scores.values()) > 3:
            primary_intent = 'mixed'
        
        return {
            "primary_intent": primary_intent,
            "visual_keywords": visual_matches,
            "audio_keywords": audio_matches,
            "emotion_keywords": emotion_matches,
            "scene_keywords": scene_matches,
            "action_keywords": action_matches,
            "technical_keywords": technical_matches
        }
    
    async def _search_semantic_content(self, query: str, beat_id: str, fuzziness: float, limit: int) -> List[Dict]:
        """搜索语义内容"""
        
        try:
            if beat_id:
                # 使用现有的Beat搜索
                result = await self.semantic_search.search_by_beat(
                    beat_id, fuzziness, limit, include_transcription=False
                )
                return result.get("recommendations", [])
            else:
                # 创建临时Beat进行搜索
                temp_beat_data = {
                    "content": query,
                    "emotion_tags": [],
                    "scene_tags": [],
                    "action_tags": [],
                    "cinematography_tags": []
                }
                
                # 简化的语义搜索
                return await self._simple_semantic_search(query, limit)
                
        except Exception as e:
            logger.warning(f"语义搜索失败: {e}")
            return []
    
    async def _simple_semantic_search(self, query: str, limit: int) -> List[Dict]:
        """简化的语义搜索"""
        
        # 获取所有向量记录进行简单匹配
        all_vectors = self.db_service.search_vectors_by_similarity("", limit * 2)
        
        results = []
        for vector_record in all_vectors[:limit]:
            asset = self.db_service.get_asset(vector_record.asset_id)
            if asset:
                results.append({
                    "asset_id": asset.id,
                    "filename": asset.filename,
                    "similarity_score": 0.5,
                    "match_type": "semantic",
                    "proxy_url": f"/assets/proxies/{asset.id}_proxy.mp4" if asset.proxy_path else None,
                    "thumbnail_url": f"/assets/thumbnails/{asset.id}_thumb.jpg" if asset.thumbnail_path else None
                })
        
        return results
    
    async def _search_transcription_content(self, query: str, limit: int) -> List[Dict]:
        """搜索转录内容"""
        
        try:
            results = self.db_service.search_transcription_text(query, limit)
            
            # 转换格式
            transcription_results = []
            for result in results:
                transcription_results.append({
                    "asset_id": result["asset_id"],
                    "filename": result["filename"],
                    "match_type": "transcription",
                    "language": result["language"],
                    "matching_segments": result["matching_segments"],
                    "transcription_score": len(result["matching_segments"]) / 10.0  # 简单评分
                })
            
            return transcription_results
            
        except Exception as e:
            logger.warning(f"转录搜索失败: {e}")
            return []
    
    async def _search_visual_content(self, query: str, query_intent: Dict, limit: int) -> List[Dict]:
        """搜索视觉内容（包括视频和图片）"""
        
        try:
            visual_results = []
            
            # 搜索视频视觉特征
            try:
                # 构建视觉查询标签
                visual_query_tags = {}
                
                # 从意图中提取视觉相关标签
                if query_intent.get("visual_keywords"):
                    # 简单的关键词到标签映射
                    for keyword in query_intent["visual_keywords"]:
                        if keyword in ['明亮', '昏暗']:
                            visual_query_tags["brightness_level"] = keyword
                        elif keyword in ['蓝色', '冷色']:
                            visual_query_tags["color_tone"] = "cool"
                        elif keyword in ['红色', '暖色']:
                            visual_query_tags["color_tone"] = "warm"
                
                if query_intent.get("technical_keywords"):
                    for keyword in query_intent["technical_keywords"]:
                        if keyword in ['特写', '远景']:
                            visual_query_tags["shot_type"] = keyword
                
                # 执行视频视觉搜索
                video_results = self.db_service.search_visual_features(visual_query_tags, limit // 2)
                
                # 转换格式
                for result in video_results:
                    visual_results.append({
                        "asset_id": result["asset_id"],
                        "filename": result["filename"],
                        "match_type": "visual_video",
                        "visual_summary": result["visual_summary"],
                        "keyframes_count": result["keyframes_count"],
                        "visual_score": 0.6  # 简单评分
                    })
            except Exception as e:
                logger.warning(f"视频视觉搜索失败: {e}")
            
            # 搜索图片内容
            try:
                # 调用图片搜索API
                import requests
                
                image_search_data = {
                    "query": query,
                    "project_id": "default",  # 可以从上下文获取
                    "limit": limit // 2,
                    "similarity_threshold": 0.3
                }
                
                # 这里应该直接调用图片搜索服务，而不是HTTP请求
                # 为了避免循环依赖，我们直接使用数据库查询
                from database import ImageAsset
                
                # 简单的图片搜索（基于文件名和描述）
                image_assets = self.db.query(ImageAsset).filter(
                    ImageAsset.processing_status == 'completed'
                ).limit(limit // 2).all()
                
                for asset in image_assets:
                    # 简单的相关性评分
                    relevance_score = 0.5
                    if asset.description:
                        # 简单的文本匹配
                        query_words = query.lower().split()
                        desc_words = asset.description.lower().split()
                        matches = len(set(query_words) & set(desc_words))
                        relevance_score = min(0.9, 0.3 + matches * 0.1)
                    
                    visual_results.append({
                        "asset_id": asset.id,
                        "filename": asset.filename,
                        "match_type": "visual_image",
                        "description": asset.description,
                        "tags": asset.tags,
                        "color_palette": asset.color_palette,
                        "visual_score": relevance_score,
                        "thumbnail_url": asset.thumbnail_path,
                        "original_url": asset.original_path
                    })
                    
            except Exception as e:
                logger.warning(f"图片视觉搜索失败: {e}")
            
            return visual_results
            
        except Exception as e:
            logger.warning(f"视觉搜索失败: {e}")
            return []
    
    async def _fuse_search_results(self, search_results: Dict[str, List], 
                                 weights: Dict[str, float], 
                                 query_intent: Dict, 
                                 limit: int) -> List[Dict]:
        """融合多模态搜索结果"""
        
        try:
            # 收集所有资产ID
            all_assets = {}
            
            # 处理语义搜索结果
            for result in search_results.get('semantic', []):
                asset_id = result["asset_id"]
                if asset_id not in all_assets:
                    all_assets[asset_id] = {
                        "asset_id": asset_id,
                        "filename": result["filename"],
                        "proxy_url": result.get("proxy_url"),
                        "thumbnail_url": result.get("thumbnail_url"),
                        "scores": {},
                        "match_details": {}
                    }
                
                all_assets[asset_id]["scores"]["semantic"] = result.get("similarity_score", 0.5)
                all_assets[asset_id]["match_details"]["semantic"] = {
                    "type": "semantic",
                    "score": result.get("similarity_score", 0.5)
                }
            
            # 处理转录搜索结果
            for result in search_results.get('transcription', []):
                asset_id = result["asset_id"]
                if asset_id not in all_assets:
                    all_assets[asset_id] = {
                        "asset_id": asset_id,
                        "filename": result["filename"],
                        "scores": {},
                        "match_details": {}
                    }
                
                all_assets[asset_id]["scores"]["transcription"] = result.get("transcription_score", 0.5)
                all_assets[asset_id]["match_details"]["transcription"] = {
                    "type": "transcription",
                    "language": result.get("language"),
                    "matching_segments": result.get("matching_segments", []),
                    "score": result.get("transcription_score", 0.5)
                }
            
            # 处理视觉搜索结果
            for result in search_results.get('visual', []):
                asset_id = result["asset_id"]
                if asset_id not in all_assets:
                    all_assets[asset_id] = {
                        "asset_id": asset_id,
                        "filename": result["filename"],
                        "scores": {},
                        "match_details": {}
                    }
                
                all_assets[asset_id]["scores"]["visual"] = result.get("visual_score", 0.5)
                all_assets[asset_id]["match_details"]["visual"] = {
                    "type": "visual",
                    "visual_summary": result.get("visual_summary", {}),
                    "score": result.get("visual_score", 0.5)
                }
            
            # 计算综合评分
            fused_results = []
            for asset_id, asset_data in all_assets.items():
                scores = asset_data["scores"]
                
                # 加权平均
                total_score = 0
                total_weight = 0
                
                for mode, weight in weights.items():
                    if mode in scores:
                        total_score += scores[mode] * weight
                        total_weight += weight
                
                if total_weight > 0:
                    final_score = total_score / total_weight
                else:
                    final_score = 0.1
                
                asset_data["final_score"] = final_score
                asset_data["match_modes"] = list(scores.keys())
                
                fused_results.append(asset_data)
            
            # 按综合评分排序
            fused_results.sort(key=lambda x: x["final_score"], reverse=True)
            
            return fused_results[:limit]
            
        except Exception as e:
            logger.error(f"结果融合失败: {e}")
            return []
    
    async def _generate_multimodal_reason(self, result: Dict, query: str, query_intent: Dict) -> str:
        """生成多模态推荐理由"""
        
        try:
            match_modes = result.get("match_modes", [])
            match_details = result.get("match_details", {})
            
            reason_parts = []
            
            # 语义匹配理由
            if "semantic" in match_modes:
                semantic_score = match_details.get("semantic", {}).get("score", 0)
                reason_parts.append(f"语义匹配度{semantic_score:.1%}")
            
            # 转录匹配理由
            if "transcription" in match_modes:
                transcription_detail = match_details.get("transcription", {})
                segments_count = len(transcription_detail.get("matching_segments", []))
                if segments_count > 0:
                    reason_parts.append(f"包含{segments_count}个相关语音片段")
            
            # 视觉匹配理由
            if "visual" in match_modes:
                visual_detail = match_details.get("visual", {})
                visual_summary = visual_detail.get("visual_summary", {})
                if visual_summary:
                    visual_features = []
                    if visual_summary.get("color_tone"):
                        visual_features.append(f"{visual_summary['color_tone']}色调")
                    if visual_summary.get("brightness_level"):
                        visual_features.append(f"{visual_summary['brightness_level']}亮度")
                    
                    if visual_features:
                        reason_parts.append(f"视觉特征匹配: {', '.join(visual_features)}")
            
            if reason_parts:
                return f"多模态匹配: {'; '.join(reason_parts)}"
            else:
                return f"综合匹配度{result.get('final_score', 0):.1%}"
                
        except Exception as e:
            logger.warning(f"多模态理由生成失败: {e}")
            return f"多模态综合推荐 (评分: {result.get('final_score', 0):.1%})"