#!/usr/bin/env python3
"""
搜索和匹配API检测脚本
测试PreVis PRO的语义搜索和多模态搜索功能
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import time

class SearchAPIValidator:
    """搜索和匹配API验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_data = {}
        
        # API端点配置
        self.endpoints = {
            "semantic_search": {
                "url": "/api/search/semantic",
                "method": "POST",
                "description": "语义搜索接口",
                "test_data": {
                    "beat_id": "default_beat",
                    "query_tags": {
                        "emotions": ["紧张", "神秘"],
                        "scenes": ["夜晚", "街道"],
                        "actions": ["奔跑", "追逐"],
                        "cinematography": ["手持", "特写"]
                    },
                    "fuzziness": 0.7,
                    "limit": 10
                }
            },
            "multimodal_search": {
                "url": "/api/multimodal/search",
                "method": "POST",
                "description": "多模态搜索接口",
                "test_data": {
                    "query": "夜晚街道追逐场景",
                    "beat_id": "default_beat",
                    "search_modes": ["semantic", "transcription", "visual"],
                    "weights": {
                        "semantic": 0.4,
                        "transcription": 0.3,
                        "visual": 0.3
                    },
                    "fuzziness": 0.7,
                    "limit": 10
                }
            },
            "beatboard_search": {
                "url": "/api/multimodal/search/beatboard",
                "method": "POST",
                "description": "BeatBoard媒体搜索接口",
                "test_data": {
                    "query": "城市夜景咖啡厅",
                    "search_modes": ["semantic", "visual"],
                    "fuzziness": 0.6,
                    "limit": 8
                }
            },
            "visual_search": {
                "url": "/api/multimodal/search/visual",
                "method": "POST",
                "description": "视觉搜索接口",
                "test_data": {
                    "query": "建筑 天空 现代",
                    "limit": 5
                }
            },
            "model_info": {
                "url": "/api/multimodal/model/info",
                "method": "GET",
                "description": "多模态模型信息接口"
            },
            "processing_estimate": {
                "url": "/api/multimodal/estimate?video_duration=30.0&enable_transcription=true&enable_visual_analysis=true&sample_interval=2.0",
                "method": "POST",
                "description": "处理时间估算接口",
                "test_data": {}
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
            full_url = f"{self.base_url}{endpoint_config['url']}"
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
        
        if not isinstance(response_data, dict):
            errors.append("响应数据不是JSON对象")
            return errors
        
        if endpoint_name == "semantic_search":
            required_fields = ["results", "total_matches", "search_time"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
            
            if "results" in response_data and isinstance(response_data["results"], list):
                for i, result in enumerate(response_data["results"]):
                    if not isinstance(result, dict):
                        errors.append(f"搜索结果[{i}]不是对象")
        
        elif endpoint_name == "multimodal_search":
            if "status" in response_data:
                if response_data["status"] != "success":
                    # 允许失败状态，但应该有错误信息
                    if "error" not in response_data and "message" not in response_data:
                        errors.append("失败状态缺少错误信息")
            else:
                errors.append("缺少status字段")
        
        elif endpoint_name == "beatboard_search":
            expected_fields = ["status", "query", "total_results", "results"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        elif endpoint_name == "visual_search":
            expected_fields = ["status", "query", "results"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        elif endpoint_name == "model_info":
            expected_fields = ["status", "multimodal_capabilities"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        elif endpoint_name == "processing_estimate":
            expected_fields = ["status", "total_estimated_time", "processing_breakdown"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        return errors
    
    def _display_response_summary(self, endpoint_name: str, response_data: Dict):
        """显示响应数据摘要"""
        if endpoint_name == "semantic_search":
            total_matches = response_data.get("total_matches", 0)
            search_time = response_data.get("search_time", 0)
            print(f"   📋 搜索结果: {total_matches} 个匹配")
            print(f"   📋 搜索耗时: {search_time:.3f} 秒")
        
        elif endpoint_name == "multimodal_search":
            status = response_data.get("status", "unknown")
            print(f"   📋 搜索状态: {status}")
            if "results" in response_data:
                results = response_data["results"]
                print(f"   📋 结果数量: {len(results) if isinstance(results, list) else 'N/A'}")
        
        elif endpoint_name == "beatboard_search":
            total_results = response_data.get("total_results", 0)
            video_results = response_data.get("video_results", 0)
            image_results = response_data.get("image_results", 0)
            print(f"   📋 总结果: {total_results} 个")
            print(f"   📋 视频: {video_results} 个, 图片: {image_results} 个")
        
        elif endpoint_name == "visual_search":
            results = response_data.get("results", [])
            total_matches = response_data.get("total_matches", len(results))
            print(f"   📋 视觉搜索结果: {total_matches} 个")
        
        elif endpoint_name == "model_info":
            capabilities = response_data.get("multimodal_capabilities", {})
            supported_modes = response_data.get("supported_search_modes", [])
            print(f"   📋 支持的搜索模式: {', '.join(supported_modes)}")
            print(f"   📋 模型能力: {len(capabilities)} 个模块")
        
        elif endpoint_name == "processing_estimate":
            total_time = response_data.get("total_estimated_time", 0)
            breakdown = response_data.get("processing_breakdown", {})
            print(f"   📋 预估总时间: {total_time:.2f} 秒")
            print(f"   📋 处理步骤: {len(breakdown)} 个")
    
    def test_search_scenarios(self) -> Dict:
        """测试不同的搜索场景"""
        print(f"\n🔍 测试搜索场景...")
        
        results = {
            "empty_query": None,
            "invalid_beat_id": None,
            "large_limit": None
        }
        
        # 测试空查询
        try:
            url = f"{self.base_url}/api/multimodal/search"
            data = {
                "query": "",
                "limit": 5
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            results["empty_query"] = {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if results["empty_query"]["success"]:
                print(f"   ✅ 空查询处理正常 ({response.status_code})")
            else:
                print(f"   ❌ 空查询处理异常 ({response.status_code})")
        
        except Exception as e:
            results["empty_query"] = {"error": str(e), "success": False}
            print(f"   ❌ 空查询测试失败: {e}")
        
        # 测试无效的beat_id
        try:
            url = f"{self.base_url}/api/search/semantic"
            data = {
                "beat_id": "invalid-beat-id-12345",
                "query_tags": {"emotions": ["测试"]},
                "fuzziness": 0.5,
                "limit": 5
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            results["invalid_beat_id"] = {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "response_data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            }
            
            if results["invalid_beat_id"]["success"]:
                print(f"   ✅ 无效Beat ID处理正常 ({response.status_code})")
            else:
                print(f"   ❌ 无效Beat ID处理异常 ({response.status_code})")
        
        except Exception as e:
            results["invalid_beat_id"] = {"error": str(e), "success": False}
            print(f"   ❌ 无效Beat ID测试失败: {e}")
        
        return results
    
    def run_full_validation(self) -> Dict:
        """运行完整的搜索API验证"""
        print("=" * 60)
        print("🔍 PreVis PRO - 搜索和匹配API检测")
        print("=" * 60)
        print(f"📍 服务器地址: {self.base_url}")
        print()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "server_status": None,
            "endpoint_tests": {},
            "search_scenarios": None,
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
            
            # 3. 测试搜索场景
            search_scenarios = self.test_search_scenarios()
            report["search_scenarios"] = search_scenarios
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            report["error"] = str(e)
        
        return report

def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("\n" + "=" * 60)
    print("📋 搜索和匹配API检测报告摘要")
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
    print(f"🔍 搜索API测试: {summary['successful_endpoints']}/{summary['total_endpoints']} 个成功")
    
    if report.get("endpoint_tests"):
        for endpoint_name, result in report["endpoint_tests"].items():
            status = "✅" if result["success"] else "❌"
            response_time = f" ({result.get('response_time', 'N/A')} ms)" if result.get("response_time") else ""
            print(f"   {status} {endpoint_name}: {result.get('status_code', 'N/A')}{response_time}")
            
            if result.get("validation_errors"):
                print(f"      ⚠️  验证警告: {len(result['validation_errors'])} 个")
    
    # 搜索场景测试
    if report.get("search_scenarios"):
        scenarios = report["search_scenarios"]
        successful_scenarios = sum(1 for test in scenarios.values() 
                                 if isinstance(test, dict) and test.get("success", False))
        total_scenarios = len([test for test in scenarios.values() if test is not None])
        
        print(f"🔍 搜索场景测试: {successful_scenarios}/{total_scenarios} 个通过")
    
    # 整体状态
    if summary["failed_endpoints"] == 0:
        print(f"\n🎯 整体状态: ✅ 所有搜索API正常")
    elif summary["successful_endpoints"] > summary["failed_endpoints"]:
        print(f"\n🎯 整体状态: ⚠️  部分搜索API异常")
    else:
        print(f"\n🎯 整体状态: ❌ 多数搜索API异常")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO 搜索和匹配API检测工具')
    parser.add_argument('--url', default='http://localhost:8000', help='API服务器地址')
    parser.add_argument('--output', help='输出报告到JSON文件')
    
    args = parser.parse_args()
    
    # 创建验证器并运行
    validator = SearchAPIValidator(args.url)
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