
import React, { useState, useEffect } from 'react';
import { X, Activity, Server, Database, Terminal } from 'lucide-react';

interface AdminConsoleProps {
  onClose: () => void;
}

export const AdminConsole: React.FC<AdminConsoleProps> = ({ onClose }) => {
  // Simulate realtime data
  const [cpuUsage, setCpuUsage] = useState(35);
  const [memoryUsage, setMemoryUsage] = useState(42);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
        setCpuUsage(prev => Math.min(100, Math.max(10, prev + (Math.random() * 10 - 5))));
        setMemoryUsage(prev => Math.min(100, Math.max(20, prev + (Math.random() * 5 - 2))));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-[800px] bg-zinc-950 border border-zinc-800 rounded-lg shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="h-10 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-4">
            <div className="flex items-center gap-2 text-yellow-500 font-mono text-xs font-bold uppercase tracking-widest">
                <Terminal size={14} />
                System Admin Console
            </div>
            <button onClick={onClose} className="text-zinc-500 hover:text-white">
                <X size={16} />
            </button>
        </div>

        {/* Body */}
        <div className="p-6 grid grid-cols-3 gap-6">
            
            {/* Column 1: Metrics */}
            <div className="col-span-1 space-y-6">
                <div className="bg-zinc-900/50 p-4 rounded border border-zinc-800">
                    <h3 className="text-xs font-bold text-zinc-500 uppercase mb-4 flex items-center gap-2">
                        <Activity size={12}/> 实时资源监控
                    </h3>
                    
                    <div className="space-y-4">
                        <div className="space-y-1">
                            <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                                <span>CPU Core 0-7</span>
                                <span>{cpuUsage.toFixed(1)}%</span>
                            </div>
                            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                <div className="h-full bg-yellow-500 transition-all duration-500" style={{ width: `${cpuUsage}%` }}></div>
                            </div>
                        </div>

                        <div className="space-y-1">
                            <div className="flex justify-between text-[10px] font-mono text-zinc-400">
                                <span>Memory (VRAM)</span>
                                <span>{memoryUsage.toFixed(1)}%</span>
                            </div>
                            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${memoryUsage}%` }}></div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mt-6">
                        <div className="bg-black p-2 rounded text-center border border-zinc-800">
                            <div className="text-[10px] text-zinc-500">Ping</div>
                            <div className="text-green-500 font-mono text-sm font-bold">26ms</div>
                        </div>
                        <div className="bg-black p-2 rounded text-center border border-zinc-800">
                            <div className="text-[10px] text-zinc-500">Uptime</div>
                            <div className="text-zinc-300 font-mono text-sm font-bold">12h 4m</div>
                        </div>
                    </div>
                </div>

                <div className="bg-zinc-900/50 p-4 rounded border border-zinc-800">
                     <h3 className="text-xs font-bold text-zinc-500 uppercase mb-4 flex items-center gap-2">
                        <Database size={12}/> 数据管理
                    </h3>
                    <button className="w-full py-2 bg-red-900/20 text-red-400 border border-red-900/50 hover:bg-red-900/40 rounded text-xs transition-colors flex items-center justify-center gap-2">
                        <X size={12} /> 清空系统日志
                    </button>
                    <div className="text-[10px] text-zinc-600 text-center mt-2">LocalStorage 使用量: 0.00 KB</div>
                </div>
            </div>

            {/* Column 2: Logs (Terminal) */}
            <div className="col-span-2 bg-black border border-zinc-800 rounded p-4 font-mono text-[10px] text-zinc-400 overflow-y-auto h-[400px]">
                <div className="text-zinc-600 border-b border-zinc-800 pb-2 mb-2">SYSTEM LOGS</div>
                <div className="space-y-1">
                    {logs.length === 0 && <span className="opacity-30">暂无日志数据</span>}
                    {/* Placeholder for logs */}
                </div>
            </div>

        </div>
      </div>
    </div>
  );
};
