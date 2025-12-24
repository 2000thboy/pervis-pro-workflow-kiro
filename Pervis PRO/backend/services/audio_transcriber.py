"""
音频转录服务
Phase 4: Whisper集成，音频转文字和时间轴对齐
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 预设默认值
WHISPER_AVAILABLE = False
whisper = None
torch = None

# 强制使用Mock模式 - 临时禁用Whisper以解决依赖问题
# TODO: 安装GTK依赖后可重新启用Whisper
FORCE_MOCK_MODE = True

if not FORCE_MOCK_MODE:
    # 尝试导入whisper，如果失败则使用Mock模式
    try:
        import whisper
        import torch
        WHISPER_AVAILABLE = True
        logger.info("Whisper 可用")
    except ImportError as e:
        logger.warning(f"Whisper 不可用，将使用Mock模式: {e}")
    except Exception as e:
        # 捕获所有其他异常（如依赖库缺失）
        logger.warning(f"Whisper 加载失败，将使用Mock模式: {e}")
else:
    logger.info("强制使用Mock模式（Whisper已禁用）")

class AudioTranscriber:
    
    def __init__(self):
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny, base, small, medium, large
        self.model = None
        self.whisper_available = WHISPER_AVAILABLE
        
        if self.whisper_available:
            try:
                self._load_model()
                logger.info(f"Whisper模型 {self.model_size} 加载成功")
            except Exception as e:
                logger.error(f"Whisper模型加载失败: {e}")
                self.whisper_available = False
        else:
            logger.info("使用Mock转录模式")
    
    def _load_model(self):
        """加载Whisper模型"""
        if not self.whisper_available:
            return
            
        try:
            # 检查GPU可用性
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"使用设备: {device}")
            
            # 加载模型
            self.model = whisper.load_model(self.model_size, device=device)
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            self.whisper_available = False
    
    async def transcribe_audio(self, audio_file_path: str, asset_id: str) -> Dict[str, Any]:
        """
        转录音频文件为带时间戳的文本
        
        Args:
            audio_file_path: 音频文件路径
            asset_id: 资产ID
            
        Returns:
            转录结果包含文本、时间戳、置信度等信息
        """
        
        if not self.whisper_available or not self.model:
            return await self._mock_transcription(audio_file_path, asset_id)
        
        try:
            # 检查音频文件是否存在
            if not os.path.exists(audio_file_path):
                return {
                    "status": "error",
                    "message": f"音频文件不存在: {audio_file_path}"
                }
            
            # 检查文件大小
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                return {
                    "status": "error", 
                    "message": "音频文件为空"
                }
            
            logger.info(f"开始转录音频文件: {audio_file_path}")
            
            # 执行转录 (在线程池中运行以避免阻塞)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._transcribe_sync, 
                audio_file_path
            )
            
            if result["status"] == "success":
                # 处理转录结果
                transcription_data = self._process_transcription_result(result["data"], asset_id)
                
                return {
                    "status": "success",
                    "asset_id": asset_id,
                    "transcription": transcription_data,
                    "processing_info": {
                        "model_size": self.model_size,
                        "audio_duration": transcription_data.get("duration", 0),
                        "segments_count": len(transcription_data.get("segments", [])),
                        "detected_language": transcription_data.get("language", "unknown")
                    }
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"音频转录失败: {e}")
            return {
                "status": "error",
                "message": f"转录失败: {str(e)}",
                "asset_id": asset_id
            }
    
    def _transcribe_sync(self, audio_file_path: str) -> Dict[str, Any]:
        """同步转录函数 (在线程池中执行)"""
        
        try:
            # 使用Whisper进行转录
            result = self.model.transcribe(
                audio_file_path,
                word_timestamps=True,  # 启用词级时间戳
                verbose=False
            )
            
            return {
                "status": "success",
                "data": result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _process_transcription_result(self, whisper_result: Dict, asset_id: str) -> Dict[str, Any]:
        """处理Whisper转录结果"""
        
        # 提取基本信息
        full_text = whisper_result.get("text", "").strip()
        language = whisper_result.get("language", "unknown")
        segments = whisper_result.get("segments", [])
        
        # 处理分段信息
        processed_segments = []
        for segment in segments:
            segment_data = {
                "id": len(processed_segments),
                "start_time": segment.get("start", 0),
                "end_time": segment.get("end", 0),
                "text": segment.get("text", "").strip(),
                "confidence": segment.get("avg_logprob", 0),  # 平均对数概率作为置信度
                "words": []
            }
            
            # 处理词级时间戳
            if "words" in segment:
                for word_info in segment["words"]:
                    word_data = {
                        "word": word_info.get("word", "").strip(),
                        "start": word_info.get("start", 0),
                        "end": word_info.get("end", 0),
                        "probability": word_info.get("probability", 0)
                    }
                    segment_data["words"].append(word_data)
            
            processed_segments.append(segment_data)
        
        # 计算总体统计
        total_duration = max([seg["end_time"] for seg in processed_segments]) if processed_segments else 0
        avg_confidence = sum([seg["confidence"] for seg in processed_segments]) / len(processed_segments) if processed_segments else 0
        
        return {
            "asset_id": asset_id,
            "full_text": full_text,
            "language": language,
            "duration": total_duration,
            "segments": processed_segments,
            "statistics": {
                "total_segments": len(processed_segments),
                "total_words": sum([len(seg["words"]) for seg in processed_segments]),
                "average_confidence": avg_confidence,
                "words_per_minute": (sum([len(seg["words"]) for seg in processed_segments]) / total_duration * 60) if total_duration > 0 else 0
            }
        }
    
    async def _mock_transcription(self, audio_file_path: str, asset_id: str) -> Dict[str, Any]:
        """Mock转录 - 当Whisper不可用时"""
        
        logger.warning("使用Mock转录模式")
        
        try:
            # 模拟处理时间
            await asyncio.sleep(1)
            
            # 生成模拟转录数据
            mock_segments = [
                {
                    "id": 0,
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "text": "这是模拟的转录文本片段一",
                    "confidence": 0.85,
                    "words": [
                        {"word": "这是", "start": 0.0, "end": 0.5, "probability": 0.9},
                        {"word": "模拟的", "start": 0.5, "end": 1.2, "probability": 0.8},
                        {"word": "转录", "start": 1.2, "end": 1.8, "probability": 0.9},
                        {"word": "文本", "start": 1.8, "end": 2.3, "probability": 0.85},
                        {"word": "片段一", "start": 2.3, "end": 3.0, "probability": 0.8}
                    ]
                },
                {
                    "id": 1,
                    "start_time": 5.0,
                    "end_time": 10.0,
                    "text": "这是第二个模拟转录片段",
                    "confidence": 0.78,
                    "words": [
                        {"word": "这是", "start": 5.0, "end": 5.4, "probability": 0.9},
                        {"word": "第二个", "start": 5.4, "end": 6.1, "probability": 0.75},
                        {"word": "模拟", "start": 6.1, "end": 6.6, "probability": 0.8},
                        {"word": "转录", "start": 6.6, "end": 7.1, "probability": 0.85},
                        {"word": "片段", "start": 7.1, "end": 7.6, "probability": 0.7}
                    ]
                }
            ]
            
            full_text = " ".join([seg["text"] for seg in mock_segments])
            
            return {
                "status": "success",
                "asset_id": asset_id,
                "transcription": {
                    "asset_id": asset_id,
                    "full_text": full_text,
                    "language": "zh",
                    "duration": 10.0,
                    "segments": mock_segments,
                    "statistics": {
                        "total_segments": len(mock_segments),
                        "total_words": sum([len(seg["words"]) for seg in mock_segments]),
                        "average_confidence": 0.815,
                        "words_per_minute": 60.0
                    }
                },
                "processing_info": {
                    "model_size": "mock",
                    "audio_duration": 10.0,
                    "segments_count": len(mock_segments),
                    "detected_language": "zh"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Mock转录失败: {str(e)}",
                "asset_id": asset_id
            }
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        
        if not self.whisper_available:
            return ["zh", "en", "ja", "ko"]  # Mock支持的语言
        
        # Whisper支持的主要语言
        return [
            "zh", "en", "ja", "ko", "es", "fr", "de", "it", "pt", "ru",
            "ar", "hi", "th", "vi", "id", "ms", "tl", "nl", "sv", "da"
        ]
    
    def estimate_processing_time(self, audio_duration: float) -> float:
        """估算处理时间"""
        
        if not self.whisper_available:
            return audio_duration * 0.1  # Mock模式很快
        
        # 根据模型大小估算 (实际时间会根据硬件有所不同)
        time_multipliers = {
            "tiny": 0.1,
            "base": 0.2, 
            "small": 0.3,
            "medium": 0.5,
            "large": 0.8
        }
        
        multiplier = time_multipliers.get(self.model_size, 0.3)
        return audio_duration * multiplier
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        
        return {
            "available": self.whisper_available,
            "model_size": self.model_size,
            "device": "cuda" if (torch and torch.cuda.is_available()) else "cpu",
            "supported_languages": len(self.get_supported_languages()),
            "features": {
                "word_timestamps": True,
                "language_detection": True,
                "confidence_scores": True,
                "multiple_speakers": False  # Whisper不直接支持说话人分离
            }
        }