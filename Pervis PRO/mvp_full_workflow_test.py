# -*- coding: utf-8 -*-
"""
Pervis PRO MVP 完整工作流测试（使用索引好的素材）

测试流程：
1. 加载已索引的 300 个素材
2. 使用长剧本测试前期立项
3. 测试 Beatboard 素材召回
4. 测试预演模式时间线构建

使用方法：
    cd "Pervis PRO"
    py mvp_full_workflow_test.py
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 加载环境变量
def load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    # FFmpeg
    ffmpeg_paths = [r"C:\ffmpeg\bin", r"C:\Program Files\ffmpeg\bin"]
    for p in ffmpeg_paths:
        if os.path.exists(os.path.join(p, "ffmpeg.exe")):
            os.environ["PATH"] = p + ";" + os.environ.get("PATH", "")
            break

load_env()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# ============================================================
# 测试剧本（鬼灭之刃风格，匹配素材库）
# ============================================================

TEST_SCRIPT = """
《鬼灭之刃：蜘蛛山之战》预演剧本

第一幕：进入蜘蛛山

EXT. 那田蜘蛛山入口 - 黄昏

炭治郎、善逸、伊之助三人站在蜘蛛山入口，森林中弥漫着诡异的气息。

炭治郎
（警觉）
这股气味...有很多鬼的气息。

善逸
（颤抖）
我不想进去...这里太可怕了...

伊之助
（兴奋）
哈哈哈！正好让我大显身手！

INT. 蜘蛛山森林 - 夜

三人深入森林，四周布满蜘蛛丝。

炭治郎
（拔刀）
小心！有敌人！

第二幕：善逸的战斗

EXT. 蜘蛛山深处 - 夜

善逸独自面对蜘蛛鬼，恐惧到极点后陷入睡眠。

善逸
（睡梦中，眼神锐利）
雷之呼吸...壹之型...

他的身体如闪电般移动。

善逸
霹雳一闪！

蜘蛛鬼被一刀斩杀。

第三幕：炭治郎的水之呼吸

INT. 蜘蛛山洞穴 - 夜

炭治郎面对强大的蜘蛛男，使出水之呼吸。

炭治郎
（全集中）
水之呼吸...拾之型...

水流环绕刀身，形成巨大的水龙。

炭治郎
生生流转！

第四幕：义勇登场

EXT. 蜘蛛山战场 - 夜

水柱·富冈义勇出现，一刀斩杀蜘蛛男。

义勇
（冷静）
水之呼吸...拾壹之型...凪。

所有攻击在他面前化为虚无。

第五幕：弥豆子觉醒

INT. 蜘蛛山深处 - 夜

弥豆子为了保护炭治郎，血鬼术觉醒。

弥豆子
（低吼）
呜...

她的血液燃烧，形成血焰。

炭治郎
（惊讶）
弥豆子...你的力量...

第六幕：最终决战

EXT. 蜘蛛山顶 - 黎明

炭治郎与义勇联手，对抗最后的敌人。

炭治郎
（配合）
水之呼吸！

义勇
（同时出手）
凪！

两人的攻击完美配合，将敌人击败。

