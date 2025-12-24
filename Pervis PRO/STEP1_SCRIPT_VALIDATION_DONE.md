# 步骤一：剧本预校验逻辑 (Script Pre-Validation)

## ✅ 已完成 (Done)
我已修改 `backend/services/script_processor.py`，增加了核心的拦截逻辑。

### 逻辑说明 (Logic Explained)
1.  **新增 `_validate_script_structure` 函数**：
    *   它不调用 AI（速度极快）。
    *   它通过关键词 (`EXT.`, `INT.`, `内景`, `外景`, `第X场`) 识别场景。
2.  **时长估算规则 (Rule of Thumb)**：
    *   采用粗略算法：`1行 ≈ 3-4秒`。
    *   虽然不如 AI 准，但作为"拦截器"足够了。
3.  **阻断机制 (Blocking)**：
    *   如果发现任何一场戏计算出超过 **120秒**。
    *   `analyze_script` 会立即停止，返回状态 `needs_split`。
    *   返回数据包含：`{"scene_header": "第5场", "estimated_duration": 150.0, "suggestion": "建议拆分"}`。

## ⏭️ 下一步 (Next Step)
修改 `gemini_client.py`，使其支持**图片输入 (Vision)**，从而跑通"本地抽帧 -> AI 分析"的真实路径。
