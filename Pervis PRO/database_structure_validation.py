#!/usr/bin/env python3
"""
数据库表结构验证脚本
用于智能工作流系统的数据库完整性检测
"""

import sys
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from database import DATABASE_URL, engine, SessionLocal
    from sqlalchemy import text, inspect
    print("✅ 成功导入数据库配置")
except ImportError as e:
    print(f"❌ 导入数据库配置失败: {e}")
    DATABASE_URL = "sqlite:///./pervis_director.db"

class DatabaseValidator:
    """数据库结构验证器"""
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            # 从DATABASE_URL提取路径
            if "sqlite:///" in DATABASE_URL:
                self.db_path = DATABASE_URL.replace("sqlite:///", "")
            else:
                self.db_path = "pervis_director.db"
        
        self.expected_tables = {
            # 核心表
            "projects": {
                "description": "项目表 - 存储项目基本信息",
                "required_columns": ["id", "title", "script_raw", "created_at"],
                "optional_columns": ["logline", "synopsis", "characters", "specs", "current_stage"]
            },
            "beats": {
                "description": "Beat表 - 存储剧本分析结果",
                "required_columns": ["id", "project_id", "content", "order_index"],
                "optional_columns": ["emotion_tags", "scene_tags", "action_tags", "cinematography_tags", "duration", "user_notes", "main_asset_id"]
            },
            "assets": {
                "description": "素材表 - 存储所有媒体素材",
                "required_columns": ["id", "project_id", "filename", "file_path"],
                "optional_columns": ["mime_type", "source", "proxy_path", "thumbnail_path", "processing_status", "processing_progress", "tags", "processing_metadata", "created_at"]
            },
            "asset_segments": {
                "description": "素材片段表 - 存储素材的时间片段信息",
                "required_columns": ["id", "asset_id", "start_time", "end_time"],
                "optional_columns": ["description", "emotion_tags", "scene_tags", "action_tags", "cinematography_tags"]
            },
            "asset_vectors": {
                "description": "素材向量表 - 存储向量化数据",
                "required_columns": ["id", "asset_id", "vector_data", "content_type"],
                "optional_columns": ["segment_id", "text_content", "created_at"]
            },
            
            # 标签管理表
            "tag_hierarchy": {
                "description": "标签层级表 - 管理标签分类体系",
                "required_columns": ["id", "tag_name"],
                "optional_columns": ["parent_id", "level", "category", "created_at", "updated_at"]
            },
            "asset_tags": {
                "description": "资产标签关联表 - 素材与标签的关联",
                "required_columns": ["id", "asset_id", "tag_id"],
                "optional_columns": ["weight", "order_index", "source", "created_at", "updated_at"]
            },
            
            # 导出功能表
            "export_history": {
                "description": "导出历史表 - 记录导出操作",
                "required_columns": ["id", "project_id", "export_type", "file_path"],
                "optional_columns": ["file_size", "file_format", "options", "status", "error_message", "created_at", "created_by"]
            },
            
            # 视频编辑表
            "timelines": {
                "description": "时间轴表 - 视频编辑时间轴",
                "required_columns": ["id", "project_id"],
                "optional_columns": ["name", "duration", "created_at", "updated_at"]
            },
            "clips": {
                "description": "视频片段表 - 时间轴上的视频片段",
                "required_columns": ["id", "timeline_id", "asset_id", "start_time", "end_time", "order_index"],
                "optional_columns": ["trim_start", "trim_end", "volume", "is_muted", "audio_fade_in", "audio_fade_out", "transition_type", "transition_duration", "clip_metadata", "created_at", "updated_at"]
            },
            "render_tasks": {
                "description": "渲染任务表 - 视频渲染任务",
                "required_columns": ["id", "timeline_id"],
                "optional_columns": ["format", "resolution", "framerate", "quality", "bitrate", "audio_bitrate", "status", "progress", "error_message", "output_path", "file_size", "created_at", "started_at", "completed_at", "celery_task_id"]
            },
            
            # 分析日志表
            "analysis_logs": {
                "description": "分析日志表 - 记录素材分析过程",
                "required_columns": ["id", "asset_id", "analysis_type"],
                "optional_columns": ["status", "progress", "steps", "current_step", "results", "error_message", "duration", "file_size", "processing_speed", "started_at", "completed_at", "created_at"]
            },
            
            # 图片处理表
            "image_assets": {
                "description": "图片资产表 - 存储图片素材",
                "required_columns": ["id", "project_id", "filename", "original_path"],
                "optional_columns": ["thumbnail_path", "mime_type", "file_size", "width", "height", "description", "tags", "color_palette", "processing_status", "processing_progress", "error_message", "created_at", "updated_at"]
            },
            "image_vectors": {
                "description": "图片向量表 - 存储图片向量数据",
                "required_columns": ["id", "image_id", "vector_type", "vector_data"],
                "optional_columns": ["content_text", "model_version", "confidence_score", "vector_dimension", "created_at"]
            }
        }
        
        self.expected_indexes = [
            # 核心表索引
            "idx_beats_project_id",
            "idx_beats_order_index", 
            "idx_assets_project_id",
            "idx_assets_processing_status",
            "idx_asset_vectors_asset_id",
            "idx_asset_vectors_content_type",
            
            # 视频编辑索引
            "idx_timelines_project_id",
            "idx_clips_timeline_id",
            "idx_clips_order_index",
            "idx_render_tasks_timeline_id",
            "idx_render_tasks_status",
            
            # 图片处理索引
            "idx_image_assets_project_id",
            "idx_image_vectors_image_id",
            
            # 复合索引
            "idx_assets_project_status",
            "idx_beats_project_order"
        ]
    
    def connect_db(self) -> sqlite3.Connection:
        """连接数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise
    
    def get_existing_tables(self) -> List[str]:
        """获取现有表列表"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return tables
    
    def get_table_columns(self, table_name: str) -> List[Tuple[str, str]]:
        """获取表的列信息"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [(row[1], row[2]) for row in cursor.fetchall()]  # (name, type)
        
        conn.close()
        return columns
    
    def get_existing_indexes(self) -> List[str]:
        """获取现有索引列表"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return indexes
    
    def validate_table_structure(self) -> Dict:
        """验证表结构完整性"""
        print("🔍 开始验证数据库表结构...")
        
        results = {
            "total_expected": len(self.expected_tables),
            "total_existing": 0,
            "missing_tables": [],
            "existing_tables": [],
            "table_details": {},
            "overall_status": "unknown"
        }
        
        existing_tables = self.get_existing_tables()
        results["total_existing"] = len(existing_tables)
        results["existing_tables"] = existing_tables
        
        print(f"📊 预期表数量: {results['total_expected']}")
        print(f"📊 现有表数量: {results['total_existing']}")
        print()
        
        # 检查每个预期的表
        for table_name, table_info in self.expected_tables.items():
            print(f"🔍 检查表: {table_name}")
            print(f"   描述: {table_info['description']}")
            
            if table_name in existing_tables:
                print(f"   ✅ 表存在")
                
                # 检查列结构
                columns = self.get_table_columns(table_name)
                column_names = [col[0] for col in columns]
                
                table_result = {
                    "exists": True,
                    "columns": columns,
                    "missing_required_columns": [],
                    "missing_optional_columns": [],
                    "extra_columns": [],
                    "status": "ok"
                }
                
                # 检查必需列
                for req_col in table_info["required_columns"]:
                    if req_col not in column_names:
                        table_result["missing_required_columns"].append(req_col)
                        print(f"   ❌ 缺少必需列: {req_col}")
                
                # 检查可选列
                for opt_col in table_info["optional_columns"]:
                    if opt_col not in column_names:
                        table_result["missing_optional_columns"].append(opt_col)
                        print(f"   ⚠️  缺少可选列: {opt_col}")
                
                # 检查额外列
                all_expected_columns = table_info["required_columns"] + table_info["optional_columns"]
                for col_name in column_names:
                    if col_name not in all_expected_columns:
                        table_result["extra_columns"].append(col_name)
                        print(f"   ℹ️  额外列: {col_name}")
                
                # 确定表状态
                if table_result["missing_required_columns"]:
                    table_result["status"] = "error"
                elif table_result["missing_optional_columns"]:
                    table_result["status"] = "warning"
                else:
                    table_result["status"] = "ok"
                
                print(f"   📋 列数量: {len(columns)}")
                print(f"   📊 状态: {table_result['status']}")
                
                results["table_details"][table_name] = table_result
                
            else:
                print(f"   ❌ 表不存在")
                results["missing_tables"].append(table_name)
                results["table_details"][table_name] = {
                    "exists": False,
                    "status": "missing"
                }
            
            print()
        
        # 确定整体状态
        if results["missing_tables"]:
            results["overall_status"] = "error"
        elif any(t["status"] == "error" for t in results["table_details"].values()):
            results["overall_status"] = "error"
        elif any(t["status"] == "warning" for t in results["table_details"].values()):
            results["overall_status"] = "warning"
        else:
            results["overall_status"] = "ok"
        
        return results
    
    def validate_indexes(self) -> Dict:
        """验证索引完整性"""
        print("🔍 开始验证数据库索引...")
        
        existing_indexes = self.get_existing_indexes()
        
        results = {
            "total_expected": len(self.expected_indexes),
            "total_existing": len(existing_indexes),
            "missing_indexes": [],
            "existing_indexes": existing_indexes,
            "extra_indexes": []
        }
        
        print(f"📊 预期索引数量: {results['total_expected']}")
        print(f"📊 现有索引数量: {results['total_existing']}")
        print()
        
        # 检查缺失的索引
        for expected_index in self.expected_indexes:
            if expected_index not in existing_indexes:
                results["missing_indexes"].append(expected_index)
                print(f"❌ 缺少索引: {expected_index}")
            else:
                print(f"✅ 索引存在: {expected_index}")
        
        # 检查额外的索引
        for existing_index in existing_indexes:
            if existing_index not in self.expected_indexes:
                results["extra_indexes"].append(existing_index)
                print(f"ℹ️  额外索引: {existing_index}")
        
        return results
    
    def validate_data_integrity(self) -> Dict:
        """验证数据完整性"""
        print("🔍 开始验证数据完整性...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        results = {
            "foreign_key_violations": [],
            "null_violations": [],
            "data_consistency_issues": [],
            "table_counts": {}
        }
        
        try:
            # 检查表记录数量
            existing_tables = self.get_existing_tables()
            for table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                results["table_counts"][table] = count
                print(f"📊 {table}: {count} 条记录")
            
            # 检查外键约束（如果表存在）
            if "projects" in existing_tables and "beats" in existing_tables:
                cursor.execute("""
                    SELECT COUNT(*) FROM beats 
                    WHERE project_id NOT IN (SELECT id FROM projects)
                """)
                orphaned_beats = cursor.fetchone()[0]
                if orphaned_beats > 0:
                    results["foreign_key_violations"].append(f"beats表中有{orphaned_beats}条记录的project_id无效")
                    print(f"❌ beats表外键违规: {orphaned_beats}条")
                else:
                    print("✅ beats表外键完整性正常")
            
            if "assets" in existing_tables and "asset_vectors" in existing_tables:
                cursor.execute("""
                    SELECT COUNT(*) FROM asset_vectors 
                    WHERE asset_id NOT IN (SELECT id FROM assets)
                """)
                orphaned_vectors = cursor.fetchone()[0]
                if orphaned_vectors > 0:
                    results["foreign_key_violations"].append(f"asset_vectors表中有{orphaned_vectors}条记录的asset_id无效")
                    print(f"❌ asset_vectors表外键违规: {orphaned_vectors}条")
                else:
                    print("✅ asset_vectors表外键完整性正常")
            
            # 检查必需字段的空值
            if "projects" in existing_tables:
                cursor.execute("SELECT COUNT(*) FROM projects WHERE title IS NULL OR title = ''")
                null_titles = cursor.fetchone()[0]
                if null_titles > 0:
                    results["null_violations"].append(f"projects表中有{null_titles}条记录的title为空")
                    print(f"❌ projects表title字段空值: {null_titles}条")
                else:
                    print("✅ projects表title字段完整性正常")
            
        except Exception as e:
            print(f"❌ 数据完整性检查失败: {e}")
            results["error"] = str(e)
        finally:
            conn.close()
        
        return results
    
    def check_file_storage_paths(self) -> Dict:
        """检查文件存储路径"""
        print("🔍 开始验证文件存储系统...")
        
        results = {
            "storage_directories": {},
            "missing_directories": [],
            "permission_issues": []
        }
        
        # 预期的存储目录
        expected_dirs = [
            "assets",
            "assets/originals", 
            "assets/proxies",
            "assets/thumbnails",
            "assets/audio",
            "storage",
            "storage/renders",
            "storage/temp",
            "exports"
        ]
        
        for dir_path in expected_dirs:
            print(f"🔍 检查目录: {dir_path}")
            
            if os.path.exists(dir_path):
                if os.path.isdir(dir_path):
                    # 检查权限
                    readable = os.access(dir_path, os.R_OK)
                    writable = os.access(dir_path, os.W_OK)
                    
                    results["storage_directories"][dir_path] = {
                        "exists": True,
                        "readable": readable,
                        "writable": writable,
                        "status": "ok" if readable and writable else "permission_issue"
                    }
                    
                    if readable and writable:
                        print(f"   ✅ 目录正常，可读写")
                    else:
                        print(f"   ⚠️  权限问题 - 可读: {readable}, 可写: {writable}")
                        results["permission_issues"].append(dir_path)
                else:
                    print(f"   ❌ 路径存在但不是目录")
                    results["storage_directories"][dir_path] = {
                        "exists": False,
                        "status": "not_directory"
                    }
            else:
                print(f"   ❌ 目录不存在")
                results["missing_directories"].append(dir_path)
                results["storage_directories"][dir_path] = {
                    "exists": False,
                    "status": "missing"
                }
        
        return results
    
    def generate_report(self, table_results: Dict, index_results: Dict, 
                       integrity_results: Dict, storage_results: Dict) -> Dict:
        """生成完整的验证报告"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "database_path": self.db_path,
            "summary": {
                "overall_status": "unknown",
                "total_issues": 0,
                "critical_issues": 0,
                "warnings": 0
            },
            "table_structure": table_results,
            "indexes": index_results,
            "data_integrity": integrity_results,
            "file_storage": storage_results,
            "recommendations": []
        }
        
        # 统计问题
        critical_issues = 0
        warnings = 0
        
        # 表结构问题
        if table_results["missing_tables"]:
            critical_issues += len(table_results["missing_tables"])
        
        for table_detail in table_results["table_details"].values():
            if table_detail.get("status") == "error":
                critical_issues += len(table_detail.get("missing_required_columns", []))
            elif table_detail.get("status") == "warning":
                warnings += len(table_detail.get("missing_optional_columns", []))
        
        # 索引问题
        warnings += len(index_results["missing_indexes"])
        
        # 数据完整性问题
        critical_issues += len(integrity_results["foreign_key_violations"])
        critical_issues += len(integrity_results["null_violations"])
        
        # 存储问题
        critical_issues += len(storage_results["missing_directories"])
        warnings += len(storage_results["permission_issues"])
        
        report["summary"]["critical_issues"] = critical_issues
        report["summary"]["warnings"] = warnings
        report["summary"]["total_issues"] = critical_issues + warnings
        
        # 确定整体状态
        if critical_issues > 0:
            report["summary"]["overall_status"] = "error"
        elif warnings > 0:
            report["summary"]["overall_status"] = "warning"
        else:
            report["summary"]["overall_status"] = "ok"
        
        # 生成建议
        if table_results["missing_tables"]:
            report["recommendations"].append("运行数据库迁移脚本创建缺失的表")
        
        if index_results["missing_indexes"]:
            report["recommendations"].append("运行性能优化脚本创建缺失的索引")
        
        if storage_results["missing_directories"]:
            report["recommendations"].append("创建缺失的存储目录")
        
        if storage_results["permission_issues"]:
            report["recommendations"].append("修复存储目录的权限问题")
        
        if integrity_results["foreign_key_violations"]:
            report["recommendations"].append("清理数据库中的外键约束违规数据")
        
        return report
    
    def run_full_validation(self) -> Dict:
        """运行完整的数据库验证"""
        print("=" * 60)
        print("🎬 PreVis PRO - 数据库结构验证")
        print("=" * 60)
        print(f"📍 数据库路径: {self.db_path}")
        print()
        
        # 检查数据库文件是否存在
        if not os.path.exists(self.db_path):
            print(f"❌ 数据库文件不存在: {self.db_path}")
            return {
                "error": "数据库文件不存在",
                "database_path": self.db_path
            }
        
        try:
            # 1. 验证表结构
            table_results = self.validate_table_structure()
            print()
            
            # 2. 验证索引
            index_results = self.validate_indexes()
            print()
            
            # 3. 验证数据完整性
            integrity_results = self.validate_data_integrity()
            print()
            
            # 4. 验证文件存储
            storage_results = self.check_file_storage_paths()
            print()
            
            # 5. 生成报告
            report = self.generate_report(table_results, index_results, 
                                        integrity_results, storage_results)
            
            return report
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            return {
                "error": str(e),
                "database_path": self.db_path
            }

def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("=" * 60)
    print("📋 验证报告摘要")
    print("=" * 60)
    
    summary = report["summary"]
    status_emoji = {
        "ok": "✅",
        "warning": "⚠️ ",
        "error": "❌"
    }
    
    print(f"🎯 整体状态: {status_emoji.get(summary['overall_status'], '❓')} {summary['overall_status'].upper()}")
    print(f"🔥 严重问题: {summary['critical_issues']}")
    print(f"⚠️  警告: {summary['warnings']}")
    print(f"📊 总问题数: {summary['total_issues']}")
    print()
    
    if report.get("recommendations"):
        print("💡 建议:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"   {i}. {rec}")
        print()
    
    # 详细统计
    table_results = report["table_structure"]
    print(f"📋 表结构: {table_results['total_existing']}/{table_results['total_expected']} 个表存在")
    
    if table_results["missing_tables"]:
        print(f"   ❌ 缺失表: {', '.join(table_results['missing_tables'])}")
    
    index_results = report["indexes"]
    print(f"📊 索引: {index_results['total_existing']}/{index_results['total_expected']} 个索引存在")
    
    if index_results["missing_indexes"]:
        print(f"   ❌ 缺失索引: {', '.join(index_results['missing_indexes'][:5])}")
        if len(index_results["missing_indexes"]) > 5:
            print(f"   ... 还有 {len(index_results['missing_indexes']) - 5} 个")
    
    storage_results = report["file_storage"]
    total_dirs = len(storage_results["storage_directories"])
    missing_dirs = len(storage_results["missing_directories"])
    existing_dirs = total_dirs - missing_dirs
    print(f"📁 存储目录: {existing_dirs}/{total_dirs} 个目录存在")
    
    if storage_results["missing_directories"]:
        print(f"   ❌ 缺失目录: {', '.join(storage_results['missing_directories'])}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO 数据库结构验证工具')
    parser.add_argument('--db-path', help='数据库文件路径')
    parser.add_argument('--output', help='输出报告到JSON文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 创建验证器
    validator = DatabaseValidator(args.db_path)
    
    # 运行验证
    report = validator.run_full_validation()
    
    if "error" in report:
        print(f"💥 验证失败: {report['error']}")
        return 1
    
    # 打印摘要
    print_report_summary(report)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"📄 详细报告已保存到: {args.output}")
    
    # 返回状态码
    if report["summary"]["overall_status"] == "error":
        return 1
    elif report["summary"]["overall_status"] == "warning":
        return 2
    else:
        return 0

if __name__ == "__main__":
    exit(main())