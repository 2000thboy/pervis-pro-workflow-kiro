#!/usr/bin/env python3
"""
智能工作流系统 - 全面功能检测脚本
检测所有后端核心功能的完整性和可用性
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加backend路径到sys.path
sys.path.insert(0, 'backend')

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemDetectionReport:
    """系统检测报告"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
        self.critical_issues = []
        self.warnings = []
        
    def add_result(self, test_name: str, status: str, details: Dict[str, Any], is_critical: bool = False):
        """添加测试结果"""
        self.tests_run += 1
        if status == "PASS":
            self.tests_passed += 1
        else:
            self.tests_failed += 1
            if is_critical:
                self.critical_issues.append(f"{test_name}: {details.get('error', 'Unknown error')}")
        
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "is_critical": is_critical
        }
        self.results.append(result)
        
        # 实时输出结果
        status_icon = "✅" if status == "PASS" else "❌"
        logger.info(f"{status_icon} {test_name}: {status}")
        if status == "FAIL" and details.get('error'):
            logger.error(f"   错误: {details['error']}")
    
    def generate_report(self) -> Dict[str, Any]:
        """生成最终报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        return {
            "summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "tests_run": self.tests_run,
                "tests_passed": self.tests_passed,
                "tests_failed": self.tests_failed,
                "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
            },
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "detailed_results": self.results
        }


class SystemDetector:
    """系统功能检测器"""
    
    def __init__(self):
        self.report = SystemDetectionReport()
        self.db = None
        
    async def run_all_tests(self):
        """运行所有检测测试"""
        logger.info("🚀 开始智能工作流系统全面检测")
        
        try:
            # 1. 基础环境检测
            await self.test_basic_environment()
            
            # 2. 数据库连接检测
            await self.test_database_connection()
            
            # 3. 剧本分析服务检测
            await self.test_script_analysis_service()
            
            # 4. 素材处理服务检测
            await self.test_asset_processing_service()
            
            # 5. 多模态搜索引擎检测
            await self.test_multimodal_search_engine()
            
            # 6. 时间轴和AutoCut服务检测
            await self.test_timeline_autocut_service()
            
            # 7. 渲染服务检测
            await self.test_render_service()
            
            # 8. API接口检测
            await self.test_api_endpoints()
            
            # 9. 文件存储系统检测
            await self.test_file_storage_system()
            
            # 10. 生成最终报告
            await self.generate_final_report()
            
        except Exception as e:
            logger.error(f"检测过程中发生严重错误: {e}")
            logger.error(traceback.format_exc())
        finally:
            if self.db:
                self.db.close()
    
    async def test_basic_environment(self):
        """测试基础环境"""
        logger.info("📋 检测基础环境...")
        
        # 检查Python版本
        try:
            python_version = sys.version
            self.report.add_result(
                "Python版本检查",
                "PASS",
                {"python_version": python_version}
            )
        except Exception as e:
            self.report.add_result(
                "Python版本检查",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
        
        # 检查关键目录
        critical_dirs = ['backend', 'frontend', 'assets', 'storage']
        for dir_name in critical_dirs:
            try:
                if os.path.exists(dir_name):
                    self.report.add_result(
                        f"目录存在检查: {dir_name}",
                        "PASS",
                        {"path": os.path.abspath(dir_name)}
                    )
                else:
                    self.report.add_result(
                        f"目录存在检查: {dir_name}",
                        "FAIL",
                        {"error": f"目录不存在: {dir_name}"},
                        is_critical=True
                    )
            except Exception as e:
                self.report.add_result(
                    f"目录存在检查: {dir_name}",
                    "FAIL",
                    {"error": str(e)},
                    is_critical=True
                )
        
        # 检查关键Python包
        required_packages = [
            'sqlalchemy', 'fastapi', 'uvicorn', 'pydantic',
            'google-generativeai', 'numpy', 'opencv-python'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.report.add_result(
                    f"Python包检查: {package}",
                    "PASS",
                    {"package": package}
                )
            except ImportError as e:
                self.report.add_result(
                    f"Python包检查: {package}",
                    "FAIL",
                    {"error": f"包未安装: {package}"},
                    is_critical=True
                )
    
    async def test_database_connection(self):
        """测试数据库连接"""
        logger.info("🗄️ 检测数据库连接...")
        
        try:
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            
            # 尝试连接数据库
            database_url = "sqlite:///backend/pervis_director.db"
            engine = create_engine(database_url)
            SessionLocal = sessionmaker(bind=engine)
            self.db = SessionLocal()
            
            # 测试基本查询
            result = self.db.execute(text("SELECT 1")).fetchone()
            if result:
                self.report.add_result(
                    "数据库连接测试",
                    "PASS",
                    {"database_url": database_url}
                )
            else:
                self.report.add_result(
                    "数据库连接测试",
                    "FAIL",
                    {"error": "无法执行基本查询"},
                    is_critical=True
                )
            
            # 检查关键表是否存在
            tables_to_check = [
                'projects', 'beats', 'assets', 'timelines', 
                'clips', 'render_tasks', 'asset_segments'
            ]
            
            for table in tables_to_check:
                try:
                    result = self.db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                    count = result[0] if result else 0
                    self.report.add_result(
                        f"数据表检查: {table}",
                        "PASS",
                        {"table": table, "record_count": count}
                    )
                except Exception as e:
                    self.report.add_result(
                        f"数据表检查: {table}",
                        "FAIL",
                        {"error": f"表不存在或无法访问: {str(e)}"},
                        is_critical=True
                    )
                    
        except Exception as e:
            self.report.add_result(
                "数据库连接测试",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
    
    async def test_script_analysis_service(self):
        """测试剧本分析服务"""
        logger.info("📝 检测剧本分析服务...")
        
        try:
            from services.script_processor import ScriptProcessor
            from models.base import ScriptAnalysisRequest
            
            if not self.db:
                self.report.add_result(
                    "剧本分析服务初始化",
                    "FAIL",
                    {"error": "数据库连接不可用"},
                    is_critical=True
                )
                return
            
            processor = ScriptProcessor(self.db)
            
            # 测试基本初始化
            self.report.add_result(
                "剧本分析服务初始化",
                "PASS",
                {"service": "ScriptProcessor"}
            )
            
            # 测试剧本分析功能
            test_script = """
            场景1：城市街道 - 白天
            
            小明匆忙地跑过繁忙的街道，手里紧握着一份重要文件。
            
            小明：(气喘吁吁) 我必须在三点前赶到办公楼！
            
            场景2：办公楼大厅 - 白天
            
            小明冲进办公楼，在前台快速整理了一下衣服，松了一口气。
            """
            
            request = ScriptAnalysisRequest(
                script_text=test_script,
                title="测试剧本",
                logline="测试用剧本分析",
                mode="detailed"
            )
            
            try:
                result = await processor.analyze_script(request)
                
                if result.status == "success":
                    self.report.add_result(
                        "剧本分析功能测试",
                        "PASS",
                        {
                            "beats_count": len(result.beats),
                            "characters_count": len(result.characters),
                            "processing_time": result.processing_time,
                            "project_id": getattr(result, 'project_id', None)
                        }
                    )
                else:
                    self.report.add_result(
                        "剧本分析功能测试",
                        "FAIL",
                        {"error": result.error},
                        is_critical=True
                    )
                    
            except Exception as e:
                self.report.add_result(
                    "剧本分析功能测试",
                    "FAIL",
                    {"error": str(e)},
                    is_critical=True
                )
                
        except ImportError as e:
            self.report.add_result(
                "剧本分析服务导入",
                "FAIL",
                {"error": f"无法导入服务: {str(e)}"},
                is_critical=True
            )
        except Exception as e:
            self.report.add_result(
                "剧本分析服务检测",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
    
    async def test_asset_processing_service(self):
        """测试素材处理服务"""
        logger.info("🎬 检测素材处理服务...")
        
        try:
            from services.asset_processor import AssetProcessor
            
            if not self.db:
                self.report.add_result(
                    "素材处理服务初始化",
                    "FAIL",
                    {"error": "数据库连接不可用"},
                    is_critical=True
                )
                return
            
            processor = AssetProcessor(self.db)
            
            # 测试基本初始化
            self.report.add_result(
                "素材处理服务初始化",
                "PASS",
                {"service": "AssetProcessor"}
            )
            
            # 检查依赖服务
            services_to_check = [
                'video_processor', 'gemini_client', 'audio_transcriber', 'visual_processor'
            ]
            
            for service_name in services_to_check:
                try:
                    service = getattr(processor, service_name, None)
                    if service:
                        self.report.add_result(
                            f"素材处理依赖服务: {service_name}",
                            "PASS",
                            {"service": service_name}
                        )
                    else:
                        self.report.add_result(
                            f"素材处理依赖服务: {service_name}",
                            "FAIL",
                            {"error": f"服务未初始化: {service_name}"}
                        )
                except Exception as e:
                    self.report.add_result(
                        f"素材处理依赖服务: {service_name}",
                        "FAIL",
                        {"error": str(e)}
                    )
            
            # 测试文件类型检测
            test_files = [
                ("test.mp4", True),
                ("test.avi", True),
                ("test.jpg", False),
                ("test.txt", False)
            ]
            
            for filename, expected_is_video in test_files:
                try:
                    is_video = processor._is_video_file(filename)
                    if is_video == expected_is_video:
                        self.report.add_result(
                            f"文件类型检测: {filename}",
                            "PASS",
                            {"filename": filename, "is_video": is_video}
                        )
                    else:
                        self.report.add_result(
                            f"文件类型检测: {filename}",
                            "FAIL",
                            {"error": f"检测结果不正确: 期望{expected_is_video}, 实际{is_video}"}
                        )
                except Exception as e:
                    self.report.add_result(
                        f"文件类型检测: {filename}",
                        "FAIL",
                        {"error": str(e)}
                    )
                    
        except ImportError as e:
            self.report.add_result(
                "素材处理服务导入",
                "FAIL",
                {"error": f"无法导入服务: {str(e)}"},
                is_critical=True
            )
        except Exception as e:
            self.report.add_result(
                "素材处理服务检测",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
    
    async def test_multimodal_search_engine(self):
        """测试多模态搜索引擎"""
        logger.info("🔍 检测多模态搜索引擎...")
        
        try:
            from services.multimodal_search import MultimodalSearchEngine
            
            if not self.db:
                self.report.add_result(
                    "多模态搜索引擎初始化",
                    "FAIL",
                    {"error": "数据库连接不可用"},
                    is_critical=True
                )
                return
            
            search_engine = MultimodalSearchEngine(self.db)
            
            # 测试基本初始化
            self.report.add_result(
                "多模态搜索引擎初始化",
                "PASS",
                {"service": "MultimodalSearchEngine"}
            )
            
            # 测试查询意图解析
            test_queries = [
                "蓝色夜景城市",
                "快乐的对话场景",
                "紧张的追逐镜头"
            ]
            
            for query in test_queries:
                try:
                    intent = await search_engine._parse_query_intent(query)
                    if isinstance(intent, dict) and 'primary_intent' in intent:
                        self.report.add_result(
                            f"查询意图解析: {query}",
                            "PASS",
                            {
                                "query": query,
                                "primary_intent": intent.get('primary_intent'),
                                "keywords_count": sum(len(v) for v in intent.values() if isinstance(v, list))
                            }
                        )
                    else:
                        self.report.add_result(
                            f"查询意图解析: {query}",
                            "FAIL",
                            {"error": "返回格式不正确"}
                        )
                except Exception as e:
                    self.report.add_result(
                        f"查询意图解析: {query}",
                        "FAIL",
                        {"error": str(e)}
                    )
            
            # 测试多模态搜索功能
            try:
                search_result = await search_engine.multimodal_search(
                    query="测试查询",
                    search_modes=['semantic'],
                    limit=5
                )
                
                if search_result.get('status') == 'success':
                    self.report.add_result(
                        "多模态搜索功能测试",
                        "PASS",
                        {
                            "results_count": len(search_result.get('results', [])),
                            "search_modes": search_result.get('search_modes', [])
                        }
                    )
                else:
                    self.report.add_result(
                        "多模态搜索功能测试",
                        "FAIL",
                        {"error": search_result.get('message', 'Unknown error')}
                    )
                    
            except Exception as e:
                self.report.add_result(
                    "多模态搜索功能测试",
                    "FAIL",
                    {"error": str(e)}
                )
                
        except ImportError as e:
            self.report.add_result(
                "多模态搜索引擎导入",
                "FAIL",
                {"error": f"无法导入服务: {str(e)}"},
                is_critical=True
            )
        except Exception as e:
            self.report.add_result(
                "多模态搜索引擎检测",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
    
    async def test_timeline_autocut_service(self):
        """测试时间轴和AutoCut服务"""
        logger.info("⏱️ 检测时间轴和AutoCut服务...")
        
        try:
            from services.timeline_service import TimelineService
            from services.autocut_orchestrator import AutoCutOrchestrator
            from models.base import Beat
            
            if not self.db:
                self.report.add_result(
                    "时间轴服务初始化",
                    "FAIL",
                    {"error": "数据库连接不可用"},
                    is_critical=True
                )
                return
            
            timeline_service = TimelineService(self.db)
            autocut_service = AutoCutOrchestrator(self.db)
            
            # 测试服务初始化
            self.report.add_result(
                "时间轴服务初始化",
                "PASS",
                {"service": "TimelineService"}
            )
            
            self.report.add_result(
                "AutoCut服务初始化",
                "PASS",
                {"service": "AutoCutOrchestrator"}
            )
            
            # 测试AutoCut智能决策功能
            test_beats = [
                Beat(
                    id="beat_1",
                    content="小明匆忙地跑过繁忙的街道",
                    emotion_tags=["紧张"],
                    scene_tags=["街道", "白天"],
                    action_tags=["跑步"],
                    cinematography_tags=["手持"],
                    duration=3.0
                ),
                Beat(
                    id="beat_2", 
                    content="小明冲进办公楼大厅",
                    emotion_tags=["急迫"],
                    scene_tags=["办公楼", "室内"],
                    action_tags=["冲进"],
                    cinematography_tags=["稳定"],
                    duration=2.5
                )
            ]
            
            test_assets = [
                {
                    "id": "asset_1",
                    "filename": "city_street.mp4",
                    "file_path": "/path/to/city_street.mp4"
                },
                {
                    "id": "asset_2",
                    "filename": "office_building.mp4", 
                    "file_path": "/path/to/office_building.mp4"
                }
            ]
            
            try:
                timeline_result = await autocut_service.generate_timeline(test_beats, test_assets)
                
                if timeline_result.get('status') == 'success':
                    timeline_data = timeline_result.get('timeline', {})
                    clips = timeline_data.get('clips', [])
                    
                    self.report.add_result(
                        "AutoCut智能决策测试",
                        "PASS",
                        {
                            "clips_generated": len(clips),
                            "total_duration": timeline_data.get('total_duration', 0),
                            "processing_time": timeline_result.get('processing_time', 0)
                        }
                    )
                else:
                    self.report.add_result(
                        "AutoCut智能决策测试",
                        "FAIL",
                        {"error": timeline_result.get('error', 'Unknown error')},
                        is_critical=True
                    )
                    
            except Exception as e:
                self.report.add_result(
                    "AutoCut智能决策测试",
                    "FAIL",
                    {"error": str(e)},
                    is_critical=True
                )
            
            # 测试时间轴基础功能
            try:
                # 创建测试项目ID
                test_project_id = "test_project_123"
                
                # 创建时间轴
                timeline = timeline_service.create_timeline(
                    project_id=test_project_id,
                    name="测试时间轴"
                )
                
                if timeline and timeline.id:
                    self.report.add_result(
                        "时间轴创建测试",
                        "PASS",
                        {
                            "timeline_id": timeline.id,
                            "project_id": timeline.project_id,
                            "name": timeline.name
                        }
                    )
                    
                    # 测试时间轴查询
                    retrieved_timeline = timeline_service.get_timeline(timeline.id)
                    if retrieved_timeline:
                        self.report.add_result(
                            "时间轴查询测试",
                            "PASS",
                            {"timeline_id": retrieved_timeline.id}
                        )
                    else:
                        self.report.add_result(
                            "时间轴查询测试",
                            "FAIL",
                            {"error": "无法查询到创建的时间轴"}
                        )
                        
                else:
                    self.report.add_result(
                        "时间轴创建测试",
                        "FAIL",
                        {"error": "时间轴创建失败"},
                        is_critical=True
                    )
                    
            except Exception as e:
                self.report.add_result(
                    "时间轴基础功能测试",
                    "FAIL",
                    {"error": str(e)},
                    is_critical=True
                )
                
        except ImportError as e:
            self.report.add_result(
                "时间轴AutoCut服务导入",
                "FAIL",
                {"error": f"无法导入服务: {str(e)}"},
                is_critical=True
            )
        except Exception as e:
            self.report.add_result(
                "时间轴AutoCut服务检测",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
    
    async def test_render_service(self):
        """测试渲染服务"""
        logger.info("🎥 检测渲染服务...")
        
        try:
            from services.render_service import RenderService
            
            if not self.db:
                self.report.add_result(
                    "渲染服务初始化",
                    "FAIL",
                    {"error": "数据库连接不可用"},
                    is_critical=True
                )
                return
            
            render_service = RenderService(self.db)
            
            # 测试基本初始化
            self.report.add_result(
                "渲染服务初始化",
                "PASS",
                {"service": "RenderService"}
            )
            
            # 检查FFmpeg集成
            try:
                ffmpeg_wrapper = render_service.ffmpeg
                if ffmpeg_wrapper:
                    self.report.add_result(
                        "FFmpeg集成检查",
                        "PASS",
                        {"ffmpeg_wrapper": str(type(ffmpeg_wrapper))}
                    )
                else:
                    self.report.add_result(
                        "FFmpeg集成检查",
                        "FAIL",
                        {"error": "FFmpeg wrapper未初始化"}
                    )
            except Exception as e:
                self.report.add_result(
                    "FFmpeg集成检查",
                    "FAIL",
                    {"error": str(e)}
                )
            
            # 检查输出目录
            try:
                output_dir = render_service.output_dir
                if output_dir.exists():
                    self.report.add_result(
                        "渲染输出目录检查",
                        "PASS",
                        {"output_dir": str(output_dir)}
                    )
                else:
                    self.report.add_result(
                        "渲染输出目录检查",
                        "FAIL",
                        {"error": f"输出目录不存在: {output_dir}"}
                    )
            except Exception as e:
                self.report.add_result(
                    "渲染输出目录检查",
                    "FAIL",
                    {"error": str(e)}
                )
            
            # 测试渲染前检查功能
            try:
                # 使用一个不存在的时间轴ID进行测试
                test_timeline_id = "nonexistent_timeline"
                check_result = await render_service.check_render_requirements(test_timeline_id)
                
                if isinstance(check_result, dict) and 'can_render' in check_result:
                    # 应该返回False，因为时间轴不存在
                    if not check_result['can_render']:
                        self.report.add_result(
                            "渲染前检查功能测试",
                            "PASS",
                            {
                                "can_render": check_result['can_render'],
                                "errors": check_result.get('errors', [])
                            }
                        )
                    else:
                        self.report.add_result(
                            "渲染前检查功能测试",
                            "FAIL",
                            {"error": "应该检测到时间轴不存在的错误"}
                        )
                else:
                    self.report.add_result(
                        "渲染前检查功能测试",
                        "FAIL",
                        {"error": "返回格式不正确"}
                    )
                    
            except Exception as e:
                self.report.add_result(
                    "渲染前检查功能测试",
                    "FAIL",
                    {"error": str(e)}
                )
            
            # 测试任务状态查询功能
            try:
                # 查询一个不存在的任务
                test_task_id = "nonexistent_task"
                task_status = await render_service.get_task_status(test_task_id)
                
                # 应该返回None
                if task_status is None:
                    self.report.add_result(
                        "任务状态查询测试",
                        "PASS",
                        {"task_id": test_task_id, "result": "None (expected)"}
                    )
                else:
                    self.report.add_result(
                        "任务状态查询测试",
                        "FAIL",
                        {"error": "应该返回None对于不存在的任务"}
                    )
                    
            except Exception as e:
                self.report.add_result(
                    "任务状态查询测试",
                    "FAIL",
                    {"error": str(e)}
                )
                
        except ImportError as e:
            self.report.add_result(
                "渲染服务导入",
                "FAIL",
                {"error": f"无法导入服务: {str(e)}"},
                is_critical=True
            )
        except Exception as e:
            self.report.add_result(
                "渲染服务检测",
                "FAIL",
                {"error": str(e)},
                is_critical=True
            )
    
    async def test_api_endpoints(self):
        """测试API接口"""
        logger.info("🌐 检测API接口...")
        
        # 这里我们检查API路由文件是否存在和可导入
        api_modules = [
            'routers.assets',
            'routers.projects', 
            'routers.autocut',
            'routers.timeline',
            'routers.render',
            'routers.multimodal'
        ]
        
        for module_name in api_modules:
            try:
                __import__(module_name)
                self.report.add_result(
                    f"API模块导入: {module_name}",
                    "PASS",
                    {"module": module_name}
                )
            except ImportError as e:
                self.report.add_result(
                    f"API模块导入: {module_name}",
                    "FAIL",
                    {"error": f"无法导入模块: {str(e)}"}
                )
            except Exception as e:
                self.report.add_result(
                    f"API模块导入: {module_name}",
                    "FAIL",
                    {"error": str(e)}
                )
    
    async def test_file_storage_system(self):
        """测试文件存储系统"""
        logger.info("📁 检测文件存储系统...")
        
        # 检查关键存储目录
        storage_dirs = [
            'assets/originals',
            'assets/proxies', 
            'assets/thumbnails',
            'storage/renders',
            'backend/assets'
        ]
        
        for dir_path in storage_dirs:
            try:
                if os.path.exists(dir_path):
                    # 检查目录权限
                    if os.access(dir_path, os.R_OK | os.W_OK):
                        self.report.add_result(
                            f"存储目录检查: {dir_path}",
                            "PASS",
                            {
                                "path": os.path.abspath(dir_path),
                                "readable": True,
                                "writable": True
                            }
                        )
                    else:
                        self.report.add_result(
                            f"存储目录检查: {dir_path}",
                            "FAIL",
                            {"error": f"目录权限不足: {dir_path}"}
                        )
                else:
                    # 尝试创建目录
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                        self.report.add_result(
                            f"存储目录检查: {dir_path}",
                            "PASS",
                            {
                                "path": os.path.abspath(dir_path),
                                "created": True
                            }
                        )
                    except Exception as create_error:
                        self.report.add_result(
                            f"存储目录检查: {dir_path}",
                            "FAIL",
                            {"error": f"无法创建目录: {str(create_error)}"}
                        )
            except Exception as e:
                self.report.add_result(
                    f"存储目录检查: {dir_path}",
                    "FAIL",
                    {"error": str(e)}
                )
    
    async def generate_final_report(self):
        """生成最终报告"""
        logger.info("📊 生成最终检测报告...")
        
        report_data = self.report.generate_report()
        
        # 保存详细报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"system_detection_report_{timestamp}.json"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 详细报告已保存到: {report_filename}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
        
        # 输出摘要
        summary = report_data['summary']
        logger.info("=" * 60)
        logger.info("🎯 系统检测摘要")
        logger.info("=" * 60)
        logger.info(f"⏱️  检测时长: {summary['duration_seconds']:.2f} 秒")
        logger.info(f"📋 测试总数: {summary['tests_run']}")
        logger.info(f"✅ 通过测试: {summary['tests_passed']}")
        logger.info(f"❌ 失败测试: {summary['tests_failed']}")
        logger.info(f"📈 成功率: {summary['success_rate']:.1f}%")
        
        if report_data['critical_issues']:
            logger.error("🚨 关键问题:")
            for issue in report_data['critical_issues']:
                logger.error(f"   • {issue}")
        
        if report_data['warnings']:
            logger.warning("⚠️  警告:")
            for warning in report_data['warnings']:
                logger.warning(f"   • {warning}")
        
        logger.info("=" * 60)
        
        return report_data


async def main():
    """主函数"""
    detector = SystemDetector()
    await detector.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())