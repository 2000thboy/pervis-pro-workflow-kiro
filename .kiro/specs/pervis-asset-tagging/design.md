# 素材标签与向量搜索系统设计

## 1. 标签层级架构

```
┌─────────────────────────────────────────────────────────────┐
│                      标签层级体系                            │
├─────────────────────────────────────────────────────────────┤
│  L1 一级标签（必填单选）                                      │
│  ├── scene_type: INT | EXT | INT-EXT                        │
│  ├── time_of_day: DAY | NIGHT | DAWN | DUSK                 │
│  └── shot_size: ECU | CU | MCU | MS | MLS | LS | ELS        │
├─────────────────────────────────────────────────────────────┤
│  L2 二级标签（必填单选）                                      │
│  ├── camera_move: STATIC | PAN | TILT | DOLLY | ...         │
│  ├── action_type: FIGHT | CHASE | DIALOGUE | IDLE | ...     │
│  └── mood: TENSE | SAD | HAPPY | CALM | EPIC | ...          │
├─────────────────────────────────────────────────────────────┤
│  L3 三级标签（可选多选）                                      │
│  ├── characters: ["角色1", "角色2", ...]                     │
│  ├── props: ["道具1", "道具2", ...]                          │
│  ├── vfx: ["特效1", "特效2", ...]                            │
│  └── environment: ["环境1", "环境2", ...]                    │
├─────────────────────────────────────────────────────────────┤
│  L4 四级标签（自由标签）                                      │
│  ├── free_tags: ["标签1", "标签2", ...] (max 10)            │
│  ├── source_work: "作品名称"                                 │
│  └── summary: "内容描述" (max 50 chars)                      │
└─────────────────────────────────────────────────────────────┘
```

## 2. 标签数据结构

```python
@dataclass
class AssetTags:
    """素材标签"""
    # L1 一级标签（必填）
    scene_type: str      # INT | EXT | INT-EXT
    time_of_day: str     # DAY | NIGHT | DAWN | DUSK | UNKNOWN
    shot_size: str       # ECU | CU | MCU | MS | MLS | LS | ELS
    
    # L2 二级标签（必填）
    camera_move: str     # STATIC | PAN | TILT | DOLLY | CRANE | HANDHELD | ZOOM
    action_type: str     # FIGHT | CHASE | DIALOGUE | IDLE | RUN | FLY | TRANSFORM | SKILL
    mood: str            # TENSE | SAD | HAPPY | CALM | HORROR | ROMANTIC | EPIC | NEUTRAL
    
    # L3 三级标签（可选）
    characters: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    vfx: List[str] = field(default_factory=list)
    environment: List[str] = field(default_factory=list)
    
    # L4 四级标签（自由）
    free_tags: List[str] = field(default_factory=list)  # max 10
    source_work: str = ""
    summary: str = ""  # max 50 chars
```

## 3. 向量搜索架构

```
┌─────────────────────────────────────────────────────────────┐
│                     向量搜索系统                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Ollama     │    │  嵌入服务    │    │  向量存储    │     │
│  │  本地模型   │───▶│  Embedding  │───▶│  Vector DB  │     │
│  │             │    │  Service    │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│        │                   │                  │             │
│        ▼                   ▼                  ▼             │
│  nomic-embed-text    生成 768 维向量      HNSW 索引         │
│  或 bge-m3                                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     搜索流程                                 │
│                                                             │
│  查询文本 ──▶ 嵌入向量 ──▶ 向量搜索 ──▶ 结果排序 ──▶ Top K  │
│      │                         │                            │
│      ▼                         ▼                            │
│  标签解析 ──────────────▶ 标签过滤 ──────────────────────▶  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 4. 混合搜索策略

### 4.1 搜索模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| `TAG_ONLY` | 仅标签匹配 | 精确筛选 |
| `VECTOR_ONLY` | 仅向量搜索 | 模糊语义搜索 |
| `HYBRID` | 混合搜索 | 默认推荐 |
| `FILTER_THEN_RANK` | 先过滤后排序 | 大规模数据 |

### 4.2 混合搜索算法

```python
def hybrid_search(query: str, tags: Dict, weights: Tuple[float, float] = (0.4, 0.6)):
    tag_weight, vector_weight = weights
    
    # 1. 标签搜索
    tag_results = search_by_tags(tags, top_k=50)
    
    # 2. 向量搜索
    query_embedding = embed(query)
    vector_results = search_by_vector(query_embedding, top_k=50)
    
    # 3. 结果融合
    merged = {}
    for r in tag_results:
        merged[r.id] = {"tag_score": r.score, "vector_score": 0}
    for r in vector_results:
        if r.id in merged:
            merged[r.id]["vector_score"] = r.score
        else:
            merged[r.id] = {"tag_score": 0, "vector_score": r.score}
    
    # 4. 计算最终分数
    final_results = []
    for id, scores in merged.items():
        final_score = tag_weight * scores["tag_score"] + vector_weight * scores["vector_score"]
        final_results.append((id, final_score))
    
    # 5. 排序返回
    return sorted(final_results, key=lambda x: x[1], reverse=True)[:5]
