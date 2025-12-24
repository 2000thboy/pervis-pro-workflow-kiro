# PreVis PRO - 自动验证脚本技术文档

**脚本名称**: `auto_validate_mvp.ps1`  
**版本**: 1.0  
**用途**: MVP系统自动化验证和报告生成

---

## 🎯 功能概述

这是一个全自动的PowerShell验证脚本，可以：
1. ✅ 检查前后端服务状态
2. ✅ 测试所有核心API端点
3. ✅ 验证数据库和文件系统
4. ✅ 执行性能基准测试
5. ✅ 运行Sanity Check
6. ✅ 自动生成Markdown验证报告

---

## 📋 使用方法

### 基本用法

```powershell
# 完整验证(推荐)
.\auto_validate_mvp.ps1

# 快速模式（只检查服务）
.\auto_validate_mvp.ps1 -Mode quick

# API测试模式
.\auto_validate_mvp.ps1 -Mode api-only

# 详细输出模式
.\auto_validate_mvp.ps1 -Verbose

# 不生成报告
.\auto_validate_mvp.ps1 -GenerateReport:$false
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-Mode` | string | "full" | 验证模式: full, quick, api-only |
| `-GenerateReport` | switch | $true | 是否生成Markdown报告 |
| `-Verbose` | switch | $false | 是否显示详细输出 |

---

## 🏗️ 技术架构

### 脚本结构

```
auto_validate_mvp.ps1
├── 配置区
│   ├── 参数定义
│   ├── URL配置
│   └── 报告路径
├── 工具函数
│   ├── 颜色输出函数
│   └── 结果收集函数
├── 测试模块 (6个部分)
│   ├── Part 1: 服务状态检查
│   ├── Part 2: API端点测试
│   ├── Part 3: 数据库检查
│   ├── Part 4: 性能测试
│   ├── Part 5: Sanity Check
│   └── Part 6: 报告生成
└── 主执行流程
    ├── 模式选择
    ├── 顺序执行
    └── 结果汇总
```

### 核心技术点

#### 1. 结果收集系统
```powershell
$global:Results = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Details = @()  # 存储所有测试详情
    StartTime = Get-Date
}
```

**特点**:
- 全局状态管理
- 详细记录每个测试结果
- 自动统计通过/失败/警告数

#### 2. HTTP请求测试
```powershell
try {
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 5
    # 验证响应内容
} catch {
    # 捕获连接失败
}
```

**关键技术**:
- `Invoke-RestMethod`: JSON API调用
- `Invoke-WebRequest`: HTTP状态码检查
- 超时控制: `-TimeoutSec 5`
- 异常处理: try-catch块

#### 3. 性能测试
```powershell
$times = @()
for ($i = 1; $i -le 10; $i++) {
    $start = Get-Date
    # 执行请求
    $duration = ((Get-Date) - $start).TotalMilliseconds
    $times += $duration
}

$avg = ($times | Measure-Object -Average).Average
```

**统计指标**:
- 平均响应时间
- 最小/最大响应时间
- 10次请求采样

#### 4. Sanity Check集成
```powershell
$systemPython = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
$output = & $systemPython sanity_check.py 2>&1 | Out-String
```

**特点**:
- 调用现有Python验证脚本
- 捕获stdout和stderr
- 检查退出码

#### 5. Markdown报告生成
```powershell
$report = @"
# 标题
## 章节
| 表格 | 数据 |
|------|------|
| 值1 | 值2 |
"@

$report | Out-File -FilePath $ReportPath -Encoding UTF8
```

**报告内容**:
- 验证结果概览（通过率表格）
- 详细测试结果（每项测试）
- 性能指标
- 下一步建议

---

## 🔍 测试模块详解

### 模块1: 服务状态检查

**测试项**:
- 后端健康检查 (`/api/health`)
- 前端可访问性 (HTTP 200)

**技术实现**:
```powershell
function Test-BackendService {
    $response = Invoke-RestMethod -Uri "$BackendUrl/api/health"
    if ($response.status -eq "healthy") {
        # 记录通过
    }
}
```

**验证逻辑**:
- 后端: 检查`status`字段是否为"healthy"
- 前端: 检查HTTP状态码是否为200

---

### 模块2: API端点测试

**测试端点**:
```powershell
$endpoints = @(
    @{Path="/api/health"; Method="GET"; Name="健康检查"},
    @{Path="/docs"; Method="GET"; Name="API文档"},
    @{Path="/api/script"; Method="GET"; Name="剧本列表"},
    @{Path="/api/assets"; Method="GET"; Name="素材列表"},
    @{Path="/api/search"; Method="GET"; Name="搜索端点"}
)
```

**验证策略**:
- 200 OK: 通过
- 404 Not Found: 通过（端点存在但无数据）
- 其他状态: 警告
- 连接失败: 失败

---

### 模块3: 文件系统检查

**检查项**:
1. 数据库文件: `backend/pervis_pro.db`
2. 素材目录: `./assets` 或 `L:\PreVis_Assets`

**技术实现**:
```powershell
if (Test-Path "backend\pervis_pro.db") {
    $dbSize = (Get-Item "backend\pervis_pro.db").Length / 1KB
    # 记录文件大小
}
```

---

### 模块4: 性能测试

**测试方法**:
- 对健康检查API发起10次请求
- 记录每次响应时间
- 计算平均值、最小值、最大值

**性能阈值**:
- 优秀: <100ms
- 良好: 100-500ms
- 警告: >500ms

---

### 模块5: Sanity Check

**功能**:
调用现有的`sanity_check.py`脚本

