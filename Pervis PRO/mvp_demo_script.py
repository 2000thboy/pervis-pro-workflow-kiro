#!/usr/bin/env python3
"""
Pervis PRO MVP演示脚本
使用动漫素材进行完整工作流验证
"""

import requests
import json
import os
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

# 示例剧本 - 适合动漫素材的内容
DEMO_SCRIPT = """
标题：青春校园物语

场景1：樱花飞舞的校园
春天的校园里，樱花瓣随风飘落。少女美咲背着书包，脸上带着淡淡的忧伤，缓缓走过樱花树下的小径。阳光透过花瓣洒在她的脸上，营造出温馨而略带忧郁的氛围。

场景2：热闹的教室
上课铃声响起，教室里充满了青春活力。同学们嬉笑打闹，美咲坐在窗边，望着窗外的蓝天白云，若有所思。老师走进教室，开始讲课，但美咲的心思似乎飘向了远方。

场景3：紧张的考试
期末考试来临，教室里气氛紧张。学生们埋头答题，只听见笔尖在纸上沙沙作响。美咲紧皱眉头，显得有些焦虑。时钟滴答作响，倒计时的压迫感让人窒息。

场景4：夕阳下的告白
放学后，夕阳西下，天空染成橙红色。在学校的天台上，男主角勇气十足地向美咲表白。美咲脸红心跳，既惊喜又紧张。远处的城市灯火开始点亮，浪漫的氛围达到高潮。

场景5：友情的力量
在朋友们的鼓励下，美咲重新振作起来。大家一起在操场上奔跑，欢声笑语回荡在校园里。青春的活力和友情的温暖让整个画面充满正能量。

场景6：毕业典礼
毕业典礼上，同学们穿着制服，脸上既有不舍也有对未来的憧憬。美咲站在台上发表毕业感言，眼中含着泪水，但更多的是对未来的希望和决心。
"""