```

## 5. 标签生成流程

```
┌─────────────────────────────────────────────────────────────┐
│                     标签生成流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  素材文件 ──▶ 文件名解析 ──▶ 基础标签                        │
│      │                                                      │
│      ▼                                                      │
│  视觉分析 ──▶ LLM 增强 ──▶ 完整标签                         │
│  (可选)       (可选)                                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     标签验证                                 │
│                                                             │
│  1. 一级标签必须有值（默认 UNKNOWN）                         │
│  2. 二级标签必须有值（默认 NEUTRAL/STATIC/IDLE）            │
│  3. 三级标签可为空                                          │
│  4. 四级标签 free_tags 最多 10 个                           │
│  5. summary 最多 50 字符                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 6. 技术选型

### 6.1 嵌入模型

**推荐方案：Ollama + nomic-embed-text**

```bash
# 安装嵌入模型
ollama pull nomic-embed-text

# 或使用 bge-m3（中文效果更好）
ollama pull bge-m3
```

### 6.2 向量存储

**方案 A：内存存储（开发/小规模）**
- 使用 `MemoryVideoStore`
- 支持 NumPy 余弦相似度计算
- 适合 < 10000 素材

**方案 B：Milvus（生产/大规模）**
- 需要 Docker 环境
- 支持 HNSW/IVF_FLAT 索引
- 适合 > 10000 素材

### 6.3 NumPy 兼容性

当前问题：`sentence_transformers` 与 NumPy 2.x 不兼容

解决方案：
1. **使用 Ollama 嵌入**（推荐）- 绕过 NumPy 问题
2. **降级 NumPy** - `pip install numpy<2`
3. **等待库更新** - sentence_transformers 更新兼容

## 7. 关键帧提取架构

```
┌─────────────────────────────────────────────────────────────┐
│                    关键帧提取流程                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  视频文件 ──▶ PySceneDetect ──▶ 场景分割 ──▶ 关键帧列表     │
│      │            │                │                        │
│      ▼            ▼                ▼                        │
│  FFmpeg ────▶ 帧提取 ────────▶ 缩略图生成                   │
│      │                             │                        │
│      ▼                             ▼                        │
│  元数据 ◀──────────────────── 帧坐标记录                    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    关键帧数据结构                            │
│                                                             │
│  @dataclass                                                 │
│  class KeyFrame:                                            │
│      frame_index: int          # 帧序号                     │
│      timestamp: float          # 时间戳（秒）               │
│      timecode: str             # SMPTE 时间码               │
│      image_path: str           # 缩略图路径                 │
│      scene_id: int             # 场景 ID                    │
│      motion_score: float       # 运动强度 (0-1)             │
│      is_scene_start: bool      # 是否场景起始帧             │
│      visual_embedding: List[float]  # CLIP 视觉向量         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.1 提取策略配置

```python
@dataclass
class KeyFrameConfig:
    strategy: str = "hybrid"      # scene_change | interval | motion | hybrid
    min_frames: int = 1           # 最小帧数
    max_frames: int = 20          # 最大帧数
    interval_seconds: float = 5.0 # 固定间隔（秒）
    motion_threshold: float = 0.3 # 运动阈值
    thumbnail_size: Tuple[int, int] = (320, 180)  # 缩略图尺寸
```

### 7.2 关键帧存储

```python
# 关键帧存储路径结构
data/
├── keyframes/
│   ├── {asset_id}/
│   │   ├── frame_0000_00.00.jpg    # 帧序号_时间戳
│   │   ├── frame_0150_05.00.jpg
│   │   └── metadata.json           # 帧元数据
```

## 8. CLIP 视觉嵌入架构

```
┌─────────────────────────────────────────────────────────────┐
│                   CLIP 视觉嵌入系统                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  关键帧     │    │  CLIP 模型  │    │  向量存储    │     │
│  │  图像       │───▶│  视觉编码   │───▶│  Visual DB  │     │
│  │             │    │             │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                            │                  │             │
│                            ▼                  ▼             │
│                     512/768 维向量       HNSW 索引          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    跨模态搜索流程                            │
│                                                             │
│  文本查询 ──▶ CLIP 文本编码 ──▶ 文本向量                    │
│                                      │                      │
│                                      ▼                      │
│  图像查询 ──▶ CLIP 图像编码 ──▶ 图像向量 ──▶ 相似度搜索    │
│                                      │                      │
│                                      ▼                      │
│                              匹配关键帧 + 时间戳             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.1 CLIP 服务设计

