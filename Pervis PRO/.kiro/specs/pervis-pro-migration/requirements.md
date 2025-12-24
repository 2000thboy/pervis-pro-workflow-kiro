# Pervis PRO Local Development Requirements Document

## Introduction

Pervis PRO是一个专业的导演工作台系统，为导演提供从剧本分析到素材管理、从创意构思到粗剪预览的完整工作流支持。本项目将现有React前端迁移到本地后端架构，构建集成AI能力的导演创作环境。

**系统定位：**
- 导演专用的创作工作台，支持剧本分析、素材管理、创意构思、粗剪预览
- 集成视频RAG能力，提供智能素材发现和推荐
- 在导演决策阶段提供"更快、更准、更有灵感"的创作支持
- 不是精确剪辑工具，不是自动成片系统，而是导演的创意助手

**核心工作流：**
- 剧本导入 → Beat分析 → 素材搜索 → 创意构思 → 粗剪预览 → 导演决策
- 从TB级CG/电影素材库中智能推荐符合创作意图的片段
- AI理解剧本情绪和视觉需求，提供个性化的素材建议

**技术问题解决：**
- 修复前端JSON解析失败（"Failed to repair JSON string"错误）
- 消除API密钥安全风险，所有AI处理迁移到后端
- 构建稳定的视频预处理和向量搜索管道
- 保持现有UI设计完全不变

## Glossary

- **Pervis_System**: 完整的本地导演工作台应用，包含前端和后端
- **Director_Workbench**: 导演工作台，集成剧本分析、素材管理、创意构思功能
- **Script_Workbench**: 剧本工作台，负责剧本导入、分析和Beat生成  
- **Beat**: 剧本语义单元，包含情绪和视觉需求，不是精确时间轴概念
- **BeatBoard_Workbench**: 可视化Beat组织界面，用于创意构思和素材关联
- **Timeline_Workbench**: 时间线预览界面，用于粗剪效果验证
- **Asset_Library**: Local TB-scale video/image collection with preprocessing and indexing
- **Video_RAG**: 视频语义检索系统，基于情绪和氛围匹配，不追求镜头精确匹配
- **Segment**: 视频语义片段，AI自动划分的有意义时间段，用于推荐而非精确剪辑
- **Proxy_Pipeline**: FFmpeg-based video processing for smooth playback and editing
- **Backend_API**: Local FastAPI server handling all processing, storage, and AI operations
- **Multi_Module_Sync**: Real-time synchronization between workbenches and data consistency

## Requirements

### Requirement 1

**User Story:** 作为导演，我希望有一个安全的本地剧本分析系统，这样我就可以处理剧本而不暴露API密钥或遇到JSON解析失败。

#### Acceptance Criteria

1. WHEN 剧本被分析时 THEN Backend_API SHALL 使用基于环境变量的API密钥在后端处理Gemini集成
2. WHEN AI响应生成时 THEN Backend_API SHALL 返回严格验证的JSON，包含全面的错误处理
3. WHEN JSON解析失败时 THEN Backend_API SHALL 返回结构化错误，包含trace_id、raw_text和重试选项
4. WHEN Script_Workbench显示结果时 THEN 系统SHALL显示清晰的错误消息而不是静默失败
5. WHEN 节拍生成时 THEN Backend_API SHALL 创建带有适当标签和元数据的结构化节拍数据
6. WHEN 前端调用AI功能时 THEN 系统SHALL完全通过后端API，绝不在前端暴露任何API密钥

### Requirement 2

**User Story:** As a director, I want robust local video preprocessing and asset management, so that I can work efficiently with TB-scale video libraries.

#### Acceptance Criteria

1. WHEN videos are uploaded THEN the Backend_API SHALL trigger FFmpeg-based proxy generation, frame extraction at configurable intervals, and Whisper audio transcription
2. WHEN video processing occurs THEN the system SHALL use BackgroundTasks for asynchronous processing with real-time status updates
3. WHEN processing completes THEN the Asset_Library SHALL store organized files under configurable ASSET_ROOT with proper indexing
4. WHEN processing fails THEN the Backend_API SHALL provide detailed error logs and recovery options
5. WHEN large video files are handled THEN the Proxy_Pipeline SHALL generate lightweight proxies for smooth timeline playback

### Requirement 3

**User Story:** As a director, I want powerful semantic search across my video library, so that I can quickly discover relevant footage for each beat.

#### Acceptance Criteria

1. WHEN semantic searches are performed THEN the Video_RAG SHALL use vector embeddings of transcripts, frame descriptions, and metadata
2. WHEN search results are returned THEN the system SHALL provide ranked assets with confidence scores and specific time segments
3. WHEN fuzziness is adjusted THEN the Video_RAG SHALL modify similarity thresholds and result ranking
4. WHEN no matches are found THEN the system SHALL suggest alternative search terms based on available content
5. WHEN search indexing occurs THEN the Backend_API SHALL create searchable vectors from text descriptions, audio transcripts, and visual tags

