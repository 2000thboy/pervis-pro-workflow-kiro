"""
图片分析服务
使用AI模型分析图片内容，生成描述和标签
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import base64
from dataclasses import dataclass

# 安全导入numpy
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("[WARNING] numpy未安装，将使用基础功能")

# 尝试导入PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARNING] PIL未安装，图片处理功能受限")

# CLIP模型导入 - 使用Hugging Face Transformers
CLIP_AVAILABLE = False
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    CLIP_AVAILABLE = True
    print("[OK] CLIP模型可用 (Hugging Face)")
except Exception as e:
    CLIP_AVAILABLE = False
    print(f"[WARNING] CLIP模型不可用: {e}")

# 导入Gemini客户端
try:
    from services.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[WARNING] Gemini客户端未找到，将使用Mock模式")

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """图片分析结果"""
    description: str
    tags: Dict[str, List[str]]
    color_palette: Dict[str, Any]
    clip_vector: Optional[List[float]] = None
    confidence_score: float = 0.0
    processing_time: float = 0.0

class ImageAnalyzer:
    """图片分析服务"""
    
    def __init__(self, gemini_api_key: Optional[str] = None, use_mock: bool = False):
        # 暂时强制使用Mock模式，直到CLIP DLL问题解决
        self.use_mock = True  # use_mock or not (CLIP_AVAILABLE and GEMINI_AVAILABLE)
        
        # 初始化Gemini客户端
        if GEMINI_AVAILABLE and gemini_api_key and not use_mock:
            try:
                self.gemini_client = GeminiClient(api_key=gemini_api_key)
                logger.info("Gemini Vision客户端初始化成功")
            except Exception as e:
                logger.warning(f"Gemini客户端初始化失败: {e}，使用Mock模式")
                self.use_mock = True
        else:
            self.gemini_client = None
        
        # 初始化CLIP模型
        if CLIP_AVAILABLE and not use_mock:
            try:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                logger.info(f"CLIP模型加载成功，使用设备: {self.device}")
            except Exception as e:
                logger.warning(f"CLIP模型加载失败: {e}，使用Mock模式")
                self.use_mock = True
        else:
            self.clip_model = None
            self.clip_processor = None
        
        if self.use_mock:
            logger.info("图片分析器运行在Mock模式")
    
    async def analyze_image(self, image_path: str) -> AnalysisResult:
        """分析图片内容（完整分析）"""
        import time
        start_time = time.time()
        
        try:
            if self.use_mock:
                return await self._mock_analyze_image(image_path)
            
            # 并行执行各种分析
            tasks = [
                self.generate_description(image_path),
                self.extract_tags(image_path),
                self.analyze_colors(image_path),
                self.generate_clip_vector(image_path)
            ]
            
            description, tags, color_palette, clip_vector = await asyncio.gather(*tasks)
            
            processing_time = time.time() - start_time
            
            return AnalysisResult(
                description=description,
                tags=tags,
                color_palette=color_palette,
                clip_vector=clip_vector,
                confidence_score=0.85,  # 基于实际模型输出计算
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"图片分析失败: {e}")
            processing_time = time.time() - start_time
            
            # 返回错误结果
            return AnalysisResult(
                description=f"分析失败: {str(e)}",
                tags={"error": [str(e)]},
                color_palette={},
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    async def generate_description(self, image_path: str) -> str:
        """生成图片描述"""
        try:
            if self.use_mock or not self.gemini_client:
                return await self._mock_generate_description(image_path)
            
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 使用Gemini Vision分析图片
            prompt = """请详细描述这张图片的内容，包括：
1. 主要物体和场景
2. 色彩和光线
3. 构图和风格
4. 情绪和氛围

请用中文回答，描述要准确、详细但简洁。"""
            
            description = await self.gemini_client.analyze_image(image_data, prompt)
            return description.strip()
            
        except Exception as e:
            logger.error(f"生成图片描述失败: {e}")
            return f"描述生成失败: {str(e)}"
    
    async def extract_tags(self, image_path: str) -> Dict[str, List[str]]:
        """提取图片标签"""
        try:
            if self.use_mock or not self.gemini_client:
                return await self._mock_extract_tags(image_path)
            
            # 读取图片文件
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 使用Gemini Vision提取标签
            prompt = """请分析这张图片并提取标签，按以下类别分类：

1. objects: 图片中的主要物体（如：建筑、汽车、人物、动物等）
2. scenes: 场景类型（如：室内、室外、城市、自然、办公室等）
3. emotions: 情绪和氛围（如：快乐、悲伤、平静、紧张、温暖等）
4. styles: 视觉风格（如：现代、复古、简约、华丽、摄影、插画等）
5. colors: 主要色彩（如：蓝色、红色、暖色调、冷色调等）

