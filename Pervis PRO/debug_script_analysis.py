#!/usr/bin/env python3
"""
调试剧本分析
"""

import requests
import json

def test_script_analysis():
    """测试剧本分析并打印详细结果"""
    
    script_text = """
EXT. 城市街道 - 白天

繁忙的都市街道，人来人往。车辆川流不息。

一个年轻人匆忙走过，手里拿着咖啡，眼神焦虑。

年轻人
（自言自语）
要迟到了...

他加快脚步，穿过人群。
"""
    
    response = requests.post(
        "http://localhost:8000/api/script/analyze",
        json={
            "script_text": script_text,
            "title": "测试剧本",
            "mode": "parse"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("=== 剧本分析结果 ===")
        print(f"状态: {result.get('status')}")
        print(f"处理时间: {result.get('processing_time', 0):.2f}秒")
        
        beats = result.get('beats', [])
        print(f"\nBeat数量: {len(beats)}")
        
        for i, beat in enumerate(beats):
            print(f"\n--- Beat {i+1} ---")
            print(f"内容: {beat.get('content', '')}")
            print(f"时长: {beat.get('duration', beat.get('duration_estimate', 'N/A'))}")
            print(f"情绪标签: {beat.get('emotion_tags', [])}")
            print(f"场景标签: {beat.get('scene_tags', [])}")
            print(f"动作标签: {beat.get('action_tags', [])}")
            print(f"摄影标签: {beat.get('cinematography_tags', [])}")
        
        # 打印原始JSON
        print("\n=== 原始JSON ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    else:
        print(f"请求失败: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_script_analysis()