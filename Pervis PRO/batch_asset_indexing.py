# -*- coding: utf-8 -*-
"""
Pervis PRO 批量素材索引和打标脚本

功能：
1. 扫描 DAM 素材库
2. 使用 Ollama 本地模型生成标签
3. 使用 Ollama 嵌入模型生成向量（绕过 NumPy 问题）
4. 存储到内存/Milvus

使用方法：
    cd "Pervis PRO"
    py batch_asset_indexing.py --sample 200
    py batch_asset_indexing.py --all
"""

import asyncio
import argparse
import json
import os
import sys
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import hashlib

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
EMBEDDING_MODEL = "nomic-embed-text"  # Ollama 嵌入模型

# 标签类型定义
TAG_CATEGORIES = {
    "scene_type": ["室内", "室外", "混合"],
    "time": ["白天", "夜晚", "黄昏", "黎明", "未知"],
    "shot_type": ["特写", "近景", "中景", "全景", "远景", "俯拍", "仰拍"],
    "mood": ["紧张", "悲伤", "欢乐", "平静", "恐怖", "浪漫", "热血", "未知"],
    "action": ["打斗", "追逐", "对话", "静态", "奔跑", "飞行", "变身", "技能释放"],
}

# 动漫关键词映射
ANIME_KEYWORDS = {
    # 鬼灭之刃
    "鬼灭": ["鬼灭之刃", "炭治郎", "弥豆子", "善逸", "伊之助", "鬼杀队"],
    "炭治郎": ["水之呼吸", "日轮刀", "主角"],
    "善逸": ["雷之呼吸", "霹雳一闪", "睡眠战斗"],
    "弥豆子": ["血鬼术", "鬼化", "妹妹"],
    "义勇": ["水柱", "水之呼吸"],
    "蜘蛛": ["蜘蛛鬼", "那田蜘蛛山"],
    
    # 动作类型
    "战斗": ["打斗", "战斗", "攻击", "技能"],
    "砍": ["斩击", "刀", "剑"],
    "冲刺": ["冲刺", "快速移动", "闪避"],
    "旋转": ["旋转", "回旋", "转身"],
    "飞": ["飞行", "跳跃", "空中"],
    "落地": ["落地", "着陆"],
    
    # 场景
    "森林": ["森林", "树林", "室外"],
    "屋": ["室内", "房间", "建筑"],
    "夜": ["夜晚", "黑暗", "月光"],
}


# ============================================================
# Ollama 嵌入服务（绕过 NumPy 问题）
# ============================================================

