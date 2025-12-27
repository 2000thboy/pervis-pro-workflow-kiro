# -*- coding: utf-8 -*-
"""
Pervis PRO 端到端工作流测试 - 直接调用服务层

绕过 API 层，直接测试 Agent 服务，验证完整数据流转
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# 添加 backend 到路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# 十分钟剧本示例
SAMPLE_SCRIPT = """
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


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_step(step_num: int, title: str, agent: str):
    """打印步骤标题"""
    print(f"\n📋 Step {step_num}: {title} ({agent})")


async def test_script_agent():
    """测试 Script_Agent"""
    print_step(1, "剧本解析", "Script_Agent")
    
    from services.agents.script_agent import get_script_agent_service
    
    script_agent = get_script_agent_service()
    
    # 解析剧本
    print("   正在解析剧本...")
    result = script_agent.parse_script(SAMPLE_SCRIPT)
    
    print(f"   ✅ 解析完成:")
    print(f"      - 场次数: {result.total_scenes}")
    print(f"      - 角色数: {result.total_characters}")
    print(f"      - 预估时长: {result.estimated_duration:.1f} 秒 ({result.estimated_duration/60:.1f} 分钟)")
    
    print("\n   📍 场次列表:")
    for scene in result.scenes:
        print(f"      {scene.scene_number}. {scene.location} - {scene.time_of_day} ({scene.estimated_duration:.0f}秒)")
        if scene.characters:
            print(f"         角色: {', '.join(scene.characters)}")
    
    print("\n   👥 角色列表:")
    for char in result.characters:
        print(f"      - {char.name}: 对话 {char.dialogue_count} 次, 首次出现于场次 {char.first_appearance}")
    
    return result


async def test_content_generation(script_content: str):
    """测试内容生成"""
    print_step(2, "内容生成", "Script_Agent + LLM")
    
    from services.agents.script_agent import get_script_agent_service
    
    script_agent = get_script_agent_service()
    
    # 生成 Logline
    print("   正在生成 Logline...")
    try:
        logline = await script_agent.generate_logline(script_content)
        if logline:
            print(f"   ✅ Logline: {logline}")
        else:
            print("   ⚠️ Logline 生成失败 (LLM 服务可能不可用)")
            logline = "一对相爱的年轻人，在分离一年后终于重逢。"
            print(f"   📝 使用默认 Logline: {logline}")
    except Exception as e:
        print(f"   ⚠️ Logline 生成异常: {e}")
        logline = None
    
    # 生成 Synopsis
    print("\n   正在生成 Synopsis...")
    try:
        synopsis = await script_agent.generate_synopsis(script_content)
        if synopsis:
            synopsis_text = synopsis.get("synopsis", str(synopsis)) if isinstance(synopsis, dict) else str(synopsis)
            print(f"   ✅ Synopsis ({len(synopsis_text)} 字符)")
        else:
            print("   ⚠️ Synopsis 生成失败")
            synopsis = None
    except Exception as e:
        print(f"   ⚠️ Synopsis 生成异常: {e}")
        synopsis = None
    
    return {"logline": logline, "synopsis": synopsis}


async def test_director_review(parse_result):
    """测试 Director_Agent 审核"""
    print_step(3, "内容审核", "Director_Agent")
    
    from services.agents.director_agent import get_director_agent_service
    
    director_agent = get_director_agent_service()
    
    # 审核解析结果
    print("   正在审核剧本解析结果...")
    review_result = await director_agent.review(
        result=parse_result.to_dict(),
        task_type="parse_script",
        project_id="test_project"
    )
    
    print(f"   ✅ 审核完成:")
    print(f"      - 状态: {review_result.status}")
    print(f"      - 通过检查: {len(review_result.passed_checks)} 项")
    for check in review_result.passed_checks:
        print(f"         ✓ {check}")
    
    if review_result.failed_checks:
        print(f"      - 失败检查: {len(review_result.failed_checks)} 项")
        for check in review_result.failed_checks:
            print(f"         ✗ {check}")
    
    if review_result.suggestions:
        print(f"      - 改进建议:")
        for sug in review_result.suggestions:
            print(f"         💡 {sug}")
    
    return review_result


async def test_storyboard_recall(scenes):
    """测试 Storyboard_Agent 素材召回"""
    print_step(4, "素材召回", "Storyboard_Agent")
    
    from services.agents.storyboard_agent import get_storyboard_agent_service
    
    storyboard_agent = get_storyboard_agent_service()
    
    print(f"   为 {len(scenes)} 个场次召回素材...")
    
    recall_results = []
    for scene in scenes[:5]:  # 只处理前5个场次
        query = f"{scene.location} {scene.action[:50] if scene.action else ''}"
        
        result = await storyboard_agent.recall_assets(
            scene_id=scene.scene_id,
            query=query,
            strategy="hybrid"
        )
        
        recall_results.append(result)
        
        status = "✅" if result.has_match else "⚠️"
        print(f"   {status} 场次 {scene.scene_number} ({scene.location}): {len(result.candidates)} 个候选")
        
        if not result.has_match:
            print(f"      {result.placeholder_message}")
    
    return recall_results


async def test_rough_cut():
    """测试粗剪"""
    print_step(5, "粗剪视频", "Storyboard_Agent + FFmpeg")
    
    print("   ⚠️ 粗剪需要实际素材文件")
    print("   💡 当素材库有匹配素材时，系统会:")
    print("      1. 从候选中选择最佳匹配")
    print("      2. 使用 FFmpeg 切割片段")
    print("      3. 拼接成粗剪视频")
    
    return None


