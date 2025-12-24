import json
import os
from pathlib import Path
from typing import Dict, Any

class TrafficController:
    """
    流量控制服务 (Traffic Control)
    管理 AI 处理的资源占用策略
    """
    
    MODES = {
        "silent": {
            "name": "静默模式",
            "description": "后台低速运行，不占用前台带宽",
            "parallel_tasks": 1,
            "keyframe_interval": 10.0, # 抽帧更稀疏
            "upload_rate_limit": "500KB/s"
        },
        "balanced": {
            "name": "平衡模式",
            "description": "默认模式，平衡速度与资源",
            "parallel_tasks": 2,
            "keyframe_interval": 5.0,
            "upload_rate_limit": "2MB/s"
        },
        "performance": {
            "name": "狂暴模式", 
            "description": "全速扫描，尽快完成索引 (可能占用带宽)",
            "parallel_tasks": 5,
            "keyframe_interval": 2.0,
            "upload_rate_limit": "Unlimited"
        }
    }
    
    CONFIG_FILE = Path("launcher_config.json")
    
    def __init__(self):
        self.current_mode = "balanced"
        self._load_config()
        
    def set_mode(self, mode_key: str) -> Dict[str, Any]:
        """切换模式"""
        if mode_key not in self.MODES:
            return {"status": "error", "message": "Invalid mode"}
            
        self.current_mode = mode_key
        self._save_config()
        
        # TODO: 这里可以调用后端 API 通知变更
        # await self._notify_backend(self.MODES[mode_key])
        
        return {
            "status": "success", 
            "mode": self.MODES[mode_key]
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前策略参数"""
        return self.MODES[self.current_mode]
        
    def _load_config(self):
        if self.CONFIG_FILE.exists():
            try:
                data = json.loads(self.CONFIG_FILE.read_text(encoding="utf-8"))
                self.current_mode = data.get("traffic_mode", "balanced")
            except:
                pass
                
    def _save_config(self):
        data = {"traffic_mode": self.current_mode}
        self.CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

# Singleton
traffic_crtl = TrafficController()
