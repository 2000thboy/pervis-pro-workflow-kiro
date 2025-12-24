import requests
import json

# 测试剧本分析API响应格式
url = "http://localhost:8000/api/script/analyze"
data = {
    "title": "测试剧本",
    "script_text": "场景1：校园\n学生们在樱花树下聊天。\n\n场景2：教室\n上课时间到了。"
}

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("响应结构:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 检查beats结构
        if 'beats' in result:
            print(f"\nBeats数量: {len(result['beats'])}")
            for i, beat in enumerate(result['beats']):
                print(f"Beat {i+1} 结构:")
                print(f"  键: {list(beat.keys())}")
                if 'description' in beat:
                    print(f"  描述: {beat['description'][:50]}...")
                else:
                    print(f"  ❌ 缺少description字段")
    else:
        print(f"错误: {response.text}")
        
except Exception as e:
    print(f"异常: {e}")