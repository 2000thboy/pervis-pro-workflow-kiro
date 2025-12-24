
import React from 'react';
import { SceneGroup } from '../types';
import { FileText, MapPin } from 'lucide-react';

interface ScriptPanelProps {
  scriptText: string;
  scenes: SceneGroup[];
  currentTime: number;
  onJumpToTime: (time: number) => void;
}

export const ScriptPanel: React.FC<ScriptPanelProps> = ({ 
  scriptText, 
  scenes, 
  currentTime,
  onJumpToTime
}) => {
  // Determine active scene based on current time
  const activeSceneId = scenes.find(
    s => currentTime >= s.startTime && currentTime < s.startTime + s.duration
  )?.id;

  return (
    <div className="flex flex-col h-full">
      {/* Tab/Toggle Header (Simplified for now) */}
      <div className="flex border-b border-zinc-800">
        <button className="flex-1 py-2 text-xs font-medium text-zinc-300 border-b-2 border-indigo-500 bg-zinc-800/50">
            大纲模式
        </button>
        <button className="flex-1 py-2 text-xs font-medium text-zinc-500 hover:text-zinc-300">
            原始剧本
        </button>
      </div>

      {/* Outline View */}
      <div className="flex-1 overflow-y-auto p-0 scrollbar-thin scrollbar-thumb-zinc-800">
         {scenes.map((scene, idx) => {
             const isActive = scene.id === activeSceneId;
             return (
                 <div 
                    key={scene.id}
                    onClick={() => onJumpToTime(scene.startTime)}
                    className={`p-4 border-b border-zinc-800/50 cursor-pointer group transition-all ${
                        isActive 
                        ? 'bg-indigo-900/20 border-l-4 border-l-indigo-500' 
                        : 'hover:bg-zinc-800/50 border-l-4 border-l-transparent'
                    }`}
                 >
                    <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            isActive ? 'bg-indigo-600 text-white' : 'bg-zinc-700 text-zinc-400'
                        }`}>
                            SCENE {idx + 1}
                        </span>
                        <span className="text-[10px] text-zinc-500 font-mono">
                            {scene.duration.toFixed(1)}s
                        </span>
                    </div>
                    
                    <h4 className={`text-xs font-bold leading-tight mb-2 ${
                        isActive ? 'text-indigo-200' : 'text-zinc-300'
                    }`}>
                        {scene.title}
                    </h4>
                    
                    <div className="space-y-1">
                        {scene.beats.slice(0, 3).map(beat => (
                            <p key={beat.id} className="text-[10px] text-zinc-500 line-clamp-1 pl-2 border-l border-zinc-800">
                                {beat.content}
                            </p>
                        ))}
                        {scene.beats.length > 3 && (
                            <p className="text-[9px] text-zinc-600 pl-2">
                                + {scene.beats.length - 3} more beats...
                            </p>
                        )}
                    </div>
                 </div>
             );
         })}
         
         <div className="p-8 text-center text-zinc-600 text-xs">
            <FileText size={24} className="mx-auto mb-2 opacity-20" />
            <p>剧本结构分析完毕</p>
         </div>
      </div>
    </div>
  );
};
