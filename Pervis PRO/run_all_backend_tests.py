# -*- coding: utf-8 -*-
"""
Pervis PRO 后端完整测试运行器

运行所有后端测试:
1. 属性测试 (Property-Based Testing)
2. 集成测试 (Integration Testing)
3. 功能验证测试

使用方法:
    py run_all_backend_tests.py
    py run_all_backend_tests.py --quick  # 快速测试模式
    py run_all_backend_tests.py --verbose  # 详细输出
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
from typing import List, Tuple

# 测试文件列表
TEST_FILES = [
    # 属性测试
    ("backend/tests/test_ai_api_properties.py", "AI API 属性测试"),
    ("backend/tests/test_llm_provider_properties.py", "LLM Provider 属性测试"),
    ("backend/tests/test_export_system_properties.py", "导出系统属性测试"),
    
    # 集成测试
    ("backend/tests/test_asset_tagging_integration.py", "素材标签集成测试"),
    ("backend/tests/test_backend_integration.py", "后端完整集成测试"),
    
    # 功能验证
    ("test_wizard_backend_validation.py", "项目向导后端验证"),
]


def run_test_file(test_file: str, verbose: bool = False) -> Tuple[bool, str, float]:
    """
    运行单个测试文件
    
    Returns:
        (success, output, duration)
    """
    start_time = time.time()
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v" if verbose else "-q",
        "--tb=short",
        "-x",  # 遇到第一个失败就停止
        "--asyncio-mode=auto"
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=300  # 5 分钟超时
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        return success, output, duration
        
    except subprocess.TimeoutExpired:
        return False, "测试超时 (>5分钟)", time.time() - start_time
    except Exception as e:
        return False, f"执行错误: {e}", time.time() - start_time


def run_quick_validation() -> bool:
    """运行快速验证测试"""
    print("\n" + "="*60)
    print("快速验证测试")
    print("="*60)
    
    # 只运行功能验证脚本
    cmd = [sys.executable, "test_wizard_backend_validation.py"]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=120
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 快速验证失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Pervis PRO 后端测试运行器")
    parser.add_argument("--quick", action="store_true", help="快速测试模式")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--file", "-f", type=str, help="只运行指定测试文件")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("Pervis PRO 后端完整测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 快速模式
    if args.quick:
        success = run_quick_validation()
        sys.exit(0 if success else 1)
    
    # 确定要运行的测试
    if args.file:
        tests_to_run = [(args.file, args.file)]
    else:
        tests_to_run = TEST_FILES
    
    # 运行测试
    results = []
    total_start = time.time()
    
    for test_file, description in tests_to_run:
        print(f"\n{'─'*60}")
        print(f"📋 {description}")
        print(f"   文件: {test_file}")
        print("─"*60)
        
        # 检查文件是否存在
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_file)
        if not os.path.exists(full_path):
            print(f"   ⚠️ 文件不存在，跳过")
            results.append((test_file, description, False, "文件不存在", 0))
            continue
        
        success, output, duration = run_test_file(test_file, args.verbose)
        results.append((test_file, description, success, output, duration))
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {status} ({duration:.1f}s)")
        
        if not success and args.verbose:
            print("\n   输出:")
            for line in output.split('\n')[-20:]:  # 只显示最后 20 行
                print(f"   {line}")
    
    # 汇总结果
    total_duration = time.time() - total_start
    passed = sum(1 for r in results if r[2])
    failed = len(results) - passed
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    for test_file, description, success, output, duration in results:
        status = "✅" if success else "❌"
        print(f"  {status} {description} ({duration:.1f}s)")
    
    print("\n" + "-"*60)
    print(f"总计: {passed} 通过, {failed} 失败")
    print(f"总耗时: {total_duration:.1f}s")
    print("-"*60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！后端功能验证完成。")
    else:
        print(f"\n⚠️ 有 {failed} 项测试失败，请检查相关功能。")
    
    # 生成测试报告
    report_path = generate_test_report(results, total_duration)
    print(f"\n📄 测试报告已生成: {report_path}")
    
    sys.exit(0 if failed == 0 else 1)


def generate_test_report(results: List, total_duration: float) -> str:
    """生成测试报告"""
    report_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"BACKEND_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    
    passed = sum(1 for r in results if r[2])
    failed = len(results) - passed
    
    content = f"""# Pervis PRO 后端测试报告

## 测试概要

- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总耗时**: {total_duration:.1f}s
- **测试数量**: {len(results)}
- **通过**: {passed}
- **失败**: {failed}
- **通过率**: {passed/len(results)*100:.1f}%

## 测试结果详情

| 测试 | 状态 | 耗时 |
|------|------|------|
"""
    
    for test_file, description, success, output, duration in results:
        status = "✅ 通过" if success else "❌ 失败"
        content += f"| {description} | {status} | {duration:.1f}s |\n"
    
    content += f"""

## 测试覆盖

### 属性测试 (Property-Based Testing)
- AI API 属性测试
- LLM Provider 属性测试
- 导出系统属性测试

### 集成测试 (Integration Testing)
- 素材标签系统集成测试
- 后端完整集成测试

### 功能验证
- 项目向导后端验证

## 结论

{"✅ 所有测试通过，后端功能验证完成。" if failed == 0 else f"⚠️ 有 {failed} 项测试失败，需要进一步检查。"}
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return report_path


if __name__ == "__main__":
    main()
