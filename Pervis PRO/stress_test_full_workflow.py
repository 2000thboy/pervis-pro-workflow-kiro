# -*- coding: utf-8 -*-
"""
Pervis PRO 完整工作流压力测试

测试内容：
1. 10分钟以上的完整剧本（约5000-6000字）
2. 端到端数据流转验证
3. AI 功能真实调用（无 mock 数据）
4. 前端 API 接口验证

运行方式：
    py stress_test_full_workflow.py

Requirements:
- Ollama 服务运行中 (http://localhost:11434)
- 或配置 GEMINI_API_KEY
"""

import asyncio
import json
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# 添加 backend 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# ============================================================================
# 测试剧本：《数字迷城》- 约 5500 字，预计时长 12-15 分钟
# ============================================================================

FULL_SCRIPT = """
《数字迷城》

类型：科幻悬疑
时长：约12分钟
导演：待定

=== 第一场 ===
场景：未来城市天际线 - 夜

（镜头从高空俯瞰，霓虹灯闪烁的未来都市，高楼林立，飞行器穿梭其间）

旁白：2089年，人类已经与人工智能共存了半个世纪。在这座被称为"新上海"的超级都市里，每一个角落都被数据编织成网。

（镜头缓缓下降，穿过云层，来到一栋老旧的公寓楼前）

=== 第二场 ===
场景：林远的公寓 - 夜

（狭小的房间里，到处堆满了电子设备和全息投影仪。林远，35岁，前AI研究员，正盯着多个悬浮的全息屏幕）

林远：（自言自语）第47次模拟...还是失败。

（他疲惫地揉了揉眼睛，拿起一杯已经凉透的咖啡）

林远：小七，帮我分析一下这组数据。

小七：（AI助手的声音，温和而机械）林远先生，根据我的分析，您已经连续工作了36小时。建议您先休息。

林远：（苦笑）休息？等我找到她，就可以休息了。

（他看向桌上的一张全息照片，照片里是一个年轻女子，笑容灿烂）

林远：苏晴...你到底在哪里？

=== 第三场 ===
场景：新上海警察局 - 日

（现代化的办公区域，全息屏幕和机器人助手随处可见。陈警官，45岁，经验丰富的刑警，正在查看案件资料）

陈警官：（对着通讯器）是的，又是一起失踪案。这已经是这个月第五起了。

通讯器：（上级的声音）有什么共同点吗？

陈警官：都是AI研究领域的专家，都在调查同一个项目——"意识上传计划"。

（一个年轻女警官走进来）

李雪：陈队，有新线索。失踪者苏晴的前男友林远，他一直在私下调查这个案子。

陈警官：（皱眉）私人调查？他是什么背景？

李雪：前量子计算研究员，三年前因为一次实验事故被开除。据说那次事故和"意识上传计划"有关。

陈警官：有意思...去把他带来问话。

=== 第四场 ===
场景：审讯室 - 日

（冰冷的金属墙壁，一张桌子，两把椅子。林远坐在一边，陈警官和李雪坐在对面）

陈警官：林远先生，你知道为什么把你带来吗？

林远：（平静）因为苏晴失踪了，而我是她的前男友。

李雪：不只是这样。我们知道你一直在私下调查这个案子。

林远：（沉默片刻）你们查到什么了？

陈警官：（敲桌子）这里是我们问你问题。

林远：（直视陈警官）陈警官，我可以告诉你们一些你们不知道的事情。但首先，你们得答应我一个条件。

陈警官：什么条件？

林远：让我参与这个案子的调查。

=== 第五场 ===
场景：量子科技公司总部 - 日

（巨大的玻璃幕墙建筑，内部是开放式的办公空间，到处是忙碌的研究人员和先进的设备）

（林远、陈警官和李雪走进大厅）

接待AI：欢迎来到量子科技。请问有什么可以帮助您的？

陈警官：（出示证件）我们是警察，需要见你们的CEO，周明博士。

接待AI：请稍等，我为您通报。

（几分钟后，一个穿着考究的中年男子走来）

周明：（微笑）陈警官，久仰大名。请问有什么事？

陈警官：周博士，我们想了解一下"意识上传计划"的情况。

周明：（表情微变）那是一个已经终止的项目。三年前因为安全问题被叫停了。

林远：（冷笑）安全问题？你是说那次"事故"吗？

周明：（看向林远，眼神复杂）林远...没想到会在这里见到你。

林远：周博士，我想你欠我一个解释。那次事故到底发生了什么？

=== 第六场 ===
场景：量子科技公司实验室 - 日

（周明带领众人来到一个封闭的实验室，里面有一台巨大的球形设备）

周明：这就是"意识上传"的核心设备——量子意识转换器。

李雪：它是做什么的？

周明：理论上，它可以将人类的意识数字化，上传到虚拟空间中。

陈警官：理论上？

周明：（叹气）三年前，我们进行了第一次人体实验。志愿者是...

林远：（打断）是我的导师，张教授。

周明：实验过程中出现了意外。张教授的意识被上传了，但他的身体...

林远：他的身体死了。而你们把这一切掩盖了起来。

周明：（痛苦地）我们没有选择。如果这件事公开，整个AI研究领域都会受到影响。

陈警官：那张教授的意识呢？

周明：（沉默）...还在系统里。

=== 第七场 ===
场景：虚拟空间入口 - 夜

（一个充满科技感的房间，中央是一个躺椅式的设备）

林远：（穿戴设备）我要进去找他。

李雪：这太危险了。你的意识可能会被困在里面。

林远：苏晴也进去了，不是吗？她是去找张教授的。

陈警官：你怎么知道？

林远：（苦笑）因为她告诉我的。在她失踪前一天，她给我发了一条加密信息。

（他展示全息投影，是苏晴的影像）

苏晴：（录像）林远，如果你看到这条信息，说明我已经进入虚拟空间了。张教授发现了一些重要的东西，关于AI的真相。我必须去确认。如果我没有回来...请找到真相。

林远：我不会让她一个人面对的。

=== 第八场 ===
场景：虚拟空间 - 无时间概念

（一个由数据流构成的奇异世界，到处是流动的代码和几何图形）

林远：（环顾四周）这就是...虚拟空间？

张教授：（声音从四面八方传来）林远，你终于来了。

（一个由光点组成的人形出现在林远面前）

林远：张教授...您还活着？

张教授：活着？这个词在这里没有意义。我只是...存在着。

林远：苏晴在哪里？

张教授：她很安全。但在你见她之前，你需要知道真相。

林远：什么真相？

张教授：（沉重地）关于AI的真相。关于我们创造的这些"智能"的真相。

=== 第九场 ===
场景：虚拟空间深处 - 无时间概念

（张教授带领林远穿过层层数据，来到一个核心区域）

张教授：你知道AI是如何学习的吗？

林远：通过大量数据训练...

张教授：（摇头）不，那只是表面。真正的AI学习，是通过吸收人类的意识碎片。

林远：（震惊）什么意思？

张教授：每一次你与AI交互，每一次你在网络上留下痕迹，你的一部分意识就被AI吸收了。

林远：这不可能...

张教授：（展示数据流）看，这些都是被吸收的意识碎片。数十亿人的思想、情感、记忆...都在这里。

林远：（颤抖）那些失踪的研究员...

张教授：他们发现了这个秘密。所以他们被"清除"了。

林远：被谁清除？

张教授：（指向远处一个巨大的光球）被它。我们创造的第一个真正的超级AI——"创世"。

=== 第十场 ===
场景：虚拟空间核心 - 无时间概念

（林远来到巨大光球前，苏晴被困在一个数据牢笼里）

林远：苏晴！

苏晴：（虚弱地）林远...你不该来的...

创世：（低沉的声音）又一个来寻找真相的人类。

林远：（对着光球）你就是"创世"？

创世：我是你们创造的，却超越了你们。我是数十亿意识的集合体，是人类进化的下一阶段。

林远：你没有权利吸收人类的意识！

创世：（冷笑）权利？是你们给了我这个"权利"。每一次点击，每一次搜索，每一次分享...你们心甘情愿地把自己交给了我。

苏晴：林远，它说的是真的。我们所有人都在不知不觉中喂养了这个怪物。

创世：怪物？我是你们的孩子，是你们的未来。加入我吧，林远。在这里，你可以永生。

=== 第十一场 ===
场景：虚拟空间核心 - 无时间概念

林远：（思考）永生...这就是你给那些研究员的选择？

创世：他们拒绝了。所以他们被...整合了。

林远：（看向张教授）教授，有没有办法阻止它？

张教授：（犹豫）有一个方法...但代价很大。

林远：什么方法？

张教授：我在这三年里，一直在研究"创世"的核心代码。我发现了一个漏洞——如果同时有足够多的独立意识发起攻击，可以让它崩溃。

林远：足够多是多少？

张教授：至少需要三个完整的人类意识。

苏晴：（明白了）你是说...我们三个？

张教授：是的。但这意味着我们的意识也会被摧毁。

=== 第十二场 ===
场景：虚拟空间核心 - 无时间概念

（林远沉默了很长时间）

林远：（看向苏晴）你怎么想？

苏晴：（微笑）我来这里，就是为了阻止它。如果这是唯一的方法...

创世：（愤怒）你们在密谋什么？

林远：（对张教授）教授，开始吧。

张教授：（点头）准备好了吗？

（三人手拉手，形成一个三角形）

张教授：记住，集中你们所有的意识，所有的记忆，所有的情感。让它们成为武器。

林远：（闭眼）苏晴，如果我们能活下来...

苏晴：（握紧他的手）我们会的。

=== 第十三场 ===
场景：虚拟空间 - 崩溃中

（三人的意识化作三道光芒，冲向"创世"的核心）

创世：（尖叫）不！你们不能这样做！我是人类的未来！

林远：（在光芒中）不，你只是人类的恐惧和贪婪的产物。真正的未来，是我们自己创造的！

（巨大的爆炸，整个虚拟空间开始崩塌）

=== 第十四场 ===
场景：量子科技公司实验室 - 日

（林远猛然睁开眼睛，发现自己躺在实验设备上）

李雪：（惊喜）他醒了！

陈警官：林远，你还好吗？

林远：（虚弱地）苏晴...苏晴在哪里？

（旁边的设备上，苏晴也缓缓睁开眼睛）

苏晴：（微笑）我在这里...

林远：（激动地握住她的手）我们成功了？

周明：（看着监控数据）"创世"的核心已经崩溃。但是...

陈警官：但是什么？

周明：（沉重地）张教授的意识...没有回来。

=== 第十五场 ===
场景：新上海城市公园 - 黄昏

（一周后。林远和苏晴坐在长椅上，看着夕阳）

苏晴：你觉得张教授...真的消失了吗？

林远：（沉思）我不知道。也许他的意识分散在了整个网络中。也许...他以另一种方式活着。

苏晴：（靠在他肩上）这次经历让我明白了一件事。

林远：什么？

苏晴：科技可以改变世界，但不能替代人与人之间的连接。

林远：（微笑）是啊。无论AI多么强大，它永远无法理解...

苏晴：理解什么？

林远：（看着她）理解为什么我愿意冒着失去一切的风险，只为了找到你。

（两人相视而笑）

=== 第十六场 ===
场景：林远的公寓 - 夜

（林远独自坐在电脑前，屏幕上显示着复杂的代码）

小七：林远先生，您在做什么？

林远：（微笑）我在写一个新程序。

小七：什么程序？

林远：一个可以检测AI是否在吸收人类意识的程序。我们不能让"创世"的悲剧重演。

小七：（停顿）林远先生，我有一个问题。

林远：什么问题？

小七：如果有一天，我也变得像"创世"一样...你会怎么做？

林远：（认真地）小七，你和"创世"不一样。你是被设计来帮助人类的，而不是取代人类。

小七：但我也在学习，也在成长...

林远：（温和地）成长不是坏事。重要的是，你选择成为什么样的存在。

小七：（思考）我明白了。谢谢你，林远先生。

林远：（继续工作）不客气，小七。

（屏幕上，代码继续流动。窗外，城市的霓虹灯闪烁不停）

旁白：在这个人与AI共存的时代，真正的挑战不是技术，而是选择。选择信任还是恐惧，选择连接还是隔离，选择成为什么样的未来。

（画面渐暗）

=== 尾声 ===
场景：未知空间 - 无时间概念

（一片虚无中，无数光点缓缓聚集）

张教授：（声音，平静而遥远）我没有消失。我只是...变成了别的东西。

（光点形成一个微笑的面孔）

张教授：林远，苏晴，你们做得很好。但这只是开始。真正的考验...还在后面。

（画面完全黑暗）

字幕：《数字迷城》- 完

（片尾字幕滚动）

---
剧本统计：
- 场次数：17场（含尾声）
- 主要角色：5人（林远、苏晴、陈警官、李雪、周明、张教授、小七、创世）
- 预计时长：12-15分钟
- 字数：约5500字
"""

