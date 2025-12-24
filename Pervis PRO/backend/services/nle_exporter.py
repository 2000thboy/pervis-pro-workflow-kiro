"""
NLE 导出服务
支持 FCPXML (Premiere/Resolve) 和 CMX3600 EDL 格式导出
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import uuid
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
from sqlalchemy.orm import Session

from database import Project, Beat, Asset, ExportHistory

class NLEExporter:
    """非线性编辑软件(NLE)导出服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
        
    async def export_fcpxml(
        self,
        project_id: str,
        frame_rate: str = "24"
    ) -> Dict[str, Any]:
        """导出为 Final Cut Pro XML (FCPXML 1.9) - 兼容 Premiere Pro & Resolve"""
        try:
            # 1. 获取项目数据
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"status": "error", "message": "Project not found"}
                
            beats = self.db.query(Beat).filter(
                Beat.project_id == project_id
            ).order_by(Beat.order_index).all()
            
            # 2. 基础参数计算
            fps_map = {
                "24": ("2400", "100"),
                "25": ("25", "1"),
                "30": ("3000", "100"),
                "60": ("6000", "100")
            }
            frame_duration = fps_map.get(frame_rate, ("2400", "100")) 
            # FCPXML uses rational time: value/timescale
            
            # 3. 构建 XML 结构
            root = ET.Element("fcpxml", version="1.9")
            
            # Resources (Assets)
            resources = ET.SubElement(root, "resources")
            
            # Format Resource
            fmt_id = "r1"
            ET.SubElement(resources, "format", id=fmt_id, frameDuration=f"{frame_duration[1]}/{frame_duration[0]}s", width="1920", height="1080")
            
            # Project Library (Sequence)
            library = ET.SubElement(root, "library")
            event = ET.SubElement(library, "event", name=project.title)
            project_node = ET.SubElement(event, "project", name=project.title)
            sequence = ET.SubElement(project_node, "sequence", format=fmt_id)
            spine = ET.SubElement(sequence, "spine")
            
            total_duration_frames = 0
            asset_resource_map = {} # map asset_path -> resource_id
            res_counter = 2
            
            # 4. 遍历 Beats 生成 Clips
            current_frame_start = 0
            
            for beat in beats:
                duration_sec = beat.duration or 3.0 # Default 3s
                duration_frames = int(duration_sec * int(frame_rate))
                
                # 尝试找到关联的 Asset
                asset = None
                if beat.files and len(beat.files) > 0:
                     # 假设 beat.files[0] 是 asset_id
                     asset_id = beat.files[0]
                     asset = self.db.query(Asset).filter(Asset.id == asset_id).first()
                
                # 创建 Clip 节点
                # 如果有 Asset，创建 asset-clip (video)，否则创建 gap (slug)
                clip_node = None
                
                if asset and asset.file_path and os.path.exists(asset.file_path):
                    file_path = os.path.abspath(asset.file_path)
                    
                    # 注册 Resource
                    if file_path not in asset_resource_map:
                        rid = f"r{res_counter}"
                        res_counter += 1
                        asset_resource_map[file_path] = rid
                        # Add asset element to resources
                        asset_res = ET.SubElement(resources, "asset", id=rid, name=asset.filename, src=f"file://localhost{file_path.replace(os.sep, '/')}")
                        ET.SubElement(asset_res, "media-rep", kind="original-media", src=f"file://localhost{file_path.replace(os.sep, '/')}")
                    
                    res_id = asset_resource_map[file_path]
                    
                    # Asset Clip
                    clip_node = ET.SubElement(spine, "asset-clip")
                    clip_node.set("ref", res_id)
                    clip_node.set("name", beat.content[:30] if beat.content else f"Beat {beat.order_index}")
                    
                    # 假定使用整个 asset duration，或者 beat duration
                    # 这里为了简单，我们让 clip 长度 = beat duration
                    # 但 Asset 需要有足够长度。如果 Asset 短于 beat，需要 loop 或 gap。
                    # 简化: Asset Clip length = Beat Duration
                    clip_node.set("duration", f"{duration_frames * int(frame_duration[1])}/{frame_duration[0]}s")
                    clip_node.set("offset", f"{current_frame_start * int(frame_duration[1])}/{frame_duration[0]}s")
                    
                else:
                    # Gap (Slug)
                    clip_node = ET.SubElement(spine, "gap")
                    clip_node.set("name", beat.content[:30] if beat.content else "Slug")
                    clip_node.set("duration", f"{duration_frames * int(frame_duration[1])}/{frame_duration[0]}s")
                    clip_node.set("offset", f"{current_frame_start * int(frame_duration[1])}/{frame_duration[0]}s")
                
                # 添加 Metadata (Notes)
                if beat.content:
                    note = ET.SubElement(clip_node, "note")
                    note.text = beat.content
                
                current_frame_start += duration_frames
            
            # 5. 保存文件
            xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            filename = f"{project_id}_premiere_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            file_path = self.export_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(xml_str)
                
            # 6. 记录历史
            self._record_history(project_id, "fcpxml", str(file_path), "xml")
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "export_id": str(uuid.uuid4()) # Placeholder
            }
            
        except Exception as e:
            return {"status": "error", "message": f"FCPXML Export Failed: {str(e)}"}

    async def export_edl_cmx3600(
        self,
        project_id: str,
        frame_rate: int = 24
    ) -> Dict[str, Any]:
        """导出 CMX3600 EDL"""
        try:
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"status": "error", "message": "Project not found"}
                
            beats = self.db.query(Beat).filter(
                Beat.project_id == project_id
            ).order_by(Beat.order_index).all()
            
            lines = []
            lines.append(f"TITLE: {project.title}")
            lines.append("FCM: NON-DROP FRAME")
            lines.append("")
            
            current_time_frame = 0 # Timeline start at 00:00:00:00
            
            for i, beat in enumerate(beats):
                event_num = f"{i+1:03d}"
                reel = "AX" # Auxiliary Reel (Placeholder)
                
                # Try to find real reel name if asset exists
                if beat.files and len(beat.files) > 0:
                     asset = self.db.query(Asset).filter(Asset.id == beat.files[0]).first()
                     if asset:
                         reel = asset.filename[:8].upper().replace(" ", "_")
                
                track = "V"
                trans = "C" # Cut
                
                # Source TC (Placeholder 01:00:00:00 for all sources for now)
                src_in_frames = 3600 * frame_rate 
                duration_frames = int((beat.duration or 3.0) * frame_rate)
                src_out_frames = src_in_frames + duration_frames
                
                # Record TC (Timeline)
                rec_in_frames = current_time_frame
                rec_out_frames = rec_in_frames + duration_frames
                
                # Format TCs
                def frames_to_tc(frames, fps):
                    h = int(frames / (3600 * fps))
                    m = int((frames % (3600 * fps)) / (60 * fps))
                    s = int((frames % (60 * fps)) / fps)
                    f = int(frames % fps)
                    return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
                
                line = f"{event_num}  {reel:<8} {track:<4} {trans:<4} {frames_to_tc(src_in_frames, frame_rate)} {frames_to_tc(src_out_frames, frame_rate)} {frames_to_tc(rec_in_frames, frame_rate)} {frames_to_tc(rec_out_frames, frame_rate)}"
                lines.append(line)
                
                # Comment
                if beat.content:
                    lines.append(f"* FROM CLIP NAME: {beat.content[:60]}")
                    
                current_time_frame += duration_frames
                
            # Save
            filename = f"{project_id}_edl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.edl"
            file_path = self.export_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
                
            self._record_history(project_id, "edl", str(file_path), "edl")
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "export_id": "new-id"
            }
            
        except Exception as e:
            return {"status": "error", "message": f"EDL Export Failed: {str(e)}"}

    def _record_history(self, project_id, export_type, path, fmt):
        try:
            record = ExportHistory(
                id=str(uuid.uuid4()),
                project_id=project_id,
                export_type=export_type,
                file_path=path,
                file_size=os.path.getsize(path),
                file_format=fmt,
                status="completed",
                created_at=datetime.now()
            )
            self.db.add(record)
            self.db.commit()
        except:
            pass
