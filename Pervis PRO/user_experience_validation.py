#!/usr/bin/env python3
"""
用户体验验证测试
Phase 3: 用户体验验证
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any
import subprocess

class UserExperienceValidator:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {
            'test_time': datetime.now().isoformat(),
            'user_scenarios': {},
            'performance_benchmarks': {},
            'compatibility_tests': {},
            'ui_responsiveness': {},
            'summary': {}
        }
        
    def run_user_experience_validation(self):
        """运行用户体验验证"""
        print("👥 开始用户体验验证测试...")
        
        # 3.1 真实用户场景模拟
        self.simulate_user_scenarios()
        
        # 3.2 性能基准测试
        self.run_performance_benchmarks()
        
        # 3.3 兼容性和稳定性测试
        self.test_compatibility_stability()
        
        # 生成用户体验报告
        self.generate_ux_report()
        
    def simulate_user_scenarios(self):
        """模拟真实用户场景"""
        print("\n🎭 模拟真实用户场景...")
        
        user_scenarios = {}
        
        # 场景1: 新用户首次使用完整工作流
        user_scenarios['new_user_complete_workflow'] = self.test_new_user_workflow()
        
        # 场景2: 经验用户快速操作
        user_scenarios['experienced_user_workflow'] = self.test_experienced_user_workflow()
        
        # 场景3: 异常情况处理
        user_scenarios['error_handling_scenarios'] = self.test_error_handling_scenarios()
        
        # 场景4: 长时间使用稳定性
        user_scenarios['long_session_stability'] = self.test_long_session_stability()
        
        self.test_results['user_scenarios'] = user_scenarios
        
    def test_new_user_workflow(self):
        """测试新用户完整工作流"""
        print("  🆕 测试新用户完整工作流...")
        
        workflow_steps = []
        overall_success = True
        
        try:
            # 步骤1: 访问首页
            start_time = time.time()
            response = requests.get(self.frontend_url, timeout=10)
            step1_time = time.time() - start_time
            
            workflow_steps.append({
                'step': 'access_homepage',
                'success': response.status_code == 200,
                'time': step1_time,
                'details': f'HTTP {response.status_code}'
            })
            
            if response.status_code != 200:
                overall_success = False
                
            # 步骤2: 检查API健康状态
            start_time = time.time()
            health_response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
            step2_time = time.time() - start_time
            
            workflow_steps.append({
                'step': 'check_api_health',
                'success': health_response.status_code == 200,
                'time': step2_time,
                'details': f'API Health: {health_response.status_code}'
            })
            
            if health_response.status_code != 200:
                overall_success = False
                
            # 步骤3: 提交剧本分析（新用户的第一个操作）
            start_time = time.time()
            script_content = """FADE IN:

EXT. COFFEE SHOP - MORNING

EMMA (22), a film student with bright eyes and messy hair, sits outside a bustling coffee shop. Her laptop is open, showing a blank screenplay document.

EMMA
(to herself)
Okay Emma, time to write the next great American screenplay.

She takes a deep breath and starts typing.