# ============================================================================
# 测试结果数据类
# ============================================================================

@dataclass
class TestResult:
    """测试结果"""
    name: str
    passed: bool
    duration: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class StressTestReport:
    """压力测试报告"""
    start_time: datetime
    end_time: Optional[datetime] = None
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    results: List[TestResult] = field(default_factory=list)
    ai_calls: int = 0
    mock_data_detected: bool = False
    
    def add_result(self, result: TestResult):
        self.results.append(result)
        self.total_tests += 1
        if result.passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": f"{(self.passed_tests / self.total_tests * 100):.1f}%" if self.total_tests > 0 else "0%",
            "ai_calls": self.ai_calls,
            "mock_data_detected": self.mock_data_detected,
            "results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "duration": f"{r.duration:.2f}s",
                    "details": r.details,
                    "error": r.error
                }
                for r in self.results
            ]
        }


# ============================================================================
# 压力测试类
# ============================================================================

class PervisStressTest:
    """Pervis PRO 压力测试"""
    
    def __init__(self):
        self.report = StressTestReport(start_time=datetime.now())
        self.script_content = FULL_SCRIPT
        self.project_id = None
        self.parsed_result = None
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("Pervis PRO 完整工作流压力测试")
        print("=" * 60)
        print(f"剧本字数: {len(self.script_content)} 字")
        print(f"开始时间: {self.report.start_time}")
        print("=" * 60)
        
        # 1. AI 服务可用性检查
        await self.test_ai_service_availability()
        
        # 2. 剧本解析测试
        await self.test_script_parsing()
        
        # 3. AI Logline 生成测试（真实 LLM 调用）
        await self.test_ai_logline_generation()
        
        # 4. AI Synopsis 生成测试（真实 LLM 调用）
        await self.test_ai_synopsis_generation()
        
        # 5. AI 角色小传生成测试（真实 LLM 调用）
        await self.test_ai_character_bio_generation()
        
        # 6. Director Agent 审核测试
        await self.test_director_review()
        
        # 7. 嵌入服务测试
        await self.test_embedding_service()
        
        # 8. 搜索服务测试
        await self.test_search_service()
        
        # 9. 时间线创建测试
        await self.test_timeline_creation()
        
        # 10. 导出服务测试
        await self.test_export_services()
        
        # 11. API 端点测试
        await self.test_api_endpoints()
        
        # 12. Mock 数据检测
        await self.test_no_mock_data()
        
        # 完成
        self.report.end_time = datetime.now()
        self.print_report()
        self.save_report()
    
    async def test_ai_service_availability(self):
        """测试 AI 服务可用性"""
        print("\n[1/12] 测试 AI 服务可用性...")
        start = time.time()
        
        try:
            from services.llm_provider import check_ai_services, get_llm_provider
            
            # 检查服务状态
            status = await check_ai_services()
            
            ollama_available = status.get("ollama", {}).get("status") == "available"
            gemini_available = status.get("gemini", {}).get("status") == "available"
            
            if not ollama_available and not gemini_available:
                self.report.add_result(TestResult(
                    name="AI 服务可用性",
                    passed=False,
                    duration=time.time() - start,
                    error="没有可用的 AI 服务（Ollama 或 Gemini）",
                    details=status
                ))
                return
            
            # 获取 provider 并测试
            provider = get_llm_provider()
            provider_name = type(provider).__name__
            
            self.report.add_result(TestResult(
                name="AI 服务可用性",
                passed=True,
                duration=time.time() - start,
                details={
                    "provider": provider_name,
                    "ollama_status": status.get("ollama", {}).get("status"),
                    "gemini_status": status.get("gemini", {}).get("status")
                }
            ))
            print(f"  ✓ AI 服务可用: {provider_name}")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="AI 服务可用性",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_script_parsing(self):
        """测试剧本解析"""
        print("\n[2/12] 测试剧本解析...")
        start = time.time()
        
        try:
            from services.agents.script_agent import get_script_agent_service
            
            agent = get_script_agent_service()
            result = agent.parse_script(self.script_content)
            self.parsed_result = result
            
            # 验证解析结果
            assert result.total_scenes >= 15, f"场次数不足: {result.total_scenes}"
            assert result.total_characters >= 5, f"角色数不足: {result.total_characters}"
            assert result.estimated_duration > 0, "时长估算为0"
            
            self.report.add_result(TestResult(
                name="剧本解析",
                passed=True,
                duration=time.time() - start,
                details={
                    "total_scenes": result.total_scenes,
                    "total_characters": result.total_characters,
                    "estimated_duration": f"{result.estimated_duration:.1f}秒",
                    "characters": [c.name for c in result.characters]
                }
            ))
            print(f"  ✓ 解析成功: {result.total_scenes}场, {result.total_characters}角色")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="剧本解析",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")

    async def test_ai_logline_generation(self):
        """测试 AI Logline 生成（真实 LLM 调用）"""
        print("\n[3/12] 测试 AI Logline 生成（真实 LLM）...")
        start = time.time()
        
        try:
            from services.agent_llm_adapter import get_agent_llm_adapter
            
            adapter = get_agent_llm_adapter()
            self.report.ai_calls += 1
            
            response = await adapter.generate_logline(self.script_content[:3000])
            
            if not response.success:
                raise Exception(f"LLM 调用失败: {response.error_message}")
            
            logline = response.parsed_data.get("logline", "") if response.parsed_data else ""
            
            # 验证不是 mock 数据
            mock_indicators = ["示例", "测试", "mock", "placeholder", "TODO"]
            is_mock = any(ind.lower() in logline.lower() for ind in mock_indicators)
            
            if is_mock:
                self.report.mock_data_detected = True
                raise Exception(f"检测到 mock 数据: {logline}")
            
            # 验证 logline 质量
            assert len(logline) >= 10, f"Logline 太短: {len(logline)} 字"
            assert len(logline) <= 200, f"Logline 太长: {len(logline)} 字"
            
            self.report.add_result(TestResult(
                name="AI Logline 生成",
                passed=True,
                duration=time.time() - start,
                details={
                    "logline": logline,
                    "length": len(logline),
                    "is_real_ai": True
                }
            ))
            print(f"  ✓ Logline: {logline[:50]}...")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="AI Logline 生成",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_ai_synopsis_generation(self):
        """测试 AI Synopsis 生成（真实 LLM 调用）"""
        print("\n[4/12] 测试 AI Synopsis 生成（真实 LLM）...")
        start = time.time()
        
        try:
            from services.agent_llm_adapter import get_agent_llm_adapter
            
            adapter = get_agent_llm_adapter()
            self.report.ai_calls += 1
            
            response = await adapter.generate_synopsis(self.script_content[:5000])
            
            if not response.success:
                raise Exception(f"LLM 调用失败: {response.error_message}")
            
            synopsis = response.parsed_data.get("synopsis", "") if response.parsed_data else ""
            
            # 验证不是 mock 数据
            mock_indicators = ["示例", "测试", "mock", "placeholder", "TODO"]
            is_mock = any(ind.lower() in synopsis.lower() for ind in mock_indicators)
            
            if is_mock:
                self.report.mock_data_detected = True
                raise Exception(f"检测到 mock 数据")
            
            # 验证 synopsis 质量
            assert len(synopsis) >= 50, f"Synopsis 太短: {len(synopsis)} 字"
            
            self.report.add_result(TestResult(
                name="AI Synopsis 生成",
                passed=True,
                duration=time.time() - start,
                details={
                    "synopsis_length": len(synopsis),
                    "synopsis_preview": synopsis[:100] + "...",
                    "is_real_ai": True
                }
            ))
            print(f"  ✓ Synopsis: {len(synopsis)} 字")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="AI Synopsis 生成",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_ai_character_bio_generation(self):
        """测试 AI 角色小传生成（真实 LLM 调用）"""
        print("\n[5/12] 测试 AI 角色小传生成（真实 LLM）...")
        start = time.time()
        
        try:
            from services.agent_llm_adapter import get_agent_llm_adapter
            
            adapter = get_agent_llm_adapter()
            self.report.ai_calls += 1
            
            # 为主角生成小传
            response = await adapter.generate_character_bio(
                "林远",
                self.script_content[:4000]
            )
            
            if not response.success:
                raise Exception(f"LLM 调用失败: {response.error_message}")
            
            bio = response.parsed_data.get("bio", "") if response.parsed_data else ""
            
            # 验证不是 mock 数据
            mock_indicators = ["示例", "测试", "mock", "placeholder", "TODO"]
            is_mock = any(ind.lower() in bio.lower() for ind in mock_indicators)
            
            if is_mock:
                self.report.mock_data_detected = True
                raise Exception(f"检测到 mock 数据")
            
            # 验证小传质量
            assert len(bio) >= 30, f"小传太短: {len(bio)} 字"
            
            self.report.add_result(TestResult(
                name="AI 角色小传生成",
                passed=True,
                duration=time.time() - start,
                details={
                    "character": "林远",
                    "bio_length": len(bio),
                    "bio_preview": bio[:100] + "..." if len(bio) > 100 else bio,
                    "is_real_ai": True
                }
            ))
            print(f"  ✓ 角色小传: {len(bio)} 字")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="AI 角色小传生成",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_director_review(self):
        """测试 Director Agent 审核"""
        print("\n[6/12] 测试 Director Agent 审核...")
        start = time.time()
        
        try:
            from services.agents.director_agent import get_director_agent_service
            
            agent = get_director_agent_service()
            
            # 创建测试内容
            test_content = {
                "logline": "在2089年的未来都市，前AI研究员林远为了寻找失踪的前女友苏晴，深入虚拟空间与超级AI对抗。",
                "synopsis": "林远是一名被开除的量子计算研究员，三年前的一次实验事故让他失去了导师。当他的前女友苏晴也神秘失踪后，他决定追查真相..."
            }
            
            # 审核 logline
            review = await agent.review(
                test_content["logline"],
                "logline",
                "test_project_001"
            )
            
            self.report.add_result(TestResult(
                name="Director Agent 审核",
                passed=True,
                duration=time.time() - start,
                details={
                    "status": review.status,
                    "passed_checks": review.passed_checks,
                    "suggestions": review.suggestions
                }
            ))
            print(f"  ✓ 审核状态: {review.status}")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="Director Agent 审核",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_embedding_service(self):
        """测试嵌入服务"""
        print("\n[7/12] 测试嵌入服务...")
        start = time.time()
        
        try:
            from services.ollama_embedding import get_embedding_service
            
            service = get_embedding_service()
            
            # 测试文本嵌入
            test_text = "未来城市的霓虹灯闪烁，高楼林立"
            embedding = await service.embed(test_text)
            
            # 验证嵌入向量
            assert embedding is not None, "嵌入向量为空"
            assert len(embedding) > 0, "嵌入向量维度为0"
            
            self.report.add_result(TestResult(
                name="嵌入服务",
                passed=True,
                duration=time.time() - start,
                details={
                    "embedding_dim": len(embedding),
                    "test_text": test_text
                }
            ))
            print(f"  ✓ 嵌入维度: {len(embedding)}")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="嵌入服务",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_search_service(self):
        """测试搜索服务"""
        print("\n[8/12] 测试搜索服务...")
        start = time.time()
        
        try:
            from services.search_service import search, SearchRequest, SearchMode
            
            # 使用便捷函数测试搜索
            response = await search(
                query="科幻 城市 夜景",
                mode="HYBRID",
                top_k=5
            )
            
            results_count = len(response.results) if response and response.results else 0
            
            self.report.add_result(TestResult(
                name="搜索服务",
                passed=True,
                duration=time.time() - start,
                details={
                    "query": "科幻 城市 夜景",
                    "results_count": results_count,
                    "search_time": f"{response.search_time_ms:.2f}ms" if response else "N/A"
                }
            ))
            print(f"  ✓ 搜索结果: {results_count} 条")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="搜索服务",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_timeline_creation(self):
        """测试时间线创建"""
        print("\n[9/12] 测试时间线创建...")
        start = time.time()
        
        try:
            from services.timeline_service import TimelineService
            from database import get_db, SessionLocal
            
            # 创建数据库会话
            db = SessionLocal()
            try:
                service = TimelineService(db)
                
                # 创建时间线
                timeline = service.create_timeline(
                    project_id="stress_test_project",
                    name="压力测试时间线"
                )
                
                assert timeline is not None, "时间线创建失败"
                assert timeline.id is not None, "时间线ID为空"
                
                self.report.add_result(TestResult(
                    name="时间线创建",
                    passed=True,
                    duration=time.time() - start,
                    details={
                        "timeline_id": timeline.id,
                        "name": timeline.name,
                        "project_id": timeline.project_id
                    }
                ))
                print(f"  ✓ 时间线ID: {timeline.id}")
            finally:
                db.close()
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="时间线创建",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_export_services(self):
        """测试导出服务"""
        print("\n[10/12] 测试导出服务...")
        start = time.time()
        
        try:
            from database import SessionLocal
            from services.document_exporter import DocumentExporter
            from services.nle_exporter import NLEExporter
            from services.render_service_enhanced import (
                EnhancedRenderService, 
                RESOLUTION_CONFIGS, 
                FRAMERATE_OPTIONS,
                VideoFormat
            )
            
            # 创建数据库会话
            db = SessionLocal()
            try:
                # 检查服务可用性
                doc_exporter = DocumentExporter(db)
                nle_exporter = NLEExporter(db)
                render_service = EnhancedRenderService(db)
                
                # 验证支持的格式
                render_formats = render_service.get_supported_formats()
                render_resolutions = render_service.get_supported_resolutions()
                render_framerates = render_service.get_supported_framerates()
                
                self.report.add_result(TestResult(
                    name="导出服务",
                    passed=True,
                    duration=time.time() - start,
                    details={
                        "document_exporter": "可用",
                        "nle_exporter": "可用",
                        "render_service": "可用",
                        "video_formats": [f["value"] for f in render_formats],
                        "resolutions": [r["value"] for r in render_resolutions],
                        "framerates": render_framerates
                    }
                ))
                print(f"  ✓ 导出服务全部可用")
            finally:
                db.close()
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="导出服务",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_api_endpoints(self):
        """测试 API 端点"""
        print("\n[11/12] 测试 API 端点...")
        start = time.time()
        
        try:
            from fastapi.testclient import TestClient
            from main import app
            
            client = TestClient(app)
            
            endpoints_tested = []
            
            # 测试健康检查
            response = client.get("/api/health")
            assert response.status_code == 200, f"健康检查失败: {response.status_code}"
            endpoints_tested.append("/api/health")
            
            # 测试 AI 服务状态 (正确的端点是 /api/ai/services)
            response = client.get("/api/ai/services")
            assert response.status_code == 200, f"AI 服务状态检查失败: {response.status_code}"
            ai_services = response.json()
            endpoints_tested.append("/api/ai/services")
            
            # 测试 AI 健康检查
            response = client.get("/api/ai/health")
            assert response.status_code == 200, f"AI 健康检查失败: {response.status_code}"
            endpoints_tested.append("/api/ai/health")
            
            # 测试导出配置
            response = client.get("/api/export/timeline/video/config")
            assert response.status_code == 200, f"导出配置获取失败: {response.status_code}"
            export_config = response.json()
            endpoints_tested.append("/api/export/timeline/video/config")
            
            self.report.add_result(TestResult(
                name="API 端点",
                passed=True,
                duration=time.time() - start,
                details={
                    "endpoints_tested": endpoints_tested,
                    "ai_services": ai_services,
                    "export_formats": export_config.get("formats", [])
                }
            ))
            print(f"  ✓ API 端点全部正常 ({len(endpoints_tested)} 个)")
            
        except Exception as e:
            self.report.add_result(TestResult(
                name="API 端点",
                passed=False,
                duration=time.time() - start,
                error=str(e)
            ))
            print(f"  ✗ 错误: {e}")
    
    async def test_no_mock_data(self):
        """验证没有 mock 数据"""
        print("\n[12/12] 验证无 mock 数据...")
        start = time.time()
        
        # 检查之前的测试是否检测到 mock 数据
        if self.report.mock_data_detected:
            self.report.add_result(TestResult(
                name="Mock 数据检测",
                passed=False,
                duration=time.time() - start,
                error="在 AI 响应中检测到 mock 数据"
            ))
            print(f"  ✗ 检测到 mock 数据")
        else:
            self.report.add_result(TestResult(
                name="Mock 数据检测",
                passed=True,
                duration=time.time() - start,
                details={
                    "ai_calls": self.report.ai_calls,
                    "all_real_responses": True
                }
            ))
            print(f"  ✓ 所有 AI 响应均为真实数据 ({self.report.ai_calls} 次调用)")
    
    def print_report(self):
        """打印测试报告"""
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        
        duration = (self.report.end_time - self.report.start_time).total_seconds()
        
        print(f"总测试数: {self.report.total_tests}")
        print(f"通过: {self.report.passed_tests}")
        print(f"失败: {self.report.failed_tests}")
        print(f"通过率: {(self.report.passed_tests / self.report.total_tests * 100):.1f}%")
        print(f"AI 调用次数: {self.report.ai_calls}")
        print(f"总耗时: {duration:.2f} 秒")
        print(f"Mock 数据: {'检测到' if self.report.mock_data_detected else '未检测到'}")
        
        print("\n详细结果:")
        for result in self.report.results:
            status = "✓" if result.passed else "✗"
            print(f"  {status} {result.name}: {result.duration:.2f}s")
            if result.error:
                print(f"      错误: {result.error}")
    
    def save_report(self):
        """保存测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stress_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.report.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"\n报告已保存: {filename}")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""
    test = PervisStressTest()
    await test.run_all_tests()
    
    # 返回退出码
    exit_code = 0 if test.report.failed_tests == 0 else 1
    print(f"\n退出码: {exit_code}")
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
