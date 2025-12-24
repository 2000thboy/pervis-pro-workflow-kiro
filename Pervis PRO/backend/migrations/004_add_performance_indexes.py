"""
添加性能优化索引
提升常用查询的性能
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    """添加性能索引"""
    
    # Assets表索引 - 提升素材查询性能
    try:
        op.create_index('idx_assets_project_id', 'assets', ['project_id'])
        print("✅ 创建索引: idx_assets_project_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_assets_project_id - {e}")
    
    try:
        op.create_index('idx_assets_created_at', 'assets', ['created_at'])
        print("✅ 创建索引: idx_assets_created_at")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_assets_created_at - {e}")
    
    try:
        op.create_index('idx_assets_mime_type', 'assets', ['mime_type'])
        print("✅ 创建索引: idx_assets_mime_type")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_assets_mime_type - {e}")
    
    try:
        op.create_index('idx_assets_processing_status', 'assets', ['processing_status'])
        print("✅ 创建索引: idx_assets_processing_status")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_assets_processing_status - {e}")
    
    # AssetVectors表索引 - 提升向量搜索性能
    try:
        op.create_index('idx_asset_vectors_asset_id', 'asset_vectors', ['asset_id'])
        print("✅ 创建索引: idx_asset_vectors_asset_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_asset_vectors_asset_id - {e}")
    
    try:
        op.create_index('idx_asset_vectors_content_type', 'asset_vectors', ['content_type'])
        print("✅ 创建索引: idx_asset_vectors_content_type")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_asset_vectors_content_type - {e}")
    
    # Projects表索引 - 提升项目查询性能
    try:
        op.create_index('idx_projects_created_at', 'projects', ['created_at'])
        print("✅ 创建索引: idx_projects_created_at")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_projects_created_at - {e}")
    
    try:
        op.create_index('idx_projects_current_stage', 'projects', ['current_stage'])
        print("✅ 创建索引: idx_projects_current_stage")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_projects_current_stage - {e}")
    
    # Beats表索引 - 提升Beat查询性能
    try:
        op.create_index('idx_beats_project_id', 'beats', ['project_id'])
        print("✅ 创建索引: idx_beats_project_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_beats_project_id - {e}")
    
    try:
        op.create_index('idx_beats_order_index', 'beats', ['order_index'])
        print("✅ 创建索引: idx_beats_order_index")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_beats_order_index - {e}")
    
    # AssetSegments表索引 - 提升片段查询性能
    try:
        op.create_index('idx_asset_segments_asset_id', 'asset_segments', ['asset_id'])
        print("✅ 创建索引: idx_asset_segments_asset_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_asset_segments_asset_id - {e}")
    
    try:
        op.create_index('idx_asset_segments_time_range', 'asset_segments', ['start_time', 'end_time'])
        print("✅ 创建索引: idx_asset_segments_time_range")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_asset_segments_time_range - {e}")
    
    # FeedbackLogs表索引 - 提升反馈查询性能
    try:
        op.create_index('idx_feedback_logs_asset_id', 'feedback_logs', ['asset_id'])
        print("✅ 创建索引: idx_feedback_logs_asset_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_feedback_logs_asset_id - {e}")
    
    try:
        op.create_index('idx_feedback_logs_timestamp', 'feedback_logs', ['timestamp'])
        print("✅ 创建索引: idx_feedback_logs_timestamp")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_feedback_logs_timestamp - {e}")
    
    # 视频编辑系统索引
    try:
        op.create_index('idx_timelines_project_id', 'timelines', ['project_id'])
        print("✅ 创建索引: idx_timelines_project_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_timelines_project_id - {e}")
    
    try:
        op.create_index('idx_clips_timeline_id', 'clips', ['timeline_id'])
        print("✅ 创建索引: idx_clips_timeline_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_clips_timeline_id - {e}")
    
    try:
        op.create_index('idx_clips_order_index', 'clips', ['order_index'])
        print("✅ 创建索引: idx_clips_order_index")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_clips_order_index - {e}")
    
    try:
        op.create_index('idx_render_tasks_timeline_id', 'render_tasks', ['timeline_id'])
        print("✅ 创建索引: idx_render_tasks_timeline_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_render_tasks_timeline_id - {e}")
    
    try:
        op.create_index('idx_render_tasks_status', 'render_tasks', ['status'])
        print("✅ 创建索引: idx_render_tasks_status")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_render_tasks_status - {e}")
    
    # 图片处理系统索引
    try:
        op.create_index('idx_image_assets_project_id', 'image_assets', ['project_id'])
        print("✅ 创建索引: idx_image_assets_project_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_image_assets_project_id - {e}")
    
    try:
        op.create_index('idx_image_vectors_image_id', 'image_vectors', ['image_id'])
        print("✅ 创建索引: idx_image_vectors_image_id")
    except Exception as e:
        print(f"⚠️  索引已存在或创建失败: idx_image_vectors_image_id - {e}")
    
    # 复合索引 - 提升复杂查询性能
    try:
        op.create_index('idx_assets_project_status', 'assets', ['project_id', 'processing_status'])
        print("✅ 创建复合索引: idx_assets_project_status")
    except Exception as e:
        print(f"⚠️  复合索引已存在或创建失败: idx_assets_project_status - {e}")
    
    try:
        op.create_index('idx_beats_project_order', 'beats', ['project_id', 'order_index'])
        print("✅ 创建复合索引: idx_beats_project_order")
    except Exception as e:
        print(f"⚠️  复合索引已存在或创建失败: idx_beats_project_order - {e}")
    
    print(f"\n🎉 性能索引创建完成 - {datetime.now()}")

def downgrade():
    """删除性能索引"""
    
    # 删除所有创建的索引
    indexes_to_drop = [
        'idx_assets_project_id',
        'idx_assets_created_at', 
        'idx_assets_mime_type',
        'idx_assets_processing_status',
        'idx_asset_vectors_asset_id',
        'idx_asset_vectors_content_type',
        'idx_projects_created_at',
        'idx_projects_current_stage',
        'idx_beats_project_id',
        'idx_beats_order_index',
        'idx_asset_segments_asset_id',
        'idx_asset_segments_time_range',
        'idx_feedback_logs_asset_id',
        'idx_feedback_logs_timestamp',
        'idx_timelines_project_id',
        'idx_clips_timeline_id',
        'idx_clips_order_index',
        'idx_render_tasks_timeline_id',
        'idx_render_tasks_status',
        'idx_image_assets_project_id',
        'idx_image_vectors_image_id',
        'idx_assets_project_status',
        'idx_beats_project_order'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name)
            print(f"✅ 删除索引: {index_name}")
        except Exception as e:
            print(f"⚠️  索引删除失败: {index_name} - {e}")
    
    print(f"\n🗑️  性能索引删除完成 - {datetime.now()}")

if __name__ == "__main__":
    print("🚀 执行数据库性能索引优化...")
    upgrade()