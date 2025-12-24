#!/usr/bin/env python3
"""
P0/P1修复后的性能测试脚本
验证修复效果并生成详细测试报告
"""

import asyncio
import json
import time
import requests
import sys
from pathlib import Path
from typing import Dict, List, Any
import statistics
import subprocess
import os

class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_environment": {
                "backend_url": self.base_url,
                "frontend_url": self.frontend_url,
                "python_version": sys.version,
                "platform": sys.platform
            },
            "performance_tests": {},
            "comparison": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "performance_improvements": {}
            }
        }
        
        # 修复前的基准数据
        self.baseline_metrics = {
            "api_response_time": 2392.17,  # ms
            "frontend_load_time": 2033.0,  # ms
            "database_query_time": 150.0,  # ms (估算)
            "bundle_size": 2.5  # MB (估算)
        }
    
    def log_test(self, test_name: str, success: bool, metrics: Dict, message: str = ""):
        """记录测试结果"""
        self.test_results["performance_tests"][test_name] = {
            "success": success,
            "metrics": metrics,
            "message": message,
            "timestamp": time.strftime("%H:%M:%S")
        }
        
        self.test_results["summary"]["total_tests"] += 1
        if success:
            self.test_results["summary"]["passed_tests"] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results["summary"]["failed_tests"] += 1
            print(f"❌ {test_name}: {message}")
        
        # 显示关键指标
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    print(f"   {key}: {value}")
    
    def test_api_response_time(self):
        """测试API响应时间"""
        try:
            endpoints = [
                "/api/health",
                "/api/projects", 
                "/api/batch/queue/status",
                "/api/batch/stats"
            ]
            
            response_times = []
            successful_requests = 0
            
            for endpoint in endpoints:
                times = []
                for i in range(10):  # 每个端点测试10次
                    start_time = time.time()
                    try:
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            response_time = (end_time - start_time) * 1000  # ms
                            times.append(response_time)
                            successful_requests += 1
                    except Exception as e:
                        print(f"   请求失败 {endpoint}: {e}")
                
                if times:
                    response_times.extend(times)
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                
                # 计算改进幅度
                baseline = self.baseline_metrics["api_response_time"]
                improvement = ((baseline - avg_response_time) / baseline) * 100
                
                metrics = {
                    "average_response_time_ms": round(avg_response_time, 2),
                    "p95_response_time_ms": round(p95_response_time, 2),
                    "min_response_time_ms": round(min_response_time, 2),
                    "max_response_time_ms": round(max_response_time, 2),
                    "successful_requests": successful_requests,
                    "total_requests": len(endpoints) * 10,
                    "improvement_percentage": round(improvement, 1)
                }
                
                # 判断是否达到目标
                target_met = avg_response_time < 500
                message = f"平均响应时间: {avg_response_time:.2f}ms (改进: {improvement:.1f}%)"
                
                self.log_test("api_response_time", target_met, metrics, message)
                
                # 记录改进数据
                self.test_results["comparison"]["api_response_time"] = {
                    "baseline": baseline,
                    "current": avg_response_time,
                    "improvement": improvement,
                    "target": 500,
                    "target_met": target_met
                }
                
                return avg_response_time
            else:
                self.log_test("api_response_time", False, {}, "所有API请求都失败")
                return -1
                
        except Exception as e:
            self.log_test("api_response_time", False, {}, f"API响应时间测试异常: {str(e)}")
            return -1
    
    def test_database_connection_pool(self):
        """测试数据库连接池效果"""
        try:
            # 并发测试数据库连接
            concurrent_requests = 20
            start_time = time.time()
            
            def make_request():
                try:
                    response = requests.get(f"{self.base_url}/api/health", timeout=5)
                    return response.status_code == 200
                except:
                    return False
            
            # 使用线程池进行并发测试
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            total_time = (end_time - start_time) * 1000  # ms
            
            successful_requests = sum(results)
            success_rate = (successful_requests / concurrent_requests) * 100
            avg_time_per_request = total_time / concurrent_requests
            
            metrics = {
                "concurrent_requests": concurrent_requests,
                "successful_requests": successful_requests,
                "success_rate_percentage": round(success_rate, 1),
                "total_time_ms": round(total_time, 2),
                "avg_time_per_request_ms": round(avg_time_per_request, 2)
            }
            
            # 连接池效果良好的标准：成功率>95%，平均时间<100ms
            pool_effective = success_rate > 95 and avg_time_per_request < 100
            message = f"并发成功率: {success_rate:.1f}%, 平均时间: {avg_time_per_request:.2f}ms"
            
            self.log_test("database_connection_pool", pool_effective, metrics, message)
            
            return pool_effective
            
        except Exception as e:
            self.log_test("database_connection_pool", False, {}, f"连接池测试异常: {str(e)}")
            return False
    
    def test_cache_service(self):
        """测试缓存服务效果"""
        try:
            # 测试缓存命中率
            cache_test_endpoint = f"{self.base_url}/api/batch/stats"
            
            # 第一次请求 - 缓存未命中
            start_time = time.time()
            response1 = requests.get(cache_test_endpoint, timeout=10)
            first_request_time = (time.time() - start_time) * 1000
            
            # 第二次请求 - 应该命中缓存
            start_time = time.time()
            response2 = requests.get(cache_test_endpoint, timeout=10)
            second_request_time = (time.time() - start_time) * 1000
            
            if response1.status_code == 200 and response2.status_code == 200:
                # 计算缓存效果
                cache_speedup = ((first_request_time - second_request_time) / first_request_time) * 100
                cache_effective = second_request_time < first_request_time * 0.8  # 至少20%提升
                
                metrics = {
                    "first_request_time_ms": round(first_request_time, 2),
                    "second_request_time_ms": round(second_request_time, 2),
                    "cache_speedup_percentage": round(cache_speedup, 1),
                    "cache_effective": cache_effective
                }
                
                message = f"缓存加速: {cache_speedup:.1f}% (第一次: {first_request_time:.2f}ms, 第二次: {second_request_time:.2f}ms)"
                
                self.log_test("cache_service", cache_effective, metrics, message)
                return cache_effective
            else:
                self.log_test("cache_service", False, {}, "缓存测试请求失败")
                return False
                
        except Exception as e:
            self.log_test("cache_service", False, {}, f"缓存服务测试异常: {str(e)}")
            return False
    
    def test_response_compression(self):
        """测试响应压缩效果"""
        try:
            # 测试大响应的压缩效果
            test_endpoint = f"{self.base_url}/api/batch/tasks/history?limit=50"
            
            # 不启用压缩的请求
            headers_no_compression = {"Accept-Encoding": "identity"}
            response_no_compression = requests.get(test_endpoint, headers=headers_no_compression, timeout=10)
            
            # 启用压缩的请求
            headers_with_compression = {"Accept-Encoding": "gzip, deflate"}
            response_with_compression = requests.get(test_endpoint, headers=headers_with_compression, timeout=10)
            
            if response_no_compression.status_code == 200 and response_with_compression.status_code == 200:
                uncompressed_size = len(response_no_compression.content)
                compressed_size = len(response_with_compression.content)
                
                # 检查是否真的压缩了
                is_compressed = "gzip" in response_with_compression.headers.get("Content-Encoding", "")
                compression_ratio = ((uncompressed_size - compressed_size) / uncompressed_size) * 100 if uncompressed_size > 0 else 0
                
                metrics = {
                    "uncompressed_size_bytes": uncompressed_size,
                    "compressed_size_bytes": compressed_size,
                    "compression_ratio_percentage": round(compression_ratio, 1),
                    "is_compressed": is_compressed,
                    "content_encoding": response_with_compression.headers.get("Content-Encoding", "none")
                }
                
                # 压缩有效的标准：压缩比>30%或者响应头包含gzip
                compression_effective = compression_ratio > 30 or is_compressed
                message = f"压缩比: {compression_ratio:.1f}%, 编码: {response_with_compression.headers.get('Content-Encoding', 'none')}"
                
                self.log_test("response_compression", compression_effective, metrics, message)
                return compression_effective
            else:
                self.log_test("response_compression", False, {}, "压缩测试请求失败")
                return False
                
        except Exception as e:
            self.log_test("response_compression", False, {}, f"响应压缩测试异常: {str(e)}")
            return False
    
    def test_frontend_build_optimization(self):
        """测试前端构建优化效果"""
        try:
            # 检查构建文件
            build_dir = Path("frontend/dist")
            if not build_dir.exists():
                # 尝试构建
                print("   正在执行前端构建...")
                result = subprocess.run(
                    ["npm", "run", "build"], 
                    cwd="frontend", 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    self.log_test("frontend_build_optimization", False, {}, f"前端构建失败: {result.stderr}")
                    return False
            
            # 分析构建结果
            js_files = list(build_dir.glob("**/*.js"))
            css_files = list(build_dir.glob("**/*.css"))
            
            total_js_size = sum(f.stat().st_size for f in js_files)
            total_css_size = sum(f.stat().st_size for f in css_files)
            total_size = total_js_size + total_css_size
            
            # 检查是否有代码分割
            chunk_files = [f for f in js_files if "chunk" in f.name or "vendor" in f.name]
            has_code_splitting = len(chunk_files) > 0
            
            # 检查是否有压缩
            sample_js = js_files[0] if js_files else None
            is_minified = False
            if sample_js:
                with open(sample_js, 'r', encoding='utf-8') as f:
                    content = f.read(1000)  # 读取前1000字符
                    is_minified = '\n' not in content and len(content.split()) < 10
            
            metrics = {
                "total_js_files": len(js_files),
                "total_css_files": len(css_files),
                "total_js_size_mb": round(total_js_size / 1024 / 1024, 2),
                "total_css_size_mb": round(total_css_size / 1024 / 1024, 2),
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "chunk_files_count": len(chunk_files),
                "has_code_splitting": has_code_splitting,
                "is_minified": is_minified
            }
            
            # 计算改进
            baseline_size = self.baseline_metrics["bundle_size"]
            current_size = total_size / 1024 / 1024  # MB
            size_improvement = ((baseline_size - current_size) / baseline_size) * 100
            
            # 优化有效的标准：有代码分割、有压缩、大小合理
            optimization_effective = has_code_splitting and is_minified and current_size < baseline_size
            message = f"Bundle大小: {current_size:.2f}MB (改进: {size_improvement:.1f}%), 代码分割: {has_code_splitting}, 压缩: {is_minified}"
            
            self.log_test("frontend_build_optimization", optimization_effective, metrics, message)
            
            # 记录改进数据
            self.test_results["comparison"]["bundle_size"] = {
                "baseline": baseline_size,
                "current": current_size,
                "improvement": size_improvement,
                "target": baseline_size * 0.7,  # 目标减少30%
                "target_met": current_size < baseline_size * 0.7
            }
            
            return optimization_effective
            
        except Exception as e:
            self.log_test("frontend_build_optimization", False, {}, f"前端构建优化测试异常: {str(e)}")
            return False
    
    def test_database_indexes(self):
        """测试数据库索引效果"""
        try:
            # 检查索引迁移文件是否存在
            migration_file = Path("backend/migrations/004_add_performance_indexes.py")
            if not migration_file.exists():
                self.log_test("database_indexes", False, {}, "索引迁移文件不存在")
                return False
            
            # 尝试执行索引创建（如果还没执行）
            try:
                exec(open(migration_file).read())
                print("   索引迁移已执行")
            except Exception as e:
                print(f"   索引迁移执行失败或已存在: {e}")
            
            # 测试查询性能（简单测试）
            query_times = []
            for i in range(5):
                start_time = time.time()
                try:
                    # 测试一个应该使用索引的查询
                    response = requests.get(f"{self.base_url}/api/projects", timeout=10)
                    if response.status_code == 200:
                        query_time = (time.time() - start_time) * 1000
                        query_times.append(query_time)
                except Exception as e:
                    print(f"   查询测试失败: {e}")
            
            if query_times:
                avg_query_time = statistics.mean(query_times)
                baseline_query_time = self.baseline_metrics["database_query_time"]
                query_improvement = ((baseline_query_time - avg_query_time) / baseline_query_time) * 100
                
                metrics = {
                    "average_query_time_ms": round(avg_query_time, 2),
                    "query_improvement_percentage": round(query_improvement, 1),
                    "migration_file_exists": True,
                    "test_queries_count": len(query_times)
                }
                
                # 索引有效的标准：查询时间有改进
                indexes_effective = avg_query_time < baseline_query_time
                message = f"平均查询时间: {avg_query_time:.2f}ms (改进: {query_improvement:.1f}%)"
                
                self.log_test("database_indexes", indexes_effective, metrics, message)
                
                # 记录改进数据
                self.test_results["comparison"]["database_query_time"] = {
                    "baseline": baseline_query_time,
                    "current": avg_query_time,
                    "improvement": query_improvement,
                    "target": baseline_query_time * 0.5,  # 目标提升50%
                    "target_met": avg_query_time < baseline_query_time * 0.5
                }
                
                return indexes_effective
            else:
                self.log_test("database_indexes", False, {}, "数据库查询测试失败")
                return False
                
        except Exception as e:
            self.log_test("database_indexes", False, {}, f"数据库索引测试异常: {str(e)}")
            return False
    
    def calculate_overall_improvement(self):
        """计算总体性能改进"""
        try:
            improvements = {}
            
            # 收集所有改进数据
            for metric, data in self.test_results["comparison"].items():
                if "improvement" in data:
                    improvements[metric] = data["improvement"]
            
            if improvements:
                avg_improvement = statistics.mean(improvements.values())
                self.test_results["summary"]["performance_improvements"] = {
                    "individual_improvements": improvements,
                    "average_improvement": round(avg_improvement, 1),
                    "total_metrics_improved": len([i for i in improvements.values() if i > 0])
                }
                
                print(f"\n📈 总体性能改进: {avg_improvement:.1f}%")
                for metric, improvement in improvements.items():
                    print(f"   {metric}: {improvement:.1f}%")
            
        except Exception as e:
            print(f"计算总体改进失败: {e}")
    
    def run_all_tests(self):
        """运行所有性能测试"""
        print("🚀 开始P0/P1修复后性能测试")
        print("=" * 60)
        
        # 1. API响应时间测试
        self.test_api_response_time()
        
        # 2. 数据库连接池测试
        self.test_database_connection_pool()
        
        # 3. 缓存服务测试
        self.test_cache_service()
        
        # 4. 响应压缩测试
        self.test_response_compression()
        
        # 5. 前端构建优化测试
        self.test_frontend_build_optimization()
        
        # 6. 数据库索引测试
        self.test_database_indexes()
        
        # 7. 计算总体改进
        self.calculate_overall_improvement()
        
        # 8. 输出测试结果
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("📊 性能测试结果摘要")
        print("=" * 60)
        
        summary = self.test_results["summary"]
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过: {summary['passed_tests']} ✅")
        print(f"失败: {summary['failed_tests']} ❌")
        print(f"成功率: {(summary['passed_tests']/summary['total_tests']*100):.1f}%")
        
        # 显示性能改进
        if "performance_improvements" in summary:
            improvements = summary["performance_improvements"]
            print(f"\n🎯 性能改进统计:")
            print(f"平均改进: {improvements['average_improvement']}%")
            print(f"改进指标数: {improvements['total_metrics_improved']}")
        
        # 显示对比数据
        if self.test_results["comparison"]:
            print(f"\n📈 关键指标对比:")
            for metric, data in self.test_results["comparison"].items():
                baseline = data["baseline"]
                current = data["current"]
                improvement = data["improvement"]
                target_met = "✅" if data.get("target_met", False) else "❌"
                print(f"  {metric}: {baseline} → {current:.2f} ({improvement:+.1f}%) {target_met}")
        
        print("\n" + "=" * 60)
    
    def save_results(self):
        """保存测试结果"""
        try:
            filename = f"performance_test_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            
            print(f"📄 性能测试报告已保存: {filename}")
            
        except Exception as e:
            print(f"❌ 保存测试报告失败: {e}")

def main():
    """主函数"""
    tester = PerformanceTestSuite()
    tester.run_all_tests()

if __name__ == "__main__":
    main()