```python
class CLIPEmbeddingService:
    """CLIP 视觉嵌入服务"""
    
    def __init__(self, model_name: str = "llava:7b"):
        self.model_name = model_name
        self.dimension = 768  # 或 512
    
    async def embed_image(self, image_path: str) -> List[float]:
        """图像嵌入"""
        pass
    
    async def embed_text(self, text: str) -> List[float]:
        """文本嵌入（与图像同空间）"""
        pass
    
    async def embed_images_batch(self, image_paths: List[str]) -> List[List[float]]:
        """批量图像嵌入"""
        pass
    
    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        pass
```

### 8.2 视觉向量存储

```python
class VisualVectorStore:
    """视觉向量存储"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.vectors: Dict[str, List[float]] = {}  # keyframe_id -> vector
        self.metadata: Dict[str, Dict] = {}        # keyframe_id -> metadata
    
    def add(self, keyframe_id: str, vector: List[float], metadata: Dict):
        """添加视觉向量"""
        pass
    
    def search(self, query_vector: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """搜索相似关键帧"""
        pass
    
    def search_by_text(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """文本搜索图像"""
        pass
```

## 9. 多模态搜索架构

```
┌─────────────────────────────────────────────────────────────┐
│                    多模态搜索系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户查询 ──┬──▶ 文本嵌入 ──▶ 文本向量搜索 ──┐              │
│             │                                │              │
│             ├──▶ 标签解析 ──▶ 标签过滤 ──────┤              │
│             │                                │              │
│             └──▶ CLIP 编码 ──▶ 视觉向量搜索 ─┤              │
│                                              │              │
│                                              ▼              │
│                                        结果融合排序          │
│                                              │              │
│                                              ▼              │
│                                   返回素材 + 关键帧 + 时间戳 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 9.1 多模态搜索策略

| 模式 | 说明 | 权重配置 |
|------|------|----------|
| `TEXT_ONLY` | 仅文本语义搜索 | text=1.0 |
| `VISUAL_ONLY` | 仅视觉相似搜索 | visual=1.0 |
| `TAG_ONLY` | 仅标签匹配 | tag=1.0 |
| `MULTIMODAL` | 多模态融合 | text=0.3, visual=0.4, tag=0.3 |

### 9.2 搜索结果数据结构

```python
@dataclass
class MultimodalSearchResult:
    asset_id: str                    # 素材 ID
    asset_path: str                  # 素材路径
    final_score: float               # 最终分数
    text_score: float                # 文本相似度
    visual_score: float              # 视觉相似度
    tag_score: float                 # 标签匹配度
    matched_keyframes: List[KeyFrameMatch]  # 匹配的关键帧
    tags: AssetTags                  # 素材标签
    
@dataclass
class KeyFrameMatch:
    keyframe_id: str                 # 关键帧 ID
    timestamp: float                 # 时间戳
    timecode: str                    # 时间码
    thumbnail_path: str              # 缩略图路径
    similarity: float                # 相似度分数
    suggested_in_point: float        # 建议入点
    suggested_out_point: float       # 建议出点
```

## 10. API 设计

### 10.1 标签 API

```python
# 生成标签
POST /api/assets/{id}/tags
{
    "use_llm": true,
    "use_vision": false
}

# 更新标签
PUT /api/assets/{id}/tags
{
    "scene_type": "INT",
    "action_type": "FIGHT",
    ...
}

# 批量打标
POST /api/assets/batch-tag
{
    "asset_ids": ["id1", "id2"],
    "use_llm": true
}
```

### 10.2 搜索 API

```python
# 混合搜索
POST /api/search
{
    "query": "炭治郎使用水之呼吸战斗",
    "tags": {
        "action_type": "FIGHT",
        "characters": ["炭治郎"]
    },
    "mode": "HYBRID",
    "weights": [0.4, 0.6],
    "top_k": 5
}

# 响应
{
    "results": [
        {
            "asset_id": "asset_001",
            "score": 0.85,
            "tag_score": 0.9,
            "vector_score": 0.82,
            "tags": {...},
            "thumbnail": "..."
        }
    ],
    "total": 5,
    "search_time_ms": 120
}
```



### 10.3 关键帧 API

```python
# 提取关键帧
POST /api/assets/{id}/keyframes
{
    "strategy": "hybrid",
    "max_frames": 20,
    "generate_embeddings": true
}

