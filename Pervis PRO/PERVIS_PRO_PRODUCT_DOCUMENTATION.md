# Pervis PRO - 产品需求与技术实施文档 (Product & Technical Documentation)

**文档版本**: v1.0
**生成日期**: 2025-12-19
**状态**: 正式发布 (Ready for Development/Audit)

---

## 1. 产品需求文档 (PRD)

### 1.1 产品概述
*   **产品名称**: Pervis PRO (Previsualization Professional)
*   **产品定位**: 专为影视前期制作（Previs）打造的本地化 AI 辅助工具，通过 AI 语义分析与视觉识别，实现剧本到分镜资源的自动化匹配。
*   **核心目标**: 解决传统 Previs 流程中“找素材难、剧本拆解繁琐、多系统割裂”的痛点，提供“一键启动、全流程序贯通”的智能化体验。
*   **用户画像**:
    *   **导演/分镜师**: 需要快速验证剧本画面感。
    *   **剪辑师**: 需要根据脚本快速查找对应的素材片段。
    *   **独立创作者**: 依赖本地素材库进行高效创作。

### 1.2 功能需求 (Functional Requirements)

#### 1.2.1 核心功能 (P0 - MVP)
1.  **一键启动 (Unified Launcher)**
    *   提供单一入口 (`启动_Pervis_PRO.py`)，自动编排启动 Backend (API) 和 Frontend (Web)。
    *   **Akiba 风格控制台**: 包含侧边导航、实时日志流、服务健康状态监控 (API/Web 端口检测)。
    *   **环境自检**: 自动识别 Python 环境、依赖库、NAS 盘符挂载状态 (`L:` 盘)。
2.  **剧本智能拆解 (Script Analysis)**
    *   支持 PDF/TXT 剧本上传。
    *   AI 自动进行场次拆分，提取【场景】、【时间】、【人物】、【动作】关键信息。
3.  **本地/NAS 素材索引 (Asset Indexing)**
    *   支持对指定目录（如 `Z:\Movies`）进行递归扫描。
    *   生成文件指纹与基础元数据（时长、格式、分辨率）。
4.  **AI 语义匹配 (Semantic Matching)**
    *   基于剧本拆解结果，在素材库中匹配最接近的视频片段/图片。

#### 1.2.2 次要功能 (P1 - Initial Release)
1.  **流量/性能控制 (Traffic Control)**
    *   提供“静默”、“平衡”、“狂暴”三种模式，动态调整扫描线程数和 API 请求频率。
    *   防止后台任务占用过多带宽影响前台操作。
2.  **存储拓扑可视化 (Storage Topology)**
    *   图形化展示本地服务器与 NAS 节点的连接状态 (在线/离线/延迟)。

### 1.3 非功能需求 (Non-functional Requirements)
*   **性能**: 启动器冷启动时间 < 3秒；服务全部就绪耗时 < 5秒。
*   **兼容性**: 
    *   OS: Windows 10/11 (主要开发环境), macOS (计划支持)。
    *   Browser: Chrome / Edge 80+。
*   **安全性**: 若缺失配置文件 (`.env`) 或关键目录，需弹窗提示并阻止崩溃；所有子进程需随主程序关闭而安全退出 (Graceful Shutdown)。

### 1.4 用户流程 (User Architecture)
1.  用户双击桌面的 `Pervis PRO` 快捷方式。
2.  **Launcher 启动**: 自动进行环境自检 -> 启动 Backend (FastAPI :8000) -> 启动 Frontend (Vite :3000)。
3.  **Web 界面打开**: 浏览器自动跳转至 Dashboard。
4.  用户在 Web 端上传剧本 -> 等待 AI 分析 -> 查看匹配结果。
5.  用户关闭 Launcher 窗口 -> 所有后台服务自动终止。

