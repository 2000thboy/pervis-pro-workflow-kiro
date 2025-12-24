# PreVis PRO - MVP Auto Validation Script
# Version: 1.0
# Purpose: Automated MVP system validation

param(
    [string]$Mode = "full",
    [switch]$GenerateReport = $true,
    [switch]$Verbose = $false
)

# Configuration
$BackendUrl = "http://localhost:8000"
$FrontendUrl = "http://localhost:3000"
$ReportPath = "MVP_AUTO_VALIDATION_REPORT_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Output functions
function Write-Success { param($msg) Write-Host "[PASS] $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }

# Results collection
$global:Results = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Details = @()
    StartTime = Get-Date
}

function Add-Result {
    param($Test, $Status, $Message, $Duration = 0)
    
    $global:Results.Details += @{
        Test = $Test
        Status = $Status
        Message = $Message
        Duration = $Duration
        Time = Get-Date
    }
    
    switch ($Status) {
        "PASS" { $global:Results.Passed++ }
        "FAIL" { $global:Results.Failed++ }
        "WARN" { $global:Results.Warnings++ }
    }
}

# ============================================
# Part 1: Service Status Check
# ============================================
function Test-BackendService {
    Write-Info "Testing backend service..."
    $start = Get-Date
    
    try {
        $response = Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 5
        $duration = ((Get-Date) - $start).TotalSeconds
        
        if ($response.status -eq "healthy") {
            Write-Success "Backend health check passed ($([math]::Round($duration, 2))s)"
            Add-Result "Backend Health" "PASS" "Service healthy, version: $($response.version)" $duration
            return $true
        } else {
            Write-Fail "Backend returned abnormal status: $($response.status)"
            Add-Result "Backend Health" "FAIL" "Abnormal status: $($response.status)" $duration
            return $false
        }
    } catch {
        $duration = ((Get-Date) - $start).TotalSeconds
        Write-Fail "Backend connection failed: $_"
        Add-Result "Backend Health" "FAIL" "Connection failed: $_" $duration
        return $false
    }
}

function Test-FrontendService {
    Write-Info "Testing frontend service..."
    $start = Get-Date
    
    try {
        $response = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 5 -UseBasicParsing
        $duration = ((Get-Date) - $start).TotalSeconds
        
        if ($response.StatusCode -eq 200) {
            Write-Success "Frontend accessible ($([math]::Round($duration, 2))s)"
            Add-Result "Frontend Access" "PASS" "HTTP $($response.StatusCode), Size: $($response.Content.Length) bytes" $duration
            return $true
        } else {
            Write-Warn "Frontend returned status code: $($response.StatusCode)"
            Add-Result "Frontend Access" "WARN" "Status code: $($response.StatusCode)" $duration
            return $false
        }
    } catch {
        $duration = ((Get-Date) - $start).TotalSeconds
        Write-Warn "Frontend service not responding: $_"
        Add-Result "Frontend Access" "WARN" "Not responding or not started" $duration
        return $false
    }
}

# ============================================
# Part 2: API Endpoint Tests
# ============================================
function Test-ApiEndpoints {
    Write-Info "Testing core API endpoints..."
    
    $endpoints = @(
        @{Path="/api/health"; Method="GET"; Name="Health Check"},
        @{Path="/docs"; Method="GET"; Name="API Docs"},
        @{Path="/api/script"; Method="GET"; Name="Script List"},
        @{Path="/api/assets"; Method="GET"; Name="Asset List"},
        @{Path="/api/search"; Method="GET"; Name="Search Endpoint"}
    )
    
    foreach ($ep in $endpoints) {
        $start = Get-Date
        try {
            $response = Invoke-WebRequest -Uri "$BackendUrl$($ep.Path)" -Method $ep.Method -TimeoutSec 3 -UseBasicParsing
            $duration = ((Get-Date) - $start).TotalSeconds
            
            if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 404) {
                Write-Success "$($ep.Name): HTTP $($response.StatusCode) ($([math]::Round($duration, 2))s)"
                Add-Result "API: $($ep.Name)" "PASS" "HTTP $($response.StatusCode)" $duration
            } else {
                Write-Warn "$($ep.Name): HTTP $($response.StatusCode)"
                Add-Result "API: $($ep.Name)" "WARN" "HTTP $($response.StatusCode)" $duration
            }
        } catch {
            $duration = ((Get-Date) - $start).TotalSeconds
            Write-Fail "$($ep.Name): Request failed"
            Add-Result "API: $($ep.Name)" "FAIL" "Request failed: $_" $duration
        }
    }
}

