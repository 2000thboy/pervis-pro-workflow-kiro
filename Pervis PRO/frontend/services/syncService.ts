/**
 * 同步服务
 * 管理BeatBoard和时间轴编辑器之间的播放位置同步
 */

export interface SyncState {
  currentTime: number;
  isPlaying: boolean;
  duration: number;
  activeSource: 'beatboard' | 'timeline' | null;
}

export interface SyncListener {
  onTimeUpdate: (time: number, source: string) => void;
  onPlayStateChange: (isPlaying: boolean, source: string) => void;
  onDurationChange: (duration: number, source: string) => void;
}

class SyncService {
  private listeners: Map<string, SyncListener> = new Map();
  private state: SyncState = {
    currentTime: 0,
    isPlaying: false,
    duration: 0,
    activeSource: null
  };
  
  private syncEnabled: boolean = false;
  
  /**
   * 注册同步监听器
   */
  register(id: string, listener: SyncListener): void {
    this.listeners.set(id, listener);
    console.log(`[Sync] Registered listener: ${id}`);
  }
  
  /**
   * 注销同步监听器
   */
  unregister(id: string): void {
    this.listeners.delete(id);
    console.log(`[Sync] Unregistered listener: ${id}`);
  }
  
  /**
   * 启用/禁用同步
   */
  setSyncEnabled(enabled: boolean): void {
    this.syncEnabled = enabled;
    console.log(`[Sync] Sync ${enabled ? 'enabled' : 'disabled'}`);
    
    if (!enabled) {
      this.state.activeSource = null;
    }
  }
  
  /**
   * 获取同步状态
   */
  isSyncEnabled(): boolean {
    return this.syncEnabled;
  }
  
  /**
   * 获取当前状态
   */
  getState(): SyncState {
    return { ...this.state };
  }
  
  /**
   * 更新播放时间
   */
  updateTime(time: number, source: string): void {
    if (!this.syncEnabled) return;
    
    // 防止循环更新
    if (this.state.activeSource === source) {
      this.state.currentTime = time;
      
      // 通知其他监听器
      this.listeners.forEach((listener, id) => {
        if (id !== source) {
          try {
            listener.onTimeUpdate(time, source);
          } catch (error) {
            console.error(`[Sync] Error updating time for ${id}:`, error);
          }
        }
      });
    }
  }
  
  /**
   * 更新播放状态
   */
  updatePlayState(isPlaying: boolean, source: string): void {
    if (!this.syncEnabled) return;
    
    this.state.isPlaying = isPlaying;
    this.state.activeSource = isPlaying ? source as any : null;
    
    // 通知所有监听器
    this.listeners.forEach((listener, id) => {
      if (id !== source) {
        try {
          listener.onPlayStateChange(isPlaying, source);
        } catch (error) {
          console.error(`[Sync] Error updating play state for ${id}:`, error);
        }
      }
    });
    
    console.log(`[Sync] Play state: ${isPlaying ? 'playing' : 'paused'} from ${source}`);
  }
  
  /**
   * 更新总时长
   */
  updateDuration(duration: number, source: string): void {
    if (!this.syncEnabled) return;
    
    this.state.duration = Math.max(this.state.duration, duration);
    
    // 通知所有监听器
    this.listeners.forEach((listener, id) => {
      if (id !== source) {
        try {
          listener.onDurationChange(this.state.duration, source);
        } catch (error) {
          console.error(`[Sync] Error updating duration for ${id}:`, error);
        }
      }
    });
  }
  
  /**
   * 跳转到指定时间
   */
  seekTo(time: number, source: string): void {
    if (!this.syncEnabled) return;
    
    this.state.currentTime = time;
    this.state.activeSource = source as any;
    
    // 通知所有监听器
    this.listeners.forEach((listener, id) => {
      try {
        listener.onTimeUpdate(time, source);
      } catch (error) {
        console.error(`[Sync] Error seeking for ${id}:`, error);
      }
    });
    
    console.log(`[Sync] Seek to ${time.toFixed(2)}s from ${source}`);
  }
  
  /**
   * 暂停所有播放
   */
  pauseAll(source: string): void {
    if (!this.syncEnabled) return;
    
    this.updatePlayState(false, source);
  }
  
  /**
   * 重置同步状态
   */
  reset(): void {
    this.state = {
      currentTime: 0,
      isPlaying: false,
      duration: 0,
      activeSource: null
    };
    
    console.log('[Sync] State reset');
  }
  
  /**
   * 获取格式化的时间字符串
   */
  formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const frames = Math.floor((seconds % 1) * 30);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
  }
  
  /**
   * 计算Beat在时间轴上的位置
   */
  calculateBeatPosition(beatIndex: number, beats: any[]): number {
    let totalTime = 0;
    for (let i = 0; i < beatIndex && i < beats.length; i++) {
      totalTime += beats[i].duration || 0;
    }
    return totalTime;
  }
  
  /**
   * 根据时间查找对应的Beat
   */
  findBeatAtTime(time: number, beats: any[]): { index: number; beat: any; progress: number } | null {
    let currentTime = 0;
    
    for (let i = 0; i < beats.length; i++) {
      const beat = beats[i];
      const beatDuration = beat.duration || 0;
      
      if (time >= currentTime && time < currentTime + beatDuration) {
        const progress = beatDuration > 0 ? (time - currentTime) / beatDuration : 0;
        return { index: i, beat, progress };
      }
      
      currentTime += beatDuration;
    }
    
    return null;
  }
}

// 全局同步服务实例
export const syncService = new SyncService();

// React Hook for using sync service
export function useSyncService(id: string) {
  const [syncState, setSyncState] = React.useState<SyncState>(syncService.getState());
  const [isRegistered, setIsRegistered] = React.useState(false);
  
  React.useEffect(() => {
    const listener: SyncListener = {
      onTimeUpdate: (time: number, source: string) => {
        setSyncState(prev => ({ ...prev, currentTime: time }));
      },
      onPlayStateChange: (isPlaying: boolean, source: string) => {
        setSyncState(prev => ({ ...prev, isPlaying }));
      },
      onDurationChange: (duration: number, source: string) => {
        setSyncState(prev => ({ ...prev, duration }));
      }
    };
    
    syncService.register(id, listener);
    setIsRegistered(true);
    
    return () => {
      syncService.unregister(id);
      setIsRegistered(false);
    };
  }, [id]);
  
  const updateTime = React.useCallback((time: number) => {
    syncService.updateTime(time, id);
  }, [id]);
  
  const updatePlayState = React.useCallback((isPlaying: boolean) => {
    syncService.updatePlayState(isPlaying, id);
  }, [id]);
  
  const updateDuration = React.useCallback((duration: number) => {
    syncService.updateDuration(duration, id);
  }, [id]);
  
  const seekTo = React.useCallback((time: number) => {
    syncService.seekTo(time, id);
  }, [id]);
  
  return {
    syncState,
    isRegistered,
    isSyncEnabled: syncService.isSyncEnabled(),
    updateTime,
    updatePlayState,
    updateDuration,
    seekTo,
    setSyncEnabled: syncService.setSyncEnabled.bind(syncService),
    formatTime: syncService.formatTime.bind(syncService),
    calculateBeatPosition: syncService.calculateBeatPosition.bind(syncService),
    findBeatAtTime: syncService.findBeatAtTime.bind(syncService)
  };
}

export default syncService;