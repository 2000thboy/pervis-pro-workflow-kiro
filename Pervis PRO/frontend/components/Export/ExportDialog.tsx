/**
 * 导出对话框组件
 * 统一的导出界面，支持 analysis、board、timeline 三种模式
 */

import React, { useState, useCallback } from 'react';
import {
    X,
    FileText,
    Image as ImageIcon,
    Video,
    Music,
    Layers,
    Download,
    Settings2,
    ChevronDown
} from 'lucide-react';
import {
    ExportDialogProps,
    ExportMode,
    ExportTask,
    DocumentExportOptions,
    BoardExportOptions,
    VideoExportOptions,
    AudioExportOptions,
    NLEExportOptions,
    DEFAULT_DOCUMENT_OPTIONS,
    DEFAULT_BOARD_OPTIONS,
    DEFAULT_VIDEO_OPTIONS,
    DEFAULT_AUDIO_OPTIONS,
    DEFAULT_NLE_OPTIONS,
    RESOLUTION_PRESETS,
    FRAMERATE_OPTIONS
} from './types';
import { ExportProgress } from './ExportProgress';
import { exportApi } from './api';

// Tab 类型
type TimelineTab = 'video' | 'audio' | 'nle';

export const ExportDialog: React.FC<ExportDialogProps> = ({
    isOpen,
    onClose,
    mode,
    projectId,
    timelineId,
    beats = [],
    scenes = []
}) => {
    // 状态
    const [documentOptions, setDocumentOptions] = useState<DocumentExportOptions>(DEFAULT_DOCUMENT_OPTIONS);
    const [boardOptions, setBoardOptions] = useState<BoardExportOptions>(DEFAULT_BOARD_OPTIONS);
    const [videoOptions, setVideoOptions] = useState<VideoExportOptions>(DEFAULT_VIDEO_OPTIONS);
    const [audioOptions, setAudioOptions] = useState<AudioExportOptions>(DEFAULT_AUDIO_OPTIONS);
    const [nleOptions, setNleOptions] = useState<NLEExportOptions>(DEFAULT_NLE_OPTIONS);
    const [timelineTab, setTimelineTab] = useState<TimelineTab>('video');
    const [currentTask, setCurrentTask] = useState<ExportTask | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // 开始导出
    const handleExport = useCallback(async () => {
        const taskId = `export-${Date.now()}`;
        const task: ExportTask = {
            id: taskId,
            type: mode === 'analysis' ? 'document' : mode === 'board' ? 'board' : timelineTab,
            status: 'preparing',
            progress: 0,
            message: '准备导出...',
            startTime: Date.now()
        };
        setCurrentTask(task);

        try {
            let result: any;

            if (mode === 'analysis') {
                // 文档导出
                setCurrentTask(prev => prev ? { ...prev, progress: 20, message: '生成文档...' } : null);
                result = await exportApi.exportDocument(projectId, documentOptions);
            } else if (mode === 'board') {
                // 故事板导出
                setCurrentTask(prev => prev ? { ...prev, progress: 20, message: '导出故事板...' } : null);
                result = await exportApi.exportBeatboard(projectId, boardOptions);
            } else if (mode === 'timeline') {
                if (timelineTab === 'video') {
                    // 视频导出
                    setCurrentTask(prev => prev ? { ...prev, progress: 10, message: '启动渲染任务...' } : null);
                    result = await exportApi.exportVideo(timelineId || projectId, videoOptions);
                    
                    // 轮询进度
                    if (result.task_id) {
                        await pollVideoProgress(result.task_id);
                        return;
                    }
                } else if (timelineTab === 'audio') {
                    // 音频导出
                    setCurrentTask(prev => prev ? { ...prev, progress: 20, message: '导出音频...' } : null);
                    result = await exportApi.exportAudio(timelineId || projectId, audioOptions);
                } else {
                    // NLE 导出
                    setCurrentTask(prev => prev ? { ...prev, progress: 20, message: '生成工程文件...' } : null);
                    result = await exportApi.exportNLE(projectId, nleOptions);
                }
            }

            // 完成
            setCurrentTask(prev => prev ? {
                ...prev,
                status: 'completed',
                progress: 100,
                message: '导出完成',
                endTime: Date.now(),
                downloadUrl: result?.file_path || result?.download_url
            } : null);

        } catch (error: any) {
            setCurrentTask(prev => prev ? {
                ...prev,
                status: 'error',
                progress: 0,
                message: '导出失败',
                endTime: Date.now(),
                error: error.message || '未知错误'
            } : null);
        }
    }, [mode, projectId, timelineId, timelineTab, documentOptions, boardOptions, videoOptions, audioOptions, nleOptions]);

    // 轮询视频导出进度
    const pollVideoProgress = async (taskId: string) => {
        const pollInterval = setInterval(async () => {
            try {
                const status = await exportApi.getVideoExportStatus(taskId);
                
                if (status.task) {
                    const { progress, status: taskStatus, message, output_path } = status.task;
                    
                    setCurrentTask(prev => prev ? {
                        ...prev,
                        progress: progress || prev.progress,
                        message: message || prev.message,
                        status: taskStatus === 'completed' ? 'completed' 
                            : taskStatus === 'failed' ? 'error' 
                            : taskStatus === 'cancelled' ? 'cancelled'
                            : 'exporting',
                        downloadUrl: output_path,
                        endTime: ['completed', 'failed', 'cancelled'].includes(taskStatus) ? Date.now() : undefined
                    } : null);

                    if (['completed', 'failed', 'cancelled'].includes(taskStatus)) {
                        clearInterval(pollInterval);
                    }
                }
            } catch (error) {
                clearInterval(pollInterval);
                setCurrentTask(prev => prev ? {
                    ...prev,
                    status: 'error',
                    message: '获取进度失败',
                    endTime: Date.now()
                } : null);
            }
        }, 1000);
    };

    // 取消导出
    const handleCancel = useCallback(async () => {
        if (currentTask && currentTask.type === 'video' && currentTask.status === 'exporting') {
            try {
                await exportApi.cancelVideoExport(currentTask.id);
            } catch (e) {
                console.error('Cancel failed', e);
            }
        }
        setCurrentTask(prev => prev ? { ...prev, status: 'cancelled', endTime: Date.now() } : null);
    }, [currentTask]);

    // 重试
    const handleRetry = useCallback(() => {
        setCurrentTask(null);
        handleExport();
    }, [handleExport]);

    // 下载
    const handleDownload = useCallback(async () => {
        if (currentTask?.downloadUrl) {
            // 如果是视频任务，使用专门的下载 API
            if (currentTask.type === 'video') {
                window.open(`http://localhost:8000/api/export/timeline/video/download/${currentTask.id}`, '_blank');
            } else {
                window.open(`http://localhost:8000/api/export/download/${currentTask.downloadUrl}`, '_blank');
            }
        }
    }, [currentTask]);

    if (!isOpen) return null;

    // 获取标题
    const getTitle = () => {
        switch (mode) {
            case 'analysis': return '导出项目文档';
            case 'board': return '导出故事板';
            case 'timeline': return '导出时间线';
            default: return '导出';
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="w-full max-w-lg bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl overflow-hidden">
                {/* 头部 */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Download size={20} className="text-yellow-500" />
                        {getTitle()}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-1.5 hover:bg-zinc-800 rounded-lg transition-colors"
                    >
                        <X size={18} className="text-zinc-400" />
                    </button>
                </div>

                {/* 内容 */}
                <div className="p-6 max-h-[60vh] overflow-y-auto">
                    {currentTask ? (
                        <ExportProgress
                            task={currentTask}
                            onCancel={handleCancel}
                            onRetry={handleRetry}
                            onDownload={handleDownload}
                        />
                    ) : (
                        <>
                            {/* Analysis 模式：文档导出选项 */}
                            {mode === 'analysis' && (
                                <DocumentExportForm
                                    options={documentOptions}
                                    onChange={setDocumentOptions}
                                    showAdvanced={showAdvanced}
                                    onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
                                />
                            )}

                            {/* Board 模式：故事板导出选项 */}
                            {mode === 'board' && (
                                <BoardExportForm
                                    options={boardOptions}
                                    onChange={setBoardOptions}
                                    beats={beats}
                                    scenes={scenes}
                                    showAdvanced={showAdvanced}
                                    onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
                                />
                            )}

                            {/* Timeline 模式：视频/音频/NLE 选项卡 */}
                            {mode === 'timeline' && (
                                <TimelineExportForm
                                    tab={timelineTab}
                                    onTabChange={setTimelineTab}
                                    videoOptions={videoOptions}
                                    onVideoChange={setVideoOptions}
                                    audioOptions={audioOptions}
                                    onAudioChange={setAudioOptions}
                                    nleOptions={nleOptions}
                                    onNleChange={setNleOptions}
                                    showAdvanced={showAdvanced}
                                    onToggleAdvanced={() => setShowAdvanced(!showAdvanced)}
                                />
                            )}
                        </>
                    )}
                </div>

                {/* 底部按钮 */}
                {!currentTask && (
                    <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-zinc-800 bg-zinc-900/50">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
                        >
                            取消
                        </button>
                        <button
                            onClick={handleExport}
                            className="flex items-center gap-2 px-5 py-2 bg-yellow-600 hover:bg-yellow-500 text-black text-sm font-bold rounded-lg transition-colors"
                        >
                            <Download size={16} />
                            开始导出
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};


// ============================================================
// 子表单组件
// ============================================================

// 文档导出表单
const DocumentExportForm: React.FC<{
    options: DocumentExportOptions;
    onChange: (options: DocumentExportOptions) => void;
    showAdvanced: boolean;
    onToggleAdvanced: () => void;
}> = ({ options, onChange, showAdvanced, onToggleAdvanced }) => {
    return (
        <div className="space-y-4">
            {/* 格式选择 */}
            <div>
                <label className="block text-xs font-medium text-zinc-400 mb-2">导出格式</label>
                <div className="grid grid-cols-3 gap-2">
                    {(['pdf', 'docx', 'md'] as const).map(format => (
                        <button
                            key={format}
                            onClick={() => onChange({ ...options, format })}
                            className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                                options.format === format
                                    ? 'border-yellow-500 bg-yellow-500/10 text-yellow-500'
                                    : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                            }`}
                        >
                            <FileText size={20} className="mx-auto mb-1" />
                            {format.toUpperCase()}
                        </button>
                    ))}
                </div>
            </div>

            {/* 内容选择 */}
            <div>
                <label className="block text-xs font-medium text-zinc-400 mb-2">包含内容</label>
                <div className="space-y-2">
                    <CheckboxOption
                        label="剧本内容"
                        checked={options.includeBeats}
                        onChange={v => onChange({ ...options, includeBeats: v })}
                    />
                    <CheckboxOption
                        label="角色信息"
                        checked={options.includeCharacters}
                        onChange={v => onChange({ ...options, includeCharacters: v })}
                    />
                    <CheckboxOption
                        label="场次信息"
                        checked={options.includeScenes}
                        onChange={v => onChange({ ...options, includeScenes: v })}
                    />
                    <CheckboxOption
                        label="标签和元数据"
                        checked={options.includeTags}
                        onChange={v => onChange({ ...options, includeTags: v })}
                    />
                    <CheckboxOption
                        label="AI 分析结果"
                        checked={options.includeAiAnalysis}
                        onChange={v => onChange({ ...options, includeAiAnalysis: v })}
                    />
                </div>
            </div>

            {/* 高级选项 */}
            <AdvancedToggle show={showAdvanced} onToggle={onToggleAdvanced} />
            {showAdvanced && (
                <div className="space-y-3 pt-2">
                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">文档模板</label>
                        <select
                            value={options.template}
                            onChange={e => onChange({ ...options, template: e.target.value as any })}
                            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                        >
                            <option value="professional">专业模板</option>
                            <option value="simple">简洁模板</option>
                            <option value="screenplay">剧本格式</option>
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
};

// 故事板导出表单
const BoardExportForm: React.FC<{
    options: BoardExportOptions;
    onChange: (options: BoardExportOptions) => void;
    beats: { id: string; title: string }[];
    scenes: { id: string; title: string }[];
    showAdvanced: boolean;
    onToggleAdvanced: () => void;
}> = ({ options, onChange, beats, scenes, showAdvanced, onToggleAdvanced }) => {
    return (
        <div className="space-y-4">
            {/* 格式选择 */}
            <div>
                <label className="block text-xs font-medium text-zinc-400 mb-2">图片格式</label>
                <div className="grid grid-cols-2 gap-2">
                    {(['png', 'jpg'] as const).map(format => (
                        <button
                            key={format}
                            onClick={() => onChange({ ...options, format })}
                            className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                                options.format === format
                                    ? 'border-yellow-500 bg-yellow-500/10 text-yellow-500'
                                    : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                            }`}
                        >
                            <ImageIcon size={20} className="mx-auto mb-1" />
                            {format.toUpperCase()}
                        </button>
                    ))}
                </div>
            </div>

            {/* 导出范围 */}
            <div>
                <label className="block text-xs font-medium text-zinc-400 mb-2">导出范围</label>
                <select
                    value={options.exportMode}
                    onChange={e => onChange({ ...options, exportMode: e.target.value as any })}
                    className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                >
                    <option value="all">全部镜头</option>
                    <option value="scene">按场次</option>
                    <option value="selected">选择镜头</option>
                </select>
            </div>

            {/* 分辨率 */}
            <div>
                <label className="block text-xs font-medium text-zinc-400 mb-2">分辨率</label>
                <div className="grid grid-cols-2 gap-2">
                    <input
                        type="number"
                        value={options.width}
                        onChange={e => onChange({ ...options, width: parseInt(e.target.value) || 1920 })}
                        className="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                        placeholder="宽度"
                    />
                    <input
                        type="number"
                        value={options.height}
                        onChange={e => onChange({ ...options, height: parseInt(e.target.value) || 1080 })}
                        className="px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                        placeholder="高度"
                    />
                </div>
            </div>

            {/* 选项 */}
            <div className="space-y-2">
                <CheckboxOption
                    label="包含镜头信息叠加"
                    checked={options.includeOverlay}
                    onChange={v => onChange({ ...options, includeOverlay: v })}
                />
                <CheckboxOption
                    label="生成联系表"
                    checked={options.includeContactSheet}
                    onChange={v => onChange({ ...options, includeContactSheet: v })}
                />
                <CheckboxOption
                    label="打包为 ZIP"
                    checked={options.createZip}
                    onChange={v => onChange({ ...options, createZip: v })}
                />
            </div>

            {/* 高级选项 */}
            <AdvancedToggle show={showAdvanced} onToggle={onToggleAdvanced} />
            {showAdvanced && (
                <div className="space-y-3 pt-2">
                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">图片质量 ({options.quality}%)</label>
                        <input
                            type="range"
                            min="50"
                            max="100"
                            value={options.quality}
                            onChange={e => onChange({ ...options, quality: parseInt(e.target.value) })}
                            className="w-full"
                        />
                    </div>
                    {options.includeContactSheet && (
                        <div>
                            <label className="block text-xs font-medium text-zinc-400 mb-2">联系表列数</label>
                            <input
                                type="number"
                                min="2"
                                max="8"
                                value={options.contactSheetColumns}
                                onChange={e => onChange({ ...options, contactSheetColumns: parseInt(e.target.value) || 4 })}
                                className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                            />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// 时间线导出表单
const TimelineExportForm: React.FC<{
    tab: TimelineTab;
    onTabChange: (tab: TimelineTab) => void;
    videoOptions: VideoExportOptions;
    onVideoChange: (options: VideoExportOptions) => void;
    audioOptions: AudioExportOptions;
    onAudioChange: (options: AudioExportOptions) => void;
    nleOptions: NLEExportOptions;
    onNleChange: (options: NLEExportOptions) => void;
    showAdvanced: boolean;
    onToggleAdvanced: () => void;
}> = ({ 
    tab, onTabChange, 
    videoOptions, onVideoChange, 
    audioOptions, onAudioChange, 
    nleOptions, onNleChange,
    showAdvanced, onToggleAdvanced 
}) => {
    return (
        <div className="space-y-4">
            {/* Tab 切换 */}
            <div className="flex border-b border-zinc-800">
                {[
                    { key: 'video', label: '视频', icon: Video },
                    { key: 'audio', label: '音频', icon: Music },
                    { key: 'nle', label: 'NLE工程', icon: Layers }
                ].map(({ key, label, icon: Icon }) => (
                    <button
                        key={key}
                        onClick={() => onTabChange(key as TimelineTab)}
                        className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                            tab === key
                                ? 'border-yellow-500 text-yellow-500'
                                : 'border-transparent text-zinc-500 hover:text-zinc-300'
                        }`}
                    >
                        <Icon size={16} />
                        {label}
                    </button>
                ))}
            </div>

            {/* 视频选项 */}
            {tab === 'video' && (
                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">视频格式</label>
                        <div className="grid grid-cols-3 gap-2">
                            {(['mp4', 'mov', 'webm'] as const).map(format => (
                                <button
                                    key={format}
                                    onClick={() => onVideoChange({ ...videoOptions, format })}
                                    className={`p-2 rounded-lg border text-xs font-medium transition-all ${
                                        videoOptions.format === format
                                            ? 'border-yellow-500 bg-yellow-500/10 text-yellow-500'
                                            : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                                    }`}
                                >
                                    {format.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">分辨率</label>
                        <div className="grid grid-cols-4 gap-2">
                            {(['720p', '1080p', '2k', '4k'] as const).map(res => (
                                <button
                                    key={res}
                                    onClick={() => onVideoChange({ ...videoOptions, resolution: res })}
                                    className={`p-2 rounded-lg border text-xs font-medium transition-all ${
                                        videoOptions.resolution === res
                                            ? 'border-yellow-500 bg-yellow-500/10 text-yellow-500'
                                            : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                                    }`}
                                >
                                    {res}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">帧率</label>
                        <select
                            value={videoOptions.framerate}
                            onChange={e => onVideoChange({ ...videoOptions, framerate: parseFloat(e.target.value) })}
                            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                        >
                            {FRAMERATE_OPTIONS.map(fps => (
                                <option key={fps} value={fps}>{fps} fps</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">质量</label>
                        <div className="grid grid-cols-4 gap-2">
                            {(['low', 'medium', 'high', 'ultra'] as const).map(q => (
                                <button
                                    key={q}
                                    onClick={() => onVideoChange({ ...videoOptions, quality: q })}
                                    className={`p-2 rounded-lg border text-xs font-medium transition-all ${
                                        videoOptions.quality === q
                                            ? 'border-yellow-500 bg-yellow-500/10 text-yellow-500'
                                            : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                                    }`}
                                >
                                    {q === 'low' ? '低' : q === 'medium' ? '中' : q === 'high' ? '高' : '极高'}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* 音频选项 */}
            {tab === 'audio' && (
                <div className="space-y-4">
                    <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg text-center">
                        <Music size={32} className="mx-auto mb-2 text-zinc-600" />
                        <p className="text-sm text-zinc-500">音频导出功能开发中</p>
                    </div>
                </div>
            )}

            {/* NLE 选项 */}
            {tab === 'nle' && (
                <div className="space-y-4">
                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">工程格式</label>
                        <div className="grid grid-cols-2 gap-2">
                            {(['fcpxml', 'edl'] as const).map(format => (
                                <button
                                    key={format}
                                    onClick={() => onNleChange({ ...nleOptions, format })}
                                    className={`p-3 rounded-lg border text-sm font-medium transition-all ${
                                        nleOptions.format === format
                                            ? 'border-yellow-500 bg-yellow-500/10 text-yellow-500'
                                            : 'border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700'
                                    }`}
                                >
                                    <Layers size={20} className="mx-auto mb-1" />
                                    {format === 'fcpxml' ? 'FCPXML' : 'EDL'}
                                    <div className="text-[10px] text-zinc-500 mt-1">
                                        {format === 'fcpxml' ? 'FCP/Premiere/Resolve' : 'CMX3600 通用'}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    <div>
                        <label className="block text-xs font-medium text-zinc-400 mb-2">帧率</label>
                        <select
                            value={nleOptions.frameRate}
                            onChange={e => onNleChange({ ...nleOptions, frameRate: e.target.value })}
                            className="w-full px-3 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-200 focus:border-yellow-500 focus:outline-none"
                        >
                            <option value="24">24 fps</option>
                            <option value="25">25 fps</option>
                            <option value="30">30 fps</option>
                        </select>
                    </div>
                </div>
            )}
        </div>
    );
};

// ============================================================
// 辅助组件
// ============================================================

const CheckboxOption: React.FC<{
    label: string;
    checked: boolean;
    onChange: (checked: boolean) => void;
}> = ({ label, checked, onChange }) => (
    <label className="flex items-center gap-2 cursor-pointer group">
        <input
            type="checkbox"
            checked={checked}
            onChange={e => onChange(e.target.checked)}
            className="w-4 h-4 rounded border-zinc-700 bg-zinc-900 text-yellow-500 focus:ring-yellow-500 focus:ring-offset-0"
        />
        <span className="text-sm text-zinc-400 group-hover:text-zinc-200 transition-colors">{label}</span>
    </label>
);

const AdvancedToggle: React.FC<{
    show: boolean;
    onToggle: () => void;
}> = ({ show, onToggle }) => (
    <button
        onClick={onToggle}
        className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
    >
        <Settings2 size={14} />
        <span>高级选项</span>
        <ChevronDown size={14} className={`transition-transform ${show ? 'rotate-180' : ''}`} />
    </button>
);

export default ExportDialog;