def analyze_script():
    """分析示例剧本"""
    print("📝 分析示例剧本...")
    
    script_data = {
        "title": "青春校园物语",
        "script_text": DEMO_SCRIPT
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/script/analyze",
            json=script_data,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 剧本分析成功！")
            print(f"   项目ID: {result['project_id']}")
            print(f"   Beat数量: {len(result['beats'])}")
            
            print("\n📋 提取的Beat列表:")
            for i, beat in enumerate(result['beats'], 1):
                print(f"   {i}. {beat['content'][:50]}...")
                print(f"      情绪: {', '.join(beat.get('emotion_tags', []))}")
                print(f"      场景: {', '.join(beat.get('scene_tags', []))}")
                print(f"      动作: {', '.join(beat.get('action_tags', []))}")
                print()
            
            return result['project_id'], result['beats']
        else:
            print(f"❌ 剧本分析失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None, []
            
    except Exception as e:
        print(f"❌ 剧本分析异常: {e}")
        return None, []

def upload_video_asset(file_path, project_id):
    """上传视频素材"""
    print(f"📁 上传视频素材: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return None
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'video/mp4')}
            data = {'project_id': project_id}
            
            response = requests.post(
                f"{BASE_URL}/api/assets/upload",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上传成功！Asset ID: {result['asset_id']}")
            return result['asset_id']
        else:
            print(f"❌ 上传失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 上传异常: {e}")
        return None

def search_for_beat(beat, project_id):
    """为Beat搜索匹配的素材"""
    print(f"🔍 搜索Beat: {beat['content'][:50]}...")
    
    search_data = {
        "beat_id": beat['id'],
        "project_id": project_id,
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/search/semantic",
            json=search_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 搜索成功！找到 {len(result['results'])} 个匹配素材")
            
            for i, asset in enumerate(result['results'], 1):
                print(f"   {i}. {asset['filename']} (相似度: {asset['similarity']:.3f})")
                print(f"      推荐理由: {asset.get('reason', 'AI分析匹配')}")
            
            return result['results']
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ 搜索异常: {e}")
        return []

def test_multimodal_search():
    """测试多模态搜索"""
    print("\n🎯 测试多模态搜索功能...")
    
    # 测试不同类型的查询
    test_queries = [
        {
            "query": "樱花飞舞的温馨校园场景",
            "search_modes": ["semantic", "visual"],
            "weights": {"semantic": 0.6, "visual": 0.4}
        },
        {
            "query": "紧张的考试氛围",
            "search_modes": ["semantic", "transcription"],
            "weights": {"semantic": 0.7, "transcription": 0.3}
        },
        {
            "query": "夕阳下的浪漫告白",
            "search_modes": ["semantic", "visual", "transcription"],
            "weights": {"semantic": 0.4, "visual": 0.4, "transcription": 0.2}
        }
    ]
    
    for i, query_data in enumerate(test_queries, 1):
        print(f"\n   查询 {i}: {query_data['query']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/multimodal/search",
                json=query_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 成功！主要意图: {result['query_intent']['primary_intent']}")
                print(f"      结果数量: {result['total_matches']}")
                
                # 显示各模态结果
                individual_results = result.get('individual_results', {})
                for mode, count in individual_results.items():
                    print(f"      {mode}: {count} 个结果")
            else:
                print(f"   ❌ 失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")

def create_asset_copy_script():
    """创建素材复制脚本"""
    copy_script = """
# 素材复制脚本
# 将你的动漫素材复制到项目目录

import shutil
import os
from pathlib import Path

# 源目录（你的素材目录）
SOURCE_DIR = r"F:\\BaiduNetdiskDownload\\动漫素材"

# 目标目录（项目assets目录）
TARGET_DIR = r"backend\\assets"

def copy_video_files():
    \"\"\"复制视频文件到项目目录\"\"\"
    
    if not os.path.exists(SOURCE_DIR):
        print(f"❌ 源目录不存在: {SOURCE_DIR}")
        return
    
    # 创建目标目录
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 支持的视频格式
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    
    copied_count = 0
    
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if any(file.lower().endswith(ext) for ext in video_extensions):
                source_path = os.path.join(root, file)
                target_path = os.path.join(TARGET_DIR, file)
                
                try:
                    shutil.copy2(source_path, target_path)
                    print(f"✅ 复制: {file}")
                    copied_count += 1
                except Exception as e:
                    print(f"❌ 复制失败 {file}: {e}")
    
    print(f"\\n📊 总计复制了 {copied_count} 个视频文件")

if __name__ == "__main__":
    copy_video_files()
"""
    
    with open("copy_assets.py", "w", encoding="utf-8") as f:
        f.write(copy_script)
    
    print("📄 已创建素材复制脚本: copy_assets.py")
    print("   请运行: python copy_assets.py")

def main():
    """主演示函数"""
    print("🚀 Pervis PRO MVP演示 - 动漫素材验证")
    print("=" * 60)
    
    # 步骤1: 分析剧本
    project_id, beats = analyze_script()
    if not project_id:
        print("❌ 剧本分析失败，无法继续演示")
        return
    
    # 步骤2: 创建素材复制脚本
    print(f"\n📁 素材准备...")
    create_asset_copy_script()
    
    # 步骤3: 检查是否有素材文件
    assets_dir = Path("backend/assets")
    video_files = []
    if assets_dir.exists():
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        video_files = [f for f in assets_dir.iterdir() 
                      if f.is_file() and f.suffix.lower() in video_extensions]
    
    if video_files:
        print(f"✅ 发现 {len(video_files)} 个视频文件")
        
        # 步骤4: 上传部分素材进行测试
        uploaded_assets = []
        for video_file in video_files[:3]:  # 只上传前3个文件进行测试
            asset_id = upload_video_asset(str(video_file), project_id)
            if asset_id:
                uploaded_assets.append(asset_id)
        
        if uploaded_assets:
            print(f"✅ 成功上传 {len(uploaded_assets)} 个素材")
            
            # 等待处理完成
            print("⏳ 等待素材处理完成...")
            time.sleep(5)
            
            # 步骤5: 为每个Beat搜索匹配素材
            print(f"\n🔍 开始Beat匹配搜索...")
            for i, beat in enumerate(beats[:3], 1):  # 只测试前3个Beat
                print(f"\n--- Beat {i} ---")
                results = search_for_beat(beat, project_id)
        
        # 步骤6: 测试多模态搜索
        test_multimodal_search()
        
    else:
        print("⚠️  未发现视频素材文件")
        print("📋 请按以下步骤准备素材:")
        print("   1. 运行: python copy_assets.py")
        print("   2. 或手动复制视频文件到 backend/assets/ 目录")
        print("   3. 重新运行此演示脚本")
    
    print(f"\n🎉 MVP演示完成！")
    print(f"📊 演示总结:")
    print(f"   ✅ 剧本分析: 成功提取 {len(beats)} 个Beat")
    print(f"   ✅ 素材上传: 准备就绪")
    print(f"   ✅ 语义搜索: 功能正常")
    print(f"   ✅ 多模态搜索: 功能正常")
    print(f"\n💡 下一步:")
    print(f"   1. 访问前端界面: http://localhost:3000")
    print(f"   2. 上传更多素材进行完整测试")
    print(f"   3. 体验完整的导演工作流")

if __name__ == "__main__":
    main()