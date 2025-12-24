"""
标签管理服务
支持标签层级管理和权重调整
"""

from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import TagHierarchy, AssetTag, Asset


class TagManager:
    """标签管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_video_tags(self, asset_id: str) -> Dict[str, Any]:
        """获取视频的所有标签及其层级关系"""
        try:
            # 检查资产是否存在
            asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                return {"status": "error", "message": "资产不存在"}
            
            # 获取资产的所有标签
            asset_tags = self.db.query(AssetTag).filter(
                AssetTag.asset_id == asset_id
            ).order_by(AssetTag.order_index).all()
            
            # 构建标签层级树
            tags_data = []
            for asset_tag in asset_tags:
                tag = self.db.query(TagHierarchy).filter(
                    TagHierarchy.id == asset_tag.tag_id
                ).first()
                
                if tag:
                    # 获取父标签
                    parent_tag = None
                    if tag.parent_id:
                        parent_tag = self.db.query(TagHierarchy).filter(
                            TagHierarchy.id == tag.parent_id
                        ).first()
                    
                    # 获取子标签
                    children = self.db.query(TagHierarchy).filter(
                        TagHierarchy.parent_id == tag.id
                    ).all()
                    
                    tags_data.append({
                        "tag_id": tag.id,
                        "tag_name": tag.tag_name,
                        "category": tag.category,
                        "level": tag.level,
                        "parent_id": tag.parent_id,
                        "parent_name": parent_tag.tag_name if parent_tag else None,
                        "children": [{"id": c.id, "name": c.tag_name} for c in children],
                        "weight": asset_tag.weight,
                        "order": asset_tag.order_index,
                        "source": asset_tag.source
                    })
            
            return {
                "status": "success",
                "asset_id": asset_id,
                "tags": tags_data,
                "total_tags": len(tags_data)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"获取标签失败: {str(e)}"
            }
    
    async def update_tag_hierarchy(
        self,
        asset_id: str,
        tag_id: str,
        parent_tag_id: Optional[str],
        order: int
    ) -> Dict[str, Any]:
        """更新标签的层级关系和顺序"""
        try:
            # 检查标签是否存在
            tag = self.db.query(TagHierarchy).filter(TagHierarchy.id == tag_id).first()
            if not tag:
                return {"status": "error", "message": "标签不存在"}
            
            # 检查是否会形成循环
            if parent_tag_id:
                if await self._check_circular_reference(tag_id, parent_tag_id):
                    return {"status": "error", "message": "不能设置循环引用"}
            
            # 更新标签层级
            tag.parent_id = parent_tag_id
            tag.updated_at = datetime.now()
            
            # 更新资产标签顺序
            asset_tag = self.db.query(AssetTag).filter(
                and_(AssetTag.asset_id == asset_id, AssetTag.tag_id == tag_id)
            ).first()
            
            if asset_tag:
                asset_tag.order_index = order
                asset_tag.updated_at = datetime.now()
            
            self.db.commit()
            
            return {
                "status": "success",
                "message": "标签层级更新成功"
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"更新标签层级失败: {str(e)}"
            }
    
    async def update_tag_weight(
        self,
        asset_id: str,
        tag_id: str,
        weight: float
    ) -> Dict[str, Any]:
        """更新标签的关联度权重"""
        try:
            # 验证权重范围
            if not 0.0 <= weight <= 1.0:
                return {"status": "error", "message": "权重必须在0.0-1.0之间"}
            
            # 查找资产标签
            asset_tag = self.db.query(AssetTag).filter(
                and_(AssetTag.asset_id == asset_id, AssetTag.tag_id == tag_id)
            ).first()
            
            if not asset_tag:
                return {"status": "error", "message": "资产标签关联不存在"}
            
            # 更新权重
            asset_tag.weight = weight
            asset_tag.updated_at = datetime.now()
            
            self.db.commit()
            
            return {
                "status": "success",
                "message": "标签权重更新成功",
                "new_weight": weight
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"更新标签权重失败: {str(e)}"
            }
    
    async def batch_update_tags(
        self,
        asset_id: str,
        updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量更新标签"""
        try:
            success_count = 0
            failed_updates = []
            
            for update in updates:
                tag_id = update.get("tag_id")
                
                # 更新权重
                if "weight" in update:
                    result = await self.update_tag_weight(
                        asset_id, tag_id, update["weight"]
                    )
                    if result["status"] == "success":
                        success_count += 1
                    else:
                        failed_updates.append({
                            "tag_id": tag_id,
                            "error": result["message"]
                        })
                
                # 更新层级
                if "parent_id" in update or "order" in update:
                    result = await self.update_tag_hierarchy(
                        asset_id,
                        tag_id,
                        update.get("parent_id"),
                        update.get("order", 0)
                    )
                    if result["status"] == "success":
                        success_count += 1
                    else:
                        failed_updates.append({
                            "tag_id": tag_id,
                            "error": result["message"]
                        })
            
            return {
                "status": "success",
                "success_count": success_count,
                "failed_count": len(failed_updates),
                "failed_updates": failed_updates
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "status": "error",
                "message": f"批量更新失败: {str(e)}"
            }
    
    async def _check_circular_reference(self, tag_id: str, parent_id: str) -> bool:
        """检查是否会形成循环引用"""
        visited = set()
        current_id = parent_id
        
        while current_id:
            if current_id == tag_id:
                return True  # 发现循环
            
            if current_id in visited:
                return True  # 发现循环
            
            visited.add(current_id)
            
            # 获取父标签
            parent = self.db.query(TagHierarchy).filter(
                TagHierarchy.id == current_id
            ).first()
            
            if not parent:
                break
            
            current_id = parent.parent_id
        
        return False  # 没有循环