# 获取关键帧列表
GET /api/assets/{id}/keyframes

# 响应
{
    "asset_id": "asset_001",
    "keyframes": [
        {
            "keyframe_id": "kf_001",
            "frame_index": 0,
            "timestamp": 0.0,
            "timecode": "00:00:00:00",
            "thumbnail_url": "/api/keyframes/kf_001/thumbnail",
            "is_scene_start": true,
            "has_embedding": true
        }
    ],
    "total": 10
}
```

### 10.4 多模态搜索 API

```python
# 多模态搜索
POST /api/search/multimodal
{
    "query": "炭治郎使用水之呼吸战斗",
    "tags": {
        "action_type": "FIGHT"
    },
    "mode": "MULTIMODAL",
    "weights": {
        "text": 0.3,
        "visual": 0.4,
        "tag": 0.3
    },
    "top_k": 5,
    "include_keyframes": true
}

# 响应
{
    "results": [
        {
            "asset_id": "asset_001",
            "final_score": 0.85,
            "text_score": 0.82,
            "visual_score": 0.88,
            "tag_score": 0.85,
            "tags": {...},
            "matched_keyframes": [
                {
                    "keyframe_id": "kf_005",
                    "timestamp": 12.5,
                    "timecode": "00:00:12:15",
                    "thumbnail_url": "...",
                    "similarity": 0.88,
                    "suggested_in_point": 10.0,
                    "suggested_out_point": 15.0
                }
            ]
        }
    ],
    "total": 5,
    "search_time_ms": 250
}
```

### 10.5 图像搜索 API

```python
# 以图搜图
POST /api/search/by-image
Content-Type: multipart/form-data
{
    "image": <file>,
    "top_k": 10
}

# 响应
{
    "results": [
        {
            "asset_id": "asset_001",
            "keyframe_id": "kf_003",
            "similarity": 0.92,
            "timestamp": 8.5,
            "thumbnail_url": "..."
        }
    ]
}
```

---

## 11. 音频标签与 RAG 系统设计（新增 2025-12-29）

### 11.1 音频标签数据结构

```python
@dataclass
class AudioTags:
    """音频标签"""
    # 基础分类
    audio_type: str          # BGM | SFX | VO | AMBIENT | FOLEY
    
    # BGM 特有标签
    bgm_style: str           # ORCHESTRAL | ELECTRONIC | ROCK | JAZZ | FOLK | CLASSICAL | POP
    
    # 情绪和节奏
    audio_mood: str          # TENSE | SAD | HAPPY | CALM | HORROR | ROMANTIC | EPIC | MYSTERIOUS
    tempo: str               # SLOW | MEDIUM | FAST | VARIABLE
    bpm: int                 # 实际 BPM 值
    bpm_range: str           # 60-80 | 80-100 | 100-120 | 120-140 | 140+
    
    # 乐器和场景
    instruments: List[str]   # 主要乐器列表
    scene_fit: str           # ACTION | DIALOGUE | TRANSITION | MONTAGE | CLIMAX
    
    # 技术信息
    duration: float          # 时长（秒）
    sample_rate: int         # 采样率
    channels: int            # 声道数
    
    # 自由标签
    free_tags: List[str]     # 自由标签（最多 10 个）
    summary: str             # 一句话描述（最多 50 字）
