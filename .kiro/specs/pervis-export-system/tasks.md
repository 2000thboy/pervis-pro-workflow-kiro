# Implementation Plan: Pervis PRO 导出系统

## Overview

本实现计划将导出系统分为以下几个阶段：
1. 存储基础设施（缓存管理、路径配置）
2. 后端导出服务增强
3. 前端导出 UI 组件
4. API 集成与测试

使用 Python 进行后端开发，TypeScript/React 进行前端开发。

## Tasks

- [ ] 1. 存储基础设施
  - [ ] 1.1 实现 StorageConfig 存储路径配置类
    - 创建 `backend/services/storage_config.py`
    - 实现 `get_app_data_dir()`、`get_cache_dir()`、`get_temp_dir()` 等方法
    - 支持 Windows/macOS/Linux 跨平台路径
    - _Requirements: 5.4, 6.5_

  - [ ] 1.2 实现 CacheManager 缓存管理器
    - 创建 `backend/services/cache_manager.py`
    - 实现 `ensure_thumbnail()`、`ensure_proxy()` 方法
    - 实现 LRU 缓存清理策略
    - 实现 `verify_asset_availability()` 素材可用性检查
    - _Requirements: 2.3, 3.8, 5.4_

  - [ ] 1.3 创建 AssetMetadata 数据库模型
    - 在 `backend/models/` 添加 `asset_metadata.py`
    - 包含 `original_path`、`thumbnail_path`、`proxy_path`、`cache_version` 等字段
    - 创建数据库迁移脚本
    - _Requirements: 5.1_

  - [ ] 1.4 创建 ExportHistory 数据库模型
    - 在 `backend/models/` 添加 `export_history.py`
    - 包含 `export_type`、`file_format`、`file_path`、`status` 等字段
    - 创建数据库迁移脚本
    - _Requirements: 5.1, 5.2_

- [ ] 2. 项目文档导出服务 (Analysis 阶段)
  - [ ] 2.1 增强 DocumentExporter 服务
    - 修改 `backend/services/document_exporter.py`
    - 实现 `export_project_document()` 方法
    - 支持导出项目信息、剧本、角色、场次、镜头、AI 分析
    - _Requirements: 1.2, 1.5_

  - [ ] 2.2 实现 PDF 导出功能
    - 使用 reportlab 或 weasyprint 生成 PDF
    - 实现专业排版模板
    - _Requirements: 1.3_

  - [ ] 2.3 实现 DOCX 导出功能
    - 使用 python-docx 生成 Word 文档
    - 实现可编辑文档模板
    - _Requirements: 1.4_

  - [ ]* 2.4 编写项目文档导出属性测试
    - **Property 1: 项目文档导出完整性**
    - **Property 2: 文档格式有效性**
    - **Validates: Requirements 1.2, 1.3, 1.4**

- [ ] 3. 故事板序列导出服务 (Board 阶段)
  - [ ] 3.1 增强 ImageExporter 服务
    - 修改 `backend/services/image_exporter.py`
    - 实现 `export_beatboard_sequence()` 方法
    - 支持按场次分组导出
    - _Requirements: 2.2, 2.3_

  - [ ] 3.2 实现图片分辨率处理
    - 支持 1080p、4K、自定义分辨率
    - 实现图片缩放和格式转换
    - _Requirements: 2.5_

  - [ ] 3.3 实现镜头信息叠加
    - 在图片上绘制场次号、镜头号、时长、描述
    - 使用 Pillow 进行图片处理
    - _Requirements: 2.7_

  - [ ] 3.4 实现联系表导出
    - 生成包含所有镜头缩略图的单页概览图
    - 支持自定义布局（每行镜头数）
    - _Requirements: 2.8_

  - [ ] 3.5 实现文件夹结构和 ZIP 打包
    - 按场次创建文件夹结构
    - 使用 zipfile 打包输出
    - _Requirements: 2.6_

  - [ ]* 3.6 编写故事板导出属性测试
    - **Property 3: 故事板序列数量一致性**
    - **Property 4: 图片分辨率一致性**
    - **Property 5: 文件夹结构正确性**
    - **Validates: Requirements 2.3, 2.5, 2.6**

- [ ] 4. 时间线视频导出服务 (Timeline 阶段)
  - [ ] 4.1 增强 RenderService 视频导出
    - 修改 `backend/services/render_service.py`
    - 支持 MP4、MOV、WebM 格式
    - 支持 720p、1080p、2K、4K 分辨率
    - _Requirements: 3.3, 3.4_

  - [ ] 4.2 实现帧率和质量控制
    - 支持 23.976、24、25、29.97、30、50、60 帧率
    - 实现质量预设（low、medium、high、ultra）
    - _Requirements: 3.5_

  - [ ] 4.3 实现音频导出功能
    - 添加 `export_audio()` 方法
    - 支持 WAV、MP3 格式
    - 支持采样率和比特率配置
    - _Requirements: 3.6_

  - [ ] 4.4 实现渲染进度追踪
    - 解析 FFmpeg 输出获取进度
    - 通过 WebSocket 或轮询推送进度
    - _Requirements: 3.7_

  - [ ]* 4.5 编写视频导出属性测试
    - **Property 6: 视频格式有效性**
    - **Property 7: 视频参数一致性**
    - **Property 8: 音频导出有效性**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6**

