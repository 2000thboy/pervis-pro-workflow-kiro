import os
from pathlib import Path
from typing import Dict, Any, List

class ContentScanner:
    """
    内容扫描服务
    负责扫描文件夹，统计视频文件，估算处理时间
    """
    
    VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.avi', '.wmv', '.flv', '.webm', '.m4v'}
    
    # 估算参数: 单个视频平均处理耗时 (基于 Gemini Flash + 抽帧)
    EST_MINUTES_PER_VIDEO = 4.0 
    
    def scan_directory(self, path_str: str) -> Dict[str, Any]:
        """
        扫描目录并返回统计信息
        """
        path = Path(path_str)
        if not path.exists():
            return {"status": "error", "message": "Path does not exist"}
            
        stats = {
            "total_files": 0,
            "new_files": 0, # MVP中简化：假设所有扫描到的都是 New，真实场景需比对DB
            "total_size_bytes": 0,
            "formats": {},
            "file_list": []
        }
        
        try:
            # 递归扫描 (限制深度以防卡死，或者用 os.walk)
            for root, dirs, files in os.walk(path_str):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in self.VIDEO_EXTENSIONS:
                        full_path = os.path.join(root, file)
                        size = os.path.getsize(full_path)
                        
                        stats["total_files"] += 1
                        stats["new_files"] += 1
                        stats["total_size_bytes"] += size
                        stats["formats"][ext] = stats["formats"].get(ext, 0) + 1
                        
                        # 只存前10个文件名作为预览
                        if len(stats["file_list"]) < 10:
                            stats["file_list"].append(file)
                            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
        # 计算估算值
        stats["estimated_time_min"] = int(stats["new_files"] * self.EST_MINUTES_PER_VIDEO)
        stats["status"] = "success"
        stats["scanned_path"] = path_str
        
        return stats

    def format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

scanner = ContentScanner()
