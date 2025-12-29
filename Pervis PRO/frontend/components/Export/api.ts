/**
 * 导出 API 服务
 * 封装所有导出相关的后端 API 调用
 */

import {
    DocumentExportOptions,
    BoardExportOptions,
    VideoExportOptions,
    AudioExportOptions,
    NLEExportOptions,
    ExportHistoryItem
} from './types';

const API_BASE = 'http://127.0.0.1:8000/api/export';

// 通用请求函数
async function request<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers
        }
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || error.message || '请求失败');
    }

    return response.json();
}

export const exportApi = {
    /**
     * 导出项目文档 (PDF/DOCX/MD)
     */
    async exportDocument(projectId: string, options: DocumentExportOptions) {
        return request<{
            status: string;
            export_id: string;
            file_path: string;
            message: string;
        }>(`${API_BASE}/script`, {
            method: 'POST',
            body: JSON.stringify({
                project_id: projectId,
                format: options.format,
                include_beats: options.includeBeats,
                include_tags: options.includeTags,
                include_metadata: options.includeMetadata,
                template: options.template
            })
        });
    },

    /**
     * 导出故事板图片
     */
    async exportBeatboard(projectId: string, options: BoardExportOptions) {
        return request<{
            status: string;
            export_id: string;
            file_path: string;
            message: string;
        }>(`${API_BASE}/beatboard`, {
            method: 'POST',
            body: JSON.stringify({
                project_id: projectId,
                format: options.format,
                width: options.width,
                height: options.height,
                quality: options.quality,
                beat_ids: options.selectedBeatIds
            })
        });
    },

    /**
     * 导出时间线视频
     */
    async exportVideo(timelineId: string, options: VideoExportOptions) {
        return request<{
            status: string;
            task_id: string;
            message: string;
            estimated_duration?: number;
            estimated_size_mb?: number;
        }>(`${API_BASE}/timeline/video`, {
            method: 'POST',
            body: JSON.stringify({
                timeline_id: timelineId,
                format: options.format,
                resolution: options.resolution,
                framerate: options.framerate,
                quality: options.quality,
                bitrate: options.bitrate,
                audio_bitrate: options.audioBitrate
            })
        });
    },

    /**
     * 获取视频导出状态
     */
    async getVideoExportStatus(taskId: string) {
        return request<{
            status: string;
            task: {
                id: string;
                status: string;
                progress: number;
                message: string;
                output_path?: string;
                error?: string;
            };
        }>(`${API_BASE}/timeline/video/status/${taskId}`);
    },

    /**
     * 取消视频导出
     */
    async cancelVideoExport(taskId: string) {
        return request<{
            status: string;
            message: string;
        }>(`${API_BASE}/timeline/video/cancel/${taskId}`, {
            method: 'POST'
        });
    },

    /**
     * 下载视频导出文件
     */
    getVideoDownloadUrl(taskId: string): string {
        return `${API_BASE}/timeline/video/download/${taskId}`;
    },

    /**
     * 导出时间线音频
     */
    async exportAudio(timelineId: string, options: AudioExportOptions) {
        return request<{
            status: string;
            message: string;
        }>(`${API_BASE}/timeline/audio`, {
            method: 'POST',
            body: JSON.stringify({
                timeline_id: timelineId,
                format: options.format,
                sample_rate: options.sampleRate,
                bitrate: options.bitrate
            })
        });
    },

    /**
     * 导出 NLE 工程文件
     */
    async exportNLE(projectId: string, options: NLEExportOptions) {
        return request<{
            status: string;
            export_id: string;
            file_path: string;
            message: string;
        }>(`${API_BASE}/nle`, {
            method: 'POST',
            body: JSON.stringify({
                project_id: projectId,
                format: options.format,
                frame_rate: options.frameRate
            })
        });
    },

    /**
     * 获取导出历史
     */
    async getExportHistory(projectId: string) {
        return request<{
            status: string;
            project_id: string;
            history: ExportHistoryItem[];
        }>(`${API_BASE}/history/${projectId}`);
    },

    /**
     * 下载导出文件
     */
    getDownloadUrl(exportId: string): string {
        return `${API_BASE}/download/${exportId}`;
    },

    /**
     * 列出视频导出任务
     */
    async listVideoTasks(limit: number = 50) {
        return request<{
            status: string;
            tasks: any[];
            total: number;
        }>(`${API_BASE}/timeline/video/tasks?limit=${limit}`);
    }
};

export default exportApi;
