import React, { useState, useEffect } from 'react';
import { Link2, LinkOff, Play, Pause, RotateCcw, Clock, Zap } from 'lucide-react';
import { useSyncService } from '../../services/syncService';

interface SyncControlProps {
  className?: string;
}

const SyncControl: React.FC<SyncControlProps> = ({ className = '' }) => {
  const {
    syncState,
    isSyncEnabled,
    setSyncEnabled,
    seekTo,
    updatePlayState,
    formatTime
  } = useSyncService('sync-control');
  
  const [showDetails, setShowDetails] = useState(false);
  
  const handleSyncToggle = () => {
    setSyncEnabled(!isSyncEnabled);
  };
  
  const handlePlayPause = () => {
    updatePlayState(!syncState.isPlaying);
  };
  
  const handleReset = () => {
    seekTo(0);
    updatePlayState(false);
  };
  
  return (
    <div className={`bg-zinc-800 rounded-lg border border-zinc-700 ${className}`}>
      {/* 主控制栏 */}
      <div className="flex items-center justify-between p-3">
        <div className="flex items-center gap-3">
          {/* 同步开关 */}
          <button
            onClick={handleSyncToggle}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
              isSyncEnabled
                ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/20'
                : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
            }`}
            title={isSyncEnabled ? '禁用同步' : '启用同步'}
          >
            {isSyncEnabled ? (
              <>
                <Link2 size={16} />
                <span className="text-sm font-medium">同步已启用</span>
              </>
            ) : (
              <>
                <LinkOff size={16} />
                <span className="text-sm font-medium">同步已禁用</span>
              </>
            )}
          </button>
          
          {/* 同步状态指示器 */}
          {isSyncEnabled && (
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                syncState.activeSource ? 'bg-green-400 animate-pulse' : 'bg-zinc-500'
              }`} />
              <span className="text-xs text-zinc-400">
                {syncState.activeSource ? `${syncState.activeSource} 控制中` : '等待控制'}
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* 时间显示 */}
          <div className="flex items-center gap-2 text-sm font-mono text-zinc-300">
            <Clock size={14} />
            <span>{formatTime(syncState.currentTime)}</span>
            {syncState.duration > 0 && (
              <>
                <span className="text-zinc-500">/</span>
                <span>{formatTime(syncState.duration)}</span>
              </>
            )}
          </div>
          
          {/* 详情切换 */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1 text-zinc-400 hover:text-white transition-colors"
            title="显示详情"
          >
            <Zap size={14} />
          </button>
        </div>
      </div>
      
      {/* 播放控制 */}
      {isSyncEnabled && (
        <div className="flex items-center justify-center gap-2 px-3 pb-3">
          <button
            onClick={handleReset}
            className="p-2 text-zinc-400 hover:text-white transition-colors"
            title="重置到开始"
          >
            <RotateCcw size={16} />
          </button>
          
          <button
            onClick={handlePlayPause}
            className="flex items-center justify-center w-10 h-10 bg-amber-500 hover:bg-amber-600 text-white rounded-full transition-colors"
            title={syncState.isPlaying ? '暂停' : '播放'}
          >
            {syncState.isPlaying ? <Pause size={18} /> : <Play size={18} />}
          </button>
          
          {/* 进度条 */}
          {syncState.duration > 0 && (
            <div className="flex-1 mx-3">
              <div 
                className="h-2 bg-zinc-700 rounded-full cursor-pointer group"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const x = e.clientX - rect.left;
                  const percentage = x / rect.width;
                  const newTime = percentage * syncState.duration;
                  seekTo(newTime);
                }}
              >
                <div 
                  className="h-full bg-amber-500 rounded-full relative group-hover:bg-amber-400 transition-colors"
                  style={{ width: `${(syncState.currentTime / syncState.duration) * 100}%` }}
                >
                  <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* 详细信息 */}
      {showDetails && isSyncEnabled && (
        <div className="border-t border-zinc-700 p-3 bg-zinc-900/50">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-zinc-400 mb-1">当前状态</div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-zinc-300">播放状态:</span>
                  <span className={syncState.isPlaying ? 'text-green-400' : 'text-zinc-400'}>
                    {syncState.isPlaying ? '播放中' : '已暂停'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-300">控制源:</span>
                  <span className="text-amber-400">
                    {syncState.activeSource || '无'}
                  </span>
                </div>
              </div>
            </div>
            
            <div>
              <div className="text-zinc-400 mb-1">时间信息</div>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span className="text-zinc-300">当前时间:</span>
                  <span className="text-white font-mono">
                    {formatTime(syncState.currentTime)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-zinc-300">总时长:</span>
                  <span className="text-white font-mono">
                    {formatTime(syncState.duration)}
                  </span>
                </div>
                {syncState.duration > 0 && (
                  <div className="flex justify-between">
                    <span className="text-zinc-300">进度:</span>
                    <span className="text-amber-400">
                      {((syncState.currentTime / syncState.duration) * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* 快速跳转 */}
          <div className="mt-3 pt-3 border-t border-zinc-700">
            <div className="text-zinc-400 text-xs mb-2">快速跳转</div>
            <div className="flex gap-2">
              {[0, 0.25, 0.5, 0.75, 1].map(percentage => (
                <button
                  key={percentage}
                  onClick={() => seekTo(syncState.duration * percentage)}
                  className="px-2 py-1 text-xs bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded transition-colors"
                  disabled={syncState.duration === 0}
                >
                  {percentage === 0 ? '开始' : 
                   percentage === 1 ? '结束' : 
                   `${(percentage * 100)}%`}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SyncControl;