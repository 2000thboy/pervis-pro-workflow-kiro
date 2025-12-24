# 🚀 Pervis PRO 控制中心 (Launcher V2) 使用手册

全新设计的 **"Control Center"** 已就绪。它取代了旧的启动脚本，为您提供全可视化的系统管理能力。

## 📦 1. 安装依赖 (Prerequisites)

为了获得现代化的 UI 体验，我们需要安装 `customtkinter` 库：

```bash
pip install customtkinter
```

## ▶️ 2. 启动控制中心 (How to Launch)

在项目根目录下运行：

```bash
python launcher/main.py
```

## ✨ 3. 功能概览 (Features)

### 🟢 存储拓扑图 (Storage Topology)
*   **左侧面板**: 您的 "可视化" NAS 仪表盘。
*   它会自动扫描 `Z:\Movies` 等路径。
*   **连线变绿** 表示挂载成功且 AI 正在索引。
*   **连线变红** 表示断开连接 (点击 "Reconnect" 即可)。

### 🎚️ 流量阀 (Traffic Control)
*   **右侧面板**: **"Processing Speed"** 滑块。
    *   **Silent Mode (静默)**: 后台慢慢跑，不干扰您打游戏或看片。
    *   **Full Mode (全速)**: 占满带宽，全速生成 AI 标签。

### 📊 AI 监控仪表 (AI Monitor)
*   **底部面板**: 实时显示 **IPM (Images Per Minute)** 处理速度。
*   (注: 目前为模拟数据显示，后续将对接真实 Backend 数据流)

---

## 🛠️ 故障排查
如果启动报错，请先运行诊断脚本：
```bash
python verify_launcher.py
```
