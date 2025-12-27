# -*- coding: utf-8 -*-
"""
系统 Agent 后端功能验证脚本

验证项目:
1. EventService 事件服务
2. HealthChecker 健康检查
3. WebSocket 端点
4. 系统 API 端点
"""

import asyncio
import sys
import os

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, success: bool, message: str = ""):
    status = "✅" if success else "❌"
    print(f"{status} {name}: {message}")


async def test_event_service():
    """测试 EventService"""
    print_section("测试 EventService")
    
    try:
        from services.event_service import event_service, EventType
        
        # 测试单例模式
        from services.event_service import EventService
        instance1 = EventService()
        instance2 = EventService()
        print_result("单例模式", instance1 is instance2, "两个实例相同")
        
        # 测试事件类型枚举
        print_result("EventType 枚举", 
                    EventType.TASK_STARTED.value == "task.started",
                    f"TASK_STARTED = {EventType.TASK_STARTED.value}")
        
        # 测试连接计数
        print_result("连接计数", 
                    event_service.connection_count == 0,
                    f"当前连接数: {event_service.connection_count}")
        
        # 测试 emit 方法（无连接时不应报错）
        await event_service.emit("test.event", {"message": "test"})
        print_result("emit 方法", True, "无连接时正常执行")
        
        # 测试便捷方法
        await event_service.emit_task_progress("task_123", 50, "测试进度")
        print_result("emit_task_progress", True, "方法调用成功")
        
        await event_service.emit_agent_status("script_agent", "working", "测试状态")
        print_result("emit_agent_status", True, "方法调用成功")
        
        await event_service.emit_system_warning("test.warning", "测试警告", {"action": "test"})
        print_result("emit_system_warning", True, "方法调用成功")
        
        return True
        
    except Exception as e:
        print_result("EventService", False, str(e))
        return False


async def test_health_checker():
    """测试 HealthChecker"""
    print_section("测试 HealthChecker")
    
    try:
        from services.health_checker import health_checker, CheckStatus
        
        # 执行完整健康检查
        result = await health_checker.check_all()
        
        print_result("健康检查执行", True, f"整体状态: {result.status}")
        
        # 显示各项检查结果
        for name, check in result.checks.items():
            status_ok = check.status in [CheckStatus.OK, CheckStatus.WARNING]
            print_result(f"  - {name}", status_ok, check.message)
        
        return True
        
    except Exception as e:
        print_result("HealthChecker", False, str(e))
        return False


def test_models():
    """测试数据模型"""
    print_section("测试数据模型")
    
    try:
        from models.system_notification import SystemNotification
        from models.background_task import BackgroundTask
        
        # 测试 SystemNotification
        notification = SystemNotification.create(
            id="test_123",
            type="task",
            level="info",
            title="测试通知",
            message="这是一条测试通知"
        )
        print_result("SystemNotification 创建", True, f"ID: {notification.id}")
        
        notification_dict = notification.to_dict()
        print_result("SystemNotification to_dict", 
                    "title" in notification_dict,
                    f"字段数: {len(notification_dict)}")
        
        # 测试 BackgroundTask
        task = BackgroundTask.create(
            id="task_456",
            type="render",
            name="测试渲染任务"
        )
        print_result("BackgroundTask 创建", True, f"ID: {task.id}")
        
        task.start()
        print_result("BackgroundTask start", 
                    task.status == "running",
                    f"状态: {task.status}")
        
        task.update_progress(50)
        print_result("BackgroundTask update_progress", 
                    task.progress == 50,
                    f"进度: {task.progress}%")
        
        task.complete({"output": "test.mp4"})
        print_result("BackgroundTask complete", 
                    task.status == "completed",
                    f"状态: {task.status}")
        
        return True
        
    except Exception as e:
        print_result("数据模型", False, str(e))
        return False


def test_router_imports():
    """测试路由导入"""
    print_section("测试路由导入")
    
    try:
        from routers.websocket import router as ws_router
        print_result("WebSocket 路由", True, "导入成功")
        
        from routers.system import router as sys_router
        print_result("System 路由", True, "导入成功")
        
        # 检查路由端点
        ws_routes = [r.path for r in ws_router.routes]
        print_result("WebSocket 端点", 
                    "/ws/events" in ws_routes,
                    f"端点: {ws_routes}")
        
        sys_routes = [r.path for r in sys_router.routes]
        print_result("System 端点", 
                    "/health" in str(sys_routes),
                    f"端点数: {len(sys_routes)}")
        
        return True
        
    except Exception as e:
        print_result("路由导入", False, str(e))
        return False


def test_database_tables():
    """测试数据库表"""
    print_section("测试数据库表")
    
    try:
        from sqlalchemy import create_engine, inspect
        
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pervis_director.db")
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)
        
        tables = inspector.get_table_names()
        
        has_notifications = "system_notifications" in tables
        has_tasks = "background_tasks" in tables
        
        print_result("system_notifications 表", has_notifications, 
                    "存在" if has_notifications else "不存在")
        print_result("background_tasks 表", has_tasks,
                    "存在" if has_tasks else "不存在")
        
        if has_notifications:
            columns = [c["name"] for c in inspector.get_columns("system_notifications")]
            print_result("  - 字段", True, f"{len(columns)} 个字段")
        
        if has_tasks:
            columns = [c["name"] for c in inspector.get_columns("background_tasks")]
            print_result("  - 字段", True, f"{len(columns)} 个字段")
        
        return has_notifications and has_tasks
        
    except Exception as e:
        print_result("数据库表", False, str(e))
        return False


async def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  Pervis PRO 系统 Agent 后端功能验证")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = []
    
    # 运行测试
    results.append(("EventService", await test_event_service()))
    results.append(("HealthChecker", await test_health_checker()))
    results.append(("数据模型", test_models()))
    results.append(("路由导入", test_router_imports()))
    results.append(("数据库表", test_database_tables()))
    
    # 汇总结果
    print_section("测试结果汇总")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        print_result(name, result, "通过" if result else "失败")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有后端测试通过！可以继续前端开发。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查问题后再继续。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
