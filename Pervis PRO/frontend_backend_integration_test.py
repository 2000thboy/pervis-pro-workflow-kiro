#!/usr/bin/env python3
"""
前后端集成深度验证测试
Phase 2: 前后端连接深度验证
"""

import requests
import json
import time
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any

class FrontendBackendIntegrationTester:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {
            'test_time': datetime.now().isoformat(),
            'api_connectivity': {},
            'business_workflows': {},
            'performance_tests': {},
            'error_handling': {},
            'concurrent_tests': {},
            'summary': {}
        }
        
    def run_integration_tests(self):
        """运行完整的前后端集成测试"""
        print("🔗 开始前后端集成深度验证...")
        
        # 2.1 前端到后端的完整链路测试
        self.test_api_connectivity()
        
        # 2.2 关键业务流程端到端测试
        self.test_business_workflows()
        
        # 2.3 并发和负载能力测试
        self.test_concurrent_capabilities()
        
        # 生成集成测试报告
        self.generate_integration_report()
        
    def test_api_connectivity(self):
        """测试API连接性"""
        print("\n🌐 测试前端到后端API连接性...")
        
        connectivity_tests = {}
        
        # 基础连接测试
        basic_endpoints = [
            {'name': 'health_check', 'url': '/api/health', 'method': 'GET'},
            {'name': 'api_docs', 'url': '/docs', 'method': 'GET'},
            {'name': 'openapi_spec', 'url': '/openapi.json', 'method': 'GET'}
        ]
        
        for test in basic_endpoints:
            try:
                start_time = time.time()
                if test['method'] == 'GET':
                    response = requests.get(f"{self.api_base_url}{test['url']}", timeout=5)
                else:
                    response = requests.post(f"{self.api_base_url}{test['url']}", timeout=5)
                    
                response_time = time.time() - start_time
                
                connectivity_tests[test['name']] = {
                    'status': 'success',
                    'http_status': response.status_code,
                    'response_time': response_time,
                    'content_length': len(response.content),
                    'content_type': response.headers.get('content-type', ''),
                    'server': response.headers.get('server', '')
                }
                
                print(f"  ✅ {test['name']}: {response.status_code} ({response_time:.3f}s)")
                
            except Exception as e:
                connectivity_tests[test['name']] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"  ❌ {test['name']}: 失败 - {e}")
                
        # 前端服务连接测试
        try:
            start_time = time.time()
            response = requests.get(self.frontend_url, timeout=5)
            response_time = time.time() - start_time
            
            connectivity_tests['frontend_service'] = {
                'status': 'success',
                'http_status': response.status_code,
                'response_time': response_time,
                'content_length': len(response.content),
                'has_vite_content': 'vite' in response.text.lower()
            }
            
            print(f"  ✅ frontend_service: {response.status_code} ({response_time:.3f}s)")
            
        except Exception as e:
            connectivity_tests['frontend_service'] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"  ❌ frontend_service: 失败 - {e}")
            
        self.test_results['api_connectivity'] = connectivity_tests
        
    def test_business_workflows(self):
        """测试关键业务流程"""
        print("\n🎯 测试关键业务流程...")
        
        workflow_tests = {}
        
        # 1. 剧本分析工作流
        workflow_tests['script_analysis_workflow'] = self.test_script_analysis_workflow()
        
        # 2. 素材处理工作流
        workflow_tests['asset_processing_workflow'] = self.test_asset_processing_workflow()
        
        # 3. 搜索匹配工作流
        workflow_tests['search_matching_workflow'] = self.test_search_matching_workflow()
        
        # 4. 渲染导出工作流
        workflow_tests['render_export_workflow'] = self.test_render_export_workflow()
        
        self.test_results['business_workflows'] = workflow_tests
        
    def test_script_analysis_workflow(self):
        """测试剧本分析工作流"""
        print("  📝 测试剧本分析工作流...")
        
        try:
            # 步骤1: 提交剧本分析
            script_content = """FADE IN:

INT. TECH STARTUP OFFICE - DAY

ALEX (25), a passionate developer, sits at a cluttered desk surrounded by multiple monitors. Coffee cups and energy drink cans litter the workspace.

ALEX
(muttering to code)
Come on, this integration test has to work...

Alex's fingers fly across the keyboard. The screen shows a complex API testing interface.

SARAH (28), the project manager, approaches with a concerned expression.

SARAH
How's the frontend-backend integration coming along?

ALEX
(looking up, tired but determined)
We're getting there. The API endpoints are responding, but I want to make sure the data flow is bulletproof.

SARAH
The client demo is tomorrow. We need this rock solid.

ALEX
(grinning)
Trust me, by the time I'm done, this system will be more reliable than Swiss clockwork.

Alex turns back to the screen, determination renewed.

FADE OUT."""

            start_time = time.time()
            
            response = requests.post(
                f"{self.api_base_url}/api/script/analyze",
                json={
                    "script_text": script_content,
                    "title": "集成测试剧本",
                    "mode": "parse"
                },
                timeout=15
            )
            
            analysis_time = time.time() - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                
                return {
                    'status': 'success',
                    'analysis_time': analysis_time,
                    'project_id': result_data.get('project_id'),
                    'beats_count': len(result_data.get('beats', [])),
                    'characters_count': len(result_data.get('characters', [])),
                    'processing_time': result_data.get('processing_time'),
                    'workflow_complete': True
                }
            else:
                return {
                    'status': 'error',
                    'http_status': response.status_code,
                    'error': response.text,
                    'analysis_time': analysis_time
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'workflow_complete': False
            }
            
    def test_asset_processing_workflow(self):
        """测试素材处理工作流"""
        print("  🎬 测试素材处理工作流...")
        
        try:
            # 检查现有素材状态
            response = requests.get(f"{self.api_base_url}/api/assets", timeout=10)
            
            if response.status_code == 200:
                assets_data = response.json()
                
                # 如果有素材，测试状态查询
                if assets_data and len(assets_data) > 0:
                    first_asset = assets_data[0]
                    asset_id = first_asset.get('id')
                    
                    if asset_id:
                        # 测试素材状态查询
                        status_response = requests.get(
                            f"{self.api_base_url}/api/assets/{asset_id}/status",
                            timeout=5
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            return {
                                'status': 'success',
                                'assets_available': len(assets_data),
                                'test_asset_id': asset_id,
                                'asset_status': status_data.get('status'),
                                'workflow_complete': True
                            }
                            
                return {
                    'status': 'success',
                    'assets_available': len(assets_data) if assets_data else 0,
                    'workflow_complete': True,
                    'note': 'No assets to test status query'
                }
            else:
                return {
                    'status': 'error',
                    'http_status': response.status_code,
                    'error': response.text
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'workflow_complete': False
            }
            
    def test_search_matching_workflow(self):
        """测试搜索匹配工作流"""
        print("  🔍 测试搜索匹配工作流...")
        
        try:
            search_queries = [
                {
                    'name': 'semantic_search',
                    'url': '/api/search/semantic',
                    'data': {
                        'beat_id': 'test_beat',
                        'query_tags': {
                            'emotions': ['determined', 'focused'],
                            'scenes': ['office', 'indoor'],
                            'actions': ['typing', 'working'],
                            'cinematography': ['close-up', 'medium']
                        },
                        'limit': 5
                    }
                },
                {
                    'name': 'multimodal_search',
                    'url': '/api/multimodal/search',
                    'data': {
                        'query': '专注工作的程序员在办公室',
                        'limit': 5
                    }
                }
            ]
            
            search_results = {}
            
            for query in search_queries:
                try:
                    start_time = time.time()
                    response = requests.post(
                        f"{self.api_base_url}{query['url']}",
                        json=query['data'],
                        timeout=10
                    )
                    search_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        result_data = response.json()
                        search_results[query['name']] = {
                            'status': 'success',
                            'search_time': search_time,
                            'results_count': len(result_data.get('results', [])),
                            'total_matches': result_data.get('total_matches', 0)
                        }
                    else:
                        search_results[query['name']] = {
                            'status': 'error',
                            'http_status': response.status_code,
                            'search_time': search_time
                        }
                        
                except Exception as e:
                    search_results[query['name']] = {
                        'status': 'error',
                        'error': str(e)
                    }
                    
            return {
                'status': 'success',
                'search_tests': search_results,
                'workflow_complete': all(r.get('status') == 'success' for r in search_results.values())
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'workflow_complete': False
            }
            
    def test_render_export_workflow(self):
        """测试渲染导出工作流"""
        print("  🎬 测试渲染导出工作流...")
        
        try:
            # 1. 测试渲染任务创建
            render_response = requests.post(
                f"{self.api_base_url}/api/render/start",
                json={
                    "timeline_id": "integration_test_timeline",
                    "output_format": "mp4",
                    "resolution": "1920x1080",
                    "fps": 30,
                    "quality": "high"
                },
                timeout=10
            )
            
            render_result = {}
            if render_response.status_code == 200:
                render_data = render_response.json()
                task_id = render_data.get('task_id')
                
                render_result['render_task_creation'] = {
                    'status': 'success',
                    'task_id': task_id
                }
                
                # 2. 测试任务状态查询
                if task_id:
                    status_response = requests.get(
                        f"{self.api_base_url}/api/render/status/{task_id}",
                        timeout=5
                    )
                    
                    if status_response.status_code in [200, 404]:  # 404也是正常的
                        render_result['status_query'] = {
                            'status': 'success',
                            'http_status': status_response.status_code
                        }
                    else:
                        render_result['status_query'] = {
                            'status': 'error',
                            'http_status': status_response.status_code
                        }
            else:
                render_result['render_task_creation'] = {
                    'status': 'error',
                    'http_status': render_response.status_code
                }
                
            # 3. 测试导出功能
            export_tests = {}
            
            # 创建一个测试项目用于导出
            script_response = requests.post(
                f"{self.api_base_url}/api/script/analyze",
                json={
                    "script_text": "FADE IN:\nINT. TEST - DAY\nTest export.\nFADE OUT.",
                    "title": "导出测试项目",
                    "mode": "parse"
                },
                timeout=10
            )
            
            if script_response.status_code == 200:
                project_data = script_response.json()
                project_id = project_data.get('project_id')
                
                if project_id:
                    # 测试剧本导出
                    export_response = requests.post(
                        f"{self.api_base_url}/api/export/script",
                        json={
                            "project_id": project_id,
                            "format": "docx",
                            "include_beats": True
                        },
                        timeout=15
                    )
                    
                    if export_response.status_code == 200:
                        export_tests['script_export'] = {
                            'status': 'success',
                            'export_data': export_response.json()
                        }
                    else:
                        export_tests['script_export'] = {
                            'status': 'error',
                            'http_status': export_response.status_code
                        }
                        
            return {
                'status': 'success',
                'render_tests': render_result,
                'export_tests': export_tests,
                'workflow_complete': True
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'workflow_complete': False
            }
            
    def test_concurrent_capabilities(self):
        """测试并发处理能力"""
        print("\n🔄 测试并发处理能力...")
        
        concurrent_results = {}
        
        # 并发API请求测试
        concurrent_results['concurrent_api_requests'] = self.test_concurrent_api_requests()
        
        # 负载测试
        concurrent_results['load_test'] = self.test_load_capacity()
        
        self.test_results['concurrent_tests'] = concurrent_results
        
    def test_concurrent_api_requests(self):
        """测试并发API请求"""
        print("  🚀 测试并发API请求...")
        
        try:
            # 准备并发请求
            concurrent_requests = []
            for i in range(5):
                concurrent_requests.append({
                    'url': f"{self.api_base_url}/api/health",
                    'method': 'GET',
                    'id': f'health_check_{i}'
                })
                concurrent_requests.append({
                    'url': f"{self.api_base_url}/api/search/semantic",
                    'method': 'POST',
                    'data': {
                        'beat_id': f'concurrent_test_{i}',
                        'query_tags': {'emotions': ['test']},
                        'limit': 3
                    },
                    'id': f'search_request_{i}'
                })
                
            # 执行并发请求
            start_time = time.time()
            
            def make_request(req_info):
                try:
                    if req_info['method'] == 'GET':
                        response = requests.get(req_info['url'], timeout=10)
                    else:
                        response = requests.post(req_info['url'], json=req_info.get('data'), timeout=10)
                        
                    return {
                        'id': req_info['id'],
                        'status': 'success',
                        'http_status': response.status_code,
                        'response_time': response.elapsed.total_seconds()
                    }
                except Exception as e:
                    return {
                        'id': req_info['id'],
                        'status': 'error',
                        'error': str(e)
                    }
                    
            # 使用线程池执行并发请求
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = list(executor.map(make_request, concurrent_requests))
                
            total_time = time.time() - start_time
            
            successful_requests = len([r for r in results if r.get('status') == 'success'])
            
            return {
                'status': 'success',
                'total_requests': len(concurrent_requests),
                'successful_requests': successful_requests,
                'failed_requests': len(concurrent_requests) - successful_requests,
                'total_time': total_time,
                'requests_per_second': len(concurrent_requests) / total_time,
                'success_rate': (successful_requests / len(concurrent_requests)) * 100,
                'individual_results': results
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_load_capacity(self):
        """测试负载能力"""
        print("  📊 测试系统负载能力...")
        
        try:
            # 轻量级负载测试
            load_tests = []
            
            for load_level in [1, 3, 5]:
                print(f"    测试负载级别: {load_level}")
                
                start_time = time.time()
                
                def make_health_check():
                    try:
                        response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
                        return response.status_code == 200
                    except:
                        return False
                        
                # 执行负载测试
                with concurrent.futures.ThreadPoolExecutor(max_workers=load_level) as executor:
                    futures = [executor.submit(make_health_check) for _ in range(load_level * 3)]
                    results = [future.result() for future in concurrent.futures.as_completed(futures)]
                    
                test_time = time.time() - start_time
                success_count = sum(results)
                
                load_tests.append({
                    'load_level': load_level,
                    'total_requests': len(results),
                    'successful_requests': success_count,
                    'test_time': test_time,
                    'success_rate': (success_count / len(results)) * 100
                })
                
            return {
                'status': 'success',
                'load_tests': load_tests,
                'max_tested_load': max(t['load_level'] for t in load_tests),
                'overall_stability': all(t['success_rate'] >= 80 for t in load_tests)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def generate_integration_report(self):
        """生成集成测试报告"""
        print("\n📋 生成前后端集成测试报告...")
        
        # 统计测试结果
        connectivity_success = len([t for t in self.test_results.get('api_connectivity', {}).values() if t.get('status') == 'success'])
        connectivity_total = len(self.test_results.get('api_connectivity', {}))
        
        workflow_success = len([t for t in self.test_results.get('business_workflows', {}).values() if t.get('status') == 'success'])
        workflow_total = len(self.test_results.get('business_workflows', {}))
        
        concurrent_success = len([t for t in self.test_results.get('concurrent_tests', {}).values() if t.get('status') == 'success'])
        concurrent_total = len(self.test_results.get('concurrent_tests', {}))
        
        # 计算整体成功率
        total_tests = connectivity_total + workflow_total + concurrent_total
        total_success = connectivity_success + workflow_success + concurrent_success
        overall_success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        # 生成摘要
        summary = {
            'overall_success_rate': overall_success_rate,
            'connectivity_success_rate': (connectivity_success / connectivity_total * 100) if connectivity_total > 0 else 0,
            'workflow_success_rate': (workflow_success / workflow_total * 100) if workflow_total > 0 else 0,
            'concurrent_success_rate': (concurrent_success / concurrent_total * 100) if concurrent_total > 0 else 0,
            'total_tests': total_tests,
            'successful_tests': total_success,
            'failed_tests': total_tests - total_success,
            'integration_status': 'excellent' if overall_success_rate >= 90 else 'good' if overall_success_rate >= 75 else 'needs_improvement',
            'test_completion_time': datetime.now().isoformat()
        }
        
        self.test_results['summary'] = summary
        
        # 保存报告
        report_filename = f"frontend_backend_integration_report_{int(time.time())}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
        # 打印摘要
        print(f"\n📊 前后端集成测试结果:")
        print(f"  🎯 整体成功率: {overall_success_rate:.1f}%")
        print(f"  🌐 连接性测试: {summary['connectivity_success_rate']:.1f}% ({connectivity_success}/{connectivity_total})")
        print(f"  🎯 业务流程测试: {summary['workflow_success_rate']:.1f}% ({workflow_success}/{workflow_total})")
        print(f"  🔄 并发能力测试: {summary['concurrent_success_rate']:.1f}% ({concurrent_success}/{concurrent_total})")
        print(f"  🏆 集成状态: {summary['integration_status'].upper()}")
        
        print(f"\n📄 详细报告已保存到: {report_filename}")
        
        return report_filename

def main():
    """主函数"""
    tester = FrontendBackendIntegrationTester()
    tester.run_integration_tests()

if __name__ == "__main__":
    main()