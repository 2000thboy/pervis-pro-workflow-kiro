
"""
模拟素材处理器 - 用于测试和演示
当真实的AI模型不可用时，提供基础的处理功能
"""

import os
import shutil
import json
import uuid
from pathlib import Path
from typing import Dict, Any

class MockAssetProcessor:
    def __init__(self):
        self.asset_root = Path("backend/assets")
        self.asset_root.mkdir(parents=True, exist_ok=True)
        
        # 确保子目录存在
        for subdir in ['originals', 'proxies', 'thumbnails', 'audio']:
            (self.asset_root / subdir).mkdir(exist_ok=True)
    
    async def process_video_mock(self, asset_id: str, file_path: str) -> Dict[str, Any]:
        """模拟视频处理"""
        try:
            # 1. 移动原始文件
            original_path = self.asset_root / "originals" / f"{asset_id}.mp4"
            shutil.move(file_path, original_path)
            
            # 2. 创建代理文件 (复制原始文件)
            proxy_path = self.asset_root / "proxies" / f"{asset_id}_proxy.mp4"
            shutil.copy2(original_path, proxy_path)
            
            # 3. 创建缩略图 (创建占位符文件)
            thumbnail_path = self.asset_root / "thumbnails" / f"{asset_id}_thumb.jpg"
            with open(thumbnail_path, 'w') as f:
                f.write("thumbnail_placeholder")
            
            # 4. 创建音频文件 (创建占位符文件)
            audio_path = self.asset_root / "audio" / f"{asset_id}.wav"
            with open(audio_path, 'w') as f:
                f.write("audio_placeholder")
            
            # 5. 生成模拟的AI分析结果
            mock_analysis = {
                "segments": [
                    {
                        "start_time": 0.0,
                        "end_time": 10.0,
                        "description": f"视频片段 - {asset_id}",
                        "tags": {
                            "emotions": ["中性"],
                            "scenes": ["室内"],
                            "actions": ["展示"],
                            "cinematography": ["中景"]
                        }
                    }
                ],
                "overall_analysis": {
                    "duration": 10.0,
                    "quality": "good",
                    "content_type": "educational"
                }
            }
            
            return {
                "status": "success",
                "paths": {
                    "original": str(original_path),
                    "proxy": str(proxy_path),
                    "thumbnail": str(thumbnail_path),
                    "audio": str(audio_path)
                },
                "analysis": mock_analysis
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_mock_vectors(self, asset_id: str, analysis: Dict[str, Any]) -> list:
        """创建模拟向量数据"""
        vectors = []
        
        # 为每个片段创建向量
        for i, segment in enumerate(analysis.get("segments", [])):
            vector_data = {
                "id": f"vector_{asset_id}_{i}",
                "asset_id": asset_id,
                "vector_data": json.dumps([0.1 + i * 0.1] * 384),  # 模拟384维向量
                "content_type": "segment_description",
                "text_content": segment["description"]
            }
            vectors.append(vector_data)
        
        return vectors

# 全局实例
mock_processor = MockAssetProcessor()
