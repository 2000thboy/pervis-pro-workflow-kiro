# -*- coding: utf-8 -*-
"""
Wizard API 端点测试

验证 wizard.py 的 API 端点是否正确工作
"""

import asyncio
import sys
sys.path.insert(0, 'backend')

from fastapi.testclient import TestClient


def create_test_app():
    """创建测试应用"""
    from fastapi import FastAPI
    from routers.wizard import router
    
    app = FastAPI()
    app.include_router(router, prefix="/api/wizard")
    return app


def test_health_check():
    """测试健康检查端点"""
    print("\n=== 测试 /api/wizard/health ===")
    app = create_test_app()
    client = TestClient(app)
    
    response = client.get("/api/wizard/health")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 健康检查通过")
        print(f"  - 状态: {data.get('status')}")
        print(f"  - Agent 状态:")
        for agent, status in data.get('agents', {}).items():
            print(f"    - {agent}: {status}")
        return True
    else:
        print(f"✗ 健康检查失败: {response.text}")
        return False


def test_parse_script():
    """测试剧本解析端点"""
    print("\n=== 测试 /api/wizard/parse-script ===")
    app = create_test_app()
    client = TestClient(app)
    
    test_script = """
INT. 咖啡厅 - 日

张三坐在窗边，看着窗外的雨。

张三
（自言自语）
今天的雨下得真大。

李四走进咖啡厅，看到张三。

李四
张三！好久不见！

EXT. 街道 - 夜

张三和李四走在街上。
"""
    
    response = client.post(
        "/api/wizard/parse-script",
        json={
            "script_content": test_script,
            "project_id": "test_project"
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 剧本解析成功")
        print(f"  - 任务ID: {data.get('task_id')}")
        print(f"  - 状态: {data.get('status')}")
        print(f"  - 场次数: {data.get('total_scenes')}")
        print(f"  - 角色数: {len(data.get('characters', []))}")
        
        for scene in data.get('scenes', []):
            print(f"  - 场次 {scene['scene_number']}: {scene['heading']}")
        
        for char in data.get('characters', []):
            print(f"  - 角色: {char['name']} (对话 {char['dialogue_count']} 次)")
        
        return True
    else:
        print(f"✗ 剧本解析失败: {response.text}")
        return False


def test_process_assets():
    """测试素材处理端点"""
    print("\n=== 测试 /api/wizard/process-assets ===")
    app = create_test_app()
    client = TestClient(app)
    
    response = client.post(
        "/api/wizard/process-assets",
        json={
            "project_id": "test_project",
            "asset_paths": [
                "角色_张三.jpg",
                "场景_咖啡厅.png",
                "参考资料.pdf"
            ],
            "auto_classify": True
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 素材处理成功")
        print(f"  - 任务ID: {data.get('task_id')}")
        print(f"  - 状态: {data.get('status')}")
        print(f"  - 处理总数: {data.get('total_processed')}")
        print(f"  - 成功: {data.get('success_count')}")
        
        for result in data.get('results', []):
            print(f"  - {result['asset_path']} -> {result['category']} (置信度: {result['confidence']})")
        
        return True
    else:
        print(f"✗ 素材处理失败: {response.text}")
        return False


def test_recall_assets():
    """测试素材召回端点"""
    print("\n=== 测试 /api/wizard/recall-assets ===")
    app = create_test_app()
    client = TestClient(app)
    
    response = client.post(
        "/api/wizard/recall-assets",
        json={
            "scene_id": "test_scene_1",
            "query": "咖啡厅 白天 对话",
            "tags": ["室内", "日景"],
            "strategy": "hybrid"
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 素材召回成功")
        print(f"  - 场次ID: {data.get('scene_id')}")
        print(f"  - 候选数: {len(data.get('candidates', []))}")
        print(f"  - 是否有匹配: {data.get('has_match')}")
        print(f"  - 占位符消息: {data.get('placeholder_message')}")
        return True
    else:
        print(f"✗ 素材召回失败: {response.text}")
        return False


def test_review_content():
    """测试内容审核端点"""
    print("\n=== 测试 /api/wizard/review-content ===")
    app = create_test_app()
    client = TestClient(app)
    
    response = client.post(
        "/api/wizard/review-content",
        json={
            "project_id": "test_project",
            "content": {"logline": "一个关于友情的故事"},
            "content_type": "logline"
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 内容审核成功")
        print(f"  - 状态: {data.get('status')}")
        print(f"  - 通过检查: {data.get('passed_checks')}")
        print(f"  - 建议: {data.get('suggestions')}")
        return True
    else:
        print(f"✗ 内容审核失败: {response.text}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Wizard API 端点测试")
    print("=" * 60)
    
    results = []
    
    results.append(test_health_check())
    results.append(test_parse_script())
    results.append(test_process_assets())
    results.append(test_recall_assets())
    results.append(test_review_content())
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n✓ 所有 API 端点测试通过！")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())



def test_create_project():
    """测试项目创建 API"""
    print("\n=== 测试 /api/wizard/create-project ===")
    
    app = create_test_app()
    client = TestClient(app)
    
    # 测试成功创建
    response = client.post("/api/wizard/create-project", json={
        "title": "测试项目",
        "project_type": "short_film",
        "duration_minutes": 15.0,
        "aspect_ratio": "16:9",
        "frame_rate": 24.0,
        "resolution": "1920x1080",
        "synopsis": "这是一个测试故事"
    })
    
    assert response.status_code == 200
    data = response.json()
    print(f"创建响应: {data}")
    
    assert data["success"] is True
    assert data["project_id"] is not None
    assert data["project_id"].startswith("proj_")
    
    # 测试缺少标题
    response = client.post("/api/wizard/create-project", json={
        "title": "",
        "project_type": "short_film"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert len(data["validation_errors"]) > 0
    print(f"验证错误: {data['validation_errors']}")
    
    print("✅ 项目创建 API 测试通过")


def test_validate_project():
    """测试项目验证 API"""
    print("\n=== 测试 /api/wizard/validate-project ===")
    
    app = create_test_app()
    client = TestClient(app)
    
    # 测试完整数据
    response = client.post("/api/wizard/validate-project", json={
        "title": "测试项目",
        "project_type": "short_film",
        "duration_minutes": 15.0,
        "aspect_ratio": "16:9",
        "frame_rate": 24.0,
        "resolution": "1920x1080",
        "script_content": "INT. 房间 - 日\n角色A走进房间。",
        "synopsis": "这是一个测试故事"
    })
    
    assert response.status_code == 200
    data = response.json()
    print(f"验证响应: {data}")
    
    assert data["is_valid"] is True
    assert data["completion_percentage"] == 100.0
    assert len(data["errors"]) == 0
    
    # 测试缺少必填字段
    response = client.post("/api/wizard/validate-project", json={
        "duration_minutes": 15.0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert len(data["missing_required"]) > 0
    print(f"缺失字段: {data['missing_required']}")
    
    # 测试格式错误
    response = client.post("/api/wizard/validate-project", json={
        "title": "测试",
        "project_type": "short_film",
        "aspect_ratio": "invalid",
        "resolution": "invalid"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    print(f"格式错误: {[e['message'] for e in data['errors']]}")
    
    print("✅ 项目验证 API 测试通过")


def test_project_crud():
    """测试项目 CRUD 操作"""
    print("\n=== 测试项目 CRUD 操作 ===")
    
    app = create_test_app()
    client = TestClient(app)
    
    # 创建项目
    response = client.post("/api/wizard/create-project", json={
        "title": "CRUD测试项目",
        "project_type": "advertisement"
    })
    
    assert response.status_code == 200
    project_id = response.json()["project_id"]
    print(f"创建项目: {project_id}")
    
    # 获取项目
    response = client.get(f"/api/wizard/project/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "CRUD测试项目"
    print(f"获取项目: {data['title']}")
    
    # 更新项目
    response = client.put(f"/api/wizard/project/{project_id}", json={
        "title": "更新后的标题",
        "synopsis": "新的故事概要"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["project"]["title"] == "更新后的标题"
    print(f"更新项目: {data['project']['title']}")
    
    # 列出项目
    response = client.get("/api/wizard/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    print(f"项目列表: {data['total']} 个项目")
    
    # 删除项目
    response = client.delete(f"/api/wizard/project/{project_id}")
    assert response.status_code == 200
    print(f"删除项目: {project_id}")
    
    # 确认删除
    response = client.get(f"/api/wizard/project/{project_id}")
    assert response.status_code == 404
    
    print("✅ 项目 CRUD 测试通过")


if __name__ == "__main__":
    test_health_check()
    test_parse_script()
    test_process_assets()
    test_recall_assets()
    test_review_content()
    test_create_project()
    test_validate_project()
    test_project_crud()
    print("\n🎉 所有 Wizard API 测试通过！")
