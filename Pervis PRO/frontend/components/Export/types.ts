/**
 * 导出系统类型定义
 */

// 导出模式
export type ExportMode = 'analysis' | 'board' | 'timeline';

// 文档导出格式
export type DocumentFormat = 'pdf' | 'docx' | 'md';

// 图片导出格式
export type ImageFormat = 'png' | 'jpg';

// 视频导出格式
export type VideoFormat = 'mp4' | 'mov' | 'webm';

// 音频导出格式
export type AudioFormat = 'wav' | 'mp3';

// NLE 导出格式
export type NLEFormat = 'fcpxml' | 'edl';

// 视频分辨率
export type VideoResolution = '720p' | '1080p' | '2k' | '4k';

// 视频质量
export type VideoQuality = 'low' | 'medium' | 'high' | 'ultra';

// 导出状态
export type ExportStatus = 'idle' | 'preparing' | 'exporting' | 'completed' | 'error' | 'cancelled';

// 文档导出选项
export interface DocumentExportOptions {
    format: DocumentFormat;
    includeBeats: boolean;
    includeTags: boolean;
    includeMetadata: boolean;
    includeCharacters: boolean;
    includeScenes: boolean;
    includeAiAnalysis: boolean;
    template: 'professional' | 'simple' | 'screenplay';
}

// 故事板导出选项
export interface BoardExportOptions {
    format: ImageFormat;
    width: number;
    height: number;
    quality: number;
    exportMode: 'all' | 'scene' | 'selected';
    selectedBeatIds?: string[];
    selectedSceneId?: string;
    includeContactSheet: boolean;
    contactSheetColumns: number;
    includeOverlay: boolean;
    createZip: boolean;
}

// 视频导出选项
export interface VideoExportOptions {
    format: VideoFormat;
    resolution: VideoResolution;
    framerate: number;
    quality: VideoQuality;
    bitrate?: number;
    audioBitrate: number;
}

// 音频导出选项
export interface AudioExportOptions {
    format: AudioFormat;
    sampleRate: number;
    bitrate: number;
}

// NLE 导出选项
export interface NLEExportOptions {
    format: NLEFormat;
    frameRate: string;
}

// 导出任务
export interface ExportTask {
    id: string;
    type: 'document' | 'board' | 'video' | 'audio' | 'nle';
    status: ExportStatus;
    progress: number;
    message: string;
    startTime: number;
    endTime?: number;
    downloadUrl?: string;
    error?: string;
}

// 导出历史记录
export interface ExportHistoryItem {
    id: string;
    exportType: string;
    fileFormat: string;
    fileSize: number;
    status: string;
    createdAt: string;
}

// 导出对话框 Props
export interface ExportDialogProps {
    isOpen: boolean;
    onClose: () => void;
    mode: ExportMode;
    projectId: string;
    timelineId?: string;
    beats?: { id: string; title: string }[];
    scenes?: { id: string; title: string }[];
}

// 导出进度 Props
export interface ExportProgressProps {
    task: ExportTask;
    onCancel: () => void;
    onRetry: () => void;
    onDownload: () => void;
}

// 预设分辨率
export const RESOLUTION_PRESETS: Record<VideoResolution, { width: number; height: number }> = {
    '720p': { width: 1280, height: 720 },
    '1080p': { width: 1920, height: 1080 },
    '2k': { width: 2560, height: 1440 },
    '4k': { width: 3840, height: 2160 }
};

// 帧率选项
export const FRAMERATE_OPTIONS = [23.976, 24, 25, 29.97, 30, 50, 60];

// 默认导出选项
export const DEFAULT_DOCUMENT_OPTIONS: DocumentExportOptions = {
    format: 'pdf',
    includeBeats: true,
    includeTags: true,
    includeMetadata: true,
    includeCharacters: true,
    includeScenes: true,
    includeAiAnalysis: false,
    template: 'professional'
};

export const DEFAULT_BOARD_OPTIONS: BoardExportOptions = {
    format: 'png',
    width: 1920,
    height: 1080,
    quality: 95,
    exportMode: 'all',
    includeContactSheet: false,
    contactSheetColumns: 4,
    includeOverlay: true,
    createZip: true
};

export const DEFAULT_VIDEO_OPTIONS: VideoExportOptions = {
    format: 'mp4',
    resolution: '1080p',
    framerate: 30,
    quality: 'high',
    audioBitrate: 192
};

export const DEFAULT_AUDIO_OPTIONS: AudioExportOptions = {
    format: 'mp3',
    sampleRate: 44100,
    bitrate: 192
};

export const DEFAULT_NLE_OPTIONS: NLEExportOptions = {
    format: 'fcpxml',
    frameRate: '24'
};
