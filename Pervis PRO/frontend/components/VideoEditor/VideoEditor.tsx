import React, { useState, useEffect } from 'react';
import { Film, Play, Download, Settings, Save, Undo, Redo, Plus } from 'lucide-react';
import TimelineEditor from './TimelineEditor';
import VideoPlayer from './VideoPlayer';
import RenderDialog from './RenderDialog';

interface VideoEditorProps {
  projectId: string;
}

interface Timeline {
  id: string;
  project_id: string;
  name: string;
  duration: number;
  clips: any[];
}

const VideoEditor: React.FC<VideoEditorProps> = ({ projectId }) => {
  const [timelines, setTimelines] = useState<Timeline[]>([]);
  const [activeTimelineId, setActiveTimelineId] = useState<string | null>(null);
  const [playhead, setPlayhead] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [showRenderDialog, setShowRenderDialog] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // 加载项目的时间轴列表
  useEffect(() => {
    loadTimelines();
  }, [projectId]);
  
  const loadTimelines = async () => {
    try {
      setIsLoading(true);
      // TODO: 实现获取项目时间轴列表的API
      // const response = await fetch(`/api/projects/${projectId}/timelines`);
      // if (response.ok) {
      //   const data = await response.json();
      //   setTimelines(data.timelines);
      //   if (data.timelines.length > 0) {
      //     setActiveTimelineId(data.timelines[0].id);
      //   }
      // }
      
      // 临时模拟数据
      const mockTimeline: Timeline = {
        id: 'timeline-1',
        project_id: projectId,
        name: '主时间轴',
        duration: 120,
        clips: []
      };
      
      setTimelines([mockTimeline]);
      setActiveTimelineId(mockTimeline.id);
    } catch (error) {
      console.error('Failed to load timelines:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 创建新时间轴
  const handleCreateTimeline = async () => {
    try {
      const response = await fetch('/api/timeline/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          project_id: projectId,
          name: `时间轴 ${timelines.length + 1}`
        })
      });
      
      if (response.ok) {
        const newTimeline = await response.json();
        setTimelines(prev => [...prev, newTimeline]);
        setActiveTimelineId(newTimeline.id);
      }
    } catch (error) {
      console.error('Failed to create timeline:', error);
    }
  };
  
  // 保存时间轴
  const handleSaveTimeline = async () => {
    // TODO: 实现保存逻辑
    console.log('Saving timeline...');
  };
  
  // 播放头变化处理
  const handlePlayheadChange = (time: number) => {
    setPlayhead(time);
  };
  
  // 播放状态变化处理
  const handlePlayStateChange = (playing: boolean) => {
    setIsPlaying(playing);
  };
  
  // 渲染完成处理
  const handleRenderComplete = (result: any) => {
    console.log('Render completed:', result);
    // TODO: 显示成功通知
  };
  
  const activeTimeline = timelines.find(t => t.id === activeTimelineId);
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-zinc-900 rounded-lg">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full mx-auto mb-2" />
          <div className="text-zinc-400">加载视频编辑器...</div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-full flex flex-col bg-zinc-950">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between p-4 bg-zinc-900 border-b border-zinc-700">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Film className="text-amber-400" size={20} />
            <h2 className="text-lg font-semibold text-white">视频编辑器</h2>
          </div>
          
          {/* 时间轴选择 */}
          {timelines.length > 0 && (
            <div className="flex items-center gap-2">
              <select
                value={activeTimelineId || ''}
                onChange={(e) => setActiveTimelineId(e.target.value)}
                className="bg-zinc-800 border border-zinc-600 rounded px-3 py-1 text-white text-sm focus:border-amber-500 focus:outline-none"
              >
                {timelines.map(timeline => (
                  <option key={timeline.id} value={timeline.id}>
                    {timeline.name}
                  </option>
                ))}
              </select>
              
              <button
                onClick={handleCreateTimeline}
                className="p-1 text-zinc-400 hover:text-amber-400 transition-colors"
                title="创建新时间轴"
              >
                <Plus size={16} />
              </button>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* 编辑操作 */}
          <button
            onClick={() => {/* TODO: 撤销 */}}
            className="p-2 text-zinc-400 hover:text-white transition-colors"
            title="撤销"
          >
            <Undo size={16} />
          </button>
          
          <button
            onClick={() => {/* TODO: 重做 */}}
            className="p-2 text-zinc-400 hover:text-white transition-colors"
            title="重做"
          >
            <Redo size={16} />
          </button>
          
          <div className="w-px h-6 bg-zinc-600 mx-2" />
          
          {/* 保存 */}
          <button
            onClick={handleSaveTimeline}
            className="flex items-center gap-2 px-3 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded transition-colors"
          >
            <Save size={16} />
            保存
          </button>
          
          {/* 渲染 */}
          <button
            onClick={() => setShowRenderDialog(true)}
            disabled={!activeTimelineId}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:bg-zinc-600 disabled:cursor-not-allowed text-white rounded transition-colors"
          >
            <Download size={16} />
            渲染视频
          </button>
        </div>
      </div>
      
      {/* 主编辑区域 */}
      <div className="flex-1 flex">
        {/* 左侧：视频预览 */}
        <div className="w-1/2 p-4">
          <div className="bg-zinc-900 rounded-lg h-full flex flex-col">
            <div className="p-4 border-b border-zinc-700">
              <h3 className="text-white font-medium">视频预览</h3>
            </div>
            
            <div className="flex-1 p-4">
              <VideoPlayer
                timelineId={activeTimelineId || undefined}
                playhead={playhead}
                isPlaying={isPlaying}
                onPlayheadChange={handlePlayheadChange}
                onPlayStateChange={handlePlayStateChange}
              />
            </div>
          </div>
        </div>
        
        {/* 右侧：素材库和属性面板 */}
        <div className="w-1/2 p-4 pl-0">
          <div className="bg-zinc-900 rounded-lg h-full flex flex-col">
            <div className="p-4 border-b border-zinc-700">
              <h3 className="text-white font-medium">素材库</h3>
            </div>
            
            <div className="flex-1 p-4">
              {/* TODO: 素材库组件 */}
              <div className="text-center text-zinc-400 py-8">
                <Film size={48} className="mx-auto mb-4 opacity-50" />
                <p>拖拽素材到时间轴开始编辑</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* 底部：时间轴编辑器 */}
      <div className="h-64 border-t border-zinc-700">
        {activeTimelineId ? (
          <TimelineEditor
            projectId={projectId}
            timelineId={activeTimelineId}
            onSave={handleSaveTimeline}
          />
        ) : (
          <div className="flex items-center justify-center h-full bg-zinc-900">
            <div className="text-center">
              <Film size={48} className="mx-auto mb-4 text-zinc-600" />
              <p className="text-zinc-400 mb-4">还没有时间轴</p>
              <button
                onClick={handleCreateTimeline}
                className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded transition-colors mx-auto"
              >
                <Plus size={16} />
                创建时间轴
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* 渲染对话框 */}
      {showRenderDialog && activeTimelineId && (
        <RenderDialog
          timelineId={activeTimelineId}
          timelineName={activeTimeline?.name || '未知时间轴'}
          isOpen={showRenderDialog}
          onClose={() => setShowRenderDialog(false)}
          onRenderComplete={handleRenderComplete}
        />
      )}
    </div>
  );
};

export default VideoEditor;