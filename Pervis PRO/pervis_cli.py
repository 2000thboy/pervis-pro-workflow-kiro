#!/usr/bin/env python3
"""
Pervis PRO 命令行工具
无需浏览器，直接使用API进行导演工作流操作
"""

import requests
import json
import os
import sys
import time
from pathlib import Path
import argparse
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"

class PervisCLI:
    def __init__(self):
        self.base_url = BASE_URL
        self.current_project_id = None
        self.current_beats = []
    
    def check_server(self):
        """检查服务器状态"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务器正常 - {data['service']} v{data['version']}")
                return True
            else:
                print(f"❌ 服务器异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接服务器: {e}")
            print("💡 请确保后端服务正在运行: cd backend && python main.py")
            return False
    
    def analyze_script(self, title: str, script_file: str):
        """分析剧本文件"""
        print(f"📝 分析剧本: {title}")
        
        if not os.path.exists(script_file):
            print(f"❌ 剧本文件不存在: {script_file}")
            return False
        
        # 读取剧本内容
        try:
            with open(script_file, 'r', encoding='utf-8') as f:
                script_content = f.read()
        except Exception as e:
            print(f"❌ 读取剧本文件失败: {e}")
            return False
        
        # 调用API分析剧本
        script_data = {
            "title": title,
            "script_text": script_content
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/script/analyze",
                json=script_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                self.current_project_id = result['project_id']
                self.current_beats = result['beats']
                
                print(f"✅ 剧本分析成功!")
                print(f"   项目ID: {self.current_project_id}")
                print(f"   Beat数量: {len(self.current_beats)}")
                
                print(f"\n📋 Beat列表:")
                for i, beat in enumerate(self.current_beats, 1):
                    print(f"   {i}. [{beat['id']}] {beat['content'][:60]}...")
                    print(f"      情绪: {', '.join(beat.get('emotion_tags', []))}")
                    print(f"      场景: {', '.join(beat.get('scene_tags', []))}")
                    print()
                
                return True
            else:
                print(f"❌ 剧本分析失败: {response.status_code}")
                print(f"   错误: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 剧本分析异常: {e}")
            return False
    
    def upload_assets(self, asset_dir: str, max_files: int = 5):
        """批量上传素材文件"""
        print(f"📁 上传素材目录: {asset_dir}")
        
        if not self.current_project_id:
            print("❌ 请先分析剧本创建项目")
            return False
        
        if not os.path.exists(asset_dir):
            print(f"❌ 素材目录不存在: {asset_dir}")
            return False
        
        # 查找视频文件
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        video_files = []
        
        for file in os.listdir(asset_dir):
            if any(file.lower().endswith(ext) for ext in video_extensions):
                video_files.append(os.path.join(asset_dir, file))
        
        if not video_files:
            print("❌ 未找到视频文件")
            return False
        
        print(f"🔍 找到 {len(video_files)} 个视频文件")
        
        # 限制上传数量
        upload_files = video_files[:max_files]
        uploaded_count = 0
        
        for file_path in upload_files:
            print(f"\n📤 上传: {os.path.basename(file_path)}")
            
            try:
                with open(file_path, 'rb') as f:
                    files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
                    data = {'project_id': self.current_project_id}
                    
                    response = requests.post(
                        f"{self.base_url}/api/assets/upload",
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ 上传成功! Asset ID: {result['asset_id']}")
                    uploaded_count += 1
                else:
                    print(f"   ❌ 上传失败: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 上传异常: {e}")
        
        print(f"\n📊 上传完成: {uploaded_count}/{len(upload_files)} 个文件")
        
        if uploaded_count > 0:
            print("⏳ 素材正在后台处理，请稍等...")
            time.sleep(3)
        
        return uploaded_count > 0
    
    def search_assets(self, query: str, search_modes: List[str] = None, limit: int = 5):
        """多模态搜索素材"""
        print(f"🔍 搜索素材: {query}")
        
        if search_modes is None:
            search_modes = ["semantic", "visual"]
        
        search_data = {
            "query": query,
            "search_modes": search_modes,
            "limit": limit
        }
        
        # 设置权重
        if len(search_modes) == 1:
            search_data["weights"] = {search_modes[0]: 1.0}
        elif len(search_modes) == 2:
            search_data["weights"] = {search_modes[0]: 0.6, search_modes[1]: 0.4}
        else:
            search_data["weights"] = {"semantic": 0.4, "visual": 0.3, "transcription": 0.3}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/multimodal/search",
                json=search_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 搜索成功!")
                print(f"   查询意图: {result['query_intent']['primary_intent']}")
                print(f"   搜索模式: {', '.join(result['search_modes'])}")
                print(f"   结果数量: {result['total_matches']}")
                
                # 显示各模态结果
                individual_results = result.get('individual_results', {})
                if individual_results:
                    print(f"   模态分布:")
                    for mode, count in individual_results.items():
                        print(f"     {mode}: {count} 个结果")
                
                # 显示推荐结果
                if result.get('recommendations'):
                    print(f"\n📋 推荐素材:")
                    for i, rec in enumerate(result['recommendations'][:5], 1):
                        print(f"   {i}. {rec.get('filename', 'Unknown')}")
                        print(f"      相似度: {rec.get('similarity', 0):.3f}")
                        print(f"      推荐理由: {rec.get('reason', 'AI分析匹配')}")
                        print()
                
                return True
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 搜索异常: {e}")
            return False
    
    def search_for_beat(self, beat_index: int):
        """为指定Beat搜索匹配素材"""
        if not self.current_beats:
            print("❌ 请先分析剧本")
            return False
        
        if beat_index < 1 or beat_index > len(self.current_beats):
            print(f"❌ Beat索引无效，请选择1-{len(self.current_beats)}")
            return False
        
        beat = self.current_beats[beat_index - 1]
        print(f"🎯 为Beat搜索素材: {beat['content'][:50]}...")
        
        if not self.current_project_id:
            print("❌ 项目ID缺失")
            return False
        
        search_data = {
            "beat_id": beat['id'],
            "project_id": self.current_project_id,
            "limit": 5
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/search/semantic",
                json=search_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 找到 {len(result['results'])} 个匹配素材")
                
                for i, asset in enumerate(result['results'], 1):
                    print(f"   {i}. {asset['filename']}")
                    print(f"      相似度: {asset['similarity']:.3f}")
                    print(f"      推荐理由: {asset.get('reason', 'AI分析匹配')}")
                    print()
                
                return True
            else:
                print(f"❌ 搜索失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 搜索异常: {e}")
            return False
    
    def list_beats(self):
        """列出当前项目的所有Beat"""
        if not self.current_beats:
            print("❌ 请先分析剧本")
            return
        
        print(f"📋 当前项目Beat列表 (项目ID: {self.current_project_id}):")
        for i, beat in enumerate(self.current_beats, 1):
            print(f"   {i}. [{beat['id']}] {beat['content']}")
            print(f"      情绪: {', '.join(beat.get('emotion_tags', []))}")
            print(f"      场景: {', '.join(beat.get('scene_tags', []))}")
            print()
    
    def interactive_mode(self):
        """交互模式"""
        print("🎬 Pervis PRO 交互模式")
        print("输入 'help' 查看命令，输入 'quit' 退出")
        
        while True:
            try:
                cmd = input("\npervis> ").strip().lower()
                
                if cmd == 'quit' or cmd == 'exit':
                    print("👋 再见!")
                    break
                elif cmd == 'help':
                    self.show_help()
                elif cmd == 'status':
                    self.check_server()
                elif cmd == 'beats':
                    self.list_beats()
                elif cmd.startswith('search '):
                    query = cmd[7:]
                    self.search_assets(query)
                elif cmd.startswith('beat '):
                    try:
                        beat_index = int(cmd[5:])
                        self.search_for_beat(beat_index)
                    except ValueError:
                        print("❌ 请输入有效的Beat编号")
                else:
                    print("❌ 未知命令，输入 'help' 查看帮助")
                    
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    def show_help(self):
        """显示帮助信息"""
        print("""
