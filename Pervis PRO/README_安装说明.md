# Pervis PRO 安装说明

## 📋 当前状态

经过检测，你的系统需要安装以下基础环境：

- ❌ **Python 3.10+** - 未安装
- ❌ **Node.js 18+** - 未安装
- ❌ **Git** - 未安装
- ❌ **FFmpeg** - 未安装（可选）

## 🚀 安装步骤

### 步骤 1：安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.10 或更高版本
3. **重要**：安装时勾选 ✅ "Add Python to PATH"
4. 点击 "Install Now"

### 步骤 2：安装 Node.js

1. 访问 https://nodejs.org/
2. 下载 LTS 版本（推荐）
3. 使用默认设置安装

### 步骤 3：安装 Git

1. 访问 https://git-scm.com/
2. 下载并安装
3. 使用默认设置

### 步骤 4：安装 FFmpeg（可选但推荐）

**方法 A：直接下载**
1. 访问 https://www.ffmpeg.org/download.html
2. 下载 Windows 版本
3. 解压到 `C:\ffmpeg`
4. 添加 `C:\ffmpeg\bin` 到系统环境变量 PATH

**方法 B：使用 Chocolatey（推荐）**
```powershell
# 以管理员身份运行 PowerShell
choco install ffmpeg
```

## 🔄 安装完成后

### 1. 重启命令行
关闭并重新打开 PowerShell 或命令提示符

### 2. 验证安装
```bash
python --version
node --version
git --version
ffmpeg -version
```

### 3. 运行自动安装脚本
```bash
python setup_environment.py
```

这个脚本会自动：
- 创建 Python 虚拟环境
- 安装后端依赖（FastAPI, SQLAlchemy 等）
- 安装前端依赖（React, Vite 等）
- 安装启动器依赖

### 4. 配置 API 密钥

编辑 `backend/.env` 文件：

```env
# AI 配置
GEMINI_API_KEY=your_gemini_api_key_here
LLM_PROVIDER=gemini

# 数据库配置
DATABASE_URL=sqlite:///./pervis_director.db

# 存储配置
ASSET_ROOT=./storage/assets
STORAGE_ROOT=./storage
```

**获取 Gemini API 密钥：**
1. 访问 https://makersuite.google.com/app/apikey
2. 创建新的 API 密钥
3. 复制并粘贴到 `.env` 文件

### 5. 启动项目

```bash
python 启动_Pervis_PRO.py
```

## 📦 项目依赖说明

### 后端依赖
- **FastAPI** - Web 框架
- **SQLAlchemy** - 数据库 ORM
- **Google Generative AI** - AI 功能
- **Sentence Transformers** - 文本嵌入
- **ChromaDB** - 向量数据库
- **FFmpeg-Python** - 视频处理
- **Celery + Redis** - 异步任务队列

### 前端依赖
- **React 18** - UI 框架
- **Vite** - 构建工具
- **TypeScript** - 类型系统
- **React Router** - 路由管理
- **Lucide React** - 图标库

### 启动器依赖
- **CustomTkinter** - 现代化 GUI
- **Pillow** - 图像处理

## 🔧 手动安装（如果自动脚本失败）

### 后端
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 前端
```bash
cd frontend
npm install
```

### 启动器
```bash
pip install customtkinter pillow
```

## 🐛 常见问题

### Python 命令未找到
- 确保安装时勾选了 "Add Python to PATH"
- 重启命令行
- 或使用 `python3` 命令

### npm 安装慢或失败
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com/
npm install
```

### pip 安装慢
```bash
# 使用国内镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### PowerShell 脚本执行被阻止
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 权限问题
以管理员身份运行 PowerShell

## 📚 更多资源

- **详细文档**: `环境安装指南.md`
- **快速指南**: `一键安装环境.md`
- **项目文档**: `README_FOR_COLLEAGUE.md`
- **使用指南**: `PERVIS_PRO_PRODUCT_DOCUMENTATION.md`

## 🎯 下一步

安装完成后，你可以：
1. 运行 `python 启动_Pervis_PRO.py` 启动项目
2. 访问 http://localhost:5173 查看前端
3. 访问 http://localhost:8000/docs 查看 API 文档
4. 阅读 `CLI_USAGE_GUIDE.md` 了解命令行使用

---

**祝你使用愉快！如有问题，请查看项目文档或联系技术支持。**