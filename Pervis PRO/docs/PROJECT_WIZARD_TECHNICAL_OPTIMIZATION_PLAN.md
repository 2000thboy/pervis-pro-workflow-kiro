# Pervis PRO 项目立项向导系统 - 完整技术优化方案

## 一、方案概述

### 1.1 核心目标

基于现有 Pervis PRO 和 multi-agent-workflow 项目，实现项目立项向导系统，包括：
- 多文件批量导入与智能分类
- Agent 协作内容生成（Script_Agent、Art_Agent、Market_Agent）
- Director_Agent 全程审核建议
- PM_Agent 版本管理（用户可见）
- Storyboard_Agent 素材召回与 CLIP 分段
- System_Agent 导出前校验
- Milvus 向量搜索升级

### 1.2 技术选型原则

✅ **全部使用成熟开源技术，可直接 pip install 或 docker pull**
✅ **优先复用现有代码，最小化开发量**
✅ **API 优先于本地模型，降低部署复杂度**

---

## 二、技术栈总览

| 功能模块 | 技术方案 | 安装方式 | 成熟度 |
|----------|----------|----------|--------|
| **镜头分割** | PySceneDetect | `pip install scenedetect[opencv]` | ⭐⭐⭐⭐⭐ |
| **视频标签** | Gemini 2.5 Flash API | `pip install google-generativeai` | ⭐⭐⭐⭐⭐ |
| **向量存储** | Milvus Standalone | `docker compose up -d` | ⭐⭐⭐⭐⭐ |
| **视频处理** | FFmpeg (已有) | 已集成 | ⭐⭐⭐⭐⭐ |
| **Agent 架构** | BaseAgent (已有) | 已实现 | ⭐⭐⭐⭐ |
| **消息总线** | MessageBus (已有) | 已实现 | ⭐⭐⭐⭐ |
| **标签匹配** | Market_Agent (已有) | 已实现 Jaccard | ⭐⭐⭐⭐ |

---

## 三、系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Pervis PRO 项目立项向导系统                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     素材预处理管道 (上传时自动执行)                   │   │
│  │                                                                      │   │
│  │  素材上传 → PySceneDetect → Gemini 标签 → Milvus 存储               │   │
│  │     │         (镜头分割)    (视频理解)    (向量索引)                  │   │
│  │     │            │             │             │                       │   │
│  │     │      ≤10秒片段      JSON标签      768维向量                    │   │
│  │     │            │             │             │                       │   │
│  │     └────────────┴─────────────┴─────────────┘                       │   │
│  │                         ↓                                            │   │
│  │                   预处理完成，标签已存储                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Agent 协作层                                  │   │
│  │                                                                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ Script   │  │ Art      │  │ Market   │  │Storyboard│            │   │
│  │  │ Agent    │  │ Agent    │  │ Agent    │  │ Agent    │            │   │
│  │  │ (编剧)   │  │ (美术)   │  │ (对标)   │  │ (故事板) │            │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘            │   │
│  │       │             │             │             │                   │   │
│  │       └─────────────┴─────────────┴─────────────┘                   │   │
│  │                         ↓                                            │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  Director_Agent (导演) - 全程审核建议，需用户确认             │  │   │
│  │  │  - 规则校验 → 项目规格一致性 → 艺术风格一致性 → 历史版本对比  │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                         ↓                                            │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  PM_Agent (项目助理) - 用户可见，版本管理                     │  │   │
│  │  │  - 版本命名: 角色_张三_v3.json                                │  │   │
│  │  │  - 修改历史、恢复版本                                         │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  │                         ↓                                            │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  System_Agent (系统) - 导出前校验                             │  │   │
│  │  │  - 标签一致性、API健康、UI检查                                │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```


---

## 四、核心模块详细方案

### 4.1 镜头分割模块 - PySceneDetect

**安装**：
```bash
pip install scenedetect[opencv]
```

**核心代码**：
```python
from scenedetect import detect, ContentDetector, split_video_ffmpeg

