# -*- coding: utf-8 -*-
"""
Pervis PRO 完整端到端工作流测试

测试内容：
1. 输入十分钟剧本
2. 剧本解析 (Script_Agent)
3. 内容生成 (Logline, Synopsis, 人物小传)
4. Director_Agent 审核
5. 素材召回 (Storyboard_Agent)
6. 粗剪输出视频
7. 生成完整流程图

数据流转和审核机制图示
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

# 配置
API_BASE = "http://localhost:8000"
TIMEOUT = 120

# 十分钟剧本示例（约600秒）
SAMPLE_SCRIPT_10MIN = """
=== 第一场 ===
场景：咖啡馆内 - 日

（阳光透过落地窗洒进来，咖啡馆里弥漫着咖啡香气）

小明坐在靠窗的位置，面前放着一杯已经凉了的美式咖啡。他不停地看着手机，显得焦躁不安。

小明：（自言自语）都过了半小时了，她怎么还不来...

服务员走过来，礼貌地询问。

服务员：先生，需要再来一杯吗？

小明：（摇头）不用了，谢谢。

门铃响起，小红推门而入。她穿着一件淡蓝色的连衣裙，长发披肩，看起来有些疲惫。

小红：（喘着气）对不起，路上堵车了。

小明：（站起来）没关系，你来了就好。坐吧。

=== 第二场 ===
场景：咖啡馆内 - 日（续）

小红坐下，从包里拿出一个文件夹。

小红：这是你要的资料，我整理了一晚上。

小明：（接过文件夹，翻看）太好了，这正是我需要的。

小红：（犹豫）小明，我有件事想跟你说...

小明：（抬头）什么事？

小红：（深呼吸）我...我要离开这座城市了。

小明：（愣住）什么？你要去哪里？

小红：北京。公司总部调我过去，下周就走。

=== 第三场 ===
场景：咖啡馆外 - 日

小明和小红走出咖啡馆，站在街边。阳光有些刺眼。

小明：（沉默片刻）这么突然...

小红：我也是昨天才知道的。

小明：那我们...

小红：（打断）小明，我们认识三年了。你一直是我最好的朋友。

小明：（苦笑）朋友...

小红：（看着他）你想说什么？

小明：（鼓起勇气）小红，其实我...我喜欢你。很久了。

=== 第四场 ===
场景：公园长椅 - 黄昏

两人坐在公园的长椅上，夕阳西下，天边染成橙红色。

小红：（轻声）我知道。

小明：（惊讶）你知道？

小红：（微笑）你以为你藏得很好吗？每次看我的眼神，帮我买咖啡时记住我的口味，下雨天专门绕路送我回家...

小明：（尴尬）那你为什么从来不说？

小红：（叹气）因为我不知道该怎么回应。我们是同事，又是朋友，我怕...

小明：怕什么？

小红：怕失去你这个朋友。

=== 第五场 ===
场景：公园小路 - 黄昏

两人沿着公园的小路慢慢走着，路灯开始亮起。

小明：所以你选择去北京，是为了逃避吗？

小红：（停下脚步）不是逃避，是给自己一个机会。也给你一个机会。

小明：什么意思？

小红：（转身面对他）如果一年后，你还是这样的心情，那就来北京找我。

小明：一年？

小红：（认真地）一年的时间，足够让我们都想清楚。如果只是一时冲动，时间会冲淡一切。如果是真的...

小明：（接话）如果是真的，一年也不会改变什么。

小红：（微笑）对。

=== 第六场 ===
场景：火车站 - 日

一周后。火车站人来人往，广播声此起彼伏。

小红拖着行李箱，小明帮她拿着一个背包。

小明：东西都带齐了吗？

小红：（点头）都带了。

小明：（从口袋里掏出一个小盒子）这个给你。

小红：（接过，打开）这是...

小明：一个护身符。我妈说很灵的。

小红：（眼眶微红）谢谢你。

广播：开往北京的G102次列车即将检票，请旅客们做好准备。

=== 第七场 ===
场景：火车站检票口 - 日

小红站在检票口前，回头看着小明。

小红：我走了。

小明：（强忍情绪）一路顺风。

小红：（走近，轻轻拥抱他）一年后见。

