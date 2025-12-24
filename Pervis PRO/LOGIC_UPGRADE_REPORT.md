# 核心逻辑升级完成报告 (Logic Upgrade Report)

按照您的指示，我已完成了后端核心逻辑的重构。这是当前系统的真实代码行为：

## 1. 剧本"阻断式"分场 (Blocking Logic)

**位置**: `backend/services/script_processor.py`
**逻辑**:
*   **Validator**: 在调用任何 AI 之前，本地函数 `_validate_script_structure` 先运行。
*   **规则**:
    *   识别 `EXT./INT./第X场`。
    *   计算字数/行数。
    *   **判定**: 如果 `estimated_duration > 120s`。
*   **动作**: 抛出 `needs_split` 状态，并且返回具体是哪一场 (`details: "第8场 宴会厅 (340s)"`)。
*   **结果**: 前端收到此状态后，**必须**弹窗要求用户手动拆分，否则流程卡住。

## 2. 真实视觉分析路径 (True Vision Path)

**位置**: `backend/services/asset_processor.py` & `visual_processor.py`
**重构后的流水线**:

1.  **Stop 1: Video Processor**
    *   验证文件，生成 `proxy.mp4` (720p)。
2.  **Stop 2: Visual Processor (New Position)**
    *   **动作**: `ffmpeg` 本地抽帧 (每 2 秒一张)。
    *   **输出**: 产生 `List[PIL.Image]` (内存中的图片对象，**不落盘**，不上传视频)。
3.  **Stop 3: Gemini Vision (New Integration)**
    *   **输入**: 只有 `List[PIL.Image]` (几张关键帧) + `Filename`。
    *   **模型**: 升级为 **`gemini-1.5-flash`** (专为多模态速度优化)。
    *   **Prompt**: "基于提供的视频关键帧图片...生成详细标签"。
    *   **输出**: 高精度的情绪、光影、运镜标签。

---

## ✅ 技术确认
1.  **API 可见性**: 代码中保留了 `print("Gemini Vision Analysis Failed: ...")`，控制台会直接打印 API 交互情况。
2.  **本地/云端分离**:
    *   ❌ 我们**没有**使用本地 LLM (本地跑不动多模态)。
    *   ✅ 我们使用 **Gemini 1.5 Flash API** (云端)。
    *   ✅ 数据隐私：只上传了 **图片切片**，几百 GB 的原片仍然锁死在您的 NAS 里。

此逻辑已固化在代码中，随时准备进行下一步：**新版启动器 (Launcher) 开发**。
