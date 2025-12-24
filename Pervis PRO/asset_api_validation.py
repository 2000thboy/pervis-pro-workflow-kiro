#!/usr/bin/env python3
"""
素材管理API检测脚本
测试PreVis PRO的素材上传、处理和查询功能
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import time
import tempfile
import ast


def _parse_tag_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        if s == "[]":
            return []

        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass

        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass

        s = s.strip("[]")
        parts = [p.strip().strip("\"'") for p in s.split(",")]
        return [p for p in parts if p]

    return [str(value).strip()] if str(value).strip() else []


def _calc_tag_metrics(expected: List[str], predicted: List[str]) -> Dict[str, Any]:
    expected_set = {t.strip().lower() for t in expected if t and t.strip()}
    predicted_set = {t.strip().lower() for t in predicted if t and t.strip()}

    tp = expected_set & predicted_set
    fp = predicted_set - expected_set
    fn = expected_set - predicted_set

    recall = (len(tp) / len(expected_set)) if expected_set else 1.0
    precision = (len(tp) / len(predicted_set)) if predicted_set else (1.0 if not expected_set else 0.0)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "expected": sorted(expected_set),
        "predicted": sorted(predicted_set),
        "true_positive": sorted(tp),
        "false_positive": sorted(fp),
        "false_negative": sorted(fn),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4)
    }

class AssetAPIValidator:
    """素材管理API验证器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.test_data = {}
        
        # API端点配置 - 调整顺序，先获取素材列表再测试状态查询
        self.endpoints = {
            "asset_upload": {
                "url": "/api/assets/upload",
                "method": "POST",
                "description": "素材上传接口",
                "test_file": True
            },
            "asset_list": {
                "url": "/api/assets/list",
                "method": "GET",
                "description": "素材列表接口"
            },
            "asset_status": {
                "url": "/api/assets/{asset_id}/status",
                "method": "GET",
                "description": "素材状态查询接口",
                "requires": ["asset_list"]
            },
            "asset_search": {
                "url": "/api/assets/search",
                "method": "GET",
                "description": "素材搜索接口"
            }
        }
    
    def create_test_file(self) -> str:
        """创建测试文件"""
        # 创建一个小的测试文本文件
        test_content = """
这是一个测试素材文件。
用于验证PreVis PRO的素材上传和处理功能。
创建时间: {}
文件ID: {}
        """.format(datetime.now(), str(uuid.uuid4()))
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            return f.name
    
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
            # 检查依赖 - 修复逻辑，检查是否有真实素材ID
            if "requires" in endpoint_config:
                for required_endpoint in endpoint_config["requires"]:
                    if required_endpoint == "asset_list" and "real_asset" not in self.test_data:
                        result["error"] = f"依赖的端点 {required_endpoint} 未提供有效数据"
                        print(f"   ❌ 依赖检查失败: {result['error']}")
                        return result
                    elif required_endpoint != "asset_list" and required_endpoint not in self.test_data:
                        result["error"] = f"依赖的端点 {required_endpoint} 未成功执行"
                        print(f"   ❌ 依赖检查失败: {result['error']}")
                        return result
            
            # 构建URL
            url = endpoint_config["url"]
            if "{asset_id}" in url:
                # 优先使用真实的asset_id
                asset_id = None
                if "real_asset" in self.test_data:
                    asset_id = self.test_data["real_asset"].get("asset_id")
                elif "asset_upload" in self.test_data:
                    upload_id = self.test_data["asset_upload"].get("asset_id")
                    if upload_id and upload_id != "processing":
                        asset_id = upload_id
                
                if asset_id:
                    url = url.replace("{asset_id}", asset_id)
                    print(f"   🔗 使用素材ID: {asset_id}")
                else:
                    result["error"] = "缺少有效的asset_id参数"
                    print(f"   ❌ URL构建失败: {result['error']}")
                    return result
            
            full_url = f"{self.base_url}{url}"
            print(f"   🌐 请求URL: {full_url}")
            
            # 发送请求
            start_time = time.time()
            
            if endpoint_config["method"] == "POST" and endpoint_config.get("test_file"):
                # 文件上传测试
                test_file_path = self.create_test_file()
                
                try:
                    with open(test_file_path, 'rb') as f:
                        files = {'file': ('test_asset.txt', f, 'text/plain')}
                        data = {'project_id': 'test_project'}
                        
                        response = requests.post(
                            full_url,
                            files=files,
                            data=data,
                            timeout=30
                        )
                finally:
                    # 清理测试文件
                    try:
                        os.unlink(test_file_path)
                    except:
                        pass
                
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
                if endpoint_name == "asset_upload" and isinstance(result["response_data"], dict):
                    self.test_data[endpoint_name] = {
                        "asset_id": result["response_data"].get("asset_id"),
                        "response": result["response_data"]
                    }
                    print(f"   💾 保存素材ID: {self.test_data[endpoint_name]['asset_id']}")
                
                # 从素材列表获取真实的asset_id用于状态查询
                elif endpoint_name == "asset_list" and isinstance(result["response_data"], list):
                    if result["response_data"]:  # 如果有素材
                        first_asset = result["response_data"][0]
                        if isinstance(first_asset, dict) and "id" in first_asset:
                            self.test_data["real_asset"] = {
                                "asset_id": first_asset["id"],
                                "filename": first_asset.get("filename", "unknown")
                            }
                            print(f"   💾 发现真实素材ID: {first_asset['id']}")
                
                # 显示部分响应数据
                if isinstance(result["response_data"], dict):
                    if endpoint_name == "asset_upload":
                        print(f"   📋 上传状态: {result['response_data'].get('status', 'N/A')}")
                        print(f"   📋 处理消息: {result['response_data'].get('message', 'N/A')}")
                    elif endpoint_name == "asset_list":
                        if isinstance(result["response_data"], list):
                            print(f"   📋 素材数量: {len(result['response_data'])}")
                        elif "assets" in result["response_data"]:
                            assets = result["response_data"]["assets"]
                            print(f"   📋 素材数量: {len(assets) if isinstance(assets, list) else 'N/A'}")
                
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
        
        if endpoint_name == "asset_upload":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            required_fields = ["asset_id", "status"]
            for field in required_fields:
                if field not in response_data:
                    errors.append(f"缺少必需字段: {field}")
        
        elif endpoint_name == "asset_status":
            if not isinstance(response_data, dict):
                errors.append("响应数据不是JSON对象")
                return errors
            
            expected_fields = ["asset_id", "status", "progress"]
            for field in expected_fields:
                if field not in response_data:
                    errors.append(f"缺少字段: {field}")
        
        elif endpoint_name == "asset_list":
            # 可能是数组或包含assets字段的对象
            if isinstance(response_data, list):
                # 直接是素材数组
                for i, asset in enumerate(response_data):
                    if not isinstance(asset, dict):
                        errors.append(f"素材[{i}]不是对象")
            elif isinstance(response_data, dict):
                if "assets" in response_data:
                    assets = response_data["assets"]
                    if not isinstance(assets, list):
                        errors.append("assets字段应该是数组")
                else:
                    errors.append("响应应该包含assets字段或直接是素材数组")
            else:
                errors.append("响应数据格式不正确")
        
        return errors
    
    def test_file_upload_scenarios(self) -> Dict:
        """测试不同的文件上传场景"""
        print(f"\n🔍 测试文件上传场景...")
        
        results = {
            "large_file": None,
            "invalid_file": None,
            "missing_file": None
        }

        # 测试大文件限制（当前后端默认限制100MB）
        try:
            url = f"{self.base_url}/api/assets/upload"
            size_bytes = 101 * 1024 * 1024
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.bin', delete=False) as f:
                large_file_path = f.name
                f.truncate(size_bytes)

            try:
                start_time = time.time()
                with open(large_file_path, 'rb') as f:
                    files = {'file': ('large_test.bin', f, 'application/octet-stream')}
                    data = {'project_id': 'test_project'}
                    response = requests.post(url, files=files, data=data, timeout=60)

                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                try:
                    body = response.json()
                except Exception:
                    body = response.text

                results["large_file"] = {
                    "status_code": response.status_code,
                    "response_time_ms": elapsed_ms,
                    "expected": 400,
                    "success": response.status_code == 400,
                    "response": body
                }

                if results["large_file"]["success"]:
                    print(f"   ✅ 大文件限制生效 ({response.status_code})")
                else:
                    print(f"   ⚠️  大文件限制未按预期返回400 ({response.status_code})")
            finally:
                try:
                    os.unlink(large_file_path)
                except Exception:
                    pass

        except Exception as e:
            results["large_file"] = {"error": str(e), "success": False}
            print(f"   ❌ 大文件限制测试失败: {e}")
        
        # 测试缺少文件的情况
        try:
            url = f"{self.base_url}/api/assets/upload"
            data = {'project_id': 'test_project'}
            
            response = requests.post(url, data=data, timeout=10)
            
            results["missing_file"] = {
                "status_code": response.status_code,
                "expected": 422,  # FastAPI验证错误
                "success": response.status_code == 422
            }
            
            if results["missing_file"]["success"]:
                print(f"   ✅ 缺少文件处理正确 (422)")
            else:
                print(f"   ❌ 缺少文件处理异常 ({response.status_code})")
        
        except Exception as e:
            results["missing_file"] = {"error": str(e), "success": False}
            print(f"   ❌ 缺少文件测试失败: {e}")
        
        return results
    
    def run_full_validation(self) -> Dict:
        """运行完整的素材API验证"""
        print("=" * 60)
        print("📁 PreVis PRO - 素材管理API检测")
        print("=" * 60)
        print(f"📍 服务器地址: {self.base_url}")
        print()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "server_status": None,
            "endpoint_tests": {},
            "upload_scenarios": None,
            "tag_recall_benchmark": None,
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
            
            # 3. 测试文件上传场景
            upload_scenarios = self.test_file_upload_scenarios()
            report["upload_scenarios"] = upload_scenarios

            # 4. 标签召回率基准测试（基于已知标签的视频样本集）
            asset_list_result = report.get("endpoint_tests", {}).get("asset_list", {})
            if asset_list_result.get("success") and isinstance(asset_list_result.get("response_data"), list):
                report["tag_recall_benchmark"] = self.run_tag_recall_benchmark(asset_list_result["response_data"])
            else:
                report["tag_recall_benchmark"] = {
                    "status": "skipped",
                    "reason": "asset_list 未成功或返回格式非数组"
                }
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            report["error"] = str(e)
        
        return report

    def run_tag_recall_benchmark(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        ground_truth = {
            "close_up_face_guilty.mp4": ["特写", "脸部", "愧疚", "情绪", "年轻人"],
            "conversation_office_serious.mp4": ["对话", "办公室", "严肃", "老板", "员工"],
            "person_walking_hurried.mp4": ["人物", "行走", "匆忙", "焦虑", "咖啡"],
            "office_modern_interior.mp4": ["办公室", "室内", "现代", "白天", "工作"],
            "city_street_busy.mp4": ["城市", "街道", "繁忙", "白天", "户外"]
        }

        benchmark_assets = [a for a in assets if a.get("filename") in ground_truth]
        if not benchmark_assets:
            return {
                "status": "skipped",
                "reason": "素材库未发现基准样本文件名",
                "expected_filenames": sorted(list(ground_truth.keys()))
            }

        per_asset = []
        micro_tp = 0
        micro_fp = 0
        micro_fn = 0

        for asset in benchmark_assets:
            filename = asset.get("filename")
            expected = ground_truth.get(filename, [])
            predicted = _parse_tag_list(asset.get("tags"))
            metrics = _calc_tag_metrics(expected, predicted)

            micro_tp += len(metrics["true_positive"])
            micro_fp += len(metrics["false_positive"])
            micro_fn += len(metrics["false_negative"])

            per_asset.append({
                "asset_id": asset.get("id"),
                "filename": filename,
                **metrics
            })

        micro_recall = (micro_tp / (micro_tp + micro_fn)) if (micro_tp + micro_fn) else 1.0
        micro_precision = (micro_tp / (micro_tp + micro_fp)) if (micro_tp + micro_fp) else 1.0
        micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) else 0.0

        return {
            "status": "success",
            "benchmark_count": len(per_asset),
            "micro": {
                "true_positive": micro_tp,
                "false_positive": micro_fp,
                "false_negative": micro_fn,
                "precision": round(micro_precision, 4),
                "recall": round(micro_recall, 4),
                "f1": round(micro_f1, 4)
            },
            "per_asset": per_asset
        }