class SceneSplitter:
    """镜头分割器 - 基于 PySceneDetect"""
    
    def __init__(self, max_scene_duration: float = 10.0):
        self.max_duration = max_scene_duration
        self.detector = ContentDetector(threshold=27.0)
    
    def detect_scenes(self, video_path: str) -> list:
        """检测镜头边界"""
        scenes = detect(video_path, self.detector)
        return [(s[0].get_seconds(), s[1].get_seconds()) for s in scenes]
    
    def split_video(self, video_path: str, output_dir: str) -> list:
        """切割视频为片段"""
        scenes = detect(video_path, self.detector)
        split_video_ffmpeg(video_path, scenes, output_dir)
        return scenes
    
    def ensure_max_duration(self, scenes: list) -> list:
        """确保每个片段 ≤10秒"""
        result = []
        for start, end in scenes:
            duration = end - start
            if duration <= self.max_duration:
                result.append((start, end))
            else:
                # 拆分长片段
                num_parts = int(duration / self.max_duration) + 1
                part_duration = duration / num_parts
                for i in range(num_parts):
                    result.append((start + i * part_duration, 
                                   start + (i + 1) * part_duration))
        return result
```

**优势**：
- ✅ 一行代码检测镜头
- ✅ 内置 FFmpeg 切割
- ✅ 多种检测算法（ContentDetector、AdaptiveDetector）
- ✅ 活跃维护，2025年仍在更新

---

### 4.2 视频标签模块 - Gemini API

**安装**：
```bash
pip install google-generativeai
```

**核心代码**：
```python
import google.generativeai as genai
import asyncio
import json

class GeminiVideoTagger:
    """Gemini 视频标签生成器"""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.tag_prompt = """
分析这个视频片段，返回JSON格式标签：
{
    "scene_type": "室内/室外/城市/自然",
    "time": "白天/夜晚/黄昏/黎明",
    "shot_type": "全景/中景/特写/过肩",
    "mood": "紧张/浪漫/悲伤/欢乐/悬疑",
    "action": "对话/追逐/打斗/静态",
    "characters": "单人/双人/群戏/无人",
    "free_tags": ["标签1", "标签2", "标签3"],
    "summary": "一句话描述"
}
只返回JSON，不要其他内容。
"""
    
    async def generate_tags(self, video_path: str) -> dict:
        """生成视频标签"""
        video_file = genai.upload_file(video_path)
        
        # 等待处理
        while video_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        response = await self.model.generate_content_async(
            [video_file, self.tag_prompt]
        )
        
        genai.delete_file(video_file.name)
        return json.loads(response.text)
    
    async def batch_process(self, video_paths: list, batch_size: int = 5) -> list:
        """批量处理"""
        results = []
        for i in range(0, len(video_paths), batch_size):
            batch = video_paths[i:i+batch_size]
            tasks = [self.generate_tags(p) for p in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
        return results
```

**成本估算 (500GB 视频)**：
| 优化策略 | 成本 |
|----------|------|
| 无优化 | ~$106 |
| 关键帧采样 (1fps) | ~$35 |
| + Batch API | ~$18 |

---

### 4.3 向量存储模块 - Milvus

**安装**：
```bash
# 下载 docker-compose
wget https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml -O docker-compose-milvus.yml

# 启动
docker compose -f docker-compose-milvus.yml up -d

# Python 客户端
pip install pymilvus
```

**核心代码**：
```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

class MilvusVideoStore:
    """Milvus 视频向量存储"""
    
    def __init__(self, host: str = "localhost", port: int = 19530):
        connections.connect(alias="default", host=host, port=port)
        self.collection_name = "video_assets"
        self._ensure_collection()
    
    def _ensure_collection(self):
        if utility.has_collection(self.collection_name):
            return
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="video_path", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="segment_index", dtype=DataType.INT64),
            FieldSchema(name="start_time", dtype=DataType.FLOAT),
            FieldSchema(name="end_time", dtype=DataType.FLOAT),
            FieldSchema(name="tags_json", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        ]
        
        schema = CollectionSchema(fields, description="Video segments with tags")
        collection = Collection(self.collection_name, schema)
        
        # 创建 IVF_FLAT 索引
        collection.create_index("embedding", {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        })
    
    def insert(self, video_path: str, segment_index: int, 
               start_time: float, end_time: float, 
               tags: dict, embedding: list):
        """插入视频片段"""
        import json
        collection = Collection(self.collection_name)
        collection.insert([[video_path], [segment_index], [start_time], 
                          [end_time], [json.dumps(tags, ensure_ascii=False)], 
                          [embedding]])
        collection.flush()
    
    def search(self, query_embedding: list, top_k: int = 5) -> list:
        """向量搜索"""
        collection = Collection(self.collection_name)
        collection.load()
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["video_path", "segment_index", "start_time", 
                          "end_time", "tags_json"]
        )
        return results[0]
    
    def search_by_tags(self, tags: list, top_k: int = 10) -> list:
        """标签搜索"""
        collection = Collection(self.collection_name)
        collection.load()
        
        expr = " or ".join([f'tags_json like "%{t}%"' for t in tags])
        return collection.query(expr=expr, limit=top_k,
            output_fields=["video_path", "segment_index", "tags_json"])