```

### 11.2 音频向量嵌入架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    音频向量嵌入系统                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  音频文件   │    │  特征提取   │    │  向量存储   │             │
│  │  (WAV/MP3) │───▶│  (CLAP/    │───▶│  Audio DB   │             │
│  │            │    │  AudioCLIP) │    │             │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                  │                  │                      │
│        ▼                  ▼                  ▼                      │
│  音频预处理         512/768 维向量       HNSW 索引                  │
│  - 格式转换                                                         │
│  - 重采样                                                           │
│  - 波形生成                                                         │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                    音频特征提取                                      │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  梅尔频谱 (Mel Spectrogram)                                  │   │
│  │  ████████████████████████████████████████████████████████   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  MFCC (Mel-frequency cepstral coefficients)                 │   │
│  │  ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃▄▅▆▇█▇▆▅▄▃▂▁                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  节奏特征 (Rhythm Features)                                  │   │
│  │  BPM: 120  |  节拍: 4/4  |  强度: ▃▃▃▃▃▃▃▃                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.3 音频 RAG 检索流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                    音频 RAG 检索流程                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  用户查询/场景描述                                                   │
│  "需要一段紧张的战斗背景音乐，节奏快，有打击乐"                     │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 1: 查询解析                                            │   │
│  │  提取关键词: 紧张, 战斗, 背景音乐, 节奏快, 打击乐            │   │
│  │  推断标签:                                                    │   │
│  │    audio_type: BGM                                           │   │
│  │    audio_mood: TENSE                                         │   │
│  │    tempo: FAST                                               │   │
│  │    scene_fit: ACTION                                         │   │
│  │    instruments: ["鼓", "打击乐"]                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 2: 标签匹配 (Top 30)                                   │   │
│  │  SELECT * FROM audio_assets                                  │   │
│  │  WHERE audio_type = 'BGM'                                    │   │
│  │    AND audio_mood = 'TENSE'                                  │   │
│  │    AND tempo = 'FAST'                                        │   │
│  │  ORDER BY tag_match_score DESC                               │   │
│  │  LIMIT 30                                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 3: 向量搜索 (Top 30)                                   │   │
│  │  query_embedding = embed_text("紧张的战斗背景音乐")          │   │
│  │  vector_search(query_embedding, top_k=30)                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 4: 结果融合 (Top 10)                                   │   │
│  │  final_score = 0.4 * tag_score + 0.6 * vector_score         │   │
│  │  排序并返回 Top 10                                           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 5: 返回结果 (Top 5)                                    │   │
│  │  返回音频信息 + 波形预览 + 标签 + 匹配分数                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.4 音频预处理管道

```
┌─────────────────────────────────────────────────────────────────────┐
│                    音频预处理管道                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  音频文件上传                                                        │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 1: 格式转换                                            │   │
│  │  - 统一转换为 WAV 格式（用于处理）                           │   │
│  │  - 保留 MP3 格式（用于播放）                                 │   │
│  │  - 重采样到 44100Hz                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 2: 特征提取                                            │   │
│  │  - 时长、采样率、声道数                                      │   │
│  │  - BPM 检测（librosa.beat.tempo）                            │   │
│  │  - 梅尔频谱生成                                              │   │
│  │  - MFCC 提取                                                 │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 3: AI 标签生成                                         │   │
│  │  - 调用 LLM 分析音频特征                                     │   │
│  │  - 生成 audio_type, bgm_style, audio_mood 等标签             │   │
│  │  - 生成一句话描述                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 4: 向量生成                                            │   │
│  │  - 使用 CLAP/AudioCLIP 生成音频向量                          │   │
│  │  - 或使用文本嵌入（基于标签和描述）                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 5: 波形图生成                                          │   │
│  │  - 生成波形数据数组（用于前端显示）                          │   │
│  │  - 生成波形图片（可选）                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│         │                                                            │
│         ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Step 6: 存储                                                │   │
│  │  - 音频文件存储到文件系统                                    │   │
│  │  - 标签和元数据存储到数据库                                  │   │
│  │  - 向量存储到向量数据库                                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.5 音频 RAG API 设计

```python
# 音频搜索
POST /api/search/audio
{
    "query": "紧张的战斗背景音乐",
    "tags": {
        "audio_type": "BGM",
        "audio_mood": "TENSE"
    },
    "mode": "HYBRID",
    "top_k": 5
}

# 响应
{
    "results": [
        {
            "audio_id": "audio_001",
            "audio_path": "/audio/battle_theme_01.mp3",
            "final_score": 0.92,
            "tag_score": 0.95,
            "vector_score": 0.90,
            "tags": {
                "audio_type": "BGM",
                "bgm_style": "ORCHESTRAL",
                "audio_mood": "TENSE",
                "tempo": "FAST",
                "bpm": 140,
                "instruments": ["鼓", "弦乐", "铜管"],
                "scene_fit": "ACTION"
            },
            "duration": 180.5,
            "waveform_data": [...],
            "preview_url": "/api/audio/preview/audio_001"
        }
    ],
    "total": 5,
    "search_time_ms": 150
}

# 场景匹配推荐
POST /api/search/audio/scene-match
{
    "scene_description": "主角与反派的最终决战，紧张激烈",
    "scene_type": "ACTION",
    "mood": "TENSE",
    "duration_hint": 120  # 期望时长（秒）
}

# 响应
{
    "recommendations": [
        {
            "audio_id": "audio_001",
            "match_reason": "情绪匹配(TENSE)、场景匹配(ACTION)、时长接近",
            "confidence": 0.95,
            ...
        }
    ]
}

# 音频预处理
POST /api/audio/preprocess
{
    "audio_ids": ["audio_001", "audio_002"]
}

# 响应
{
    "task_id": "task_xxx",
    "status": "processing",
    "total": 2,
    "processed": 0
}
```
