# -*- coding: utf-8 -*-
"""
Market_Agent 服务（市场分析 Agent）

Feature: pervis-project-wizard Phase 2
Task: 2.7 实现 Market_Agent

提供市场分析功能：
- 目标受众分析
- 市场定位
- 竞品分析
- 发行渠道建议

Requirements: 11.2, 11.3, 11.4, 11.5, 11.6, 11.7
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class AudienceProfile:
    """目标受众画像"""
    primary_age_range: str = ""
    gender_distribution: str = ""
    interests: List[str] = field(default_factory=list)
    viewing_habits: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_age_range": self.primary_age_range,
            "gender_distribution": self.gender_distribution,
            "interests": self.interests,
            "viewing_habits": self.viewing_habits,
            "platforms": self.platforms
        }


@dataclass
class CompetitorInfo:
    """竞品信息"""
    title: str
    year: int = 0
    genre: str = ""
    box_office: str = ""
    rating: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "year": self.year,
            "genre": self.genre,
            "box_office": self.box_office,
            "rating": self.rating,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses
        }


@dataclass
class MarketAnalysisResult:
    """市场分析结果"""
    analysis_id: str
    project_id: str
    audience: AudienceProfile = field(default_factory=AudienceProfile)
    market_position: str = ""
    competitors: List[CompetitorInfo] = field(default_factory=list)
    distribution_channels: List[str] = field(default_factory=list)
    marketing_suggestions: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    estimated_budget_range: str = ""
    confidence: float = 0.7
    is_dynamic: bool = False  # 是否基于实际项目数据
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "project_id": self.project_id,
            "audience": self.audience.to_dict(),
            "market_position": self.market_position,
            "competitors": [c.to_dict() for c in self.competitors],
            "distribution_channels": self.distribution_channels,
            "marketing_suggestions": self.marketing_suggestions,
            "risk_factors": self.risk_factors,
            "opportunities": self.opportunities,
            "estimated_budget_range": self.estimated_budget_range,
            "confidence": self.confidence,
            "is_dynamic": self.is_dynamic,
            "created_at": self.created_at.isoformat()
        }


class MarketAgentService:
    """
    Market_Agent 服务
    
    市场分析 Agent，提供市场洞察和发行建议
    """
    
    def __init__(self):
        self._llm_adapter = None
        self._analysis_cache: Dict[str, MarketAnalysisResult] = {}
    
    def _get_llm_adapter(self):
        """延迟加载 LLM 适配器"""
        if self._llm_adapter is None:
            try:
                from services.agent_llm_adapter import get_agent_llm_adapter
                self._llm_adapter = get_agent_llm_adapter()
            except Exception as e:
                logger.error(f"LLM 适配器加载失败: {e}")
        return self._llm_adapter
    
    async def analyze_market(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> MarketAnalysisResult:
        """
        市场分析
        
        Args:
            project_id: 项目ID
            project_data: 项目数据（包含类型、剧本、角色等）
        
        Returns:
            市场分析结果
        """
        adapter = self._get_llm_adapter()
        
        # 创建基础结果
        result = MarketAnalysisResult(
            analysis_id=f"mkt_{uuid4().hex[:12]}",
            project_id=project_id
        )
        
        # 提取项目信息
        project_type = project_data.get("project_type", "short_film")
        genre = project_data.get("genre", "")
        logline = project_data.get("logline", "")
        synopsis = project_data.get("synopsis", "")
        duration = project_data.get("duration_minutes", 0)
        
        if adapter:
            try:
                # 使用 LLM 生成分析
                response = await adapter.analyze_market(project_data)
                
                if response.success and response.parsed_data:
                    data = response.parsed_data
                    
                    # 填充受众信息
                    if "audience" in data:
                        aud = data["audience"]
                        result.audience = AudienceProfile(
                            primary_age_range=aud.get("age_range", "18-35"),
                            gender_distribution=aud.get("gender", "均衡"),
                            interests=aud.get("interests", []),
                            viewing_habits=aud.get("habits", []),
                            platforms=aud.get("platforms", [])
                        )
                    
                    result.market_position = data.get("position", "")
                    result.distribution_channels = data.get("channels", [])
                    result.marketing_suggestions = data.get("suggestions", [])
                    result.risk_factors = data.get("risks", [])
                    result.opportunities = data.get("opportunities", [])
                    result.confidence = data.get("confidence", 0.7)
                    result.is_dynamic = True
                    
                    # 缓存结果
                    self._analysis_cache[project_id] = result
                    return result
                    
            except Exception as e:
                logger.error(f"LLM 市场分析失败: {e}")
        
        # 回退：基于规则的分析
        result = self._rule_based_analysis(project_id, project_data)
        self._analysis_cache[project_id] = result
        return result
    
    def _rule_based_analysis(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> MarketAnalysisResult:
        """基于规则的市场分析（回退方案）"""
        project_type = project_data.get("project_type", "short_film")
        duration = project_data.get("duration_minutes", 0)
        
        result = MarketAnalysisResult(
            analysis_id=f"mkt_{uuid4().hex[:12]}",
            project_id=project_id,
            is_dynamic=False,
            confidence=0.5
        )
        
        # 根据项目类型设置默认值
        type_profiles = {
            "short_film": {
                "audience": AudienceProfile(
                    primary_age_range="18-35",
                    gender_distribution="均衡",
                    interests=["独立电影", "艺术片", "电影节"],
                    viewing_habits=["流媒体", "电影节", "短视频平台"],
                    platforms=["YouTube", "Vimeo", "B站", "电影节"]
                ),
                "position": "独立短片市场，面向电影爱好者和专业观众",
                "channels": ["电影节投递", "流媒体平台", "社交媒体推广"],
                "suggestions": [
                    "参加国内外短片电影节",
                    "在 B站/YouTube 发布预告片",
                    "建立社交媒体账号进行宣传"
                ]
            },
            "advertisement": {
                "audience": AudienceProfile(
                    primary_age_range="25-45",
                    gender_distribution="根据产品定位",
                    interests=["消费品", "品牌"],
                    viewing_habits=["电视", "社交媒体", "视频网站"],
                    platforms=["电视", "抖音", "微信", "YouTube"]
                ),
                "position": "商业广告市场",
                "channels": ["电视投放", "社交媒体", "视频网站贴片"],
                "suggestions": [
                    "明确目标受众画像",
                    "制作多版本适配不同平台",
                    "配合产品发布节点投放"
                ]
            },
            "music_video": {
                "audience": AudienceProfile(
                    primary_age_range="15-30",
                    gender_distribution="根据艺人粉丝群体",
                    interests=["音乐", "娱乐", "偶像"],
                    viewing_habits=["音乐平台", "短视频", "社交媒体"],
                    platforms=["QQ音乐", "网易云", "B站", "抖音"]
                ),
                "position": "音乐视频市场",
                "channels": ["音乐平台首发", "社交媒体推广", "粉丝社群"],
                "suggestions": [
                    "配合专辑/单曲发布",
                    "制作幕后花絮增加互动",
                    "利用粉丝社群进行预热"
                ]
            },
            "feature_film": {
                "audience": AudienceProfile(
                    primary_age_range="18-50",
                    gender_distribution="根据题材",
                    interests=["电影", "娱乐"],
                    viewing_habits=["影院", "流媒体"],
                    platforms=["院线", "爱奇艺", "腾讯视频", "Netflix"]
                ),
                "position": "院线/流媒体电影市场",
                "channels": ["院线发行", "流媒体平台", "海外发行"],
                "suggestions": [
                    "制定完整的宣发计划",
                    "参加电影节争取奖项",
                    "建立多渠道发行策略"
                ]
            }
        }
        
        profile = type_profiles.get(project_type, type_profiles["short_film"])
        
        result.audience = profile["audience"]
        result.market_position = profile["position"]
        result.distribution_channels = profile["channels"]
        result.marketing_suggestions = profile["suggestions"]
        
        # 通用风险和机会
        result.risk_factors = [
            "市场竞争激烈",
            "观众注意力分散",
            "宣发预算有限"
        ]
        result.opportunities = [
            "新媒体平台降低发行门槛",
            "垂直领域受众精准",
            "口碑传播效应"
        ]
        
        return result
    
    def get_dynamic_analysis(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ) -> MarketAnalysisResult:
        """
        获取动态分析（基于实际项目数据）
        
        如果有缓存且项目数据未变化，返回缓存
        """
        cached = self._analysis_cache.get(project_id)
        if cached and cached.is_dynamic:
            return cached
        
        # 需要重新分析
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.analyze_market(project_id, project_data)
        )
    
    def get_cached_analysis(
        self,
        project_id: str
    ) -> Optional[MarketAnalysisResult]:
        """获取缓存的分析结果"""
        return self._analysis_cache.get(project_id)
    
    def clear_cache(self, project_id: str):
        """清除缓存"""
        if project_id in self._analysis_cache:
            del self._analysis_cache[project_id]


# 全局服务实例
_market_agent_service: Optional[MarketAgentService] = None


def get_market_agent_service() -> MarketAgentService:
    """获取 Market_Agent 服务实例"""
    global _market_agent_service
    if _market_agent_service is None:
        _market_agent_service = MarketAgentService()
    return _market_agent_service