```

**Milvus vs ChromaDB**：
| 特性 | ChromaDB | Milvus |
|------|----------|--------|
| 数据规模 | 百万级 | 亿级 |
| 生产就绪 | 开发/测试 | 生产级 |
| 分布式 | ❌ | ✅ |
| GPU 加速 | ❌ | ✅ |


---

## 五、Agent 层优化方案

### 5.1 现有 Agent 复用分析

| Agent | 现有状态 | 需要修改 | 工作量 |
|-------|----------|----------|--------|
| **Script_Agent** | ✅ 已实现 | 无 | 0 |
| **Art_Agent** | ✅ 已实现 | 无 | 0 |
| **Market_Agent** | ✅ 已实现 | 语义修正为"对标参考" | 0.5天 |
| **Director_Agent** | ✅ 已实现 | 增加四步审核、项目记忆 | 1天 |
| **PM_Agent** | ❌ 需新增 | 版本管理、文件命名 | 2天 |
| **Storyboard_Agent** | ❌ 需新增 | 素材召回、5候选缓存 | 2天 |
| **System_Agent** | ❌ 需新增 | 导出校验 | 1天 |

### 5.2 Market_Agent 修正（对标参考寻找）

**现有功能已满足需求**：
```python
# market_agent.py 已有功能
- match_by_tags(): Jaccard 相似度标签匹配 ✅
- vector_search(): 向量语义搜索 ✅
- fetch_douban_data(): 豆瓣数据获取接口 ✅
```

**只需修改**：
1. 将"市场分析"改为"对标参考寻找"
2. 调整参与时机：美术确认后、导演审核前

### 5.3 Storyboard_Agent 实现

```python
# multi-agent-workflow/backend/app/agents/storyboard_agent.py

from .base_agent import BaseAgent
from ..core.agent_types import AgentType

