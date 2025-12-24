"""
图片搜索引擎
实现图片的语义搜索和相似度搜索
"""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import numpy as np

# 尝试导入sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, OSError) as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print(f"⚠️ sentence-transformers未安装或加载失败，将使用Mock模式: {e}")

logger = logging.getLogger(__name__)

@dataclass
class ImageSearchResult:
    """图片搜索结果"""
    id: str
    filename: str
    description: str
    thumbnail_url: str
    original_url: str
    similarity_score: float
    match_reason: str
    tags: Dict[str, List[str]]
    color_palette: Dict[str, Any]
    metadata: Dict[str, Any]

class ImageSearchEngine:
    """图片搜索引擎"""
    
    def __init__(self, db: Session, use_mock: bool = False):
        self.db = db
        self.use_mock = use_mock or not SENTENCE_TRANSFORMERS_AVAILABLE
        
        # 初始化文本编码模型
        if SENTENCE_TRANSFORMERS_AVAILABLE and not use_mock:
            try:
                self.text_encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("文本编码模型加载成功")
            except Exception as e:
                logger.warning(f"文本编码模型加载失败: {e}，使用Mock模式")
                self.use_mock = True
                self.text_encoder = None
        else:
            self.text_encoder = None
        
        if self.use_mock:
            logger.info("图片搜索引擎运行在Mock模式")
    
    async def search_by_text(self, query: str, project_id: str, limit: int = 10, 
                           similarity_threshold: float = 0.3) -> List[ImageSearchResult]:
        """基于文本查询搜索图片"""
        try:
            if self.use_mock:
                return await self._mock_search_by_text(query, project_id, limit)
            
            logger.info(f"开始文本搜索: '{query}' (项目: {project_id})")
            
            # 1. 将查询文本向量化
            query_vector = await self._encode_text(query)
            if query_vector is None:
                return []
            
            # 2. 从数据库获取图片和向量数据
            images_with_vectors = await self._get_images_with_vectors(project_id)
            
            # 3. 计算相似度并排序
            results = []
            for image_data in images_with_vectors:
                # 计算与描述向量的相似度
                desc_similarity = 0.0
                if image_data.get('description_vector'):
                    desc_similarity = self._calculate_cosine_similarity(
                        query_vector, image_data['description_vector']
                    )
                
                # 计算与CLIP向量的相似度（如果有）
                clip_similarity = 0.0
                if image_data.get('clip_vector'):
                    # 需要将查询文本也用CLIP编码，这里简化处理
                    clip_similarity = desc_similarity * 0.8  # 简化计算
                
                # 综合相似度
                final_similarity = max(desc_similarity, clip_similarity)
                
                if final_similarity >= similarity_threshold:
                    # 生成匹配理由
                    match_reason = await self._generate_match_reason(query, image_data, final_similarity)
                    
                    result = ImageSearchResult(
                        id=image_data['id'],
                        filename=image_data['filename'],
                        description=image_data['description'] or '',
                        thumbnail_url=image_data['thumbnail_path'] or '',
                        original_url=image_data['original_path'],
                        similarity_score=final_similarity,
                        match_reason=match_reason,
                        tags=image_data['tags'] or {},
                        color_palette=image_data['color_palette'] or {},
                        metadata=image_data['metadata'] or {}
                    )
                    results.append(result)
            
            # 4. 按相似度排序并限制结果数量
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            results = results[:limit]
            
            logger.info(f"文本搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"文本搜索失败: {e}")
            return []
    
    async def search_by_image(self, reference_image_path: str, project_id: str, 
                            limit: int = 10, similarity_threshold: float = 0.5) -> List[ImageSearchResult]:
        """基于图片搜索相似图片"""
        try:
            if self.use_mock:
                return await self._mock_search_by_image(reference_image_path, project_id, limit)
            
            logger.info(f"开始图片相似搜索 (项目: {project_id})")
            
            # 1. 提取参考图片的CLIP向量
            from .image_analyzer import ImageAnalyzer
            analyzer = ImageAnalyzer(use_mock=self.use_mock)
            reference_vector = await analyzer.generate_clip_vector(reference_image_path)
            
            if not reference_vector:
                logger.warning("无法提取参考图片的特征向量")
                return []
            
            # 2. 从数据库获取所有图片的CLIP向量
            images_with_vectors = await self._get_images_with_vectors(project_id)
            
            # 3. 计算相似度
            results = []
            for image_data in images_with_vectors:
                if image_data.get('clip_vector'):
                    similarity = self._calculate_cosine_similarity(
                        reference_vector, image_data['clip_vector']
                    )
                    
                    if similarity >= similarity_threshold:
                        match_reason = f"视觉特征相似度: {similarity:.2f}"
                        
                        result = ImageSearchResult(
                            id=image_data['id'],
                            filename=image_data['filename'],
                            description=image_data['description'] or '',
                            thumbnail_url=image_data['thumbnail_path'] or '',
                            original_url=image_data['original_path'],
                            similarity_score=similarity,
                            match_reason=match_reason,
                            tags=image_data['tags'] or {},
                            color_palette=image_data['color_palette'] or {},
                            metadata=image_data['metadata'] or {}
                        )
                        results.append(result)
            
            # 4. 排序并限制结果
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            results = results[:limit]
            
            logger.info(f"图片相似搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"图片相似搜索失败: {e}")
            return []
    
    async def search_by_tags(self, tags: List[str], project_id: str, 
                           match_mode: str = 'any', limit: int = 10) -> List[ImageSearchResult]:
        """基于标签搜索图片"""
        try:
            if self.use_mock:
                return await self._mock_search_by_tags(tags, project_id, limit)
            
            logger.info(f"开始标签搜索: {tags} (模式: {match_mode}, 项目: {project_id})")
            
            # 从数据库查询包含指定标签的图片
            from ..database import ImageAsset
            
            query = self.db.query(ImageAsset).filter(ImageAsset.project_id == project_id)
            
            # 构建标签过滤条件
            tag_conditions = []
            for tag in tags:
                # 在JSON字段中搜索标签
                tag_condition = or_(
                    func.json_extract(ImageAsset.tags, '$.objects').like(f'%{tag}%'),
                    func.json_extract(ImageAsset.tags, '$.scenes').like(f'%{tag}%'),
                    func.json_extract(ImageAsset.tags, '$.emotions').like(f'%{tag}%'),
                    func.json_extract(ImageAsset.tags, '$.styles').like(f'%{tag}%'),
                    func.json_extract(ImageAsset.tags, '$.colors').like(f'%{tag}%')
                )
                tag_conditions.append(tag_condition)
            
            # 根据匹配模式组合条件
            if match_mode == 'all':
                # 必须包含所有标签
                for condition in tag_conditions:
                    query = query.filter(condition)
            else:
                # 包含任意标签
                if tag_conditions:
                    query = query.filter(or_(*tag_conditions))
            
            # 执行查询
            images = query.limit(limit).all()
            
            # 构建搜索结果
            results = []
            for image in images:
                # 计算标签匹配度
                match_score = self._calculate_tag_match_score(tags, image.tags or {})
                match_reason = f"标签匹配: {', '.join(tags)}"
                
                result = ImageSearchResult(
                    id=image.id,
                    filename=image.filename,
                    description=image.description or '',
                    thumbnail_url=image.thumbnail_path or '',
                    original_url=image.original_path,
                    similarity_score=match_score,
                    match_reason=match_reason,
                    tags=image.tags or {},
                    color_palette=image.color_palette or {},
                    metadata={
                        'width': getattr(image, 'width', 0),
                        'height': getattr(image, 'height', 0),
                        'file_size': getattr(image, 'file_size', 0)
                    }
                )
                results.append(result)
            
            # 按匹配度排序
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"标签搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"标签搜索失败: {e}")
            return []
    
    async def search_by_color(self, target_color: str, project_id: str, 
                            tolerance: float = 0.3, limit: int = 10) -> List[ImageSearchResult]:
        """基于颜色搜索图片"""
        try:
            if self.use_mock:
                return await self._mock_search_by_color(target_color, project_id, limit)
            
            logger.info(f"开始颜色搜索: {target_color} (项目: {project_id})")
            
            # 解析目标颜色
            target_rgb = self._hex_to_rgb(target_color)
            if not target_rgb:
                logger.warning(f"无效的颜色格式: {target_color}")
                return []
            
            # 从数据库获取图片数据
            from ..database import ImageAsset
            images = self.db.query(ImageAsset).filter(
                ImageAsset.project_id == project_id,
                ImageAsset.color_palette.isnot(None)
            ).all()
            
            results = []
            for image in images:
                color_palette = image.color_palette or {}
                
                # 检查主色调
                dominant_color = color_palette.get('dominant')
                if dominant_color:
                    dominant_rgb = self._hex_to_rgb(dominant_color)
                    if dominant_rgb:
                        color_distance = self._calculate_color_distance(target_rgb, dominant_rgb)
                        similarity = max(0, 1 - color_distance / 255)  # 归一化到0-1
                        
                        if similarity >= (1 - tolerance):
                            match_reason = f"主色调匹配: {dominant_color} (相似度: {similarity:.2f})"
                            
                            result = ImageSearchResult(
                                id=image.id,
                                filename=image.filename,
                                description=image.description or '',
                                thumbnail_url=image.thumbnail_path or '',
                                original_url=image.original_path,
                                similarity_score=similarity,
                                match_reason=match_reason,
                                tags=image.tags or {},
                                color_palette=image.color_palette or {},
                                metadata={
                                    'width': getattr(image, 'width', 0),
                                    'height': getattr(image, 'height', 0),
                                    'file_size': getattr(image, 'file_size', 0)
                                }
                            )
                            results.append(result)
            
            # 排序并限制结果
            results.sort(key=lambda x: x.similarity_score, reverse=True)
            results = results[:limit]
            
            logger.info(f"颜色搜索完成，找到 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"颜色搜索失败: {e}")
            return []
    
    async def _encode_text(self, text: str) -> Optional[List[float]]:
        """将文本编码为向量"""
        try:
            if self.use_mock or not self.text_encoder:
                # Mock向量
                return list(np.random.rand(384).astype(float))
            
            # 使用sentence-transformers编码
            embedding = self.text_encoder.encode(text)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            return None
    
    async def _get_images_with_vectors(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目中的图片及其向量数据"""
        try:
            from ..database import ImageAsset, ImageVector
            
            # 查询图片和向量数据
            query = self.db.query(ImageAsset).filter(
                ImageAsset.project_id == project_id,
                ImageAsset.processing_status == 'completed'
            )
            
            images = query.all()
            results = []
            
            for image in images:
                # 获取向量数据
                vectors = self.db.query(ImageVector).filter(
                    ImageVector.image_id == image.id
                ).all()
                
                # 解析向量数据
                description_vector = None
                clip_vector = None
                
                for vector in vectors:
                    try:
                        vector_data = json.loads(vector.vector_data)
                        if vector.vector_type == 'description':
                            description_vector = vector_data
                        elif vector.vector_type == 'clip':
                            clip_vector = vector_data
                    except json.JSONDecodeError:
                        continue
                
                image_data = {
                    'id': image.id,
                    'filename': image.filename,
                    'description': image.description,
                    'thumbnail_path': image.thumbnail_path,
                    'original_path': image.original_path,
                    'tags': image.tags,
                    'color_palette': image.color_palette,
                    'description_vector': description_vector,
                    'clip_vector': clip_vector,
                    'metadata': {
                        'width': getattr(image, 'width', 0),
                        'height': getattr(image, 'height', 0),
                        'file_size': getattr(image, 'file_size', 0)
                    }
                }
                results.append(image_data)
            
            return results
            
        except Exception as e:
            logger.error(f"获取图片向量数据失败: {e}")
            return []
    
    def _calculate_cosine_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """计算余弦相似度"""
        try:
            if not vector1 or not vector2 or len(vector1) != len(vector2):
                return 0.0
            
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            return float(max(0, min(1, similarity)))  # 限制在0-1范围
            
        except Exception as e:
            logger.error(f"计算余弦相似度失败: {e}")
            return 0.0
    
    def _calculate_tag_match_score(self, query_tags: List[str], image_tags: Dict[str, List[str]]) -> float:
        """计算标签匹配分数"""
        try:
            if not query_tags or not image_tags:
                return 0.0
            
            # 将所有图片标签合并为一个列表
            all_image_tags = []
            for tag_list in image_tags.values():
                if isinstance(tag_list, list):
                    all_image_tags.extend([tag.lower() for tag in tag_list])
            
            # 计算匹配的标签数量
            query_tags_lower = [tag.lower() for tag in query_tags]
            matched_tags = sum(1 for tag in query_tags_lower if tag in all_image_tags)
            
            # 计算匹配分数
            match_score = matched_tags / len(query_tags) if query_tags else 0.0
            return match_score
            
        except Exception as e:
            logger.error(f"计算标签匹配分数失败: {e}")
            return 0.0
    
    def _hex_to_rgb(self, hex_color: str) -> Optional[Tuple[int, int, int]]:
        """将十六进制颜色转换为RGB"""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) != 6:
                return None
            
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            return (r, g, b)
            
        except ValueError:
            return None
    
    def _calculate_color_distance(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """计算两个RGB颜色之间的欧几里得距离"""
        try:
            r1, g1, b1 = color1
            r2, g2, b2 = color2
            
            distance = ((r2 - r1) ** 2 + (g2 - g1) ** 2 + (b2 - b1) ** 2) ** 0.5
            return distance
            
        except Exception as e:
            logger.error(f"计算颜色距离失败: {e}")
            return float('inf')
    
    async def _generate_match_reason(self, query: str, image_data: Dict[str, Any], similarity: float) -> str:
        """生成匹配理由"""
        try:
            reasons = []
            
            # 基于相似度的理由
            if similarity > 0.8:
                reasons.append("高度匹配")
            elif similarity > 0.6:
                reasons.append("较好匹配")
            else:
                reasons.append("部分匹配")
            
            # 基于描述的理由
            description = image_data.get('description', '')
            if description and any(word in description for word in query.split()):
                reasons.append("描述相关")
            
            # 基于标签的理由
            tags = image_data.get('tags', {})
            if tags:
                query_words = query.lower().split()
                for tag_category, tag_list in tags.items():
                    if isinstance(tag_list, list):
                        for tag in tag_list:
                            if any(word in tag.lower() for word in query_words):
                                reasons.append(f"{tag_category}匹配")
                                break
            
            if not reasons:
                reasons.append("语义相似")
            
            return f"相似度 {similarity:.2f}: " + ", ".join(reasons[:3])
            
        except Exception as e:
            logger.error(f"生成匹配理由失败: {e}")
            return f"相似度 {similarity:.2f}"
    
    # Mock方法
    async def _mock_search_by_text(self, query: str, project_id: str, limit: int) -> List[ImageSearchResult]:
        """Mock文本搜索"""
        await asyncio.sleep(0.1)
        
        results = []
        for i in range(min(3, limit)):
            result = ImageSearchResult(
                id=f"mock_image_{i}",
                filename=f"mock_image_{i}.jpg",
                description=f"这是一张与'{query}'相关的图片",
                thumbnail_url=f"/thumbnails/mock_image_{i}_thumb.jpg",
                original_url=f"/originals/mock_image_{i}.jpg",
                similarity_score=0.9 - i * 0.1,
                match_reason=f"与查询'{query}'高度匹配",
                tags={
                    "objects": ["物体1", "物体2"],
                    "scenes": ["场景1"],
                    "emotions": ["情绪1"]
                },
                color_palette={"dominant": "#4A90E2"},
                metadata={"width": 1920, "height": 1080}
            )
            results.append(result)
        
        return results
    
    async def _mock_search_by_image(self, reference_path: str, project_id: str, limit: int) -> List[ImageSearchResult]:
        """Mock图片搜索"""
        await asyncio.sleep(0.1)
        
        results = []
        for i in range(min(2, limit)):
            result = ImageSearchResult(
                id=f"similar_image_{i}",
                filename=f"similar_image_{i}.jpg",
                description="视觉上相似的图片",
                thumbnail_url=f"/thumbnails/similar_image_{i}_thumb.jpg",
                original_url=f"/originals/similar_image_{i}.jpg",
                similarity_score=0.8 - i * 0.1,
                match_reason=f"视觉特征相似度: {0.8 - i * 0.1:.2f}",
                tags={"objects": ["相似物体"]},
                color_palette={"dominant": "#E74C3C"},
                metadata={"width": 1920, "height": 1080}
            )
            results.append(result)
        
        return results
    
    async def _mock_search_by_tags(self, tags: List[str], project_id: str, limit: int) -> List[ImageSearchResult]:
        """Mock标签搜索"""
        await asyncio.sleep(0.05)
        
        results = []
        for i, tag in enumerate(tags[:limit]):
            result = ImageSearchResult(
                id=f"tag_image_{i}",
                filename=f"tag_image_{i}.jpg",
                description=f"包含标签'{tag}'的图片",
                thumbnail_url=f"/thumbnails/tag_image_{i}_thumb.jpg",
                original_url=f"/originals/tag_image_{i}.jpg",
                similarity_score=0.9,
                match_reason=f"标签匹配: {tag}",
                tags={"objects": [tag]},
                color_palette={"dominant": "#2ECC71"},
                metadata={"width": 1920, "height": 1080}
            )
            results.append(result)
        
        return results
    
    async def _mock_search_by_color(self, color: str, project_id: str, limit: int) -> List[ImageSearchResult]:
        """Mock颜色搜索"""
        await asyncio.sleep(0.05)
        
        results = []
        for i in range(min(2, limit)):
            result = ImageSearchResult(
                id=f"color_image_{i}",
                filename=f"color_image_{i}.jpg",
                description=f"包含颜色{color}的图片",
                thumbnail_url=f"/thumbnails/color_image_{i}_thumb.jpg",
                original_url=f"/originals/color_image_{i}.jpg",
                similarity_score=0.85,
                match_reason=f"主色调匹配: {color}",
                tags={"colors": [color]},
                color_palette={"dominant": color},
                metadata={"width": 1920, "height": 1080}
            )
            results.append(result)
        
        return results

# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_search_engine():
        # 创建搜索引擎（Mock模式）
        search_engine = ImageSearchEngine(db=None, use_mock=True)
        
        # 测试文本搜索
        results = await search_engine.search_by_text("蓝色天空", "test_project", limit=5)
        
        print(f"搜索结果数量: {len(results)}")
        for result in results:
            print(f"- {result.filename}: {result.similarity_score:.2f} - {result.match_reason}")
    
    # 运行测试
    asyncio.run(test_search_engine())