### 1.5 验收标准 (Acceptance Criteria)
*   [ ] 点击“一键启动”后，5秒内浏览器自动打开且页面无报错。
*   [ ] 启动器能够正确识别并显示 `API ✓ | Web ✓` 状态。
*   [ ] 扫描 NAS 目录时，UI 不卡顿（异步线程正常工作）。
*   [ ] 关闭启动器后，任务管理器中无残留的 `python.exe` (backend) 或 `node.exe` (frontend) 僵尸进程。

---

## 2. 技术实现路径 (Technical Implementation Path)

### 2.1 技术选型 (Stack Selection)

| 模块 | 选型 | 理由 (Rationale) |
| :--- | :--- | :--- |
| **Launcher UI** | **Python + CustomTkinter** | 提供现代化、高DPI支持的深色模式 UI；能直接调用 OS 底层 API (Win32) 进行盘符扫描；与 Backend 同语言栈，维护成本低。 |
| **Backend** | **FastAPI (Python)** | 高性能异步框架，天然适配 AI 库 (LangChain/Gemini SDK)；OpenAPI 文档自动生成方便前后端联调。 |
| **Frontend** | **React + Vite** | 现代 Web 开发标准，构建速度快，生态丰富 (组件库)。 |
| **Database** | **SQLite (MVP) -> PostgreSQL** | MVP 阶段单文件数据库部署最简便；后期可无缝迁移至 PG。 |
| **IPC/Process** | **subprocess + threading** | 启动器通过标准输入输出 (StdIO) 捕获子进程日志，简单可靠，无需复杂的 Message Queue。 |

### 2.2 架构设计 (Architecture)

```mermaid
graph TD
    User[用户] --> LauncherUI[启动器 UI (CustomTkinter)]
    
    subgraph Launcher System
        LauncherUI --> detector[Detector (环境侦测)]
        LauncherUI --> process_mgr[ProcessManager (进程管理)]
        LauncherUI --> traffic_crtl[TrafficControl (性能配置)]
    end
    
    process_mgr -- Spawn/Kill --> BackendService[Backend (FastAPI :8000)]
    process_mgr -- Spawn/Kill --> FrontendService[Frontend (Vite :3000)]
    
    subgraph Core Services
        BackendService --> AI_Engine[AI Engine (Gemini)]
        BackendService --> DB[(SQLite DB)]
        BackendService --> FileSystem[FileSystem (NAS/Local)]
    end
    
    FrontendService -- HTTP API --> BackendService
```

### 2.3 开发迭代规划

#### 阶段一：基础架构建设 (Infrastructure) - **已完成**
*   搭建 Monorepo 目录结构。
*   实现 Launcher 基础框架 (Detector, ProcessManagerUI)。
*   完成 Python 虚拟环境与依赖管理逻辑。

#### 阶段二：核心业务逻辑 (MVP Logic) - **当前阶段**
*   **Launcher**: 实现 NAS 盘符递归扫描，集成可视化拓扑图。
*   **Backend**: 接入 Gemini API 实现剧本 Prompt 工程；实现文件系统 Crawler。
*   **Frontend**: 搭建 Dashboard 框架，展示系统状态与文件列表。

#### 阶段三：视觉与体验优化 (Refinement) - **Next**
*   **Launcher**: 实现 Akiba 风格 UI (Sidebar, Animations)。**(已完成)**
*   **Feature**: 增加断点续传、增量扫描功能。

### 2.4 关键技术难点与解决方案
1.  **NAS 大量小文件扫描慢**:
    *   *方案*: 使用 `scandir` (Python 3.5+) 替代 `listdir`；并在 `TrafficControl` 中实现多线程生产者-消费者模型，根据用户设定的模式（平衡/狂暴）动态调整并发数。
2.  **跨进程日志实时显示**:
    *   *方案*: `ProcessManager` 使用独立线程无阻塞读取 `subprocess.stdout`，并通过 `queue.Queue` 将日志回传给主 UI 线程进行渲染，避免界面假死。
3.  **端口冲突处理**:
    *   *方案*: `Detector` 在启动前通过 `socket.connect` 检测 8000/3000 端口。若被占用，弹窗提示用户或尝试 Kill 占用进程（需谨慎）。

---