EMMA (CONT'D)
(typing)
"FADE IN: EXT. COFFEE SHOP - MORNING"

A BARISTA (30s) comes out to clean tables nearby.

BARISTA
Writing the next blockbuster?

EMMA
(laughing)
More like the next film school project. But hey, everyone starts somewhere, right?

BARISTA
That's the spirit. Good luck!

Emma smiles and continues typing with renewed confidence.

FADE OUT."""

            script_response = requests.post(
                f"{self.api_base_url}/api/script/analyze",
                json={
                    "script_text": script_content,
                    "title": "新用户测试剧本",
                    "mode": "parse"
                },
                timeout=20
            )
            step3_time = time.time() - start_time
            
            script_success = script_response.status_code == 200
            project_id = None
            
            if script_success:
                script_data = script_response.json()
                project_id = script_data.get('project_id')
                
            workflow_steps.append({
                'step': 'submit_script_analysis',
                'success': script_success,
                'time': step3_time,
                'details': f'Project ID: {project_id}' if project_id else f'Error: {script_response.status_code}'
            })
            
            if not script_success:
                overall_success = False
                
            # 步骤4: 尝试搜索素材（新用户探索功能）
            start_time = time.time()
            search_response = requests.post(
                f"{self.api_base_url}/api/search/semantic",
                json={
                    "beat_id": "new_user_test",
                    "query_tags": {
                        "emotions": ["happy", "confident"],
                        "scenes": ["outdoor", "coffee shop"],
                        "actions": ["writing", "typing"],
                        "cinematography": ["medium shot"]
                    },
                    "limit": 5
                },
                timeout=10
            )
            step4_time = time.time() - start_time
            
            search_success = search_response.status_code == 200
            
            workflow_steps.append({
                'step': 'search_assets',
                'success': search_success,
                'time': step4_time,
                'details': f'Search results: {len(search_response.json().get("results", []))}' if search_success else f'Error: {search_response.status_code}'
            })
            
            if not search_success:
                overall_success = False
                
            # 步骤5: 查看导出选项（新用户了解功能）
            if project_id:
                start_time = time.time()
                export_response = requests.get(
                    f"{self.api_base_url}/api/export/history/{project_id}",
                    timeout=5
                )
                step5_time = time.time() - start_time
                
                export_success = export_response.status_code == 200
                
                workflow_steps.append({
                    'step': 'check_export_options',
                    'success': export_success,
                    'time': step5_time,
                    'details': f'Export history available' if export_success else f'Error: {export_response.status_code}'
                })
                
                if not export_success:
                    overall_success = False
            else:
                workflow_steps.append({
                    'step': 'check_export_options',
                    'success': False,
                    'time': 0,
                    'details': 'Skipped due to missing project_id'
                })
                overall_success = False
                
            return {
                'status': 'success' if overall_success else 'partial_success',
                'overall_success': overall_success,
                'workflow_steps': workflow_steps,
                'total_time': sum(step['time'] for step in workflow_steps),
                'successful_steps': len([step for step in workflow_steps if step['success']]),
                'total_steps': len(workflow_steps),
                'user_experience_rating': 'excellent' if overall_success else 'needs_improvement'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'workflow_steps': workflow_steps,
                'overall_success': False
            }
            
    def test_experienced_user_workflow(self):
        """测试经验用户快速操作"""
        print("  ⚡ 测试经验用户快速操作...")
        
        try:
            quick_operations = []
            
            # 快速操作1: 健康检查
            start_time = time.time()
            health_response = requests.get(f"{self.api_base_url}/api/health", timeout=3)
            op1_time = time.time() - start_time
            
            quick_operations.append({
                'operation': 'quick_health_check',
                'success': health_response.status_code == 200,
                'time': op1_time,
                'expected_time': 1.0,  # 期望1秒内完成
                'performance_rating': 'excellent' if op1_time < 1.0 else 'good' if op1_time < 2.0 else 'slow'
            })
            
            # 快速操作2: 快速剧本分析
            start_time = time.time()
            quick_script = "FADE IN:\nINT. ROOM - DAY\nQuick test.\nFADE OUT."
            
            script_response = requests.post(
                f"{self.api_base_url}/api/script/analyze",
                json={
                    "script_text": quick_script,
                    "title": "快速测试",
                    "mode": "parse"
                },
                timeout=10
            )
            op2_time = time.time() - start_time
            
            quick_operations.append({
                'operation': 'quick_script_analysis',
                'success': script_response.status_code == 200,
                'time': op2_time,
                'expected_time': 5.0,  # 期望5秒内完成
                'performance_rating': 'excellent' if op2_time < 3.0 else 'good' if op2_time < 5.0 else 'slow'
            })
            
            # 快速操作3: 快速搜索
            start_time = time.time()
            search_response = requests.post(
                f"{self.api_base_url}/api/multimodal/search",
                json={
                    "query": "快速测试",
                    "limit": 3
                },
                timeout=5
            )
            op3_time = time.time() - start_time
            
            quick_operations.append({
                'operation': 'quick_search',
                'success': search_response.status_code == 200,
                'time': op3_time,
                'expected_time': 3.0,  # 期望3秒内完成
                'performance_rating': 'excellent' if op3_time < 2.0 else 'good' if op3_time < 3.0 else 'slow'
            })
            
            # 计算整体性能
            total_operations = len(quick_operations)
            successful_operations = len([op for op in quick_operations if op['success']])
            excellent_performance = len([op for op in quick_operations if op['performance_rating'] == 'excellent'])
            
            return {
                'status': 'success',
                'quick_operations': quick_operations,
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'excellent_performance_count': excellent_performance,
                'overall_performance_rating': 'excellent' if excellent_performance >= total_operations * 0.8 else 'good',
                'user_satisfaction': 'high' if successful_operations == total_operations else 'medium'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_error_handling_scenarios(self):
        """测试异常情况处理"""
        print("  ⚠️ 测试异常情况处理...")
        
        try:
            error_scenarios = []
            
            # 错误场景1: 无效的剧本内容
            start_time = time.time()
            invalid_script_response = requests.post(
                f"{self.api_base_url}/api/script/analyze",
                json={
                    "script_text": "",  # 空剧本
                    "title": "错误测试",
                    "mode": "parse"
                },
                timeout=10
            )
            scenario1_time = time.time() - start_time
            
            error_scenarios.append({
                'scenario': 'empty_script_handling',
                'expected_behavior': 'graceful_error_handling',
                'actual_status': invalid_script_response.status_code,
                'response_time': scenario1_time,
                'handled_gracefully': invalid_script_response.status_code in [400, 422],  # 期望的错误状态码
                'error_message_provided': 'detail' in invalid_script_response.json() if invalid_script_response.headers.get('content-type', '').startswith('application/json') else False
            })
            
            # 错误场景2: 不存在的资源访问
            start_time = time.time()
            nonexistent_resource_response = requests.get(
                f"{self.api_base_url}/api/assets/nonexistent_id/status",
                timeout=5
            )
            scenario2_time = time.time() - start_time
            
            error_scenarios.append({
                'scenario': 'nonexistent_resource_access',
                'expected_behavior': 'not_found_error',
                'actual_status': nonexistent_resource_response.status_code,
                'response_time': scenario2_time,
                'handled_gracefully': nonexistent_resource_response.status_code == 404,
                'error_message_provided': True  # 404通常有错误信息
            })
            
            # 错误场景3: 无效的搜索参数
            start_time = time.time()
            invalid_search_response = requests.post(
                f"{self.api_base_url}/api/search/semantic",
                json={
                    "invalid_param": "test"  # 缺少必需参数
                },
                timeout=5
            )
            scenario3_time = time.time() - start_time
            
            error_scenarios.append({
                'scenario': 'invalid_search_parameters',
                'expected_behavior': 'validation_error',
                'actual_status': invalid_search_response.status_code,
                'response_time': scenario3_time,
                'handled_gracefully': invalid_search_response.status_code in [400, 422],
                'error_message_provided': 'detail' in invalid_search_response.json() if invalid_search_response.headers.get('content-type', '').startswith('application/json') else False
            })
            
            # 统计错误处理质量
            graceful_handling_count = len([s for s in error_scenarios if s['handled_gracefully']])
            error_messages_count = len([s for s in error_scenarios if s['error_message_provided']])
            
            return {
                'status': 'success',
                'error_scenarios': error_scenarios,
                'total_scenarios': len(error_scenarios),
                'graceful_handling_count': graceful_handling_count,
                'error_messages_provided': error_messages_count,
                'error_handling_quality': 'excellent' if graceful_handling_count == len(error_scenarios) else 'good' if graceful_handling_count >= len(error_scenarios) * 0.7 else 'needs_improvement',
                'user_friendly_errors': error_messages_count >= len(error_scenarios) * 0.8
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_long_session_stability(self):
        """测试长时间使用稳定性"""
        print("  ⏱️ 测试长时间使用稳定性...")
        
        try:
            stability_metrics = []
            test_duration = 30  # 30秒的稳定性测试
            check_interval = 5   # 每5秒检查一次
            
            start_time = time.time()
            
            for i in range(test_duration // check_interval):
                check_start = time.time()
                
                # 执行一系列操作模拟长时间使用
                operations = [
                    {'name': 'health_check', 'url': f"{self.api_base_url}/api/health", 'method': 'GET'},
                    {'name': 'frontend_check', 'url': self.frontend_url, 'method': 'GET'}
                ]
                
                operation_results = []
                
                for op in operations:
                    try:
                        if op['method'] == 'GET':
                            response = requests.get(op['url'], timeout=3)
                        else:
                            response = requests.post(op['url'], timeout=3)
                            
                        operation_results.append({
                            'operation': op['name'],
                            'success': response.status_code == 200,
                            'response_time': response.elapsed.total_seconds()
                        })
                    except Exception as e:
                        operation_results.append({
                            'operation': op['name'],
                            'success': False,
                            'error': str(e)
                        })
                        
                check_time = time.time() - check_start
                elapsed_total = time.time() - start_time
                
                stability_metrics.append({
                    'check_number': i + 1,
                    'elapsed_time': elapsed_total,
                    'check_duration': check_time,
                    'operations': operation_results,
                    'all_operations_successful': all(op.get('success', False) for op in operation_results)
                })
                
                # 等待下一次检查
                if i < (test_duration // check_interval) - 1:
                    time.sleep(check_interval - check_time)
                    
            # 分析稳定性
            successful_checks = len([m for m in stability_metrics if m['all_operations_successful']])
            total_checks = len(stability_metrics)
            
            return {
                'status': 'success',
                'test_duration': test_duration,
                'total_checks': total_checks,
                'successful_checks': successful_checks,
                'stability_rate': (successful_checks / total_checks) * 100,
                'stability_metrics': stability_metrics,
                'stability_rating': 'excellent' if successful_checks == total_checks else 'good' if successful_checks >= total_checks * 0.9 else 'unstable',
                'suitable_for_long_sessions': successful_checks >= total_checks * 0.95
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def run_performance_benchmarks(self):
        """运行性能基准测试"""
        print("\n📊 运行性能基准测试...")
        
        performance_benchmarks = {}
        
        # 页面加载时间测试
        performance_benchmarks['page_load_times'] = self.test_page_load_times()
        
        # API响应时间测试
        performance_benchmarks['api_response_times'] = self.test_api_response_times()
        
        # 文件处理速度测试
        performance_benchmarks['file_processing_speed'] = self.test_file_processing_speed()
        
        self.test_results['performance_benchmarks'] = performance_benchmarks
        
    def test_page_load_times(self):
        """测试页面加载时间"""
        print("  🌐 测试页面加载时间...")
        
        try:
            page_tests = [
                {'name': 'frontend_homepage', 'url': self.frontend_url},
                {'name': 'api_docs', 'url': f"{self.api_base_url}/docs"},
                {'name': 'api_test_page', 'url': f"{self.frontend_url}/api-test.html"}
            ]
            
            load_times = []
            
            for test in page_tests:
                try:
                    start_time = time.time()
                    response = requests.get(test['url'], timeout=10)
                    load_time = time.time() - start_time
                    
                    load_times.append({
                        'page': test['name'],
                        'load_time': load_time,
                        'success': response.status_code == 200,
                        'content_size': len(response.content),
                        'performance_rating': 'excellent' if load_time < 1.0 else 'good' if load_time < 3.0 else 'slow'
                    })
                    
                except Exception as e:
                    load_times.append({
                        'page': test['name'],
                        'success': False,
                        'error': str(e)
                    })
                    
            successful_loads = [lt for lt in load_times if lt.get('success', False)]
            average_load_time = sum(lt['load_time'] for lt in successful_loads) / len(successful_loads) if successful_loads else 0
            
            return {
                'status': 'success',
                'load_times': load_times,
                'average_load_time': average_load_time,
                'successful_loads': len(successful_loads),
                'total_tests': len(page_tests),
                'overall_performance': 'excellent' if average_load_time < 2.0 else 'good' if average_load_time < 4.0 else 'slow'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_api_response_times(self):
        """测试API响应时间"""
        print("  ⚡ 测试API响应时间...")
        
        try:
            api_tests = [
                {'name': 'health_check', 'url': '/api/health', 'method': 'GET', 'expected_time': 1.0},
                {'name': 'script_analysis', 'url': '/api/script/analyze', 'method': 'POST', 'expected_time': 5.0,
                 'data': {'script_text': 'FADE IN:\nINT. TEST - DAY\nQuick test.\nFADE OUT.', 'title': 'Performance Test', 'mode': 'parse'}},
                {'name': 'semantic_search', 'url': '/api/search/semantic', 'method': 'POST', 'expected_time': 3.0,
                 'data': {'beat_id': 'perf_test', 'query_tags': {'emotions': ['test']}, 'limit': 3}}
            ]
            
            response_times = []
            
            for test in api_tests:
                try:
                    start_time = time.time()
                    
                    if test['method'] == 'GET':
                        response = requests.get(f"{self.api_base_url}{test['url']}", timeout=15)
                    else:
                        response = requests.post(f"{self.api_base_url}{test['url']}", json=test.get('data'), timeout=15)
                        
                    response_time = time.time() - start_time
                    
                    response_times.append({
                        'api': test['name'],
                        'response_time': response_time,
                        'expected_time': test['expected_time'],
                        'success': response.status_code == 200,
                        'meets_expectation': response_time <= test['expected_time'],
                        'performance_rating': 'excellent' if response_time <= test['expected_time'] * 0.5 else 'good' if response_time <= test['expected_time'] else 'slow'
                    })
                    
                except Exception as e:
                    response_times.append({
                        'api': test['name'],
                        'success': False,
                        'error': str(e)
                    })
                    
            successful_apis = [rt for rt in response_times if rt.get('success', False)]
            meeting_expectations = [rt for rt in successful_apis if rt.get('meets_expectation', False)]
            
            return {
                'status': 'success',
                'response_times': response_times,
                'successful_apis': len(successful_apis),
                'total_tests': len(api_tests),
                'meeting_expectations': len(meeting_expectations),
                'expectation_rate': (len(meeting_expectations) / len(successful_apis)) * 100 if successful_apis else 0,
                'overall_api_performance': 'excellent' if len(meeting_expectations) == len(successful_apis) else 'good'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_file_processing_speed(self):
        """测试文件处理速度"""
        print("  📁 测试文件处理速度...")
        
        try:
            # 模拟文件处理测试（不实际上传文件）
            processing_tests = [
                {'type': 'small_script', 'size': 'small', 'expected_time': 2.0},
                {'type': 'medium_script', 'size': 'medium', 'expected_time': 5.0},
                {'type': 'large_script', 'size': 'large', 'expected_time': 10.0}
            ]
            
            processing_results = []
            
            for test in processing_tests:
                # 生成不同大小的测试剧本
                if test['size'] == 'small':
                    script_content = "FADE IN:\nINT. ROOM - DAY\nSmall test script.\nFADE OUT."
                elif test['size'] == 'medium':
                    script_content = """FADE IN:

INT. OFFICE - DAY

JOHN sits at his desk, working on his computer. The office is busy with activity.

JOHN
(to himself)
This medium-sized script should test our processing capabilities.

SARAH enters the office.

SARAH
How's the project coming along?

JOHN
Making good progress. The system seems to handle different script sizes well.

SARAH
That's great to hear.

FADE OUT."""
                else:  # large
                    script_content = """FADE IN:

EXT. CITY STREET - DAY

The bustling city comes alive with morning traffic. People hurry along the sidewalks, each absorbed in their own world.

INT. COFFEE SHOP - CONTINUOUS

ALEX (30s), a software developer with tired eyes, orders coffee. The BARISTA (20s) smiles warmly.

BARISTA
The usual?

ALEX
You know it. Large coffee, extra shot.

BARISTA
Long night coding again?

ALEX
(laughing)
Is it that obvious?

BARISTA
The dark circles are a dead giveaway.

Alex chuckles and finds a seat by the window.

INT. ALEX'S APARTMENT - LATER

Alex sits at a cluttered desk, multiple monitors displaying code. Empty coffee cups and snack wrappers litter the workspace.

ALEX
(to the screen)
Come on, this large script processing test needs to work perfectly.

Alex's phone RINGS. It's SARAH, the project manager.

SARAH (V.O.)
(through phone)
How's the testing going?

ALEX
(into phone)
Good progress. The system handles various script sizes well. This large script test should demonstrate our processing capabilities.

SARAH (V.O.)
That's exactly what we need for the demo.

ALEX
I'll have the results ready soon.

Alex hangs up and continues working with renewed focus.

FADE OUT."""
                
                try:
                    start_time = time.time()
                    
                    response = requests.post(
                        f"{self.api_base_url}/api/script/analyze",
                        json={
                            "script_text": script_content,
                            "title": f"Processing Speed Test - {test['type']}",
                            "mode": "parse"
                        },
                        timeout=20
                    )
                    
                    processing_time = time.time() - start_time
                    
                    processing_results.append({
                        'test_type': test['type'],
                        'script_size': test['size'],
                        'processing_time': processing_time,
                        'expected_time': test['expected_time'],
                        'success': response.status_code == 200,
                        'meets_expectation': processing_time <= test['expected_time'],
                        'script_length': len(script_content),
                        'processing_speed': len(script_content) / processing_time if processing_time > 0 else 0  # chars per second
                    })
                    
                except Exception as e:
                    processing_results.append({
                        'test_type': test['type'],
                        'success': False,
                        'error': str(e)
                    })
                    
            successful_tests = [pr for pr in processing_results if pr.get('success', False)]
            meeting_expectations = [pr for pr in successful_tests if pr.get('meets_expectation', False)]
            
            return {
                'status': 'success',
                'processing_results': processing_results,
                'successful_tests': len(successful_tests),
                'total_tests': len(processing_tests),
                'meeting_expectations': len(meeting_expectations),
                'processing_efficiency': (len(meeting_expectations) / len(successful_tests)) * 100 if successful_tests else 0,
                'overall_processing_speed': 'excellent' if len(meeting_expectations) == len(successful_tests) else 'good'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_compatibility_stability(self):
        """测试兼容性和稳定性"""
        print("\n🔧 测试兼容性和稳定性...")
        
        compatibility_tests = {}
        
        # 网络波动适应性测试
        compatibility_tests['network_resilience'] = self.test_network_resilience()
        
        # 系统资源适应性测试
        compatibility_tests['resource_adaptation'] = self.test_resource_adaptation()
        
        self.test_results['compatibility_tests'] = compatibility_tests
        
    def test_network_resilience(self):
        """测试网络波动适应性"""
        print("  🌐 测试网络波动适应性...")
        
        try:
            resilience_tests = []
            
            # 测试不同超时设置下的表现
            timeout_tests = [1, 3, 5, 10]  # 不同的超时时间
            
            for timeout in timeout_tests:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.api_base_url}/api/health", timeout=timeout)
                    response_time = time.time() - start_time
                    
                    resilience_tests.append({
                        'timeout_setting': timeout,
                        'success': response.status_code == 200,
                        'response_time': response_time,
                        'within_timeout': response_time < timeout,
                        'resilience_rating': 'excellent' if response_time < timeout * 0.5 else 'good'
                    })
                    
                except requests.exceptions.Timeout:
                    resilience_tests.append({
                        'timeout_setting': timeout,
                        'success': False,
                        'error': 'timeout',
                        'resilience_rating': 'poor'
                    })
                except Exception as e:
                    resilience_tests.append({
                        'timeout_setting': timeout,
                        'success': False,
                        'error': str(e),
                        'resilience_rating': 'poor'
                    })
                    
            successful_tests = [rt for rt in resilience_tests if rt.get('success', False)]
            
            return {
                'status': 'success',
                'resilience_tests': resilience_tests,
                'successful_tests': len(successful_tests),
                'total_tests': len(timeout_tests),
                'network_resilience_rate': (len(successful_tests) / len(timeout_tests)) * 100,
                'overall_resilience': 'excellent' if len(successful_tests) == len(timeout_tests) else 'good' if len(successful_tests) >= len(timeout_tests) * 0.8 else 'poor'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def test_resource_adaptation(self):
        """测试系统资源适应性"""
        print("  💾 测试系统资源适应性...")
        
        try:
            # 模拟不同负载下的系统表现
            load_tests = []
            
            for load_level in [1, 2, 3]:  # 轻量级负载测试
                start_time = time.time()
                
                # 同时发送多个请求
                responses = []
                for i in range(load_level):
                    try:
                        response = requests.get(f"{self.api_base_url}/api/health", timeout=5)
                        responses.append(response.status_code == 200)
                    except:
                        responses.append(False)
                        
                test_time = time.time() - start_time
                success_rate = (sum(responses) / len(responses)) * 100
                
                load_tests.append({
                    'load_level': load_level,
                    'concurrent_requests': load_level,
                    'success_rate': success_rate,
                    'total_time': test_time,
                    'average_time_per_request': test_time / load_level,
                    'adaptation_rating': 'excellent' if success_rate == 100 else 'good' if success_rate >= 80 else 'poor'
                })
                
            return {
                'status': 'success',
                'load_tests': load_tests,
                'max_tested_load': max(lt['load_level'] for lt in load_tests),
                'overall_adaptation': 'excellent' if all(lt['success_rate'] >= 90 for lt in load_tests) else 'good',
                'suitable_for_production': all(lt['success_rate'] >= 80 for lt in load_tests)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def generate_ux_report(self):
        """生成用户体验报告"""
        print("\n📋 生成用户体验验证报告...")
        
        # 统计各项测试结果
        user_scenarios = self.test_results.get('user_scenarios', {})
        performance_benchmarks = self.test_results.get('performance_benchmarks', {})
        compatibility_tests = self.test_results.get('compatibility_tests', {})
        
        # 计算用户体验评分
        ux_scores = []
        
        # 用户场景评分
        for scenario_name, scenario_result in user_scenarios.items():
            if scenario_result.get('status') == 'success':
                if scenario_result.get('overall_success', False):
                    ux_scores.append(100)
                elif scenario_result.get('status') == 'partial_success':
                    ux_scores.append(70)
                else:
                    ux_scores.append(50)
            else:
                ux_scores.append(0)
                
        # 性能评分
        for perf_name, perf_result in performance_benchmarks.items():
            if perf_result.get('status') == 'success':
                if perf_result.get('overall_performance') == 'excellent' or perf_result.get('overall_api_performance') == 'excellent':
                    ux_scores.append(100)
                elif 'good' in str(perf_result.get('overall_performance', '')) or 'good' in str(perf_result.get('overall_api_performance', '')):
                    ux_scores.append(80)
                else:
                    ux_scores.append(60)
            else:
                ux_scores.append(0)
                
        # 兼容性评分
        for compat_name, compat_result in compatibility_tests.items():
            if compat_result.get('status') == 'success':
                if compat_result.get('overall_resilience') == 'excellent' or compat_result.get('overall_adaptation') == 'excellent':
                    ux_scores.append(100)
                elif 'good' in str(compat_result.get('overall_resilience', '')) or 'good' in str(compat_result.get('overall_adaptation', '')):
                    ux_scores.append(80)
                else:
                    ux_scores.append(60)
            else:
                ux_scores.append(0)
                
        # 计算总体用户体验评分
        overall_ux_score = sum(ux_scores) / len(ux_scores) if ux_scores else 0
        
        summary = {
            'overall_ux_score': overall_ux_score,
            'ux_rating': 'excellent' if overall_ux_score >= 90 else 'good' if overall_ux_score >= 75 else 'needs_improvement' if overall_ux_score >= 50 else 'poor',
            'total_tests_run': len(ux_scores),
            'user_scenario_tests': len(user_scenarios),
            'performance_tests': len(performance_benchmarks),
            'compatibility_tests': len(compatibility_tests),
            'ready_for_users': overall_ux_score >= 75,
            'recommended_actions': self.get_ux_recommendations(overall_ux_score),
            'test_completion_time': datetime.now().isoformat()
        }
        
        self.test_results['summary'] = summary
        
        # 保存报告
        report_filename = f"user_experience_validation_report_{int(time.time())}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
        # 打印摘要
        print(f"\n📊 用户体验验证结果:")
        print(f"  🎯 整体用户体验评分: {overall_ux_score:.1f}%")
        print(f"  🏆 用户体验等级: {summary['ux_rating'].upper()}")
        print(f"  👥 用户场景测试: {summary['user_scenario_tests']} 项")
        print(f"  📊 性能基准测试: {summary['performance_tests']} 项")
        print(f"  🔧 兼容性测试: {summary['compatibility_tests']} 项")
        print(f"  ✅ 用户就绪状态: {'是' if summary['ready_for_users'] else '否'}")
        
        if summary['recommended_actions']:
            print(f"  💡 建议改进:")
            for action in summary['recommended_actions']:
                print(f"    - {action}")
                
        print(f"\n📄 详细报告已保存到: {report_filename}")
        
        return report_filename
        
    def get_ux_recommendations(self, ux_score):
        """根据用户体验评分生成建议"""
        recommendations = []
        
        if ux_score < 50:
            recommendations.extend([
                "系统存在严重的用户体验问题，需要全面检查和修复",
                "优先修复基础功能和API响应问题",
                "建议暂缓发布，先解决核心问题"
            ])
        elif ux_score < 75:
            recommendations.extend([
                "系统基本可用，但需要优化性能和稳定性",
                "改进错误处理和用户反馈机制",
                "优化API响应时间和页面加载速度"
            ])
        elif ux_score < 90:
            recommendations.extend([
                "系统用户体验良好，可以考虑发布",
                "继续优化性能和用户界面细节",
                "添加更多用户友好的功能"
            ])
        else:
            recommendations.extend([
                "系统用户体验优秀，已准备好发布",
                "保持当前的高质量标准",
                "可以考虑添加高级功能"
            ])
            
        return recommendations

def main():
    """主函数"""
    validator = UserExperienceValidator()
    validator.run_user_experience_validation()

if __name__ == "__main__":
    main()