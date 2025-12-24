# 需求文档

## 简介

本功能旨在修复 Pervis PRO 前端中所有返回 Mock 数据的 AI 功能，将其替换为真实的 AI API 调用。系统需要支持 Gemini API 和本地 Ollama 模型两种 AI 后端。

## 术语表

- **Gemini_API**: Google 的 Gemini AI 服务，通过 API Key 访问
- **Ollama**: 本地运行的大语言模型服务，支持 Qwen 等模型
- **LLM_Provider**: 大语言模型提供者抽象层，统一管理不同 AI 后端
- **Mock_Data**: 硬编码的假数据，用于开发测试但不应在生产环境使用
- **Beat**: 剧本中的语义单元/场景片段
- **Tag**: 描述视频内容的标签（情绪、场景、动作等）
- **geminiService**: 前端服务文件，包含 AI 相关函数
- **apiClient**: 前端 API 客户端，负责与后端通信

## 需求

### 需求 1: 配置 Gemini API Key

**用户故事:** 作为开发者，我希望系统能正确配置 Gemini API Key，以便使用 Google AI 服务。

#### 验收标准

1. WHEN 系统启动时 THEN LLM_Provider SHALL 从环境变量读取 GEMINI_API_KEY
2. WHEN GEMINI_API_KEY 已配置 THEN Gemini_API SHALL 成功连接并返回真实 AI 响应
3. IF GEMINI_API_KEY 未配置且 LLM_PROVIDER 为 gemini THEN LLM_Provider SHALL 抛出明确的配置错误

### 需求 2: 修复视频内容分析 Mock 问题

**用户故事:** 作为用户，我希望上传视频后能获得真实的 AI 分析结果，而不是硬编码的假数据。

#### 验收标准

1. WHEN 用户上传视频文件 THEN geminiService SHALL 调用后端 AI 分析 API
2. WHEN 视频分析完成 THEN 系统 SHALL 返回真实的标签数据（情绪、场景、动作、摄影技法）
3. THE analyzeVideoContent 函数 SHALL 不返回任何硬编码的 Mock 数据
4. WHEN AI 分析失败 THEN 系统 SHALL 返回明确的错误信息而非 Mock 数据

### 需求 3: 修复标签重生成 Mock 问题

**用户故事:** 作为用户，我希望点击"AI 重写标签"按钮时能获得真实的 AI 生成标签。

#### 验收标准

1. WHEN 用户点击重写标签按钮 THEN apiClient SHALL 调用后端 AI 标签生成 API
2. WHEN 标签生成完成 THEN 系统 SHALL 返回基于内容分析的真实标签
3. THE regenerateBeatTags 函数 SHALL 不返回硬编码的标签值
4. WHEN 标签生成失败 THEN 系统 SHALL 显示错误提示而非返回默认标签

### 需求 4: 修复资产描述生成 Mock 问题

**用户故事:** 作为用户，我希望系统能为上传的视频生成有意义的 AI 描述。

#### 验收标准

1. WHEN 视频上传完成 THEN geminiService SHALL 调用 AI 生成描述
2. THE generateAssetDescription 函数 SHALL 返回基于视频内容的真实描述
3. THE 返回的描述 SHALL 包含视频的关键内容信息而非通用模板文字

### 需求 5: 修复反馈记录 Mock 问题

**用户故事:** 作为用户，我希望我的素材反馈能被真实记录以改进推荐质量。

#### 验收标准

1. WHEN 用户对素材进行反馈（接受/拒绝）THEN geminiService SHALL 调用后端反馈记录 API
2. THE recordAssetFeedback 函数 SHALL 将反馈数据持久化到后端
3. THE 反馈记录 SHALL 不仅仅是 console.log 输出

### 需求 6: 修复 AI 粗剪 Mock 问题

**用户故事:** 作为用户，我希望 AI 粗剪功能能调用真实 AI 分析视频内容并智能选择最佳片段。

#### 验收标准

1. WHEN 用户触发 AI 粗剪 THEN 系统 SHALL 调用后端 AI API 进行内容分析
2. THE performAIRoughCut 函数 SHALL 不返回任何硬编码的 Mock 数据
3. THE AI 粗剪 SHALL 基于剧本内容和视频标签进行语义匹配分析
4. THE 返回的入出点 SHALL 由 AI 根据内容相关性智能计算
5. THE 返回的 confidence 值 SHALL 反映 AI 分析的真实置信度
6. THE 返回的 reason 字段 SHALL 包含 AI 生成的匹配理由说明

### 需求 7: 支持本地 Ollama 模型

**用户故事:** 作为用户，我希望在没有 Gemini API 时能使用本地 Ollama 模型。

#### 验收标准

1. WHEN LLM_PROVIDER 设置为 local THEN 系统 SHALL 使用 Ollama 作为 AI 后端
2. WHEN Ollama 服务可用 THEN 所有 AI 功能 SHALL 正常工作
3. IF Ollama 服务不可用 THEN 系统 SHALL 返回明确的连接错误
4. THE Ollama 集成 SHALL 支持 Qwen 等本地模型

### 需求 8: 统一前端 AI 服务调用

**用户故事:** 作为开发者，我希望前端有统一的 AI 服务调用入口，避免 Mock 数据混乱。

#### 验收标准

1. THE 前端 SHALL 统一使用 apiClient.ts 作为 AI 服务调用入口
2. THE geminiService.ts 中的 Mock 函数 SHALL 被替换为调用 apiClient 的实现
3. WHEN 任何 AI 功能被调用 THEN 系统 SHALL 通过后端 API 获取真实结果
