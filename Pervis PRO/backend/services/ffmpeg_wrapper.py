"""
FFmpeg Wrapper Service
Provides core video processing functionality: trimming, concatenation, transitions, audio processing, etc.
"""

import ffmpeg
import subprocess
import os
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoInfo:
    """Video information data class"""
    def __init__(self, data: dict):
        self.duration = float(data.get('duration', 0))
        self.width = int(data.get('width', 0))
        self.height = int(data.get('height', 0))
        self.fps = self._parse_fps(data.get('r_frame_rate', '30/1'))
        self.codec = data.get('codec_name', 'unknown')
        self.bitrate = int(data.get('bit_rate', 0))
        self.has_audio = data.get('has_audio', False)
        
    def _parse_fps(self, fps_str: str) -> float:
        """Parse frame rate string (e.g.: '30/1' -> 30.0)"""
        try:
            num, den = fps_str.split('/')
            return float(num) / float(den)
        except:
            return 30.0


class FFmpegWrapper:
    """FFmpeg command wrapper"""
    
    def __init__(self, check_on_init=False):
        """
        Initialize FFmpegWrapper
        
        Args:
            check_on_init: Whether to check FFmpeg on initialization (default False, lazy check)
        """
        self._ffmpeg_checked = False
        if check_on_init:
            self._check_ffmpeg()
        
    def _check_ffmpeg(self):
        """Check if FFmpeg is available"""
        if self._ffmpeg_checked:
            return
            
        try:
            # Use FFmpeg detector for checking
            try:
                from .ffmpeg_detector import ffmpeg_detector
                
                status = ffmpeg_detector.check_installation()
                
                if status.is_installed and status.is_version_supported:
                    logger.info(f"FFmpeg is available: version {status.version} at {status.path}")
                    self._ffmpeg_checked = True
                else:
                    error_msg = self._generate_ffmpeg_error_message(status)
                    logger.error(f"FFmpeg check failed: {error_msg}")
                    raise RuntimeError(error_msg)
                    
            except ImportError:
                # Fallback to original check method
                try:
                    result = subprocess.run(
                        ['ffmpeg', '-version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        logger.info("FFmpeg is available")
                        self._ffmpeg_checked = True
                    else:
                        raise RuntimeError("FFmpeg not found")
                except Exception as e:
                    logger.error(f"FFmpeg check failed: {e}")
                    raise RuntimeError(
                        "FFmpeg not installed. Please install FFmpeg: "
                        "https://ffmpeg.org/download.html"
                    )
        except Exception as e:
            logger.error(f"FFmpeg check failed: {e}")
            raise RuntimeError(str(e))
    
    def _generate_ffmpeg_error_message(self, status) -> str:
        """Generate FFmpeg error message"""
        if not status.is_installed:
            msg = "FFmpeg is not installed"
            if status.installation_guide:
                guide = status.installation_guide
                msg += f"\n\nPlease install FFmpeg ({guide.os_type}):\n"
                msg += "\n".join(guide.commands)
                if guide.download_url:
                    msg += f"\n\nDownload: {guide.download_url}"
                if guide.notes:
                    msg += f"\n\nNotes:\n" + "\n".join(f"- {note}" for note in guide.notes)
            return msg
        elif not status.is_version_supported:
            msg = f"FFmpeg version too old ({status.version}), please upgrade to latest version"
            if status.installation_guide:
                guide = status.installation_guide
                msg += f"\n\nUpgrade method:\n"
                msg += "\n".join(guide.commands)
            return msg
        else:
            return "FFmpeg check failed"
        
        return msg
    
    def get_video_info(self, input_path: str) -> VideoInfo:
        """
        Get video information
        
        Args:
            input_path: Input video path
            
        Returns:
            VideoInfo object
        """
        self._check_ffmpeg()  # Check only when used
        try:
            probe = ffmpeg.probe(input_path)
            video_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'video'),
                None
            )
            audio_stream = next(
                (s for s in probe['streams'] if s['codec_type'] == 'audio'),
                None
            )
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            video_stream['has_audio'] = audio_stream is not None
            video_stream['duration'] = probe['format'].get('duration', 0)
            
            return VideoInfo(video_stream)
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise
    
    def generate_thumbnail(
        self,
        input_path: str,
        timestamp: float,
        output_path: str,
        width: int = 320
    ) -> str:
        """
        Generate video thumbnail
        
        Args:
            input_path: Input video path
            timestamp: Time point (seconds)
            output_path: Output image path
            width: Thumbnail width
            
        Returns:
            Output file path
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            (
                ffmpeg
                .input(input_path, ss=timestamp)
                .filter('scale', width, -1)
                .output(output_path, vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Thumbnail generated: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
    
    def trim_video(
        self,
        input_path: str,
        start: float,
        end: float,
        output_path: str,
        copy_codec: bool = False
    ) -> str:
        """
        Trim video segment
        
        Args:
            input_path: Input video path
            start: Start time (seconds)
            end: End time (seconds)
            output_path: Output video path
            copy_codec: Whether to use copy mode (fast but not precise)
            
        Returns:
            Output file path
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            duration = end - start
            
            if copy_codec:
                # Fast mode: direct copy encoding (may not be precise)
                (
                    ffmpeg
                    .input(input_path, ss=start, t=duration)
                    .output(output_path, c='copy')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            else:
                # Precise mode: re-encode
                (
                    ffmpeg
                    .input(input_path, ss=start, t=duration)
                    .output(output_path)
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            
            logger.info(f"Video trimmed: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
    
    def concat_videos(
        self,
        video_paths: List[str],
        output_path: str,
        transition_duration: float = 0.0
    ) -> str:
        """
        Concatenate multiple videos
        
        Args:
            video_paths: List of input video paths
            output_path: Output video path
            transition_duration: Transition duration (seconds)
            
        Returns:
            Output file path
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            if len(video_paths) == 0:
                raise ValueError("No videos to concat")
            
            if len(video_paths) == 1:
                # Only one video, direct copy
                import shutil
                shutil.copy2(video_paths[0], output_path)
                return output_path
            
            # Create concat file list
            concat_file = output_path + '.concat.txt'
            with open(concat_file, 'w', encoding='utf-8') as f:
                for path in video_paths:
                    # Use absolute path
                    abs_path = os.path.abspath(path)
                    f.write(f"file '{abs_path}'\n")
            
            try:
                # Use concat demuxer to concatenate
                (
                    ffmpeg
                    .input(concat_file, format='concat', safe=0)
                    .output(output_path, c='copy')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
            finally:
                # Clean up temporary files
                if os.path.exists(concat_file):
                    os.remove(concat_file)
            
            logger.info(f"Videos concatenated: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise

    def add_transition(
        self,
        video1_path: str,
        video2_path: str,
        transition_type: str,
        duration: float,
        output_path: str
    ) -> str:
        """
        Add transition effect between two videos
        
        Args:
            video1_path: First video path
            video2_path: Second video path
            transition_type: Transition type (fade, wipe, dissolve)
            duration: Transition duration (seconds)
            output_path: Output video path
            
        Returns:
            Output file path
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get video information
            info1 = self.get_video_info(video1_path)
            info2 = self.get_video_info(video2_path)
            
            # Load two videos
            v1 = ffmpeg.input(video1_path)
            v2 = ffmpeg.input(video2_path)
            
            if transition_type == 'fade':
                # Fade in/out transition
                # First video fade out
                v1_fade = v1.video.filter(
                    'fade',
                    type='out',
                    start_time=info1.duration - duration,
                    duration=duration
                )
                # Second video fade in
                v2_fade = v2.video.filter(
                    'fade',
                    type='in',
                    start_time=0,
                    duration=duration
                )
                
                # Concatenate
                video = ffmpeg.concat(v1_fade, v2_fade, v=1, a=0)
                audio = ffmpeg.concat(v1.audio, v2.audio, v=0, a=1)
                
            elif transition_type == 'dissolve':
                # Dissolve transition (cross fade)
                # Use xfade filter
                video = ffmpeg.filter(
                    [v1.video, v2.video],
                    'xfade',
                    transition='fade',
                    duration=duration,
                    offset=info1.duration - duration
                )
                audio = ffmpeg.concat(v1.audio, v2.audio, v=0, a=1)
                
            elif transition_type == 'wipe':
                # Wipe transition
                video = ffmpeg.filter(
                    [v1.video, v2.video],
                    'xfade',
                    transition='wipeleft',
                    duration=duration,
                    offset=info1.duration - duration
                )
                audio = ffmpeg.concat(v1.audio, v2.audio, v=0, a=1)
                
            else:
                raise ValueError(f"Unknown transition type: {transition_type}")
            
            # Output
            (
                ffmpeg
                .output(video, audio, output_path)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Transition added: {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
    
    def get_duration(self, input_path: str) -> float:
        """
        Get video duration
        
        Args:
            input_path: Input video path
            
        Returns:
            Duration (seconds)
        """
        info = self.get_video_info(input_path)
        return info.duration


# Global instance
ffmpeg_wrapper = FFmpegWrapper()