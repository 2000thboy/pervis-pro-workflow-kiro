# 技术架构与NAS集成路径说明

## 1. 核心逻辑澄清：启动器 vs 浏览器 (Launcher vs Web)

您提到"素材管理在哪里调整"的疑问非常关键。为了保持专业系统的清晰度，我们将功能严格分层：

### 🛠️ 启动器 (Control Center) = **"基础设施配置"**
**定位**：负责"连接"和"设置"，不负责"创作"。
**NAS 逻辑**：
- 在这里告诉系统："我的 NAS 挂载在 `Z:\PreVis_Assets`"。
- 在这里点击："**扫描入库**"。
- 类似于 Adobe Premiere 的 "Media Cache" 设置或 DaVinci Resolve 的 "Media Storage" 设置。
- **原因**：这是系统级的路径配置，一次配置，永久有效。

### 🌐 浏览器 (Web Workbench) = **"创意资产管理"**
**定位**：负责"筛选"、"打标"和"使用"。
**素材逻辑**：
- 在这里**看**到所有已扫描的素材。
- 进行 AI 搜索、打标签、拖拽到时间轴。
- **注意**：网页端**不进行**底层的磁盘路径挂载操作，只操作"已入库"的数据引用。

---

## 2. NAS 挂载现状诊断 (Current Status)

### 现状
- **后端 (`main.py`)**：目前只硬编码挂载了 `./assets` 目录作为静态资源服务 (`/assets`)。
- **局限性**：
    1.  系统**无法**直接访问 NAS 上的文件（除非手动拷贝到 `./assets`）。
    2.  浏览器安全限制 (Security Sandbox) 禁止网页直接读取本地/局域网路径（如 `file:///Z:/video.mp4`）。

### 风险点
- 直接在浏览器引用 `Z:\...` 路径**百分之百会失败**（Chrome 安全拦截）。
- **必须**通过后端作为一个 "流媒体代理 (Streaming Proxy)" 来转发视频流。

---

## 3. 完整技术实施路径 (Technical Path)

为了实现"原地引用 NAS 素材"，我们需要打通以下技术链路：

### 第一步：物理挂载 (OS Level)
- **状态**：用户需在 Windows 中将 NAS 映射为盘符（如 `Z:`）或确保 UNC 路径 (`\\nas\share`) 可访问。
- **无需代码**：这是操作系统层面的预备。

### 第二步：配置与索引 (Launcher & Backend)
- **操作**：在启动器输入路径 `Z:\Projects\Movie1`。
- **后端动作**：
    - 调用 `POST /api/storage/scan`。
    - 遍历目录，**仅读取元数据** (文件名、大小、时长)，写入 SQLite 数据库。
    - **关键**：记录 `file_path = "Z:\Projects\Movie1\shot_01.mp4"`。

### 第三步：流媒体代理 (The Missing Link)
- **问题**：前端 `<video src="Z:\...">` 无法播放。
- **解决方案**：新增后端接口 `GET /api/stream?path=...`。
    - 前端请求：`http://localhost:8000/api/stream?id=asset_123`
    - 后端逻辑：找到 `asset_123` 对应的 `Z:\...` 路径，使用 `FileResponse` 或 `StreamingResponse` 将文件流式传输给前端。
- **必要性**：这是支持 NAS 的唯一可行技术方案。

### 第四步：前端展示
- **Web 端**：查询 API 获取素材列表。
- **播放器**：视频 `src` 指向后端的代理接口，而不是本地路径。

## 4. 总结与计划

目前后端**缺** "流媒体代理" 接口，且静态文件服务配置过死。

**下一步计划 (Next Steps)**:
1.  [Backend] 实现 `/api/assets/stream/{asset_id}` 接口 (解决浏览器读取 NAS 文件的问题)。
2.  [Launcher] 完成路径添加界面 (触发扫描)。
3.  [Verification] 挂载一个非项目目录，验证能否播放。
