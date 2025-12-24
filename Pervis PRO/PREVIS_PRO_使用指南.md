# PreVis PRO 完整使用指南

## 📋 目录
1. [快速启动](#快速启动)
2. [功能使用说明](#功能使用说明)
3. [素材管理](#素材管理)
4. [团队部署指南](#团队部署指南)
5. [常见问题](#常见问题)

---

## 🚀 快速启动

### 方式一：GUI启动器（推荐，秋叶风格）

双击运行项目根目录下的GUI启动器：
```
PreVis_PRO_启动器.pyw
```

特点：
- 单窗口界面，无CMD弹窗
- 自动检查和安装依赖
- 实时显示服务状态
- 一键启动/停止服务
- 快捷按钮访问各功能

### 方式二：批处理启动

双击运行：
```
启动PreVis_PRO.bat
```

或者运行Python启动器：
```bash
python 一键启动PreVis_PRO.py
```

### 方式二：手动启动

#### 步骤1：启动后端服务
```bash
# 进入后端目录
cd backend

# 启动FastAPI服务
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 步骤2：启动前端服务
```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

#### 步骤3：访问系统
- **前端界面**: http://localhost:3000
- **后端API文档**: http://localhost:8000/docs
- **MVP工作流**: http://localhost:3000/mvp-workflow

### 系统检查
启动后运行健康检查：
```bash
python sanity_check.py
```

---

## 🎬 功能使用说明

### MVP完整工作流（核心功能）

访问地址：`http://localhost:3000/mvp-workflow`

#### 步骤1：剧本输入
1. 在文本框中输入剧本内容
2. 支持标准剧本格式（EXT./INT. 场景标记）
3. 点击"分析剧本"按钮

**示例剧本：**
```
FADE IN:

EXT. 城市街道 - 白天

繁忙的都市街道，人来人往。

一个年轻人匆忙走过，手里拿着咖啡。

CUT TO:

INT. 办公室 - 白天

现代化的开放式办公室。

FADE OUT.
```

#### 步骤2：Beat分析
- 系统自动将剧本分解为故事节拍（Beats）
- 每个Beat包含：内容描述、情感标签、场景标签
- 点击Beat旁边的搜索图标可以搜索匹配素材

#### 步骤3：素材搜索
- 输入关键词搜索素材库
- 支持语义搜索（理解意图）
- 点击搜索结果将素材添加到时间轴

#### 步骤4：时间轴编辑
- **拖拽操作**：移动片段位置
- **点击选择**：选中片段进行编辑
- **Ctrl+点击**：多选片段
- **快捷键**：
  - `空格`：播放/暂停
  - `Delete`：删除选中片段
  - `Home`：跳到开始
  - `End`：跳到结尾
  - `←/→`：前进/后退1秒

#### 步骤5：预览播放
- 实时预览编辑效果
- 支持播放速度调节（0.25x - 2x）
- 支持全屏播放

#### 步骤6：导出分享
- 点击"开始渲染"按钮
- 实时显示渲染进度
- 完成后可下载视频文件

---

## 📁 素材管理

### 素材目录结构
```
assets/
├── originals/      # 原始素材文件
├── proxies/        # 代理文件（低分辨率预览）
├── thumbnails/     # 缩略图
└── audio/          # 音频文件
```

### 添加素材方式

#### 方式一：通过界面上传
1. 访问 `http://localhost:3000/batch-processing`
2. 拖拽文件到上传区域
3. 等待处理完成

#### 方式二：直接复制文件
1. 将视频/图片文件复制到 `assets/originals/` 目录
2. 运行素材处理脚本：
```bash
python fix_asset_processing.py
```

#### 方式三：使用CLI工具
```bash
# 添加单个素材
python pervis_cli.py add-asset "path/to/video.mp4"

# 批量添加目录
python pervis_cli.py scan-directory "path/to/media/folder"
```

### 支持的素材格式
- **视频**: MP4, MOV, AVI, MKV, WebM
- **图片**: JPG, PNG, GIF, WebP
- **音频**: MP3, WAV, AAC, FLAC

### 素材处理流程
1. **上传** → 文件保存到 `originals/`
2. **分析** → 提取元数据、生成缩略图
3. **向量化** → 生成语义搜索向量
4. **索引** → 加入搜索数据库

---

## 🌐 团队部署指南

### 局域网部署（公司内部测试）

#### 步骤1：确定服务器IP
```bash
# Windows
ipconfig

# 找到IPv4地址，例如：192.168.1.100
```

#### 步骤2：修改后端配置
编辑 `backend/.env` 文件：
```env
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["http://192.168.1.100:3000", "http://localhost:3000"]
```

#### 步骤3：修改前端配置
编辑 `frontend/.env` 文件：
```env
VITE_API_URL=http://192.168.1.100:8000
```

#### 步骤4：启动服务
```bash
# 后端
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm run dev -- --host 0.0.0.0
```

#### 步骤5：团队成员访问
其他电脑访问：`http://192.168.1.100:3000`

### 共享素材库

#### 方式一：网络共享文件夹
1. 将 `assets` 文件夹设置为网络共享
2. 修改 `.env` 中的 `ASSET_ROOT` 指向共享路径：
```env
ASSET_ROOT=\\\\192.168.1.100\\shared\\assets
```

#### 方式二：NAS存储
1. 将素材存储在NAS上
2. 映射网络驱动器（如 Z:）
3. 修改配置：
```env
ASSET_ROOT=Z:\\previs_assets
```

### 防火墙设置
确保开放以下端口：
- **8000**: 后端API
- **3000**: 前端界面

Windows防火墙设置：
```powershell
# 以管理员身份运行
netsh advfirewall firewall add rule name="PreVis Backend" dir=in action=allow protocol=TCP localport=8000
netsh advfirewall firewall add rule name="PreVis Frontend" dir=in action=allow protocol=TCP localport=3000
```

---

## 🔧 环境要求

### 必需软件
| 软件 | 版本要求 | 用途 |
|------|---------|------|
| Python | 3.10+ | 后端运行 |
| Node.js | 18+ | 前端运行 |
| FFmpeg | 4.0+ | 视频处理 |

### FFmpeg安装
```bash
# Windows (使用Chocolatey)
choco install ffmpeg

# 或手动下载
# https://ffmpeg.org/download.html
# 解压后将bin目录添加到系统PATH
```

### Python依赖安装
```bash
cd backend
pip install -r requirements.txt
```

### Node.js依赖安装
```bash
cd frontend
npm install
```

---

## ❓ 常见问题

### Q1: 后端启动失败
**错误**: `ModuleNotFoundError`
**解决**: 
```bash
cd backend
pip install -r requirements.txt
```

### Q2: 前端无法连接后端
**错误**: `Network Error` 或 `CORS Error`
**解决**:
1. 确认后端已启动（访问 http://localhost:8000/api/health）
2. 检查 `frontend/.env` 中的API地址配置

### Q3: 视频渲染失败
**错误**: `FFmpeg not found`
**解决**:
1. 安装FFmpeg
2. 确保FFmpeg在系统PATH中
3. 重启终端和服务

### Q4: 素材搜索无结果
**原因**: 素材未被索引
**解决**:
```bash
python fix_asset_processing.py
```

### Q5: 局域网其他电脑无法访问
**检查项**:
1. 防火墙是否开放端口
2. 服务是否绑定到 `0.0.0.0`
3. IP地址是否正确

---

## 📞 技术支持

### 系统状态检查
```bash
python sanity_check.py
```

### 查看API文档
访问：http://localhost:8000/docs

### 日志位置
- 后端日志：终端输出
- 前端日志：浏览器控制台（F12）

### 数据库位置
- SQLite数据库：`backend/pervis_director.db`

---

## 🎯 快速测试清单

给团队成员的测试步骤：

1. ✅ 访问 http://[服务器IP]:3000
2. ✅ 点击进入 MVP工作流
3. ✅ 输入测试剧本，点击分析
4. ✅ 查看生成的Beat列表
5. ✅ 搜索素材并添加到时间轴
6. ✅ 预览播放效果
7. ✅ 尝试导出视频

**预期结果**: 能够完成从剧本到视频的完整流程

---

*文档版本: 1.0*  
*更新时间: 2024-12-19*
