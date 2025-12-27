"""
FFmpeg检测和诊断服务
检测系统中FFmpeg的安装状态、版本信息，并提供安装指导
"""

import subprocess
import platform
import os
import re
from typing import Optional, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FFmpegStatus:
    """FFmpeg状态数据类"""
    is_installed: bool
    version: Optional[str] = None
    path: Optional[str] = None
    is_version_supported: bool = False
    installation_guide: Optional['InstallationGuide'] = None


@dataclass
class InstallationGuide:
    """安装指导数据类"""
    os_type: str
    method: str  # "package_manager", "binary", "source"
    commands: List[str]
    download_url: Optional[str] = None
    notes: List[str] = None
    
    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class InstallationGuideGenerator:
    """安装指导生成器"""
    
    # 下载链接
    DOWNLOAD_LINKS = {
        "windows": "https://ffmpeg.org/download.html#build-windows",
        "macos": "https://ffmpeg.org/download.html#build-mac",
        "linux": "https://ffmpeg.org/download.html#build-linux"
    }
    
    # 包管理器命令
    PACKAGE_MANAGER_COMMANDS = {
        "windows": {
            "chocolatey": ["choco install ffmpeg"],
            "winget": ["winget install Gyan.FFmpeg"],
            "scoop": ["scoop install ffmpeg"]
        },
        "macos": {
            "homebrew": ["brew install ffmpeg"],
            "macports": ["sudo port install ffmpeg"]
        },
        "linux": {
            "ubuntu": ["sudo apt update", "sudo apt install ffmpeg"],
            "centos": ["sudo yum install epel-release", "sudo yum install ffmpeg"],
            "fedora": ["sudo dnf install ffmpeg"],
            "arch": ["sudo pacman -S ffmpeg"]
        }
    }
    
    def generate_guide(self, os_type: str) -> InstallationGuide:
        """
        生成针对特定操作系统的安装指导
        
        Args:
            os_type: 操作系统类型 (windows, macos, linux)
            
        Returns:
            InstallationGuide对象
        """
        os_type = os_type.lower()
        
        if os_type == "windows":
            return self._generate_windows_guide()
        elif os_type == "macos":
            return self._generate_macos_guide()
        elif os_type == "linux":
            return self._generate_linux_guide()
        else:
            return self._generate_generic_guide()
    
    def _generate_windows_guide(self) -> InstallationGuide:
        """生成Windows安装指导"""
        commands = [
            "# 方法1: 使用Chocolatey (推荐)",
            "choco install ffmpeg",
            "",
            "# 方法2: 使用Winget",
            "winget install Gyan.FFmpeg",
            "",
            "# 方法3: 手动安装",
            "# 1. 访问 https://ffmpeg.org/download.html#build-windows",
            "# 2. 下载Windows版本的FFmpeg",
            "# 3. 解压到 C:\\ffmpeg",
            "# 4. 将 C:\\ffmpeg\\bin 添加到系统PATH环境变量"
        ]
        
        notes = [
            "安装后需要重启命令行或IDE以使PATH生效",
            "推荐使用Chocolatey包管理器进行安装",
            "如果没有包管理器，可以手动下载并配置PATH"
        ]
        
        return InstallationGuide(
            os_type="windows",
            method="package_manager",
            commands=commands,
            download_url=self.DOWNLOAD_LINKS["windows"],
            notes=notes
        )
    
    def _generate_macos_guide(self) -> InstallationGuide:
        """生成macOS安装指导"""
        commands = [
            "# 方法1: 使用Homebrew (推荐)",
            "brew install ffmpeg",
            "",
            "# 方法2: 使用MacPorts",
            "sudo port install ffmpeg",
            "",
            "# 如果没有Homebrew，先安装:",
            '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        ]
        
        notes = [
            "推荐使用Homebrew包管理器",
            "安装Homebrew需要Xcode命令行工具",
            "安装完成后FFmpeg会自动添加到PATH"
        ]
        
        return InstallationGuide(
            os_type="macos",
            method="package_manager",
            commands=commands,
            download_url=self.DOWNLOAD_LINKS["macos"],
            notes=notes
        )
    
    def _generate_linux_guide(self) -> InstallationGuide:
        """生成Linux安装指导"""
        commands = [
            "# Ubuntu/Debian:",
            "sudo apt update && sudo apt install ffmpeg",
            "",
            "# CentOS/RHEL:",
            "sudo yum install epel-release && sudo yum install ffmpeg",
            "",
            "# Fedora:",
            "sudo dnf install ffmpeg",
            "",
            "# Arch Linux:",
            "sudo pacman -S ffmpeg"
        ]
        
        notes = [
            "选择适合你的Linux发行版的命令",
            "某些发行版可能需要启用额外的软件源",
            "安装完成后FFmpeg会自动添加到PATH"
        ]
        
        return InstallationGuide(
            os_type="linux",
            method="package_manager",
            commands=commands,
            download_url=self.DOWNLOAD_LINKS["linux"],
            notes=notes
        )
    
    def _generate_generic_guide(self) -> InstallationGuide:
        """生成通用安装指导"""
        commands = [
            "# 请访问FFmpeg官方网站下载适合您系统的版本:",
            "# https://ffmpeg.org/download.html",
            "",
            "# 下载后请确保FFmpeg可执行文件在系统PATH中"
        ]
        
        notes = [
            "请根据您的操作系统选择合适的安装方法",
            "安装后需要确保ffmpeg命令可以在终端中执行"
        ]
        
        return InstallationGuide(
            os_type="unknown",
            method="manual",
            commands=commands,
            download_url="https://ffmpeg.org/download.html",
            notes=notes
        )
    
    def get_download_links(self) -> Dict[str, str]:
        """获取所有平台的下载链接"""
        return self.DOWNLOAD_LINKS.copy()
    
    def get_package_manager_commands(self) -> Dict[str, Dict[str, List[str]]]:
        """获取所有平台的包管理器命令"""
        return self.PACKAGE_MANAGER_COMMANDS.copy()


class FFmpegDetector:
    """FFmpeg检测器"""
    
    # 支持的最低版本
    MIN_VERSION = "4.0.0"
    
    def __init__(self):
        self.guide_generator = InstallationGuideGenerator()
    
    def check_installation(self) -> FFmpegStatus:
        """
        检查FFmpeg安装状态
        
        Returns:
            FFmpegStatus对象
        """
        try:
            # 检查FFmpeg是否在PATH中
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # FFmpeg已安装，解析版本信息
                version = self._parse_version(result.stdout)
                path = self._get_ffmpeg_path()
                is_supported = self.validate_version(version, self.MIN_VERSION)
                
                status = FFmpegStatus(
                    is_installed=True,
                    version=version,
                    path=path,
                    is_version_supported=is_supported
                )
                
                # 如果版本不支持，提供升级指导
                if not is_supported:
                    status.installation_guide = self._get_upgrade_guide()
                
                logger.info(f"FFmpeg detected: version {version}, path {path}")
                return status
            else:
                # FFmpeg命令执行失败
                return self._create_not_installed_status()
                
        except FileNotFoundError:
            # FFmpeg命令不存在
            logger.warning("FFmpeg not found in PATH")
            return self._create_not_installed_status()
        except subprocess.TimeoutExpired:
            # 命令超时
            logger.error("FFmpeg version check timed out")
            return self._create_not_installed_status()
        except Exception as e:
            # 其他错误
            logger.error(f"Error checking FFmpeg installation: {e}")
            return self._create_not_installed_status()
    
    def _parse_version(self, version_output: str) -> Optional[str]:
        """
        从FFmpeg版本输出中解析版本号
        
        Args:
            version_output: FFmpeg -version命令的输出
            
        Returns:
            版本号字符串，如 "4.4.2"
        """
        try:
            # 匹配版本号模式，如 "ffmpeg version 4.4.2" 或 "ffmpeg version n4.4.4-161-ge4c06648f5"
            match = re.search(r'ffmpeg version n?(\d+\.\d+(?:\.\d+)?)', version_output)
            if match:
                return match.group(1)
            
            # 备用模式，匹配任何数字.数字格式
            match = re.search(r'version n?(\d+\.\d+(?:\.\d+)?)', version_output)
            if match:
                return match.group(1)
                
            return None
        except Exception as e:
            logger.error(f"Error parsing FFmpeg version: {e}")
            return None
    
    def _get_ffmpeg_path(self) -> Optional[str]:
        """
        获取FFmpeg可执行文件的路径
        
        Returns:
            FFmpeg可执行文件路径
        """
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['where', 'ffmpeg'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                result = subprocess.run(
                    ['which', 'ffmpeg'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
            return None
        except Exception as e:
            logger.error(f"Error getting FFmpeg path: {e}")
            return None
    
    def validate_version(self, version: Optional[str], min_version: str) -> bool:
        """
        验证FFmpeg版本是否满足最低要求
        
        Args:
            version: 当前版本
            min_version: 最低版本要求
            
        Returns:
            是否满足版本要求
        """
        if not version:
            return False
        
        try:
            current_parts = [int(x) for x in version.split('.')]
            min_parts = [int(x) for x in min_version.split('.')]
            
            # 补齐版本号长度
            max_len = max(len(current_parts), len(min_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            min_parts.extend([0] * (max_len - len(min_parts)))
            
            # 比较版本号
            for current, minimum in zip(current_parts, min_parts):
                if current > minimum:
                    return True
                elif current < minimum:
                    return False
            
            return True  # 版本相等
        except Exception as e:
            logger.error(f"Error validating version: {e}")
            return False
    
    def _create_not_installed_status(self) -> FFmpegStatus:
        """创建FFmpeg未安装的状态对象"""
        os_type = self._detect_os_type()
        installation_guide = self.guide_generator.generate_guide(os_type)
        
        return FFmpegStatus(
            is_installed=False,
            installation_guide=installation_guide
        )
    
    def _get_upgrade_guide(self) -> InstallationGuide:
        """获取升级指导"""
        os_type = self._detect_os_type()
        guide = self.guide_generator.generate_guide(os_type)
        
        # 修改指导信息为升级提示
        guide.notes.insert(0, f"检测到FFmpeg版本过低，建议升级到 {self.MIN_VERSION} 或更高版本")
        
        return guide
    
    def _detect_os_type(self) -> str:
        """检测操作系统类型"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            return "unknown"
    
    def get_installation_guide(self, os_type: Optional[str] = None) -> InstallationGuide:
        """
        获取安装指导
        
        Args:
            os_type: 操作系统类型，如果不提供则自动检测
            
        Returns:
            InstallationGuide对象
        """
        if not os_type:
            os_type = self._detect_os_type()
        
        return self.guide_generator.generate_guide(os_type)
    
    def get_version(self) -> Optional[str]:
        """
        获取FFmpeg版本号
        
        Returns:
            版本号字符串
        """
        status = self.check_installation()
        return status.version if status.is_installed else None
    
    def is_available(self) -> bool:
        """
        检查FFmpeg是否可用
        
        Returns:
            是否可用
        """
        status = self.check_installation()
        return status.is_installed and status.is_version_supported


# 全局实例
ffmpeg_detector = FFmpegDetector()