class OllamaEmbedding:
    """使用 Ollama 生成嵌入向量"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = EMBEDDING_MODEL):
        self.base_url = base_url
        self.model = model
        self._available = None
    
    async def check_available(self) -> bool:
        """检查嵌入模型是否可用"""
        if self._available is not None:
            return self._available
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # 检查模型是否已安装
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m.get("name", "") for m in data.get("models", [])]
                        self._available = any(self.model in m for m in models)
                        if not self._available:
                            print(f"⚠️ 嵌入模型 {self.model} 未安装")
                            print(f"   可用模型: {models}")
                            print(f"   安装命令: ollama pull {self.model}")
                        return self._available
        except Exception as e:
            print(f"⚠️ Ollama 服务不可用: {e}")
            self._available = False
        return False
    
    async def embed(self, text: str) -> Optional[List[float]]:
        """生成文本嵌入向量"""
        if not await self.check_available():
            return None
        
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("embedding")
        except Exception as e:
            print(f"⚠️ 生成嵌入失败: {e}")
        return None
    
    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """批量生成嵌入向量"""
        results = []
        for text in texts:
            embedding = await self.embed(text)
            results.append(embedding)
        return results


# ============================================================
# 标签生成器
# ============================================================

class TagGenerator:
    """标签生成器"""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = LOCAL_MODEL):
        self.base_url = base_url
        self.model = model
    
    def extract_from_filename(self, filename: str) -> Dict[str, Any]:
        """从文件名提取标签"""
        # 清理文件名
        name = filename
        # 移除常见前缀
        prefixes_to_remove = [
            "【免费更新+V Lingshao2605】",
            "【",
            "】",
        ]
        for prefix in prefixes_to_remove:
            name = name.replace(prefix, "")
        
        # 移除扩展名
        name = Path(name).stem
        
        tags = {
            "scene_type": "未知",
            "time": "未知",
            "shot_type": "未知",
            "mood": "未知",
            "action": "静态",
            "characters": [],
            "free_tags": [],
            "source_anime": "未知",
            "summary": name[:100]
        }
        
        # 提取关键词
        keywords = []
        for word in re.split(r'[\s_\-\.]+', name):
            if len(word) > 1:
                keywords.append(word)
        
        # 匹配动漫关键词
        matched_tags = set()
        for keyword in keywords:
            for key, related in ANIME_KEYWORDS.items():
                if key in keyword or keyword in key:
                    matched_tags.update(related)
                    if key in ["鬼灭", "炭治郎", "善逸", "弥豆子", "义勇"]:
                        tags["source_anime"] = "鬼灭之刃"
        
        # 识别场景类型
        if any(k in name for k in ["室内", "房间", "屋", "车厢", "餐厅"]):
            tags["scene_type"] = "室内"
        elif any(k in name for k in ["室外", "森林", "街道", "天空", "山", "海"]):
            tags["scene_type"] = "室外"
        
        # 识别时间
        if any(k in name for k in ["夜", "月", "黑暗"]):
            tags["time"] = "夜晚"
        elif any(k in name for k in ["日", "阳光", "白天"]):
            tags["time"] = "白天"
        elif any(k in name for k in ["黄昏", "夕阳"]):
            tags["time"] = "黄昏"
        
        # 识别镜头类型
        if any(k in name for k in ["特写", "脸", "眼"]):
            tags["shot_type"] = "特写"
        elif any(k in name for k in ["全景", "远景", "全身"]):
            tags["shot_type"] = "全景"
        elif any(k in name for k in ["近景"]):
            tags["shot_type"] = "近景"
        
        # 识别动作
        if any(k in name for k in ["战斗", "打斗", "砍", "斩", "攻击", "技能"]):
            tags["action"] = "打斗"
            tags["mood"] = "紧张"
        elif any(k in name for k in ["跑", "追", "逃", "冲刺"]):
            tags["action"] = "追逐"
        elif any(k in name for k in ["飞", "跳", "空中"]):
            tags["action"] = "飞行"
        elif any(k in name for k in ["旋转", "转身"]):
            tags["action"] = "技能释放"
        
        # 识别情绪
        if any(k in name for k in ["燃", "热血", "战斗", "怒"]):
            tags["mood"] = "热血"
        elif any(k in name for k in ["哭", "泪", "悲"]):
            tags["mood"] = "悲伤"
        elif any(k in name for k in ["笑", "搞笑", "欢乐"]):
            tags["mood"] = "欢乐"
        
        # 识别角色
        character_names = ["炭治郎", "善逸", "伊之助", "弥豆子", "义勇", "蝴蝶忍", "煤炭郎"]
        for char in character_names:
            if char in name:
                tags["characters"].append(char)
        
        # 合并标签
        tags["free_tags"] = list(matched_tags)[:10]
        if not tags["free_tags"]:
            tags["free_tags"] = keywords[:10]
        
        return tags
    
    async def generate_with_llm(self, filename: str, description: str = "") -> Dict[str, Any]:
        """使用 LLM 生成标签"""
        # 先用文件名提取基础标签
        base_tags = self.extract_from_filename(filename)
        
        # 如果有 LLM，尝试增强标签
        try:
            import aiohttp
            
            prompt = f"""分析以下视频素材文件名，生成标签。

文件名: {filename}
{f'描述: {description}' if description else ''}

