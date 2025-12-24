"""
图片素材处理服务实现示例
解决故事板中图片素材缺失的问题
"""

import os
import json
from PIL import Image, ImageStat
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import asyncio
from services.gemini_client import GeminiClient

class ImageAssetProcessor:
    """图片素材处理器 - 解决故事板素材匹配问题的核心组件"""
    
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        self.thumbnails_dir = self.storage_root / "thumbnails"
        self.gemini_client = GeminiClient()
        
        # 确保目录存在
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_image_for_storyboard(self, image_path: str, beat_context: Dict = None) -> Dict:
        """
        为故事板处理图片素材
        这是解决素材匹配问题的关键方法
        """
        
        try:
            image_path = Path(image_path)
            
            # 1. 基本信息提取
            basic_info = self._extract_basic_info(image_path)
            
            # 2. 生成缩略图（多尺寸）
            thumbnails = await self._generate_thumbnails(image_path)
            
            # 3. 视觉特征分析
            visual_features = self._analyze_visual_features(image_path)
            
            # 4. AI标签生成（针对故事板需求）
            ai_tags = await self._generate_storyboard_tags(image_path, beat_context)
            
            # 5. 创建搜索向量
            search_vector = await self._create_search_vector(image_path, ai_tags)
            
            return {
                "status": "success",
                "basic_info": basic_info,
                "thumbnails": thumbnails,
                "visual_features": visual_features,
                "ai_tags": ai_tags,
                "search_vector": search_vector,
                "storyboard_ready": True
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"图片处理失败: {str(e)}"
            }
    
    def _extract_basic_info(self, image_path: Path) -> Dict:
        """提取图片基本信息"""
        
        with Image.open(image_path) as img:
            return {
                "filename": image_path.name,
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "file_size": image_path.stat().st_size,
                "aspect_ratio": img.size[0] / img.size[1]
            }
    
    async def _generate_thumbnails(self, image_path: Path) -> Dict[str, str]:
        """生成多尺寸缩略图"""
        
        thumbnails = {}
        sizes = {
            "small": (150, 150),
            "medium": (300, 300), 
            "large": (600, 600),
            "storyboard": (400, 225)  # 16:9 比例，适合故事板
        }
        
        with Image.open(image_path) as img:
            for size_name, (width, height) in sizes.items():
                # 保持宽高比的缩放
                img_copy = img.copy()
                img_copy.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                # 创建固定尺寸的画布（用于故事板统一显示）
                if size_name == "storyboard":
                    canvas = Image.new('RGB', (width, height), (0, 0, 0))
                    # 居中放置
                    x = (width - img_copy.width) // 2
                    y = (height - img_copy.height) // 2
                    canvas.paste(img_copy, (x, y))
                    img_copy = canvas
                
                # 保存缩略图
                thumb_filename = f"{image_path.stem}_{size_name}.jpg"
                thumb_path = self.thumbnails_dir / thumb_filename
                img_copy.save(thumb_path, "JPEG", quality=85)
                
                thumbnails[size_name] = str(thumb_path)
        
        return thumbnails
    
    def _analyze_visual_features(self, image_path: Path) -> Dict:
        """分析视觉特征 - 用于故事板匹配"""
        
        with Image.open(image_path) as img:
            # 转换为RGB模式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 1. 主色调分析
            dominant_colors = self._extract_dominant_colors(img)
            
            # 2. 亮度和对比度
            stat = ImageStat.Stat(img)
            brightness = sum(stat.mean) / len(stat.mean)
            
            # 3. 构图分析
            composition = self._analyze_composition(img)
            
            # 4. 色彩情绪分析
            color_mood = self._analyze_color_mood(dominant_colors)
            
            return {
                "dominant_colors": dominant_colors,
                "brightness": brightness,
                "composition": composition,
                "color_mood": color_mood,
                "visual_style": self._determine_visual_style(img, dominant_colors, brightness)
            }
    
    def _extract_dominant_colors(self, img: Image.Image, num_colors: int = 5) -> List[Dict]:
        """提取主色调"""
        
        # 缩小图片以提高处理速度
        img_small = img.resize((150, 150))
        
        # 获取颜色统计
        colors = img_small.getcolors(maxcolors=256*256*256)
        if not colors:
            return []
        
        # 按出现频率排序
        colors.sort(key=lambda x: x[0], reverse=True)
        
        dominant_colors = []
        for count, color in colors[:num_colors]:
            if isinstance(color, int):  # 灰度图
                color = (color, color, color)
            
            dominant_colors.append({
                "rgb": color,
                "hex": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                "percentage": count / (img_small.width * img_small.height) * 100
            })
        
        return dominant_colors
    
    def _analyze_composition(self, img: Image.Image) -> Dict:
        """分析构图类型"""
        
        width, height = img.size
        aspect_ratio = width / height
        
        # 基本构图类型判断
        if aspect_ratio > 1.5:
            composition_type = "横向"
        elif aspect_ratio < 0.7:
            composition_type = "纵向"
        else:
            composition_type = "方形"
        
        # 简单的构图分析（可以用更复杂的算法）
        center_crop = img.crop((width//4, height//4, 3*width//4, 3*height//4))
        center_brightness = sum(ImageStat.Stat(center_crop.convert('L')).mean)
        edge_brightness = sum(ImageStat.Stat(img.convert('L')).mean) - center_brightness
        
        focus_type = "中心构图" if center_brightness > edge_brightness else "边缘构图"
        
        return {
            "type": composition_type,
            "aspect_ratio": aspect_ratio,
            "focus": focus_type
        }
    
    def _analyze_color_mood(self, dominant_colors: List[Dict]) -> Dict:
        """分析色彩情绪 - 关键的故事板匹配维度"""
        
        if not dominant_colors:
            return {"mood": "neutral", "energy": "medium"}
        
        # 基于主色调的情绪分析
        primary_color = dominant_colors[0]["rgb"]
        r, g, b = primary_color
        
        # 色相分析
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        
        if max_val == min_val:  # 灰色
            mood = "neutral"
            energy = "low"
        elif r > g and r > b:  # 红色系
            mood = "passionate" if r > 180 else "warm"
            energy = "high"
        elif g > r and g > b:  # 绿色系
            mood = "natural"
            energy = "medium"
        elif b > r and b > g:  # 蓝色系
            mood = "calm" if b > 150 else "cool"
            energy = "low"
        else:
            mood = "mixed"
            energy = "medium"
        
        # 亮度影响情绪
        brightness = (r + g + b) / 3
        if brightness > 200:
            mood += "_bright"
            energy = "high"
        elif brightness < 80:
            mood += "_dark"
            if energy == "high":
                energy = "medium"
        
        return {
            "mood": mood,
            "energy": energy,
            "warmth": "warm" if r > b else "cool"
        }
    
    def _determine_visual_style(self, img: Image.Image, colors: List[Dict], brightness: float) -> List[str]:
        """确定视觉风格标签"""
        
        styles = []
        
        # 基于亮度的风格
        if brightness > 180:
            styles.append("明亮")
        elif brightness < 80:
            styles.append("暗调")
        
        # 基于色彩饱和度的风格
        if len(colors) > 0:
            primary_rgb = colors[0]["rgb"]
            saturation = max(primary_rgb) - min(primary_rgb)
            
            if saturation > 100:
                styles.append("鲜艳")
            elif saturation < 30:
                styles.append("单调")
        
        # 基于构图的风格（简化版）
        width, height = img.size
        if width > height * 1.5:
            styles.append("电影感")
        
        return styles
    
    async def _generate_storyboard_tags(self, image_path: Path, beat_context: Dict = None) -> Dict:
        """
        生成故事板相关的AI标签
        这是解决素材匹配的关键功能
        """
        
        try:
            # 构建针对故事板的提示词
            prompt = self._build_storyboard_prompt(beat_context)
            
            # 使用Gemini Vision分析图片
            analysis = await self.gemini_client.analyze_image_for_storyboard(
                str(image_path), 
                prompt
            )
            
            # 解析和标准化标签
            tags = self._parse_and_normalize_tags(analysis)
            
            return tags
            
        except Exception as e:
            # 降级到基于文件名的标签生成
            return self._generate_fallback_tags(image_path)
    
    def _build_storyboard_prompt(self, beat_context: Dict = None) -> str:
        """构建故事板分析提示词"""
        
        base_prompt = """
        请分析这张图片，为故事板制作提供以下标签：
        
        1. 场景类型：室内/户外、城市/自然、白天/夜晚等
        2. 情绪氛围：紧张、浪漫、神秘、欢乐、悲伤、平静等
        3. 动作元素：静态、动态、追逐、对话、独白等
        4. 镜头风格：特写、中景、远景、俯视、仰视等
        5. 视觉风格：现代、复古、科幻、自然、都市等
        
        请用中文回答，每个类别提供2-3个最相关的标签。
        """
        
        if beat_context:
            base_prompt += f"\n\n故事板上下文：{beat_context.get('content', '')}"
            if beat_context.get('emotion_tags'):
                base_prompt += f"\n期望情绪：{', '.join(beat_context['emotion_tags'])}"
        
        return base_prompt
    
    def _parse_and_normalize_tags(self, analysis: str) -> Dict:
        """解析和标准化AI生成的标签"""
        
        # 这里应该有更复杂的NLP解析逻辑
        # 简化版本：基于关键词匹配
        
        tags = {
            "scene_tags": [],
            "emotion_tags": [],
            "action_tags": [],
            "cinematography_tags": [],
            "style_tags": []
        }
        
        # 场景标签映射
        scene_keywords = {
            "室内": ["室内", "房间", "屋内"],
            "户外": ["户外", "室外", "外景"],
            "城市": ["城市", "都市", "街道"],
            "自然": ["自然", "森林", "山", "海"],
            "白天": ["白天", "日间", "阳光"],
            "夜晚": ["夜晚", "夜间", "黑暗"]
        }
        
        # 情绪标签映射
        emotion_keywords = {
            "紧张": ["紧张", "焦虑", "压抑"],
            "浪漫": ["浪漫", "温馨", "甜蜜"],
            "神秘": ["神秘", "诡异", "未知"],
            "欢乐": ["欢乐", "快乐", "愉悦"],
            "悲伤": ["悲伤", "忧郁", "沉重"],
            "平静": ["平静", "宁静", "安详"]
        }
        
        # 简单的关键词匹配
        analysis_lower = analysis.lower()
        
        for tag, keywords in scene_keywords.items():
            if any(keyword in analysis_lower for keyword in keywords):
                tags["scene_tags"].append(tag)
        
        for tag, keywords in emotion_keywords.items():
            if any(keyword in analysis_lower for keyword in keywords):
                tags["emotion_tags"].append(tag)
        
        return tags
    
    def _generate_fallback_tags(self, image_path: Path) -> Dict:
        """基于文件名生成降级标签"""
        
        filename = image_path.stem.lower()
        
        tags = {
            "scene_tags": [],
            "emotion_tags": [],
            "action_tags": [],
            "cinematography_tags": [],
            "style_tags": []
        }
        
        # 基于文件名的简单标签生成
        if any(word in filename for word in ["night", "夜", "dark"]):
            tags["scene_tags"].append("夜晚")
        if any(word in filename for word in ["day", "日", "sun"]):
            tags["scene_tags"].append("白天")
        if any(word in filename for word in ["city", "城市", "street"]):
            tags["scene_tags"].append("城市")
        
        return tags
    
    async def _create_search_vector(self, image_path: Path, tags: Dict) -> Optional[List[float]]:
        """为图片创建搜索向量"""
        
        try:
            # 构建描述文本
            description_parts = []
            
            for tag_type, tag_list in tags.items():
                if tag_list:
                    description_parts.extend(tag_list)
            
            description = " ".join(description_parts)
            
            if not description:
                description = f"图片 {image_path.stem}"
            
            # 使用语义搜索引擎创建向量
            # 这里需要集成到现有的SemanticSearchEngine
            return None  # 占位符
            
        except Exception as e:
            print(f"向量创建失败: {e}")
            return None

# 使用示例
async def process_images_for_storyboard(image_directory: str, beat_context: Dict = None):
    """批量处理图片用于故事板"""
    
    processor = ImageAssetProcessor("L:/PreVis_Assets")
    image_dir = Path(image_directory)
    
    results = []
    
    for image_file in image_dir.glob("*.{jpg,jpeg,png,webp}"):
        print(f"处理图片: {image_file.name}")
        
        result = await processor.process_image_for_storyboard(
            str(image_file), 
            beat_context
        )
        
        results.append({
            "file": image_file.name,
            "result": result
        })
    
    return results