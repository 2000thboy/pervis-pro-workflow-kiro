
import React from 'react';
import { MonitorPlay } from 'lucide-react';

interface LayoutProps {
  leftPanel: React.ReactNode;   // Zone A: Script
  centerPanel: React.ReactNode; // Zone B: Visual Board
  rightPanel: React.ReactNode;  // Zone C: Inspector & Preview
  bottomPanel: React.ReactNode; // Zone D: Timeline
}

export const Layout: React.FC<LayoutProps> = ({ 
  leftPanel, 
  centerPanel, 
  rightPanel, 
  bottomPanel,
}) => {
  return (
    <div className="flex-1 flex flex-col w-full h-full overflow-hidden relative animate-in fade-in duration-500">
      
      {/* Main Workspace (Zones A, B, C) */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Zone A: Narrative Context (Script) */}
        <aside className="w-[20%] min-w-[280px] border-r border-zinc-800 bg-zinc-900/20 flex flex-col backdrop-blur-sm">
            <div className="h-8 flex items-center px-3 border-b border-zinc-800/50">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
                    剧本 & 大纲
                </span>
            </div>
            <div className="flex-1 overflow-hidden relative">
                {leftPanel}
            </div>
        </aside>

        {/* Zone B: Visual Ideation (Board) */}
        <main className="flex-1 bg-zinc-950 flex flex-col relative overflow-hidden">
            {centerPanel}
        </main>

        {/* Zone C: Inspection & Preview */}
        <aside className="w-[30%] min-w-[320px] max-w-[450px] border-l border-zinc-800 bg-zinc-900 flex flex-col z-10 shadow-xl shadow-black/50">
            <div className="h-8 flex items-center justify-between px-3 border-b border-zinc-800 bg-zinc-900">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                    监视器 & 属性
                </span>
                <MonitorPlay size={12} className="text-zinc-600" />
            </div>
            {rightPanel}
        </aside>
      </div>

      {/* Zone D: Temporal Flow (Timeline) */}
      <div className="h-[280px] border-t border-zinc-800 bg-zinc-900 flex flex-col flex-shrink-0 relative z-30">
        {bottomPanel}
      </div>
    </div>
  );
};
