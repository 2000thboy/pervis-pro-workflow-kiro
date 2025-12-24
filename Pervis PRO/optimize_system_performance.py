#!/usr/bin/env python3
"""
系统性能优化脚本
根据稳定性报告中的建议进行性能优化
"""

import asyncio
import json
import time
import requests
from pathlib import Path
import sys
from typing import Dict, List, Any

class PerformanceOptimizer:
    """系统性能优化器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.optimization_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "optimizations": {},
            "performance_metrics": {},
            "recommendations": []
        }
    
    def log_optimization(self, name: str, success: bool, message: str, details: Dict = None):
        """记录优化结果"""
        self.optimization_results["optimizations"][name] = {
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.strftime("%H:%M:%S")
        }
        
        status = "✅" if success else "❌"
        print(f"{status} {name}: {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")
    
    def measure_api_performance(self):
        """测量API性能"""
        try:
            endpoints = [
                "/api/health",
                "/api/projects",
                "/api/batch/queue/status",
                "/api/batch/stats"
            ]
            
            performance_data = {}
            
            for endpoint in endpoints:
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000  # ms
                    performance_data[endpoint] = {
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    }
                    
                except Exception as e:
                    performance_data[endpoint] = {
                        "response_time_ms": -1,
                        "status_code": -1,
                        "success": False,
                        "error": str(e)
                    }
            
            # 计算平均响应时间
            successful_times = [
                data["response_time_ms"] 
                for data in performance_data.values() 
                if data["success"] and data["response_time_ms"] > 0
            ]
            
            avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
            
            self.optimization_results["performance_metrics"]["api_performance"] = {
                "average_response_time_ms": avg_response_time,
                "endpoints": performance_data,
                "successful_endpoints": len([d for d in performance_data.values() if d["success"]])
            }
            
            self.log_optimization(
                "api_performance_measurement",
                True,
                f"API性能测量完成，平均响应时间: {avg_response_time:.2f}ms",
                {"endpoints_tested": len(endpoints), "successful": len(successful_times)}
            )
            
            return avg_response_time
            
        except Exception as e:
            self.log_optimization(
                "api_performance_measurement",
                False,
                f"API性能测量失败: {str(e)}"
            )
            return -1
    
    def optimize_database_connections(self):
        """优化数据库连接"""
        try:
            # 检查数据库配置文件
            backend_config_files = [
                "backend/app/config.py",
                "backend/database.py"
            ]
            
            optimizations_applied = []
            
            for config_file in backend_config_files:
                if Path(config_file).exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查是否已经有连接池配置
                    if "pool_size" not in content and "sqlite" not in content.lower():
                        optimizations_applied.append(f"建议在{config_file}中添加连接池配置")
                    
                    # 检查是否启用了调试模式
                    if "debug=True" in content or "echo=True" in content:
                        optimizations_applied.append(f"建议在生产环境中关闭{config_file}的调试模式")
            
            self.log_optimization(
                "database_optimization",
                True,
                f"数据库配置检查完成",
                {"suggestions": optimizations_applied}
            )
            
            if optimizations_applied:
                self.optimization_results["recommendations"].extend(optimizations_applied)
            
        except Exception as e:
            self.log_optimization(
                "database_optimization",
                False,
                f"数据库优化检查失败: {str(e)}"
            )
    
    def optimize_frontend_assets(self):
        """优化前端资源"""
        try:
            frontend_files = [
                "frontend/package.json",
                "frontend/vite.config.ts",
                "frontend/tsconfig.json"
            ]
            
            optimizations = []
            
            # 检查package.json中的依赖
            package_json_path = Path("frontend/package.json")
            if package_json_path.exists():
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # 检查是否有开发依赖在生产环境中
                dev_deps = package_data.get("devDependencies", {})
                deps = package_data.get("dependencies", {})
                
                # 建议优化
                if len(deps) > 20:
                    optimizations.append("考虑使用代码分割减少bundle大小")
                
                if "react-dev-tools" in deps:
                    optimizations.append("将react-dev-tools移至devDependencies")
            
            # 检查是否有构建优化配置
            vite_config_path = Path("frontend/vite.config.ts")
            if vite_config_path.exists():
                with open(vite_config_path, 'r', encoding='utf-8') as f:
                    vite_content = f.read()
                
                if "build.rollupOptions" not in vite_content:
                    optimizations.append("建议在vite.config.ts中添加构建优化配置")
                
                if "build.minify" not in vite_content:
                    optimizations.append("建议启用代码压缩")
            
            self.log_optimization(
                "frontend_optimization",
                True,
                f"前端资源优化检查完成",
                {"suggestions": optimizations}
            )
            
            self.optimization_results["recommendations"].extend(optimizations)
            
        except Exception as e:
            self.log_optimization(
                "frontend_optimization",
                False,
                f"前端优化检查失败: {str(e)}"
            )
    
    def check_system_resources(self):
        """检查系统资源使用"""
        try:
            import psutil
            
            # 获取系统资源信息
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            resource_data = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }
            
            # 生成建议
            suggestions = []
            if cpu_percent > 80:
                suggestions.append("CPU使用率过高，建议优化计算密集型任务")
            
            if memory.percent > 80:
                suggestions.append("内存使用率过高，建议优化内存使用")
            
            if disk.percent > 90:
                suggestions.append("磁盘空间不足，建议清理临时文件")
            
            self.optimization_results["performance_metrics"]["system_resources"] = resource_data
            
            self.log_optimization(
                "system_resources_check",
                True,
                f"系统资源检查完成",
                resource_data
            )
            
            if suggestions:
                self.optimization_results["recommendations"].extend(suggestions)
            
        except ImportError:
            self.log_optimization(
                "system_resources_check",
                False,
                "psutil未安装，无法检查系统资源"
            )
        except Exception as e:
            self.log_optimization(
                "system_resources_check",
                False,
                f"系统资源检查失败: {str(e)}"
            )
    
    def optimize_mock_services(self):
        """优化Mock服务配置"""
        try:
            mock_services = [
                "backend/services/audio_transcriber.py",
                "backend/services/visual_processor.py",
                "backend/services/semantic_search.py"
            ]
            
            mock_status = {}
            
            for service_file in mock_services:
                if Path(service_file).exists():
                    with open(service_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    is_mock = "FORCE_MOCK_MODE = True" in content
                    mock_status[service_file] = is_mock
            
            # 检查是否所有服务都在Mock模式
            all_mock = all(mock_status.values())
            
            if all_mock:
                suggestion = "所有AI服务都在Mock模式，这有助于性能但限制了功能。考虑在需要时启用真实服务。"
                self.optimization_results["recommendations"].append(suggestion)
            
            self.log_optimization(
                "mock_services_optimization",
                True,
                f"Mock服务配置检查完成",
                {"mock_services": mock_status, "all_mock": all_mock}
            )
            
        except Exception as e:
            self.log_optimization(
                "mock_services_optimization",
                False,
                f"Mock服务优化检查失败: {str(e)}"
            )
    
    def generate_performance_recommendations(self):
        """生成性能优化建议"""
        try:
            # 基于测量结果生成建议
            api_perf = self.optimization_results["performance_metrics"].get("api_performance", {})
            avg_response_time = api_perf.get("average_response_time_ms", 0)
            
            if avg_response_time > 1000:  # 超过1秒
                self.optimization_results["recommendations"].extend([
                    "API响应时间过长，建议启用数据库连接池",
                    "考虑添加Redis缓存以减少数据库查询",
                    "优化数据库查询，添加必要的索引",
                    "考虑使用异步处理减少阻塞操作"
                ])
            elif avg_response_time > 500:  # 超过500ms
                self.optimization_results["recommendations"].extend([
                    "API响应时间偏长，建议优化数据库查询",
                    "考虑添加适当的缓存机制"
                ])
            
            # 通用优化建议
            general_recommendations = [
                "定期清理临时文件和日志文件",
                "监控系统资源使用情况",
                "考虑使用CDN加速静态资源",
                "启用gzip压缩减少传输大小",
                "使用HTTP/2提升网络性能"
            ]
            
            self.optimization_results["recommendations"].extend(general_recommendations)
            
            self.log_optimization(
                "performance_recommendations",
                True,
                f"生成了 {len(self.optimization_results['recommendations'])} 条优化建议"
            )
            
        except Exception as e:
            self.log_optimization(
                "performance_recommendations",
                False,
                f"生成性能建议失败: {str(e)}"
            )
    
    def run_optimization_analysis(self):
        """运行完整的性能优化分析"""
        print("🚀 开始系统性能优化分析")
        print("=" * 60)
        
        # 1. 测量API性能
        self.measure_api_performance()
        
        # 2. 检查数据库配置
        self.optimize_database_connections()
        
        # 3. 检查前端资源
        self.optimize_frontend_assets()
        
        # 4. 检查系统资源
        self.check_system_resources()
        
        # 5. 检查Mock服务
        self.optimize_mock_services()
        
        # 6. 生成优化建议
        self.generate_performance_recommendations()
        
        # 7. 输出结果
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """打印优化摘要"""
        print("\n" + "=" * 60)
        print("📊 性能优化分析结果")
        print("=" * 60)
        
        # 统计优化项目
        optimizations = self.optimization_results["optimizations"]
        total = len(optimizations)
        successful = len([o for o in optimizations.values() if o["success"]])
        
        print(f"检查项目: {total}")
        print(f"成功: {successful} ✅")
        print(f"失败: {total - successful} ❌")
        
        # 显示性能指标
        api_perf = self.optimization_results["performance_metrics"].get("api_performance", {})
        if api_perf:
            avg_time = api_perf.get("average_response_time_ms", 0)
            print(f"平均API响应时间: {avg_time:.2f}ms")
        
        # 显示建议数量
        recommendations = self.optimization_results["recommendations"]
        print(f"优化建议: {len(recommendations)} 条")
        
        if recommendations:
            print("\n🔧 主要优化建议:")
            for i, rec in enumerate(recommendations[:5], 1):  # 显示前5条
                print(f"  {i}. {rec}")
            
            if len(recommendations) > 5:
                print(f"  ... 还有 {len(recommendations) - 5} 条建议")
        
        print("\n" + "=" * 60)
    
    def save_results(self):
        """保存优化结果"""
        try:
            filename = f"performance_optimization_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.optimization_results, f, ensure_ascii=False, indent=2)
            
            print(f"📄 优化报告已保存: {filename}")
            
        except Exception as e:
            print(f"❌ 保存优化报告失败: {e}")

def main():
    """主函数"""
    optimizer = PerformanceOptimizer()
    optimizer.run_optimization_analysis()

if __name__ == "__main__":
    main()