# ============================================
# Part 3: Database and File System Check
# ============================================
function Test-Database {
    Write-Info "Testing database..."
    
    if (Test-Path "backend\pervis_pro.db") {
        $dbSize = (Get-Item "backend\pervis_pro.db").Length / 1KB
        Write-Success "Database file exists ($([math]::Round($dbSize, 2)) KB)"
        Add-Result "Database File" "PASS" "Size: $([math]::Round($dbSize, 2)) KB" 0
        return $true
    } else {
        Write-Warn "Database file not found (may be first run)"
        Add-Result "Database File" "WARN" "File not found" 0
        return $false
    }
}

function Test-AssetDirectory {
    Write-Info "Testing asset directory..."
    
    $assetDirs = @("./assets", "L:\PreVis_Assets")
    $found = $false
    
    foreach ($dir in $assetDirs) {
        if (Test-Path $dir) {
            $count = (Get-ChildItem $dir -File -ErrorAction SilentlyContinue | Measure-Object).Count
            Write-Success "Asset directory exists: $dir (Files: $count)"
            Add-Result "Asset Directory" "PASS" "Path: $dir, Files: $count" 0
            $found = $true
            break
        }
    }
    
    if (-not $found) {
        Write-Warn "No asset directory found"
        Add-Result "Asset Directory" "WARN" "No standard asset directory found" 0
    }
    
    return $found
}

# ============================================
# Part 4: Performance Test
# ============================================
function Test-ApiPerformance {
    Write-Info "Testing API performance (10 requests)..."
    
    $times = @()
    for ($i = 1; $i -le 10; $i++) {
        $start = Get-Date
        try {
            Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 3 | Out-Null
            $duration = ((Get-Date) - $start).TotalMilliseconds
            $times += $duration
        } catch {
            Write-Warn "Request $i failed"
        }
    }
    
    if ($times.Count -gt 0) {
        $avg = ($times | Measure-Object -Average).Average
        $min = ($times | Measure-Object -Minimum).Minimum
        $max = ($times | Measure-Object -Maximum).Maximum
        
        Write-Success "Average response time: $([math]::Round($avg, 2))ms (Min: $([math]::Round($min, 2))ms, Max: $([math]::Round($max, 2))ms)"
        Add-Result "API Performance" "PASS" "Avg: $([math]::Round($avg, 2))ms, Min: $([math]::Round($min, 2))ms, Max: $([math]::Round($max, 2))ms" ($avg/1000)
        
        if ($avg -gt 500) {
            Write-Warn "Response time is slow (>500ms)"
        }
    } else {
        Write-Fail "Performance test failed, all requests failed"
        Add-Result "API Performance" "FAIL" "All requests failed" 0
    }
}

# ============================================
# Part 5: Run Sanity Check
# ============================================
function Run-SanityCheck {
    Write-Info "Running Sanity Check..."
    $start = Get-Date
    
    try {
        $systemPython = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
        
        if (Test-Path "sanity_check.py") {
            $output = & $systemPython sanity_check.py 2>&1 | Out-String
            $duration = ((Get-Date) - $start).TotalSeconds
            
            if ($LASTEXITCODE -eq 0 -or $output -match "PASS") {
                Write-Success "Sanity Check passed ($([math]::Round($duration, 2))s)"
                Add-Result "Sanity Check" "PASS" "Full validation passed" $duration
                
                if ($Verbose) {
                    Write-Host $output
                }
            } else {
                Write-Fail "Sanity Check failed"
                Add-Result "Sanity Check" "FAIL" $output $duration
            }
        } else {
            Write-Warn "sanity_check.py file not found"
            Add-Result "Sanity Check" "WARN" "Script file not found" 0
        }
    } catch {
        $duration = ((Get-Date) - $start).TotalSeconds
        Write-Fail "Sanity Check execution failed: $_"
        Add-Result "Sanity Check" "FAIL" "Execution error: $_" $duration
    }
}