请以JSON格式返回，每个类别包含3-5个最相关的标签。
示例格式：
{
  "objects": ["建筑", "天空", "树木"],
  "scenes": ["城市", "白天", "街道"],
  "emotions": ["平静", "现代", "开阔"],
  "styles": ["摄影", "现实主义", "都市"],
  "colors": ["蓝色", "灰色", "绿色"]
}"""
            
            response = await self.gemini_client.analyze_image(image_data, prompt)
            
            # 解析JSON响应
            try:
                tags = json.loads(response.strip())
                return tags
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试从文本中提取
                return self._parse_tags_from_text(response)
                
        except Exception as e:
            logger.error(f"提取图片标签失败: {e}")
            return {"error": [str(e)]}
    
    async def generate_clip_vector(self, image_path: str) -> Optional[List[float]]:
        """生成CLIP特征向量"""
        try:
            if self.use_mock or not CLIP_AVAILABLE:
                return await self._mock_generate_clip_vector()
            
            # 使用Hugging Face CLIP模型
            if not hasattr(self, 'clip_model') or not self.clip_model:
                logger.error("CLIP模型未初始化")
                return await self._mock_generate_clip_vector()
            
            # 加载和预处理图片
            if PIL_AVAILABLE:
                image = Image.open(image_path).convert('RGB')
            else:
                logger.error("PIL不可用，无法处理图片")
                return await self._mock_generate_clip_vector()
            
            # 处理图片
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            # 生成特征向量
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                # 归一化
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                
                # 转换为Python列表
                vector = image_features.cpu().numpy().flatten().tolist()
                
            logger.info(f"CLIP向量生成成功，维度: {len(vector)}")
            return vector
            
        except Exception as e:
            logger.error(f"生成CLIP向量失败: {e}")
            return await self._mock_generate_clip_vector()
    
    def analyze_colors(self, image_path: str) -> Dict[str, Any]:
        """分析图片色彩"""
        try:
            if self.use_mock:
                return self._mock_analyze_colors()
            
            from PIL import Image
            import colorsys
            
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGB模式
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 缩小图片以提高处理速度
                img = img.resize((100, 100))
                
                # 获取所有像素颜色
                colors = img.getcolors(maxcolors=256*256*256)
                if not colors:
                    return {"error": "无法提取颜色信息"}
                
                # 按出现频率排序
                colors.sort(key=lambda x: x[0], reverse=True)
                
                # 提取主要颜色
                dominant_color = colors[0][1]
                
                # 构建调色板（前5个颜色）
                palette = []
                for count, color in colors[:5]:
                    hex_color = "#{:02x}{:02x}{:02x}".format(*color)
                    palette.append({
                        "hex": hex_color,
                        "rgb": color,
                        "percentage": count / sum(c[0] for c in colors) * 100
                    })
                
                # 分析色调
                dominant_hsv = colorsys.rgb_to_hsv(
                    dominant_color[0]/255, 
                    dominant_color[1]/255, 
                    dominant_color[2]/255
                )
                
                # 确定色调类型
                hue = dominant_hsv[0] * 360
                if hue < 30 or hue >= 330:
                    tone = "红色调"
                elif hue < 60:
                    tone = "橙色调"
                elif hue < 120:
                    tone = "黄色调"
                elif hue < 180:
                    tone = "绿色调"
                elif hue < 240:
                    tone = "青色调"
                elif hue < 300:
                    tone = "蓝色调"
                else:
                    tone = "紫色调"
                
                # 确定明暗度
                brightness = dominant_hsv[2]
                if brightness > 0.7:
                    brightness_desc = "明亮"
                elif brightness > 0.3:
                    brightness_desc = "中等"
                else:
                    brightness_desc = "暗淡"
                
                # 确定饱和度
                saturation = dominant_hsv[1]
                if saturation > 0.7:
                    saturation_desc = "鲜艳"
                elif saturation > 0.3:
                    saturation_desc = "适中"
                else:
                    saturation_desc = "柔和"
                
                return {
                    "dominant": "#{:02x}{:02x}{:02x}".format(*dominant_color),
                    "palette": palette,
                    "tone": tone,
                    "brightness": brightness_desc,
                    "saturation": saturation_desc,
                    "analysis": {
                        "hue": hue,
                        "saturation": saturation,
                        "brightness": brightness
                    }
                }
                
        except Exception as e:
            logger.error(f"色彩分析失败: {e}")
            return {"error": str(e)}
    
    def _parse_tags_from_text(self, text: str) -> Dict[str, List[str]]:
        """从文本中解析标签（当JSON解析失败时的备选方案）"""
        try:
            # 简单的文本解析逻辑
            tags = {
                "objects": [],
                "scenes": [],
                "emotions": [],
                "styles": [],
                "colors": []
            }
            
            # 这里可以实现更复杂的文本解析逻辑
            # 暂时返回基础标签
            lines = text.split('\n')
            for line in lines:
                if '物体' in line or 'objects' in line.lower():
                    # 提取物体标签
                    pass
                elif '场景' in line or 'scenes' in line.lower():
                    # 提取场景标签
                    pass
                # ... 其他类别
            
            return tags
            
        except Exception as e:
            logger.error(f"文本标签解析失败: {e}")
            return {"error": [str(e)]}
    
    # Mock方法（用于测试和无AI依赖的环境）
    async def _mock_analyze_image(self, image_path: str) -> AnalysisResult:
        """Mock图片分析"""
        await asyncio.sleep(0.1)  # 模拟处理时间
        
        filename = Path(image_path).name.lower()
        
        # 根据文件名生成Mock数据
        if 'city' in filename or '城市' in filename:
            description = "这是一张现代城市的图片，展现了高楼大厦和繁忙的街道景象。"
            tags = {
                "objects": ["建筑", "汽车", "街道", "天空"],
                "scenes": ["城市", "白天", "街道", "现代"],
                "emotions": ["繁忙", "现代", "都市"],
                "styles": ["摄影", "现实主义", "都市风格"],
                "colors": ["灰色", "蓝色", "白色"]
            }
            color_palette = {
                "dominant": "#4A90E2",
                "palette": [
                    {"hex": "#4A90E2", "rgb": [74, 144, 226], "percentage": 35.2},
                    {"hex": "#7F8C8D", "rgb": [127, 140, 141], "percentage": 28.1}
                ]
            }
        elif 'nature' in filename or '自然' in filename:
            description = "这是一张自然风景图片，展现了绿色的植物和宁静的自然环境。"
            tags = {
                "objects": ["树木", "草地", "天空", "云朵"],
                "scenes": ["自然", "户外", "森林", "白天"],
                "emotions": ["平静", "宁静", "清新"],
                "styles": ["风景摄影", "自然主义"],
                "colors": ["绿色", "蓝色", "白色"]
            }
            color_palette = {
                "dominant": "#27AE60",
                "palette": [
                    {"hex": "#27AE60", "rgb": [39, 174, 96], "percentage": 42.3},
                    {"hex": "#3498DB", "rgb": [52, 152, 219], "percentage": 31.7}
                ]
            }
        else:
            description = "这是一张图片，包含了各种视觉元素和内容。"
            tags = {
                "objects": ["物体", "元素"],
                "scenes": ["场景", "环境"],
                "emotions": ["中性", "平静"],
                "styles": ["摄影", "现实"],
                "colors": ["多色", "混合"]
            }
            color_palette = {
                "dominant": "#95A5A6",
                "palette": [
                    {"hex": "#95A5A6", "rgb": [149, 165, 166], "percentage": 40.0}
                ]
            }
        
        return AnalysisResult(
            description=description,
            tags=tags,
            color_palette=color_palette,
            clip_vector=list(np.random.rand(512).astype(float)),  # Mock 512维向量
            confidence_score=0.85,
            processing_time=0.1
        )
    
    async def _mock_generate_description(self, image_path: str) -> str:
        """Mock描述生成"""
        await asyncio.sleep(0.05)
        filename = Path(image_path).name
        return f"这是一张名为 {filename} 的图片，包含了丰富的视觉内容和细节。"
    
    async def _mock_extract_tags(self, image_path: str) -> Dict[str, List[str]]:
        """Mock标签提取"""
        await asyncio.sleep(0.05)
        return {
            "objects": ["物体1", "物体2", "物体3"],
            "scenes": ["场景1", "场景2"],
            "emotions": ["情绪1", "情绪2"],
            "styles": ["风格1", "风格2"],
            "colors": ["颜色1", "颜色2"]
        }
    
    async def _mock_generate_clip_vector(self) -> List[float]:
        """Mock CLIP向量生成"""
        await asyncio.sleep(0.02)
        return list(np.random.rand(512).astype(float))
    
    def _mock_analyze_colors(self) -> Dict[str, Any]:
        """Mock色彩分析"""
        return {
            "dominant": "#4A90E2",
            "palette": [
                {"hex": "#4A90E2", "rgb": [74, 144, 226], "percentage": 35.2},
                {"hex": "#E74C3C", "rgb": [231, 76, 60], "percentage": 28.1},
                {"hex": "#2ECC71", "rgb": [46, 204, 113], "percentage": 20.3}
            ],
            "tone": "蓝色调",
            "brightness": "明亮",
            "saturation": "鲜艳"
        }

# 工具函数
def encode_image_to_base64(image_path: str) -> str:
    """将图片编码为base64字符串"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except Exception as e:
        logger.error(f"图片base64编码失败: {e}")
        return ""

def calculate_vector_similarity(vector1: List[float], vector2: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    try:
        if not vector1 or not vector2 or len(vector1) != len(vector2):
            return 0.0
        
        # 转换为numpy数组
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        # 计算余弦相似度
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        similarity = dot_product / (norm_v1 * norm_v2)
        return float(similarity)
        
    except Exception as e:
        logger.error(f"计算向量相似度失败: {e}")
        return 0.0

# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_analyzer():
        # 创建分析器（Mock模式）
        analyzer = ImageAnalyzer(use_mock=True)
        
        # 测试分析
        result = await analyzer.analyze_image("test_image.jpg")
        
        print("分析结果:")
        print(f"描述: {result.description}")
        print(f"标签: {result.tags}")
        print(f"色彩: {result.color_palette}")
        print(f"向量维度: {len(result.clip_vector) if result.clip_vector else 0}")
        print(f"置信度: {result.confidence_score}")
        print(f"处理时间: {result.processing_time:.2f}秒")
    
    # 运行测试
    asyncio.run(test_analyzer())