def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("\n" + "=" * 60)
    print("📋 素材管理API检测报告摘要")
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
    print(f"📁 素材API测试: {summary['successful_endpoints']}/{summary['total_endpoints']} 个成功")
    
    if report.get("endpoint_tests"):
        for endpoint_name, result in report["endpoint_tests"].items():
            status = "✅" if result["success"] else "❌"
            response_time = f" ({result.get('response_time', 'N/A')} ms)" if result.get("response_time") else ""
            print(f"   {status} {endpoint_name}: {result.get('status_code', 'N/A')}{response_time}")
            
            if result.get("validation_errors"):
                print(f"      ⚠️  验证警告: {len(result['validation_errors'])} 个")
    
    # 上传场景测试
    if report.get("upload_scenarios"):
        scenarios = report["upload_scenarios"]
        successful_scenarios = sum(1 for test in scenarios.values() 
                                 if isinstance(test, dict) and test.get("success", False))
        total_scenarios = len([test for test in scenarios.values() if test is not None])
        
        print(f"📤 上传场景测试: {successful_scenarios}/{total_scenarios} 个通过")
    
    # 整体状态
    if summary["failed_endpoints"] == 0:
        print(f"\n🎯 整体状态: ✅ 所有素材API正常")
    elif summary["successful_endpoints"] > summary["failed_endpoints"]:
        print(f"\n🎯 整体状态: ⚠️  部分素材API异常")
    else:
        print(f"\n🎯 整体状态: ❌ 多数素材API异常")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO 素材管理API检测工具')
    parser.add_argument('--url', default='http://localhost:8000', help='API服务器地址')
    parser.add_argument('--output', help='输出报告到JSON文件')
    
    args = parser.parse_args()
    
    # 创建验证器并运行
    validator = AssetAPIValidator(args.url)
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
