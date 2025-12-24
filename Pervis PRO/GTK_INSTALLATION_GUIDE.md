# GTK依赖安装指南

**目标**: 安装GTK3库以解决后端Python依赖问题  
**预计时间**: 30-60分钟  
**方法**: 使用MSYS2安装GTK

---

## 安装步骤

### 步骤1: 下载MSYS2（5分钟）

1. 访问 https://www.msys2.org/
2. 下载最新的MSYS2安装器
   - 64位: `msys2-x86_64-xxxxxxxx.exe`
3. 或使用命令下载：

```powershell
# 下载MSYS2安装器
$url = "https://github.com/msys2/msys2-installer/releases/download/2024-01-13/msys2-x86_64-20240113.exe"
$output = "$env:TEMP\msys2-installer.exe"
Invoke-WebRequest -Uri $url -OutFile $output
Write-Host "✅ MSYS2安装器已下载到: $output"
```

### 步骤2: 安装MSYS2（10分钟）

```powershell
# 静默安装MSYS2到默认位置
Start-Process -FilePath "$env:TEMP\msys2-installer.exe" -ArgumentList "install", "--root", "C:\msys64", "--confirm-command" -Wait

# 或手动安装：
# 1. 双击运行安装器
# 2. 安装路径：C:\msys64（默认）
# 3. 完成后不要立即运行MSYS2
```

### 步骤3: 更新MSYS2包管理器（5分钟）

```powershell
# 启动MSYS2并更新
C:\msys64\usr\bin\bash.exe -lc "pacman -Syu --noconfirm"

# 关闭窗口后再次更新
C:\msys64\usr\bin\bash.exe -lc "pacman -Su --noconfirm"
```

### 步骤4: 安装GTK3和依赖（10-15分钟）

```powershell
# 安装GTK3及相关库
C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm mingw-w64-x86_64-gtk3"

# 安装额外的GObject库（解决libgobject-2.0-0问题）
C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm mingw-w64-x86_64-gobject-introspection"
C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm mingw-w64-x86_64-cairo"
C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm mingw-w64-x86_64-pango"

# 安装WeasyPrint需要的库
C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm mingw-w64-x86_64-pango-devel"
```

### 步骤5: 配置环境变量（2分钟）

```powershell
# 添加mingw64到PATH（临时，当前会话）
$env:Path = "C:\msys64\mingw64\bin;$env:Path"

# 永久添加到系统PATH
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\msys64\mingw64\bin", [EnvironmentVariableTarget]::Machine)

# 设置GI_TYPELIB_PATH（GObject Introspection需要）
[Environment]::SetEnvironmentVariable("GI_TYPELIB_PATH", "C:\msys64\mingw64\lib\girepository-1.0", [EnvironmentVariableTarget]::Machine)

Write-Host "✅ 环境变量已配置"
```

### 步骤6: 验证安装（2分钟）

```powershell
# 检查DLL是否可访问
Test-Path "C:\msys64\mingw64\bin\libgobject-2.0-0.dll"
Test-Path "C:\msys64\mingw64\bin\libgtk-3-0.dll"
Test-Path "C:\msys64\mingw64\bin\libcairo-2.dll"

# 检查环境变量
$env:Path -split ';' | Select-String "msys64"
```

### 步骤7: 重新安装Python依赖（可选，5-10分钟）

某些库可能需要重新安装以识别新的GTK：

```powershell
cd "f:\100KIRO project\Pervis PRO"

# 重新安装可能需要GTK的库
pip uninstall -y weasyprint
pip install weasyprint

# 如需重新安装其他依赖
# pip install --upgrade --force-reinstall sentence-transformers
```

### 步骤8: 测试后端启动（5分钟）

```powershell
# 移除所有FORCE_MOCK_MODE（可选）
# 或保持Mock模式，只测试启动

cd "f:\100KIRO project\Pervis PRO\backend"
python main.py

# 在另一个终端测试
Start-Sleep -Seconds 10
curl http://localhost:8000/api/health
```

---

## 快速执行脚本

完整自动化脚本（需要管理员权限）：

