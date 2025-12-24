import os
import sys
import socket
import subprocess
import time
import asyncio
import platform
from typing import Dict, List, Any
from  pathlib import Path

class SystemDetector:
    """
    启动器核心侦测服务 (Detection Service)
    负责在UI显示前扫描系统环境、网络状态和服务健康度
    """
    
    def __init__(self):
        self.system_info = {
            "os": platform.system(),
            "node": platform.node(),
            "status": "initializing"
        }
        self.services_status = {}
        self.storage_status = {}
        
    async def run_full_scan(self) -> Dict[str, Any]:
        """运行完整系统扫描"""
        scan_results = {
            "timestamp": time.time(),
            "overall_health": "unknown",
            "checks": {}
        }
        
        # 并行运行各项检查
        checks = await asyncio.gather(
            self.check_local_environment(),
            self.check_network_connectivity(),
            self.check_core_services()
        )
        
        scan_results["checks"]["local"] = checks[0]
        scan_results["checks"]["network"] = checks[1]
        scan_results["checks"]["services"] = checks[2]
        
        # 计算整体健康度
        scan_results["overall_health"] = self._calculate_health(checks)
        
        return scan_results
    
    async def check_local_environment(self) -> Dict[str, Any]:
        """检查本地环境配置"""
        results = {"status": "ok", "issues": []}
        
        # 1. 检查配置文件
        config_path = Path(".env")
        if not config_path.exists():
            results["issues"].append("缺少 .env 配置文件")
            results["status"] = "warning"
            
        # 2. 检查关键目录
        required_dirs = ["assets", "logs", "backend", "launcher"]
        for d in required_dirs:
            if not Path(d).exists():
                results["issues"].append(f"关键目录缺失: {d}")
        
        # 3. 检查Python环境 (简单检查)
        results["python_version"] = sys.version.split(" ")[0]
        
        return results

    async def check_network_connectivity(self) -> Dict[str, Any]:
        """检查网络和NAS连接"""
        results = {
            "internet": False,
            "nas_devices": []
        }
        
        # 1. 检查外网连通性 (Ping Google DNS / Baidu)
        # 简单起见，这里假设有网，实际部署可以用 aiohttp 请求一下
        try:
            # 可以在这里做实际请求，demo中先mock一下或者ping
            results["internet"] = True 
        except:
            pass
            
        # 2. 扫描已知的NAS路径
        # 从环境变量读取 NAS_PATHS (如果有)
        nas_paths = os.getenv("NAS_PATHS", "").split(";")
        # 添加一些默认测试路径
        if os.path.exists("Z:/"):
            nas_paths.append("Z:/Movies")
            
        for path in nas_paths:
            if not path: continue
            is_connected = await self._ping_path(path)
            results["nas_devices"].append({
                "path": path,
                "status": "online" if is_connected else "offline",
                "latency": "local" if ":" in path else "unknown" # 简单判断
            })
            
        return results

    async def check_all_drives(self) -> List[str]:
        """扫描所有可用盘符"""
        import string
        from ctypes import windll
        
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:")
            bitmask >>= 1
            
        return drives
        
    async def check_core_services(self) -> Dict[str, Any]:
        """侦测核心服务端口 (8000, 3000)"""
        services = {
            "Backend (API)": ("127.0.0.1", 8000),
            "DAM (API)": ("127.0.0.1", 8001),
            "Frontend (Web)": ("127.0.0.1", 3000),
            "Database": ("127.0.0.1", 5432) # Postgres example, MVP uses SQLite file so this might fail
        }
        
        status = {}
        
        for name, (host, port) in services.items():
            is_open = self._check_port(host, port)
            status[name] = "running" if is_open else "stopped"
            
        return status

    async def _ping_path(self, path: str) -> bool:
        """非阻塞检查路径是否存在"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, os.path.exists, path)
        
    def _check_port(self, host: str, port: int) -> bool:
        """检查端口占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except:
                return False

    def _calculate_health(self, checks: List[Dict]) -> str:
        """简单的健康度评分"""
        # 如果服务都挂了 -> critical
        # 如果NAS没连上 -> warning
        services = checks[2]
        if services.get("Backend (API)") == "stopped":
            return "critical_backend_down"
            
        return "healthy"

# 单例模式
detector = SystemDetector()
