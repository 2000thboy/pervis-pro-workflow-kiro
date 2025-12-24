"""
视觉处理服务
Phase 4: CLIP集成，视觉特征提取和画面分析
"""

from __future__ import annotations

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)

# 预设默认值
CLIP_AVAILABLE = False
clip = None
torch = None
Image = None
cv2 = None

# 强制使用Mock模式 - 已禁用，启用真实AI内核
# 依赖要求: torch, clip, opencv-python, pillow
FORCE_MOCK_MODE = False

if not FORCE_MOCK_MODE:
    # 尝试导入CLIP和相关库，如果失败则自动回退到Mock模式但会报警
    try:
        import clip
        import torch
        from PIL import Image
        import cv2
        CLIP_AVAILABLE = True
        logger.info("✅ 视觉内核已激活: CLIP/Torch/OpenCV 加载成功")
    except (ImportError, OSError) as e:
        logger.warning(f"⚠️ 视觉内核启动失败 (依赖缺失或DLL错误): {e}。系统将自动降级运行在Mock模式。")
        logger.warning("提示: 如果遇到DLL加载错误，请安装 [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)")
        CLIP_AVAILABLE = False
else:
    # Mock模式 - 创建基本的Mock类以避免NameError
    logger.info("强制使用Mock模式（CLIP已禁用）")
    
    # Mock PIL.Image with Image.Image support
    class MockImage:
        size = (1920, 1080)
    
    class MockPILImage:
        Image = MockImage  # 支持 Image.Image 语法
        
        def fromarray(self, arr):
            return MockImage()
    
    Image = MockPILImage()