## 3. 项目文件结构 (Project Structure)

```text
Pervis_PRO/
├── .env                       # 全局配置文件 (API Keys, Paths)
├── 启动_Pervis_PRO.py          # [Entry] 统一启动入口
├── launcher/                  # [Module] 启动器与控制中心
│   ├── main.py                # 启动器主逻辑
│   ├── services/              # 纯逻辑服务层
│   │   ├── detector.py        # 环境/网络侦测
│   │   ├── process_manager.py # 子进程与日志管理
│   │   ├── scanner.py         # 文件扫描器
│   │   └── traffic_control.py # 性能控制配置
│   └── ui/                    # 界面层 (CustomTkinter)
│       ├── main_window.py     # 主窗口容器
│       ├── storage_panel.py   # 存储拓扑组件
│       └── pages/             # 页面子模块
│           ├── home.py        # 首页
│           ├── console.py     # 日志控制台
│           └── settings.py    # 设置页
├── backend/                   # [Module] 核心业务后端
│   ├── main.py                # FastAPI App 入口
│   ├── core/                  # 核心配置
│   ├── routers/               # API 路由
│   └── services/              # 业务逻辑 (AI, FileOps)
├── frontend/                  # [Module] Web 前端
│   ├── package.json
│   ├── vite.config.js
│   └── src/
├── assets/                    # 静态资源 (Icons, Images)
├── logs/                      # 系统运行日志
└── docs/                      # 项目文档
    └── PERVIS_PRO_PRODUCT_DOCUMENTATION.md
```

---

## 4. MVP 最小可行产品方案

### 4.1 核心价值 (Value Proposition)
MVP 版本必须能够验证 **“用户点击一次即可建立本地文件与 AI 的连接”** 这一核心假设。

### 4.2 功能范围 (Scope)
| 模块 | 必须包含 (Must Have) | 暂不包含 (Won't Have) |
| :--- | :--- | :--- |
| **启动器** | 完整环境自检、一键启动、Web/API 端口监控、自定义素材路径引入 | 自动更新、插件系统、换肤功能 |
| **AI 引擎** | 文本脚本 -> 关键词提取 | 视频内容深度理解 (Visual Understanding) |
| **文件系统** | 基础文件遍历、元数据读取 | 视频转码、云端同步 |

### 4.3 核心指标 (Key Metrics)
1.  **启动成功率**: > 95% (在预设环境配置下)。
2.  **交互延迟**: 点击“一键启动”到 Web 页面呈现 < 8秒。
3.  **稳定性**: 连续运行 4 小时无 Crash。

### 4.4 迭代路线图 (Roadmap)
### 4.4 迭代路线图 (Roadmap)
*   **v0.1.0 (Alpha)**: 跑通前后端启动流程，验证环境。**(已完成)**
*   **v0.2.0 (Beta)**: 启动器 UI 重构 (Akiba Style)，完善错误处理与日志查看。**(当前版本)**
*   **v0.3.0 (Vision Activation & Vector Memory) - CURRENT PHASE**:
    *   **Unlock Vision Kernel**: 移除 `visual_processor` 的 Mock 限制，激活已预埋的 CLIP/Gemini Vision 本地分析能力。**(已完成 - Pro Mode Active)**
    *   **Vector Database Implementation**: 引入 ChromaDB/FAISS，将 `visual_processor` 提取的特征向量 (Feature Vectors) 进行持久化存储，实现毫秒级“以文搜图”。**(Pending)**
    *   **Semantic Search API**: 升级后端搜索接口，支持 Vector Similarity Search。
*   **v0.4.0 (Workflow Integration)**:
    *   **Export Pipeline**: 生成标准 XML/EDL 文件，支持一键导入 Premiere/DaVinci。
    *   **Team Sync**: 支持 NAS 路径的云端配置同步，多人协作去重。
*   **v1.0.0 (Release)**: 完成核心 AI 匹配业务闭环，正式交付用户。

---

*注：本文档基于 2025-12-19 之系统状态生成，作为后续开发与代码审核的基准文件。*
