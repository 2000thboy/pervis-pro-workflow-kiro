"""
增强的错误处理器
提供用户友好的错误信息和解决方案
"""

import logging
import traceback
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举"""
    FFMPEG_NOT_FOUND = "ffmpeg_not_found"
    FFMPEG_VERSION_LOW = "ffmpeg_version_low"
    FFMPEG_EXECUTION_FAILED = "ffmpeg_execution_failed"
    DISK_SPACE_INSUFFICIENT = "disk_space_insufficient"
    MEMORY_INSUFFICIENT = "memory_insufficient"
    FILE_NOT_FOUND = "file_not_found"
    FILE_PERMISSION_DENIED = "file_permission_denied"
    UNSUPPORTED_FORMAT = "unsupported_format"
    NETWORK_STORAGE_ERROR = "network_storage_error"
    INVALID_CONFIGURATION = "invalid_configuration"
    TIMELINE_EMPTY = "timeline_empty"
    ASSET_MISSING = "asset_missing"
    RENDER_TIMEOUT = "render_timeout"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class UserFriendlyError:
    """用户友好错误数据类"""
    error_code: str
    title: str
    message: str
    solutions: List[str]
    documentation_link: Optional[str] = None
    is_recoverable: bool = True
    technical_details: Optional[str] = None


class EnhancedErrorHandler:
    """增强的错误处理器"""
    
    # 错误信息模板
    ERROR_TEMPLATES = {
        ErrorType.FFMPEG_NOT_FOUND: {
            "title": "FFmpeg未安装",
            "message": "系统中未检测到FFmpeg，这是视频处理的必需组件。",
            "solutions": [
                "请按照系统提供的安装指导安装FFmpeg",
                "安装完成后重启应用程序",
                "确认FFmpeg已添加到系统PATH环境变量"
            ],
            "documentation_link": "https://ffmpeg.org/download.html",
            "is_recoverable": True
        },
        ErrorType.FFMPEG_VERSION_LOW: {
            "title": "FFmpeg版本过低",
            "message": "检测到的FFmpeg版本不满足最低要求，可能导致某些功能无法正常工作。",
            "solutions": [
                "请升级FFmpeg到最新版本",
                "使用包管理器更新: brew upgrade ffmpeg (macOS) 或 choco upgrade ffmpeg (Windows)",
                "或从官网下载最新版本手动安装"
            ],
            "documentation_link": "https://ffmpeg.org/download.html",
            "is_recoverable": True
        },
        ErrorType.FFMPEG_EXECUTION_FAILED: {
            "title": "视频处理失败",
            "message": "FFmpeg在处理视频时遇到错误，可能是文件格式不兼容或参数设置问题。",
            "solutions": [
                "检查视频文件是否损坏或格式不支持",
                "尝试降低输出质量设置",
                "确保有足够的磁盘空间和内存",
                "检查文件路径中是否包含特殊字符"
            ],
            "is_recoverable": True
        },
        ErrorType.DISK_SPACE_INSUFFICIENT: {
            "title": "磁盘空间不足",
            "message": "可用磁盘空间不足以完成视频渲染，需要更多存储空间。",
            "solutions": [
                "清理磁盘空间，删除不需要的文件",
                "选择其他磁盘作为输出位置",
                "降低视频质量设置以减少文件大小",
                "使用代理文件模式进行编辑"
            ],
            "is_recoverable": True
        },
        ErrorType.MEMORY_INSUFFICIENT: {
            "title": "内存不足",
            "message": "系统内存不足以处理当前的视频渲染任务。",
            "solutions": [
                "关闭其他不必要的应用程序",
                "启用代理文件模式以降低内存使用",
                "降低视频分辨率和质量设置",
                "分段处理长视频"
            ],
            "is_recoverable": True
        },
        ErrorType.FILE_NOT_FOUND: {
            "title": "文件未找到",
            "message": "无法找到指定的视频文件，文件可能已被移动或删除。",
            "solutions": [
                "检查文件是否存在于原始位置",
                "重新导入缺失的素材文件",
                "检查网络连接（如果文件在网络存储上）",
                "从备份中恢复文件"
            ],
            "is_recoverable": True
        },
        ErrorType.FILE_PERMISSION_DENIED: {
            "title": "文件权限不足",
            "message": "没有足够的权限访问或修改指定的文件或目录。",
            "solutions": [
                "以管理员身份运行应用程序",
                "检查文件和目录的权限设置",
                "确保文件没有被其他程序占用",
                "选择有写入权限的输出目录"
            ],
            "is_recoverable": True
        },
        ErrorType.UNSUPPORTED_FORMAT: {
            "title": "不支持的文件格式",
            "message": "当前文件格式不被支持，无法进行处理。",
            "solutions": [
                "将文件转换为支持的格式（MP4、MOV等）",
                "使用其他视频转换工具预处理文件",
                "检查文件是否损坏",
                "联系技术支持获取格式支持信息"
            ],
            "is_recoverable": True
        },
        ErrorType.NETWORK_STORAGE_ERROR: {
            "title": "网络存储错误",
            "message": "无法访问网络存储位置，可能是网络连接问题。",
            "solutions": [
                "检查网络连接状态",
                "重新连接网络驱动器",
                "使用本地存储作为临时方案",
                "联系网络管理员检查存储服务"
            ],
            "is_recoverable": True
        },
        ErrorType.INVALID_CONFIGURATION: {
            "title": "配置参数无效",
            "message": "提供的渲染配置参数无效或不兼容。",
            "solutions": [
                "检查分辨率、帧率、比特率等参数设置",
                "使用预设的质量配置",
                "确保参数值在有效范围内",
                "重置为默认配置"
            ],
            "is_recoverable": True
        },
        ErrorType.TIMELINE_EMPTY: {
            "title": "时间轴为空",
            "message": "时间轴中没有任何视频片段，无法进行渲染。",
            "solutions": [
                "添加视频片段到时间轴",
                "检查片段是否正确导入",
                "确认时间轴配置正确",
                "重新创建时间轴"
            ],
            "is_recoverable": True
        },
        ErrorType.ASSET_MISSING: {
            "title": "素材文件缺失",
            "message": "时间轴中引用的部分素材文件无法找到。",
            "solutions": [
                "重新链接缺失的素材文件",
                "从原始位置重新导入素材",
                "检查素材文件路径是否正确",
                "使用替代素材文件"
            ],
            "is_recoverable": True
        },
        ErrorType.RENDER_TIMEOUT: {
            "title": "渲染超时",
            "message": "渲染任务执行时间过长，已被系统终止。",
            "solutions": [
                "降低视频质量和分辨率设置",
                "分段渲染长视频",
                "检查系统性能和资源使用情况",
                "使用更快的编码预设"
            ],
            "is_recoverable": True
        },
        ErrorType.UNKNOWN_ERROR: {
            "title": "未知错误",
            "message": "发生了未预期的错误，请查看技术详情或联系技术支持。",
            "solutions": [
                "重试操作",
                "重启应用程序",
                "检查系统日志获取更多信息",
                "联系技术支持并提供错误详情"
            ],
            "is_recoverable": True
        }
    }
    
    def handle_ffmpeg_error(self, error: Exception) -> UserFriendlyError:
        """
        处理FFmpeg相关错误
        
        Args:
            error: 原始异常对象
            
        Returns:
            用户友好的错误对象
        """
        error_type = self._classify_error(error)
        return self._create_user_friendly_error(error_type, error)
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """
        分类错误类型
        
        Args:
            error: 原始异常对象
            
        Returns:
            错误类型枚举
        """
        error_message = str(error).lower()
        
        # FFmpeg相关错误
        if "ffmpeg not found" in error_message or "ffmpeg not installed" in error_message:
            return ErrorType.FFMPEG_NOT_FOUND
        
        if "version" in error_message and ("low" in error_message or "old" in error_message):
            return ErrorType.FFMPEG_VERSION_LOW
        
        # 文件相关错误
        if isinstance(error, FileNotFoundError) or "no such file" in error_message:
            return ErrorType.FILE_NOT_FOUND
        
        if isinstance(error, PermissionError) or "permission denied" in error_message:
            return ErrorType.FILE_PERMISSION_DENIED
        
        # 资源相关错误
        if "disk" in error_message and ("space" in error_message or "full" in error_message):
            return ErrorType.DISK_SPACE_INSUFFICIENT
        
        if "memory" in error_message or "out of memory" in error_message:
            return ErrorType.MEMORY_INSUFFICIENT
        
        # 格式相关错误
        if "format" in error_message and ("unsupported" in error_message or "invalid" in error_message):
            return ErrorType.UNSUPPORTED_FORMAT
        
        # 网络相关错误
        if "network" in error_message or "connection" in error_message:
            return ErrorType.NETWORK_STORAGE_ERROR
        
        # 配置相关错误
        if "invalid" in error_message and ("config" in error_message or "parameter" in error_message):
            return ErrorType.INVALID_CONFIGURATION
        
        # 时间轴相关错误
        if "timeline" in error_message and "empty" in error_message:
            return ErrorType.TIMELINE_EMPTY
        
        if "asset" in error_message and ("missing" in error_message or "not found" in error_message):
            return ErrorType.ASSET_MISSING
        
        # 超时错误
        if "timeout" in error_message or isinstance(error, TimeoutError):
            return ErrorType.RENDER_TIMEOUT
        
        # FFmpeg执行错误
        if "ffmpeg" in error_message:
            return ErrorType.FFMPEG_EXECUTION_FAILED
        
        return ErrorType.UNKNOWN_ERROR
    
    def _create_user_friendly_error(self, error_type: ErrorType, original_error: Exception) -> UserFriendlyError:
        """
        创建用户友好的错误对象
        
        Args:
            error_type: 错误类型
            original_error: 原始异常
            
        Returns:
            用户友好的错误对象
        """
        template = self.ERROR_TEMPLATES.get(error_type, self.ERROR_TEMPLATES[ErrorType.UNKNOWN_ERROR])
        
        # 获取技术详情
        technical_details = self._get_technical_details(original_error)
        
        # 根据具体错误调整解决方案
        solutions = self._customize_solutions(error_type, original_error, template["solutions"])
        
        return UserFriendlyError(
            error_code=error_type.value,
            title=template["title"],
            message=template["message"],
            solutions=solutions,
            documentation_link=template.get("documentation_link"),
            is_recoverable=template.get("is_recoverable", True),
            technical_details=technical_details
        )
    
    def _get_technical_details(self, error: Exception) -> str:
        """
        获取技术详情
        
        Args:
            error: 原始异常
            
        Returns:
            技术详情字符串
        """
        return f"{type(error).__name__}: {str(error)}"
    
    def _customize_solutions(self, error_type: ErrorType, error: Exception, default_solutions: List[str]) -> List[str]:
        """
        根据具体错误定制解决方案
        
        Args:
            error_type: 错误类型
            error: 原始异常
            default_solutions: 默认解决方案
            
        Returns:
            定制的解决方案列表
        """
        solutions = default_solutions.copy()
        error_message = str(error).lower()
        
        # 根据具体错误信息添加特定解决方案
        if error_type == ErrorType.FFMPEG_EXECUTION_FAILED:
            if "codec" in error_message:
                solutions.insert(0, "尝试使用不同的视频编码器")
            if "resolution" in error_message:
                solutions.insert(0, "检查视频分辨率设置是否合理")
        
        elif error_type == ErrorType.FILE_NOT_FOUND:
            if "network" in error_message or "smb" in error_message:
                solutions.insert(0, "检查网络驱动器连接状态")
        
        elif error_type == ErrorType.DISK_SPACE_INSUFFICIENT:
            # 可以添加具体的空间需求信息
            if hasattr(error, 'required_space'):
                solutions.insert(0, f"至少需要 {error.required_space} MB 的可用空间")
        
        return solutions
    
    def generate_solution_suggestions(self, error_type: str) -> List[str]:
        """
        生成解决方案建议
        
        Args:
            error_type: 错误类型字符串
            
        Returns:
            解决方案列表
        """
        try:
            error_enum = ErrorType(error_type)
            template = self.ERROR_TEMPLATES.get(error_enum)
            return template["solutions"] if template else []
        except ValueError:
            return ["请联系技术支持获取帮助"]
    
    def log_diagnostic_info(self, context: Dict[str, Any]) -> None:
        """
        记录诊断信息
        
        Args:
            context: 上下文信息字典
        """
        try:
            logger.error("Diagnostic Information:", extra={
                "context": context,
                "timestamp": context.get("timestamp"),
                "user_id": context.get("user_id"),
                "operation": context.get("operation"),
                "error_details": context.get("error_details")
            })
        except Exception as e:
            logger.error(f"Failed to log diagnostic info: {e}")
    
    def is_recoverable_error(self, error: Exception) -> bool:
        """
        判断错误是否可恢复
        
        Args:
            error: 异常对象
            
        Returns:
            是否可恢复
        """
        error_type = self._classify_error(error)
        template = self.ERROR_TEMPLATES.get(error_type)
        return template.get("is_recoverable", True) if template else True
    
    def get_error_documentation_link(self, error_type: str) -> Optional[str]:
        """
        获取错误相关的文档链接
        
        Args:
            error_type: 错误类型字符串
            
        Returns:
            文档链接
        """
        try:
            error_enum = ErrorType(error_type)
            template = self.ERROR_TEMPLATES.get(error_enum)
            return template.get("documentation_link") if template else None
        except ValueError:
            return None


# 全局实例
enhanced_error_handler = EnhancedErrorHandler()
