# -*- coding: utf-8 -*-
"""
素材标签数据模型

Feature: pervis-asset-tagging
Task: 1.1 定义标签数据结构

实现四级标签层级体系：
- L1 一级标签（必填单选）：scene_type, time_of_day, shot_size
- L2 二级标签（必填单选）：camera_move, action_type, mood
- L3 三级标签（可选多选）：characters, props, vfx, environment
- L4 四级标签（自由）：free_tags, source_work, summary
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# L1 一级标签枚举（必填单选）
# ============================================================

class SceneType(str, Enum):
    """场景类型"""
    INT = "INT"           # 室内
    EXT = "EXT"           # 室外
    INT_EXT = "INT-EXT"   # 混合
    UNKNOWN = "UNKNOWN"   # 未知
    
    @classmethod
    def from_chinese(cls, value: str) -> "SceneType":
        mapping = {
            "室内": cls.INT,
            "室外": cls.EXT,
            "混合": cls.INT_EXT,
        }
        return mapping.get(value, cls.UNKNOWN)


class TimeOfDay(str, Enum):
    """时间"""
    DAY = "DAY"           # 白天
    NIGHT = "NIGHT"       # 夜晚
    DAWN = "DAWN"         # 黎明
    DUSK = "DUSK"         # 黄昏
    UNKNOWN = "UNKNOWN"   # 未知
    
    @classmethod
    def from_chinese(cls, value: str) -> "TimeOfDay":
        mapping = {
            "白天": cls.DAY,
            "夜晚": cls.NIGHT,
            "黎明": cls.DAWN,
            "黄昏": cls.DUSK,
        }
        return mapping.get(value, cls.UNKNOWN)


class ShotSize(str, Enum):
    """镜头类型"""
    ECU = "ECU"   # 大特写 Extreme Close-Up
    CU = "CU"     # 特写 Close-Up
    MCU = "MCU"   # 中近景 Medium Close-Up
    MS = "MS"     # 中景 Medium Shot
    MLS = "MLS"   # 中远景 Medium Long Shot
    LS = "LS"     # 远景 Long Shot
    ELS = "ELS"   # 大远景 Extreme Long Shot
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_chinese(cls, value: str) -> "ShotSize":
        mapping = {
            "大特写": cls.ECU,
            "特写": cls.CU,
            "中近景": cls.MCU,
            "近景": cls.MCU,
            "中景": cls.MS,
            "中远景": cls.MLS,
            "远景": cls.LS,
            "全景": cls.LS,
            "大远景": cls.ELS,
        }
        return mapping.get(value, cls.UNKNOWN)


# ============================================================
# L2 二级标签枚举（必填单选）
# ============================================================

class CameraMove(str, Enum):
    """镜头运动"""
    STATIC = "STATIC"       # 静止
    PAN = "PAN"             # 横摇
    TILT = "TILT"           # 俯仰
    DOLLY = "DOLLY"         # 推轨
    CRANE = "CRANE"         # 升降
    HANDHELD = "HANDHELD"   # 手持
    ZOOM = "ZOOM"           # 变焦
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_chinese(cls, value: str) -> "CameraMove":
        mapping = {
            "静止": cls.STATIC,
            "横摇": cls.PAN,
            "俯仰": cls.TILT,
            "推轨": cls.DOLLY,
            "升降": cls.CRANE,
            "手持": cls.HANDHELD,
            "变焦": cls.ZOOM,
        }
        return mapping.get(value, cls.UNKNOWN)


class ActionType(str, Enum):
    """动作类型"""
    FIGHT = "FIGHT"           # 打斗
    CHASE = "CHASE"           # 追逐
    DIALOGUE = "DIALOGUE"     # 对话
    IDLE = "IDLE"             # 静态
    RUN = "RUN"               # 奔跑
    FLY = "FLY"               # 飞行
    TRANSFORM = "TRANSFORM"   # 变身
    SKILL = "SKILL"           # 技能释放
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_chinese(cls, value: str) -> "ActionType":
        mapping = {
            "打斗": cls.FIGHT,
            "战斗": cls.FIGHT,
            "追逐": cls.CHASE,
            "对话": cls.DIALOGUE,
            "静态": cls.IDLE,
            "奔跑": cls.RUN,
            "飞行": cls.FLY,
            "变身": cls.TRANSFORM,
            "技能释放": cls.SKILL,
            "技能": cls.SKILL,
        }
        return mapping.get(value, cls.UNKNOWN)


class Mood(str, Enum):
    """情绪基调"""
    TENSE = "TENSE"         # 紧张
    SAD = "SAD"             # 悲伤
    HAPPY = "HAPPY"         # 欢乐
    CALM = "CALM"           # 平静
    HORROR = "HORROR"       # 恐怖
    ROMANTIC = "ROMANTIC"   # 浪漫
    EPIC = "EPIC"           # 热血
    NEUTRAL = "NEUTRAL"     # 中性
    UNKNOWN = "UNKNOWN"
    
    @classmethod
    def from_chinese(cls, value: str) -> "Mood":
        mapping = {
            "紧张": cls.TENSE,
            "悲伤": cls.SAD,
            "欢乐": cls.HAPPY,
            "平静": cls.CALM,
            "恐怖": cls.HORROR,
            "浪漫": cls.ROMANTIC,
            "热血": cls.EPIC,
            "燃": cls.EPIC,
            "中性": cls.NEUTRAL,
        }
        return mapping.get(value, cls.UNKNOWN)


# ============================================================
# 标签权重配置
# ============================================================

TAG_WEIGHTS = {
    "L1": 1.0,   # 一级标签权重
    "L2": 0.8,   # 二级标签权重
    "L3": 0.6,   # 三级标签权重
    "L4": 0.4,   # 四级标签权重
}

# 各级标签字段
L1_FIELDS = ["scene_type", "time_of_day", "shot_size"]
L2_FIELDS = ["camera_move", "action_type", "mood"]
L3_FIELDS = ["characters", "props", "vfx", "environment"]
L4_FIELDS = ["free_tags", "source_work", "summary"]


# ============================================================
# 标签数据类
# ============================================================

@dataclass
class AssetTags:
    """素材标签"""
    
    # L1 一级标签（必填）
    scene_type: str = "UNKNOWN"      # INT | EXT | INT-EXT | UNKNOWN
    time_of_day: str = "UNKNOWN"     # DAY | NIGHT | DAWN | DUSK | UNKNOWN
    shot_size: str = "UNKNOWN"       # ECU | CU | MCU | MS | MLS | LS | ELS | UNKNOWN
    
    # L2 二级标签（必填）
    camera_move: str = "UNKNOWN"     # STATIC | PAN | TILT | DOLLY | CRANE | HANDHELD | ZOOM
    action_type: str = "UNKNOWN"     # FIGHT | CHASE | DIALOGUE | IDLE | RUN | FLY | TRANSFORM | SKILL
    mood: str = "UNKNOWN"            # TENSE | SAD | HAPPY | CALM | HORROR | ROMANTIC | EPIC | NEUTRAL
    
    # L3 三级标签（可选）
    characters: List[str] = field(default_factory=list)
    props: List[str] = field(default_factory=list)
    vfx: List[str] = field(default_factory=list)
    environment: List[str] = field(default_factory=list)
    
    # L4 四级标签（自由）
    free_tags: List[str] = field(default_factory=list)  # max 10
    source_work: str = ""
    summary: str = ""  # max 50 chars
    
    def validate(self) -> List[str]:
        """验证标签，返回错误列表"""
        errors = []
        
        # 验证 L1 标签
        if self.scene_type not in [e.value for e in SceneType]:
            errors.append(f"无效的 scene_type: {self.scene_type}")
        if self.time_of_day not in [e.value for e in TimeOfDay]:
            errors.append(f"无效的 time_of_day: {self.time_of_day}")
        if self.shot_size not in [e.value for e in ShotSize]:
            errors.append(f"无效的 shot_size: {self.shot_size}")
        
        # 验证 L2 标签
        if self.camera_move not in [e.value for e in CameraMove]:
            errors.append(f"无效的 camera_move: {self.camera_move}")
        if self.action_type not in [e.value for e in ActionType]:
            errors.append(f"无效的 action_type: {self.action_type}")
        if self.mood not in [e.value for e in Mood]:
            errors.append(f"无效的 mood: {self.mood}")
        
        # 验证 L4 标签
        if len(self.free_tags) > 10:
            errors.append(f"free_tags 超过 10 个: {len(self.free_tags)}")
        if len(self.summary) > 50:
            errors.append(f"summary 超过 50 字符: {len(self.summary)}")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查标签是否有效"""
        return len(self.validate()) == 0
    
    def get_coverage(self) -> Dict[str, float]:
        """计算标签覆盖率"""
        l1_filled = sum(1 for f in L1_FIELDS if getattr(self, f) != "UNKNOWN")
        l2_filled = sum(1 for f in L2_FIELDS if getattr(self, f) != "UNKNOWN")
        l3_filled = sum(1 for f in ["characters", "props", "vfx", "environment"] if getattr(self, f))
        l4_filled = sum(1 for f in ["free_tags", "source_work", "summary"] if getattr(self, f))
        
        return {
            "L1": l1_filled / len(L1_FIELDS),
            "L2": l2_filled / len(L2_FIELDS),
            "L3": l3_filled / 4,
            "L4": l4_filled / 3,
            "total": (l1_filled + l2_filled + l3_filled + l4_filled) / 13
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            # L1
            "scene_type": self.scene_type,
            "time_of_day": self.time_of_day,
            "shot_size": self.shot_size,
            # L2
            "camera_move": self.camera_move,
            "action_type": self.action_type,
            "mood": self.mood,
            # L3
            "characters": self.characters,
            "props": self.props,
            "vfx": self.vfx,
            "environment": self.environment,
            # L4
            "free_tags": self.free_tags,
            "source_work": self.source_work,
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetTags":
        """从字典创建"""
        return cls(
            # L1
            scene_type=data.get("scene_type", "UNKNOWN"),
            time_of_day=data.get("time_of_day", "UNKNOWN"),
            shot_size=data.get("shot_size", "UNKNOWN"),
            # L2
            camera_move=data.get("camera_move", "UNKNOWN"),
            action_type=data.get("action_type", "UNKNOWN"),
            mood=data.get("mood", "UNKNOWN"),
            # L3
            characters=data.get("characters", []),
            props=data.get("props", []),
            vfx=data.get("vfx", []),
            environment=data.get("environment", []),
            # L4
            free_tags=data.get("free_tags", [])[:10],
            source_work=data.get("source_work", ""),
            summary=data.get("summary", "")[:50],
        )
    
    @classmethod
    def from_legacy(cls, legacy_tags: Dict[str, Any]) -> "AssetTags":
        """从旧版标签格式转换"""
        return cls(
            # L1 - 从旧格式映射
            scene_type=SceneType.from_chinese(legacy_tags.get("scene_type", "")).value,
            time_of_day=TimeOfDay.from_chinese(legacy_tags.get("time", "")).value,
            shot_size=ShotSize.from_chinese(legacy_tags.get("shot_type", "")).value,
            # L2
            camera_move=CameraMove.from_chinese(legacy_tags.get("camera_move", "")).value,
            action_type=ActionType.from_chinese(legacy_tags.get("action", "")).value,
            mood=Mood.from_chinese(legacy_tags.get("mood", "")).value,
            # L3
            characters=legacy_tags.get("characters", []),
            props=[],
            vfx=[],
            environment=[],
            # L4
            free_tags=legacy_tags.get("free_tags", [])[:10],
            source_work=legacy_tags.get("source_anime", ""),
            summary=legacy_tags.get("summary", "")[:50],
        )
    
    def get_search_text(self) -> str:
        """生成用于向量搜索的文本"""
        parts = []
        
        # L1 标签
        if self.scene_type != "UNKNOWN":
            parts.append(f"场景:{self.scene_type}")
        if self.time_of_day != "UNKNOWN":
            parts.append(f"时间:{self.time_of_day}")
        if self.shot_size != "UNKNOWN":
            parts.append(f"镜头:{self.shot_size}")
        
        # L2 标签
        if self.action_type != "UNKNOWN":
            parts.append(f"动作:{self.action_type}")
        if self.mood != "UNKNOWN":
            parts.append(f"情绪:{self.mood}")
        
        # L3 标签
        if self.characters:
            parts.append(f"角色:{','.join(self.characters)}")
        if self.vfx:
            parts.append(f"特效:{','.join(self.vfx)}")
        if self.environment:
            parts.append(f"环境:{','.join(self.environment)}")
        
        # L4 标签
        if self.free_tags:
            parts.append(' '.join(self.free_tags))
        if self.summary:
            parts.append(self.summary)
        
        return ' '.join(parts)
    
    def match_score(self, query_tags: "AssetTags") -> float:
        """计算与查询标签的匹配分数"""
        score = 0.0
        total_weight = 0.0
        
        # L1 匹配
        for field in L1_FIELDS:
            total_weight += TAG_WEIGHTS["L1"]
            if getattr(self, field) == getattr(query_tags, field) and getattr(self, field) != "UNKNOWN":
                score += TAG_WEIGHTS["L1"]
        
        # L2 匹配
        for field in L2_FIELDS:
            total_weight += TAG_WEIGHTS["L2"]
            if getattr(self, field) == getattr(query_tags, field) and getattr(self, field) != "UNKNOWN":
                score += TAG_WEIGHTS["L2"]
        
        # L3 匹配（列表交集）
        for field in ["characters", "props", "vfx", "environment"]:
            query_list = getattr(query_tags, field)
            self_list = getattr(self, field)
            if query_list:
                total_weight += TAG_WEIGHTS["L3"]
                if self_list:
                    intersection = set(query_list) & set(self_list)
                    if intersection:
                        score += TAG_WEIGHTS["L3"] * len(intersection) / len(query_list)
        
        # L4 匹配（free_tags 交集）
        if query_tags.free_tags:
            total_weight += TAG_WEIGHTS["L4"]
            if self.free_tags:
                intersection = set(query_tags.free_tags) & set(self.free_tags)
                if intersection:
                    score += TAG_WEIGHTS["L4"] * len(intersection) / len(query_tags.free_tags)
        
        return score / total_weight if total_weight > 0 else 0.0


# ============================================================
# 标签关键词映射（用于从文件名提取标签）
# ============================================================

KEYWORD_MAPPINGS = {
    # 场景类型
    "scene_type": {
        "INT": ["室内", "房间", "屋", "车厢", "餐厅", "教室", "办公室", "卧室"],
        "EXT": ["室外", "森林", "街道", "天空", "山", "海", "草原", "城市", "战场"],
    },
    # 时间
    "time_of_day": {
        "DAY": ["白天", "日", "阳光", "晴天", "午后"],
        "NIGHT": ["夜", "月", "黑暗", "星空", "深夜"],
        "DAWN": ["黎明", "日出", "清晨"],
        "DUSK": ["黄昏", "夕阳", "傍晚", "日落"],
    },
    # 镜头类型
    "shot_size": {
        "ECU": ["大特写", "眼睛", "嘴唇"],
        "CU": ["特写", "脸", "表情"],
        "MCU": ["近景", "半身"],
        "MS": ["中景", "腰部以上"],
        "LS": ["全景", "全身", "远景"],
        "ELS": ["大远景", "鸟瞰", "俯瞰"],
    },
    # 镜头运动
    "camera_move": {
        "STATIC": ["静止", "固定"],
        "PAN": ["横摇", "左右"],
        "TILT": ["俯仰", "上下"],
        "DOLLY": ["推轨", "推进", "拉远"],
        "CRANE": ["升降", "升起", "下降"],
        "HANDHELD": ["手持", "晃动"],
        "ZOOM": ["变焦", "拉近", "推远"],
    },
    # 动作类型
    "action_type": {
        "FIGHT": ["战斗", "打斗", "砍", "斩", "攻击", "技能", "对决", "格斗"],
        "CHASE": ["追逐", "追", "逃", "冲刺"],
        "DIALOGUE": ["对话", "说话", "交谈"],
        "IDLE": ["静态", "站立", "坐", "休息"],
        "RUN": ["跑", "奔跑", "冲"],
        "FLY": ["飞", "跳", "空中", "腾空"],
        "TRANSFORM": ["变身", "觉醒", "进化"],
        "SKILL": ["技能", "必杀", "绝招", "呼吸"],
    },
    # 情绪
    "mood": {
        "TENSE": ["紧张", "危险", "压迫"],
        "SAD": ["悲伤", "哭", "泪", "离别"],
        "HAPPY": ["欢乐", "笑", "搞笑", "开心"],
        "CALM": ["平静", "安静", "祥和"],
        "HORROR": ["恐怖", "惊悚", "阴森"],
        "ROMANTIC": ["浪漫", "爱情", "温馨"],
        "EPIC": ["热血", "燃", "激昂", "史诗", "震撼"],
    },
}

# 动漫作品关键词
ANIME_KEYWORDS = {
    "鬼灭之刃": ["鬼灭", "炭治郎", "弥豆子", "善逸", "伊之助", "鬼杀队", "呼吸", "日轮刀"],
    "进击的巨人": ["巨人", "艾伦", "三笠", "兵长", "立体机动"],
    "咒术回战": ["咒术", "虎杖", "五条", "领域展开"],
    "火影忍者": ["火影", "鸣人", "佐助", "卡卡西", "忍术", "查克拉"],
    "海贼王": ["海贼", "路飞", "索隆", "恶魔果实"],
    "龙珠": ["龙珠", "悟空", "贝吉塔", "超级赛亚人"],
    "JOJO": ["JOJO", "替身", "STAND"],
}

# 角色关键词
CHARACTER_KEYWORDS = {
    # 鬼灭之刃
    "炭治郎": ["炭治郎", "�的治郎", "灶门"],
    "善逸": ["善逸", "我妻"],
    "伊之助": ["伊之助", "�的之助"],
    "弥豆子": ["弥豆子", "祢豆子"],
    "义勇": ["义勇", "富冈"],
    "蝴蝶忍": ["蝴蝶忍", "胡蝶"],
    "炎柱": ["炎柱", "�的�的郎"],
    # 通用
    "主角": ["主角", "男主", "女主"],
    "反派": ["反派", "BOSS", "敌人"],
}

# 特效关键词
VFX_KEYWORDS = {
    "火焰": ["火", "焰", "燃烧", "炎"],
    "水流": ["水", "波", "浪", "流"],
    "雷电": ["雷", "电", "闪电", "霹雳"],
    "爆炸": ["爆", "炸", "爆发"],
    "光芒": ["光", "闪", "发光", "光芒"],
    "黑暗": ["暗", "黑", "阴影"],
    "冰雪": ["冰", "雪", "冻"],
    "风": ["风", "旋风", "龙卷"],
}
