# PreVis PRO - MVP Auto Validation Report

**Validation Time**: 2025-12-18 21:58:02
**Completion Time**: 2025-12-18 21:58:07
**Total Duration**: 4.64 seconds
**Validation Mode**: full

---

## Validation Results Overview

| Metric | Count |
|--------|-------|
| PASS | 5 |
| FAIL | 4 |
| WARN | 2 |
| **Total** | 11 |

**Pass Rate**: 45.45%

---

## Detailed Test Results

| Test | Status | Duration | Details |
|------|--------|----------|---------|
| Backend Health | [PASS] | 2.06s | Service healthy, version: 0.2.0 |
| Frontend Access | [WARN] | 2.05s | Not responding or not started |
| API: Health Check | [PASS] | 0.01s | HTTP 200 |
| API: API Docs | [PASS] | 0.01s | HTTP 200 |
| API: Script List | [FAIL] | 0s | Request failed: {"detail":"Not Found"} |
| API: Asset List | [FAIL] | - | Request failed: {"detail":"Not Found"} |
| API: Search Endpoint | [FAIL] | 0s | Request failed: {"detail":"Not Found"} |
| Database File | [WARN] | - | File not found |
| Asset Directory | [PASS] | - | Path: ./assets, Files: 0 |
| API Performance | [PASS] | 0s | Avg: 0.81ms, Min: 0ms, Max: 1.59ms |
| Sanity Check | [FAIL] | 0.46s | 
==================================================
python.exe : Traceback (most recent call last):
所在位置 F:\100KIRO project\Pervis PRO\auto_validat
e_mvp.ps1:225 字符: 23
+             $output = & $systemPython sanity_
check.py 2>&1 | Out-Stri ...
+                       ~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (T 
   raceback (most recent call last)::String)   
  [], RemoteException
    + FullyQualifiedErrorId : NativeCommandErr 
   or
 
  File "F:\100KIRO project\Pervis PRO\sanity_ch
eck.py", line 171, in <module>
    main()
    ~~~~^^
  File "F:\100KIRO project\Pervis PRO\sanity_ch
eck.py", line 131, in main
    print("\U0001f3ac PreVis PRO - MVP Sanity C
heck")
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'gbk' codec can't encode ch
aracter '\U0001f3ac' in position 0: illegal mul
tibyte sequence
 |

---

## System Status Summary

### Service Status
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Recommendations
- [FAIL] Found 4 failed items, need fixes
- [WARN] Found 2 warning items, suggest review

---

**Report Generated**: 2025-12-18 21:58:07