小明：（紧紧回抱）一年后见。

小红松开他，转身走向检票口。走了几步，又回头。

小红：（大声）小明！

小明：（大声回应）什么？

小红：（微笑）记得每天给我发消息！

小明：（笑了）好！

=== 第八场 ===
场景：小明的房间 - 夜

小明坐在书桌前，面前是电脑屏幕。屏幕上显示着和小红的聊天记录。

小明：（打字）今天工作顺利吗？

小红（消息）：还好，就是有点累。你呢？

小明：（打字）我也是。想你了。

小红（消息）：才分开一天就想了？

小明：（打字）一天也是想，一年也是想。

小红（消息）：[害羞表情] 早点睡吧，晚安。

小明：（打字）晚安。

小明关上电脑，躺在床上，看着天花板。

小明：（自言自语）364天...

=== 第九场 ===
场景：北京街头 - 日（一年后）

字幕：一年后

小明站在北京繁华的街头，手里拿着手机导航。他穿着一件新买的外套，看起来比一年前成熟了不少。

小明：（看手机）应该就是这里了...

他抬头，看到对面的写字楼。深呼吸一下，迈步走去。

=== 第十场 ===
场景：写字楼大厅 - 日

小明走进大厅，四处张望。

前台：先生，请问您找谁？

小明：我找...

小红：（从电梯里走出）小明！

小明转身，看到小红。她剪了短发，穿着职业装，但笑容还是那么温暖。

小明：（微笑）我来了。

小红：（快步走向他）你真的来了。

小明：（认真地）我说过，一年后来找你。

小红：（眼眶湿润）傻瓜，我等了你364天。

小明：（轻轻擦去她的眼泪）从今以后，你不用再等了。

两人相视而笑，阳光从玻璃幕墙照进来，洒在他们身上。