# ============================================
# Part 6: Generate Report
# ============================================
function Generate-Report {
    $endTime = Get-Date
    $totalDuration = ($endTime - $global:Results.StartTime).TotalSeconds
    
    $report = "# PreVis PRO - MVP Auto Validation Report`n`n"
    $report += "**Validation Time**: $($global:Results.StartTime.ToString('yyyy-MM-dd HH:mm:ss'))`n"
    $report += "**Completion Time**: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))`n"
    $report += "**Total Duration**: $([math]::Round($totalDuration, 2)) seconds`n"
    $report += "**Validation Mode**: $Mode`n`n"
    $report += "---`n`n"
    $report += "## Validation Results Overview`n`n"
    $report += "| Metric | Count |`n"
    $report += "|--------|-------|`n"
    $report += "| PASS | $($global:Results.Passed) |`n"
    $report += "| FAIL | $($global:Results.Failed) |`n"
    $report += "| WARN | $($global:Results.Warnings) |`n"
    $report += "| **Total** | $($global:Results.Passed + $global:Results.Failed + $global:Results.Warnings) |`n`n"
    
    $passRate = [math]::Round(($global:Results.Passed / ($global:Results.Passed + $global:Results.Failed + $global:Results.Warnings)) * 100, 2)
    $report += "**Pass Rate**: $passRate%`n`n"
    $report += "---`n`n"
    $report += "## Detailed Test Results`n`n"
    $report += "| Test | Status | Duration | Details |`n"
    $report += "|------|--------|----------|---------|`n"

    foreach ($detail in $global:Results.Details) {
        $statusIcon = switch ($detail.Status) {
            "PASS" { "[PASS]" }
            "FAIL" { "[FAIL]" }
            "WARN" { "[WARN]" }
        }
        
        $durationStr = if ($detail.Duration -gt 0) { "$([math]::Round($detail.Duration, 2))s" } else { "-" }
        $report += "| $($detail.Test) | $statusIcon | $durationStr | $($detail.Message) |`n"
    }
    
    $report += "`n---`n`n## System Status Summary`n`n"
    $report += "### Service Status`n"
    $report += "- Backend: $BackendUrl`n"
    $report += "- Frontend: $FrontendUrl`n`n"
    $report += "### Recommendations`n"
    
    if ($global:Results.Failed -gt 0) {
        $report += "- [FAIL] Found $($global:Results.Failed) failed items, need fixes`n"
    }
    
    if ($global:Results.Warnings -gt 0) {
        $report += "- [WARN] Found $($global:Results.Warnings) warning items, suggest review`n"
    }
    
    if ($global:Results.Failed -eq 0 -and $global:Results.Warnings -eq 0) {
        $report += "- [PASS] System fully operational, ready for demo!`n"
    }
    
    $report += "`n---`n`n**Report Generated**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    
    # Save report
    $report | Out-File -FilePath $ReportPath -Encoding UTF8
    Write-Success "Report generated: $ReportPath"
}

# ============================================
# Main Execution
# ============================================
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   PreVis PRO - MVP Auto Validation" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

Write-Info "Validation Mode: $Mode"
Write-Info "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"

# Execute tests
switch ($Mode) {
    "quick" {
        Write-Info "Quick mode: Service status only"
        Test-BackendService
        Test-FrontendService
    }
    "api-only" {
        Write-Info "API test mode"
        Test-BackendService
        Test-ApiEndpoints
        Test-ApiPerformance
    }
    default {
        Write-Info "Full validation mode"
        
        Write-Host "`n[Step 1] Service Status Check" -ForegroundColor Yellow
        $backendOk = Test-BackendService
        $frontendOk = Test-FrontendService
        
        if ($backendOk) {
            Write-Host "`n[Step 2] API Function Tests" -ForegroundColor Yellow
            Test-ApiEndpoints
        }
        
        Write-Host "`n[Step 3] File System Check" -ForegroundColor Yellow
        Test-Database
        Test-AssetDirectory
        
        if ($backendOk) {
            Write-Host "`n[Step 4] Performance Tests" -ForegroundColor Yellow
            Test-ApiPerformance
        }
        
        Write-Host "`n[Step 5] Full System Validation" -ForegroundColor Yellow
        Run-SanityCheck
    }
}

# Generate report
if ($GenerateReport) {
    Write-Host "`n[Step 6] Generate Validation Report" -ForegroundColor Yellow
    Generate-Report
}

# Display summary
Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "   Validation Complete" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

Write-Host "[PASS] Passed: $($global:Results.Passed)" -ForegroundColor Green
Write-Host "[FAIL] Failed: $($global:Results.Failed)" -ForegroundColor Red
Write-Host "[WARN] Warnings: $($global:Results.Warnings)" -ForegroundColor Yellow

$passRate = [math]::Round(($global:Results.Passed / ($global:Results.Passed + $global:Results.Failed + $global:Results.Warnings)) * 100, 2)
Write-Host "`nPass Rate: $passRate%`n" -ForegroundColor $(if ($passRate -ge 90) { "Green" } elseif ($passRate -ge 70) { "Yellow" } else { "Red" })

if ($global:Results.Failed -eq 0) {
    Write-Success "System validation passed! Ready for demo!"
    exit 0
} else {
    Write-Fail "Issues found, please review report: $ReportPath"
    exit 1
}
