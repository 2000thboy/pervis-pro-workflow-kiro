# Pervis PRO 前端按钮与 AI 集成状态报告

**检查日期**: 2025-12-24  
**检查范围**: 所有前端页面按钮、AI 功能调用

---

## 📊 总体状态

| 类别 | 真实 AI | Mock 数据 | 待确认 |
|------|---------|-----------|--------|
| 剧本分析 | ✅ 3 | ❌ 0 | - |
| 视频分析 | ⚠️ 1 | ❌ 1 | - |
| 语义搜索 | ✅ 2 | - | - |
| 标签生成 | ⚠️ 1 | ❌ 1 | - |
| 导出功能 | ✅ 2 | - | - |
| 反馈记录 | ❌ 0 | ❌ 1 | - |

---

## 🔍 详细分析

### 1. 首页 (LandingPage)

| 按钮/功能 | 位置 | 状态 | 说明 |
|-----------|------|------|------|
| **开始新项目** | 右侧主按钮 | ✅ 正常 | 打开 ScriptIngestion 弹窗 |
| **打开最近项目** | 左侧项目卡片 | ✅ 正常 | 从 localStorage 加载项目 |
| **删除项目** | 项目卡片悬停 | ✅ 正常 | 调用 `api.deleteProject()` |

---

### 2. 剧本导入 (ScriptIngestion)

| 按钮/功能 | 调用函数 | AI 状态 | 说明 |
|-----------|----------|---------|------|
| **填充示例 (Fill Demo)** | `api.remoteGenerateDemoScript()` | ✅ **真实 AI** | 调用后端 `/api/script/demo`，使用 LLM 生成 |
| **手动创作 (Manual)** | - | N/A | 创建空白项目，无 AI 调用 |
| **AI 智能构建 (AI Build)** | `generateStructureFromSynopsis()` | ✅ **真实 AI** | 调用后端 `/api/script/analyze` |
| **原样解析 (Parse)** | `analyzeScriptToStructure()` | ✅ **真实 AI** | 调用后端 `/api/script/analyze` |
| **智能构建 (Smart Build)** | `smartBuildScript()` | ✅ **真实 AI** | 调用后端 `/api/script/analyze` (creative mode) |

**结论**: 剧本分析功能 **全部使用真实 AI**

---

### 3. 剧本分析页 (StepAnalysis)

| 按钮/功能 | 调用函数 | AI 状态 | 说明 |
|-----------|----------|---------|------|
| **AI 重写标签** | `regenerateBeatTags()` | ⚠️ **Mock** | `apiClient.ts` 返回硬编码标签 |
| **生成人物关系图** | - | ❌ 未实现 | 按钮存在但无功能 |
| **修改目标时长** | - | N/A | 本地状态更新 |
| **下一步: 故事板** | - | N/A | 导航功能 |

**问题**: `regenerateBeatTags()` 在 `apiClient.ts` 中返回硬编码数据：
```typescript
export const regenerateBeatTags = async (_content: string): Promise<any> => {
  return {
    scene_slug: "INT. LOCATION - DAY",
    location_type: "INT",
    // ... 硬编码值
  };
};
```

---

### 4. 故事板页 (StepBeatBoard)

| 按钮/功能 | 调用函数 | AI 状态 | 说明 |
|-----------|----------|---------|------|
| **AI 搜索素材** | `searchVisualAssets()` | ✅ **真实 AI** | 调用后端 `/api/search/semantic` |
| **选择候选素材** | - | N/A | 本地状态更新 |
| **进入时间线** | - | N/A | 导航功能 |

**Inspector 组件内**:
| 按钮/功能 | 调用函数 | AI 状态 | 说明 |
|-----------|----------|---------|------|
| **搜索素材** | `searchVisualAssets()` | ✅ **真实 AI** | 调用后端语义搜索 |
| **记录反馈** | `recordAssetFeedback()` | ⚠️ **Mock** | 仅 console.log |

---

### 5. 时间线页 (StepTimeline)

| 按钮/功能 | 调用函数 | AI 状态 | 说明 |
|-----------|----------|---------|------|
| **序列设置** | - | ❌ 未实现 | 按钮存在但无功能 |
| **导出** | - | ⚠️ 待确认 | 按钮存在，需检查实现 |
| **播放/暂停** | - | N/A | 本地播放控制 |
| **缩放** | - | N/A | 本地 UI 控制 |

---

### 6. 素材库页 (StepLibrary)

| 按钮/功能 | 调用函数 | AI 状态 | 说明 |
|-----------|----------|---------|------|
| **上传素材** | `api.uploadAsset()` | ⚠️ **部分 Mock** | 上传真实，但 AI 分析是 Mock |
| **模拟局域网导入** | `loadDemoAssets()` | N/A | 加载演示数据 |
| **删除素材** | `api.deleteAsset()` | ✅ 正常 | 本地删除 |
| **搜索** | - | N/A | 本地过滤 |

