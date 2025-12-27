# -*- coding: utf-8 -*-
"""
Pervis PRO 批量素材索引 V2

Feature: pervis-asset-tagging
Task: 4.1 更新批量索引脚本

新功能：
1. 集成四级标签层级体系
2. 使用 Ollama 嵌入服务
3. 支持增量索引
4. 生成标签覆盖率报告

使用方法：
    cd "Pervis PRO"
    py batch_asset_indexing_v2.py --sample 300
    py batch_asset_indexing_v2.py --all --analyze
"""

import asyncio
import argparse
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 加载环境变量
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# ============================================================
# 配置
# ============================================================

DAM_ASSET_ROOT = os.getenv("ASSET_ROOT", r"U:\PreVis_Assets")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LOCAL_MODEL = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:7b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


# ============================================================
# 标签生成器 V2（使用新标签体系）
# ============================================================

class TagGeneratorV2:
    """标签生成器 V2 - 使用四级标签体系"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = LOCAL_MODEL):
        self.base_url = base_url
        self.model = model
    
    def extract_from_filename(self, filename: str, parent_dir: str = "") -> Dict[str, Any]:
        """从文件名和目录名提取标签"""
        from models.asset_tags import (
            SceneType, TimeOfDay, ShotSize, CameraMove, ActionType, Mood,
            KEYWORD_MAPPINGS, ANIME_KEYWORDS, CHARACTER_KEYWORDS, VFX_KEYWORDS
        )
        
        # 清理文件名
        name = filename
        prefixes_to_remove = ["【免费更新+V Lingshao2605】", "【", "】"]
        for prefix in prefixes_to_remove:
            name = name.replace(prefix, "")
        name = Path(name).stem
        
        # 合并文件名和目录名
        full_text = f"{parent_dir} {name}"
        
        # 初始化标签
        tags = {
            # L1
            "scene_type": "UNKNOWN",
            "time_of_day": "UNKNOWN",
            "shot_size": "UNKNOWN",
            # L2
            "camera_move": "UNKNOWN",
            "action_type": "UNKNOWN",
            "mood": "UNKNOWN",
            # L3
            "characters": [],
            "props": [],
            "vfx": [],
            "environment": [],
            # L4
            "free_tags": [],
            "source_work": "",
            "summary": name[:50],
        }
        
        # 从关键词映射提取标签
        for field, value_keywords in KEYWORD_MAPPINGS.items():
            for value, keywords in value_keywords.items():
                if any(kw in full_text for kw in keywords):
                    tags[field] = value
                    break
        
        # 识别来源作品
        for anime, keywords in ANIME_KEYWORDS.items():
            if any(kw in full_text for kw in keywords):
                tags["source_work"] = anime
                break
        
        # 识别角色
        for char, keywords in CHARACTER_KEYWORDS.items():
            if any(kw in full_text for kw in keywords):
                if char not in tags["characters"]:
                    tags["characters"].append(char)
        
        # 识别特效
        for vfx, keywords in VFX_KEYWORDS.items():
            if any(kw in full_text for kw in keywords):
                if vfx not in tags["vfx"]:
                    tags["vfx"].append(vfx)
        
        # 提取自由标签（从文件名分词）
        words = re.split(r'[\s_\-\.]+', name)
        free_tags = [w for w in words if len(w) > 1 and len(w) < 10][:10]
        tags["free_tags"] = free_tags
        
        return tags

    async def generate_with_llm(self, filename: str, parent_dir: str = "") -> Dict[str, Any]:
        """使用 LLM 增强标签"""
        # 先用文件名提取基础标签
        base_tags = self.extract_from_filename(filename, parent_dir)
        
        try:
            import aiohttp
            
            prompt = f"""分析以下视频素材，生成标签。

文件名: {filename}
目录: {parent_dir}

请返回 JSON 格式的标签：
{{
  "scene_type": "INT/EXT/INT-EXT/UNKNOWN",
  "time_of_day": "DAY/NIGHT/DAWN/DUSK/UNKNOWN",
  "shot_size": "ECU/CU/MCU/MS/MLS/LS/ELS/UNKNOWN",
  "camera_move": "STATIC/PAN/TILT/DOLLY/CRANE/HANDHELD/ZOOM/UNKNOWN",
  "action_type": "FIGHT/CHASE/DIALOGUE/IDLE/RUN/FLY/TRANSFORM/SKILL/UNKNOWN",
  "mood": "TENSE/SAD/HAPPY/CALM/HORROR/ROMANTIC/EPIC/NEUTRAL/UNKNOWN",
  "characters": ["角色1", "角色2"],
  "vfx": ["特效1", "特效2"],
  "environment": ["环境1"],
  "source_work": "作品名称"
}}