请返回 JSON 格式：
{{
  "scene_type": "室内/室外/混合",
  "time": "白天/夜晚/黄昏/黎明",
  "shot_type": "特写/近景/中景/全景/远景",
  "mood": "紧张/悲伤/欢乐/平静/热血",
  "action": "打斗/追逐/对话/静态/飞行/技能释放",
  "characters": ["角色1", "角色2"],
  "free_tags": ["标签1", "标签2", "标签3"]
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
                        
                        # 尝试解析 JSON
                        try:
                            # 提取 JSON 部分
                            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
                            if json_match:
                                llm_tags = json.loads(json_match.group())
                                # 合并标签
                                for key in ["scene_type", "time", "shot_type", "mood", "action"]:
                                    if key in llm_tags and llm_tags[key] != "未知":
                                        base_tags[key] = llm_tags[key]
                                if "characters" in llm_tags:
                                    base_tags["characters"] = list(set(base_tags.get("characters", []) + llm_tags["characters"]))
                                if "free_tags" in llm_tags:
                                    base_tags["free_tags"] = list(set(base_tags.get("free_tags", []) + llm_tags["free_tags"]))[:15]
                        except json.JSONDecodeError:
                            pass
                            
        except Exception as e:
            pass  # 使用基础标签
        
        return base_tags


# ============================================================
# 批量索引器
# ============================================================

@dataclass
class IndexingStats:
    """索引统计"""
    total_files: int = 0
    indexed: int = 0
    tagged: int = 0
    embedded: int = 0
    failed: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            "total_files": self.total_files,
            "indexed": self.indexed,
            "tagged": self.tagged,
            "embedded": self.embedded,
            "failed": self.failed,
            "elapsed_seconds": elapsed,
            "rate": self.indexed / elapsed if elapsed > 0 else 0
        }


class BatchAssetIndexer:
    """批量素材索引器"""
    
    VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
    
    def __init__(
        self,
        asset_root: str = DAM_ASSET_ROOT,
        use_llm: bool = True,
        use_embedding: bool = True
    ):
        self.asset_root = asset_root
        self.use_llm = use_llm
        self.use_embedding = use_embedding
        
        self.tag_generator = TagGenerator()
        self.embedding_service = OllamaEmbedding()
        self.video_store = None
        self.stats = IndexingStats()
        
        # 索引缓存（避免重复索引）
        self.index_cache_path = Path(__file__).parent / "data" / "index_cache.json"
        self.index_cache: Dict[str, str] = {}  # {file_hash: segment_id}
    
    def _load_cache(self):
        """加载索引缓存"""
        if self.index_cache_path.exists():
            try:
                with open(self.index_cache_path, "r", encoding="utf-8") as f:
                    self.index_cache = json.load(f)
                print(f"📂 已加载索引缓存: {len(self.index_cache)} 条记录")
            except:
                self.index_cache = {}
    
    def _save_cache(self):
        """保存索引缓存"""
        self.index_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_cache_path, "w", encoding="utf-8") as f:
            json.dump(self.index_cache, f, ensure_ascii=False, indent=2)
    
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件哈希（用于去重）"""
        # 使用文件路径和大小生成哈希
        stat = os.stat(file_path)
        content = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def scan_assets(self, sample_size: int = None, target_dirs: List[str] = None) -> List[str]:
        """扫描素材文件"""
        print(f"\n📁 扫描素材库: {self.asset_root}")
        
        video_files = []
        
        for root, dirs, files in os.walk(self.asset_root):
            # 如果指定了目标目录，只扫描这些目录
            if target_dirs:
                rel_path = os.path.relpath(root, self.asset_root)
                if not any(target in rel_path for target in target_dirs):
                    continue
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in self.VIDEO_EXTENSIONS:
                    video_files.append(os.path.join(root, file))
        
        print(f"   找到 {len(video_files)} 个视频文件")
        
        # 采样
        if sample_size and sample_size < len(video_files):
            import random
            random.shuffle(video_files)
            video_files = video_files[:sample_size]
            print(f"   采样 {sample_size} 个文件")
        
        self.stats.total_files = len(video_files)
        return video_files
    
    async def initialize_store(self):
        """初始化存储"""
        from services.milvus_store import get_video_store, VectorStoreType, MemoryVideoStore
        
        # 使用内存存储（Milvus 需要 Docker）
        self.video_store = MemoryVideoStore()
        await self.video_store.initialize()
        print("✅ 视频存储初始化完成")
    
    async def index_file(self, file_path: str, index: int) -> bool:
        """索引单个文件"""
        try:
            filename = Path(file_path).name
            file_hash = self._get_file_hash(file_path)
            
            # 检查缓存
            if file_hash in self.index_cache:
                return True
            
            # 生成标签
            if self.use_llm:
                tags = await self.tag_generator.generate_with_llm(filename)
            else:
                tags = self.tag_generator.extract_from_filename(filename)
            
            self.stats.tagged += 1
            
            # 生成嵌入向量
            embedding = None
            if self.use_embedding:
                # 使用标签和文件名生成描述
                description = f"{tags.get('summary', '')} {' '.join(tags.get('free_tags', []))}"
                embedding = await self.embedding_service.embed(description)
                if embedding:
                    self.stats.embedded += 1
            
            # 创建视频片段
            from services.milvus_store import VideoSegment
            segment = VideoSegment(
                segment_id=f"asset_{index:06d}",
                video_id=file_hash[:16],
                video_path=file_path,
                start_time=0,
                end_time=5.0,  # 默认时长
                duration=5.0,
                tags=tags,
                embedding=embedding,
                description=tags.get("summary", filename)
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
    
    async def run(
        self,
        sample_size: int = None,
        target_dirs: List[str] = None,
        batch_size: int = 10
    ):
        """运行批量索引"""
        print("\n" + "="*70)
        print("Pervis PRO 批量素材索引")
        print("="*70)
        
        # 加载缓存
        self._load_cache()
        
        # 初始化存储
        await self.initialize_store()
        
        # 检查嵌入服务
        if self.use_embedding:
            available = await self.embedding_service.check_available()
            if not available:
                print("⚠️ 嵌入服务不可用，将跳过向量生成")
                self.use_embedding = False
        
        # 扫描文件
        video_files = self.scan_assets(sample_size, target_dirs)
        
        if not video_files:
            print("❌ 没有找到视频文件")
            return
        
        # 批量索引
        print(f"\n🚀 开始索引 {len(video_files)} 个文件...")
        print(f"   使用 LLM: {self.use_llm}")
        print(f"   使用嵌入: {self.use_embedding}")
        print("-"*70)
        
        for i, file_path in enumerate(video_files):
            # 进度显示
            if (i + 1) % 10 == 0 or i == 0:
                progress = (i + 1) / len(video_files) * 100
                print(f"   [{i+1}/{len(video_files)}] {progress:.1f}% - {Path(file_path).name[:40]}...")
            
            await self.index_file(file_path, i)
            
            # 定期保存缓存
            if (i + 1) % 50 == 0:
                self._save_cache()
        
        # 最终保存
        self._save_cache()
        
        # 输出统计
        self._print_stats()
        self._save_report()
    
    def _print_stats(self):
        """打印统计信息"""
        stats = self.stats.to_dict()
        
        print("\n" + "="*70)
        print("📊 索引统计")
        print("="*70)
        print(f"   总文件数: {stats['total_files']}")
        print(f"   已索引: {stats['indexed']}")
        print(f"   已打标: {stats['tagged']}")
        print(f"   已嵌入: {stats['embedded']}")
        print(f"   失败: {stats['failed']}")
        print(f"   耗时: {stats['elapsed_seconds']:.1f} 秒")
        print(f"   速率: {stats['rate']:.2f} 文件/秒")
        print("="*70)
    
    def _save_report(self):
        """保存索引报告"""
        report_path = Path(__file__).parent / f"indexing_report_{int(time.time())}.json"
        
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
    
    async def analyze_tags(self):
        """分析标签分布"""
        print("\n" + "="*70)
        print("📊 标签分布分析")
        print("="*70)
        
        if not self.video_store:
            print("❌ 存储未初始化")
            return
        
        # 统计标签
        tag_stats = {
            "scene_type": {},
            "time": {},
            "shot_type": {},
            "mood": {},
            "action": {},
            "source_anime": {},
            "free_tags": {}
        }
        
        count = await self.video_store.count()
        print(f"   总素材数: {count}")
        
        # 遍历所有素材
        for segment_id, segment in self.video_store._segments.items():
            tags = segment.tags
            
            for category in ["scene_type", "time", "shot_type", "mood", "action", "source_anime"]:
                value = tags.get(category, "未知")
                tag_stats[category][value] = tag_stats[category].get(value, 0) + 1
            
            for tag in tags.get("free_tags", []):
                tag_stats["free_tags"][tag] = tag_stats["free_tags"].get(tag, 0) + 1
        
        # 输出统计
        for category, values in tag_stats.items():
            if category == "free_tags":
                # 只显示 Top 20
                sorted_tags = sorted(values.items(), key=lambda x: x[1], reverse=True)[:20]
                print(f"\n   {category} (Top 20):")
                for tag, cnt in sorted_tags:
                    print(f"      {tag}: {cnt}")
            else:
                print(f"\n   {category}:")
                for value, cnt in sorted(values.items(), key=lambda x: x[1], reverse=True):
                    pct = cnt / count * 100 if count > 0 else 0
                    print(f"      {value}: {cnt} ({pct:.1f}%)")


# ============================================================
# 主函数
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Pervis PRO 批量素材索引")
    parser.add_argument("--sample", type=int, default=200, help="采样数量（默认200）")
    parser.add_argument("--all", action="store_true", help="索引所有文件")
    parser.add_argument("--no-llm", action="store_true", help="不使用 LLM 生成标签")
    parser.add_argument("--no-embedding", action="store_true", help="不生成嵌入向量")
    parser.add_argument("--dirs", nargs="+", help="指定目录（如 鬼灭 打斗）")
    parser.add_argument("--analyze", action="store_true", help="分析标签分布")
    
    args = parser.parse_args()
    
    sample_size = None if args.all else args.sample
    
    indexer = BatchAssetIndexer(
        use_llm=not args.no_llm,
        use_embedding=not args.no_embedding
    )
    
    await indexer.run(
        sample_size=sample_size,
        target_dirs=args.dirs
    )
    
    if args.analyze:
        await indexer.analyze_tags()


if __name__ == "__main__":
    asyncio.run(main())