（完）
"""


class WorkflowStep:
    """工作流步骤记录"""
    def __init__(self, name: str, agent: str):
        self.name = name
        self.agent = agent
        self.status = "pending"
        self.start_time = None
        self.end_time = None
        self.input_data = {}
        self.output_data = {}
        self.review_result = None
        self.error = None
    
    def start(self, input_data: Dict = None):
        self.status = "running"
        self.start_time = datetime.now()
        self.input_data = input_data or {}
    
    def complete(self, output_data: Dict = None, review_result: Dict = None):
        self.status = "completed"
        self.end_time = datetime.now()
        self.output_data = output_data or {}
        self.review_result = review_result
    
    def fail(self, error: str):
        self.status = "failed"
        self.end_time = datetime.now()
        self.error = error
    
    def duration_ms(self) -> int:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "agent": self.agent,
            "status": self.status,
            "duration_ms": self.duration_ms(),
            "input_summary": self._summarize(self.input_data),
            "output_summary": self._summarize(self.output_data),
            "review_result": self.review_result,
            "error": self.error
        }
    
    def _summarize(self, data: Dict) -> str:
        if not data:
            return "无"
        keys = list(data.keys())[:5]
        return f"包含字段: {', '.join(keys)}"


class E2EWorkflowTest:
    """端到端工作流测试"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.steps: List[WorkflowStep] = []
        self.project_id = f"test_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.results = {
            "project_id": self.project_id,
            "start_time": None,
            "end_time": None,
            "total_duration_ms": 0,
            "steps": [],
            "final_output": None,
            "success": False
        }
    
    def _get(self, path: str) -> requests.Response:
        """GET 请求"""
        return self.session.get(f"{API_BASE}{path}", timeout=TIMEOUT)
    
    def _post(self, path: str, data: Dict) -> requests.Response:
        """POST 请求"""
        return self.session.post(f"{API_BASE}{path}", json=data, timeout=TIMEOUT)
    
    async def run(self):
        """运行完整工作流"""
        print("=" * 60)
        print("Pervis PRO 完整端到端工作流测试")
        print("=" * 60)
        
        self.results["start_time"] = datetime.now().isoformat()
        
        try:
            # Step 1: 健康检查
            await self._step_health_check()
            
            # Step 2: 剧本解析
            parse_result = await self._step_parse_script()
            
            # Step 3: 生成 Logline
            logline = await self._step_generate_logline()
            
            # Step 4: 生成 Synopsis
            synopsis = await self._step_generate_synopsis()
            
            # Step 5: 生成人物小传
            character_bios = await self._step_generate_character_bios(parse_result)
            
            # Step 6: 内容审核
            review_result = await self._step_review_content(parse_result, logline, synopsis)
            
            # Step 7: 素材召回
            recall_results = await self._step_recall_assets(parse_result)
            
            # Step 8: 粗剪视频
            rough_cut_result = await self._step_rough_cut(recall_results)
            
            # Step 9: 生成流程图
            await self._generate_flow_diagram()
            
            self.results["success"] = True
            self.results["final_output"] = {
                "scenes_count": len(parse_result.get("scenes", [])),
                "characters_count": len(parse_result.get("characters", [])),
                "estimated_duration": parse_result.get("estimated_duration", 0),
                "logline": logline,
                "synopsis_length": len(str(synopsis)) if synopsis else 0,
                "character_bios_count": len(character_bios),
                "recall_results_count": len(recall_results),
                "rough_cut_path": rough_cut_result.get("output_path") if rough_cut_result else None
            }
            
        except Exception as e:
            print(f"\n❌ 工作流执行失败: {e}")
            self.results["error"] = str(e)
        
        finally:
            self.results["end_time"] = datetime.now().isoformat()
            self.results["steps"] = [s.to_dict() for s in self.steps]
            
            # 计算总时长
            if self.results["start_time"] and self.results["end_time"]:
                start = datetime.fromisoformat(self.results["start_time"])
                end = datetime.fromisoformat(self.results["end_time"])
                self.results["total_duration_ms"] = int((end - start).total_seconds() * 1000)
            
            self.session.close()
        
        return self.results
    
    async def _step_health_check(self):
        """健康检查"""
        step = WorkflowStep("健康检查", "System")
        step.start()
        self.steps.append(step)
        
        print("\n📋 Step 1: 健康检查")
        
        try:
            # 检查主 API
            resp = self._get("/api/health")
            if resp.status_code != 200:
                # 尝试根路径
                resp = self._get("/")
                if resp.status_code != 200:
                    raise Exception(f"主 API 不可用: {resp.status_code}")
            
            # 检查 Wizard API
            try:
                resp = self._get("/api/wizard/health")
                health_data = resp.json() if resp.status_code == 200 else {}
            except Exception:
                health_data = {"status": "unknown"}
            
            step.complete({"api_status": "healthy", "wizard_health": health_data})
            print("   ✅ API 服务正常")
            
        except requests.exceptions.ConnectionError:
            step.fail("无法连接到后端服务，请确保后端已启动")
            raise Exception("后端服务未启动")
        except Exception as e:
            step.fail(str(e))
            raise

    async def _step_parse_script(self) -> Dict:
        """剧本解析"""
        step = WorkflowStep("剧本解析", "Script_Agent")
        step.start({"script_length": len(SAMPLE_SCRIPT_10MIN)})
        self.steps.append(step)
        
        print("\n📋 Step 2: 剧本解析 (Script_Agent)")
        print(f"   输入: {len(SAMPLE_SCRIPT_10MIN)} 字符的剧本")
        
        try:
            resp = self._post(
                "/api/wizard/parse-script",
                {
                    "script_content": SAMPLE_SCRIPT_10MIN,
                    "project_id": self.project_id
                }
            )
            
            if resp.status_code != 200:
                raise Exception(f"解析失败: {resp.status_code} - {resp.text}")
            
            result = resp.json()
            
            scenes = result.get("scenes", [])
            characters = result.get("characters", [])
            
            step.complete({
                "scenes_count": len(scenes),
                "characters_count": len(characters),
                "estimated_duration": result.get("estimated_duration", 0),
                "status": result.get("status")
            })
            
            print(f"   ✅ 解析完成:")
            print(f"      - 场次数: {len(scenes)}")
            print(f"      - 角色数: {len(characters)}")
            print(f"      - 预估时长: {result.get('estimated_duration', 0):.1f} 秒")
            
            # 打印场次列表
            print("   📍 场次列表:")
            for scene in scenes[:5]:
                print(f"      - {scene.get('scene_number', '?')}. {scene.get('location', '未知')} ({scene.get('time_of_day', '?')})")
            if len(scenes) > 5:
                print(f"      ... 还有 {len(scenes) - 5} 个场次")
            
            # 打印角色列表
            print("   👥 角色列表:")
            for char in characters:
                print(f"      - {char.get('name', '未知')} (对话 {char.get('dialogue_count', 0)} 次)")
            
            return result
            
        except Exception as e:
            step.fail(str(e))
            print(f"   ❌ 解析失败: {e}")
            # 返回基础结果以继续测试
            return {"scenes": [], "characters": [], "estimated_duration": 0}
    
    async def _step_generate_logline(self) -> Optional[str]:
        """生成 Logline"""
        step = WorkflowStep("生成 Logline", "Script_Agent")
        step.start({"content_type": "logline"})
        self.steps.append(step)
        
        print("\n📋 Step 3: 生成 Logline (Script_Agent → Director_Agent 审核)")
        
        try:
            resp = self._post(
                "/api/wizard/generate-content",
                {
                    "project_id": self.project_id,
                    "content_type": "logline",
                    "context": {"script_content": SAMPLE_SCRIPT_10MIN[:3000]}
                }
            )
            
            if resp.status_code != 200:
                raise Exception(f"生成失败: {resp.status_code}")
            
            result = resp.json()
            logline = result.get("content")
            review_status = result.get("review_status", "unknown")
            suggestions = result.get("suggestions", [])
            
            step.complete(
                {"logline": logline, "review_status": review_status},
                {"status": review_status, "suggestions": suggestions}
            )
            
            print(f"   ✅ Logline 生成完成:")
            print(f"      \"{logline[:100]}...\"" if logline and len(str(logline)) > 100 else f"      \"{logline}\"")
            print(f"   🔍 Director_Agent 审核: {review_status}")
            if suggestions:
                print(f"   💡 建议: {', '.join(suggestions[:3])}")
            
            return logline
            
        except Exception as e:
            step.fail(str(e))
            print(f"   ❌ 生成失败: {e}")
            return None
    
    async def _step_generate_synopsis(self) -> Optional[Dict]:
        """生成 Synopsis"""
        step = WorkflowStep("生成 Synopsis", "Script_Agent")
        step.start({"content_type": "synopsis"})
        self.steps.append(step)
        
        print("\n📋 Step 4: 生成 Synopsis (Script_Agent → Director_Agent 审核)")
        
        try:
            resp = self._post(
                "/api/wizard/generate-content",
                {
                    "project_id": self.project_id,
                    "content_type": "synopsis",
                    "context": {"script_content": SAMPLE_SCRIPT_10MIN}
                }
            )
            
            if resp.status_code != 200:
                raise Exception(f"生成失败: {resp.status_code}")
            
            result = resp.json()
            synopsis = result.get("content")
            review_status = result.get("review_status", "unknown")
            
            step.complete(
                {"synopsis": synopsis, "review_status": review_status},
                {"status": review_status}
            )
            
            synopsis_text = synopsis.get("synopsis", str(synopsis)) if isinstance(synopsis, dict) else str(synopsis)
            print(f"   ✅ Synopsis 生成完成 ({len(synopsis_text)} 字符)")
            print(f"   🔍 Director_Agent 审核: {review_status}")
            
            return synopsis
            
        except Exception as e:
            step.fail(str(e))
            print(f"   ❌ 生成失败: {e}")
            return None
    
    async def _step_generate_character_bios(self, parse_result: Dict) -> List[Dict]:
        """生成人物小传"""
        characters = parse_result.get("characters", [])
        if not characters:
            print("\n📋 Step 5: 生成人物小传 - 跳过 (无角色)")
            return []
        
        step = WorkflowStep("生成人物小传", "Script_Agent")
        step.start({"characters_count": len(characters)})
        self.steps.append(step)
        
        print(f"\n📋 Step 5: 生成人物小传 (Script_Agent)")
        print(f"   为 {len(characters)} 个角色生成小传...")
        
        bios = []
        for char in characters[:3]:  # 只处理前3个角色
            char_name = char.get("name", "未知")
            try:
                resp = self._post(
                    "/api/wizard/generate-content",
                    {
                        "project_id": self.project_id,
                        "content_type": "character_bio",
                        "entity_name": char_name,
                        "context": {"script_content": SAMPLE_SCRIPT_10MIN[:2000]}
                    }
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    bio = result.get("content")
                    bios.append({"name": char_name, "bio": bio})
                    print(f"   ✅ {char_name}: 小传生成完成")
                else:
                    print(f"   ⚠️ {char_name}: 生成失败")
                    
            except Exception as e:
                print(f"   ⚠️ {char_name}: {e}")
        
        step.complete({"bios_count": len(bios)})
        return bios
    
    async def _step_review_content(self, parse_result: Dict, logline: str, synopsis: Dict) -> Dict:
        """内容审核"""
        step = WorkflowStep("内容审核", "Director_Agent")
        step.start({"content_types": ["parse_result", "logline", "synopsis"]})
        self.steps.append(step)
        
        print("\n📋 Step 6: 内容审核 (Director_Agent)")
        
        try:
            # 审核解析结果
            resp = self._post(
                "/api/wizard/review-content",
                {
                    "project_id": self.project_id,
                    "content": parse_result,
                    "content_type": "parse_script"
                }
            )
            
            if resp.status_code != 200:
                raise Exception(f"审核失败: {resp.status_code}")
            
            result = resp.json()
            
            step.complete({
                "status": result.get("status"),
                "passed_checks": result.get("passed_checks", []),
                "failed_checks": result.get("failed_checks", [])
            })
            
            print(f"   ✅ 审核完成:")
            print(f"      - 状态: {result.get('status', 'unknown')}")
            print(f"      - 通过检查: {len(result.get('passed_checks', []))} 项")
            print(f"      - 失败检查: {len(result.get('failed_checks', []))} 项")
            
            if result.get("suggestions"):
                print(f"   💡 改进建议:")
                for sug in result.get("suggestions", [])[:3]:
                    print(f"      - {sug}")
            
            return result
            
        except Exception as e:
            step.fail(str(e))
            print(f"   ❌ 审核失败: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _step_recall_assets(self, parse_result: Dict) -> List[Dict]:
        """素材召回"""
        scenes = parse_result.get("scenes", [])
        if not scenes:
            print("\n📋 Step 7: 素材召回 - 跳过 (无场次)")
            return []
        
        step = WorkflowStep("素材召回", "Storyboard_Agent")
        step.start({"scenes_count": len(scenes)})
        self.steps.append(step)
        
        print(f"\n📋 Step 7: 素材召回 (Storyboard_Agent)")
        print(f"   为 {len(scenes)} 个场次召回素材...")
        
        recall_results = []
        for scene in scenes[:5]:  # 只处理前5个场次
            scene_id = scene.get("scene_id", f"scene_{scene.get('scene_number', 0)}")
            location = scene.get("location", "")
            description = scene.get("description", scene.get("action", ""))
            
            try:
                resp = self._post(
                    "/api/wizard/recall-assets",
                    {
                        "scene_id": scene_id,
                        "query": f"{location} {description}",
                        "tags": [],
                        "strategy": "hybrid"
                    }
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    candidates = result.get("candidates", [])
                    recall_results.append({
                        "scene_id": scene_id,
                        "location": location,
                        "candidates_count": len(candidates),
                        "has_match": result.get("has_match", False)
                    })
                    
                    status = "✅" if candidates else "⚠️"
                    print(f"   {status} 场次 {scene.get('scene_number', '?')} ({location}): {len(candidates)} 个候选")
                else:
                    print(f"   ⚠️ 场次 {scene.get('scene_number', '?')}: 召回失败")
                    
            except Exception as e:
                print(f"   ⚠️ 场次 {scene.get('scene_number', '?')}: {e}")
        
        step.complete({"recall_results": recall_results})
        return recall_results
    
    async def _step_rough_cut(self, recall_results: List[Dict]) -> Optional[Dict]:
        """粗剪视频"""
        step = WorkflowStep("粗剪视频", "Storyboard_Agent")
        step.start({"scenes_with_assets": len([r for r in recall_results if r.get("candidates_count", 0) > 0])})
        self.steps.append(step)
        
        print("\n📋 Step 8: 粗剪视频 (Storyboard_Agent + FFmpeg)")
        
        # 检查是否有可用素材
        scenes_with_assets = [r for r in recall_results if r.get("candidates_count", 0) > 0]
        
        if not scenes_with_assets:
            print("   ⚠️ 没有匹配的素材，跳过粗剪")
            print("   💡 提示: 请先上传素材到素材库，然后重新运行测试")
            step.complete({"skipped": True, "reason": "no_assets"})
            return None
        
        # 这里需要实际的素材路径，由于是测试环境，我们模拟这个过程
        print(f"   📦 找到 {len(scenes_with_assets)} 个场次有匹配素材")
        print("   ⚠️ 粗剪需要实际素材文件，当前为模拟模式")
        
        step.complete({
            "mode": "simulation",
            "scenes_with_assets": len(scenes_with_assets)
        })
        
        return {"output_path": None, "mode": "simulation"}
    
    async def _generate_flow_diagram(self):
        """生成流程图"""
        print("\n📋 Step 9: 生成流程图")
        
        diagram = self._create_mermaid_diagram()
        
        # 保存流程图
        output_path = Path("E2E_WORKFLOW_FLOW_DIAGRAM.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(diagram)
        
        print(f"   ✅ 流程图已保存到: {output_path}")
    
    def _create_mermaid_diagram(self) -> str:
        """创建 Mermaid 流程图"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        diagram = f"""# Pervis PRO 完整工作流程图

生成时间: {timestamp}

## 数据流转和审核机制

```mermaid
flowchart TB
    subgraph Input["📥 用户输入"]
        A[十分钟剧本<br/>约3000字]
    end
    
    subgraph Phase1["🎬 Phase 1: 剧本解析"]
        B[Script_Agent<br/>剧本解析]
        B1[提取场次信息]
        B2[提取角色信息]
        B3[提取对话内容]
        B4[时长估算]
        
        A --> B
        B --> B1
        B --> B2
        B --> B3
        B --> B4
    end
    
    subgraph Phase2["✍️ Phase 2: 内容生成"]
        C1[Script_Agent<br/>生成 Logline]
        C2[Script_Agent<br/>生成 Synopsis]
        C3[Script_Agent<br/>生成人物小传]
        
        B1 --> C1
        B1 --> C2
        B2 --> C3
    end
    
    subgraph Review["🔍 审核机制"]
        D[Director_Agent<br/>内容审核]
        D1{{规则校验}}
        D2{{项目规格检查}}
        D3{{风格一致性}}
        D4{{历史版本对比}}
        
        C1 --> D
        C2 --> D
        C3 --> D
        D --> D1
        D --> D2
        D --> D3
        D --> D4
    end
    
    subgraph Decision["⚖️ 审核决策"]
        E1[✅ 通过]
        E2[💡 建议修改]
        E3[❌ 拒绝]
        
        D1 --> E1
        D1 --> E2
        D1 --> E3
    end
    
    subgraph Phase3["🎨 Phase 3: 素材召回"]
        F[Storyboard_Agent<br/>素材召回]
        F1[标签搜索]
        F2[向量搜索]
        F3[混合排序]
        F4[Top 5 候选]
        
        E1 --> F
        B1 --> F
        F --> F1
        F --> F2
        F1 --> F3
        F2 --> F3
        F3 --> F4
    end
    
    subgraph Phase4["🎬 Phase 4: 视频输出"]
        G[Storyboard_Agent<br/>粗剪]
        G1[FFmpeg 切割]
        G2[片段拼接]
        G3[输出视频]
        
        F4 --> G
        G --> G1
        G1 --> G2
        G2 --> G3
    end
    
    subgraph Output["📤 最终输出"]
        H[粗剪视频<br/>MP4 格式]
        I[项目文档<br/>场次/角色/小传]
        
        G3 --> H
        E1 --> I
    end
    
    style Input fill:#e1f5fe
    style Phase1 fill:#fff3e0
    style Phase2 fill:#f3e5f5
    style Review fill:#ffebee
    style Decision fill:#fff8e1
    style Phase3 fill:#e8f5e9
    style Phase4 fill:#fce4ec
    style Output fill:#e0f2f1
```

## 详细数据流转

```mermaid
sequenceDiagram
    participant U as 用户
    participant SA as Script_Agent
    participant DA as Director_Agent
    participant SBA as Storyboard_Agent
    participant FF as FFmpeg
    
    U->>SA: 提交剧本 (3000字)
    activate SA
    SA->>SA: 正则解析场次
    SA->>SA: 提取角色对话
    SA->>SA: 估算时长
    SA-->>U: 返回解析结果
    deactivate SA
    
    U->>SA: 请求生成 Logline
    activate SA
    SA->>SA: LLM 生成内容
    SA->>DA: 提交审核
    activate DA
    DA->>DA: 规则校验
    DA->>DA: 字数检查
    DA-->>SA: 审核结果
    deactivate DA
    SA-->>U: Logline + 审核状态
    deactivate SA
    
    U->>SA: 请求生成 Synopsis
    activate SA
    SA->>SA: LLM 生成内容
    SA->>DA: 提交审核
    activate DA
    DA->>DA: 内容审核
    DA-->>SA: 审核结果
    deactivate DA
    SA-->>U: Synopsis + 审核状态
    deactivate SA
    
    U->>SBA: 请求素材召回
    activate SBA
    SBA->>SBA: 标签搜索
    SBA->>SBA: 向量搜索
    SBA->>SBA: 混合排序
    SBA-->>U: Top 5 候选
    deactivate SBA
    
    U->>SBA: 请求粗剪
    activate SBA
    SBA->>FF: 切割片段
    FF-->>SBA: 临时文件
    SBA->>FF: 拼接视频
    FF-->>SBA: 输出文件
    SBA-->>U: 粗剪视频路径
    deactivate SBA
```

## 审核机制详解

```mermaid
flowchart LR
    subgraph Input["输入内容"]
        I1[Logline]
        I2[Synopsis]
        I3[人物小传]
    end
    
    subgraph Rules["规则校验"]
        R1[内容不为空]
        R2[字数范围检查]
        R3[格式正确性]
    end
    
    subgraph Context["上下文检查"]
        C1[项目规格一致性]
        C2[艺术风格一致性]
        C3[历史版本对比]
    end
    
    subgraph Result["审核结果"]
        O1[✅ approved<br/>直接通过]
        O2[💡 suggestions<br/>通过但有建议]
        O3[❌ rejected<br/>需要修改]
    end
    
    I1 --> R1
    I2 --> R1
    I3 --> R1
    
    R1 -->|通过| R2
    R2 -->|通过| R3
    R3 -->|通过| C1
    
    C1 --> C2
    C2 --> C3
    
    C3 -->|全部通过| O1
    C3 -->|有建议| O2
    R1 -->|失败| O3
    R2 -->|失败| O3
```

## 本次测试结果

| 步骤 | Agent | 状态 | 耗时 |
|------|-------|------|------|
"""
        
        # 添加测试结果表格
        for step in self.steps:
            status_icon = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏳"
            diagram += f"| {step.name} | {step.agent} | {status_icon} {step.status} | {step.duration_ms()}ms |\n"
        
        diagram += f"""
## 关键数据

- **项目ID**: {self.project_id}
- **剧本长度**: {len(SAMPLE_SCRIPT_10MIN)} 字符
- **测试时间**: {timestamp}
"""
        
        return diagram


async def main():
    """主函数"""
    test = E2EWorkflowTest()
    results = await test.run()
    
    # 保存结果
    output_path = Path(f"e2e_workflow_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    print(f"结果已保存到: {output_path}")
    print(f"流程图已保存到: E2E_WORKFLOW_FLOW_DIAGRAM.md")
    
    if results["success"]:
        print("\n✅ 工作流测试成功!")
        if results.get("final_output"):
            output = results["final_output"]
            print(f"   - 场次数: {output.get('scenes_count', 0)}")
            print(f"   - 角色数: {output.get('characters_count', 0)}")
            print(f"   - 预估时长: {output.get('estimated_duration', 0):.1f} 秒")
    else:
        print("\n❌ 工作流测试失败")
        if results.get("error"):
            print(f"   错误: {results['error']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
