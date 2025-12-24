
import React from 'react';
import { Beat } from '../types';
import { Image, Video } from 'lucide-react';

interface BeatCardProps {
  beat: Beat;
  isSelected: boolean;
  onSelect: () => void;
  indexInScene: number;
}

export const BeatCard: React.FC<BeatCardProps> = ({ 
  beat, 
  isSelected, 
  onSelect,
  indexInScene
}) => {
  const activeAsset = beat.assets.find(a => a.id === beat.mainAssetId) || beat.assets[0];

  return (
    <div 
      onClick={onSelect}
      className={`relative group flex-shrink-0 cursor-pointer transition-all duration-200 rounded-md overflow-hidden ${
        isSelected 
            ? 'ring-2 ring-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.4)] z-10 scale-[1.02]' 
            : 'ring-1 ring-zinc-800 hover:ring-zinc-600 hover:bg-zinc-800'
      }`}
      style={{ width: '220px', aspectRatio: '16/9' }}
    >
      {/* Full Bleed Visual */}
      <div className="absolute inset-0 bg-zinc-900">
        {activeAsset ? (
            activeAsset.type === 'video' ? (
                <video src={activeAsset.thumbnailUrl} className="w-full h-full object-cover opacity-90" muted />
            ) : (
                <img src={activeAsset.thumbnailUrl} alt="beat visual" className="w-full h-full object-cover opacity-90" />
            )
        ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-zinc-700 bg-zinc-900/50 pattern-grid">
                <Image size={24} strokeWidth={1} />
                <span className="text-[9px] mt-2 font-mono uppercase tracking-widest opacity-50">Empty Shot</span>
            </div>
        )}
      </div>

      {/* Hover Overlay Gradient */}
      <div className={`absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent transition-opacity duration-200 ${
          isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
      }`}></div>

      {/* Info Overlay (Visible on Hover or Select) */}
      <div className={`absolute bottom-0 left-0 right-0 p-3 transition-opacity duration-200 ${
          isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
      }`}>
        <div className="flex justify-between items-end mb-1">
             <span className="text-[10px] font-bold text-white bg-black/50 px-1.5 rounded backdrop-blur-sm">
                {String.fromCharCode(65 + indexInScene)}
             </span>
             <span className="text-[9px] font-mono text-zinc-300">
                {beat.duration.toFixed(1)}s
             </span>
        </div>
        <p className="text-[10px] text-zinc-300 line-clamp-2 leading-tight drop-shadow-md">
            {beat.content}
        </p>
      </div>

      {/* Type Indicator */}
      {activeAsset?.type === 'video' && (
        <div className="absolute top-2 right-2 text-white/50">
            <Video size={12} fill="currentColor" />
        </div>
      )}
    </div>
  );
};
