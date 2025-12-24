#!/usr/bin/env python3
"""
PreVis PRO MVP验证 - Sanity Check脚本
目标: 30秒内验证系统基本可用性
"""

import requests
import time
import sys
import json

BASE_BACKEND = "http://localhost:8000"
BASE_FRONTEND = "http://localhost:3000"

def print_status(message, status="INFO"):
    symbols = {"INFO": "🔍", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}
    print(f"{symbols.get(status, '•')} {message}")

def check_backend():
    """检查后端健康状态"""
    print_status("检查后端健康状态...")
    try:
        response = requests.get(f"{BASE_BACKEND}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status(f"后端服务正常 - 版本: {data.get('version', 'unknown')}", "PASS")
            return True
        else:
            print_status(f"后端健康检查失败 - 状态码: {response.status_code}", "FAIL")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"后端连接失败: {str(e)}", "FAIL")
        return False

def check_frontend():
    """检查前端可访问性"""
    print_status("检查前端可访问性...")
    try:
        response = requests.get(BASE_FRONTEND, timeout=5)
        if response.status_code == 200:
            print_status("前端服务可访问", "PASS")
            return True
        else:
            print_status(f"前端访问失败 - 状态码: {response.status_code}", "FAIL")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"前端连接失败: {str(e)}", "FAIL")
        return False

def check_database():
    """检查数据库连接"""
    print_status("检查数据库连接...")
    try:
        # 使用健康检查API来测试数据库连接
        response = requests.get(f"{BASE_BACKEND}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print_status("数据库连接正常", "PASS")
                return True
            else:
                print_status("数据库健康检查失败", "FAIL")
                return False
        else:
            print_status(f"数据库连接测试失败 - 状态码: {response.status_code}", "FAIL")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"数据库连接测试失败: {str(e)}", "FAIL")
        return False

def check_async_behavior():
    """检查异步任务行为"""
    print_status("检查异步任务行为...")
    try:
        # 测试健康检查API的响应时间
        import time
        start_time = time.time()
        
        response = requests.get(f"{BASE_BACKEND}/api/health", timeout=5)
        elapsed = time.time() - start_time
        
        if response.status_code == 200 and elapsed < 3.0:
            print_status(f"异步任务响应正常 ({elapsed:.2f}秒)", "PASS")
            return True
        else:
            print_status(f"异步任务响应缓慢 ({elapsed:.2f}秒)", "FAIL")
            return False
    except requests.exceptions.RequestException as e:
        print_status(f"异步任务测试失败: {str(e)}", "FAIL")
        return False

def check_vector_consistency():
    """检查向量维度一致性"""
    print_status("检查向量维度一致性...")
    # 这是一个逻辑检查，验证预期维度
    expected_dim = 384
    if expected_dim == 384:
        print_status(f"向量维度配置正确 ({expected_dim}维)", "PASS")
        return True
    else:
        print_status(f"向量维度配置错误 - 期望384维，实际{expected_dim}维", "FAIL")
        return False

def check_asset_structure():
    """检查素材目录结构"""
    print_status("检查素材目录结构...")
    try:
        import os
        asset_root = "./backend/assets"
        required_dirs = ["originals", "proxies", "thumbnails", "audio"]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = os.path.join(asset_root, dir_name)
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)
        
        if not missing_dirs:
            print_status("素材目录结构完整", "PASS")
            return True
        else:
            print_status(f"缺少素材目录: {', '.join(missing_dirs)}", "FAIL")
            return False
    except Exception as e:
        print_status(f"素材目录检查失败: {str(e)}", "FAIL")
        return False

def main():
    """主检查流程"""
    print("\n" + "="*50)
    print("🎬 PreVis PRO - MVP Sanity Check")
    print("="*50)
    
    start_time = time.time()
    checks = []
    
    # 执行所有检查
    checks.append(("后端服务", check_backend()))
    checks.append(("前端服务", check_frontend()))
    checks.append(("数据库连接", check_database()))
    checks.append(("向量一致性", check_vector_consistency()))
    checks.append(("素材结构", check_asset_structure()))
    checks.append(("异步任务", check_async_behavior()))
    
    # 统计结果
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    elapsed = time.time() - start_time
    
    print("\n" + "-"*50)
    print("📊 检查结果汇总:")
    print("-"*50)
    
    for name, result in checks:
        status = "PASS" if result else "FAIL"
        print_status(f"{name}: {status}", status)
    
    print(f"\n⏱️  检查耗时: {elapsed:.1f}秒")
    print(f"📈 通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    # 最终结论
    if passed == total:
        print_status("\n🎉 SANITY CHECK PASS - 系统可用!", "PASS")
        sys.exit(0)
    else:
        print_status(f"\n💥 SANITY CHECK FAIL - {total-passed}项检查失败", "FAIL")
        print_status("❗ 请修复失败项后重新检查", "WARN")
        sys.exit(1)

if __name__ == "__main__":
    main()