- [ ] 5. NLE 工程导出服务
  - [ ] 5.1 增强 NLEExporter 服务
    - 修改 `backend/services/nle_exporter.py`
    - 实现 FCPXML 格式导出
    - 实现 EDL (CMX3600) 格式导出
    - _Requirements: 4.1, 4.2_

  - [ ] 5.2 实现片段信息完整导出
    - 包含入出点、时长、轨道信息
    - 保留素材文件相对路径引用
    - _Requirements: 4.3, 4.4_

  - [ ]* 5.3 编写 NLE 导出属性测试
    - **Property 9: NLE 工程文件有效性**
    - **Property 10: NLE 片段信息完整性**
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ] 6. 后端 API 端点
  - [ ] 6.1 创建导出 API 路由
    - 创建 `backend/routers/export.py`（如不存在则新建）
    - 实现 `POST /api/export/project` - 项目文档导出
    - 实现 `POST /api/export/beatboard/sequence` - 故事板序列导出
    - _Requirements: 1.1, 2.1_

  - [ ] 6.2 实现时间线导出 API
    - 实现 `POST /api/export/timeline/video` - 视频导出
    - 实现 `POST /api/export/timeline/audio` - 音频导出
    - 实现 `POST /api/export/nle` - NLE 工程导出
    - _Requirements: 3.1, 3.6, 4.1_

  - [ ] 6.3 实现导出历史和下载 API
    - 实现 `GET /api/export/history` - 获取导出历史
    - 实现 `GET /api/export/download/{export_id}` - 下载导出文件
    - 实现 `GET /api/export/status/{task_id}` - 获取导出状态
    - _Requirements: 5.2, 5.3_

- [ ] 7. Checkpoint - 后端功能验证
  - 确保所有后端 API 可正常调用
  - 确保所有测试通过
  - 如有问题请询问用户

- [ ] 8. 前端导出 UI 组件
  - [ ] 8.1 创建 ExportDialog 基础组件
    - 创建 `frontend/components/ExportDialog.tsx`
    - 实现统一的对话框样式
    - 支持 analysis、board、timeline 三种模式
    - _Requirements: 6.4_

  - [ ] 8.2 实现项目文档导出选项 UI
    - 格式选择（PDF/DOCX）
    - 内容选择（剧本、角色、场次、镜头、AI 分析）
    - _Requirements: 1.1, 1.2_

  - [ ] 8.3 实现故事板导出选项 UI
    - 导出模式选择（全部/场次/镜头）
    - 格式和分辨率选择
    - 联系表选项
    - _Requirements: 2.1, 2.2_

  - [ ] 8.4 实现时间线导出选项 UI
    - 视频/音频/NLE 选项卡
    - 格式、分辨率、帧率、质量选择
    - _Requirements: 3.1, 4.1_

  - [ ] 8.5 创建 ExportProgress 进度组件
    - 创建 `frontend/components/ExportProgress.tsx`
    - 显示进度条、百分比、预计剩余时间
    - 支持取消和重试
    - _Requirements: 3.7, 6.5_

- [ ] 9. 前端页面集成
  - [ ] 9.1 集成 StepAnalysis 导出按钮
    - 修改 `frontend/StepAnalysis.tsx`
    - 添加"导出项目文档"按钮
    - 连接 ExportDialog 组件
    - _Requirements: 6.1_

  - [ ] 9.2 集成 StepBeatBoard 导出按钮
    - 修改 `frontend/StepBeatBoard.tsx`
    - 添加"导出故事板"按钮
    - 连接 ExportDialog 组件
    - _Requirements: 6.2_

  - [ ] 9.3 集成 StepTimeline 导出按钮
    - 修改 `frontend/StepTimeline.tsx`
    - 添加"导出视频"和"导出工程"按钮
    - 连接 ExportDialog 组件
    - _Requirements: 6.3_

  - [ ] 9.4 实现前端 API 调用
    - 在 `frontend/services/apiClient.ts` 添加导出相关 API
    - 实现 `exportProjectDocument()`、`exportBeatboardSequence()`
    - 实现 `exportTimelineVideo()`、`exportTimelineAudio()`、`exportNLE()`
    - 实现 `getExportStatus()`、`getExportHistory()`、`downloadExport()`
    - _Requirements: 6.4, 6.5, 6.6_

- [ ] 10. 导出历史管理
  - [ ] 10.1 实现导出历史清理任务
    - 创建定时任务清理超过 7 天的导出文件
    - 更新历史记录状态
    - _Requirements: 5.4_

  - [ ]* 10.2 编写导出历史属性测试
    - **Property 11: 导出历史记录完整性**
    - **Property 12: 导出文件清理正确性**
    - **Validates: Requirements 5.1, 5.4**

- [ ] 11. Final Checkpoint - 完整功能验证
  - 确保所有导出功能正常工作
  - 确保前后端集成正常
  - 确保所有测试通过
  - 如有问题请询问用户

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- **系统 Agent 功能将作为单独的 spec 开发**，不在本导出系统 spec 中实现
  - 确保所有导出功能正常工作
  - 确保前后端集成正常
  - 确保所有测试通过
  - 如有问题请询问用户

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