📖 Pervis PRO CLI 命令帮助:

基础命令:
  status          - 检查服务器状态
  help            - 显示此帮助信息
  quit/exit       - 退出程序

项目操作:
  beats           - 列出当前项目的所有Beat
  search <查询>   - 多模态搜索素材
  beat <编号>     - 为指定Beat搜索匹配素材

示例:
  search 樱花飞舞的校园
  beat 1
  search 紧张的考试氛围
        """)

def main():
    parser = argparse.ArgumentParser(description="Pervis PRO 命令行工具")
    parser.add_argument("--script", help="剧本文件路径")
    parser.add_argument("--title", help="剧本标题", default="未命名剧本")
    parser.add_argument("--assets", help="素材目录路径")
    parser.add_argument("--search", help="搜索查询")
    parser.add_argument("--interactive", "-i", action="store_true", help="进入交互模式")
    
    args = parser.parse_args()
    
    cli = PervisCLI()
    
    print("🎬 Pervis PRO 命令行工具")
    print("=" * 40)
    
    # 检查服务器状态
    if not cli.check_server():
        return 1
    
    # 分析剧本
    if args.script:
        if not cli.analyze_script(args.title, args.script):
            return 1
    
    # 上传素材
    if args.assets:
        if not cli.upload_assets(args.assets):
            return 1
    
    # 搜索素材
    if args.search:
        cli.search_assets(args.search)
    
    # 交互模式
    if args.interactive:
        cli.interactive_mode()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())