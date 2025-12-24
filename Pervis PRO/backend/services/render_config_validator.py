"""
渲染配置参数验证器
验证渲染选项的有效性和兼容性
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    ERROR = "error"      # 严重错误，无法继续
    WARNING = "warning"  # 警告，可以继续但可能有问题
    INFO = "info"        # 信息提示


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    
    def add_message(self, level: ValidationLevel, message: str):
        """添加验证消息"""
        if level == ValidationLevel.ERROR:
            self.errors.append(message)
            self.is_valid = False
        elif level == ValidationLevel.WARNING:
            self.warnings.append(message)
        elif level == ValidationLevel.INFO:
            self.info.append(message)
    
    def get_all_messages(self) -> List[str]:
        """获取所有消息"""
        messages = []
        for error in self.errors:
            messages.append(f"错误: {error}")
        for warning in self.warnings:
            messages.append(f"警告: {warning}")
        for info in self.info:
            messages.append(f"信息: {info}")
        return messages


class RenderConfigValidator:
    """渲染配置验证器"""
    
    # 支持的格式和选项
    SUPPORTED_FORMATS = {
        'mp4': {
            'codecs': ['h264', 'h265', 'av1'],
            'containers': ['mp4'],
            'max_bitrate': 100000,  # kbps
            'audio_codecs': ['aac', 'mp3']
        },
        'mov': {
            'codecs': ['h264', 'h265', 'prores'],
            'containers': ['mov'],
            'max_bitrate': 200000,
            'audio_codecs': ['aac', 'pcm']
        },
        'avi': {
            'codecs': ['h264', 'xvid'],
            'containers': ['avi'],
            'max_bitrate': 50000,
            'audio_codecs': ['mp3', 'pcm']
        },
        'webm': {
            'codecs': ['vp8', 'vp9', 'av1'],
            'containers': ['webm'],
            'max_bitrate': 50000,
            'audio_codecs': ['vorbis', 'opus']
        }
    }
    
    SUPPORTED_RESOLUTIONS = {
        '480p': (854, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080),
        '1440p': (2560, 1440),
        '4k': (3840, 2160),
        '8k': (7680, 4320)
    }
    
    SUPPORTED_FRAMERATES = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120]
    
    QUALITY_PRESETS = {
        'low': {'crf': 28, 'preset': 'fast', 'bitrate_factor': 0.5},
        'medium': {'crf': 23, 'preset': 'medium', 'bitrate_factor': 1.0},
        'high': {'crf': 18, 'preset': 'slow', 'bitrate_factor': 1.5},
        'ultra': {'crf': 15, 'preset': 'slower', 'bitrate_factor': 2.0}
    }
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def validate_render_options(self, options: Dict[str, Any]) -> ValidationResult:
        """
        验证渲染选项
        
        Args:
            options: 渲染选项字典
            
        Returns:
            ValidationResult对象
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], info=[])
        
        try:
            # 验证必需字段
            self._validate_required_fields(options, result)
            
            # 验证格式
            self._validate_format(options, result)
            
            # 验证分辨率
            self._validate_resolution(options, result)
            
            # 验证帧率
            self._validate_framerate(options, result)
            
            # 验证质量设置
            self._validate_quality(options, result)
            
            # 验证比特率
            self._validate_bitrate(options, result)
            
            # 验证音频设置
            self._validate_audio_settings(options, result)
            
            # 验证兼容性
            self._validate_compatibility(options, result)
            
            # 验证性能影响
            self._validate_performance_impact(options, result)
            
        except Exception as e:
            result.add_message(ValidationLevel.ERROR, f"验证过程中发生错误: {str(e)}")
            logger.error(f"Render config validation error: {e}")
        
        return result
    
    def _validate_required_fields(self, options: Dict[str, Any], result: ValidationResult):
        """验证必需字段"""
        required_fields = ['format', 'resolution', 'framerate']
        
        for field in required_fields:
            if field not in options or options[field] is None:
                result.add_message(ValidationLevel.ERROR, f"缺少必需字段: {field}")
    
    def _validate_format(self, options: Dict[str, Any], result: ValidationResult):
        """验证输出格式"""
        format_value = options.get('format', '').lower()
        
        if not format_value:
            return
        
        if format_value not in self.SUPPORTED_FORMATS:
            result.add_message(
                ValidationLevel.ERROR,
                f"不支持的格式: {format_value}。支持的格式: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )
            return
        
        # 检查编解码器兼容性
        codec = options.get('codec', 'h264').lower()
        format_info = self.SUPPORTED_FORMATS[format_value]
        
        if codec not in format_info['codecs']:
            result.add_message(
                ValidationLevel.WARNING,
                f"编解码器 {codec} 可能与格式 {format_value} 不兼容。推荐: {', '.join(format_info['codecs'])}"
            )
    
    def _validate_resolution(self, options: Dict[str, Any], result: ValidationResult):
        """验证分辨率"""
        resolution = options.get('resolution', '').lower()
        
        if not resolution:
            return
        
        # 支持预设分辨率
        if resolution in self.SUPPORTED_RESOLUTIONS:
            width, height = self.SUPPORTED_RESOLUTIONS[resolution]
            result.add_message(ValidationLevel.INFO, f"分辨率: {width}x{height}")
            return
        
        # 支持自定义分辨率 (如 "1920x1080")
        if 'x' in resolution:
            try:
                width_str, height_str = resolution.split('x')
                width, height = int(width_str), int(height_str)
                
                # 验证分辨率范围
                if width < 320 or height < 240:
                    result.add_message(ValidationLevel.ERROR, "分辨率过低，最小支持320x240")
                elif width > 7680 or height > 4320:
                    result.add_message(ValidationLevel.WARNING, "分辨率过高，可能导致性能问题")
                
                # 验证宽高比
                aspect_ratio = width / height
                common_ratios = [16/9, 4/3, 21/9, 1/1]
                
                if not any(abs(aspect_ratio - ratio) < 0.1 for ratio in common_ratios):
                    result.add_message(ValidationLevel.WARNING, f"非标准宽高比: {aspect_ratio:.2f}")
                
            except ValueError:
                result.add_message(ValidationLevel.ERROR, f"无效的分辨率格式: {resolution}")
        else:
            result.add_message(ValidationLevel.ERROR, f"不支持的分辨率: {resolution}")
    
    def _validate_framerate(self, options: Dict[str, Any], result: ValidationResult):
        """验证帧率"""
        framerate = options.get('framerate')
        
        if framerate is None:
            return
        
        try:
            fps = float(framerate)
            
            if fps <= 0:
                result.add_message(ValidationLevel.ERROR, "帧率必须大于0")
                return
            
            if fps > 240:
                result.add_message(ValidationLevel.WARNING, "帧率过高，可能导致文件过大")
            elif fps < 15:
                result.add_message(ValidationLevel.WARNING, "帧率过低，可能影响播放流畅度")
            
            # 检查是否为标准帧率
            if fps not in self.SUPPORTED_FRAMERATES:
                closest_fps = min(self.SUPPORTED_FRAMERATES, key=lambda x: abs(x - fps))
                result.add_message(
                    ValidationLevel.INFO,
                    f"非标准帧率 {fps}，建议使用 {closest_fps}"
                )
            
        except (ValueError, TypeError):
            result.add_message(ValidationLevel.ERROR, f"无效的帧率值: {framerate}")
    
    def _validate_quality(self, options: Dict[str, Any], result: ValidationResult):
        """验证质量设置"""
        quality = options.get('quality', '').lower()
        
        if not quality:
            return
        
        if quality not in self.QUALITY_PRESETS:
            result.add_message(
                ValidationLevel.WARNING,
                f"未知的质量预设: {quality}。支持的预设: {', '.join(self.QUALITY_PRESETS.keys())}"
            )
            return
        
        # 根据质量预设提供建议
        preset_info = self.QUALITY_PRESETS[quality]
        if quality == 'ultra':
            result.add_message(ValidationLevel.INFO, "超高质量设置将显著增加渲染时间和文件大小")
        elif quality == 'low':
            result.add_message(ValidationLevel.INFO, "低质量设置适合快速预览，不建议用于最终输出")
    
    def _validate_bitrate(self, options: Dict[str, Any], result: ValidationResult):
        """验证比特率"""
        bitrate = options.get('bitrate')
        audio_bitrate = options.get('audio_bitrate')
        format_value = options.get('format', '').lower()
        
        # 验证视频比特率
        if bitrate is not None:
            try:
                video_bitrate = int(bitrate)
                
                if video_bitrate <= 0:
                    result.add_message(ValidationLevel.ERROR, "视频比特率必须大于0")
                elif video_bitrate < 500:
                    result.add_message(ValidationLevel.WARNING, "视频比特率过低，可能影响画质")
                elif video_bitrate > 100000:
                    result.add_message(ValidationLevel.WARNING, "视频比特率过高，文件将非常大")
                
                # 检查格式限制
                if format_value in self.SUPPORTED_FORMATS:
                    max_bitrate = self.SUPPORTED_FORMATS[format_value]['max_bitrate']
                    if video_bitrate > max_bitrate:
                        result.add_message(
                            ValidationLevel.WARNING,
                            f"比特率 {video_bitrate} 超过格式 {format_value} 的建议最大值 {max_bitrate}"
                        )
                
            except (ValueError, TypeError):
                result.add_message(ValidationLevel.ERROR, f"无效的视频比特率: {bitrate}")
        
        # 验证音频比特率
        if audio_bitrate is not None:
            try:
                audio_br = int(audio_bitrate)
                
                if audio_br <= 0:
                    result.add_message(ValidationLevel.ERROR, "音频比特率必须大于0")
                elif audio_br < 64:
                    result.add_message(ValidationLevel.WARNING, "音频比特率过低，可能影响音质")
                elif audio_br > 512:
                    result.add_message(ValidationLevel.WARNING, "音频比特率过高，通常不必要")
                
            except (ValueError, TypeError):
                result.add_message(ValidationLevel.ERROR, f"无效的音频比特率: {audio_bitrate}")
    
    def _validate_audio_settings(self, options: Dict[str, Any], result: ValidationResult):
        """验证音频设置"""
        audio_codec = options.get('audio_codec', '').lower()
        format_value = options.get('format', '').lower()
        
        if audio_codec and format_value in self.SUPPORTED_FORMATS:
            supported_audio = self.SUPPORTED_FORMATS[format_value]['audio_codecs']
            
            if audio_codec not in supported_audio:
                result.add_message(
                    ValidationLevel.WARNING,
                    f"音频编解码器 {audio_codec} 可能与格式 {format_value} 不兼容。推荐: {', '.join(supported_audio)}"
                )
    
    def _validate_compatibility(self, options: Dict[str, Any], result: ValidationResult):
        """验证选项兼容性"""
        format_value = options.get('format', '').lower()
        resolution = options.get('resolution', '').lower()
        quality = options.get('quality', '').lower()
        
        # 检查高分辨率与格式的兼容性
        if resolution in ['4k', '8k'] and format_value in ['avi']:
            result.add_message(
                ValidationLevel.WARNING,
                f"格式 {format_value} 不适合高分辨率 {resolution}，建议使用 mp4 或 mov"
            )
        
        # 检查质量与分辨率的匹配
        if quality == 'low' and resolution in ['4k', '8k']:
            result.add_message(
                ValidationLevel.WARNING,
                "高分辨率配合低质量设置可能无法发挥分辨率优势"
            )
    
    def _validate_performance_impact(self, options: Dict[str, Any], result: ValidationResult):
        """验证性能影响"""
        resolution = options.get('resolution', '').lower()
        quality = options.get('quality', '').lower()
        framerate = options.get('framerate', 30)
        
        # 计算复杂度分数
        complexity_score = 0
        
        # 分辨率影响
        if resolution in ['4k', '8k']:
            complexity_score += 3
        elif resolution in ['1440p']:
            complexity_score += 2
        elif resolution in ['1080p']:
            complexity_score += 1
        
        # 质量影响
        if quality == 'ultra':
            complexity_score += 3
        elif quality == 'high':
            complexity_score += 2
        elif quality == 'medium':
            complexity_score += 1
        
        # 帧率影响
        try:
            fps = float(framerate)
            if fps >= 60:
                complexity_score += 2
            elif fps >= 30:
                complexity_score += 1
        except (ValueError, TypeError):
            pass
        
        # 提供性能建议
        if complexity_score >= 6:
            result.add_message(
                ValidationLevel.WARNING,
                "当前设置复杂度很高，渲染时间可能很长，建议确保有足够的系统资源"
            )
        elif complexity_score >= 4:
            result.add_message(
                ValidationLevel.INFO,
                "当前设置复杂度中等，渲染时间可能较长"
            )
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """加载验证规则"""
        return {
            'max_file_size_gb': 50,
            'max_duration_hours': 24,
            'min_disk_space_gb': 10,
            'recommended_ram_gb': 8
        }
    
    def get_recommended_settings(self, use_case: str) -> Dict[str, Any]:
        """
        根据使用场景获取推荐设置
        
        Args:
            use_case: 使用场景 (preview, web, broadcast, archive)
            
        Returns:
            推荐的渲染设置
        """
        recommendations = {
            'preview': {
                'format': 'mp4',
                'resolution': '720p',
                'framerate': 30,
                'quality': 'medium',
                'bitrate': 2000,
                'audio_bitrate': 128
            },
            'web': {
                'format': 'mp4',
                'resolution': '1080p',
                'framerate': 30,
                'quality': 'high',
                'bitrate': 5000,
                'audio_bitrate': 192
            },
            'broadcast': {
                'format': 'mov',
                'resolution': '1080p',
                'framerate': 25,
                'quality': 'ultra',
                'bitrate': 15000,
                'audio_bitrate': 256
            },
            'archive': {
                'format': 'mov',
                'resolution': '4k',
                'framerate': 24,
                'quality': 'ultra',
                'bitrate': 50000,
                'audio_bitrate': 320
            }
        }
        
        return recommendations.get(use_case, recommendations['web'])
    
    def estimate_file_size(self, options: Dict[str, Any], duration_seconds: float) -> Dict[str, float]:
        """
        估算输出文件大小
        
        Args:
            options: 渲染选项
            duration_seconds: 视频时长（秒）
            
        Returns:
            文件大小估算信息
        """
        try:
            video_bitrate = int(options.get('bitrate', 5000))  # kbps
            audio_bitrate = int(options.get('audio_bitrate', 192))  # kbps
            
            # 计算文件大小 (MB)
            video_size_mb = (video_bitrate * duration_seconds) / (8 * 1024)
            audio_size_mb = (audio_bitrate * duration_seconds) / (8 * 1024)
            total_size_mb = video_size_mb + audio_size_mb
            
            return {
                'video_size_mb': round(video_size_mb, 2),
                'audio_size_mb': round(audio_size_mb, 2),
                'total_size_mb': round(total_size_mb, 2),
                'total_size_gb': round(total_size_mb / 1024, 2)
            }
            
        except (ValueError, TypeError) as e:
            logger.error(f"File size estimation error: {e}")
            return {
                'video_size_mb': 0,
                'audio_size_mb': 0,
                'total_size_mb': 0,
                'total_size_gb': 0
            }


# 全局实例
render_config_validator = RenderConfigValidator()