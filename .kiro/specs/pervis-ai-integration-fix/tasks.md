# 实现计划: Pervis PRO AI 集成修复

## 概述

本计划将修复 Pervis PRO 前端中所有返回 Mock 数据的 AI 功能，替换为真实的后端 AI API 调用。

## 任务

- [x] 1. 配置 Gemini API Key 和环境变量
  - [x] 1.1 更新 .env 文件添加 GEMINI_API_KEY
    - 添加 `GEMINI_API_KEY=AIzaSyD1wZksttq-FEA24vKFC5p-rjnzsPIttfc`
    - 确保 `LLM_PROVIDER=gemini` 配置正确
    - _Requirements: 1.1, 1.2_
  - [x] 1.2 编写属性测试验证 API Key 配置
    - **Property 2: API Key 配置验证**
    - **Validates: Requirements 1.3**

- [x] 2. 实现后端 AI 标签生成 API
  - [x] 2.1 在 LLMProvider 中添加 generate_beat_tags 方法
    - GeminiProvider 实现
    - OllamaProvider 实现
    - _Requirements: 3.1, 3.2_
  - [x] 2.2 创建 /api/ai/generate-tags 路由
    - 接收 content 参数
    - 返回 TagSchema 格式数据
    - _Requirements: 3.1_
  - [x] 2.3 编写属性测试验证标签生成
    - **Property 4: 标签生成内容相关性**
    - **Validates: Requirements 3.2, 3.3**

- [x] 3. 实现后端 AI 资产描述生成 API
  - [x] 3.1 在 LLMProvider 中添加 generate_asset_description 方法
    - 基于文件名和元数据生成描述
    - _Requirements: 4.1, 4.2_
  - [x] 3.2 创建 /api/ai/generate-description 路由
    - 接收 asset_id 和 filename 参数
    - 返回 AI 生成的描述文本
    - _Requirements: 4.1_

- [x] 4. 实现后端 AI 粗剪分析 API
  - [x] 4.1 在 LLMProvider 中添加 analyze_rough_cut 方法
    - 分析剧本内容和视频标签
    - 返回入出点、置信度和理由
    - _Requirements: 6.1, 6.3_
  - [x] 4.2 创建 /api/ai/rough-cut 路由
    - 接收 script_content 和 video_tags 参数
    - 返回 RoughCutResult 格式数据
    - _Requirements: 6.1_
  - [x] 4.3 编写属性测试验证粗剪输出
    - **Property 3: AI 粗剪输出完整性**
    - **Validates: Requirements 6.4, 6.5, 6.6**

- [x] 5. 检查点 - 确保后端 API 测试通过
  - 所有后端测试通过 ✓

- [x] 6. 修复前端 apiClient.ts 中的 Mock 函数
  - [x] 6.1 修改 regenerateBeatTags 函数
    - 替换硬编码返回为调用 /api/ai/generate-tags
    - _Requirements: 3.1, 3.3_
  - [x] 6.2 修改 generateAssetDescription 函数
    - 替换硬编码返回为调用 /api/ai/generate-description
    - _Requirements: 4.1, 4.3_
  - [x] 6.3 修改 performAIRoughCut 函数
    - 替换简化逻辑为调用 /api/ai/rough-cut
    - _Requirements: 6.1, 6.2_

- [x] 7. 修复前端 geminiService.ts 中的 Mock 函数
  - [x] 7.1 修改 analyzeVideoContent 函数
    - 移除 mockDelay 和硬编码数据
    - 调用 apiClient 中的实现
    - _Requirements: 2.1, 2.3_
  - [x] 7.2 修改 generateAssetDescription 函数
    - 移除 mockDelay 和硬编码字符串
    - 调用 apiClient 中的实现
    - _Requirements: 4.1, 4.3_
  - [x] 7.3 修改 regenerateBeatTags 函数
    - 移除 mockDelay 和硬编码标签
    - 调用 apiClient 中的实现
    - _Requirements: 3.1, 3.3_
  - [x] 7.4 修改 recordAssetFeedback 函数
    - 移除 console.log
    - 调用 apiClient 中的 recordAssetFeedback
    - _Requirements: 5.1, 5.3_
  - [x] 7.5 修改 performAIRoughCut 函数
    - 移除 mockDelay 和硬编码返回值
    - 调用 apiClient 中的实现
    - _Requirements: 6.1, 6.2_

- [x] 8. 检查点 - 确保前端编译通过
  - TypeScript 编译无错误 ✓

- [x] 9. 编写集成属性测试
  - [x] 9.1 编写无 Mock 数据返回属性测试
    - **Property 1: 无 Mock 数据返回**
    - **Validates: Requirements 2.3, 3.3, 6.2**
  - [x] 9.2 编写反馈记录持久化属性测试
    - **Property 5: 反馈记录持久化**
    - **Validates: Requirements 5.2**
  - [x] 9.3 编写 LLM Provider 切换属性测试
    - **Property 6: LLM Provider 切换**
    - **Validates: Requirements 7.1**

- [x] 10. 最终检查点 - 确保所有测试通过
  - 所有 14 个属性测试通过 ✓

## 备注

- 所有任务都是必须执行的
- 每个任务都引用了具体的需求以确保可追溯性
- 检查点用于确保增量验证
- 属性测试验证通用正确性属性