### Requirement 4

**User Story:** As a director, I want seamless multi-workbench synchronization, so that changes in one interface immediately reflect across all views.

#### Acceptance Criteria

1. WHEN beats are modified in Script_Workbench THEN the BeatBoard_Workbench and Timeline_Workbench SHALL update in real-time
2. WHEN assets are assigned in BeatBoard_Workbench THEN the Timeline_Workbench SHALL reflect new media associations immediately
3. WHEN timing is adjusted in Timeline_Workbench THEN the BeatBoard_Workbench SHALL update duration displays accordingly
4. WHEN data conflicts occur THEN the Multi_Module_Sync SHALL resolve conflicts with user confirmation
5. WHEN network interruptions happen THEN the system SHALL maintain local state and sync when connectivity resumes

### Requirement 5

**User Story:** As a director, I want professional timeline editing capabilities, so that I can create precise rough cuts with frame-accurate control.

#### Acceptance Criteria

1. WHEN working in Timeline_Workbench THEN the system SHALL provide drag-and-drop beat reordering with magnetic snapping
2. WHEN trimming beat durations THEN the Timeline_Workbench SHALL offer frame-accurate in/out point adjustment
3. WHEN replacing assets THEN the system SHALL open AssetPickerModal with semantic search and fuzziness controls
4. WHEN timeline playback occurs THEN the system SHALL use proxy files for smooth real-time preview
5. WHEN exporting timelines THEN the Backend_API SHALL generate Premiere Pro compatible XML/EDL files with media references

### Requirement 6

**User Story:** 作为导演，我希望现有的UI设计完全保持不变，这样我已建立的工作流程保持一致和专业。

#### Acceptance Criteria

1. WHEN 本地系统部署时 THEN 界面SHALL保持完全相同的暗色主题、字体、卡片布局和信息密度
2. WHEN 添加新组件如AssetPickerModal时 THEN 它们SHALL遵循现有设计模式和视觉层次
3. WHEN 工作台界面增强时 THEN 它们SHALL保持当前的BeatBoard、Timeline和Inspector布局
4. WHEN 实现响应式行为时 THEN 界面SHALL在各种屏幕尺寸下保持专业外观
5. WHEN UI交互发生时 THEN 它们SHALL保持现有的动画时间、悬停状态和视觉反馈
6. WHEN 迁移到后端API时 THEN 前端界面SHALL保持完全不变，用户感受不到任何差异

### Requirement 7

**User Story:** As a developer, I want comprehensive local development setup, so that I can deploy and maintain the system effectively.

#### Acceptance Criteria

1. WHEN setting up the development environment THEN the documentation SHALL provide step-by-step installation for FFmpeg, Python, Node.js, and database dependencies
2. WHEN configuring the system THEN the setup SHALL specify GEMINI_API_KEY, ASSET_ROOT, and database connection variables
3. WHEN running smoke tests THEN the system SHALL verify video processing, AI integration, search functionality, and multi-workbench sync
4. WHEN troubleshooting occurs THEN the documentation SHALL cover common FFmpeg, database, and API integration issues
5. WHEN deploying updates THEN the system SHALL support hot-reloading for frontend and graceful backend restarts

### Requirement 8

**User Story:** As a system operator, I want robust error handling and performance monitoring, so that I can maintain system stability under heavy video processing loads.

#### Acceptance Criteria

1. WHEN video processing errors occur THEN the Backend_API SHALL log FFmpeg output, file paths, and processing parameters
2. WHEN AI API calls fail THEN the system SHALL implement exponential backoff retry with fallback error responses
3. WHEN database operations fail THEN the system SHALL provide transaction rollback and data consistency recovery
4. WHEN system resources are monitored THEN the Backend_API SHALL track video processing queue, memory usage, and disk space
5. WHEN performance degrades THEN the system SHALL provide alerts and automatic proxy quality adjustment

### Requirement 9

**User Story:** As a project planner, I want clear capacity requirements and MVP validation metrics, so that I can properly provision resources and validate system performance.

#### Acceptance Criteria

1. WHEN planning MVP validation THEN the system SHALL support processing 50-100 video assets ranging from 30 seconds to 10 minutes each
2. WHEN estimating storage requirements THEN the system SHALL account for original videos (10-50GB), proxy files (2-10GB), extracted frames (1-5GB), and database/vectors (500MB-2GB)
3. WHEN designing the tagging system THEN the Backend_API SHALL support hierarchical tags including scene_types (20-30 categories), emotions (15-20 categories), shot_types (10-15 categories), characters (project-specific), and props/objects (50-100 categories)
4. WHEN processing the MVP dataset THEN the system SHALL complete full preprocessing pipeline within 2-4 hours on standard hardware (8GB RAM, 4-core CPU)
5. WHEN validating search performance THEN the Video_RAG SHALL return relevant results within 500ms for queries against the full MVP dataset

