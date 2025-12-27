# 素材标签与向量搜索系统实现计划

## 概述

实现完整的标签层级体系和向量搜索功能，支持精确搜索和模糊语义搜索。

## Phase 1: 标签层级体系（2天）

- [x] 1.1 定义标签数据结构
  - 创建 `backend/models/asset_tags.py` ✅
  - 实现 `AssetTags` 数据类 ✅
  - 定义一级到四级标签枚举 ✅
  - 实现标签验证逻辑 ✅
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 1.2 实现标签生成器
  - 更新 `backend/services/tag_manager.py` ✅
  - 实现文件名解析规则（支持中英文）✅
  - 实现关键词到标签的映射 ✅
  - 支持动漫素材的特殊关键词 ✅
  - _Requirements: 5.1_

- [x] 1.3 实现 LLM 标签增强
  - 更新 `backend/services/agents/art_agent.py` ✅
  - 使用 Ollama 本地模型生成标签 ✅
  - 实现标签格式化和验证 ✅
  - 支持批量标签生成 ✅
  - _Requirements: 5.1_

- [x] 1.4 标签存储和索引
  - 更新 `backend/services/milvus_store.py` ✅
  - 添加标签字段索引 ✅
  - 实现标签搜索接口 ✅
  - 支持多级标签过滤 ✅
  - _Requirements: 3.3_

## Phase 2: 向量嵌入服务（2天）

- [x] 2.1 实现 Ollama 嵌入服务
  - 创建 `backend/services/ollama_embedding.py` ✅
  - 支持 `nomic-embed-text` 模型 ✅
  - 支持 `bge-m3` 模型（中文优化）✅
  - 实现批量嵌入接口 ✅
  - _Requirements: 3.1, 3.2_

- [x] 2.2 嵌入模型管理
  - 实现模型可用性检查 ✅
  - 自动回退到备选模型 ✅
  - 缓存嵌入结果 ✅
  - _Requirements: 3.2_

- [x] 2.3 向量存储集成
  - 更新 `MemoryVideoStore` 支持向量搜索 ✅
  - 实现余弦相似度计算（纯 Python，避免 NumPy 2.x 问题）✅
  - 支持向量索引持久化 ✅
  - _Requirements: 3.3_

## Phase 3: 混合搜索实现（2天）

- [x] 3.1 实现搜索策略
  - 创建 `backend/services/search_service.py` ✅
  - 实现 `TAG_ONLY` 模式 ✅
  - 实现 `VECTOR_ONLY` 模式 ✅
  - 实现 `HYBRID` 模式 ✅
  - 实现 `FILTER_THEN_RANK` 模式 ✅
  - _Requirements: 3.4, 4.1_

- [x] 3.2 结果融合算法
  - 实现标签分数计算（带权重）✅
  - 实现向量分数归一化 ✅
  - 实现混合分数计算 ✅
  - 支持自定义权重配置 ✅
  - _Requirements: 4.2_

- [x] 3.3 搜索 API
  - 创建 `backend/routers/search.py` ✅
  - 实现 `POST /api/search` 端点 ✅
  - 支持查询参数配置 ✅
  - 返回详细的匹配信息 ✅
  - _Requirements: 7.2_

## Phase 4: 批量索引工具（1天）

- [x] 4.1 更新批量索引脚本
  - 更新 `batch_asset_indexing.py` ✅
  - 集成新的标签层级体系 ✅
  - 集成 Ollama 嵌入服务 ✅
  - 支持增量索引 ✅
  - _Requirements: 5.3_

- [x] 4.2 索引进度和报告
  - 实现索引进度显示 ✅
  - 生成标签覆盖率报告 ✅
  - 生成向量覆盖率报告 ✅
  - _Requirements: 5.1, 5.2_

## Phase 5: 测试和验证（1天）

- [x] 5.1 单元测试
  - 标签生成测试 ✅
  - 向量嵌入测试 ✅
  - 搜索功能测试 ✅
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 5.2 集成测试 ✅ (2025-12-26)
  - 完整工作流测试 ✅
  - 搜索准确率测试 ✅ (100% 准确率)
  - 性能基准测试 ✅ (平均 0.3ms，最大 0.5ms)
  - 测试结果: 10/10 全部通过
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 5.3 MVP 验证 ✅ (2025-12-26)
  - 索引 300+ 素材 ✅
  - 验证标签覆盖率 ≥ 80% ✅
  - 验证搜索 Top5 命中率 ≥ 80% ✅ (100%)
  - 验证搜索响应时间 < 500ms ✅ (< 1ms)
  - _Requirements: 5.1, 5.2, 5.3_

## Phase 6: 关键帧提取实现（2天）

- [x] 6.1 关键帧提取服务
  - 创建 `backend/services/keyframe_extractor.py` ✅
  - 实现场景变化检测提取策略 ✅
  - 实现固定间隔提取策略 ✅
  - 实现混合提取策略 ✅
  - _Requirements: 6.1, 6.2_

- [x] 6.2 关键帧数据模型
  - 创建 `backend/models/keyframe.py` ✅
  - 实现 `KeyFrame` 数据类 ✅
  - 实现 `KeyFrameConfig` 配置类 ✅
  - 添加数据库迁移脚本（待完成）
  - _Requirements: 6.3, 6.4_

- [x] 6.3 关键帧存储服务
  - ✅ 创建 `backend/services/keyframe_store.py`
  - ✅ 实现关键帧缩略图存储
  - ✅ 实现关键帧元数据存储
  - ✅ 支持按素材 ID 查询关键帧
  - ✅ 支持视觉嵌入存储和搜索
  - ✅ 实现提取任务管理
  - _Requirements: 6.3_

