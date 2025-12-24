"""
视频处理服务
Phase 2: FFmpeg集成，生成代理文件和提取音频
"""

import os
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import uuid

class VideoProcessor:
    
    def __init__(self):
        self.asset_root = os.getenv("ASSET_ROOT", "./assets")
        self.ensure_directories()
        self.ffmpeg_available = self.check_ffmpeg_available()
        if not self.ffmpeg_available:
            print("FFmpeg不可用，将使用模拟模式")
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            f"{self.asset_root}/originals",
            f"{self.asset_root}/proxies", 
            f"{self.asset_root}/thumbnails",
            f"{self.asset_root}/audio"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    async def process_video(self, asset_id: str, input_file_path: str) -> Dict[str, Any]:
        """
        完整的视频处理流程
        """
        
        # 严格模式 - 拒绝Mock
        if not self.ffmpeg_available:
            raise RuntimeError("FFmpeg 未安装或未在PATH中。无法处理视频。请安装 FFmpeg 以使用此高级功能。")
        
        try:
            # 1. 移动原始文件到指定位置
            original_path = f"{self.asset_root}/originals/{asset_id}.mp4"
            await self._move_file(input_file_path, original_path)
            
            # 2. 生成代理文件 (720p, 较低码率)
            proxy_path = f"{self.asset_root}/proxies/{asset_id}_proxy.mp4"
            await self._generate_proxy(original_path, proxy_path)
            
            # 3. 生成缩略图
            thumbnail_path = f"{self.asset_root}/thumbnails/{asset_id}_thumb.jpg"
            await self._generate_thumbnail(original_path, thumbnail_path)
            
            # 4. 提取音频 (用于后续转录)
            audio_path = f"{self.asset_root}/audio/{asset_id}.wav"
            await self._extract_audio(original_path, audio_path)
            
            # 5. 获取视频信息
            video_info = await self._get_video_info(original_path)
            
            return {
                "status": "success",
                "paths": {
                    "original": original_path,
                    "proxy": proxy_path,
                    "thumbnail": thumbnail_path,
                    "audio": audio_path
                },
                "video_info": video_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "trace_id": str(uuid.uuid4())
            }
    
    async def _move_file(self, source: str, destination: str):
        """移动文件到目标位置"""
        import shutil
        shutil.move(source, destination)
    
    async def _generate_proxy(self, input_path: str, output_path: str):
        """生成代理文件 - 720p, 较低码率"""
        
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vf", "scale=1280:720",  # 缩放到720p
            "-c:v", "libx264",        # H.264编码
            "-crf", "28",             # 较高压缩率
            "-preset", "fast",        # 快速编码
            "-c:a", "aac",            # AAC音频
            "-b:a", "128k",           # 音频码率
            "-y",                     # 覆盖输出文件
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg proxy generation failed: {stderr.decode()}")
    
    async def _generate_thumbnail(self, input_path: str, output_path: str):
        """生成缩略图 - 取视频中间帧"""
        
        cmd = [
            "ffmpeg", "-i", input_path,
            "-ss", "00:00:01",        # 跳到第1秒
            "-vframes", "1",          # 只取1帧
            "-vf", "scale=320:180",   # 缩放到小尺寸
            "-y",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"FFmpeg thumbnail generation failed: {stderr.decode()}")
    
    async def _extract_audio(self, input_path: str, output_path: str):
        """提取音频为WAV格式"""
        
        cmd = [
            "ffmpeg", "-i", input_path,
            "-vn",                    # 不要视频
            "-acodec", "pcm_s16le",   # PCM 16位
            "-ar", "16000",           # 16kHz采样率 (适合语音识别)
            "-ac", "1",               # 单声道
            "-y",
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # 如果没有音频轨道，创建空文件
            Path(output_path).touch()
    
    async def _get_video_info(self, input_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            input_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {"duration": 0, "width": 0, "height": 0}
        
        try:
            import json
            info = json.loads(stdout.decode())
            
            # 提取视频流信息
            video_stream = None
            for stream in info.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                    break
            
            duration = float(info.get("format", {}).get("duration", 0))
            width = int(video_stream.get("width", 0)) if video_stream else 0
            height = int(video_stream.get("height", 0)) if video_stream else 0
            
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "format": info.get("format", {}).get("format_name", "unknown")
            }
            
        except Exception:
            return {"duration": 0, "width": 0, "height": 0}
    
    def check_ffmpeg_available(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            subprocess.run(["ffmpeg", "-version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def _mock_video_processing(self, asset_id: str, input_file_path: str) -> Dict[str, Any]:
        """模拟视频处理 - 当FFmpeg不可用时"""
        
        try:
            import shutil
            
            # 1. 移动原始文件
            original_path = f"{self.asset_root}/originals/{asset_id}.txt"
            shutil.move(input_file_path, original_path)
            
            # 2. 创建模拟的代理文件
            proxy_path = f"{self.asset_root}/proxies/{asset_id}_proxy.mp4"
            with open(proxy_path, 'w') as f:
                f.write("Mock proxy video file")
            
            # 3. 创建模拟的缩略图
            thumbnail_path = f"{self.asset_root}/thumbnails/{asset_id}_thumb.jpg"
            with open(thumbnail_path, 'w') as f:
                f.write("Mock thumbnail image")
            
            # 4. 创建模拟的音频文件
            audio_path = f"{self.asset_root}/audio/{asset_id}.wav"
            with open(audio_path, 'w') as f:
                f.write("Mock audio file")
            
            return {
                "status": "success",
                "paths": {
                    "original": original_path,
                    "proxy": proxy_path,
                    "thumbnail": thumbnail_path,
                    "audio": audio_path
                },
                "video_info": {
                    "duration": 30.0,
                    "width": 1920,
                    "height": 1080,
                    "format": "mock"
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "trace_id": str(uuid.uuid4())
            }