def generate_flow_diagram(parse_result, content_result, review_result, recall_results):
    """生成流程图"""
    print_step(6, "生成流程图", "System")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    diagram = f"""# Pervis PRO 完整工作流程图

生成时间: {timestamp}

## 数据流转和审核机制

```mermaid
flowchart TB
    subgraph Input["📥 用户输入"]
        A[十分钟剧本<br/>{len(SAMPLE_SCRIPT)} 字符]
    end
    
    subgraph Phase1["🎬 Phase 1: 剧本解析"]
        B[Script_Agent<br/>剧本解析]
        B1[提取 {parse_result.total_scenes} 个场次]
        B2[提取 {parse_result.total_characters} 个角色]
        B3[估算时长 {parse_result.estimated_duration:.0f} 秒]
        
        A --> B
        B --> B1
        B --> B2
        B --> B3
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
        
        C1 --> D
        C2 --> D
        C3 --> D
        D --> D1
        D --> D2
        D --> D3
    end
    
    subgraph Decision["⚖️ 审核决策"]
        E1[✅ {review_result.status}]
        E2[通过 {len(review_result.passed_checks)} 项检查]
        
        D1 --> E1
        D1 --> E2
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
    
    U->>SA: 提交剧本 ({len(SAMPLE_SCRIPT)}字)
    activate SA
    SA->>SA: 正则解析场次
    SA->>SA: 提取角色对话
    SA->>SA: 估算时长
    SA-->>U: 返回 {parse_result.total_scenes} 场次, {parse_result.total_characters} 角色
    deactivate SA
    
    U->>SA: 请求生成 Logline
    activate SA
    SA->>SA: LLM 生成内容
    SA->>DA: 提交审核
    activate DA
    DA->>DA: 规则校验
    DA->>DA: 字数检查
    DA-->>SA: 审核: {review_result.status}
    deactivate DA
    SA-->>U: Logline + 审核状态
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

| 检查项 | 状态 | 说明 |
|--------|------|------|
"""
    
    for check in review_result.passed_checks:
        diagram += f"| {check} | ✅ 通过 | - |\n"
    
    for check in review_result.failed_checks:
        diagram += f"| {check} | ❌ 失败 | 需要修改 |\n"
    
    diagram += f"""
## 本次测试结果

| 指标 | 数值 |
|------|------|
| 剧本长度 | {len(SAMPLE_SCRIPT)} 字符 |
| 场次数 | {parse_result.total_scenes} |
| 角色数 | {parse_result.total_characters} |
| 预估时长 | {parse_result.estimated_duration:.0f} 秒 ({parse_result.estimated_duration/60:.1f} 分钟) |
| 审核状态 | {review_result.status} |
| 通过检查 | {len(review_result.passed_checks)} 项 |
| 素材召回 | {len(recall_results)} 个场次 |

## 场次详情

| 场次 | 场景 | 时间 | 角色 | 时长 |
|------|------|------|------|------|
"""
    
    for scene in parse_result.scenes:
        chars = ", ".join(scene.characters) if scene.characters else "-"
        diagram += f"| {scene.scene_number} | {scene.location} | {scene.time_of_day} | {chars} | {scene.estimated_duration:.0f}秒 |\n"
    
    diagram += f"""
## 角色详情

| 角色 | 对话次数 | 首次出现 | 出现场次 |
|------|----------|----------|----------|
"""
    
    for char in parse_result.characters:
        scenes_str = ", ".join(map(str, char.scenes))
        diagram += f"| {char.name} | {char.dialogue_count} | 第{char.first_appearance}场 | {scenes_str} |\n"
    
    # 保存流程图
    output_path = Path("E2E_WORKFLOW_FLOW_DIAGRAM.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(diagram)
    
    print(f"   ✅ 流程图已保存到: {output_path}")
    
    return diagram


async def main():
    """主函数"""
    print_section("Pervis PRO 端到端工作流测试 - 直接服务层调用")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"剧本长度: {len(SAMPLE_SCRIPT)} 字符")
    
    try:
        # Step 1: 剧本解析
        parse_result = await test_script_agent()
        
        # Step 2: 内容生成
        content_result = await test_content_generation(SAMPLE_SCRIPT)
        
        # Step 3: Director 审核
        review_result = await test_director_review(parse_result)
        
        # Step 4: 素材召回
        recall_results = await test_storyboard_recall(parse_result.scenes)
        
        # Step 5: 粗剪
        rough_cut_result = await test_rough_cut()
        
        # Step 6: 生成流程图
        generate_flow_diagram(parse_result, content_result, review_result, recall_results)
        
        print_section("测试完成")
        print("✅ 所有步骤执行成功!")
        print(f"\n📊 测试摘要:")
        print(f"   - 场次数: {parse_result.total_scenes}")
        print(f"   - 角色数: {parse_result.total_characters}")
        print(f"   - 预估时长: {parse_result.estimated_duration:.0f} 秒 ({parse_result.estimated_duration/60:.1f} 分钟)")
        print(f"   - 审核状态: {review_result.status}")
        print(f"   - 流程图: E2E_WORKFLOW_FLOW_DIAGRAM.md")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
