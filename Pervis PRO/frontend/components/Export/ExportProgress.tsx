/**
 * 导出进度组件
 * 显示导出任务的进度、状态和操作按钮
 */

import React from 'react';
import { 
    Loader2, 
    CheckCircle, 
    XCircle, 
    Download, 
    RefreshCw, 
    X,
    Clock
} from 'lucide-react';
import { ExportProgressProps, ExportStatus } from './types';

// 格式化时间
const formatDuration = (ms: number): string => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
        return `${minutes}分${remainingSeconds}秒`;
    }
    return `${remainingSeconds}秒`;
};

// 状态图标
const StatusIcon: React.FC<{ status: ExportStatus }> = ({ status }) => {
    switch (status) {
        case 'preparing':
        case 'exporting':
            return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />;
        case 'completed':
            return <CheckCircle className="w-5 h-5 text-green-500" />;
        case 'error':
            return <XCircle className="w-5 h-5 text-red-500" />;
        case 'cancelled':
            return <X className="w-5 h-5 text-zinc-500" />;
        default:
            return <Clock className="w-5 h-5 text-zinc-500" />;
    }
};

// 状态文本
const getStatusText = (status: ExportStatus): string => {
    switch (status) {
        case 'idle': return '等待中';
        case 'preparing': return '准备中...';
        case 'exporting': return '导出中...';
        case 'completed': return '导出完成';
        case 'error': return '导出失败';
        case 'cancelled': return '已取消';
        default: return '未知状态';
    }
};

export const ExportProgress: React.FC<ExportProgressProps> = ({
    task,
    onCancel,
    onRetry,
    onDownload
}) => {
    const elapsed = task.endTime 
        ? task.endTime - task.startTime 
        : Date.now() - task.startTime;
    
    const isActive = task.status === 'preparing' || task.status === 'exporting';
    const canDownload = task.status === 'completed' && task.downloadUrl;
    const canRetry = task.status === 'error' || task.status === 'cancelled';
    const canCancel = isActive;

    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
            {/* 头部：状态和时间 */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <StatusIcon status={task.status} />
                    <span className="text-sm font-medium text-zinc-200">
                        {getStatusText(task.status)}
                    </span>
                </div>
                <div className="flex items-center gap-1 text-xs text-zinc-500">
                    <Clock size={12} />
                    <span>{formatDuration(elapsed)}</span>
                </div>
            </div>

            {/* 进度条 */}
            <div className="mb-3">
                <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                        className={`h-full transition-all duration-300 ${
                            task.status === 'completed' 
                                ? 'bg-green-500' 
                                : task.status === 'error' 
                                    ? 'bg-red-500' 
                                    : 'bg-yellow-500'
                        }`}
                        style={{ width: `${task.progress}%` }}
                    />
                </div>
                <div className="flex justify-between mt-1">
                    <span className="text-xs text-zinc-500">{task.message}</span>
                    <span className="text-xs text-zinc-400 font-mono">{task.progress}%</span>
                </div>
            </div>

            {/* 错误信息 */}
            {task.error && (
                <div className="mb-3 p-2 bg-red-950/30 border border-red-900/50 rounded text-xs text-red-400">
                    {task.error}
                </div>
            )}

            {/* 操作按钮 */}
            <div className="flex items-center gap-2">
                {canDownload && (
                    <button
                        onClick={onDownload}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white text-xs font-medium rounded transition-colors"
                    >
                        <Download size={14} />
                        下载文件
                    </button>
                )}
                
                {canRetry && (
                    <button
                        onClick={onRetry}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 text-xs font-medium rounded transition-colors"
                    >
                        <RefreshCw size={14} />
                        重试
                    </button>
                )}
                
                {canCancel && (
                    <button
                        onClick={onCancel}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-400 text-xs font-medium rounded transition-colors"
                    >
                        <X size={14} />
                        取消
                    </button>
                )}
            </div>
        </div>
    );
};

export default ExportProgress;
