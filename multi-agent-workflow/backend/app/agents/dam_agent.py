"""
DAM Agent - 数字资产管理Agent

需求: 3.5 - WHEN 向量搜索完成后 THEN DAM_Agent SHALL 寻找匹配的标签素材
需求: 5.3 - WHEN 素材格式不符合规范时 THEN 系统Agent SHALL 强制接管并提示修复
需求: 5.4 - WHEN 标签命名不符合规则时 THEN 系统 SHALL 返回错误提示要求修复

本模块实现了DAM Agent，负责:
- 数字资产管理
- 标签管理
- 素材匹配
- 格式验证
"""
import asyncio
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from .base_agent import BaseAgent, AgentLifecycleState
from ..core.message_bus import MessageBus, Message, Response
from ..core.agent_types import AgentState, AgentType
from ..core.communication_protocol import (
    ProtocolMessage,
    ProtocolMessageType,
    ProtocolStatus,
)

logger = logging.getLogger(__name__)


class AssetType(Enum):
    """素材类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"
    MODEL_3D = "model_3d"


class AssetStatus(Enum):
    """素材状态枚举"""
    PENDING = "pending"
    VALIDATED = "validated"
    INVALID = "invalid"
    ARCHIVED = "archived"


# 支持的文件格式
SUPPORTED_FORMATS = {
    AssetType.VIDEO: [".mp4", ".mov", ".avi", ".mkv", ".webm"],
    AssetType.AUDIO: [".mp3", ".wav", ".aac", ".flac", ".ogg"],
    AssetType.IMAGE: [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"],
    AssetType.TEXT: [".txt", ".md", ".json", ".xml"],
    AssetType.MODEL_3D: [".obj", ".fbx", ".gltf", ".glb"],
}

# 标签命名规则：小写字母、数字、下划线、连字符
TAG_PATTERN = re.compile(r'^[a-z0-9_-]+$')


@dataclass
class Asset:
    """素材数据类"""
    asset_id: str
    name: str
    asset_type: AssetType
    file_path: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: AssetStatus = AssetStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "asset_type": self.asset_type.value,
            "file_path": self.file_path,
            "tags": self.tags,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class MatchResult:
    """素材匹配结果"""
    asset: Asset
    score: float
    matched_tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset.to_dict(),
            "score": self.score,
            "matched_tags": self.matched_tags
        }


class DAMAgent(BaseAgent):
    """
    DAM Agent - 数字资产管理Agent
    
    负责管理系统中的所有数字资产，包括:
    - 素材的添加、删除、更新
    - 标签管理和验证
    - 素材匹配和搜索
    - 格式验证
    
    需求: 3.5 - 寻找匹配的标签素材
    需求: 5.3 - 素材格式验证
    需求: 5.4 - 标签命名验证
    """
    
    # DAM Agent的固定ID
    DAM_AGENT_ID = "dam"
    
    def __init__(
        self,
        message_bus: MessageBus,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化DAM Agent
        
        Args:
            message_bus: 消息总线实例
            config: 配置选项
        """
        super().__init__(
            agent_id=self.DAM_AGENT_ID,
            agent_type=AgentType.DAM,
            message_bus=message_bus,
            capabilities=[
                "asset_management",
                "tag_management",
                "asset_matching",
                "format_validation",
                "metadata_extraction"
            ],
            config=config
        )
        
        # 素材存储
        self._assets: Dict[str, Asset] = {}
        # 标签索引：tag -> Set[asset_id]
        self._tag_index: Dict[str, Set[str]] = {}
        # 类型索引：asset_type -> Set[asset_id]
        self._type_index: Dict[AssetType, Set[str]] = {t: set() for t in AssetType}
        
        logger.info("DAM Agent创建完成")

    
    # ========================================================================
    # 生命周期钩子
    # ========================================================================
    
    async def _on_initialize(self):
        """初始化钩子"""
        # 注册数据请求处理器
        self.register_message_handler(
            ProtocolMessageType.DATA_REQUEST,
            self._handle_data_request
        )
        logger.info("DAM Agent初始化完成")
    
    async def _on_start(self):
        """启动钩子"""
        logger.info("DAM Agent已启动")
    
    async def _on_stop(self):
        """停止钩子"""
        logger.info("DAM Agent正在停止")
    
    # ========================================================================
    # 消息处理
    # ========================================================================
    
    async def handle_message(self, message: Message) -> Optional[Response]:
        """处理普通消息"""
        self._log_operation(
            "message_received",
            details={"message_id": message.id, "source": message.source}
        )
        return None
    
    async def handle_protocol_message(self, message: ProtocolMessage) -> Optional[ProtocolMessage]:
        """处理协议消息"""
        msg_type = message.payload.message_type
        
        if msg_type == ProtocolMessageType.DATA_REQUEST:
            return await self._handle_data_request(message)
        
        return None
    
    async def _handle_data_request(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理数据请求"""
        data = message.payload.data
        request_type = data.get("request_type")
        
        response_data = {}
        
        if request_type == "match_assets":
            tags = data.get("tags", [])
            asset_type = data.get("asset_type")
            limit = data.get("limit", 10)
            results = await self.match_assets(tags, asset_type, limit)
            response_data = {"results": [r.to_dict() for r in results]}
        elif request_type == "get_asset":
            asset_id = data.get("asset_id")
            asset = self.get_asset(asset_id)
            response_data = asset.to_dict() if asset else {"error": "Asset not found"}
        elif request_type == "list_assets":
            asset_type = data.get("asset_type")
            assets = self.list_assets(asset_type)
            response_data = {"assets": [a.to_dict() for a in assets]}
        elif request_type == "validate_tags":
            tags = data.get("tags", [])
            validation = self.validate_tags(tags)
            response_data = validation
        
        return message.create_response(
            ProtocolStatus.SUCCESS,
            data=response_data
        )

    
    # ========================================================================
    # 素材管理
    # ========================================================================
    
    def add_asset(
        self,
        asset_id: str,
        name: str,
        asset_type: AssetType,
        file_path: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        添加素材
        
        Args:
            asset_id: 素材ID
            name: 素材名称
            asset_type: 素材类型
            file_path: 文件路径
            tags: 标签列表
            metadata: 元数据
            
        Returns:
            (是否成功, 错误信息)
        """
        # 验证格式
        format_valid, format_error = self.validate_format(file_path, asset_type)
        if not format_valid:
            return False, format_error
        
        # 验证标签
        if tags:
            tag_validation = self.validate_tags(tags)
            if not tag_validation["valid"]:
                return False, f"Invalid tags: {tag_validation['invalid_tags']}"
        
        # 创建素材
        asset = Asset(
            asset_id=asset_id,
            name=name,
            asset_type=asset_type,
            file_path=file_path,
            tags=tags or [],
            metadata=metadata or {},
            status=AssetStatus.VALIDATED
        )
        
        # 存储素材
        self._assets[asset_id] = asset
        
        # 更新索引
        self._type_index[asset_type].add(asset_id)
        for tag in asset.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(asset_id)
        
        self._log_operation(
            "asset_added",
            details={"asset_id": asset_id, "name": name, "type": asset_type.value}
        )
        
        return True, None
    
    def remove_asset(self, asset_id: str) -> bool:
        """移除素材"""
        if asset_id not in self._assets:
            return False
        
        asset = self._assets[asset_id]
        
        # 从索引中移除
        self._type_index[asset.asset_type].discard(asset_id)
        for tag in asset.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(asset_id)
        
        # 删除素材
        del self._assets[asset_id]
        
        self._log_operation(
            "asset_removed",
            details={"asset_id": asset_id}
        )
        
        return True
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """获取素材"""
        return self._assets.get(asset_id)
    
    def list_assets(self, asset_type: Optional[AssetType] = None) -> List[Asset]:
        """列出素材"""
        if asset_type:
            asset_ids = self._type_index.get(asset_type, set())
            return [self._assets[aid] for aid in asset_ids if aid in self._assets]
        return list(self._assets.values())
    
    def update_asset_tags(self, asset_id: str, tags: List[str]) -> Tuple[bool, Optional[str]]:
        """更新素材标签"""
        if asset_id not in self._assets:
            return False, "Asset not found"
        
        # 验证标签
        tag_validation = self.validate_tags(tags)
        if not tag_validation["valid"]:
            return False, f"Invalid tags: {tag_validation['invalid_tags']}"
        
        asset = self._assets[asset_id]
        
        # 从旧标签索引中移除
        for old_tag in asset.tags:
            if old_tag in self._tag_index:
                self._tag_index[old_tag].discard(asset_id)
        
        # 更新标签
        asset.tags = tags
        asset.updated_at = datetime.utcnow().isoformat()
        
        # 添加到新标签索引
        for tag in tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(asset_id)
        
        return True, None

    
    # ========================================================================
    # 素材匹配 - 需求 3.5
    # ========================================================================
    
    async def match_assets(
        self,
        search_tags: List[str],
        asset_type: Optional[AssetType] = None,
        limit: int = 10
    ) -> List[MatchResult]:
        """
        根据标签匹配素材
        
        需求: 3.5 - WHEN 向量搜索完成后 THEN DAM_Agent SHALL 寻找匹配的标签素材
        
        Args:
            search_tags: 搜索标签列表
            asset_type: 素材类型过滤
            limit: 结果数量限制
            
        Returns:
            匹配结果列表
        """
        await self.update_work_state(AgentState.WORKING, "matching_assets")
        
        results: List[MatchResult] = []
        
        # 获取候选素材
        if asset_type:
            candidate_ids = self._type_index.get(asset_type, set())
        else:
            candidate_ids = set(self._assets.keys())
        
        # 计算每个素材的匹配分数
        for asset_id in candidate_ids:
            asset = self._assets.get(asset_id)
            if not asset:
                continue
            
            # 计算匹配的标签
            matched_tags = [tag for tag in search_tags if tag in asset.tags]
            
            if matched_tags:
                # 计算分数：匹配标签数 / 搜索标签数
                score = len(matched_tags) / len(search_tags) if search_tags else 0
                
                results.append(MatchResult(
                    asset=asset,
                    score=score,
                    matched_tags=matched_tags
                ))
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        await self.update_work_state(AgentState.IDLE)
        
        self._log_operation(
            "assets_matched",
            details={
                "search_tags": search_tags,
                "results_count": len(results[:limit])
            }
        )
        
        return results[:limit]
    
    def get_assets_by_tag(self, tag: str) -> List[Asset]:
        """根据标签获取素材"""
        asset_ids = self._tag_index.get(tag, set())
        return [self._assets[aid] for aid in asset_ids if aid in self._assets]
    
    def get_all_tags(self) -> List[str]:
        """获取所有标签"""
        return list(self._tag_index.keys())

    
    # ========================================================================
    # 格式验证 - 需求 5.3
    # ========================================================================
    
    def validate_format(
        self,
        file_path: str,
        asset_type: AssetType
    ) -> Tuple[bool, Optional[str]]:
        """
        验证素材格式
        
        需求: 5.3 - WHEN 素材格式不符合规范时 THEN 系统Agent SHALL 强制接管并提示修复
        
        Args:
            file_path: 文件路径
            asset_type: 素材类型
            
        Returns:
            (是否有效, 错误信息)
        """
        # 获取文件扩展名
        ext = self._get_file_extension(file_path)
        
        if not ext:
            return False, "File has no extension"
        
        # 检查是否是支持的格式
        supported = SUPPORTED_FORMATS.get(asset_type, [])
        
        if ext.lower() not in supported:
            return False, f"Unsupported format '{ext}' for {asset_type.value}. Supported: {supported}"
        
        return True, None
    
    def _get_file_extension(self, file_path: str) -> Optional[str]:
        """获取文件扩展名"""
        if '.' not in file_path:
            return None
        return '.' + file_path.rsplit('.', 1)[-1].lower()
    
    def get_supported_formats(self, asset_type: AssetType) -> List[str]:
        """获取支持的格式列表"""
        return SUPPORTED_FORMATS.get(asset_type, [])
    
    # ========================================================================
    # 标签验证 - 需求 5.4
    # ========================================================================
    
    def validate_tags(self, tags: List[str]) -> Dict[str, Any]:
        """
        验证标签命名
        
        需求: 5.4 - WHEN 标签命名不符合规则时 THEN 系统 SHALL 返回错误提示要求修复
        
        Args:
            tags: 标签列表
            
        Returns:
            验证结果
        """
        valid_tags = []
        invalid_tags = []
        
        for tag in tags:
            if self._is_valid_tag(tag):
                valid_tags.append(tag)
            else:
                invalid_tags.append(tag)
        
        return {
            "valid": len(invalid_tags) == 0,
            "valid_tags": valid_tags,
            "invalid_tags": invalid_tags,
            "rule": "Tags must contain only lowercase letters, numbers, underscores, and hyphens"
        }
    
    def _is_valid_tag(self, tag: str) -> bool:
        """检查标签是否有效"""
        if not tag or len(tag) > 50:
            return False
        return bool(TAG_PATTERN.match(tag))
    
    def normalize_tag(self, tag: str) -> str:
        """规范化标签"""
        # 转小写，替换空格为下划线，移除非法字符
        normalized = tag.lower().strip()
        normalized = re.sub(r'\s+', '_', normalized)
        normalized = re.sub(r'[^a-z0-9_-]', '', normalized)
        return normalized
    
    # ========================================================================
    # 状态查询
    # ========================================================================
    
    def get_dam_status(self) -> Dict[str, Any]:
        """获取DAM Agent状态"""
        return {
            **self.get_status(),
            "total_assets": len(self._assets),
            "total_tags": len(self._tag_index),
            "assets_by_type": {
                t.value: len(ids) for t, ids in self._type_index.items()
            }
        }
