
import React from 'react';
import { Asset } from '../types';
import { Upload, Library, Star, X, Video, Link as LinkIcon, ThumbsDown, ThumbsUp } from 'lucide-react';
import { useLanguage } from './LanguageContext';

interface AssetWallProps {
  assets: Asset[];
  mainAssetId?: string;
  onUpload: () => void;
  onLinkLocal: () => void;
  onOpenLibrary: () => void;
  onSelect: (asset: Asset) => void;
  onSetMain: (assetId: string) => void;
  onRemove: (assetId: string) => void;
  onFeedback?: (asset: Asset, type: 'explicit_accept' | 'explicit_reject') => void;
  selectedAssetId: string | null;
}

export const AssetWall: React.FC<AssetWallProps> = ({ 
  assets, 
  mainAssetId, 
  onUpload,
  onLinkLocal,
  onOpenLibrary, 
  onSelect, 
  onSetMain, 
  onRemove,
  onFeedback,
  selectedAssetId
}) => {
  const { t } = useLanguage();

  return (
    <div className="flex gap-2 overflow-x-auto p-2 min-h-[100px] scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent items-start">
      {/* Action Buttons */}
      <div className="flex flex-col gap-1 flex-shrink-0">
        <button 
          onClick={onUpload} 
          title="上传文件 (Storage)"
          className="w-16 h-8 border border-dashed border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/50 rounded flex items-center justify-center transition-colors"
        >
            <Upload size={14} className="text-zinc-500" />
        </button>
        <button 
          onClick={onLinkLocal} 
          title={t('asset.link_local')}
          className="w-16 h-8 border border-zinc-700 hover:border-blue-500/50 hover:bg-blue-900/10 rounded flex items-center justify-center bg-zinc-900 transition-colors"
        >
            <LinkIcon size={14} className="text-blue-400" />
        </button>
        <button 
          onClick={onOpenLibrary} 
          title="从项目库选择"
          className="w-16 h-8 border border-zinc-700 hover:border-zinc-500 hover:bg-zinc-800/50 rounded flex items-center justify-center bg-zinc-900 transition-colors"
        >
            <Library size={14} className="text-zinc-500" />
        </button>
      </div>

      {/* Asset List */}
      {assets.map((asset) => (
        <div 
          key={asset.id} 
          className={`relative group w-32 h-24 flex-shrink-0 cursor-pointer rounded overflow-hidden border transition-all ${
            asset.id === selectedAssetId ? 'border-indigo-500 ring-1 ring-indigo-500' : 'border-zinc-800 hover:border-zinc-600'
          }`}
          onClick={(e) => {
            e.stopPropagation();
            onSelect(asset);
          }}
          onDoubleClick={(e) => {
            e.stopPropagation();
            onSetMain(asset.id);
          }}
        >
          {asset.type === 'video' ? (
             <video src={asset.thumbnailUrl} className="w-full h-full object-cover opacity-80" muted />
          ) : (
             <img 
               src={asset.thumbnailUrl} 
               alt="thumbnail"
               className={`w-full h-full object-cover transition-opacity ${asset.id === mainAssetId ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`} 
             />
          )}
          
          {/* Main Indicator (Top Right) */}
          {asset.id === mainAssetId && (
            <div className="absolute top-0 right-0 bg-indigo-600 p-0.5 rounded-bl shadow-sm z-10">
                <Star size={8} className="text-white fill-current" />
            </div>
          )}

          {/* Type Indicators */}
          <div className="absolute bottom-0 left-0 right-0 bg-black/60 px-1 py-0.5 text-[8px] text-white flex items-center justify-between">
            <span className="flex items-center gap-0.5">
                {asset.type === 'video' ? <Video size={6} /> : <Library size={6} />}
                {asset.source === 'local' ? 'LOCAL' : 'CLOUD'}
            </span>
          </div>

          {/* Feedback & Actions Overlay */}
          <div className="absolute inset-0 bg-black/70 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center gap-2 transition-opacity z-20">
             
             {/* Selection Tools */}
             <div className="flex gap-2">
                 <button 
                    onClick={(e) => { e.stopPropagation(); onSetMain(asset.id); if (onFeedback) onFeedback(asset, 'explicit_accept'); }} 
                    title="设为封面 (采纳)"
                    className={`p-1.5 rounded-full hover:bg-white/20 transition-colors ${asset.id === mainAssetId ? "text-yellow-400" : "text-zinc-300"}`}
                 >
                    <Star size={12} className={asset.id === mainAssetId ? "fill-current" : ""} />
                 </button>
                 <button 
                    onClick={(e) => { e.stopPropagation(); onRemove(asset.id); }} 
                    title="移除引用"
                    className="p-1.5 rounded-full hover:bg-white/20 text-red-400 hover:text-red-300 transition-colors"
                 >
                    <X size={12} />
                 </button>
             </div>

             {/* Feedback Tools (State Machine Interaction) */}
             {onFeedback && (
                 <div className="flex gap-2 mt-1">
                    <button 
                        onClick={(e) => { e.stopPropagation(); onFeedback(asset, 'explicit_accept'); }}
                        title="Good Match (+Trust)"
                        className="p-1 bg-green-900/50 hover:bg-green-600 rounded text-green-200"
                    >
                        <ThumbsUp size={10} />
                    </button>
                    <button 
                        onClick={(e) => { e.stopPropagation(); onFeedback(asset, 'explicit_reject'); }}
                        title="Bad Match (-Trust)"
                        className="p-1 bg-red-900/50 hover:bg-red-600 rounded text-red-200"
                    >
                        <ThumbsDown size={10} />
                    </button>
                 </div>
             )}
          </div>
        </div>
      ))}
    </div>
  );
};
