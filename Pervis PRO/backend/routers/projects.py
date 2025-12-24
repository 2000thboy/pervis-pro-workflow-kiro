"""
项目管理API路由
处理项目创建、管理和Beat分析
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

from database import get_db

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    title: str
    script_raw: str
    logline: str

class ProjectResponse(BaseModel):
    id: str
    title: str
    script_raw: str
    logline: Optional[str] = ""
    created_at: str
    beats_count: int = 0

class Beat(BaseModel):
    id: str
    content: str
    order_index: int
    emotion_tags: List[str] = []
    scene_tags: List[str] = []
    duration: Optional[float] = None

class BeatsResponse(BaseModel):
    project_id: str
    beats: List[Beat]

@router.post("", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """创建新项目并分析剧本"""
    try:
        project_id = str(uuid.uuid4())
        
        # 插入项目记录
        db.execute(
            text("""
            INSERT INTO projects (id, title, script_raw, logline, created_at)
            VALUES (:id, :title, :script_raw, :logline, :created_at)
            """),
            {
                "id": project_id,
                "title": project.title,
                "script_raw": project.script_raw,
                "logline": project.logline,
                "created_at": datetime.now()
            }
        )
        
        # 简单的剧本分析 - 生成基础Beats
        script_lines = [line.strip() for line in project.script_raw.split('\n') if line.strip()]
        
        beats = []
        current_beat = ""
        beat_count = 0
        
        for line in script_lines:
            if line.startswith(('EXT.', 'INT.', 'FADE IN:', 'FADE OUT:', 'CUT TO:')):
                # 场景转换，创建新Beat
                if current_beat:
                    beats.append({
                        'content': current_beat.strip(),
                        'emotion_tags': ['neutral'],
                        'scene_tags': ['scene'],
                        'duration': 5.0
                    })
                    beat_count += 1
                current_beat = line
            else:
                current_beat += " " + line
                
            # 限制Beat数量
            if beat_count >= 10:
                break
        
        # 添加最后一个Beat
        if current_beat and beat_count < 10:
            beats.append({
                'content': current_beat.strip(),
                'emotion_tags': ['neutral'],
                'scene_tags': ['scene'],
                'duration': 5.0
            })
        
        # 如果没有生成任何Beat，创建一个默认的
        if not beats:
            beats = [{
                'content': project.script_raw[:200] + "..." if len(project.script_raw) > 200 else project.script_raw,
                'emotion_tags': ['neutral'],
                'scene_tags': ['general'],
                'duration': 10.0
            }]
        
        # 保存Beats
        for i, beat in enumerate(beats):
            beat_id = str(uuid.uuid4())
            db.execute(
                text("""
                INSERT INTO beats (id, project_id, content, order_index, emotion_tags, scene_tags, duration)
                VALUES (:id, :project_id, :content, :order_index, :emotion_tags, :scene_tags, :duration)
                """),
                {
                    "id": beat_id,
                    "project_id": project_id,
                    "content": beat.get('content', ''),
                    "order_index": i,
                    "emotion_tags": ','.join(beat.get('emotion_tags', [])),
                    "scene_tags": ','.join(beat.get('scene_tags', [])),
                    "duration": beat.get('duration', 5.0)
                }
            )
        
        db.commit()
        
        return ProjectResponse(
            id=project_id,
            title=project.title,
            script_raw=project.script_raw,
            logline=project.logline,
            created_at=datetime.now().isoformat(),
            beats_count=len(beats)
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"项目创建失败: {str(e)}")

@router.get("/{project_id}/beats", response_model=BeatsResponse)
async def get_project_beats(project_id: str, db: Session = Depends(get_db)):
    """获取项目的Beat列表"""
    try:
        # 检查项目是否存在
        project = db.execute(
            text("SELECT id FROM projects WHERE id = :project_id"),
            {"project_id": project_id}
        ).fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取Beats
        beats_data = db.execute(
            text("""
            SELECT id, content, order_index, emotion_tags, scene_tags, duration
            FROM beats 
            WHERE project_id = :project_id 
            ORDER BY order_index
            """),
            {"project_id": project_id}
        ).fetchall()
        
        beats = []
        for beat_row in beats_data:
            beats.append(Beat(
                id=beat_row[0],
                content=beat_row[1],
                order_index=beat_row[2],
                emotion_tags=beat_row[3].split(',') if beat_row[3] else [],
                scene_tags=beat_row[4].split(',') if beat_row[4] else [],
                duration=beat_row[5]
            ))
        
        return BeatsResponse(
            project_id=project_id,
            beats=beats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Beats失败: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """获取项目详情"""
    try:
        project_data = db.execute(
            text("SELECT id, title, script_raw, logline, created_at FROM projects WHERE id = :project_id"),
            {"project_id": project_id}
        ).fetchone()
        
        if not project_data:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 获取Beats数量
        beats_count = db.execute(
            text("SELECT COUNT(*) FROM beats WHERE project_id = :project_id"),
            {"project_id": project_id}
        ).fetchone()[0]
        
        return ProjectResponse(
            id=project_data[0],
            title=project_data[1],
            script_raw=project_data[2],
            logline=project_data[3] or "",
            created_at=project_data[4],
            beats_count=beats_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目失败: {str(e)}")

@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: Session = Depends(get_db)):
    """获取项目列表"""
    try:
        projects_data = db.execute(
            text("SELECT id, title, script_raw, logline, created_at FROM projects ORDER BY created_at DESC")
        ).fetchall()
        
        projects = []
        for project_row in projects_data:
            # 获取每个项目的Beats数量
            beats_count = db.execute(
                text("SELECT COUNT(*) FROM beats WHERE project_id = :project_id"),
                {"project_id": project_row[0]}
            ).fetchone()[0]
            
            projects.append(ProjectResponse(
                id=project_row[0],
                title=project_row[1],
                script_raw=project_row[2],
                logline=project_row[3] or "",
                created_at=project_row[4],
                beats_count=beats_count
            ))
        
        return projects
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """删除项目"""
    try:
        # 检查项目是否存在
        project = db.execute(
            text("SELECT id FROM projects WHERE id = :project_id"),
            {"project_id": project_id}
        ).fetchone()
        
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 删除相关的Beats
        db.execute(
            text("DELETE FROM beats WHERE project_id = :project_id"), 
            {"project_id": project_id}
        )
        
        # 删除项目
        db.execute(
            text("DELETE FROM projects WHERE id = :project_id"), 
            {"project_id": project_id}
        )
        
        db.commit()
        
        return {"message": "项目删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除项目失败: {str(e)}")