class VisualProcessor:
    
    def __init__(self):
        self.model_name = os.getenv("CLIP_MODEL", "ViT-B/32")  # ViT-B/32, ViT-B/16, ViT-L/14
        self.model = None
        self.preprocess = None
        self.device = None
        self.clip_available = CLIP_AVAILABLE
        
        if self.clip_available:
            try:
                self._load_model()
                logger.info(f"CLIP模型 {self.model_name} 加载成功")
            except Exception as e:
                logger.error(f"CLIP模型加载失败: {e}")
                self.clip_available = False
        else:
            logger.info("使用Mock视觉处理模式")
    
    def _load_model(self):
        """加载CLIP模型"""
        if not self.clip_available:
            return
            
        try:
            # 检查GPU可用性
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"使用设备: {self.device}")
            
            # 加载CLIP模型
            self.model, self.preprocess = clip.load(self.model_name, device=self.device)
            
        except Exception as e:
            logger.error(f"CLIP模型加载失败: {e}")
            self.clip_available = False
    
    async def extract_visual_features(self, video_path: str, asset_id: str, 
                                    sample_interval: float = 2.0,
                                    return_images: bool = False) -> Dict[str, Any]:
        """
        从视频中提取视觉特征
        
        Args:
            video_path: 视频文件路径
            asset_id: 资产ID
            sample_interval: 关键帧采样间隔(秒)
            return_images: 是否返回PIL图像对象列表 (用于Gemini Vision)
            
        Returns:
            视觉特征分析结果
        """
        
        if not self.clip_available or not self.model:
            return await self._mock_visual_analysis(video_path, asset_id)
        
        try:
            # 检查视频文件是否存在
            if not os.path.exists(video_path):
                return {
                    "status": "error",
                    "message": f"视频文件不存在: {video_path}"
                }
            
            logger.info(f"开始提取视频视觉特征: {video_path}")
            
            # 在线程池中执行视觉分析以避免阻塞
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._extract_features_sync, 
                video_path, asset_id, sample_interval, return_images
            )
            
            return result
            
        except Exception as e:
            logger.error(f"视觉特征提取失败: {e}")
            return {
                "status": "error",
                "message": f"视觉分析失败: {str(e)}",
                "asset_id": asset_id
            }
    
    def _extract_features_sync(self, video_path: str, asset_id: str, sample_interval: float, 
                             return_images: bool = False) -> Dict[str, Any]:
        """同步视觉特征提取函数 (在线程池中执行)"""
        
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {
                    "status": "error",
                    "message": "无法打开视频文件"
                }
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # 计算采样帧
            frame_interval = int(fps * sample_interval) if fps > 0 else 30
            sample_frames = list(range(0, total_frames, frame_interval))
            
            logger.info(f"视频时长: {duration:.1f}秒, 采样{len(sample_frames)}帧")
            
            # 提取关键帧和特征
            keyframes = []
            visual_features = []
            pil_images_list = []
            
            for frame_idx in sample_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    continue
                
                # 转换为RGB格式
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # 提取CLIP特征
                image_features = self._extract_clip_features(pil_image)
                
                if return_images:
                    pil_images_list.append(pil_image)
                
                # 分析画面内容
                frame_analysis = self._analyze_frame_content(pil_image, frame_idx / fps)
                
                keyframes.append({
                    "frame_index": frame_idx,
                    "timestamp": frame_idx / fps,
                    "features": image_features.tolist() if image_features is not None else [],
                    "analysis": frame_analysis
                })
                
                if image_features is not None:
                    visual_features.append(image_features)
            
            cap.release()
            
            # 计算全局视觉特征
            global_features = self._compute_global_features(visual_features)
            
            # 生成视觉描述
            visual_description = self._generate_visual_description(keyframes)
            
            return {
                "status": "success",
                "asset_id": asset_id,
                "visual_analysis": {
                    "duration": duration,
                    "keyframes_count": len(keyframes),
                    "sample_interval": sample_interval,
                    "keyframes": keyframes,
                    "global_features": global_features,
                    "visual_description": visual_description,
                    "color_analysis": self._analyze_color_palette(keyframes),
                    "composition_analysis": self._analyze_composition(keyframes)
                },
                "images": pil_images_list if return_images else []
            }

            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _extract_clip_features(self, image: Image.Image) -> Optional[np.ndarray]:
        """使用CLIP提取图像特征"""
        
        try:
            # 预处理图像
            image_input = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                image_features = self.model.encode_image(image_input)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy()[0]
            
        except Exception as e:
            logger.warning(f"CLIP特征提取失败: {e}")
            return None
    
    def _analyze_frame_content(self, image: Image.Image, timestamp: float) -> Dict[str, Any]:
        """分析单帧内容"""
        
        try:
            # 基础图像分析
            width, height = image.size
            aspect_ratio = width / height
            
            # 转换为numpy数组进行分析
            img_array = np.array(image)
            
            # 亮度分析
            brightness = np.mean(img_array)
            
            # 对比度分析
            contrast = np.std(img_array)
            
            # 色彩分析
            color_channels = np.mean(img_array, axis=(0, 1))
            
            # 边缘检测 (简化版)
            gray = np.mean(img_array, axis=2)
            edges = np.abs(np.gradient(gray)).mean()
            
            return {
                "timestamp": timestamp,
                "dimensions": {"width": width, "height": height},
                "aspect_ratio": aspect_ratio,
                "brightness": float(brightness),
                "contrast": float(contrast),
                "color_balance": {
                    "red": float(color_channels[0]),
                    "green": float(color_channels[1]),
                    "blue": float(color_channels[2])
                },
                "edge_density": float(edges),
                "estimated_complexity": self._estimate_visual_complexity(img_array)
            }
            
        except Exception as e:
            logger.warning(f"帧内容分析失败: {e}")
            return {
                "timestamp": timestamp,
                "error": str(e)
            }
    
    def _estimate_visual_complexity(self, img_array: np.ndarray) -> str:
        """估算视觉复杂度"""
        
        try:
            # 计算颜色变化
            color_variance = np.var(img_array)
            
            # 计算边缘密度
            gray = np.mean(img_array, axis=2)
            edges = np.abs(np.gradient(gray)).mean()
            
            # 简单的复杂度分类
            if color_variance > 2000 and edges > 20:
                return "high"
            elif color_variance > 1000 or edges > 10:
                return "medium"
            else:
                return "low"
                
        except Exception:
            return "unknown"
    
    def _compute_global_features(self, visual_features: List[np.ndarray]) -> Dict[str, Any]:
        """计算全局视觉特征"""
        
        if not visual_features:
            return {"error": "没有有效的视觉特征"}
        
        try:
            # 转换为numpy数组
            features_array = np.array(visual_features)
            
            # 计算统计特征
            mean_features = np.mean(features_array, axis=0)
            std_features = np.std(features_array, axis=0)
            
            # 计算特征变化
            feature_variance = np.var(features_array, axis=0).mean()
            
            return {
                "mean_features": mean_features.tolist(),
                "feature_variance": float(feature_variance),
                "feature_dimension": len(mean_features),
                "temporal_consistency": self._calculate_temporal_consistency(features_array)
            }
            
        except Exception as e:
            logger.warning(f"全局特征计算失败: {e}")
            return {"error": str(e)}
    
    def _calculate_temporal_consistency(self, features_array: np.ndarray) -> float:
        """计算时间一致性"""
        
        try:
            if len(features_array) < 2:
                return 1.0
            
            # 计算相邻帧之间的相似度
            similarities = []
            for i in range(len(features_array) - 1):
                similarity = np.dot(features_array[i], features_array[i + 1])
                similarities.append(similarity)
            
            return float(np.mean(similarities))
            
        except Exception:
            return 0.5
    
    def _analyze_color_palette(self, keyframes: List[Dict]) -> Dict[str, Any]:
        """分析色彩调色板"""
        
        try:
            all_colors = []
            
            for frame in keyframes:
                analysis = frame.get("analysis", {})
                color_balance = analysis.get("color_balance", {})
                
                if color_balance:
                    all_colors.append([
                        color_balance.get("red", 0),
                        color_balance.get("green", 0),
                        color_balance.get("blue", 0)
                    ])
            
            if not all_colors:
                return {"error": "没有颜色数据"}
            
            colors_array = np.array(all_colors)
            
            # 计算主要色调
            mean_color = np.mean(colors_array, axis=0)
            
            # 色彩温度估算
            color_temp = "warm" if mean_color[0] > mean_color[2] else "cool"
            
            # 色彩饱和度
            saturation = np.std(colors_array)
            
            return {
                "dominant_color": {
                    "red": float(mean_color[0]),
                    "green": float(mean_color[1]),
                    "blue": float(mean_color[2])
                },
                "color_temperature": color_temp,
                "saturation_level": float(saturation),
                "color_consistency": float(1.0 - np.var(colors_array) / 10000)
            }
            
        except Exception as e:
            logger.warning(f"色彩分析失败: {e}")
            return {"error": str(e)}
    
    def _analyze_composition(self, keyframes: List[Dict]) -> Dict[str, Any]:
        """分析构图特征"""
        
        try:
            brightness_values = []
            contrast_values = []
            complexity_counts = {"low": 0, "medium": 0, "high": 0}
            
            for frame in keyframes:
                analysis = frame.get("analysis", {})
                
                brightness = analysis.get("brightness", 0)
                contrast = analysis.get("contrast", 0)
                complexity = analysis.get("estimated_complexity", "unknown")
                
                brightness_values.append(brightness)
                contrast_values.append(contrast)
                
                if complexity in complexity_counts:
                    complexity_counts[complexity] += 1
            
            # 计算构图统计
            avg_brightness = np.mean(brightness_values) if brightness_values else 0
            avg_contrast = np.mean(contrast_values) if contrast_values else 0
            
            # 主要复杂度
            dominant_complexity = max(complexity_counts, key=complexity_counts.get)
            
            # 光线条件估算
            lighting_condition = self._estimate_lighting_condition(avg_brightness, avg_contrast)
            
            return {
                "average_brightness": float(avg_brightness),
                "average_contrast": float(avg_contrast),
                "dominant_complexity": dominant_complexity,
                "lighting_condition": lighting_condition,
                "visual_stability": self._calculate_visual_stability(brightness_values, contrast_values)
            }
            
        except Exception as e:
            logger.warning(f"构图分析失败: {e}")
            return {"error": str(e)}
    
    def _estimate_lighting_condition(self, brightness: float, contrast: float) -> str:
        """估算光线条件"""
        
        if brightness > 150:
            return "bright" if contrast > 50 else "overexposed"
        elif brightness < 80:
            return "dark" if contrast > 30 else "underexposed"
        else:
            return "normal"
    
    def _calculate_visual_stability(self, brightness_values: List[float], contrast_values: List[float]) -> float:
        """计算视觉稳定性"""
        
        try:
            if len(brightness_values) < 2:
                return 1.0
            
            brightness_stability = 1.0 - (np.std(brightness_values) / np.mean(brightness_values))
            contrast_stability = 1.0 - (np.std(contrast_values) / np.mean(contrast_values))
            
            return float((brightness_stability + contrast_stability) / 2)
            
        except Exception:
            return 0.5
    
    def _generate_visual_description(self, keyframes: List[Dict]) -> Dict[str, Any]:
        """生成视觉描述"""
        
        try:
            if not keyframes:
                return {"error": "没有关键帧数据"}
            
            # 分析整体视觉特征
            total_frames = len(keyframes)
            
            # 亮度分布
            brightness_values = [frame.get("analysis", {}).get("brightness", 0) for frame in keyframes]
            avg_brightness = np.mean(brightness_values)
            
            # 色彩分析
            color_analysis = self._analyze_color_palette(keyframes)
            
            # 构图分析
            composition_analysis = self._analyze_composition(keyframes)
            
            # 生成描述性标签
            visual_tags = self._generate_visual_tags(
                avg_brightness, 
                color_analysis, 
                composition_analysis
            )
            
            return {
                "total_keyframes": total_frames,
                "visual_summary": {
                    "brightness_level": self._categorize_brightness(avg_brightness),
                    "color_tone": color_analysis.get("color_temperature", "neutral"),
                    "visual_complexity": composition_analysis.get("dominant_complexity", "medium"),
                    "lighting_quality": composition_analysis.get("lighting_condition", "normal")
                },
                "visual_tags": visual_tags,
                "technical_quality": {
                    "stability": composition_analysis.get("visual_stability", 0.5),
                    "consistency": color_analysis.get("color_consistency", 0.5)
                }
            }
            
        except Exception as e:
            logger.warning(f"视觉描述生成失败: {e}")
            return {"error": str(e)}
    
    def _categorize_brightness(self, brightness: float) -> str:
        """分类亮度级别"""
        if brightness > 180:
            return "very_bright"
        elif brightness > 120:
            return "bright"
        elif brightness > 80:
            return "normal"
        elif brightness > 40:
            return "dark"
        else:
            return "very_dark"
    
    def _generate_visual_tags(self, brightness: float, color_analysis: Dict, composition_analysis: Dict) -> List[str]:
        """生成视觉标签"""
        
        tags = []
        
        # 亮度标签
        brightness_level = self._categorize_brightness(brightness)
        tags.append(brightness_level)
        
        # 色彩标签
        color_temp = color_analysis.get("color_temperature", "neutral")
        tags.append(f"{color_temp}_tone")
        
        # 构图标签
        complexity = composition_analysis.get("dominant_complexity", "medium")
        tags.append(f"{complexity}_complexity")
        
        # 光线标签
        lighting = composition_analysis.get("lighting_condition", "normal")
        tags.append(f"{lighting}_lighting")
        
        return tags
    
    async def _mock_visual_analysis(self, video_path: str, asset_id: str) -> Dict[str, Any]:
        """Mock视觉分析 - 当CLIP不可用时"""
        
        logger.warning("使用Mock视觉分析模式")
        
        try:
            # 模拟处理时间
            await asyncio.sleep(2)
            
            # 生成模拟视觉分析数据
            mock_keyframes = [
                {
                    "frame_index": 0,
                    "timestamp": 0.0,
                    "features": [0.1] * 512,  # 模拟CLIP特征向量
                    "analysis": {
                        "timestamp": 0.0,
                        "dimensions": {"width": 1920, "height": 1080},
                        "aspect_ratio": 1.78,
                        "brightness": 120.5,
                        "contrast": 45.2,
                        "color_balance": {"red": 110, "green": 115, "blue": 95},
                        "edge_density": 15.3,
                        "estimated_complexity": "medium"
                    }
                },
                {
                    "frame_index": 60,
                    "timestamp": 2.0,
                    "features": [0.15] * 512,
                    "analysis": {
                        "timestamp": 2.0,
                        "dimensions": {"width": 1920, "height": 1080},
                        "aspect_ratio": 1.78,
                        "brightness": 135.8,
                        "contrast": 52.1,
                        "color_balance": {"red": 125, "green": 120, "blue": 100},
                        "edge_density": 18.7,
                        "estimated_complexity": "high"
                    }
                }
            ]
            
            return {
                "status": "success",
                "asset_id": asset_id,
                "visual_analysis": {
                    "duration": 10.0,
                    "keyframes_count": len(mock_keyframes),
                    "sample_interval": 2.0,
                    "keyframes": mock_keyframes,
                    "global_features": {
                        "mean_features": [0.125] * 512,
                        "feature_variance": 0.02,
                        "feature_dimension": 512,
                        "temporal_consistency": 0.85
                    },
                    "visual_description": {
                        "total_keyframes": 2,
                        "visual_summary": {
                            "brightness_level": "normal",
                            "color_tone": "warm",
                            "visual_complexity": "medium",
                            "lighting_quality": "normal"
                        },
                        "visual_tags": ["normal", "warm_tone", "medium_complexity", "normal_lighting"],
                        "technical_quality": {
                            "stability": 0.8,
                            "consistency": 0.75
                        }
                    },
                    "color_analysis": {
                        "dominant_color": {"red": 117.5, "green": 117.5, "blue": 97.5},
                        "color_temperature": "warm",
                        "saturation_level": 15.2,
                        "color_consistency": 0.75
                    },
                    "composition_analysis": {
                        "average_brightness": 128.15,
                        "average_contrast": 48.65,
                        "dominant_complexity": "medium",
                        "lighting_condition": "normal",
                        "visual_stability": 0.8
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Mock视觉分析失败: {str(e)}",
                "asset_id": asset_id
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        
        return {
            "available": self.clip_available,
            "model_name": self.model_name,
            "device": self.device if self.device else "cpu",
            "features": {
                "visual_features": True,
                "color_analysis": True,
                "composition_analysis": True,
                "keyframe_extraction": True,
                "temporal_analysis": True
            }
        }
    
    def estimate_processing_time(self, video_duration: float, sample_interval: float = 2.0) -> float:
        """估算处理时间"""
        
        if not self.clip_available:
            return video_duration * 0.1  # Mock模式很快
        
        # 估算关键帧数量
        keyframes_count = max(1, int(video_duration / sample_interval))
        
        # 根据设备和模型估算时间
        base_time_per_frame = 0.5 if self.device == "cuda" else 2.0
        
        return keyframes_count * base_time_per_frame
