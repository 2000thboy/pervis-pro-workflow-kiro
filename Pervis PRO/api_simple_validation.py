#!/usr/bin/env python3
"""
API接口功能检测脚本（简化版）
使用requests库测试PreVis PRO的REST API端点
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import time

class SimpleAPIValidator:
    """简化的API接口验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_data = {}
        
        # API端点配置
        self.endpoints = {
            "project_create": {
                "url": "/api/projects",
                "method": "POST", 
                "description": "创建项目接口",
                "test_data": {
                    "title": "API测试项目",
                    "script_raw": "EXT. 城市街道 - 夜晚\n\n一个神秘的身影在雨中奔跑。\n\nINT. 咖啡厅 - 白天\n\n主角坐在窗边，思考着昨晚发生的事情。\n\nEXT. 公园 - 黄昏\n\n两人在公园里相遇，开始了一段对话。",
                    "logline": "一个关于神秘追逐和意外相遇的故事"
                }
            },
            "project_list": {
                "url": "/api/projects",
                "method": "GET",
                "description": "获取项目列表接口"
            },
            "project_get": {
                "url": "/api/projects/{project_id}",
                "method": "GET",
                "description": "获取项目详情接口",
                "requires": ["project_create"]
            },
            "project_beats": {
                "url": "/api/projects/{project_id}/beats",
                "method": "GET", 
                "description": "获取项目Beats接口",
                "requires": ["project_create"]
            }
        }
    
    def check_server_status(self) -> Dict:
        """检查服务器状态"""
        print("🔍 检查服务器状态...")
        
        result = {
            "server_running": False,
            "response_time": None,
            "error": None,
            "status_code": None
        }
        
        try:
            # 尝试访问项目列表端点
            url = f"{self.base_url}/api/projects"
            
            start_time = time.time()
            response = requests.get(url, timeout=10)
            result["response_time"] = round((time.time() - start_time) * 1000, 2)
            result["status_code"] = response.status_code
            
            if response.status_code < 500:  # 接受4xx和2xx状态码
                result["server_running"] = True
                print(f"   ✅ 服务器响应正常")
                print(f"   📊 响应时间: {result['response_time']} ms")
                print(f"   📊 状态码: {result['status_code']}")
            else:
                result["error"] = f"服务器错误: {response.status_code}"
                print(f"   ❌ 服务器错误: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            result["error"] = "连接被拒绝，服务器可能未启动"
            print(f"   ❌ 连接被拒绝，服务器可能未启动")
        except requests.exceptions.Timeout:
            result["error"] = "请求超时"
            print(f"   ❌ 请求超时")
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ 服务器检查失败: {e}")
        
        return result
    
    def test_endpoint(self, endpoint_name: str, endpoint_config: Dict) -> Dict:
        """测试单个API端点"""
        print(f"\n🔍 测试接口: {endpoint_name}")
        print(f"   描述: {endpoint_config['description']}")
        print(f"   方法: {endpoint_config['method']}")
        
        result = {
            "endpoint": endpoint_name,
            "url": endpoint_config["url"],
            "method": endpoint_config["method"],
            "success": False,
            "status_code": None,
            "response_time": None,
            "response_data": None,
            "error": None,
            "validation_errors": []
        }
        
        try:
            # 检查依赖
            if "requires" in endpoint_config:
                for required_endpoint in endpoint_config["requires"]:
                    if required_endpoint not in self.test_data:
                        result["error"] = f"依赖的端点 {required_endpoint} 未成功执行"
                        print(f"   ❌ 依赖检查失败: {result['error']}")
                        return result
            
            # 构建URL
            url = endpoint_config["url"]
            if "{project_id}" in url and "project_create" in self.test_data:
                project_id = self.test_data["project_create"].get("project_id")
                if project_id:
                    url = url.replace("{project_id}", project_id)
                else:
                    result["error"] = "缺少project_id参数"
                    print(f"   ❌ URL构建失败: {result['error']}")
                    return result
            
            full_url = f"{self.base_url}{url}"
            print(f"   🌐 请求URL: {full_url}")
            
            # 发送请求
            start_time = time.time()
            
            if endpoint_config["method"] == "POST":
                request_data = endpoint_config.get("test_data")
                response = requests.post(
                    full_url, 
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
            elif endpoint_config["method"] == "GET":
                response = requests.get(full_url, timeout=30)
            else:
                result["error"] = f"不支持的HTTP方法: {endpoint_config['method']}"
                print(f"   ❌ {result['error']}")
                return result
            
            result["status_code"] = response.status_code
            result["response_time"] = round((time.time() - start_time) * 1000, 2)
            
            # 解析响应数据
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text
            
            # 判断成功状态
            if 200 <= result["status_code"] < 300:
                result["success"] = True
                print(f"   ✅ 请求成功")
                print(f"   📊 状态码: {result['status_code']}")
                print(f"   📊 响应时间: {result['response_time']} ms")
                
                # 验证响应数据
                validation_result = self._validate_response(endpoint_name, result["response_data"])
                result["validation_errors"] = validation_result
                
                if not validation_result:
                    print(f"   ✅ 响应数据验证通过")
                else:
                    print(f"   ⚠️  响应数据验证警告: {len(validation_result)} 个问题")
                    for error in validation_result:
                        print(f"      - {error}")
                
                # 保存测试数据供后续使用
                if endpoint_name == "project_create" and isinstance(result["response_data"], dict):
                    self.test_data[endpoint_name] = {
                        "project_id": result["response_data"].get("id"),
                        "response": result["response_data"]
                    }
                    print(f"   💾 保存项目ID: {self.test_data[endpoint_name]['project_id']}")
                
                # 显示部分响应数据
                if isinstance(result["response_data"], dict):
                    if endpoint_name == "project_create":
                        print(f"   📋 项目标题: {result['response_data'].get('title', 'N/A')}")
                        print(f"   📋 Beats数量: {result['response_data'].get('beats_count', 'N/A')}")
                    elif endpoint_name == "project_list":
                        if isinstance(result["response_data"], list):
                            print(f"   📋 项目数量: {len(result['response_data'])}")
                    elif endpoint_name == "project_beats":
                        beats = result["response_data"].get("beats", [])
                        print(f"   📋 Beat数量: {len(beats)}")
                
            else:
                result["success"] = False
                print(f"   ❌ 请求失败")
                print(f"   📊 状态码: {result['status_code']}")
                print(f"   📊 响应时间: {result['response_time']} ms")
                
                if isinstance(result["response_data"], dict):
                    error_detail = result["response_data"].get("detail", "未知错误")
                    print(f"   📋 错误详情: {error_detail}")
                elif isinstance(result["response_data"], str):
                    print(f"   📋 响应内容: {result['response_data'][:200]}...")
                
        except requests.exceptions.ConnectionError:
            result["error"] = "连接被拒绝"
            print(f"   ❌ 连接被拒绝")
        except requests.exceptions.Timeout:
            result["error"] = "请求超时"
            print(f"   ❌ 请求超时")
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ 测试失败: {e}")
        
        return result
    
    def _validate_response(self, endpoint_name: str, response_data: Any) -> List[str]:
        """验证响应数据格式"""
        errors = []
        
        if endpoint_name == "project_create":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            required_fields = ["id", "title", "script_raw", "logline", "created_at"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
            
            if "beats_count" in response_data:
                if not isinstance(response_data["beats_count"], int):
                    errors.append("beats_count应该是整数")
                elif response_data["beats_count"] < 0:
                    errors.append("beats_count不应该是负数")
        
        elif endpoint_name == "project_get":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            required_fields = ["id", "title", "script_raw", "logline"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
        
        elif endpoint_name == "project_beats":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            if "project_id" not in response_data:
                errors.append("缺少project_id字段")
            
            if "beats" not in response_data:
                errors.append("缺少beats字段")
            elif not isinstance(response_data["beats"], list):
                errors.append("beats应该是数组")
            else:
                # 验证beats数组中的对象
                for i, beat in enumerate(response_data["beats"]):
                    if not isinstance(beat, dict):
                        errors.append(f"beats[{i}]不是对象")
                        continue
                    
                    beat_required = ["id", "content", "order_index"]
                    for field in beat_required:
                        if field not in beat:
                            errors.append(f"beats[{i}]缺少字段: {field}")
        
        elif endpoint_name == "project_list":
            if not isinstance(response_data, list):
                errors.append("项目列表应该是数组")
            else:
                for i, project in enumerate(response_data):
                    if not isinstance(project, dict):
                        errors.append(f"项目[{i}]不是对象")
                        continue
                    
                    required_fields = ["id", "title"]
                    for field in required_fields:
                        if field not in project:
                            errors.append(f"项目[{i}]缺少字段: {field}")
        
        return errors
    
    def test_error_handling(self) -> Dict:
        """测试错误处理"""
        print(f"\n🔍 测试错误处理...")
        
        results = {
            "invalid_project_id": None,
            "missing_fields": None
        }
        
        # 测试无效的项目ID
        try:
            invalid_id = "invalid-project-id-12345"
            url = f"{self.base_url}/api/projects/{invalid_id}"
            
            response = requests.get(url, timeout=10)
            results["invalid_project_id"] = {
                "status_code": response.status_code,
                "expected": 404,
                "success": response.status_code == 404
            }
            
            if results["invalid_project_id"]["success"]:
                print(f"   ✅ 无效项目ID处理正确 (404)")
            else:
                print(f"   ❌ 无效项目ID处理异常 ({response.status_code})")
        
        except Exception as e:
            results["invalid_project_id"] = {"error": str(e), "success": False}
            print(f"   ❌ 无效项目ID测试失败: {e}")
        
        # 测试缺少必需字段
        try:
            url = f"{self.base_url}/api/projects"
            incomplete_data = {"title": "测试项目"}  # 缺少script_raw和logline
            
            response = requests.post(
                url, 
                json=incomplete_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            results["missing_fields"] = {
                "status_code": response.status_code,
                "expected": 422,  # FastAPI的验证错误
                "success": response.status_code == 422
            }
            
            if results["missing_fields"]["success"]:
                print(f"   ✅ 缺少字段处理正确 (422)")
            else:
                print(f"   ❌ 缺少字段处理异常 ({response.status_code})")
                # 显示响应内容以便调试
                try:
                    error_data = response.json()
                    print(f"   📋 错误响应: {error_data}")
                except:
                    print(f"   📋 响应文本: {response.text[:200]}")
        
        except Exception as e:
            results["missing_fields"] = {"error": str(e), "success": False}
            print(f"   ❌ 缺少字段测试失败: {e}")
        
        return results
    
    def cleanup_test_data(self) -> Dict:
        """清理测试数据"""
        print(f"\n🧹 清理测试数据...")
        
        results = {
            "cleanup_attempted": False,
            "cleanup_success": False,
            "error": None
        }
        
        if "project_create" in self.test_data:
            project_id = self.test_data["project_create"].get("project_id")
            if project_id:
                try:
                    url = f"{self.base_url}/api/projects/{project_id}"
                    response = requests.delete(url, timeout=10)
                    
                    results["cleanup_attempted"] = True
                    
                    if 200 <= response.status_code < 300:
                        results["cleanup_success"] = True
                        print(f"   ✅ 测试项目删除成功")
                    else:
                        results["error"] = f"删除失败: {response.status_code}"
                        print(f"   ⚠️  测试项目删除失败: {response.status_code}")
                
                except Exception as e:
                    results["error"] = str(e)
                    print(f"   ⚠️  测试项目删除异常: {e}")
        
        return results
    
    def run_full_validation(self) -> Dict:
        """运行完整的API验证"""
        print("=" * 60)
        print("🌐 PreVis PRO - API接口功能检测")
        print("=" * 60)
        print(f"📍 服务器地址: {self.base_url}")
        print()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "server_status": None,
            "endpoint_tests": {},
            "error_handling": None,
            "cleanup": None,
            "summary": {
                "total_endpoints": len(self.endpoints),
                "successful_endpoints": 0,
                "failed_endpoints": 0,
                "server_running": False
            }
        }
        
        try:
            # 1. 检查服务器状态
            server_status = self.check_server_status()
            report["server_status"] = server_status
            report["summary"]["server_running"] = server_status["server_running"]
            
            if not server_status["server_running"]:
                print(f"\n❌ 服务器未运行，无法进行API测试")
                print(f"💡 请确保后端服务已启动:")
                print(f"   cd backend && python main.py")
                print(f"   或者: cd backend && uvicorn main:app --reload")
                return report
            
            # 2. 测试各个API端点
            for endpoint_name, endpoint_config in self.endpoints.items():
                result = self.test_endpoint(endpoint_name, endpoint_config)
                report["endpoint_tests"][endpoint_name] = result
                
                if result["success"]:
                    report["summary"]["successful_endpoints"] += 1
                else:
                    report["summary"]["failed_endpoints"] += 1
            
            # 3. 测试错误处理
            error_handling = self.test_error_handling()
            report["error_handling"] = error_handling
            
            # 4. 清理测试数据
            cleanup = self.cleanup_test_data()
            report["cleanup"] = cleanup
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            report["error"] = str(e)
        
        return report

def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("\n" + "=" * 60)
    print("📋 API接口检测报告摘要")
    print("=" * 60)
    
    if "error" in report:
        print(f"❌ 检测失败: {report['error']}")
        return
    
    summary = report["summary"]
    
    # 服务器状态
    if summary["server_running"]:
        print(f"🎯 服务器状态: ✅ 运行中")
        if "server_status" in report and "response_time" in report["server_status"]:
            print(f"📊 服务器响应时间: {report['server_status']['response_time']} ms")
    else:
        print(f"🎯 服务器状态: ❌ 未运行")
        if "server_status" in report and "error" in report["server_status"]:
            print(f"📋 错误信息: {report['server_status']['error']}")
        return
    
    # API端点测试结果
    print(f"🌐 API端点测试: {summary['successful_endpoints']}/{summary['total_endpoints']} 个成功")
    
    if report.get("endpoint_tests"):
        for endpoint_name, result in report["endpoint_tests"].items():
            status = "✅" if result["success"] else "❌"
            response_time = f" ({result.get('response_time', 'N/A')} ms)" if result.get("response_time") else ""
            print(f"   {status} {endpoint_name}: {result.get('status_code', 'N/A')}{response_time}")
            
            if result.get("validation_errors"):
                print(f"      ⚠️  验证警告: {len(result['validation_errors'])} 个")
    
    # 错误处理测试
    if report.get("error_handling"):
        error_tests = report["error_handling"]
        successful_error_tests = sum(1 for test in error_tests.values() 
                                   if isinstance(test, dict) and test.get("success", False))
        total_error_tests = len([test for test in error_tests.values() if test is not None])
        
        print(f"🚨 错误处理测试: {successful_error_tests}/{total_error_tests} 个通过")
        
        for test_name, test_result in error_tests.items():
            if isinstance(test_result, dict):
                status = "✅" if test_result.get("success", False) else "❌"
                expected = test_result.get("expected", "N/A")
                actual = test_result.get("status_code", "N/A")
                print(f"   {status} {test_name}: 期望{expected}, 实际{actual}")
    
    # 清理结果
    if report.get("cleanup"):
        cleanup = report["cleanup"]
        if cleanup.get("cleanup_attempted"):
            status = "✅" if cleanup.get("cleanup_success") else "⚠️ "
            print(f"🧹 数据清理: {status}")
    
    # 整体状态
    if summary["failed_endpoints"] == 0:
        print(f"\n🎯 整体状态: ✅ 所有API正常")
    elif summary["successful_endpoints"] > summary["failed_endpoints"]:
        print(f"\n🎯 整体状态: ⚠️  部分API异常")
    else:
        print(f"\n🎯 整体状态: ❌ 多数API异常")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO API接口功能检测工具')
    parser.add_argument('--url', default='http://localhost:8000', help='API服务器地址')
    parser.add_argument('--output', help='输出报告到JSON文件')
    
    args = parser.parse_args()
    
    # 创建验证器并运行
    validator = SimpleAPIValidator(args.url)
    report = validator.run_full_validation()
    
    # 打印摘要
    print_report_summary(report)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细报告已保存到: {args.output}")
    
    # 返回状态码
    if "error" in report:
        return 1
    
    summary = report["summary"]
    if not summary["server_running"]:
        return 1
    elif summary["failed_endpoints"] > 0:
        return 2
    else:
        return 0

if __name__ == "__main__":
    exit(main())