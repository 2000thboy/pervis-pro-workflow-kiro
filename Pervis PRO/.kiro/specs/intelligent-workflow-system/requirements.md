# 智能工作流系统需求文档

## 简介

智能工作流系统旨在解决当前PreVis Pro中素材库、时间轴和导出功能缺乏智能识别和自动填充的问题。系统将实现从剧本输入到最终成片导出的完整智能化工作流。

## 术语表

- **智能工作流系统 (Intelligent_Workflow_System)**: 集成剧本分析、素材匹配、时间轴生成和导出功能的核心系统
- **RAG素材引擎 (RAG_Asset_Engine)**: 基于检索增强生成技术的素材智能匹配引擎
- **剧本分析器 (Script_Analyzer)**: 分析剧本内容并提取场景、情感、动作等关键信息的组件
- **素材库管理器 (Asset_Library_Manager)**: 管理和索引所有视频、音频、图片素材的系统
- **时间轴生成器 (Timeline_Generator)**: 根据剧本分析结果自动生成时间轴的组件
- **BeatBoard智能填充器 (BeatBoard_Smart_Filler)**: 为故事板自动匹配和填充相关素材的组件
- **导出渲染器 (Export_Renderer)**: 将时间轴内容渲染为最终视频文件的组件

## 需求

### 需求 1

**用户故事:** 作为内容创作者，我希望上传剧本后系统能智能分析并逐步处理，以便我能看到明确的处理进度和结果。

#### 验收标准

1. WHEN 用户上传剧本文件 THEN 剧本分析器 SHALL 显示分析进度并提取场景、角色、情感和动作信息
2. WHEN 剧本分析完成 THEN 智能工作流系统 SHALL 显示分析结果摘要包括场景数量、关键词和建议素材类型
3. WHEN 分析过程中出现错误 THEN 智能工作流系统 SHALL 显示具体错误信息并提供重试选项
4. WHEN 分析完成 THEN 智能工作流系统 SHALL 自动触发素材匹配流程
5. WHEN 用户查看分析结果 THEN 剧本分析器 SHALL 提供每个场景的详细标签和元数据

### 需求 2

**用户故事:** 作为内容创作者，我希望素材库能智能识别和分类我的素材，以便系统能自动为剧本匹配合适的内容。

#### 验收标准

1. WHEN 用户上传视频素材 THEN 素材库管理器 SHALL 自动提取视觉特征、音频特征和元数据信息
2. WHEN 素材分析完成 THEN RAG素材引擎 SHALL 为每个素材生成语义向量并建立索引
3. WHEN 系统接收剧本场景描述 THEN RAG素材引擎 SHALL 返回相关度排序的匹配素材列表
4. WHEN 素材匹配过程执行 THEN 素材库管理器 SHALL 显示匹配进度和找到的素材数量
5. WHEN 没有找到匹配素材 THEN RAG素材引擎 SHALL 提供相似素材建议和缺失素材类型提示

### 需求 3

**用户故事:** 作为内容创作者，我希望BeatBoard能自动填充匹配的素材，以便我能快速预览和调整故事板内容。

#### 验收标准

1. WHEN 剧本分析完成 THEN BeatBoard智能填充器 SHALL 为每个场景自动匹配并显示最佳素材
2. WHEN BeatBoard显示素材 THEN BeatBoard智能填充器 SHALL 提供素材相关度评分和替换选项
3. WHEN 用户点击素材 THEN BeatBoard智能填充器 SHALL 显示素材详细信息和其他候选素材
4. WHEN 用户替换素材 THEN BeatBoard智能填充器 SHALL 更新场景内容并重新计算时间轴
5. WHEN 所有场景填充完成 THEN BeatBoard智能填充器 SHALL 提供整体预览和编辑建议

### 需求 4

**用户故事:** 作为内容创作者，我希望时间轴能根据剧本和选定素材自动生成，以便我能获得可编辑的视频序列。

#### 验收标准

1. WHEN BeatBoard内容确认 THEN 时间轴生成器 SHALL 根据场景顺序和素材时长自动创建时间轴
2. WHEN 时间轴生成过程中 THEN 时间轴生成器 SHALL 显示生成进度和当前处理的场景
3. WHEN 素材时长不匹配场景需求 THEN 时间轴生成器 SHALL 自动调整素材播放速度或截取合适片段
4. WHEN 时间轴生成完成 THEN 时间轴生成器 SHALL 提供可视化时间轴编辑器供用户调整
5. WHEN 用户修改时间轴 THEN 时间轴生成器 SHALL 实时更新总时长和场景衔接效果

### 需求 5

**用户故事:** 作为内容创作者，我希望能将完成的时间轴导出为视频文件，以便我能获得最终的成片作品。

#### 验收标准

1. WHEN 用户点击导出按钮 THEN 导出渲染器 SHALL 验证时间轴完整性并显示导出选项
2. WHEN 导出过程开始 THEN 导出渲染器 SHALL 显示渲染进度包括当前帧数和预计完成时间
3. WHEN 渲染过程中出现错误 THEN 导出渲染器 SHALL 暂停渲染并显示详细错误信息和解决建议
4. WHEN 渲染完成 THEN 导出渲染器 SHALL 生成最终视频文件并提供预览和下载选项
5. WHEN 用户选择不同导出格式 THEN 导出渲染器 SHALL 支持多种分辨率和编码格式的导出选项

### 需求 6

**用户故事:** 作为内容创作者，我希望整个工作流程能提供实时反馈和错误处理，以便我能及时了解系统状态并解决问题。

#### 验收标准

1. WHEN 任何处理步骤执行 THEN 智能工作流系统 SHALL 显示当前步骤状态和整体进度
2. WHEN 系统检测到资源不足 THEN 智能工作流系统 SHALL 暂停处理并提示用户释放资源或调整设置
3. WHEN 处理步骤失败 THEN 智能工作流系统 SHALL 记录错误日志并提供重试或跳过选项
4. WHEN 用户取消操作 THEN 智能工作流系统 SHALL 安全停止当前处理并清理临时文件
5. WHEN 系统空闲时 THEN 智能工作流系统 SHALL 显示就绪状态和下一步操作建议

## 部署（Deployment）

### MCP（Model Context Protocol）

#### 安装与运行方式

- MCP 以开发/运维工具链形式接入项目，通过项目根目录的 `.mcp.json` 声明 MCP Server 列表与启动参数。
- MCP Server 采用 `npx` 拉起，不需要将 MCP 依赖写入项目运行时依赖。

#### 安装目录结构（规范）

```
Pervis PRO/
├── .mcp.json
├── backend/
├── frontend/
└── logs/
    └── mcp/
```

#### 关键配置摘要

- MCP 配置文件：`.mcp.json`
- MCP Server 启动器：`npx`
- 需要提供的密钥类环境变量（按启用的 Server 配置）：`NEON_API_KEY`、`SUPABASE_ACCESS_TOKEN`、`SUPABASE_PROJECT_REF`、`FIGMA_ACCESS_TOKEN`、`CONTEXT7_API_KEY`、`REF_API_KEY`、`API_KEY`、`EDGEONE_PAGES_API_TOKEN`、`EDGEONE_PAGES_PROJECT_NAME`、`SEMGREP_APP_TOKEN`

#### 监控与告警（最小要求）

- 必须监控 MCP Server 进程存活（退出即告警）
- 必须收集标准输出/错误输出到 `logs/mcp/`
- 必须对连续启动失败（例如 3 次/5 分钟）触发告警
