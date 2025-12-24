#!/usr/bin/env python3
"""
API接口功能检测脚本
测试PreVis PRO的REST API端点响应和功能
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import time

class APIValidator:
    """API接口验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.test_data = {}
        
        # API端点配置
        self.endpoints = {
            "script_analysis": {
                "url": "/api/scripts/analyze",
                "method": "POST",
                "description": "剧本分析接口",
                "test_data": {
                    "script_text": "EXT. 城市街道 - 夜晚\n\n一个神秘的身影在雨中奔跑。\n\nINT. 咖啡厅 - 白天\n\n主角坐在窗边，思考着昨晚发生的事情。",
                    "project_id": None  # 将在测试中生成
                }
            },
            "project_create": {
                "url": "/api/projects",
                "method": "POST", 
                "description": "创建项目接口",
                "test_data": {
                    "title": "测试项目",
                    "script_raw": "EXT. 城市街道 - 夜晚\n\n一个神秘的身影在雨中奔跑。\n\nINT. 咖啡厅 - 白天\n\n主角坐在窗边，思考着昨晚发生的事情。",
                    "logline": "一个关于神秘追逐的故事"
                }
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
            },
            "project_list": {
                "url": "/api/projects",
                "method": "GET",
                "description": "获取项目列表接口"
            }
        }
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def check_server_status(self) -> Dict:
        """检查服务器状态"""
        print("🔍 检查服务器状态...")
        
        result = {
            "server_running": False,
            "response_time": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            
            # 尝试访问根路径或健康检查端点
            test_urls = [
                f"{self.base_url}/",
                f"{self.base_url}/health", 
                f"{self.base_url}/docs",
                f"{self.base_url}/api/projects"  # 直接测试API端点
            ]
            
            for url in test_urls:
                try:
                    async with self.session.get(url, timeout=5) as response:
                        result["response_time"] = round((time.time() - start_time) * 1000, 2)
                        
                        if response.status < 500:  # 接受4xx和2xx状态码
                            result["server_running"] = True
                            print(f"   ✅ 服务器响应正常 ({url})")
                            print(f"   📊 响应时间: {result['response_time']} ms")
                            print(f"   📊 状态码: {response.status}")
                            break
                        
                except Exception as e:
                    continue
            
            if not result["server_running"]:
                result["error"] = "所有测试端点均无响应"
                print(f"   ❌ 服务器无响应")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ 服务器检查失败: {e}")
        
        return result
    
    async def test_endpoint(self, endpoint_name: str, endpoint_config: Dict) -> Dict:
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
            
            # 准备请求数据
            request_data = endpoint_config.get("test_data")
            
            # 发送请求
            start_time = time.time()
            
            if endpoint_config["method"] == "POST":
                async with self.session.post(
                    full_url, 
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    result["status_code"] = response.status
                    result["response_time"] = round((time.time() - start_time) * 1000, 2)
                    
                    try:
                        result["response_data"] = await response.json()
                    except:
                        result["response_data"] = await response.text()
                    
            elif endpoint_config["method"] == "GET":
                async with self.session.get(full_url) as response:
                    result["status_code"] = response.status
                    result["response_time"] = round((time.time() - start_time) * 1000, 2)
                    
                    try:
                        result["response_data"] = await response.json()
                    except:
                        result["response_data"] = await response.text()
            
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
                
            else:
                result["success"] = False
                print(f"   ❌ 请求失败")
                print(f"   📊 状态码: {result['status_code']}")
                print(f"   📊 响应时间: {result['response_time']} ms")
                
                if isinstance(result["response_data"], dict):
                    error_detail = result["response_data"].get("detail", "未知错误")
                    print(f"   📋 错误详情: {error_detail}")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ 测试失败: {e}")
        
        return result
    
    def _validate_response(self, endpoint_name: str, response_data: Any) -> List[str]:
        """验证响应数据格式"""
        errors = []
        
        if not isinstance(response_data, dict):
            errors.append("响应数据不是JSON对象")
            return errors
        
        # 根据端点类型验证特定字段
        if endpoint_name == "project_create":
            required_fields = ["id", "title", "script_raw", "logline", "created_at"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
            
            if "beats_count" in response_data:
                if not isinstance(response_data["beats_count"], int):
                    errors.append("beats_count应该是整数")
        
        elif endpoint_name == "project_get":
            required_fields = ["id", "title", "script_raw", "logline"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
        
        elif endpoint_name == "project_beats":
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
    
    async def test_error_handling(self) -> Dict:
        """测试错误处理"""
        print(f"\n🔍 测试错误处理...")
        
        results = {
            "invalid_project_id": None,
            "malformed_json": None,
            "missing_fields": None
        }
        
        # 测试无效的项目ID
        try:
            invalid_id = "invalid-project-id"
            url = f"{self.base_url}/api/projects/{invalid_id}"
            
            async with self.session.get(url) as response:
                results["invalid_project_id"] = {
                    "status_code": response.status,
                    "expected": 404,
                    "success": response.status == 404
                }
                
                if results["invalid_project_id"]["success"]:
                    print(f"   ✅ 无效项目ID处理正确 (404)")
                else:
                    print(f"   ❌ 无效项目ID处理异常 ({response.status})")
        
        except Exception as e:
            results["invalid_project_id"] = {"error": str(e), "success": False}
            print(f"   ❌ 无效项目ID测试失败: {e}")
        
        # 测试缺少必需字段
        try:
            url = f"{self.base_url}/api/projects"
            incomplete_data = {"title": "测试项目"}  # 缺少script_raw和logline
            
            async with self.session.post(
                url, 
                json=incomplete_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                results["missing_fields"] = {
                    "status_code": response.status,
                    "expected": 422,  # FastAPI的验证错误
                    "success": response.status == 422
                }
                
                if results["missing_fields"]["success"]:
                    print(f"   ✅ 缺少字段处理正确 (422)")
                else:
                    print(f"   ❌ 缺少字段处理异常 ({response.status})")
        
        except Exception as e:
            results["missing_fields"] = {"error": str(e), "success": False}
            print(f"   ❌ 缺少字段测试失败: {e}")
        
        return results
    
    async def test_performance(self) -> Dict:
        """测试API性能"""
        print(f"\n🔍 测试API性能...")
        
        results = {
            "concurrent_requests": None,
            "response_times": [],
            "average_response_time": None,
            "max_response_time": None,
            "min_response_time": None
        }
        
        try:
            # 并发请求测试
            concurrent_count = 5
            tasks = []
            
            for i in range(concurrent_count):
                task = self._single_performance_request(i)
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # 分析结果
            successful_responses = []
            for response in responses:
                if isinstance(response, dict) and "response_time" in response:
                    successful_responses.append(response)
                    results["response_times"].append(response["response_time"])
            
            if results["response_times"]:
                results["average_response_time"] = round(sum(results["response_times"]) / len(results["response_times"]), 2)
                results["max_response_time"] = max(results["response_times"])
                results["min_response_time"] = min(results["response_times"])
            
            results["concurrent_requests"] = {
                "total_requests": concurrent_count,
                "successful_requests": len(successful_responses),
                "total_time": round(total_time * 1000, 2),
                "success_rate": len(successful_responses) / concurrent_count
            }
            
            print(f"   📊 并发请求: {concurrent_count} 个")
            print(f"   📊 成功请求: {len(successful_responses)} 个")
            print(f"   📊 成功率: {results['concurrent_requests']['success_rate']:.2%}")
            print(f"   📊 平均响应时间: {results['average_response_time']} ms")
            print(f"   📊 最大响应时间: {results['max_response_time']} ms")
            print(f"   📊 最小响应时间: {results['min_response_time']} ms")
            
        except Exception as e:
            results["error"] = str(e)
            print(f"   ❌ 性能测试失败: {e}")
        
        return results
    
    async def _single_performance_request(self, request_id: int) -> Dict:
        """单个性能测试请求"""
        try:
            url = f"{self.base_url}/api/projects"
            start_time = time.time()
            
            async with self.session.get(url) as response:
                response_time = round((time.time() - start_time) * 1000, 2)
                
                return {
                    "request_id": request_id,
                    "status_code": response.status,
                    "response_time": response_time,
                    "success": 200 <= response.status < 300
                }
        
        except Exception as e:
            return {
                "request_id": request_id,
                "error": str(e),
                "success": False
            }
    
    async def run_full_validation(self) -> Dict:
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
            "performance": None,
            "summary": {
                "total_endpoints": len(self.endpoints),
                "successful_endpoints": 0,
                "failed_endpoints": 0,
                "server_running": False
            }
        }
        
        try:
            # 1. 检查服务器状态
            server_status = await self.check_server_status()
            report["server_status"] = server_status
            report["summary"]["server_running"] = server_status["server_running"]
            
            if not server_status["server_running"]:
                print(f"\n❌ 服务器未运行，无法进行API测试")
                print(f"💡 请确保后端服务已启动: python backend/main.py")
                return report
            
            # 2. 测试各个API端点
            for endpoint_name, endpoint_config in self.endpoints.items():
                result = await self.test_endpoint(endpoint_name, endpoint_config)
                report["endpoint_tests"][endpoint_name] = result
                
                if result["success"]:
                    report["summary"]["successful_endpoints"] += 1
                else:
                    report["summary"]["failed_endpoints"] += 1
            
            # 3. 测试错误处理
            error_handling = await self.test_error_handling()
            report["error_handling"] = error_handling
            
            # 4. 测试性能
            performance = await self.test_performance()
            report["performance"] = performance
            
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
        return
    
    # API端点测试结果
    print(f"🌐 API端点测试: {summary['successful_endpoints']}/{summary['total_endpoints']} 个成功")
    
    if report.get("endpoint_tests"):
        for endpoint_name, result in report["endpoint_tests"].items():
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {endpoint_name}: {result.get('status_code', 'N/A')}")
    
    # 错误处理测试
    if report.get("error_handling"):
        error_tests = report["error_handling"]
        successful_error_tests = sum(1 for test in error_tests.values() 
                                   if isinstance(test, dict) and test.get("success", False))
        total_error_tests = len([test for test in error_tests.values() if test is not None])
        
        print(f"🚨 错误处理测试: {successful_error_tests}/{total_error_tests} 个通过")
    
    # 性能测试
    if report.get("performance") and "average_response_time" in report["performance"]:
        perf = report["performance"]
        print(f"⚡ 性能测试: 平均响应时间 {perf['average_response_time']} ms")
        
        if "concurrent_requests" in perf:
            concurrent = perf["concurrent_requests"]
            print(f"🔄 并发测试: {concurrent['success_rate']:.1%} 成功率")
    
    # 整体状态
    if summary["failed_endpoints"] == 0:
        print(f"\n🎯 整体状态: ✅ 所有API正常")
    elif summary["successful_endpoints"] > summary["failed_endpoints"]:
        print(f"\n🎯 整体状态: ⚠️  部分API异常")
    else:
        print(f"\n🎯 整体状态: ❌ 多数API异常")

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO API接口功能检测工具')
    parser.add_argument('--url', default='http://localhost:8000', help='API服务器地址')
    parser.add_argument('--output', help='输出报告到JSON文件')
    
    args = parser.parse_args()
    
    # 运行API验证
    async with APIValidator(args.url) as validator:
        report = await validator.run_full_validation()
    
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
    exit(asyncio.run(main()))