# -*- coding: utf-8 -*-
"""
音频导出服务
支持 WAV 和 MP3 格式的时间线音频导出
"""

import os
import uuid
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class AudioFormat(str, Enum):
    """音频格式"""
    WAV = "wav"
    MP3 = "mp3"


@dataclass
class AudioExportOptions:
    """音频导出选项"""
    format: AudioFormat = AudioFormat.MP3
    sample_rate: int = 44100  # 44.1kHz
    bitrate: int = 192  # kbps (仅 MP3)
    channels: int = 2  # 立体声


class AudioExporter:
    """音频导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.output_dir = Path("storage/exports/audio")
        self.temp_dir = Path("storage/exports/audio/temp")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 事件服务
        self._event_service = None
    
    def _get_event_service(self):
        """延迟加载事件服务"""
        if self._event_service is None:
            try:
                from services.event_service import event_service
                self._event_service = event_service
            except Exception as e:
                logger.warning(f"EventService 加载失败: {e}")
        return self._event_service
    
    def _check_ffmpeg(self) -> bool:
        """检查 FFmpeg 是否可用"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def export_timeline_audio(
        self,
        timeline_id: str,
        options: Optional[AudioExportOptions] = None
    ) -> Dict[str, Any]:
        """
        导出时间线音频
        
        Args:
            timeline_id: 时间线ID
            options: 导出选项
        """
        options = options or AudioExportOptions()
        task_id = str(uuid.uuid4())
        
        try:
            # 检查 FFmpeg
            if not self._check_ffmpeg():
                return {
                    "status": "error",
                    "message": "FFmpeg 不可用，无法导出音频"
                }
            
            # 获取时间线数据
            timeline_result = self.db.execute(
                text("SELECT id, project_id FROM timelines WHERE id = :id"),
                {"id": timeline_id}
            ).fetchone()
            
            if not timeline_result:
                return {
                    "status": "error",
                    "message": "时间线不存在"
                }
            
            # 获取时间线片段
            clips_result = self.db.execute(
                text("""
                    SELECT tc.id, tc.asset_id, tc.start_time, tc.end_time, 
                           tc.trim_start, tc.trim_end, tc.order_index,
                           a.file_path
                    FROM timeline_clips tc
                    LEFT JOIN assets a ON tc.asset_id = a.id
                    WHERE tc.timeline_id = :timeline_id
                    ORDER BY tc.order_index
                """),
                {"timeline_id": timeline_id}
            ).fetchall()
            
            if not clips_result:
                return {
                    "status": "error",
                    "message": "时间线中没有片段"
                }
            
            # 提取音频片段
            audio_segments = []
            temp_files = []
            
            for i, clip in enumerate(clips_result):
                file_path = clip[7]  # file_path
                if not file_path or not os.path.exists(file_path):
                    continue
                
                trim_start = clip[4] or 0
                trim_end = clip[5]
                
                # 提取音频到临时文件
                temp_audio = str(self.temp_dir / f"audio_{task_id}_{i}.wav")
                temp_files.append(temp_audio)
                
                cmd = ['ffmpeg', '-y', '-i', file_path]
                
                if trim_start > 0:
                    cmd.extend(['-ss', str(trim_start)])
                
                if trim_end:
                    duration = trim_end - trim_start
                    cmd.extend(['-t', str(duration)])
                
                cmd.extend([
                    '-vn',  # 不要视频
                    '-acodec', 'pcm_s16le',
                    '-ar', str(options.sample_rate),
                    '-ac', str(options.channels),
                    temp_audio
                ])
                
                try:
                    subprocess.run(cmd, capture_output=True, check=True, timeout=60)
                    if os.path.exists(temp_audio):
                        audio_segments.append(temp_audio)
                except Exception as e:
                    logger.warning(f"提取音频失败: {e}")
            
            if not audio_segments:
                # 清理临时文件
                for f in temp_files:
                    if os.path.exists(f):
                        os.remove(f)
                return {
                    "status": "error",
                    "message": "没有可导出的音频"
                }
            
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"audio_{timeline_id[:8]}_{timestamp}.{options.format.value}"
            output_path = str(self.output_dir / output_filename)
            
            # 合并音频
            if len(audio_segments) == 1:
                # 单个片段，直接转换
                self._convert_audio(audio_segments[0], output_path, options)
            else:
                # 多个片段，先合并再转换
                concat_file = str(self.temp_dir / f"concat_{task_id}.txt")
                temp_files.append(concat_file)
                
                with open(concat_file, 'w') as f:
                    for seg in audio_segments:
                        f.write(f"file '{seg}'\n")
                
                merged_wav = str(self.temp_dir / f"merged_{task_id}.wav")
                temp_files.append(merged_wav)
                
                # 合并
                concat_cmd = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                    '-i', concat_file,
                    '-c', 'copy',
                    merged_wav
                ]
                subprocess.run(concat_cmd, capture_output=True, check=True, timeout=120)
                
                # 转换到目标格式
                self._convert_audio(merged_wav, output_path, options)
            
            # 清理临时文件
            for f in temp_files:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass
            
            # 获取文件大小
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            # 记录导出历史
            export_id = str(uuid.uuid4())
            self.db.execute(
                text("""
                    INSERT INTO export_history 
                    (id, project_id, export_type, file_path, file_size, file_format, status, created_at)
                    VALUES (:id, :project_id, :export_type, :file_path, :file_size, :file_format, :status, :created_at)
                """),
                {
                    "id": export_id,
                    "project_id": timeline_result[1],
                    "export_type": "timeline_audio",
                    "file_path": output_path,
                    "file_size": file_size,
                    "file_format": options.format.value,
                    "status": "completed",
                    "created_at": datetime.now()
                }
            )
            self.db.commit()
            
            return {
                "status": "success",
                "task_id": task_id,
                "export_id": export_id,
                "file_path": output_path,
                "file_size": file_size,
                "format": options.format.value,
                "sample_rate": options.sample_rate,
                "bitrate": options.bitrate if options.format == AudioFormat.MP3 else None
            }
            
        except Exception as e:
            logger.error(f"音频导出失败: {e}")
            return {
                "status": "error",
                "message": f"音频导出失败: {str(e)}"
            }
    
    def _convert_audio(self, input_path: str, output_path: str, options: AudioExportOptions):
        """转换音频格式"""
        cmd = ['ffmpeg', '-y', '-i', input_path]
        
        if options.format == AudioFormat.WAV:
            cmd.extend([
                '-acodec', 'pcm_s16le',
                '-ar', str(options.sample_rate),
                '-ac', str(options.channels)
            ])
        elif options.format == AudioFormat.MP3:
            cmd.extend([
                '-acodec', 'libmp3lame',
                '-ar', str(options.sample_rate),
                '-ac', str(options.channels),
                '-b:a', f'{options.bitrate}k'
            ])
        
        cmd.append(output_path)
        subprocess.run(cmd, capture_output=True, check=True, timeout=120)


def get_audio_exporter(db: Session) -> AudioExporter:
    """获取音频导出服务实例"""
    return AudioExporter(db)
