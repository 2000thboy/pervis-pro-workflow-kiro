# 视频编辑和输出系统 - 设计文档

## 概述

PreVis PRO视频编辑和输出系统是一个完整的非线性视频编辑解决方案，集成了时间轴编辑、实时预览、视频渲染和导出功能。系统使用FFmpeg作为核心视频处理引擎，提供专业级的视频编辑能力。

## 架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                 │
├─────────────────────────────────────────────────────────────┤
│  TimelineEditor  │  VideoPlayer  │  RenderDialog  │  Controls│
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                        API层                                  │
├─────────────────────────────────────────────────────────────┤
│  /api/timeline/*  │  /api/render/*  │  /api/preview/*       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        服务层                                 │
├─────────────────────────────────────────────────────────────┤
│  TimelineService  │  RenderService  │  ProxyService         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                        处理层                                 │
├─────────────────────────────────────────────────────────────┤
│  FFmpegWrapper  │  VideoProcessor  │  AudioProcessor        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      存储和队列                               │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  Celery  │  File Storage          │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈

**后端**:
- **FFmpeg**: 视频处理核心引擎
- **ffmpeg-python**: Python FFmpeg绑定
- **Celery**: 异步任务队列（渲染任务）
- **Redis**: 任务状态和缓存
- **PostgreSQL**: 项目和时间轴数据存储

**前端**:
- **React**: UI框架
- **Wavesurfer.js**: 音频波形显示
- **Video.js**: 视频播放器
- **React DnD**: 拖拽功能
- **Fabric.js**: 时间轴画布渲染

## 组件和接口

### 1. TimelineService (后端)

时间轴管理服务，处理Clip的CRUD操作。

```python
class TimelineService:
    def create_timeline(self, project_id: str) -> Timeline:
        """创建新的时间轴"""
        
    def add_clip(self, timeline_id: str, clip_data: ClipData) -> Clip:
        """添加视频片段到时间轴"""
        
    def update_clip(self, clip_id: str, updates: dict) -> Clip:
        """更新片段属性（位置、时长、音量等）"""
        
    def delete_clip(self, clip_id: str) -> bool:
        """删除片段"""
        
    def get_timeline(self, timeline_id: str) -> Timeline:
        """获取完整的时间轴数据"""
        
    def reorder_clips(self, timeline_id: str, clip_order: List[str]) -> bool:
        """重新排序片段"""
```

### 2. RenderService (后端)

视频渲染服务，使用Celery异步处理渲染任务。

```python
class RenderService:
    def start_render(self, timeline_id: str, options: RenderOptions) -> str:
        """启动渲染任务，返回task_id"""
        
    def get_render_status(self, task_id: str) -> RenderStatus:
        """获取渲染进度和状态"""
        
    def cancel_render(self, task_id: str) -> bool:
        """取消渲染任务"""
        
    def get_render_result(self, task_id: str) -> RenderResult:
        """获取渲染结果（文件路径、大小等）"""
        
    async def _render_video(self, timeline: Timeline, options: RenderOptions):
        """实际的渲染逻辑（Celery任务）"""
```

### 3. ProxyService (后端)

代理文件生成服务，为大型视频创建低分辨率副本。

```python
class ProxyService:
    def generate_proxy(self, asset_id: str) -> str:
        """生成代理文件，返回代理文件路径"""
        
    def get_proxy_path(self, asset_id: str) -> Optional[str]:
        """获取已存在的代理文件路径"""
        
    def delete_proxy(self, asset_id: str) -> bool:
        """删除代理文件"""
```

### 4. FFmpegWrapper (后端)

FFmpeg命令封装，提供常用的视频处理操作。

```python
class FFmpegWrapper:
    def trim_video(self, input_path: str, start: float, end: float, output_path: str):
        """剪切视频片段"""
        
    def concat_videos(self, video_paths: List[str], output_path: str):
        """拼接多个视频"""
        
    def add_transition(self, video1: str, video2: str, transition_type: str, duration: float, output: str):
        """添加转场效果"""
        
    def adjust_audio(self, input_path: str, volume: float, output_path: str):
        """调整音频音量"""
        
    def generate_thumbnail(self, input_path: str, timestamp: float, output_path: str):
        """生成视频缩略图"""
        
    def get_video_info(self, input_path: str) -> VideoInfo:
        """获取视频信息（时长、分辨率、编码等）"""
```

### 5. TimelineEditor (前端)

时间轴编辑器React组件。

```typescript
interface TimelineEditorProps {
    projectId: string;
    onSave?: (timeline: Timeline) => void;
}

const TimelineEditor: React.FC<TimelineEditorProps> = ({ projectId, onSave }) => {
    // 状态管理
    const [timeline, setTimeline] = useState<Timeline | null>(null);
    const [selectedClips, setSelectedClips] = useState<string[]>([]);
    const [playhead, setPlayhead] = useState<number>(0);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    
    // 核心功能
    const handleAddClip = (assetId: string, position: number) => {};
    const handleMoveClip = (clipId: string, newPosition: number) => {};
    const handleTrimClip = (clipId: string, start: number, end: number) => {};
    const handleDeleteClip = (clipId: string) => {};
    
    return (
        <div className="timeline-editor">
            <VideoPreview playhead={playhead} timeline={timeline} />
            <TimelineTrack clips={timeline?.clips} onClipUpdate={handleMoveClip} />
            <PlaybackControls onPlay={handlePlay} onPause={handlePause} />
        </div>
    );
};
```

### 6. RenderDialog (前端)

渲染设置对话框组件。

```typescript
interface RenderDialogProps {
    timelineId: string;
    onClose: () => void;
    onRenderComplete: (result: RenderResult) => void;
}

const RenderDialog: React.FC<RenderDialogProps> = ({ timelineId, onClose, onRenderComplete }) => {
    const [options, setOptions] = useState<RenderOptions>({
        format: 'mp4',
        resolution: '1080p',
        framerate: 30,
        quality: 'high'
    });
    
    const [renderProgress, setRenderProgress] = useState<number>(0);
    const [isRendering, setIsRendering] = useState<boolean>(false);
    
    const handleStartRender = async () => {
        const taskId = await startRender(timelineId, options);
        pollRenderStatus(taskId);
    };
    
    return (
        <Dialog>
            <RenderSettings options={options} onChange={setOptions} />
            {isRendering && <ProgressBar progress={renderProgress} />}
            <Button onClick={handleStartRender}>开始渲染</Button>
        </Dialog>
    );
};
```

## 数据模型

### Timeline (时间轴)

```python
class Timeline(Base):
    __tablename__ = "timelines"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String)
    duration = Column(Float)  # 总时长（秒）
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    clips = relationship("Clip", back_populates="timeline")
```

### Clip (片段)

```python
class Clip(Base):
    __tablename__ = "clips"
    
    id = Column(String, primary_key=True)
    timeline_id = Column(String, ForeignKey("timelines.id"))
    asset_id = Column(String, ForeignKey("assets.id"))
    
    # 时间属性
    start_time = Column(Float)  # 在时间轴上的开始时间
    end_time = Column(Float)    # 在时间轴上的结束时间
    trim_start = Column(Float)  # 素材的入点
    trim_end = Column(Float)    # 素材的出点
    
    # 音频属性
    volume = Column(Float, default=1.0)  # 音量（0-2）
    is_muted = Column(Boolean, default=False)
    audio_fade_in = Column(Float, default=0.0)
    audio_fade_out = Column(Float, default=0.0)
    
    # 转场属性
    transition_type = Column(String, nullable=True)  # fade, cut, wipe
    transition_duration = Column(Float, default=0.0)
    
    # 顺序
    order = Column(Integer)
    
    timeline = relationship("Timeline", back_populates="clips")
    asset = relationship("Asset")
```

### RenderTask (渲染任务)

```python
class RenderTask(Base):
    __tablename__ = "render_tasks"
    
    id = Column(String, primary_key=True)
    timeline_id = Column(String, ForeignKey("timelines.id"))
    
    # 渲染选项
    format = Column(String)  # mp4, mov
    resolution = Column(String)  # 720p, 1080p, 4k
    framerate = Column(Integer)  # 24, 30, 60
    quality = Column(String)  # low, medium, high
    bitrate = Column(Integer, nullable=True)
    
    # 状态
    status = Column(String)  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # 结果
    output_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # 时间
    created_at = Column(DateTime)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

### ProxyFile (代理文件)

```python
class ProxyFile(Base):
    __tablename__ = "proxy_files"
    
    id = Column(String, primary_key=True)
    asset_id = Column(String, ForeignKey("assets.id"))
    proxy_path = Column(String)
    resolution = Column(String)  # 480p
    file_size = Column(Integer)
    created_at = Column(DateTime)
```

## 错误处理

### 渲染错误

```python
class RenderError(Exception):
    """渲染过程中的错误"""
    pass

class InsufficientDiskSpaceError(RenderError):
    """磁盘空间不足"""
    pass

class MissingAssetError(RenderError):
    """素材文件缺失"""
    pass

class FFmpegError(RenderError):
    """FFmpeg执行错误"""
    pass
```

### 错误处理策略

1. **渲染前检查**: 验证所有素材文件存在、磁盘空间充足
2. **进度保存**: 渲染过程中定期保存进度，支持断点续传
3. **错误日志**: 详细记录FFmpeg输出和错误信息
4. **自动重试**: 对于临时性错误（网络、IO），自动重试3次
5. **用户通知**: 通过WebSocket实时通知用户渲染状态和错误

## 测试策略

### 单元测试

- TimelineService的CRUD操作
- FFmpegWrapper的视频处理功能
- RenderService的任务管理

### 集成测试

- 完整的视频编辑流程（添加→编辑→渲染）
- 多种格式和分辨率的渲染
- 转场效果的正确性

### 性能测试

- 大型项目（100+片段）的加载和编辑性能
- 4K视频的渲染速度
- 代理文件的生成速度

### 端到端测试

- 从BeatBoard到最终视频的完整工作流
- 不同浏览器的兼容性
- 并发渲染任务的处理

## 性能优化

### 1. 代理文件策略

- 自动为大于100MB的视频生成480p代理
- 编辑时使用代理，渲染时使用原始文件
- 后台异步生成，不阻塞用户操作

### 2. 时间轴渲染优化

- 使用Canvas进行时间轴绘制，而非DOM元素
- 虚拟滚动，只渲染可见区域的Clip
- 防抖处理拖拽和调整操作

### 3. 渲染优化

- 使用FFmpeg硬件加速（NVENC, VideoToolbox）
- 多线程并行处理（如果硬件支持）
- 智能缓存中间结果

### 4. 内存管理

- 限制同时加载的视频数量
- 自动清理未使用的缓存
- 使用流式处理大文件

## 部署考虑

### 存储需求

- 原始素材: 用户上传，大小不限
- 代理文件: 约为原始文件的10-20%
- 渲染输出: 根据设置，通常为原始文件的50-100%
- 建议: 至少500GB可用空间

### 计算资源

- CPU: 多核处理器（推荐8核以上）
- GPU: 支持硬件加速（NVIDIA/AMD）
- RAM: 至少16GB（推荐32GB）
- 并发渲染: 根据硬件限制，建议2-4个任务

### 扩展性

- 使用Celery分布式任务队列
- 支持多个Worker节点
- 可配置的渲染优先级
- 负载均衡和任务调度

## 安全考虑

1. **文件访问控制**: 只允许访问用户自己的项目文件
2. **资源限制**: 限制单个渲染任务的最大时长和文件大小
3. **输入验证**: 验证所有用户输入的参数
4. **临时文件清理**: 定期清理过期的临时文件和缓存
5. **错误信息**: 不暴露系统路径和敏感信息

## 未来扩展

1. **高级效果**: 色彩校正、滤镜、特效
2. **多轨道**: 支持多个视频和音频轨道
3. **协作编辑**: 多用户实时协作
4. **云渲染**: 使用云服务加速渲染
5. **AI辅助**: 自动剪辑、智能转场建议
