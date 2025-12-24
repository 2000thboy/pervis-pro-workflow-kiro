#!/usr/bin/env python3
"""
PreVis PRO 稳定性报告生成器
自动收集系统状态信息并生成标准化报告
"""

import json
import os
import sqlite3
import subprocess
import time
from datetime import datetime
from pathlib import Path
import requests

def get_system_info():
    """获取系统基本信息"""
    return {
        "timestamp": datetime.now().isoformat(),
        "platform": os.name,
        "python_version": subprocess.check_output(["python", "--version"]).decode().strip(),
        "working_directory": os.getcwd()
    }

def check_p0_fixes():
    """检查P0修复状态"""
    fixes = {
        "database_async": False,
        "embedding_async": False, 
        "vector_validation": False,
        "polling_unified": False,
        "asset_structure": False
    }
    
    # 检查数据库异步化
    try:
        with open("backend/services/database_service.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "async def" in content and "await" in content:
                fixes["database_async"] = True
    except:
        pass
    
    # 检查embedding异步化
    try:
        with open("backend/services/semantic_search.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "run_in_executor" in content or "async def" in content:
                fixes["embedding_async"] = True
    except:
        pass
    
    # 检查向量维度校验
    try:
        with open("backend/services/semantic_search.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "384" in content and ("len(vector)" in content or "dimension" in content):
                fixes["vector_validation"] = True
    except:
        pass
    
    # 检查轮询机制
    try:
        with open("frontend/services/apiClient.ts", "r", encoding="utf-8") as f:
            content = f.read()
            if "setTimeout" in content and "polling" in content.lower():
                fixes["polling_unified"] = True
    except:
        pass
    
    # 检查素材目录结构
    asset_dirs = ["backend/assets/originals", "backend/assets/proxies", 
                  "backend/assets/thumbnails", "backend/assets/audio"]
    fixes["asset_structure"] = all(os.path.exists(d) for d in asset_dirs)
    
    return fixes

def check_performance_metrics():
    """检查性能指标"""
    metrics = {
        "backend_response_time": None,
        "frontend_load_time": None,
        "database_size": None,
        "asset_count": None
    }
    
    # 测试后端响应时间
    try:
        start = time.time()
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            metrics["backend_response_time"] = round((time.time() - start) * 1000, 2)
    except:
        pass
    
    # 测试前端加载时间
    try:
        start = time.time()
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            metrics["frontend_load_time"] = round((time.time() - start) * 1000, 2)
    except:
        pass
    
    # 检查数据库大小
    try:
        db_path = "backend/pervis_director.db"
        if os.path.exists(db_path):
            metrics["database_size"] = round(os.path.getsize(db_path) / 1024 / 1024, 2)  # MB
    except:
        pass
    
    # 统计素材数量
    try:
        asset_dirs = {
            "originals": "backend/assets/originals",
            "proxies": "backend/assets/proxies", 
            "thumbnails": "backend/assets/thumbnails",
            "audio": "backend/assets/audio"
        }
        asset_counts = {}
        for name, path in asset_dirs.items():
            if os.path.exists(path):
                asset_counts[name] = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
        metrics["asset_count"] = asset_counts
    except:
        pass
    
    return metrics

def check_demo_readiness():
    """检查演示项目就绪状态"""
    demo_status = {
        "project_exists": False,
        "script_ready": False,
        "beats_ready": False,
        "assets_ready": False,
        "tags_ready": False
    }
    
    demo_path = "demo_projects/cyberpunk_trailer"
    
    # 检查项目文件
    demo_status["project_exists"] = os.path.exists(f"{demo_path}/project.json")
    demo_status["script_ready"] = os.path.exists(f"{demo_path}/script.txt")
    demo_status["beats_ready"] = os.path.exists(f"{demo_path}/beats.json")
    demo_status["tags_ready"] = os.path.exists(f"{demo_path}/tags.json")
    
    # 检查素材目录
    assets_path = f"{demo_path}/assets"
    if os.path.exists(assets_path):
        asset_files = [f for f in os.listdir(assets_path) if f.endswith(('.mp4', '.mov', '.avi'))]
        demo_status["assets_ready"] = len(asset_files) >= 3
    
    return demo_status

def assess_overall_status(p0_fixes, performance, demo_status):
    """评估整体状态"""
    # P0修复完成度
    p0_completion = sum(p0_fixes.values()) / len(p0_fixes)
    
    # 性能指标健康度
    perf_health = 0
    if performance["backend_response_time"] and performance["backend_response_time"] < 500:
        perf_health += 0.25
    if performance["frontend_load_time"] and performance["frontend_load_time"] < 2000:
        perf_health += 0.25
    if performance["database_size"] and performance["database_size"] > 0:
        perf_health += 0.25
    if performance["asset_count"]:
        perf_health += 0.25
    
    # 演示就绪度
    demo_readiness = sum(demo_status.values()) / len(demo_status)
    
    # 综合评分
    overall_score = (p0_completion * 0.4 + perf_health * 0.3 + demo_readiness * 0.3)
    
    if overall_score >= 0.9:
        return "PASS", "系统完全就绪，可进行生产部署和外部演示"
    elif overall_score >= 0.7:
        return "CONDITIONAL_PASS", "系统基本就绪，建议完善部分功能后演示"
    else:
        return "FAIL", "系统未就绪，需要完成关键修复后再评估"

def generate_recommendations(p0_fixes, performance, demo_status):
    """生成改进建议"""
    recommendations = []
    
    # P0修复建议
    if not p0_fixes["database_async"]:
        recommendations.append("🔴 P0: 数据库操作需要异步化处理")
    if not p0_fixes["embedding_async"]:
        recommendations.append("🔴 P0: Embedding生成需要异步化处理")
    if not p0_fixes["vector_validation"]:
        recommendations.append("🔴 P0: 需要添加向量维度校验机制")
    if not p0_fixes["polling_unified"]:
        recommendations.append("🔴 P0: 需要统一前端轮询机制")
    
    # 性能优化建议
    if performance["backend_response_time"] and performance["backend_response_time"] > 500:
        recommendations.append("🟡 性能: 后端响应时间需要优化")
    if performance["frontend_load_time"] and performance["frontend_load_time"] > 2000:
        recommendations.append("🟡 性能: 前端加载时间需要优化")
    
    # 演示准备建议
    if not demo_status["assets_ready"]:
        recommendations.append("🟢 演示: 需要准备完整的演示素材")
    if not all(demo_status.values()):
        recommendations.append("🟢 演示: 需要完善演示项目文件")
    
    return recommendations

def generate_report():
    """生成完整的稳定性报告"""
    print("🔍 正在收集系统信息...")
    
    # 收集数据
    system_info = get_system_info()
    p0_fixes = check_p0_fixes()
    performance = check_performance_metrics()
    demo_status = check_demo_readiness()
    
    # 评估状态
    overall_status, status_message = assess_overall_status(p0_fixes, performance, demo_status)
    recommendations = generate_recommendations(p0_fixes, performance, demo_status)
    
    print("📊 正在生成报告...")
    
    # 生成Markdown报告
    report_content = f"""# PreVis PRO 系统稳定性报告

**生成时间**: {system_info['timestamp']}  
**检查范围**: P0工程稳定性、性能指标、演示就绪度  
**系统环境**: {system_info['platform']} - {system_info['python_version']}

## 🎯 总体结论

**状态**: {overall_status}  
**评估**: {status_message}

---

## 📋 P0工程稳定性检查

### 并发与阻塞修复状态
- **数据库异步化**: {'✅ 已修复' if p0_fixes['database_async'] else '❌ 待修复'}
- **Embedding异步化**: {'✅ 已修复' if p0_fixes['embedding_async'] else '❌ 待修复'}
- **向量维度校验**: {'✅ 已实现' if p0_fixes['vector_validation'] else '❌ 待实现'}
- **轮询机制统一**: {'✅ 已统一' if p0_fixes['polling_unified'] else '❌ 待统一'}
- **素材目录结构**: {'✅ 完整' if p0_fixes['asset_structure'] else '❌ 不完整'}

### P0修复完成度
**进度**: {sum(p0_fixes.values())}/{len(p0_fixes)} ({sum(p0_fixes.values())/len(p0_fixes)*100:.0f}%)

---

## 📊 系统性能指标

### 响应时间
- **后端API响应**: {performance['backend_response_time'] or 'N/A'}ms
- **前端页面加载**: {performance['frontend_load_time'] or 'N/A'}ms

### 数据规模
- **数据库大小**: {performance['database_size'] or 'N/A'}MB
- **素材统计**: {json.dumps(performance['asset_count'], ensure_ascii=False, indent=2) if performance['asset_count'] else 'N/A'}

---

## 🎬 演示系统就绪度

### 演示项目状态
- **项目配置文件**: {'✅ 就绪' if demo_status['project_exists'] else '❌ 缺失'}
- **演示剧本**: {'✅ 就绪' if demo_status['script_ready'] else '❌ 缺失'}
- **Beat数据**: {'✅ 就绪' if demo_status['beats_ready'] else '❌ 缺失'}
- **标签映射**: {'✅ 就绪' if demo_status['tags_ready'] else '❌ 缺失'}
- **演示素材**: {'✅ 就绪' if demo_status['assets_ready'] else '❌ 不足'}

### 演示就绪度
**进度**: {sum(demo_status.values())}/{len(demo_status)} ({sum(demo_status.values())/len(demo_status)*100:.0f}%)

---

## 🛠️ 改进建议

"""
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            report_content += f"{i}. {rec}\n"
    else:
        report_content += "🎉 当前系统状态良好，无需特别改进。\n"
    
    report_content += f"""
---

## 🔍 风险评估

### 技术风险
- **并发处理**: {'低风险' if sum(p0_fixes.values()) >= 4 else '中等风险' if sum(p0_fixes.values()) >= 2 else '高风险'}
- **性能表现**: {'低风险' if performance['backend_response_time'] and performance['backend_response_time'] < 500 else '中等风险'}
- **数据一致性**: {'低风险' if p0_fixes['vector_validation'] else '中等风险'}

### 交付风险
- **演示准备**: {'低风险' if sum(demo_status.values()) >= 4 else '中等风险' if sum(demo_status.values()) >= 3 else '高风险'}
- **系统稳定性**: {'低风险' if overall_status == 'PASS' else '中等风险' if overall_status == 'CONDITIONAL_PASS' else '高风险'}

---

## 📈 下一步行动

### 立即执行 (P0)
"""
    
    p0_actions = [rec for rec in recommendations if "🔴 P0" in rec]
    if p0_actions:
        for action in p0_actions:
            report_content += f"- {action.replace('🔴 P0: ', '')}\n"
    else:
        report_content += "- 无P0级别紧急任务\n"
    
    report_content += """
### 短期优化 (P1)
"""
    
    p1_actions = [rec for rec in recommendations if "🟡 性能" in rec]
    if p1_actions:
        for action in p1_actions:
            report_content += f"- {action.replace('🟡 性能: ', '')}\n"
    else:
        report_content += "- 性能表现良好\n"
    
    report_content += """
### 演示准备 (P2)
"""
    
    demo_actions = [rec for rec in recommendations if "🟢 演示" in rec]
    if demo_actions:
        for action in demo_actions:
            report_content += f"- {action.replace('🟢 演示: ', '')}\n"
    else:
        report_content += "- 演示系统已就绪\n"
    
    report_content += f"""
---

## 📋 验证清单

在进行外部演示前，请确认：

- [ ] 运行 `python sanity_check.py` 显示 PASS
- [ ] 所有P0问题已修复
- [ ] 演示项目完整可用
- [ ] 系统性能满足要求
- [ ] 准备好演示话术和材料

---

**报告生成**: 自动化脚本 `generate_stability_report.py`  
**下次检查**: 建议每周生成一次稳定性报告  
**联系方式**: 如有问题请查看 `DEMO_VALIDATION_CHECKLIST.md`
"""
    
    # 保存报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"STABILITY_REPORT_{timestamp}.md"
    
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    # 更新最新报告
    with open("STABILITY_REPORT_LATEST.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"✅ 报告已生成: {report_filename}")
    print(f"📄 最新报告: STABILITY_REPORT_LATEST.md")
    
    # 输出简要结果
    print(f"\n🎯 系统状态: {overall_status}")
    print(f"📊 P0修复: {sum(p0_fixes.values())}/{len(p0_fixes)}")
    print(f"🎬 演示就绪: {sum(demo_status.values())}/{len(demo_status)}")
    
    if overall_status == "PASS":
        print("🎉 系统已就绪，可进行演示和交付！")
    else:
        print("⚠️  系统需要进一步完善，请查看报告中的改进建议。")

if __name__ == "__main__":
    generate_report()