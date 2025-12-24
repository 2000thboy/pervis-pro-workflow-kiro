#!/usr/bin/env python3
"""
文件存储系统验证脚本
检查PreVis PRO的文件存储结构、权限和配置
"""

import os
import sys
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tempfile

class FileStorageValidator:
    """文件存储系统验证器"""
    
    def __init__(self):
        self.base_path = os.getcwd()
        
        # 预期的存储目录结构
        self.expected_structure = {
            "assets": {
                "description": "主要素材存储目录",
                "subdirs": {
                    "originals": "原始素材文件",
                    "proxies": "代理文件（低分辨率）",
                    "thumbnails": "缩略图文件",
                    "audio": "音频文件"
                },
                "required": True
            },
            "storage": {
                "description": "系统存储目录",
                "subdirs": {
                    "renders": "渲染输出文件",
                    "temp": "临时文件",
                    "proxies": "额外代理文件存储"
                },
                "required": True
            },
            "exports": {
                "description": "导出文件目录",
                "subdirs": {},
                "required": True
            },
            "backend/assets": {
                "description": "后端素材目录",
                "subdirs": {
                    "originals": "后端原始文件",
                    "proxies": "后端代理文件", 
                    "thumbnails": "后端缩略图",
                    "audio": "后端音频文件"
                },
                "required": False
            },
            "backend/storage": {
                "description": "后端存储目录",
                "subdirs": {
                    "images": "图片存储",
                    "renders": "后端渲染输出"
                },
                "required": False
            }
        }
        
        # 配置文件路径
        self.config_files = [
            "backend/.env",
            "backend/.env.example", 
            "frontend/.env",
            "frontend/.env.example"
        ]
    
    def check_directory_structure(self) -> Dict:
        """检查目录结构"""
        print("🔍 检查文件存储目录结构...")
        
        results = {
            "directories": {},
            "missing_required": [],
            "missing_optional": [],
            "permission_issues": [],
            "total_checked": 0,
            "total_existing": 0
        }
        
        for dir_path, dir_info in self.expected_structure.items():
            full_path = os.path.join(self.base_path, dir_path)
            results["total_checked"] += 1
            
            print(f"\n📁 检查目录: {dir_path}")
            print(f"   描述: {dir_info['description']}")
            print(f"   必需: {'是' if dir_info['required'] else '否'}")
            
            dir_result = {
                "path": full_path,
                "exists": False,
                "readable": False,
                "writable": False,
                "size_mb": 0,
                "file_count": 0,
                "subdirs": {},
                "issues": []
            }
            
            if os.path.exists(full_path):
                if os.path.isdir(full_path):
                    dir_result["exists"] = True
                    results["total_existing"] += 1
                    
                    # 检查权限
                    dir_result["readable"] = os.access(full_path, os.R_OK)
                    dir_result["writable"] = os.access(full_path, os.W_OK)
                    
                    if not dir_result["readable"] or not dir_result["writable"]:
                        results["permission_issues"].append(dir_path)
                        dir_result["issues"].append("权限不足")
                    
                    # 计算目录大小和文件数量
                    try:
                        total_size = 0
                        file_count = 0
                        for root, dirs, files in os.walk(full_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    total_size += os.path.getsize(file_path)
                                    file_count += 1
                                except (OSError, IOError):
                                    pass
                        
                        dir_result["size_mb"] = round(total_size / (1024 * 1024), 2)
                        dir_result["file_count"] = file_count
                        
                    except Exception as e:
                        dir_result["issues"].append(f"无法计算大小: {e}")
                    
                    # 检查子目录
                    for subdir_name, subdir_desc in dir_info["subdirs"].items():
                        subdir_path = os.path.join(full_path, subdir_name)
                        subdir_exists = os.path.exists(subdir_path) and os.path.isdir(subdir_path)
                        
                        dir_result["subdirs"][subdir_name] = {
                            "exists": subdir_exists,
                            "description": subdir_desc,
                            "path": subdir_path
                        }
                        
                        if subdir_exists:
                            print(f"   ✅ 子目录存在: {subdir_name}")
                        else:
                            print(f"   ⚠️  子目录缺失: {subdir_name}")
                    
                    print(f"   📊 大小: {dir_result['size_mb']} MB")
                    print(f"   📊 文件数: {dir_result['file_count']}")
                    print(f"   🔐 权限: 读{'✅' if dir_result['readable'] else '❌'} 写{'✅' if dir_result['writable'] else '❌'}")
                    
                else:
                    print(f"   ❌ 路径存在但不是目录")
                    dir_result["issues"].append("不是目录")
            else:
                print(f"   ❌ 目录不存在")
                if dir_info["required"]:
                    results["missing_required"].append(dir_path)
                else:
                    results["missing_optional"].append(dir_path)
            
            results["directories"][dir_path] = dir_result
        
        return results
    
    def check_config_files(self) -> Dict:
        """检查配置文件"""
        print("\n🔍 检查配置文件...")
        
        results = {
            "config_files": {},
            "missing_files": [],
            "invalid_files": []
        }
        
        for config_path in self.config_files:
            full_path = os.path.join(self.base_path, config_path)
            
            print(f"\n📄 检查配置文件: {config_path}")
            
            file_result = {
                "path": full_path,
                "exists": False,
                "readable": False,
                "size_bytes": 0,
                "storage_configs": [],
                "issues": []
            }
            
            if os.path.exists(full_path):
                if os.path.isfile(full_path):
                    file_result["exists"] = True
                    file_result["readable"] = os.access(full_path, os.R_OK)
                    
                    try:
                        file_result["size_bytes"] = os.path.getsize(full_path)
                        
                        # 读取配置内容
                        if file_result["readable"]:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # 查找存储相关配置
                            storage_keywords = [
                                "ASSET_STORAGE_PATH",
                                "UPLOAD_FOLDER", 
                                "STORAGE_PATH",
                                "RENDER_OUTPUT_PATH",
                                "PROXY_PATH",
                                "THUMBNAIL_PATH"
                            ]
                            
                            for keyword in storage_keywords:
                                if keyword in content:
                                    # 提取配置值
                                    for line in content.split('\n'):
                                        if keyword in line and '=' in line:
                                            file_result["storage_configs"].append(line.strip())
                            
                            print(f"   ✅ 文件存在且可读")
                            print(f"   📊 大小: {file_result['size_bytes']} 字节")
                            
                            if file_result["storage_configs"]:
                                print(f"   🔧 存储配置项: {len(file_result['storage_configs'])}")
                                for config in file_result["storage_configs"]:
                                    print(f"      {config}")
                            else:
                                print(f"   ℹ️  未找到存储相关配置")
                        else:
                            print(f"   ❌ 文件不可读")
                            file_result["issues"].append("文件不可读")
                            
                    except Exception as e:
                        print(f"   ❌ 读取文件失败: {e}")
                        file_result["issues"].append(f"读取失败: {e}")
                        results["invalid_files"].append(config_path)
                else:
                    print(f"   ❌ 路径存在但不是文件")
                    file_result["issues"].append("不是文件")
                    results["invalid_files"].append(config_path)
            else:
                print(f"   ⚠️  配置文件不存在")
                results["missing_files"].append(config_path)
            
            results["config_files"][config_path] = file_result
        
        return results
    
    def test_file_operations(self) -> Dict:
        """测试文件操作"""
        print("\n🔍 测试文件操作权限...")
        
        results = {
            "write_tests": {},
            "read_tests": {},
            "delete_tests": {},
            "failed_operations": []
        }
        
        # 测试目录列表
        test_dirs = ["assets", "storage", "exports"]
        
        for test_dir in test_dirs:
            dir_path = os.path.join(self.base_path, test_dir)
            
            print(f"\n📁 测试目录: {test_dir}")
            
            if not os.path.exists(dir_path):
                print(f"   ⚠️  目录不存在，跳过测试")
                continue
            
            # 写入测试
            write_result = self._test_write_operation(dir_path)
            results["write_tests"][test_dir] = write_result
            
            if write_result["success"]:
                print(f"   ✅ 写入测试通过")
                
                # 读取测试
                read_result = self._test_read_operation(write_result["test_file"])
                results["read_tests"][test_dir] = read_result
                
                if read_result["success"]:
                    print(f"   ✅ 读取测试通过")
                else:
                    print(f"   ❌ 读取测试失败: {read_result['error']}")
                    results["failed_operations"].append(f"{test_dir}:读取")
                
                # 删除测试
                delete_result = self._test_delete_operation(write_result["test_file"])
                results["delete_tests"][test_dir] = delete_result
                
                if delete_result["success"]:
                    print(f"   ✅ 删除测试通过")
                else:
                    print(f"   ❌ 删除测试失败: {delete_result['error']}")
                    results["failed_operations"].append(f"{test_dir}:删除")
            else:
                print(f"   ❌ 写入测试失败: {write_result['error']}")
                results["failed_operations"].append(f"{test_dir}:写入")
        
        return results
    
    def _test_write_operation(self, dir_path: str) -> Dict:
        """测试写入操作"""
        try:
            test_file = os.path.join(dir_path, f"test_write_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tmp")
            test_content = f"测试文件 - 创建时间: {datetime.now()}"
            
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            return {
                "success": True,
                "test_file": test_file,
                "content_length": len(test_content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "test_file": None
            }
    
    def _test_read_operation(self, file_path: str) -> Dict:
        """测试读取操作"""
        if not file_path or not os.path.exists(file_path):
            return {
                "success": False,
                "error": "测试文件不存在"
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "content_length": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_delete_operation(self, file_path: str) -> Dict:
        """测试删除操作"""
        if not file_path or not os.path.exists(file_path):
            return {
                "success": False,
                "error": "测试文件不存在"
            }
        
        try:
            os.remove(file_path)
            return {
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def check_disk_space(self) -> Dict:
        """检查磁盘空间"""
        print("\n🔍 检查磁盘空间...")
        
        results = {
            "disk_usage": {},
            "warnings": [],
            "critical_issues": []
        }
        
        # 检查主要目录的磁盘使用情况
        check_paths = [self.base_path]
        
        for path in check_paths:
            if os.path.exists(path):
                try:
                    # 获取磁盘使用情况
                    total, used, free = shutil.disk_usage(path)
                    
                    total_gb = total / (1024**3)
                    used_gb = used / (1024**3)
                    free_gb = free / (1024**3)
                    usage_percent = (used / total) * 100
                    
                    disk_info = {
                        "path": path,
                        "total_gb": round(total_gb, 2),
                        "used_gb": round(used_gb, 2),
                        "free_gb": round(free_gb, 2),
                        "usage_percent": round(usage_percent, 2)
                    }
                    
                    results["disk_usage"][path] = disk_info
                    
                    print(f"📊 磁盘使用情况 ({path}):")
                    print(f"   总容量: {disk_info['total_gb']} GB")
                    print(f"   已使用: {disk_info['used_gb']} GB ({disk_info['usage_percent']}%)")
                    print(f"   可用空间: {disk_info['free_gb']} GB")
                    
                    # 检查警告条件
                    if usage_percent > 90:
                        warning = f"磁盘使用率过高: {usage_percent}%"
                        results["critical_issues"].append(warning)
                        print(f"   🚨 {warning}")
                    elif usage_percent > 80:
                        warning = f"磁盘使用率较高: {usage_percent}%"
                        results["warnings"].append(warning)
                        print(f"   ⚠️  {warning}")
                    
                    if free_gb < 1:
                        warning = f"可用空间不足: {free_gb} GB"
                        results["critical_issues"].append(warning)
                        print(f"   🚨 {warning}")
                    elif free_gb < 5:
                        warning = f"可用空间较少: {free_gb} GB"
                        results["warnings"].append(warning)
                        print(f"   ⚠️  {warning}")
                    
                except Exception as e:
                    print(f"   ❌ 获取磁盘信息失败: {e}")
        
        return results
    
    def generate_recommendations(self, dir_results: Dict, config_results: Dict, 
                               ops_results: Dict, disk_results: Dict) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 目录相关建议
        if dir_results["missing_required"]:
            recommendations.append(f"创建缺失的必需目录: {', '.join(dir_results['missing_required'])}")
        
        if dir_results["permission_issues"]:
            recommendations.append(f"修复目录权限问题: {', '.join(dir_results['permission_issues'])}")
        
        # 配置文件建议
        if config_results["missing_files"]:
            recommendations.append("创建缺失的配置文件，参考.example文件")
        
        # 文件操作建议
        if ops_results["failed_operations"]:
            recommendations.append(f"修复文件操作权限问题: {', '.join(ops_results['failed_operations'])}")
        
        # 磁盘空间建议
        if disk_results["critical_issues"]:
            recommendations.append("紧急清理磁盘空间或扩容")
        elif disk_results["warnings"]:
            recommendations.append("监控磁盘使用情况，考虑清理临时文件")
        
        return recommendations
    
    def run_full_validation(self) -> Dict:
        """运行完整的文件存储验证"""
        print("=" * 60)
        print("📁 PreVis PRO - 文件存储系统验证")
        print("=" * 60)
        print(f"📍 基础路径: {self.base_path}")
        print()
        
        try:
            # 1. 检查目录结构
            dir_results = self.check_directory_structure()
            
            # 2. 检查配置文件
            config_results = self.check_config_files()
            
            # 3. 测试文件操作
            ops_results = self.test_file_operations()
            
            # 4. 检查磁盘空间
            disk_results = self.check_disk_space()
            
            # 5. 生成建议
            recommendations = self.generate_recommendations(
                dir_results, config_results, ops_results, disk_results
            )
            
            # 生成报告
            report = {
                "timestamp": datetime.now().isoformat(),
                "base_path": self.base_path,
                "directory_structure": dir_results,
                "config_files": config_results,
                "file_operations": ops_results,
                "disk_space": disk_results,
                "recommendations": recommendations,
                "summary": {
                    "total_directories": dir_results["total_checked"],
                    "existing_directories": dir_results["total_existing"],
                    "missing_required": len(dir_results["missing_required"]),
                    "permission_issues": len(dir_results["permission_issues"]),
                    "failed_operations": len(ops_results["failed_operations"]),
                    "disk_warnings": len(disk_results["warnings"]),
                    "disk_critical": len(disk_results["critical_issues"])
                }
            }
            
            return report
            
        except Exception as e:
            print(f"❌ 验证过程中发生错误: {e}")
            return {
                "error": str(e),
                "base_path": self.base_path
            }

def print_report_summary(report: Dict):
    """打印报告摘要"""
    print("\n" + "=" * 60)
    print("📋 文件存储验证报告摘要")
    print("=" * 60)
    
    if "error" in report:
        print(f"❌ 验证失败: {report['error']}")
        return
    
    summary = report["summary"]
    
    print(f"📁 目录检查: {summary['existing_directories']}/{summary['total_directories']} 个目录存在")
    
    if summary["missing_required"] > 0:
        print(f"❌ 缺失必需目录: {summary['missing_required']} 个")
    
    if summary["permission_issues"] > 0:
        print(f"⚠️  权限问题: {summary['permission_issues']} 个目录")
    
    if summary["failed_operations"] > 0:
        print(f"❌ 文件操作失败: {summary['failed_operations']} 个")
    
    if summary["disk_critical"] > 0:
        print(f"🚨 磁盘空间严重不足: {summary['disk_critical']} 个问题")
    elif summary["disk_warnings"] > 0:
        print(f"⚠️  磁盘空间警告: {summary['disk_warnings']} 个")
    
    if report["recommendations"]:
        print("\n💡 修复建议:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"   {i}. {rec}")
    
    # 确定整体状态
    if (summary["missing_required"] > 0 or 
        summary["failed_operations"] > 0 or 
        summary["disk_critical"] > 0):
        print(f"\n🎯 整体状态: ❌ 需要修复")
    elif (summary["permission_issues"] > 0 or 
          summary["disk_warnings"] > 0):
        print(f"\n🎯 整体状态: ⚠️  有警告")
    else:
        print(f"\n🎯 整体状态: ✅ 正常")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PreVis PRO 文件存储系统验证工具')
    parser.add_argument('--output', help='输出报告到JSON文件')
    parser.add_argument('--create-missing', action='store_true', help='自动创建缺失的目录')
    
    args = parser.parse_args()
    
    # 创建验证器
    validator = FileStorageValidator()
    
    # 运行验证
    report = validator.run_full_validation()
    
    # 打印摘要
    print_report_summary(report)
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细报告已保存到: {args.output}")
    
    # 自动创建缺失目录
    if args.create_missing and "directory_structure" in report:
        missing_dirs = report["directory_structure"]["missing_required"]
        if missing_dirs:
            print(f"\n🔧 自动创建缺失目录...")
            for dir_path in missing_dirs:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"   ✅ 创建目录: {dir_path}")
                except Exception as e:
                    print(f"   ❌ 创建失败: {dir_path} - {e}")
    
    # 返回状态码
    if "error" in report:
        return 1
    
    summary = report["summary"]
    if (summary["missing_required"] > 0 or 
        summary["failed_operations"] > 0 or 
        summary["disk_critical"] > 0):
        return 1
    elif (summary["permission_issues"] > 0 or 
          summary["disk_warnings"] > 0):
        return 2
    else:
        return 0

if __name__ == "__main__":
    exit(main())