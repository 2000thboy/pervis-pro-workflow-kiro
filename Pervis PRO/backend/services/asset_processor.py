"""
素材处理服务
Phase 2: 集成视频处理、AI分析和数据库存储
"""

import os
import tempfile
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
from services.video_processor import VideoProcessor
from services.gemini_client import GeminiClient
from services.database_service import DatabaseService
from services.audio_transcriber import AudioTranscriber
from services.visual_processor import VisualProcessor
from services.memory_store import MemoryStore
from models.base import AssetCreate
import uuid
import asyncio

class AssetProcessor:
    
    def __init__(self, db: Session):
        self.db = db
        self.db_service = DatabaseService(db)
        self.video_processor = VideoProcessor()
        self.gemini_client = GeminiClient()
        self.audio_transcriber = AudioTranscriber()
        self.visual_processor = VisualProcessor()
        self.memory_store = MemoryStore()  # Initialize Vector Memory
    
    async def process_uploaded_file(self, file: UploadFile, project_id: str) -> Dict[str, Any]:
        """
        处理上传的文件 - 完整流程
        """
        
        try:
            # 1. 创建资产记录
            asset_data = AssetCreate(
                project_id=project_id,
                filename=file.filename,
                mime_type=file.content_type or "application/octet-stream",
                source="upload"
            )
            
            asset = await self.db_service.create_asset(asset_data)
            
            # 2. 保存上传的文件到临时位置
            temp_file_path = await self._save_uploaded_file(file)
            
            # 3. 更新状态为处理中
            await self.db_service.update_asset_status(asset.id, "processing", 10)
            
            # 4. 检查文件类型并处理
            if self._is_video_file(file.filename):
                result = await self._process_video_asset(asset.id, temp_file_path)
            else:
                result = await self._process_image_asset(asset.id, temp_file_path)
            
            if result["status"] == "success":
                # 5. 更新资产路径信息
                paths = result.get("paths", {})
                await self.db_service.update_asset_paths(
                    asset.id,
                    file_path=paths.get("original"),
                    proxy_path=paths.get("proxy"),
                    thumbnail_path=paths.get("thumbnail")
                )
                
                # 6. 更新状态为完成
                await self.db_service.update_asset_status(asset.id, "completed", 100)
                
                return {
                    "status": "success",
                    "asset_id": asset.id,
                    "processing_result": result
                }
            else:
                # 处理失败
                await self.db_service.update_asset_status(asset.id, "error", 0)
                return {
                    "status": "error",
                    "asset_id": asset.id,
                    "error": result.get("error", "Unknown processing error")
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "trace_id": str(uuid.uuid4())
            }
        finally:
            # 清理临时文件
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    async def _process_video_asset(self, asset_id: str, file_path: str) -> Dict[str, Any]:
        """处理视频资产"""
        
        try:
            # 1. 视频处理 (代理文件、缩略图、音频提取)
            await self.db_service.update_asset_status(asset_id, "processing", 30)
            video_result = await self.video_processor.process_video(asset_id, file_path)
            
            if video_result["status"] != "success":
                return video_result
            
            # 2. 视觉特征提取 (预处理 - 提取关键帧图片)
            await self.db_service.update_asset_status(asset_id, "processing", 40)
            
            visual_result = None
            pil_images = []
            
            if video_result.get("paths", {}).get("original"):
                original_path = video_result["paths"]["original"]
                # 请求返回PIL图片用于AI分析
                visual_result = await self.visual_processor.extract_visual_features(
                    original_path, 
                    asset_id, 
                    return_images=True
                )
                
                if visual_result["status"] == "success":
                    # 获取图片列表
                    pil_images = visual_result.get("images", [])
                    # 存储视觉分析数据到数据库
                    visual_data = visual_result["visual_analysis"]
                    self.db_service.store_visual_data(asset_id, visual_data)

            # 3. AI内容分析 (Multimodal Vision)
            await self.db_service.update_asset_status(asset_id, "processing", 60)
            
            # 获取资产信息用于AI分析
            asset = self.db_service.get_asset(asset_id)
            description = f"视频文件: {asset.filename}"
            
            # 传入关键帧图片进行多模态分析
            ai_result = await self.gemini_client.analyze_video_content(
                filename=asset.filename,
                description=description,
                images=pil_images
            )
            
            # 4. 创建segments和向量索引
            await self.db_service.update_asset_status(asset_id, "processing", 80)
            
            segments_for_vectors = []
            
            if ai_result["status"] == "success":
                ai_data = ai_result["data"]
                
                # 创建segment记录
                for segment_data in ai_data.get("segments", []):
                    segment = await self.db_service.create_asset_segment(
                        asset_id=asset_id,
                        start_time=segment_data.get("start_time", 0),
                        end_time=segment_data.get("end_time", 10),
                        description=segment_data.get("description", ""),
                        tags=segment_data.get("tags", {})
                    )
                    
                    # 准备向量化数据
                    segments_for_vectors.append({
                        "id": segment.id,
                        "description": segment.description,
                        "tags": {
                            "emotions": segment.emotion_tags or [],
                            "scenes": segment.scene_tags or [],
                            "actions": segment.action_tags or [],
                            "cinematography": segment.cinematography_tags or []
                        }
                    })
                
                # 4. 音频转录处理
            await self.db_service.update_asset_status(asset_id, "processing", 80)
            
            transcription_result = None
            if video_result.get("paths", {}).get("audio"):
                audio_path = video_result["paths"]["audio"]
                transcription_result = await self.audio_transcriber.transcribe_audio(audio_path, asset_id)
                
                if transcription_result["status"] == "success":
                    # 存储转录数据到数据库
                    transcription_data = transcription_result["transcription"]
                    self.db_service.store_transcription_data(asset_id, transcription_data)
            
            # 5. [Moved] 视觉特征提取已在步骤2完成
            # 此前逻辑已合并到上方
            
            # 6. 创建向量索引 (Inject into Memory Store)
            await self.db_service.update_asset_status(asset_id, "processing", 90)
            
            # Persist Visual Vectors to ChromaDB
            if visual_result and visual_result["status"] == "success":
                # Check if we have raw feature vectors (usually 512-float list)
                # Note: VisualProcessor need to return 'feature_vector' in visual_result
                # If not available, we skip for now or compute here. 
                # Assuming VisualProcessor.extract_visual_features returns 'feature_vector' for the whole clip or per keyframe.
                
                # For MVP, let's look for a global feature vector in visual_result
                feature_vector = visual_result.get("visual_analysis", {}).get("feature_vector")
                
                if feature_vector:
                    # Metadata for retrieval
                    metadata = {
                        "asset_id": asset_id,
                        "filename": asset.filename,
                        "type": "visual",
                        "project_id": asset.project_id
                    }
                    self.memory_store.add_memory(
                        asset_id=f"{asset_id}_visual_global",
                        vector=feature_vector,
                        metadata=metadata
                    )
                    # print(f"🧠 [Memory] Ingested visual vector for {asset.filename}")
            
            # Keep existing logic as fallback or parallel if needed, but primarily reliance on MemoryStore now.
            if segments_for_vectors:
                 # Legacy or Text-based vector logic (optional to keep or migrate)
                 pass
            
            return {
                "status": "success",
                "paths": video_result["paths"],
                "video_info": video_result.get("video_info", {}),
                "ai_analysis": ai_result,
                "transcription": transcription_result,
                "visual_analysis": visual_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_image_asset(self, asset_id: str, file_path: str) -> Dict[str, Any]:
        """处理图片资产 - 简化版本"""
        
        try:
            # 对于图片，只需要移动文件和生成缩略图
            import shutil
            
            asset_root = self.video_processor.asset_root
            original_path = f"{asset_root}/originals/{asset_id}.jpg"
            thumbnail_path = f"{asset_root}/thumbnails/{asset_id}_thumb.jpg"
            
            # 移动原始文件
            shutil.move(file_path, original_path)
            
            # 复制作为缩略图 (简化处理)
            shutil.copy2(original_path, thumbnail_path)
            
            return {
                "status": "success",
                "paths": {
                    "original": original_path,
                    "thumbnail": thumbnail_path
                }
            }
            
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e)
            }
    
    async def _save_uploaded_file(self, file: UploadFile) -> str:
        """保存上传文件到临时位置"""
        
        # 创建临时文件
        suffix = os.path.splitext(file.filename)[1] if file.filename else ""
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        
        try:
            # 读取并写入文件内容
            content = await file.read()
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(content)
            
            return temp_path
            
        except Exception:
            # 如果出错，清理临时文件
            os.close(temp_fd)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise
    
    def _is_video_file(self, filename: str) -> bool:
        """判断是否为视频文件"""
        if not filename:
            return False
        
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        ext = os.path.splitext(filename)[1].lower()
        return ext in video_extensions
    
    async def get_asset_status(self, asset_id: str) -> Dict[str, Any]:
        """获取资产处理状态"""
        
        asset = await self.db_service.get_asset(asset_id)
        if not asset:
            return {
                "status": "error",
                "message": "Asset not found"
            }
        
        # 获取segments
        segments = await self.db_service.get_asset_segments(asset_id)
        
        segment_list = []
        for segment in segments:
            segment_list.append({
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
        
        # 获取转录数据
        transcription_data = self.db_service.get_transcription_data(asset_id)
        
        # 获取视觉分析数据
        visual_data = self.db_service.get_visual_data(asset_id)
        
        return {
            "status": asset.processing_status,
            "progress": asset.processing_progress,
            "proxy_url": f"/assets/proxies/{asset_id}_proxy.mp4" if asset.proxy_path else None,
            "thumbnail_url": f"/assets/thumbnails/{asset_id}_thumb.jpg" if asset.thumbnail_path else None,
            "segments": segment_list,
            "transcription": transcription_data,
            "visual_analysis": visual_data
        }
    
    def _prepare_transcription_vectors(self, transcription_data: Dict[str, Any]) -> List[Dict]:
        """准备转录文本的向量化数据"""
        
        vector_segments = []
        
        for segment in transcription_data.get("segments", []):
            # 为每个转录片段创建向量数据
            vector_segment = {
                "id": f"transcript_{segment['id']}",
                "description": segment["text"],
                "tags": {
                    "content_type": ["transcript", "audio"],
                    "language": [transcription_data.get("language", "unknown")],
                    "confidence": [f"confidence_{int(segment['confidence'] * 100)}"],
                    "time_range": [f"{segment['start_time']:.1f}s-{segment['end_time']:.1f}s"]
                }
            }
            vector_segments.append(vector_segment)
        
        # 如果转录文本较长，也为全文创建一个向量
        full_text = transcription_data.get("full_text", "")
        if len(full_text) > 50:  # 只有足够长的文本才创建全文向量
            vector_segments.append({
                "id": "transcript_full",
                "description": full_text,
                "tags": {
                    "content_type": ["transcript", "audio", "full_text"],
                    "language": [transcription_data.get("language", "unknown")],
                    "duration": [f"{transcription_data.get('duration', 0):.1f}s"]
                }
            })
        
        return vector_segments
    
    def _prepare_visual_vectors(self, visual_data: Dict[str, Any]) -> List[Dict]:
        """准备视觉特征的向量化数据"""
        
        vector_segments = []
        
        # 为每个关键帧创建向量数据
        keyframes = visual_data.get("keyframes", [])
        for keyframe in keyframes:
            timestamp = keyframe.get("timestamp", 0)
            analysis = keyframe.get("analysis", {})
            
            # 构建视觉描述
            visual_description_parts = []
            
            # 亮度和对比度描述
            brightness = analysis.get("brightness", 0)
            contrast = analysis.get("contrast", 0)
            
            if brightness > 150:
                visual_description_parts.append("明亮画面")
            elif brightness < 80:
                visual_description_parts.append("昏暗画面")
            else:
                visual_description_parts.append("正常亮度")
            
            if contrast > 50:
                visual_description_parts.append("高对比度")
            elif contrast < 20:
                visual_description_parts.append("低对比度")
            
            # 色彩描述
            color_balance = analysis.get("color_balance", {})
            if color_balance:
                red = color_balance.get("red", 0)
                blue = color_balance.get("blue", 0)
                if red > blue + 20:
                    visual_description_parts.append("暖色调")
                elif blue > red + 20:
                    visual_description_parts.append("冷色调")
            
            # 复杂度描述
            complexity = analysis.get("estimated_complexity", "medium")
            visual_description_parts.append(f"{complexity}复杂度画面")
            
            description = " ".join(visual_description_parts)
            
            vector_segment = {
                "id": f"visual_{keyframe.get('frame_index', 0)}",
                "description": description,
                "tags": {
                    "content_type": ["visual", "keyframe"],
                    "timestamp": [f"{timestamp:.1f}s"],
                    "brightness": [self._categorize_brightness(brightness)],
                    "complexity": [complexity],
                    "visual_features": ["color_analysis", "composition"]
                }
            }
            vector_segments.append(vector_segment)
        
        # 为整体视觉特征创建一个向量
        visual_summary = visual_data.get("visual_description", {}).get("visual_summary", {})
        if visual_summary:
            overall_description_parts = []
            
            brightness_level = visual_summary.get("brightness_level", "normal")
            color_tone = visual_summary.get("color_tone", "neutral")
            complexity = visual_summary.get("visual_complexity", "medium")
            lighting = visual_summary.get("lighting_quality", "normal")
            
            overall_description_parts.extend([
                f"{brightness_level}亮度",
                f"{color_tone}色调",
                f"{complexity}复杂度",
                f"{lighting}光线"
            ])
            
            vector_segments.append({
                "id": "visual_overall",
                "description": " ".join(overall_description_parts),
                "tags": {
                    "content_type": ["visual", "overall"],
                    "brightness_level": [brightness_level],
                    "color_tone": [color_tone],
                    "visual_complexity": [complexity],
                    "lighting_quality": [lighting]
                }
            })
        
        return vector_segments
    
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