只返回 JSON，不要其他内容。"""

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.3}
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("response", "")
                        
                        # 解析 JSON
                        json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                        if json_match:
                            llm_tags = json.loads(json_match.group())
                            # 合并标签（LLM 结果覆盖基础标签）
                            for key in ["scene_type", "time_of_day", "shot_size", 
                                       "camera_move", "action_type", "mood", "source_work"]:
                                if key in llm_tags and llm_tags[key] not in ["UNKNOWN", "", None]:
                                    base_tags[key] = llm_tags[key]
                            for key in ["characters", "vfx", "environment"]:
                                if key in llm_tags and llm_tags[key]:
                                    base_tags[key] = list(set(base_tags.get(key, []) + llm_tags[key]))
        except Exception as e:
            pass  # 使用基础标签
        
        return base_tags


# ============================================================
# 索引统计
# ============================================================

@dataclass
class IndexingStatsV2:
    """索引统计 V2"""
    total_files: int = 0
    indexed: int = 0
    embedded: int = 0
    failed: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    # 关键帧和视觉嵌入统计
    keyframes_extracted: int = 0
    visual_embedded: int = 0
    
    # 标签覆盖统计
    tag_coverage: Dict[str, int] = field(default_factory=lambda: {
        "scene_type": 0, "time_of_day": 0, "shot_size": 0,
        "camera_move": 0, "action_type": 0, "mood": 0,
        "characters": 0, "vfx": 0, "environment": 0,
        "source_work": 0, "free_tags": 0,
    })
    
    def to_dict(self) -> Dict[str, Any]:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        coverage_pct = {
            k: v / self.indexed * 100 if self.indexed > 0 else 0
            for k, v in self.tag_coverage.items()
        }
        return {
            "total_files": self.total_files,
            "indexed": self.indexed,
            "embedded": self.embedded,
            "failed": self.failed,
            "keyframes_extracted": self.keyframes_extracted,
            "visual_embedded": self.visual_embedded,
            "elapsed_seconds": elapsed,
            "rate": self.indexed / elapsed if elapsed > 0 else 0,
            "embedding_rate": self.embedded / self.indexed * 100 if self.indexed > 0 else 0,
            "keyframe_rate": self.keyframes_extracted / self.indexed * 100 if self.indexed > 0 else 0,
            "visual_embedding_rate": self.visual_embedded / self.indexed * 100 if self.indexed > 0 else 0,
            "tag_coverage_pct": coverage_pct,
        }


# ============================================================
# 批量索引器 V2
# ============================================================

class BatchAssetIndexerV2:
    """批量素材索引器 V2"""
    
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
    
    def __init__(
        self,
        asset_root: str = DAM_ASSET_ROOT,
        use_llm: bool = False,  # 默认关闭 LLM（速度考虑）
        use_embedding: bool = True,
        use_keyframes: bool = False,  # 关键帧提取
        use_visual_embedding: bool = False,  # CLIP 视觉嵌入
    ):
        self.asset_root = asset_root
        self.use_llm = use_llm
        self.use_embedding = use_embedding
        self.use_keyframes = use_keyframes
        self.use_visual_embedding = use_visual_embedding
        
        self.tag_generator = TagGeneratorV2()
        self.embedding_service = None
        self.video_store = None
        self.keyframe_extractor = None
        self.clip_service = None
        self.visual_store = None
        self.stats = IndexingStatsV2()
        
        # 索引缓存
        self.cache_path = Path(__file__).parent / "data" / "index_cache_v2.json"
        self.index_cache: Dict[str, str] = {}
    
    def _load_cache(self):
        """加载索引缓存"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    self.index_cache = json.load(f)
                print(f"📂 已加载索引缓存: {len(self.index_cache)} 条记录")
            except:
                self.index_cache = {}
    
    def _save_cache(self):
        """保存索引缓存"""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.index_cache, f, ensure_ascii=False, indent=2)
    
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件哈希"""
        stat = os.stat(file_path)
        content = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def scan_assets(self, sample_size: int = None, target_dirs: List[str] = None) -> List[Tuple[str, str]]:
        """扫描素材文件，返回 (文件路径, 父目录名) 列表"""
        print(f"\n📁 扫描素材库: {self.asset_root}")
        
        video_files = []
        
        for root, dirs, files in os.walk(self.asset_root):
            if target_dirs:
                rel_path = os.path.relpath(root, self.asset_root)
                if not any(target in rel_path for target in target_dirs):
                    continue
            
            parent_dir = Path(root).name
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.VIDEO_EXTENSIONS:
                    video_files.append((os.path.join(root, file), parent_dir))
        
        print(f"   找到 {len(video_files)} 个视频文件")
        
        if sample_size and sample_size < len(video_files):
            import random
            random.shuffle(video_files)
            video_files = video_files[:sample_size]
            print(f"   采样 {sample_size} 个文件")
        
        self.stats.total_files = len(video_files)
        return video_files
    
    async def initialize(self):
        """初始化服务"""
        from services.milvus_store import MemoryVideoStore
        from services.ollama_embedding import OllamaEmbeddingService
        
        # 初始化存储
        self.video_store = MemoryVideoStore()
        await self.video_store.initialize()
        print("✅ 视频存储初始化完成")
        
        # 初始化嵌入服务
        if self.use_embedding:
            cache_path = str(Path(__file__).parent / "data" / "embedding_cache.json")
            self.embedding_service = OllamaEmbeddingService(
                model=EMBEDDING_MODEL,
                cache_path=cache_path
            )
            available, model = await self.embedding_service.check_available()
            if available:
                print(f"✅ 嵌入服务初始化完成: {model} (维度: {self.embedding_service.dimension})")
            else:
                print("⚠️ 嵌入服务不可用，将跳过向量生成")
                self.use_embedding = False
        
        # 初始化关键帧提取器
        if self.use_keyframes:
            try:
                from services.keyframe_extractor import KeyFrameExtractor
                from models.keyframe import KeyFrameConfig
                
                config = KeyFrameConfig(
                    strategy="hybrid",
                    max_frames=10,
                    interval_seconds=3.0,
                )
                self.keyframe_extractor = KeyFrameExtractor(config)
                print("✅ 关键帧提取器初始化完成")
            except Exception as e:
                print(f"⚠️ 关键帧提取器初始化失败: {e}")
                self.use_keyframes = False
        
        # 初始化 CLIP 视觉嵌入服务
        if self.use_visual_embedding:
            try:
                from services.clip_embedding import get_clip_service
                from services.visual_vector_store import get_visual_store
                
                self.clip_service = get_clip_service()
                await self.clip_service.initialize()
                
                self.visual_store = get_visual_store(
                    storage_path=str(Path(__file__).parent / "data" / "visual_vectors")
                )
                
                print(f"✅ CLIP 视觉嵌入服务初始化完成: {self.clip_service.model_name} (维度: {self.clip_service.dimension})")
            except Exception as e:
                print(f"⚠️ CLIP 视觉嵌入服务初始化失败: {e}")
                self.use_visual_embedding = False

    async def index_file(self, file_path: str, parent_dir: str, index: int) -> bool:
        """索引单个文件"""
        from services.milvus_store import VideoSegment
        
        try:
            filename = Path(file_path).name
            file_hash = self._get_file_hash(file_path)
            segment_id = f"asset_{index:06d}"
            
            # 检查缓存
            if file_hash in self.index_cache:
                return True
            
            # 生成标签
            if self.use_llm:
                tags = await self.tag_generator.generate_with_llm(filename, parent_dir)
            else:
                tags = self.tag_generator.extract_from_filename(filename, parent_dir)
            
            # 更新标签覆盖统计
            for field in self.stats.tag_coverage:
                value = tags.get(field)
                if value and value not in ["UNKNOWN", "", None]:
                    if isinstance(value, list) and value:
                        self.stats.tag_coverage[field] += 1
                    elif not isinstance(value, list):
                        self.stats.tag_coverage[field] += 1
            
            # 生成嵌入向量
            embedding = None
            if self.use_embedding and self.embedding_service:
                # 生成搜索文本
                search_text = self._generate_search_text(tags, filename)
                embedding = await self.embedding_service.embed(search_text)
                if embedding:
                    self.stats.embedded += 1
            
            # 提取关键帧
            keyframes = []
            if self.use_keyframes and self.keyframe_extractor:
                try:
                    keyframes = await self.keyframe_extractor.extract(file_path)
                    if keyframes:
                        self.stats.keyframes_extracted += 1
                except Exception as e:
                    pass  # 关键帧提取失败不影响主流程
            
            # 生成视觉嵌入
            if self.use_visual_embedding and self.clip_service and self.visual_store and keyframes:
                try:
                    visual_count = 0
                    for kf in keyframes:
                        if kf.image_path and os.path.exists(kf.image_path):
                            visual_vec = await self.clip_service.embed_image(kf.image_path)
                            if visual_vec:
                                self.visual_store.add(
                                    keyframe_id=f"{segment_id}_kf_{kf.frame_index:04d}",
                                    asset_id=segment_id,
                                    vector=visual_vec,
                                    frame_index=kf.frame_index,
                                    timestamp=kf.timestamp,
                                    timecode=kf.timecode,
                                    thumbnail_path=kf.image_path,
                                    metadata={"scene_id": kf.scene_id},
                                )
                                visual_count += 1
                    if visual_count > 0:
                        self.stats.visual_embedded += 1
                except Exception as e:
                    pass  # 视觉嵌入失败不影响主流程
            
            # 创建视频片段
            segment = VideoSegment(
                segment_id=segment_id,
                video_id=file_hash[:16],
                video_path=file_path,
                start_time=0,
                end_time=5.0,
                duration=5.0,
                tags=tags,
                embedding=embedding,
                description=tags.get("summary", filename[:50])
            )
            
            # 存储
            await self.video_store.insert(segment)
            
            # 更新缓存
            self.index_cache[file_hash] = segment.segment_id
            self.stats.indexed += 1
            
            return True
            
        except Exception as e:
            self.stats.failed += 1
            print(f"   ❌ 索引失败 [{index}]: {e}")
            return False
    
    def _generate_search_text(self, tags: Dict[str, Any], filename: str) -> str:
        """生成用于向量搜索的文本"""
        parts = []
        
        # L1/L2 标签
        for field in ["scene_type", "time_of_day", "action_type", "mood"]:
            value = tags.get(field)
            if value and value != "UNKNOWN":
                parts.append(value)
        
        # L3 标签
        for field in ["characters", "vfx", "environment"]:
            values = tags.get(field, [])
            if values:
                parts.extend(values)
        
        # L4 标签
        if tags.get("source_work"):
            parts.append(tags["source_work"])
        if tags.get("free_tags"):
            parts.extend(tags["free_tags"][:5])
        if tags.get("summary"):
            parts.append(tags["summary"])
        
        return ' '.join(parts) if parts else filename
    
    async def run(
        self,
        sample_size: int = None,
        target_dirs: List[str] = None
    ):
        """运行批量索引"""
        print("\n" + "="*70)
        print("Pervis PRO 批量素材索引 V2")
        print("="*70)
        
        self._load_cache()
        await self.initialize()
        
        video_files = self.scan_assets(sample_size, target_dirs)
        
        if not video_files:
            print("❌ 没有找到视频文件")
            return
        
        print(f"\n🚀 开始索引 {len(video_files)} 个文件...")
        print(f"   使用 LLM: {self.use_llm}")
        print(f"   使用嵌入: {self.use_embedding}")
        print(f"   使用关键帧: {self.use_keyframes}")
        print(f"   使用视觉嵌入: {self.use_visual_embedding}")
        print("-"*70)
        
        for i, (file_path, parent_dir) in enumerate(video_files):
            if (i + 1) % 20 == 0 or i == 0:
                progress = (i + 1) / len(video_files) * 100
                print(f"   [{i+1}/{len(video_files)}] {progress:.1f}%")
            
            await self.index_file(file_path, parent_dir, i)
            
            if (i + 1) % 100 == 0:
                self._save_cache()
                if self.embedding_service:
                    self.embedding_service.save_cache()
                if self.visual_store:
                    self.visual_store.save()
        
        self._save_cache()
        if self.embedding_service:
            self.embedding_service.save_cache()
        if self.visual_store:
            self.visual_store.save()
        
        # 保存完整的素材数据到新格式缓存（关键修复！）
        await self._save_segments_cache()
        
        self._print_stats()
        self._save_report()
    
    async def _save_segments_cache(self):
        """保存完整的素材数据到缓存文件（供后端启动时加载）"""
        if self.video_store and hasattr(self.video_store, 'save_to_cache'):
            cache_path = Path(__file__).parent / "data" / "segments_cache.json"
            success = await self.video_store.save_to_cache(str(cache_path))
            if success:
                print(f"✅ 已保存完整素材数据到 {cache_path}")
            else:
                print(f"⚠️ 保存素材数据失败")
        else:
            # 手动保存
            import json
            cache_path = Path(__file__).parent / "data" / "segments_cache.json"
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            segments_data = []
            for segment in self.video_store._segments.values():
                seg_dict = segment.to_dict()
                seg_dict["embedding"] = segment.embedding
                segments_data.append(seg_dict)
            
            data = {
                "version": "2.0",
                "count": len(segments_data),
                "segments": segments_data
            }
            
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            
            print(f"✅ 已保存 {len(segments_data)} 条素材数据到 {cache_path}")
    
    def _print_stats(self):
        """打印统计信息"""
        stats = self.stats.to_dict()
        
        print("\n" + "="*70)
        print("📊 索引统计")
        print("="*70)
        print(f"   总文件数: {stats['total_files']}")
        print(f"   已索引: {stats['indexed']}")
        print(f"   已嵌入: {stats['embedded']} ({stats['embedding_rate']:.1f}%)")
        print(f"   关键帧提取: {stats['keyframes_extracted']} ({stats['keyframe_rate']:.1f}%)")
        print(f"   视觉嵌入: {stats['visual_embedded']} ({stats['visual_embedding_rate']:.1f}%)")
        print(f"   失败: {stats['failed']}")
        print(f"   耗时: {stats['elapsed_seconds']:.1f} 秒")
        print(f"   速率: {stats['rate']:.2f} 文件/秒")
        
        print("\n📊 标签覆盖率")
        print("-"*70)
        for field, pct in stats['tag_coverage_pct'].items():
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"   {field:15s} {bar} {pct:.1f}%")
        print("="*70)
    
    def _save_report(self):
        """保存索引报告"""
        report_path = Path(__file__).parent / f"indexing_report_v2_{int(time.time())}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "asset_root": self.asset_root,
            "stats": self.stats.to_dict(),
            "config": {
                "use_llm": self.use_llm,
                "use_embedding": self.use_embedding,
                "llm_model": LOCAL_MODEL,
                "embedding_model": EMBEDDING_MODEL
            }
        }
        
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 报告已保存: {report_path}")
        return report_path

    async def analyze_tags(self):
        """分析标签分布"""
        print("\n" + "="*70)
        print("📊 标签分布分析")
        print("="*70)
        
        if not self.video_store:
            print("❌ 存储未初始化")
            return
        
        count = await self.video_store.count()
        print(f"   总素材数: {count}")
        
        # 统计各级标签
        l1_stats = {"scene_type": {}, "time_of_day": {}, "shot_size": {}}
        l2_stats = {"camera_move": {}, "action_type": {}, "mood": {}}
        l3_stats = {"characters": {}, "vfx": {}, "environment": {}}
        l4_stats = {"source_work": {}, "free_tags": {}}
        
        for segment_id, segment in self.video_store._segments.items():
            tags = segment.tags
            
            # L1 统计
            for field in l1_stats:
                value = tags.get(field, "UNKNOWN")
                l1_stats[field][value] = l1_stats[field].get(value, 0) + 1
            
            # L2 统计
            for field in l2_stats:
                value = tags.get(field, "UNKNOWN")
                l2_stats[field][value] = l2_stats[field].get(value, 0) + 1
            
            # L3 统计
            for field in ["characters", "vfx", "environment"]:
                for value in tags.get(field, []):
                    l3_stats[field][value] = l3_stats[field].get(value, 0) + 1
            
            # L4 统计
            if tags.get("source_work"):
                sw = tags["source_work"]
                l4_stats["source_work"][sw] = l4_stats["source_work"].get(sw, 0) + 1
            for tag in tags.get("free_tags", []):
                l4_stats["free_tags"][tag] = l4_stats["free_tags"].get(tag, 0) + 1
        
        # 输出 L1 统计
        print("\n📌 L1 一级标签（必填单选）")
        for field, values in l1_stats.items():
            print(f"\n   {field}:")
            for value, cnt in sorted(values.items(), key=lambda x: x[1], reverse=True)[:5]:
                pct = cnt / count * 100 if count > 0 else 0
                print(f"      {value}: {cnt} ({pct:.1f}%)")
        
        # 输出 L2 统计
        print("\n📌 L2 二级标签（必填单选）")
        for field, values in l2_stats.items():
            print(f"\n   {field}:")
            for value, cnt in sorted(values.items(), key=lambda x: x[1], reverse=True)[:5]:
                pct = cnt / count * 100 if count > 0 else 0
                print(f"      {value}: {cnt} ({pct:.1f}%)")
        
        # 输出 L3 统计
        print("\n📌 L3 三级标签（可选多选）Top 10")
        for field, values in l3_stats.items():
            if values:
                print(f"\n   {field}:")
                for value, cnt in sorted(values.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"      {value}: {cnt}")
        
        # 输出 L4 统计
        print("\n📌 L4 四级标签（自由）")
        if l4_stats["source_work"]:
            print("\n   source_work:")
            for value, cnt in sorted(l4_stats["source_work"].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"      {value}: {cnt}")
        
        if l4_stats["free_tags"]:
            print("\n   free_tags (Top 20):")
            for value, cnt in sorted(l4_stats["free_tags"].items(), key=lambda x: x[1], reverse=True)[:20]:
                print(f"      {value}: {cnt}")


# ============================================================
# 搜索测试
# ============================================================

async def test_search(indexer: BatchAssetIndexerV2):
    """测试搜索功能"""
    from services.search_service import HybridSearchService, SearchRequest, SearchMode
    
    print("\n" + "="*70)
    print("🔍 搜索测试")
    print("="*70)
    
    search_service = HybridSearchService(
        video_store=indexer.video_store,
        embedding_service=indexer.embedding_service
    )
    
    test_cases = [
        {"query": "炭治郎战斗", "tags": {"action_type": "FIGHT"}},
        {"query": "善逸雷之呼吸", "tags": {"characters": ["善逸"]}},
        {"query": "热血打斗场面", "tags": {"mood": "EPIC", "action_type": "FIGHT"}},
        {"query": "夜晚森林", "tags": {"time_of_day": "NIGHT"}},
    ]
    
    for i, tc in enumerate(test_cases):
        print(f"\n测试 {i+1}: query=\"{tc['query']}\" tags={tc['tags']}")
        
        request = SearchRequest(
            query=tc["query"],
            tags=tc["tags"],
            mode=SearchMode.HYBRID,
            top_k=3
        )
        
        response = await search_service.search(request)
        
        print(f"   结果数: {response.total}, 耗时: {response.search_time_ms:.1f}ms")
        for j, r in enumerate(response.results):
            print(f"   [{j+1}] score={r.score:.3f} - {Path(r.video_path).name[:40]}...")


# ============================================================
# 主函数
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Pervis PRO 批量素材索引 V2")
    parser.add_argument("--sample", type=int, default=300, help="采样数量（默认300）")
    parser.add_argument("--all", action="store_true", help="索引所有文件")
    parser.add_argument("--llm", action="store_true", help="使用 LLM 增强标签")
    parser.add_argument("--no-embedding", action="store_true", help="不生成嵌入向量")
    parser.add_argument("--keyframes", action="store_true", help="提取关键帧")
    parser.add_argument("--visual", action="store_true", help="生成 CLIP 视觉嵌入")
    parser.add_argument("--dirs", nargs="+", help="指定目录")
    parser.add_argument("--analyze", action="store_true", help="分析标签分布")
    parser.add_argument("--test-search", action="store_true", help="测试搜索功能")
    
    args = parser.parse_args()
    
    sample_size = None if args.all else args.sample
    
    indexer = BatchAssetIndexerV2(
        use_llm=args.llm,
        use_embedding=not args.no_embedding,
        use_keyframes=args.keyframes,
        use_visual_embedding=args.visual,
    )
    
    await indexer.run(
        sample_size=sample_size,
        target_dirs=args.dirs
    )
    
    if args.analyze:
        await indexer.analyze_tags()
    
    if args.test_search:
        await test_search(indexer)


if __name__ == "__main__":
    asyncio.run(main())