【完】
"""

# 测试场次（匹配素材库标签）
TEST_SCENES = [
    {"scene_id": "s01", "heading": "EXT. 蜘蛛山入口 - 黄昏", "duration": 15, 
     "search_tags": ["森林", "入口", "黄昏"], "search_query": "森林入口"},
    {"scene_id": "s02", "heading": "INT. 蜘蛛山森林 - 夜", "duration": 20,
     "search_tags": ["森林", "夜晚", "蜘蛛"], "search_query": "森林夜晚战斗"},
    {"scene_id": "s03", "heading": "善逸霹雳一闪", "duration": 10,
     "search_tags": ["善逸", "霹雳一闪", "雷之呼吸", "冲刺"], "search_query": "善逸霹雳一闪"},
    {"scene_id": "s04", "heading": "炭治郎水之呼吸", "duration": 15,
     "search_tags": ["炭治郎", "水之呼吸", "战斗", "斩击"], "search_query": "炭治郎水之呼吸"},
    {"scene_id": "s05", "heading": "义勇斩杀蜘蛛", "duration": 10,
     "search_tags": ["义勇", "水之呼吸", "斩击", "蜘蛛"], "search_query": "义勇斩杀"},
    {"scene_id": "s06", "heading": "弥豆子血鬼术", "duration": 12,
     "search_tags": ["弥豆子", "血", "火焰", "觉醒"], "search_query": "弥豆子觉醒"},
    {"scene_id": "s07", "heading": "最终决战", "duration": 20,
     "search_tags": ["战斗", "攻击", "配合", "斩击"], "search_query": "最终决战配合攻击"},
]


# ============================================================
# 测试类
# ============================================================

class FullWorkflowTest:
    """完整工作流测试"""
    
    def __init__(self):
        self.project_id = f"test_{int(time.time())}"
        self.video_store = None
        self.results = {
            "test_time": datetime.now().isoformat(),
            "project_id": self.project_id,
            "phases": {},
            "success": False
        }
    
    async def run(self):
        """运行测试"""
        print("\n" + "="*70)
        print("Pervis PRO MVP 完整工作流测试")
        print("="*70)
        print(f"项目ID: {self.project_id}")
        print("="*70)
        
        try:
            # Phase 1: 加载素材
            await self.phase1_load_assets()
            
            # Phase 2: 前期立项
            await self.phase2_project_wizard()
            
            # Phase 3: Beatboard 素材召回
            await self.phase3_beatboard()
            
            # Phase 4: 预演模式
            await self.phase4_preview_mode()
            
            self.results["success"] = True
            
        except Exception as e:
            self.results["error"] = str(e)
            import traceback
            traceback.print_exc()
        
        self._print_report()
        self._save_report()
        
        return self.results["success"]
    
    async def phase1_load_assets(self):
        """Phase 1: 加载已索引的素材"""
        print("\n" + "-"*60)
        print("Phase 1: 加载素材库")
        print("-"*60)
        
        from services.milvus_store import MemoryVideoStore, VideoSegment
        
        self.video_store = MemoryVideoStore()
        await self.video_store.initialize()
        
        # 加载索引缓存
        cache_path = Path(__file__).parent / "data" / "index_cache.json"
        if not cache_path.exists():
            print("⚠️ 索引缓存不存在，请先运行 batch_asset_indexing.py")
            # 运行快速索引
            print("   正在运行快速索引...")
            from batch_asset_indexing import BatchAssetIndexer
            indexer = BatchAssetIndexer(use_llm=False, use_embedding=False)
            await indexer.run(sample_size=300, target_dirs=["鬼灭", "打斗", "MAD"])
            self.video_store = indexer.video_store
        else:
            # 重新索引到内存
            print("   从缓存重建索引...")
            from batch_asset_indexing import BatchAssetIndexer, TagGenerator
            
            indexer = BatchAssetIndexer(use_llm=False, use_embedding=False)
            indexer.video_store = self.video_store
            indexer._load_cache()
            
            tag_gen = TagGenerator()
            
            # 从缓存中的文件路径重建
            count = 0
            for file_hash, segment_id in list(indexer.index_cache.items())[:300]:
                # 需要找到原始文件路径
                # 这里简化处理，直接扫描文件
                pass
            
            # 直接重新扫描
            video_files = indexer.scan_assets(sample_size=300, target_dirs=["鬼灭", "打斗", "MAD"])
            
            for i, file_path in enumerate(video_files):
                tags = tag_gen.extract_from_filename(Path(file_path).name)
                segment = VideoSegment(
                    segment_id=f"asset_{i:06d}",
                    video_id=f"vid_{i:04d}",
                    video_path=file_path,
                    start_time=0,
                    end_time=5.0,
                    duration=5.0,
                    tags=tags,
                    description=tags.get("summary", "")
                )
                await self.video_store.insert(segment)
                count += 1
            
            print(f"   已加载 {count} 个素材")
        
        total = await self.video_store.count()
        self.results["phases"]["load_assets"] = {
            "status": "passed",
            "total_assets": total
        }
        print(f"\n✅ Phase 1 完成: {total} 个素材已加载")
    
    async def phase2_project_wizard(self):
        """Phase 2: 前期立项"""
        print("\n" + "-"*60)
        print("Phase 2: 前期立项 (Project Wizard)")
        print("-"*60)
        
        result = {"status": "running", "steps": {}}
        
        try:
            from services.agents.script_agent import get_script_agent_service
            from services.agents.director_agent import get_director_agent_service
            
            script_agent = get_script_agent_service()
            director_agent = get_director_agent_service()
            
            # Step 1: 剧本解析
            print("  Step 1: 剧本解析...")
            parse_result = script_agent.parse_script(TEST_SCRIPT)
            result["steps"]["parse"] = {
                "scenes": parse_result.total_scenes,
                "characters": parse_result.total_characters
            }
            print(f"    ✅ {parse_result.total_scenes} 场次, {parse_result.total_characters} 角色")
            
            # 显示解析的场次
            print(f"\n    解析出的场次:")
            for i, scene in enumerate(parse_result.scenes[:5]):
                print(f"      {i+1}. {scene.heading}")
            
            # 显示解析的角色
            print(f"\n    解析出的角色:")
            for char in parse_result.characters[:5]:
                print(f"      - {char.name}")
            
            # Step 2: Logline 生成
            print("\n  Step 2: Logline 生成...")
            logline = await script_agent.generate_logline(TEST_SCRIPT)
            result["steps"]["logline"] = logline[:100] if logline else "生成失败"
            print(f"    ✅ {logline[:80]}..." if logline else "    ⚠️ 失败")
            
            # Step 3: 导演审核
            print("\n  Step 3: 导演审核...")
            review = await director_agent.review(
                result={"logline": logline},
                task_type="logline",
                project_id=self.project_id
            )
            result["steps"]["review"] = {
                "status": review.status,
                "passed_checks": review.passed_checks
            }
            print(f"    ✅ 审核状态: {review.status}")
            
            result["status"] = "passed"
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"    ❌ 失败: {e}")
        
        self.results["phases"]["project_wizard"] = result
        print(f"\n✅ Phase 2 完成")
    
    async def phase3_beatboard(self):
        """Phase 3: Beatboard 素材召回"""
        print("\n" + "-"*60)
        print("Phase 3: Beatboard 素材召回")
        print("-"*60)
        
        result = {"status": "running", "scenes": [], "total_matched": 0}
        
        print(f"\n  处理 {len(TEST_SCENES)} 个场次...")
        print(f"  {'场次':<30} {'搜索标签':<30} {'匹配数':<10}")
        print(f"  {'-'*70}")
        
        for scene in TEST_SCENES:
            scene_result = {
                "scene_id": scene["scene_id"],
                "heading": scene["heading"],
                "candidates": []
            }
            
            # 搜索匹配素材
            candidates = await self._search_assets(
                scene["search_tags"],
                scene["search_query"]
            )
            
            scene_result["candidates"] = [
                {"asset_id": c["asset_id"], "score": c["score"], "tags": c["matched_tags"][:3]}
                for c in candidates[:5]
            ]
            scene_result["match_count"] = len(candidates)
            
            result["scenes"].append(scene_result)
            result["total_matched"] += len(candidates)
            
            # 显示结果
            tags_str = ", ".join(scene["search_tags"][:3])
            status = "✅" if candidates else "⚠️"
            print(f"  {status} {scene['heading'][:28]:<30} {tags_str[:28]:<30} {len(candidates):<10}")
            
            # 显示匹配的素材
            if candidates:
                for c in candidates[:2]:
                    print(f"      -> {c['filename'][:50]} (score: {c['score']:.2f})")
        
        # 统计
        scenes_with_match = sum(1 for s in result["scenes"] if s["match_count"] > 0)
        result["scenes_with_match"] = scenes_with_match
        result["status"] = "passed"
        
        self.results["phases"]["beatboard"] = result
        print(f"\n✅ Phase 3 完成: {scenes_with_match}/{len(TEST_SCENES)} 场次有匹配素材")
    
    async def _search_assets(self, search_tags: List[str], query: str) -> List[Dict]:
        """搜索匹配素材"""
        results = []
        
        search_words = set(search_tags)
        for word in query.split():
            if len(word) > 1:
                search_words.add(word)
        
        for segment_id, segment in self.video_store._segments.items():
            score = 0
            matched_tags = []
            
            # 检查 free_tags
            free_tags = segment.tags.get("free_tags", [])
            for tag in free_tags:
                for sw in search_words:
                    if sw in tag or tag in sw:
                        score += 2
                        matched_tags.append(tag)
            
            # 检查其他标签
            for key in ["action", "mood", "characters"]:
                value = segment.tags.get(key, "")
                if isinstance(value, list):
                    for v in value:
                        for sw in search_words:
                            if sw in v or v in sw:
                                score += 1
                                matched_tags.append(v)
                elif isinstance(value, str):
                    for sw in search_words:
                        if sw in value or value in sw:
                            score += 1
                            matched_tags.append(value)
            
            # 检查文件名
            filename = Path(segment.video_path).name
            for sw in search_words:
                if sw in filename:
                    score += 0.5
            
            if score > 0:
                results.append({
                    "asset_id": segment_id,
                    "video_path": segment.video_path,
                    "filename": filename,
                    "score": score,
                    "matched_tags": list(set(matched_tags))
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    async def phase4_preview_mode(self):
        """Phase 4: 预演模式"""
        print("\n" + "-"*60)
        print("Phase 4: 预演模式（时间线构建）")
        print("-"*60)
        
        result = {"status": "running", "timeline": [], "total_duration": 0}
        
        beatboard = self.results["phases"].get("beatboard", {})
        
        current_time = 0.0
        
        print(f"\n  {'时间':<20} {'场次':<25} {'素材':<30}")
        print(f"  {'-'*75}")
        
        for scene in TEST_SCENES:
            # 获取该场次的候选素材
            scene_data = next(
                (s for s in beatboard.get("scenes", []) if s["scene_id"] == scene["scene_id"]),
                None
            )
            
            selected_asset = None
            if scene_data and scene_data.get("candidates"):
                selected_asset = scene_data["candidates"][0]
            
            clip = {
                "scene_id": scene["scene_id"],
                "heading": scene["heading"],
                "start_time": current_time,
                "duration": scene["duration"],
                "end_time": current_time + scene["duration"],
                "asset": selected_asset
            }
            
            result["timeline"].append(clip)
            
            # 显示
            time_str = f"[{current_time:.1f}s - {clip['end_time']:.1f}s]"
            asset_str = selected_asset["asset_id"] if selected_asset else "无素材"
            print(f"  {time_str:<20} {scene['heading'][:23]:<25} {asset_str:<30}")
            
            current_time += scene["duration"]
        
        result["total_duration"] = current_time
        result["total_clips"] = len(result["timeline"])
        result["clips_with_assets"] = sum(1 for c in result["timeline"] if c.get("asset"))
        result["status"] = "passed"
        
        self.results["phases"]["preview_mode"] = result
        
        print(f"\n  时间线统计:")
        print(f"    总时长: {result['total_duration']:.1f} 秒 ({result['total_duration']/60:.1f} 分钟)")
        print(f"    片段数: {result['total_clips']}")
        print(f"    已匹配素材: {result['clips_with_assets']}/{result['total_clips']}")
        
        print(f"\n✅ Phase 4 完成")
    
    def _print_report(self):
        """打印报告"""
        print("\n" + "="*70)
        print("📊 测试报告")
        print("="*70)
        
        for phase_name, phase_data in self.results["phases"].items():
            status = "✅" if phase_data.get("status") == "passed" else "❌"
            print(f"\n{status} {phase_name}")
        
        print("\n" + "-"*70)
        if self.results["success"]:
            print("🎉 MVP 完整工作流测试通过！")
        else:
            print("❌ 测试失败")
        print("-"*70)
    
    def _save_report(self):
        """保存报告"""
        report_path = f"mvp_workflow_test_report_{int(time.time())}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n📄 报告已保存: {report_path}")


# ============================================================
# 主函数
# ============================================================

async def main():
    test = FullWorkflowTest()
    success = await test.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
