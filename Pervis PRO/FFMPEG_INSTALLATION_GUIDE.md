# FFmpeg 安装指南

## 概述

PreVis PRO 需要 FFmpeg 来处理视频渲染和导出功能。本指南将帮助您在不同操作系统上安装 FFmpeg。

## 系统要求

- **最低版本**: FFmpeg 4.0 或更高
- **推荐版本**: FFmpeg 4.4 或更高
- **支持的操作系统**: Windows, macOS, Linux

## 安装方法

### Windows

#### 方法 1: 使用 Chocolatey (推荐)

1. 安装 Chocolatey (如果尚未安装):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. 安装 FFmpeg:
   ```powershell
   choco install ffmpeg
   ```

#### 方法 2: 手动安装

1. 访问 [FFmpeg 官方网站](https://ffmpeg.org/download.html#build-windows)
2. 下载 Windows 版本的 FFmpeg
3. 解压到目录 (例如: `C:\ffmpeg`)
4. 将 `C:\ffmpeg\bin` 添加到系统 PATH 环境变量

### macOS

#### 方法 1: 使用 Homebrew (推荐)

```bash
# 安装 Homebrew (如果尚未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 FFmpeg
brew install ffmpeg
```

#### 方法 2: 使用 MacPorts

```bash
sudo port install ffmpeg
```

### Linux

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

#### CentOS/RHEL/Fedora

```bash
# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg

# Fedora
sudo dnf install ffmpeg
```

#### Arch Linux

```bash
sudo pacman -S ffmpeg
```

## 验证安装

安装完成后，打开终端/命令提示符并运行：

```bash
ffmpeg -version
```

您应该看到类似以下的输出：

```
ffmpeg version 4.4.2 Copyright (c) 2000-2021 the FFmpeg developers
built with gcc 9 (Ubuntu 9.4.0-1ubuntu1~20.04.1)
configuration: --prefix=/usr --extra-version=0ubuntu0.20.04.1 ...
```

## 故障排除

### 常见问题

#### 1. "ffmpeg: command not found" 或 "'ffmpeg' 不是内部或外部命令"

**原因**: FFmpeg 未正确安装或未添加到 PATH 环境变量

**解决方案**:
- 确认 FFmpeg 已正确安装
- 检查 PATH 环境变量是否包含 FFmpeg 的 bin 目录
- 重启终端/命令提示符
- 在 Windows 上，可能需要重启计算机

#### 2. 版本过低警告

**原因**: 安装的 FFmpeg 版本低于推荐版本

**解决方案**:
- 更新到最新版本的 FFmpeg
- 使用包管理器更新: `brew upgrade ffmpeg` (macOS) 或 `sudo apt upgrade ffmpeg` (Ubuntu)

#### 3. 权限错误

**原因**: 没有足够的权限安装或运行 FFmpeg

**解决方案**:
- 在 Linux/macOS 上使用 `sudo` 运行安装命令
- 在 Windows 上以管理员身份运行命令提示符

### 高级配置

#### 自定义编译选项

如果您需要特定的编解码器支持，可以从源代码编译 FFmpeg:

```bash
# 下载源代码
git clone https://git.ffmpeg.org/ffmpeg.git
cd ffmpeg

# 配置编译选项
./configure --enable-gpl --enable-libx264 --enable-libx265 --enable-libvpx

# 编译和安装
make
sudo make install
```

#### 环境变量配置

您可以设置以下环境变量来自定义 FFmpeg 行为:

- `FFMPEG_PATH`: 指定 FFmpeg 可执行文件的路径
- `FFMPEG_DATADIR`: 指定 FFmpeg 数据目录

## PreVis PRO 集成

### 自动检测

PreVis PRO 会在启动时自动检测 FFmpeg 的安装状态:

1. 检查系统 PATH 中的 FFmpeg
2. 验证版本兼容性
3. 显示安装状态和建议

### 手动配置

如果自动检测失败，您可以在 PreVis PRO 的设置中手动指定 FFmpeg 路径:

1. 打开 PreVis PRO
2. 进入 "系统状态" 页面
3. 点击 "FFmpeg 状态" 部分的 "安装指南"
4. 按照提示完成安装

### 性能优化

为了获得最佳性能，建议:

1. 使用 SSD 存储临时文件
2. 确保有足够的 RAM (推荐 8GB 以上)
3. 使用硬件加速 (如果可用)

## 支持的格式

PreVis PRO 支持以下视频格式的导出:

- **MP4** (H.264/H.265)
- **MOV** (QuickTime)
- **AVI** (多种编解码器)
- **WebM** (VP8/VP9)

## 获取帮助

如果您在安装过程中遇到问题:

1. 查看 PreVis PRO 的系统诊断页面
2. 检查系统日志中的错误信息
3. 访问 [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)
4. 联系 PreVis PRO 技术支持

## 更新日志

- **v1.0**: 初始版本，支持基本的 FFmpeg 检测和安装指导
- **v1.1**: 添加了自动版本检测和兼容性验证
- **v1.2**: 改进了错误处理和用户友好的安装指导

---

*最后更新: 2024年12月*