class StoryboardAgent(BaseAgent):
    """故事板 Agent - 素材召回与候选缓存"""
    
    def __init__(self, agent_id: str, message_bus, milvus_store, config=None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.STORYBOARD,
            message_bus=message_bus,
            capabilities=["asset_recall", "candidate_cache", "rough_cut"],
            config=config
        )
        self.milvus = milvus_store
        self._candidate_cache = {}  # scene_id -> [5 candidates]
    
    async def recall_assets(self, scene_id: str, scene_tags: list, 
                           scene_description: str) -> list:
        """素材召回 - 返回 Top 5 候选"""
        
        # 1. 标签匹配（快速）
        tag_results = self.milvus.search_by_tags(scene_tags, top_k=20)
        
        # 2. 向量搜索（语义）
        query_embedding = await self._generate_embedding(scene_description)
        vector_results = self.milvus.search(query_embedding, top_k=20)
        
        # 3. 合并排序
        candidates = self._merge_and_rank(tag_results, vector_results)[:5]
        
        # 4. 缓存 5 个候选
        self._candidate_cache[scene_id] = candidates
        
        return candidates
    
    def get_cached_candidates(self, scene_id: str) -> list:
        """获取缓存的候选（用户丝滑切换）"""
        return self._candidate_cache.get(scene_id, [])
    
    def switch_candidate(self, scene_id: str, index: int) -> dict:
        """切换候选"""
        candidates = self._candidate_cache.get(scene_id, [])
        if 0 <= index < len(candidates):
            return candidates[index]
        return None
    
    async def rough_cut(self, video_path: str, start: float, end: float, 
                       output_path: str) -> str:
        """粗剪 - 使用 FFmpeg 切割"""
        import subprocess
        cmd = [
            "ffmpeg", "-i", video_path,
            "-ss", str(start), "-to", str(end),
            "-c", "copy", "-y", output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path
    
    def _merge_and_rank(self, tag_results: list, vector_results: list) -> list:
        """合并并排序结果"""
        seen = set()
        merged = []
        
        # 交替合并，去重
        for t, v in zip(tag_results, vector_results):
            if t["video_path"] not in seen:
                merged.append(t)
                seen.add(t["video_path"])
            if v["video_path"] not in seen:
                merged.append(v)
                seen.add(v["video_path"])
        
        return merged
```

### 5.4 PM_Agent 实现（用户可见）

```python
# multi-agent-workflow/backend/app/agents/pm_agent.py

from .base_agent import BaseAgent
from ..core.agent_types import AgentType
from datetime import datetime

class PMAgent(BaseAgent):
    """项目助理 Agent - 用户可见，版本管理"""
    
    def __init__(self, agent_id: str, message_bus, db, config=None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PM,
            message_bus=message_bus,
            capabilities=["version_management", "project_context"],
            config=config
        )
        self.db = db
    
    def generate_version_name(self, content_type: str, name: str, 
                             version: int, ext: str = "json") -> str:
        """生成版本命名: 角色_张三_v3.json"""
        if name:
            return f"{content_type}_{name}_v{version}.{ext}"
        return f"{content_type}_v{version}.{ext}"
    
    async def record_version(self, project_id: str, content_type: str,
                            name: str, content: dict, agent: str) -> dict:
        """记录新版本"""
        # 获取当前版本号
        current = await self.db.query(
            "SELECT MAX(version) FROM content_versions WHERE project_id=? AND content_type=? AND name=?",
            [project_id, content_type, name]
        )
        new_version = (current[0][0] or 0) + 1
        
        # 生成版本命名
        version_name = self.generate_version_name(content_type, name, new_version)
        
        # 保存
        await self.db.execute(
            """INSERT INTO content_versions 
               (project_id, content_type, name, version, version_name, content, agent, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [project_id, content_type, name, new_version, version_name,
             json.dumps(content), agent, datetime.now().isoformat()]
        )
        
        return {"version": new_version, "version_name": version_name}
    
    async def get_version_history(self, project_id: str, 
                                  content_type: str = None) -> list:
        """获取版本历史（前端展示）"""
        query = "SELECT * FROM content_versions WHERE project_id=?"
        params = [project_id]
        
        if content_type:
            query += " AND content_type=?"
            params.append(content_type)
        
        query += " ORDER BY created_at DESC"
        return await self.db.query(query, params)
    
    async def restore_version(self, version_id: int) -> dict:
        """恢复历史版本"""
        version = await self.db.query(
            "SELECT * FROM content_versions WHERE id=?", [version_id]
        )
        if version:
            return json.loads(version[0]["content"])
        return None
    
    async def get_project_context(self, project_id: str) -> dict:
        """获取项目上下文（供 Director_Agent 使用）"""
        return {
            "specs": await self._get_project_specs(project_id),
            "style": await self._get_style_context(project_id),
            "history": await self.get_version_history(project_id),
            "decisions": await self._get_user_decisions(project_id)
        }
```


---

## 六、完整预处理管道

### 6.1 VideoPreprocessor 整合实现

```python
# Pervis PRO/backend/services/video_preprocessor.py

import os
import asyncio
from typing import List, Dict
from scenedetect import detect, ContentDetector, split_video_ffmpeg
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

class VideoPreprocessor:
    """视频预处理器 - 素材上传时自动执行完整处理流程"""
    
    def __init__(self, gemini_api_key: str, milvus_host: str = "localhost"):
        # 镜头分割
        self.scene_detector = ContentDetector(threshold=27.0)
        self.max_scene_duration = 10.0  # ≤10秒
        
        # Gemini 标签
        genai.configure(api_key=gemini_api_key)
        self.gemini = genai.GenerativeModel('gemini-2.5-flash')
        
        # 向量生成 (使用 sentence-transformers，免费本地运行)
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # Milvus 存储
        from .milvus_store import MilvusVideoStore
        self.milvus = MilvusVideoStore(host=milvus_host)
        
        # 临时目录
        self.temp_dir = "./temp/segments"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def preprocess(self, video_path: str, asset_id: str) -> Dict:
        """完整预处理流程"""
        
        # Step 1: PySceneDetect 镜头分割
        print(f"[1/4] 镜头分割: {video_path}")
        scenes = detect(video_path, self.scene_detector)
        scene_times = [(s[0].get_seconds(), s[1].get_seconds()) for s in scenes]
        
        # Step 2: 确保 ≤10秒 并切割
        print(f"[2/4] 切割视频片段...")
        segments = self._ensure_max_duration(scene_times)
        segment_paths = await self._split_video(video_path, segments, asset_id)
        
        # Step 3: Gemini 标签生成
        print(f"[3/4] Gemini 标签生成 ({len(segment_paths)} 个片段)...")
        tags_list = await self._batch_generate_tags(segment_paths)
        
        # Step 4: 存储到 Milvus
        print(f"[4/4] 存储到 Milvus...")
        for i, (seg_path, tags, (start, end)) in enumerate(
            zip(segment_paths, tags_list, segments)):
            
            # 生成向量 (基于标签文本)
            tag_text = " ".join(tags.get("free_tags", []) + [tags.get("summary", "")])
            embedding = self.embedder.encode(tag_text).tolist()
            
            self.milvus.insert(
                video_path=video_path,
                segment_index=i,
                start_time=start,
                end_time=end,
                tags=tags,
                embedding=embedding
            )
        
        return {
            "asset_id": asset_id,
            "video_path": video_path,
            "segments_count": len(segments),
            "segments": segments,
            "tags": tags_list,
            "status": "completed"
        }
    
    def _ensure_max_duration(self, scenes: List[tuple]) -> List[tuple]:
        """确保每个片段 ≤10秒"""
        result = []
        for start, end in scenes:
            duration = end - start
            if duration <= self.max_scene_duration:
                result.append((start, end))
            else:
                num_parts = int(duration / self.max_scene_duration) + 1
                part_dur = duration / num_parts
                for i in range(num_parts):
                    result.append((start + i * part_dur, start + (i + 1) * part_dur))
        return result
    
    async def _split_video(self, video_path: str, segments: List[tuple], 
                          asset_id: str) -> List[str]:
        """使用 FFmpeg 切割视频"""
        import subprocess
        paths = []
        
        for i, (start, end) in enumerate(segments):
            output = f"{self.temp_dir}/{asset_id}_seg{i:04d}.mp4"
            cmd = [
                "ffmpeg", "-i", video_path,
                "-ss", str(start), "-to", str(end),
                "-c:v", "libx264", "-crf", "28", "-preset", "fast",
                "-c:a", "aac", "-y", output
            ]
            subprocess.run(cmd, capture_output=True)
            paths.append(output)
        
        return paths
    
    async def _batch_generate_tags(self, video_paths: List[str], 
                                   batch_size: int = 3) -> List[Dict]:
        """批量 Gemini 标签生成"""
        results = []
        
        for i in range(0, len(video_paths), batch_size):
            batch = video_paths[i:i+batch_size]
            tasks = [self._generate_tags_single(p) for p in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for r in batch_results:
                if isinstance(r, Exception):
                    results.append({"error": str(r), "free_tags": [], "summary": ""})
                else:
                    results.append(r)
            
            # 避免 API 限流
            await asyncio.sleep(1)
        
        return results
    
    async def _generate_tags_single(self, video_path: str) -> Dict:
        """单个视频标签生成"""
        import json
        
        prompt = """分析视频，返回JSON：
{"scene_type":"室内/室外","time":"白天/夜晚","shot_type":"全景/中景/特写",
"mood":"紧张/浪漫/悲伤/欢乐","action":"对话/追逐/静态",
"characters":"单人/双人/群戏/无人","free_tags":["标签1","标签2"],"summary":"一句话"}
只返回JSON。"""
        
        video_file = genai.upload_file(video_path)
        
        while video_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        response = await self.gemini.generate_content_async([video_file, prompt])
        genai.delete_file(video_file.name)
        
        # 解析 JSON
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "").strip()
        
        return json.loads(text)
```

### 6.2 使用示例

```python
# 素材上传时调用
async def on_asset_upload(file_path: str, asset_id: str):
    preprocessor = VideoPreprocessor(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        milvus_host="localhost"
    )
    
    result = await preprocessor.preprocess(file_path, asset_id)
    print(f"预处理完成: {result['segments_count']} 个片段")
    return result
```

---

## 七、数据库模型

### 7.1 新增表结构

```sql
-- content_versions 表 (PM_Agent 版本管理)
CREATE TABLE IF NOT EXISTS content_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(100) NOT NULL,
    content_type VARCHAR(50) NOT NULL,  -- 角色/场次/Logline 等
    name VARCHAR(100),                   -- 张三/场次1 等
    version INTEGER NOT NULL,
    version_name VARCHAR(200) NOT NULL,  -- 角色_张三_v3.json
    content TEXT NOT NULL,               -- JSON 内容
    agent VARCHAR(50) NOT NULL,          -- 生成的 Agent
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_project_type (project_id, content_type)
);

-- user_decisions 表 (用户决策记录)
CREATE TABLE IF NOT EXISTS user_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(100) NOT NULL,
    version_id INTEGER NOT NULL,
    decision VARCHAR(20) NOT NULL,       -- accepted/rejected/modified
    feedback TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (version_id) REFERENCES content_versions(id)
);

-- project_specs 表 (项目规格)
CREATE TABLE IF NOT EXISTS project_specs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(100) UNIQUE NOT NULL,
    duration INTEGER,                    -- 时长(秒)
    aspect_ratio VARCHAR(20),            -- 16:9
    frame_rate INTEGER,                  -- 24
    resolution VARCHAR(20),              -- 1920x1080
    style_description TEXT,              -- 风格描述
    reference_projects TEXT,             -- 对标项目 JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```


---

## 八、实施计划

### 8.1 Phase 1: 基础设施 (3天)

| 任务 | 工具 | 命令 | 产出 |
|------|------|------|------|
| 安装 PySceneDetect | pip | `pip install scenedetect[opencv]` | 镜头分割能力 |
| 安装 Gemini SDK | pip | `pip install google-generativeai` | 视频标签能力 |
| 部署 Milvus | Docker | `docker compose up -d` | 向量存储 |
| 安装 pymilvus | pip | `pip install pymilvus` | Python 客户端 |
| 安装 sentence-transformers | pip | `pip install sentence-transformers` | 向量生成 |

### 8.2 Phase 2: 预处理管道 (2天)

| 任务 | 文件 | 说明 |
|------|------|------|
| 创建 MilvusVideoStore | `backend/services/milvus_store.py` | Milvus 封装 |
| 创建 VideoPreprocessor | `backend/services/video_preprocessor.py` | 完整预处理 |
| 集成到素材上传 | `backend/routers/assets.py` | 上传时自动处理 |

### 8.3 Phase 3: Agent 层 (4天)

| 任务 | 文件 | 说明 |
|------|------|------|
| 修正 Market_Agent | `agents/market_agent.py` | 语义改为对标参考 |
| 增强 Director_Agent | `agents/director_agent.py` | 四步审核、项目记忆 |
| 新增 PM_Agent | `agents/pm_agent.py` | 版本管理 |
| 新增 Storyboard_Agent | `agents/storyboard_agent.py` | 素材召回 |
| 新增 System_Agent | `agents/system_agent.py` | 导出校验 |
| 更新 agent_types.py | `core/agent_types.py` | 添加新 Agent 类型 |

### 8.4 Phase 4: API 层 (2天)

| 任务 | 端点 | 说明 |
|------|------|------|
| 版本管理 API | `GET/POST /api/wizard/versions` | PM_Agent |
| 素材召回 API | `POST /api/wizard/recall-assets` | Storyboard_Agent |
| 候选切换 API | `POST /api/wizard/switch-candidate` | 5候选切换 |
| 导出校验 API | `POST /api/wizard/validate-export` | System_Agent |

### 8.5 Phase 5: 前端集成 (3天)

| 任务 | 组件 | 说明 |
|------|------|------|
| 版本历史面板 | `VersionHistoryPanel.tsx` | 显示版本号、修改历史 |
| Agent 状态面板 | `AgentStatusPanel.tsx` | 显示 Agent 工作状态 |
| 候选切换 UI | `CandidateSwitcher.tsx` | 5候选丝滑切换 |

---

## 九、成本总结

### 9.1 开发成本

| 阶段 | 工时 | 说明 |
|------|------|------|
| Phase 1 基础设施 | 3天 | 安装配置 |
| Phase 2 预处理管道 | 2天 | 核心功能 |
| Phase 3 Agent 层 | 4天 | 业务逻辑 |
| Phase 4 API 层 | 2天 | 接口开发 |
| Phase 5 前端集成 | 3天 | UI 组件 |
| **总计** | **14天** | - |

### 9.2 运行成本

| 项目 | 成本 | 说明 |
|------|------|------|
| Gemini 视频标签 | ~$18-35 / 500GB | 一次性预处理 |
| Milvus | $0 | 自托管 Docker |
| PySceneDetect | $0 | 开源 |
| sentence-transformers | $0 | 本地运行 |
| **新素材增量** | ~$0.05/小时视频 | 持续成本 |

### 9.3 节省对比

| 方案 | 开发时间 | 说明 |
|------|----------|------|
| 从头开发 | ~38天 | 自研所有模块 |
| 本方案 | ~14天 | 使用成熟开源 |
| **节省** | **63%** | - |

---

## 十、快速启动命令

```bash
# 1. 安装 Python 依赖
pip install scenedetect[opencv] google-generativeai pymilvus sentence-transformers

# 2. 启动 Milvus
wget https://github.com/milvus-io/milvus/releases/download/v2.4.0/milvus-standalone-docker-compose.yml
docker compose -f milvus-standalone-docker-compose.yml up -d

# 3. 验证 Milvus
docker compose ps  # 应该看到 3 个容器运行中

# 4. 设置环境变量
set GEMINI_API_KEY=your_api_key_here

# 5. 测试预处理
py -c "from backend.services.video_preprocessor import VideoPreprocessor; print('OK')"
```

---

## 十一、技术栈总结

```
┌─────────────────────────────────────────────────────────────────┐
│                    技术栈一览                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  镜头分割     PySceneDetect          pip install               │
│  视频标签     Gemini 2.5 Flash API   $0.50/1M tokens           │
│  向量生成     sentence-transformers  本地免费                   │
│  向量存储     Milvus 2.4             Docker 自托管              │
│  视频处理     FFmpeg                 已集成                     │
│  Agent 架构   BaseAgent              已实现                     │
│  消息总线     MessageBus             已实现                     │
│  标签匹配     Jaccard + 向量搜索     已实现                     │
│                                                                  │
│  全部成熟技术，可直接 pip/docker 安装，无需从头开发             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 十二、风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Gemini API 限流 | 批量处理 + 延时 + 重试机制 |
| Milvus 内存占用 | Standalone 模式，8GB 内存足够百万向量 |
| 镜头检测不准 | 调整 threshold 参数，或使用 AdaptiveDetector |
| 网络问题 | Gemini 支持断点续传，Milvus 本地部署 |

---

**文档版本**: v1.0
**创建日期**: 2025-12-25
**作者**: Kiro AI Assistant