### Requirement 10

**User Story:** 作为技术架构师，我希望有灵活的模型部署选项和清晰的成本预测，这样我可以在预算约束内选择最优的AI处理策略。

#### Acceptance Criteria

1. WHEN 配置AI处理时 THEN 系统SHALL支持云API（Gemini Pro）和本地LLM部署选项，具有运行时切换能力
2. WHEN 估算云API成本时 THEN 系统SHALL预测Gemini Pro使用量约为$50-200用于MVP验证（100个视频×每视频2-5次API调用×每次调用$0.50-2.00）
3. WHEN 部署本地LLM时 THEN 系统SHALL支持Llama 3.1 8B或Qwen 2.5 7B等模型，需要16-32GB RAM和GPU加速以获得可接受的性能
4. WHEN 处理视频内容时 THEN 系统SHALL使用可配置模型，包括Whisper（tiny/base/small）用于转录，CLIP用于视觉嵌入，以及用于特定领域标记的自定义微调模型
5. WHEN 平衡成本和性能时 THEN 系统SHALL提供混合部署选项，使用本地模型进行批量处理，云API进行复杂分析任务

### Requirement 11

**User Story:** 作为前端开发者，我希望将现有geminiService.ts完全迁移到后端API调用，这样可以解决JSON解析问题并提高系统稳定性。

#### Acceptance Criteria

1. WHEN 替换geminiService.ts时 THEN 系统SHALL创建新的apiClient.ts来处理所有后端API调用
2. WHEN ScriptIngestion组件处理剧本时 THEN 它SHALL调用POST /api/sanitize而不是直接调用Gemini API
3. WHEN 处理AI响应错误时 THEN 前端SHALL显示结构化错误信息而不是返回空的默认结构
4. WHEN 用户看到错误时 THEN 系统SHALL提供清晰的中文错误消息和重试选项
5. WHEN 迁移完成时 THEN 前端代码SHALL完全不包含任何AI API密钥或直接AI调用
6. WHEN 视频素材处理时 THEN 前端SHALL通过/api/assets/upload上传并轮询状态，而不是本地处理

### Requirement 12

**User Story:** 作为导演，我希望系统能够理解视频中的语音内容，这样我可以基于对话、旁白和音效进行精确的素材搜索。

#### Acceptance Criteria

1. WHEN 视频上传时 THEN Backend_API SHALL使用Whisper模型自动转录音频内容为文字
2. WHEN 转录完成时 THEN 系统SHALL将转录文本与视频时间轴对齐，创建带时间戳的字幕数据
3. WHEN 语义搜索时 THEN Video_RAG SHALL同时搜索视觉标签、转录文本和元数据，提供多维度匹配
4. WHEN 转录文本包含关键词时 THEN 搜索结果SHALL高亮显示匹配的语音片段和时间点
5. WHEN 音频质量较差时 THEN 系统SHALL提供转录置信度评分，并支持手动校正功能
6. WHEN 多语言内容时 THEN Whisper_Service SHALL自动检测语言并提供相应的转录结果

### Requirement 13

**User Story:** 作为导演，我希望系统能够理解视频的视觉内容，这样我可以基于画面构图、色彩、物体和场景进行智能搜索。

#### Acceptance Criteria

1. WHEN 视频处理时 THEN Backend_API SHALL使用CLIP模型提取关键帧的视觉特征向量
2. WHEN 视觉分析完成时 THEN 系统SHALL生成画面描述、物体识别、色彩分析和构图标签
3. WHEN 语义搜索时 THEN Video_RAG SHALL结合文本查询和视觉特征进行多模态匹配
4. WHEN 用户描述视觉需求时 THEN 系统SHALL理解"蓝色调"、"特写镜头"、"城市夜景"等视觉概念
5. WHEN 相似画面搜索时 THEN 系统SHALL基于视觉相似度返回构图和色调相近的片段
6. WHEN 视觉特征提取时 THEN 系统SHALL支持可配置的关键帧采样间隔和特征维度

### Requirement 14

**User Story:** 作为系统管理员，我希望系统能够高效处理大规模视频库，这样可以支持TB级素材的批量导入和实时搜索。

#### Acceptance Criteria

1. WHEN 批量上传视频时 THEN Backend_API SHALL支持并发处理多个文件，使用队列管理和负载均衡
2. WHEN 处理大文件时 THEN 系统SHALL支持断点续传、分块上传和进度恢复功能
3. WHEN 系统负载较高时 THEN Processing_Queue SHALL自动调整处理优先级和资源分配
4. WHEN 存储空间不足时 THEN 系统SHALL提供智能清理策略和存储优化建议
5. WHEN 搜索大规模数据时 THEN Vector_Database SHALL使用索引优化确保毫秒级响应时间
6. WHEN 系统扩展时 THEN 架构SHALL支持水平扩展和分布式处理能力