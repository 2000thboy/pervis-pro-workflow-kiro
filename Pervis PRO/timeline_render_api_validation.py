#!/usr/bin/env python3
"""
时间轴和渲染API检测脚本
测试PreVis PRO的时间轴编辑和视频渲染功能
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import time

class TimelineRenderAPIValidator:
    """时间轴和渲染API验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_data = {}
        
        # API端点配置
        self.endpoints = {
            "timeline_list": {
                "url": "/api/timeline/list",
                "method": "GET",
                "description": "时间轴列表接口"
            },
            "timeline_create": {
                "url": "/api/timeline/create",
                "method": "POST",
                "description": "创建时间轴接口",
                "test_data": {
                    "project_id": "test_project_timeline",
                    "name": "测试时间轴"
                }
            },
            "timeline_get": {
                "url": "/api/timeline/{timeline_id}",
                "method": "GET",
                "description": "获取时间轴详情接口",
                "requires": ["timeline_create"]
            },
            "autocut_generate": {
                "url": "/api/autocut/generate",
                "method": "POST",
                "description": "AutoCut自动剪辑接口",
                "test_data": {
                    "project_id": "test_project_autocut",
                    "beats": [
                        {
                            "id": "beat_1",
                            "content": "EXT. 城市街道 - 夜晚。一个神秘的身影在雨中奔跑。",
                            "emotion_tags": ["紧张", "神秘"],
                            "scene_tags": ["夜晚", "街道"],
                            "action_tags": ["奔跑"],
                            "cinematography_tags": ["手持"],
                            "duration": 5.0
                        },
                        {
                            "id": "beat_2", 
                            "content": "INT. 咖啡厅 - 白天。主角坐在窗边，思考着昨晚发生的事情。",
                            "emotion_tags": ["沉思", "平静"],
                            "scene_tags": ["白天", "咖啡厅"],
                            "action_tags": ["坐着", "思考"],
                            "cinematography_tags": ["特写"],
                            "duration": 4.0
                        }
                    ],
                    "available_assets": [
                        {
                            "id": "asset_1",
                            "filename": "city_night_chase.mp4",
                            "mime_type": "video/mp4",
                            "file_path": "/assets/city_night_chase.mp4"
                        },
                        {
                            "id": "asset_2",
                            "filename": "coffee_shop_scene.mp4", 
                            "mime_type": "video/mp4",
                            "file_path": "/assets/coffee_shop_scene.mp4"
                        }
                    ]
                }
            },
            "autocut_health": {
                "url": "/api/autocut/health",
                "method": "GET",
                "description": "AutoCut健康检查接口"
            },
            "render_check": {
                "url": "/api/render/{timeline_id}/check",
                "method": "GET",
                "description": "渲染前置检查接口",
                "requires": ["timeline_create"]
            },
            "render_tasks": {
                "url": "/api/render/tasks",
                "method": "GET",
                "description": "渲染任务列表接口"
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
            url = f"{self.base_url}/"
            
            start_time = time.time()
            response = requests.get(url, timeout=10)
            result["response_time"] = round((time.time() - start_time) * 1000, 2)
            result["status_code"] = response.status_code
            
            if response.status_code < 500:
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
            if "{timeline_id}" in url:
                timeline_id = None
                if "timeline_create" in self.test_data:
                    timeline_id = self.test_data["timeline_create"].get("timeline_id")
                
                if timeline_id:
                    url = url.replace("{timeline_id}", timeline_id)
                    print(f"   🔗 使用时间轴ID: {timeline_id}")
                else:
                    result["error"] = "缺少有效的timeline_id参数"
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
                if endpoint_name == "timeline_create" and isinstance(result["response_data"], dict):
                    self.test_data[endpoint_name] = {
                        "timeline_id": result["response_data"].get("id"),
                        "response": result["response_data"]
                    }
                    print(f"   💾 保存时间轴ID: {self.test_data[endpoint_name]['timeline_id']}")
                
                # 显示部分响应数据
                if isinstance(result["response_data"], dict):
                    self._display_response_summary(endpoint_name, result["response_data"])
                
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
        
        if endpoint_name == "timeline_list":
            if not isinstance(response_data, list):
                errors.append("时间轴列表应该是数组")
            else:
                for i, timeline in enumerate(response_data):
                    if not isinstance(timeline, dict):
                        errors.append(f"时间轴[{i}]不是对象")
        
        elif endpoint_name == "timeline_create":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            required_fields = ["id", "project_id", "name", "duration"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
        
        elif endpoint_name == "timeline_get":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            expected_fields = ["id", "project_id", "name"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        elif endpoint_name == "autocut_generate":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            required_fields = ["status", "timeline", "decisions"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
        
        elif endpoint_name == "autocut_health":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            if "status" not in response_data:
                errors.append("缺少status字段")
        
        elif endpoint_name == "render_check":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            if "status" not in response_data:
                errors.append("缺少status字段")
        
        elif endpoint_name == "render_tasks":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            expected_fields = ["status", "tasks"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        return errors
    
    def _display_response_summary(self, endpoint_name: str, response_data: Dict):
        """显示响应数据摘要"""
        if endpoint_name == "timeline_list":
            if isinstance(response_data, list):
                print(f"   📋 时间轴数量: {len(response_data)}")
        
        elif endpoint_name == "timeline_create":
            timeline_name = response_data.get("name", "N/A")
            duration = response_data.get("duration", 0)
            print(f"   📋 时间轴名称: {timeline_name}")
            print(f"   📋 时长: {duration} 秒")
        
        elif endpoint_name == "timeline_get":
            timeline_name = response_data.get("name", "N/A")
            clips = response_data.get("clips", [])
            print(f"   📋 时间轴名称: {timeline_name}")
            print(f"   📋 片段数量: {len(clips) if isinstance(clips, list) else 'N/A'}")
        
        elif endpoint_name == "autocut_generate":
            status = response_data.get("status", "unknown")
            decisions = response_data.get("decisions", [])
            processing_time = response_data.get("processing_time", 0)
            print(f"   📋 生成状态: {status}")
            print(f"   📋 决策数量: {len(decisions) if isinstance(decisions, list) else 'N/A'}")
            print(f"   📋 处理时间: {processing_time:.3f} 秒")
        
        elif endpoint_name == "autocut_health":
            status = response_data.get("status", "unknown")
            service = response_data.get("service", "N/A")
            print(f"   📋 服务状态: {status}")
            print(f"   📋 服务名称: {service}")
        
        elif endpoint_name == "render_check":
            status = response_data.get("status", "unknown")
            print(f"   📋 检查状态: {status}")
            if "requirements" in response_data:
                requirements = response_data["requirements"]
                print(f"   📋 前置条件: {len(requirements) if isinstance(requirements, dict) else 'N/A'} 项")
        
        elif endpoint_name == "render_tasks":
            tasks = response_data.get("tasks", [])
            print(f"   📋 渲染任务数量: {len(tasks) if isinstance(tasks, list) else 'N/A'}")
    
    def test_timeline_scenarios(self) -> Dict:
        """测试时间轴相关场景"""
        print(f"\n🔍 测试时间轴场景...")
        
        results = {
            "invalid_project_id": None,
            "empty_timeline_name": None
        }
        
        # 测试无效的项目ID
        try:
            url = f"{self.base_url}/api/timeline/create"
            data = {
                "project_id": "",  # 空项目ID
                "name": "测试时间轴"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            results["invalid_project_id"] = {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300 or response.status_code == 422,
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if results["invalid_project_id"]["success"]:
                print(f"   ✅ 无效项目ID处理正常 ({response.status_code})")
            else:
                print(f"   ❌ 无效项目ID处理异常 ({response.status_code})")
        
        except Exception as e:
            results["invalid_project_id"] = {"error": str(e), "success": False}
            print(f"   ❌ 无效项目ID测试失败: {e}")
        
        return results
    
    def run_full_validation(self) -> Dict:
        """运行完整的时间轴和渲染API验证"""
        print("=" * 60)
        print("🎬 PreVis PRO - 时间轴和渲染API检测")
        print("=" * 60)
        print(f"📍 服务器地址: {self.base_url}")
        print()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "server_status": None,
            "endpoint_tests": {},
            "timeline_scenarios": None,
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
                return report
            
            # 2. 测试各个API端点
            for endpoint_name, endpoint_config in self.endpoints.items():
                result = self.test_endpoint(endpoint_name, endpoint_config)
                report["endpoint_tests"][endpoint_name] = result
                
                if result["success"]:
                    report["summary"]["successful_endpoints"] += 1
                else:
                    report["summary"]["failed_endpoints"] += 1
            
            # 3. 测试时间轴场景
            timeline_scenarios = self.test_timeline_scenarios()
            report["timeline_scenarios"] = timeline_scenarios
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            report["error"] = str(e)
        
        return report

def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("\n" + "=" * 60)
    print("📋 时间轴和渲染API检测报告摘要")
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
    print(f"🎬 时间轴和渲染API测试: {summary['successful_endpoints']}/{summary['total_endpoints']} 个成功")
    
    if report.get("endpoint_tests"):
        for endpoint_name, result in report["endpoint_tests"].items():
            status = "✅" if result["success"] else "❌"
            response_time = f" ({result.get('response_time', 'N/A')} ms)" if result.get("response_time") else ""
            print(f"   {status} {endpoint_name}: {result.get('status_code', 'N/A')}{response_time}")
            
            if result.get("validation_errors"):
                print(f"      ⚠️  验证警告: {len(result['validation_errors'])} 个")
    
    # 时间轴场景测试
    if report.get("timeline_scenarios"):
        scenarios = report["timeline_scenarios"]
        successful_scenarios = sum(1 for test in scenarios.values() 
                                 if isinstance(test, dict) and test.get("success", False))
        total_scenarios = len([test for test in scenarios.values() if test is not None])
        
        print(f"🎬 时间轴场景测试: {successful_scenarios}/{total_scenarios} 个通过")
    
    # 整体状态
    if summary["failed_endpoints"] == 0:
        print(f"\n🎯 整体状态: ✅ 所有时间轴和渲染API正常")
    elif summary["successful_endpoints"] > summary["failed_endpoints"]:
        print(f"\n🎯 整体状态: ⚠️  部分时间轴和渲染API异常")
    else:
        print(f"\n🎯 整体状态: ❌ 多数时间轴和渲染API异常")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO 时间轴和渲染API检测工具')
    parser.add_argument('--url', default='http://localhost:8000', help='API服务器地址')
    parser.add_argument('--output', help='输出报告到JSON文件')
    
    args = parser.parse_args()
    
    # 创建验证器并运行
    validator = TimelineRenderAPIValidator(args.url)
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