- [x] 6.4 关键帧 API
  - 创建 `backend/routers/keyframes.py` ✅
  - 实现 `POST /api/keyframes/extract` 提取端点 ✅
  - 实现 `GET /api/assets/{id}/keyframes` 查询端点 ✅
  - 实现缩略图服务端点 ✅
  - _Requirements: 10.3_

## Phase 7: CLIP 视觉嵌入实现（2天）

- [x] 7.1 CLIP 嵌入服务
  - 创建 `backend/services/clip_embedding.py` ✅
  - 支持 Ollama llava 模型 ✅
  - 支持 HuggingFace CLIP 模型 ✅
  - 实现图像嵌入接口 ✅
  - 实现文本嵌入接口（跨模态）✅
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 7.2 视觉向量存储
  - 创建 `backend/services/visual_vector_store.py` ✅
  - 实现视觉向量存储和索引 ✅
  - 实现视觉相似度搜索 ✅
  - 支持持久化存储 ✅
  - _Requirements: 7.4_

- [x] 7.3 批量视觉嵌入
  - 更新 `batch_asset_indexing_v2.py` ✅
  - 集成关键帧提取 ✅
  - 集成 CLIP 视觉嵌入 ✅
  - 生成视觉嵌入覆盖率报告 ✅
  - _Requirements: 7.3, 9.5_

## Phase 8: 多模态搜索集成（2天）

> **⚠️ 功能状态说明（2025-12-27 更新）**
> 
> 根据产品需求调整：
> - **以图搜图功能暂缓**：代码保留但 API 暂不开放
> - **视觉模型用于标签生成**：在剧本环节由 Script_Agent 调用
> - **详见**：`pervis-project-wizard` spec 的 Requirement 5.1.8 和 Phase 9 任务

- [x] 8.1 多模态搜索服务
  - 创建 `backend/services/multimodal_search.py` ✅
  - 实现 `MULTIMODAL` 搜索模式 ✅
  - 实现文本+视觉+标签融合算法 ✅
  - 支持自定义权重配置 ✅
  - _Requirements: 9.1_

- [x] 8.2 搜索结果增强
  - 实现 `MultimodalSearchResult` 数据结构 ✅
  - 返回匹配的关键帧信息 ✅
  - 返回建议的入出点时间戳 ✅
  - 支持时间轴参考信息 ✅
  - _Requirements: 8.3, 9.2_

- [x] 8.3 多模态搜索 API
  - 更新 `backend/routers/search.py` ✅
  - 实现 `POST /api/search/multimodal` 端点 ✅
  - 实现 `POST /api/search/by-image` 以图搜图端点 ✅
  - 支持关键帧结果返回 ✅
  - _Requirements: 10.4, 10.5_

- [x] 8.4 召回逻辑修复
  - 修复 `search_service.py` 缺少 `summary` 字段问题 ✅
  - 确保打标和召回的标签字段完全一致 ✅
  - 添加标签一致性验证测试
  - **修复 MemoryVideoStore 缓存加载问题** ✅ (2025-12-27)
    - 问题：后端重启后 MemoryVideoStore 数据丢失
    - 解决：添加 `segments_cache.json` 持久化存储
    - 修改 `milvus_store.py` 在初始化时自动加载缓存
    - 修改 `batch_asset_indexing_v2.py` 保存完整素材数据
  - _Requirements: 2.2_

## 依赖项

### 必需

- Ollama 本地服务（已安装）
- `nomic-embed-text` 或 `bge-m3` 嵌入模型
- PySceneDetect（关键帧提取）
- FFmpeg（帧提取和缩略图生成）

### 可选

- Milvus（大规模部署）
- `llava:7b`（CLIP 视觉嵌入，Ollama）
- `chinese-clip`（中文优化 CLIP，HuggingFace）

## 安装命令

```bash
# 安装嵌入模型（选择其一）
ollama pull nomic-embed-text
ollama pull bge-m3

# 安装视觉模型（CLIP 功能）
ollama pull llava:7b

# 安装 Python 依赖
pip install scenedetect[opencv] pillow

# 验证安装
ollama list
```

## 验收标准

| 指标 | 目标值 | 验证方法 |
|------|--------|----------|
| 一级标签覆盖率 | ≥ 95% | 统计报告 |
| 二级标签覆盖率 | ≥ 80% | 统计报告 |
| 向量覆盖率 | ≥ 90% | 统计报告 |
| 搜索 Top5 命中率 | ≥ 80% | 测试用例 |
| 搜索响应时间 | < 500ms | 性能测试 |
| 索引速度 | ≥ 10 文件/秒 | 性能测试 |
| 关键帧提取覆盖率 | ≥ 95% | 统计报告 |
| 视觉嵌入覆盖率 | ≥ 90% | 统计报告 |
| 跨模态搜索相关性 | ≥ 60% | 测试用例 |
| 图像嵌入速度 | ≥ 5 帧/秒 | 性能测试 |

## 时间估算

| 阶段 | 工时 |
|------|------|
| Phase 1: 标签层级 | 2 天 |
| Phase 2: 向量嵌入 | 2 天 |
| Phase 3: 混合搜索 | 2 天 |
| Phase 4: 批量索引 | 1 天 |
| Phase 5: 测试验证 | 1 天 |
| Phase 6: 关键帧提取 | 2 天 |
| Phase 7: CLIP 视觉嵌入 | 2 天 |
| Phase 8: 多模态搜索 | 2 天 |
| **总计** | **14 天** |

