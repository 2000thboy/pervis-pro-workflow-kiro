# Requirements Document

## Introduction

Pervis PRO 导出系统需求文档。本系统为影视预可视化工作流提供完整的导出功能，覆盖从立项到最终输出的各个环节。每个工作流阶段都应有对应的导出能力，支持行业标准格式。

## Glossary

- **Project_Exporter**: 项目导出器，负责导出完整项目文档包
- **BeatBoard_Exporter**: 故事板导出器，按场次导出序列图片
- **Timeline_Exporter**: 时间线导出器，使用 FFmpeg 导出视频/音频
- **Scene**: 场次，剧本中的场景单位
- **Beat**: 镜头，场次中的最小叙事单位
- **FFmpeg**: 开源多媒体处理工具

## Requirements

### Requirement 1: 项目文档导出 (Analysis 阶段)

**User Story:** As a 导演/制片人, I want to 导出完整的项目立项文档, so that 我可以用于项目汇报、融资或团队沟通。

#### Acceptance Criteria

1. WHEN 用户在 Analysis 阶段点击导出按钮 THEN THE Project_Exporter SHALL 显示导出选项对话框
2. THE Project_Exporter SHALL 支持导出以下内容：
   - 项目基本信息（标题、Logline、Synopsis）
   - 完整剧本文本
   - 角色列表及描述
   - 场次大纲
   - 镜头分解表（Beat 列表）
   - AI 分析评估报告
3. WHEN 用户选择 PDF 格式 THEN THE Project_Exporter SHALL 生成专业排版的 PDF 文档
4. WHEN 用户选择 DOCX 格式 THEN THE Project_Exporter SHALL 生成可编辑的 Word 文档
5. THE Project_Exporter SHALL 在导出文档中包含项目元数据（创建时间、版本号、画幅比例、帧率）

### Requirement 2: 故事板序列导出 (Board 阶段)

**User Story:** As a 分镜师/导演, I want to 按场次导出故事板序列图片, so that 我可以用于现场拍摄参考或团队审阅。

#### Acceptance Criteria

1. WHEN 用户在 Board 阶段点击导出按钮 THEN THE BeatBoard_Exporter SHALL 显示导出选项对话框
2. THE BeatBoard_Exporter SHALL 支持以下导出模式：
   - 全部场次导出
   - 选择特定场次导出
   - 选择特定镜头导出
3. WHEN 导出单个场次 THEN THE BeatBoard_Exporter SHALL 生成该场次所有镜头的序列图片
4. THE BeatBoard_Exporter SHALL 支持以下图片格式：PNG、JPG
5. THE BeatBoard_Exporter SHALL 支持以下分辨率选项：1920x1080、3840x2160、自定义
6. WHEN 导出完成 THEN THE BeatBoard_Exporter SHALL 按场次创建文件夹结构组织图片
7. THE BeatBoard_Exporter SHALL 在每张图片上叠加镜头信息（场次号、镜头号、时长、描述）
8. WHEN 用户选择"导出联系表" THEN THE BeatBoard_Exporter SHALL 生成包含所有镜头缩略图的单页概览图

### Requirement 3: 时间线视频导出 (Timeline 阶段)

**User Story:** As a 剪辑师/导演, I want to 使用 FFmpeg 导出时间线视频和音频, so that 我可以获得可播放的预览片或用于后续制作。

#### Acceptance Criteria

1. WHEN 用户在 Timeline 阶段点击导出按钮 THEN THE Timeline_Exporter SHALL 显示导出选项对话框
2. THE Timeline_Exporter SHALL 使用 FFmpeg 进行视频渲染
3. THE Timeline_Exporter SHALL 支持以下视频格式：MP4 (H.264)、MOV (ProRes)、WebM
4. THE Timeline_Exporter SHALL 支持以下分辨率：720p、1080p、2K、4K
5. THE Timeline_Exporter SHALL 支持以下帧率：23.976、24、25、29.97、30、50、60
6. WHEN 用户选择"仅导出音频" THEN THE Timeline_Exporter SHALL 导出 WAV 或 MP3 格式音频
7. THE Timeline_Exporter SHALL 显示实时渲染进度（百分比、预计剩余时间）
8. IF 渲染过程中发生错误 THEN THE Timeline_Exporter SHALL 显示详细错误信息并提供重试选项
9. WHEN 渲染完成 THEN THE Timeline_Exporter SHALL 提供下载链接和本地保存选项

### Requirement 4: NLE 工程导出 (Timeline 阶段)

**User Story:** As a 剪辑师, I want to 导出 NLE 工程文件, so that 我可以在专业剪辑软件中继续编辑。

#### Acceptance Criteria

1. THE Timeline_Exporter SHALL 支持导出 XML 格式（兼容 Premiere Pro、Final Cut Pro）
2. THE Timeline_Exporter SHALL 支持导出 EDL 格式（通用剪辑交换格式）
3. WHEN 导出 XML/EDL THEN THE Timeline_Exporter SHALL 包含所有片段的入出点、时长、轨道信息
4. THE Timeline_Exporter SHALL 在导出时保留素材文件的相对路径引用

### Requirement 5: 导出历史与管理

**User Story:** As a 用户, I want to 查看和管理导出历史, so that 我可以重新下载之前的导出文件。

#### Acceptance Criteria

1. THE System SHALL 记录每次导出的历史记录（时间、类型、格式、文件大小、状态）
2. WHEN 用户查看导出历史 THEN THE System SHALL 显示最近的导出记录列表
3. THE System SHALL 提供重新下载已完成导出文件的功能
4. THE System SHALL 自动清理超过 7 天的导出文件以节省存储空间

### Requirement 6: 前端导出 UI 集成

**User Story:** As a 用户, I want to 在每个工作流阶段都能方便地找到导出功能, so that 我可以随时导出当前阶段的成果。

#### Acceptance Criteria

1. THE System SHALL 在 Analysis 阶段的工具栏添加"导出项目文档"按钮
2. THE System SHALL 在 Board 阶段的工具栏添加"导出故事板"按钮
3. THE System SHALL 在 Timeline 阶段的工具栏添加"导出视频"和"导出工程"按钮
4. WHEN 用户点击导出按钮 THEN THE System SHALL 显示统一风格的导出对话框
5. THE System SHALL 在导出过程中显示进度指示器
6. WHEN 导出完成 THEN THE System SHALL 显示成功通知并提供下载/打开选项