```powershell
# install_gtk.ps1
# 以管理员身份运行

Write-Host "🚀 开始安装GTK依赖..." -ForegroundColor Green

# 1. 下载MSYS2
Write-Host "📥 下载MSYS2..." -ForegroundColor Yellow
$url = "https://github.com/msys2/msys2-installer/releases/download/2024-01-13/msys2-x86_64-20240113.exe"
$installer = "$env:TEMP\msys2-installer.exe"

if (!(Test-Path $installer)) {
    Invoke-WebRequest -Uri $url -OutFile $installer
    Write-Host "✅ 下载完成" -ForegroundColor Green
} else {
    Write-Host "✅ 安装器已存在" -ForegroundColor Green
}

# 2. 安装MSYS2
Write-Host "📦 安装MSYS2..." -ForegroundColor Yellow
if (!(Test-Path "C:\msys64")) {
    Start-Process -FilePath $installer -ArgumentList "install", "--root", "C:\msys64", "--confirm-command" -Wait
    Write-Host "✅ MSYS2安装完成" -ForegroundColor Green
} else {
    Write-Host "✅ MSYS2已安装" -ForegroundColor Green
}

# 3. 更新包管理器
Write-Host "🔄 更新包管理器..." -ForegroundColor Yellow
C:\msys64\usr\bin\bash.exe -lc "pacman -Sy --noconfirm"

# 4. 安装GTK3
Write-Host "📚 安装GTK3和依赖..." -ForegroundColor Yellow
C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm mingw-w64-x86_64-gtk3 mingw-w64-x86_64-gobject-introspection mingw-w64-x86_64-cairo mingw-w64-x86_64-pango"

# 5. 配置环境变量
Write-Host "⚙️  配置环境变量..." -ForegroundColor Yellow
$mingwPath = "C:\msys64\mingw64\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)

if ($currentPath -notlike "*$mingwPath*") {
    [Environment]::SetEnvironmentVariable("Path", "$currentPath;$mingwPath", [EnvironmentVariableTarget]::Machine)
    Write-Host "✅ PATH已更新" -ForegroundColor Green
} else {
    Write-Host "✅ PATH已包含mingw64" -ForegroundColor Green
}

# 更新当前会话的PATH
$env:Path = "$mingwPath;$env:Path"

# 6. 验证安装
Write-Host "✔️  验证安装..." -ForegroundColor Yellow
if (Test-Path "C:\msys64\mingw64\bin\libgobject-2.0-0.dll") {
    Write-Host "✅ libgobject-2.0-0.dll 已安装" -ForegroundColor Green
} else {
    Write-Host "❌ libgobject-2.0-0.dll 未找到" -ForegroundColor Red
}

Write-Host "`n🎉 GTK依赖安装完成!" -ForegroundColor Green
Write-Host "⚠️  请重新打开PowerShell窗口以使环境变量生效" -ForegroundColor Yellow
```

---

## 故障排查

### 问题1: MSYS2下载失败

**解决方案**:
1. 手动访问 https://www.msys2.org/ 下载
2. 或使用镜像站点下载

### 问题2: pacman命令失败

**解决方案**:
```powershell
# 重置pacman数据库
C:\msys64\usr\bin\bash.exe -lc "rm -rf /var/lib/pacman/sync/*"
C:\msys64\usr\bin\bash.exe -lc "pacman -Sy"
```

### 问题3: 环境变量未生效

**解决方案**:
1. 关闭所有PowerShell窗口
2. 重新打开新的PowerShell窗口
3. 验证: `$env:Path -split ';' | Select-String "msys64"`

### 问题4: Python仍然找不到DLL

**解决方案**:
```powershell
# 检查DLL位置
Get-ChildItem "C:\msys64\mingw64\bin\libgobject*.dll"

# 手动添加到Python脚本
$env:Path = "C:\msys64\mingw64\bin;$env:Path"
python backend/main.py
```

---

## 安装后恢复FORCE_MOCK_MODE

安装成功后，可以选择性地移除之前添加的FORCE_MOCK_MODE：

```python
# audio_transcriber.py, visual_processor.py, semantic_search.py
# 将 FORCE_MOCK_MODE = True 改为 False
FORCE_MOCK_MODE = False  # 或直接删除此行
```

---

**创建时间**: 2025-12-18 17:21  
**预计完成**: 17:50-18:20  
**状态**: 准备执行
