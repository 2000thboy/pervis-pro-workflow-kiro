"""
图片处理服务
负责图片的基础处理操作，包括格式转换、缩略图生成、元数据提取等
"""

import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import json
import hashlib

try:
    from PIL import Image, ImageOps
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL/Pillow未安装，图片处理功能将受限")

import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ImageProcessor:
    """图片处理服务"""
    
    def __init__(self, storage_path: str = "storage/images"):
        self.storage_path = Path(storage_path)
        self.thumbnail_size = (320, 240)
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'tiff']
        self.max_file_size_mb = 50
        
        # 创建存储目录
        self.originals_dir = self.storage_path / "originals"
        self.thumbnails_dir = self.storage_path / "thumbnails"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保存储目录存在"""
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.originals_dir.mkdir(parents=True, exist_ok=True)
            self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"图片存储目录已创建: {self.storage_path}")
        except Exception as e:
            logger.error(f"创建存储目录失败: {e}")
            raise
    
    def validate_image(self, file_path: str) -> Dict[str, Any]:
        """验证图片格式和完整性"""
        try:
            file_path = Path(file_path)
            
            # 检查文件是否存在
            if not file_path.exists():
                return {"valid": False, "error": "文件不存在"}
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size_mb * 1024 * 1024:
                return {
                    "valid": False, 
                    "error": f"文件大小超过限制 ({self.max_file_size_mb}MB)"
                }
            
            # 检查文件扩展名
            extension = file_path.suffix.lower().lstrip('.')
            if extension not in self.supported_formats:
                return {
                    "valid": False, 
                    "error": f"不支持的文件格式: {extension}"
                }
            
            # 如果PIL可用，验证图片完整性
            if PIL_AVAILABLE:
                try:
                    with Image.open(file_path) as img:
                        img.verify()  # 验证图片完整性
                        
                    # 重新打开获取基本信息
                    with Image.open(file_path) as img:
                        width, height = img.size
                        format_name = img.format
                        mode = img.mode
                        
                    return {
                        "valid": True,
                        "width": width,
                        "height": height,
                        "format": format_name,
                        "mode": mode,
                        "file_size": file_size
                    }
                        
                except Exception as e:
                    return {"valid": False, "error": f"图片文件损坏: {e}"}
            else:
                # 没有PIL时的基础验证
                return {
                    "valid": True,
                    "file_size": file_size,
                    "format": extension.upper()
                }
                
        except Exception as e:
            logger.error(f"图片验证失败: {e}")
            return {"valid": False, "error": f"验证过程出错: {e}"}
    
    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取图片元数据"""
        try:
            file_path = Path(file_path)
            metadata = {
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            if not PIL_AVAILABLE:
                return metadata
            
            try:
                with Image.open(file_path) as img:
                    # 基本信息
                    metadata.update({
                        "width": img.size[0],
                        "height": img.size[1],
                        "format": img.format,
                        "mode": img.mode,
                        "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                    })
                    
                    # EXIF信息
                    if hasattr(img, '_getexif') and img._getexif():
                        exif_data = {}
                        exif = img._getexif()
                        
                        for tag_id, value in exif.items():
                            tag = TAGS.get(tag_id, tag_id)
                            if isinstance(value, (str, int, float)):
                                exif_data[tag] = value
                        
                        if exif_data:
                            metadata["exif"] = exif_data
                    
                    # 色彩信息
                    if img.mode == 'RGB':
                        # 获取主要颜色（简化版）
                        img_small = img.resize((50, 50))
                        colors = img_small.getcolors(maxcolors=256)
                        if colors:
                            # 按出现频率排序
                            colors.sort(key=lambda x: x[0], reverse=True)
                            dominant_color = colors[0][1]
                            
                            metadata["color_info"] = {
                                "dominant_rgb": dominant_color,
                                "dominant_hex": "#{:02x}{:02x}{:02x}".format(*dominant_color)
                            }
                            
            except Exception as e:
                logger.warning(f"提取图片元数据失败: {e}")
                
            return metadata
            
        except Exception as e:
            logger.error(f"提取元数据失败: {e}")
            return {"error": str(e)}
    
    def generate_thumbnail(self, image_path: str, output_path: Optional[str] = None) -> str:
        """生成缩略图"""
        try:
            if not PIL_AVAILABLE:
                raise Exception("PIL/Pillow未安装，无法生成缩略图")
            
            image_path = Path(image_path)
            
            if output_path is None:
                # 生成缩略图文件名
                stem = image_path.stem
                output_path = self.thumbnails_dir / f"{stem}_thumb.jpg"
            else:
                output_path = Path(output_path)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with Image.open(image_path) as img:
                # 处理EXIF旋转信息
                img = ImageOps.exif_transpose(img)
                
                # 转换为RGB模式（处理RGBA、P等模式）
                if img.mode != 'RGB':
                    # 如果有透明度，使用白色背景
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'RGBA':
                            background.paste(img, mask=img.split()[-1])
                        else:
                            background.paste(img, mask=img.split()[-1])
                        img = background
                    else:
                        img = img.convert('RGB')
                
                # 生成缩略图（保持宽高比）
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # 保存缩略图
                img.save(output_path, "JPEG", quality=85, optimize=True)
            
            logger.info(f"缩略图生成成功: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
            raise
    
    def save_uploaded_file(self, file_content: bytes, filename: str, project_id: str) -> Tuple[str, str]:
        """保存上传的文件"""
        try:
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix.lower()
            
            # 构建文件路径
            safe_filename = f"{file_id}{file_extension}"
            original_path = self.originals_dir / safe_filename
            
            # 保存原始文件
            with open(original_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"文件保存成功: {original_path}")
            return str(original_path), file_id
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            raise
    
    async def process_image(self, file_content: bytes, filename: str, project_id: str) -> Dict[str, Any]:
        """处理上传的图片（完整流程）"""
        try:
            # 1. 保存原始文件
            original_path, file_id = self.save_uploaded_file(file_content, filename, project_id)
            
            # 2. 验证图片
            validation = self.validate_image(original_path)
            if not validation["valid"]:
                # 删除无效文件
                try:
                    os.remove(original_path)
                except:
                    pass
                raise Exception(f"图片验证失败: {validation['error']}")
            
            # 3. 提取元数据
            metadata = self.extract_metadata(original_path)
            
            # 4. 生成缩略图
            thumbnail_path = None
            try:
                thumbnail_path = self.generate_thumbnail(original_path)
            except Exception as e:
                logger.warning(f"生成缩略图失败: {e}")
            
            # 5. 构建结果
            result = {
                "id": file_id,
                "filename": filename,
                "original_path": original_path,
                "thumbnail_path": thumbnail_path,
                "metadata": metadata,
                "validation": validation,
                "processing_status": "completed"
            }
            
            logger.info(f"图片处理完成: {filename}")
            return result
            
        except Exception as e:
            logger.error(f"图片处理失败: {e}")
            return {
                "filename": filename,
                "processing_status": "failed",
                "error": str(e)
            }
    
    async def batch_process_images(self, files_data: List[Tuple[bytes, str]], project_id: str) -> List[Dict[str, Any]]:
        """批量处理图片"""
        try:
            logger.info(f"开始批量处理 {len(files_data)} 个图片文件")
            
            # 并发处理（限制并发数）
            semaphore = asyncio.Semaphore(5)  # 最多5个并发
            
            async def process_single(file_data):
                async with semaphore:
                    content, filename = file_data
                    return await self.process_image(content, filename, project_id)
            
            # 执行批量处理
            tasks = [process_single(file_data) for file_data in files_data]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        "filename": files_data[i][1],
                        "processing_status": "failed",
                        "error": str(result)
                    })
                else:
                    processed_results.append(result)
            
            success_count = sum(1 for r in processed_results if r.get("processing_status") == "completed")
            logger.info(f"批量处理完成: {success_count}/{len(files_data)} 成功")
            
            return processed_results
            
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
            raise
    
    def delete_image_files(self, original_path: str, thumbnail_path: Optional[str] = None):
        """删除图片文件"""
        try:
            # 删除原始文件
            if original_path and os.path.exists(original_path):
                os.remove(original_path)
                logger.info(f"删除原始文件: {original_path}")
            
            # 删除缩略图
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"删除缩略图: {thumbnail_path}")
                
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            stats = {
                "storage_path": str(self.storage_path),
                "originals_count": 0,
                "thumbnails_count": 0,
                "total_size_mb": 0,
                "originals_size_mb": 0,
                "thumbnails_size_mb": 0
            }
            
            # 统计原始文件
            if self.originals_dir.exists():
                originals = list(self.originals_dir.glob("*"))
                stats["originals_count"] = len(originals)
                stats["originals_size_mb"] = sum(f.stat().st_size for f in originals if f.is_file()) / (1024 * 1024)
            
            # 统计缩略图
            if self.thumbnails_dir.exists():
                thumbnails = list(self.thumbnails_dir.glob("*"))
                stats["thumbnails_count"] = len(thumbnails)
                stats["thumbnails_size_mb"] = sum(f.stat().st_size for f in thumbnails if f.is_file()) / (1024 * 1024)
            
            stats["total_size_mb"] = stats["originals_size_mb"] + stats["thumbnails_size_mb"]
            
            return stats
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {"error": str(e)}
    
    def cleanup_orphaned_files(self, existing_image_ids: List[str]):
        """清理孤立的文件（数据库中不存在的文件）"""
        try:
            cleaned_count = 0
            
            # 清理原始文件
            if self.originals_dir.exists():
                for file_path in self.originals_dir.glob("*"):
                    if file_path.is_file():
                        # 从文件名提取ID
                        file_id = file_path.stem
                        if file_id not in existing_image_ids:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.info(f"清理孤立原始文件: {file_path}")
            
            # 清理缩略图
            if self.thumbnails_dir.exists():
                for file_path in self.thumbnails_dir.glob("*"):
                    if file_path.is_file():
                        # 从文件名提取ID（去掉_thumb后缀）
                        file_id = file_path.stem.replace("_thumb", "")
                        if file_id not in existing_image_ids:
                            file_path.unlink()
                            cleaned_count += 1
                            logger.info(f"清理孤立缩略图: {file_path}")
            
            logger.info(f"清理完成，删除了 {cleaned_count} 个孤立文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理孤立文件失败: {e}")
            raise

# 工具函数
def get_image_hash(file_path: str) -> str:
    """计算图片文件的哈希值（用于去重）"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5()
            for chunk in iter(lambda: f.read(4096), b""):
                file_hash.update(chunk)
        return file_hash.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败: {e}")
        return ""

def is_image_file(filename: str) -> bool:
    """检查文件是否为图片格式"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff'}
    return Path(filename).suffix.lower() in image_extensions

# 使用示例
if __name__ == "__main__":
    # 测试图片处理器
    processor = ImageProcessor()
    
    # 获取存储统计
    stats = processor.get_storage_stats()
    print("存储统计:", json.dumps(stats, indent=2, ensure_ascii=False))