**上传流程中的 AI 分析**:
- `analyzeVideoContent()` 在 `geminiService.ts` 中是 **Mock**
- `generateAssetDescription()` 在 `geminiService.ts` 中是 **Mock**

---

### 7. 侧边栏功能

| 按钮/功能 | 位置 | 状态 | 说明 |
|-----------|------|------|------|
| **AI 就绪状态** | 底部 | ✅ 正常 | 打开 AdminConsole |
| **设置** | 底部 | ✅ 正常 | 打开 SettingsModal |
| **语言切换** | 底部 | ✅ 正常 | 中/英切换 |
| **退出项目** | 底部 | ✅ 正常 | 返回首页 |

---

## ⚠️ Mock 数据问题汇总

### geminiService.ts 中的 Mock 函数

```typescript
// 1. analyzeVideoContent - MOCK
export const analyzeVideoContent = async (fileBlob: Blob, filename: string): Promise<VideoMetadata> => {
    await mockDelay(2000);
    return {
        processingStatus: 'done',
        globalTags: {
            characters: [{ label: '人物', weight: 1.0 }],  // 硬编码
            // ...
        },
        // ...
    };
};

// 2. generateAssetDescription - MOCK
export const generateAssetDescription = async (fileBlob: Blob, filename: string): Promise<string> => {
    await mockDelay(500);
    return `视频文件: ${filename}，AI分析完成。`;  // 硬编码
};

// 3. regenerateBeatTags - MOCK
export const regenerateBeatTags = async (content: string): Promise<TagSchema> => {
    await mockDelay(300);
    return {
        scene_slug: "INT. LOCATION - DAY",  // 硬编码
        // ...
    };
};

// 4. recordAssetFeedback - MOCK
export const recordAssetFeedback = async (...): Promise<void> => {
    await mockDelay(100);
    console.log(`记录反馈: ${type} for ${assetId}`);  // 仅日志
};

// 5. performAIRoughCut - MOCK
export const performAIRoughCut = async (...): Promise<{...}> => {
    await mockDelay(500);
    return {
        inPoint: 0,
        outPoint: 5,
        confidence: 0.7,
        reason: "基于内容分析的自动选择"  // 硬编码
    };
};
```

---

## ✅ 真实 AI 功能

### 后端 API 已实现

| 端点 | 功能 | 状态 |
|------|------|------|
| `POST /api/script/analyze` | 剧本分析 | ✅ 使用 LLM |
| `POST /api/script/demo` | 生成演示剧本 | ✅ 使用 LLM |
| `POST /api/search/semantic` | 语义搜索 | ✅ 使用向量搜索 |
| `POST /api/export/script` | 导出剧本 | ✅ 已实现 |
| `POST /api/export/nle` | 导出 NLE | ✅ 已实现 |

---

## 🔧 修复建议

### 优先级 P0 (必须修复)

1. **视频分析 Mock 问题**
   - 文件: `geminiService.ts` → `analyzeVideoContent()`
   - 建议: 调用后端 `/api/assets/{id}/analyze` 或使用 `apiClient.ts` 中的实现

2. **标签重生成 Mock 问题**
   - 文件: `apiClient.ts` → `regenerateBeatTags()`
   - 建议: 调用后端 `/api/script/analyze` 并提取标签

### 优先级 P1 (建议修复)

3. **反馈记录 Mock 问题**
   - 文件: `geminiService.ts` → `recordAssetFeedback()`
   - 建议: 调用后端 `/api/feedback/record`

4. **AI 粗剪 Mock 问题**
   - 文件: `geminiService.ts` → `performAIRoughCut()`
   - 建议: 实现后端 AI 粗剪逻辑

### 优先级 P2 (可选)

5. **未实现按钮**
   - "生成人物关系图" - StepAnalysis
   - "序列设置" - StepTimeline

---

## 📋 服务文件对比

| 功能 | geminiService.ts | apiClient.ts | 推荐使用 |
|------|------------------|--------------|----------|
| 剧本分析 | ✅ 真实 API | ✅ 真实 API | apiClient |
| 视频分析 | ❌ Mock | ✅ 真实 API | apiClient |
| 语义搜索 | ✅ 真实 API | ✅ 真实 API | apiClient |
| 标签重生成 | ❌ Mock | ❌ Mock | 需修复 |
| 反馈记录 | ❌ Mock | ✅ 真实 API | apiClient |
| AI 粗剪 | ❌ Mock | ⚠️ 简化逻辑 | 需修复 |

---

## 🎯 结论

**整体评估**: 前端核心功能基本正常，但存在部分 Mock 数据问题

- **正常工作**: 剧本分析、语义搜索、项目管理、导出功能
- **需要修复**: 视频 AI 分析、标签重生成、反馈记录
- **未实现**: 人物关系图、序列设置

**建议**: 统一使用 `apiClient.ts` 替代 `geminiService.ts`，后者包含较多 Mock 代码