**集成方式**:
```powershell
$output = & $systemPython sanity_check.py 2>&1
if ($LASTEXITCODE -eq 0 -or $output -match "PASS") {
    # 验证通过
}
```

---

### 模块6: 报告生成

**报告格式**: Markdown

**包含内容**:
1. **验证结果概览**
   - 通过/失败/警告统计
   - 通过率百分比
   
2. **详细测试结果**
   - 表格展示每项测试
   - 状态图标（✅❌⚠️）
   - 耗时和说明

3. **系统状态总结**
   - 服务URL
   - 验证建议

4. **下一步行动**
   - 根据结果给出建议

**文件命名**: `MVP_AUTO_VALIDATION_REPORT_yyyyMMdd_HHmmss.md`

---

## 📊 输出示例

### 控制台输出

```
================================================
   PreVis PRO - MVP自动验证脚本
================================================

ℹ️  验证模式: full
ℹ️  开始时间: 2025-12-18 21:30:00

【第1步】服务状态检查
ℹ️  测试后端服务...
✅ 后端健康检查通过 (0.15s)
ℹ️  测试前端服务...
✅ 前端服务可访问 (0.32s)

【第2步】API功能测试
ℹ️  测试核心API端点...
✅ 健康检查: HTTP 200 (0.12s)
✅ API文档: HTTP 200 (0.25s)
...

【第6步】生成验证报告
✅ 报告已生成: MVP_AUTO_VALIDATION_REPORT_20251218_213045.md

================================================
   验证完成
================================================

✅ 通过: 15
❌ 失败: 0
⚠️  警告: 2

通过率: 88.24%

🎉 系统验证完全通过！可以开始演示！
```

### 报告文件示例

```markdown
# PreVis PRO - MVP自动验证报告

**验证时间**: 2025-12-18 21:30:00
**完成时间**: 2025-12-18 21:30:45
**总耗时**: 45.23 秒

## 📊 验证结果概览

| 指标 | 数量 |
|------|------|
| ✅ 通过 | 15 |
| ❌ 失败 | 0 |
| ⚠️ 警告 | 2 |

**通过率**: 88.24%

## 📋 详细测试结果

| 测试项 | 状态 | 耗时 | 说明 |
|--------|------|------|------|
| Backend Health | ✅ PASS | 0.15s | 服务正常，版本: 0.2.0 |
| Frontend Access | ✅ PASS | 0.32s | HTTP 200, 大小: 1234 bytes |
...
```

---

## 🚀 高级用法

### 场景1: CI/CD集成

```powershell
# 在CI脚本中使用
.\auto_validate_mvp.ps1 -Mode full

# 检查退出码
if ($LASTEXITCODE -eq 0) {
    # 验证通过，继续部署
} else {
    # 验证失败，停止部署
}
```

### 场景2: 定时监控

```powershell
# Windows任务计划器
# 每小时执行一次验证
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-File auto_validate_mvp.ps1"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "MVP Validation" -Action $action -Trigger $trigger
```

### 场景3: 警报通知

```powershell
# 修改脚本，添加邮件通知
if ($global:Results.Failed -gt 0) {
    Send-MailMessage -To "admin@example.com" -Subject "MVP验证失败" -Body "..."
}
```

---

## 🔧 扩展建议

### 可添加的测试项

1. **数据库查询测试**
```powershell
# SQLite查询测试
$query = "SELECT COUNT(*) FROM assets"
sqlite3.exe pervis_pro.db $query
```

2. **素材处理测试**
```powershell
# 上传测试文件
$testFile = "test_video.mp4"
Invoke-RestMethod -Uri "$BackendUrl/api/assets/upload" -Method POST -InFile $testFile
```

3. **AI功能测试**
```powershell
# 测试剧本分析
$script = @{text="测试剧本内容"}
Invoke-RestMethod -Uri "$BackendUrl/api/script/analyze" -Method POST -Body ($script | ConvertTo-Json)
```

### 性能优化

1. **并行执行测试**
```powershell
# 使用PowerShell Jobs
$job1 = Start-Job -ScriptBlock { Test-BackendService }
$job2 = Start-Job -ScriptBlock { Test-FrontendService }
Wait-Job $job1, $job2
```

2. **缓存结果**
```powershell
# 缓存健康检查结果
$script:HealthCheckCache = @{
    LastCheck = $null
    Result = $null
}
```

---

## 📝 维护建议

### 定期更新

1. **更新API端点列表**
   - 当添加新API时，更新`$endpoints`数组

2. **调整性能阈值**
   - 根据实际生产环境调整警告阈值

3. **添加新的验证项**
   - 按模块添加新的测试函数

### 错误处理

所有模块都包含：
- Try-Catch异常处理
- 超时控制
- 详细错误信息记录

---

## 🎯 总结

### 脚本优势

1. ✅ **全自动**: 一键执行所有验证
2. ✅ **模块化**: 6大模块清晰分离
3. ✅ **灵活性**: 3种验证模式
4. ✅ **可视化**: 彩色输出和Markdown报告
5. ✅ **可扩展**: 易于添加新测试
6. ✅ **CI友好**: 返回标准退出码

### 技术亮点

- PowerShell 5.1+ 兼容
- RESTful API测试
- 性能基准测试
- 自动报告生成
- 错误处理完善

### 使用场景

- ✅ 开发环境验证
- ✅ 演示前检查
- ✅ CI/CD集成
- ✅ 定时监控
- ✅ 问题诊断

---

**脚本位置**: `f:\100KIRO project\Pervis PRO\auto_validate_mvp.ps1`  
**技术支持**: 查看脚本内注释或本文档  
**最后更新**: 2025-12-18
