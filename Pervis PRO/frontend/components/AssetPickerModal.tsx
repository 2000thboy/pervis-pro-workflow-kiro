
import React from 'react';
import { X, Check, Loader2, Sparkles, Youtube } from 'lucide-react';
import { useLanguage } from '../LanguageContext';
import { Asset } from '../types';

interface AssetPickerModalProps {
    query: string;
    results: Asset[];
    isLoading: boolean;
    onClose: () => void;
    onApply: (asset: Asset) => void;
}

export const AssetPickerModal: React.FC<AssetPickerModalProps> = ({
    query,
    results,
    isLoading,
    onClose,
    onApply
}) => {
    const { t } = useLanguage();

    return (
        <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in zoom-in-95 duration-200">
            <div className="w-[1000px] h-[700px] bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl flex flex-col overflow-hidden">

                {/* Header */}
                <div className="p-6 border-b border-zinc-800 flex items-start justify-between bg-zinc-900/30">
                    <div>
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            <Sparkles className="text-indigo-500" size={20} />
                            AI Asset Matcher
                        </h2>
                        <div className="flex items-center gap-2 mt-2">
                            <span className="text-xs text-zinc-500">Query Context:</span>
                            <code className="px-2 py-0.5 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-300 font-mono">
                                {query.length > 60 ? query.substring(0, 60) + '...' : query}
                            </code>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-zinc-800 rounded-full text-zinc-500 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-6 bg-zinc-950/50">
                    {isLoading ? (
                        <div className="h-full flex flex-col items-center justify-center space-y-4">
                            <Loader2 size={40} className="animate-spin text-indigo-500" />
                            <p className="text-sm text-zinc-400 animate-pulse">Scanning Vector Database...</p>
                        </div>
                    ) : results.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-zinc-600">
                            <Youtube size={48} strokeWidth={1} className="mb-4 opacity-20" />
                            <p>No matching assets found.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-3 gap-6">
                            {results.map((asset, idx) => (
                                <div
                                    key={asset.id}
                                    className="group relative aspect-video bg-zinc-900 rounded-lg overflow-hidden border border-zinc-800 hover:border-indigo-500 transition-all cursor-pointer hover:shadow-lg hover:shadow-indigo-500/10"
                                    onClick={() => onApply(asset)}
                                >
                                    {/* Thumbnail */}
                                    {asset.thumbnailUrl ? (
                                        <img src={asset.thumbnailUrl} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center bg-zinc-900 text-zinc-700">
                                            <Youtube size={32} />
                                        </div>
                                    )}

                                    {/* Overlay Info */}
                                    <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/90 to-transparent pt-8">
                                        <div className="flex items-end justify-between">
                                            <div>
                                                <div className="text-xs font-bold text-white mb-0.5">Match Score: {asset.name.replace('Match: ', '')}</div>
                                                <div className="text-[10px] text-zinc-400 line-clamp-1">{asset.notes}</div>
                                            </div>
                                            <button className="p-1.5 bg-indigo-600 rounded-full text-white opacity-0 group-hover:opacity-100 transform translate-y-2 group-hover:translate-y-0 transition-all">
                                                <Check size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-zinc-800 bg-zinc-900/50 flex justify-between items-center text-[10px] text-zinc-500">
                    <span>Powered by Pervis PRO Vision Kernel</span>
                    <span>{results.length} results found</span>
                </div>
            </div>
        </div>
    );
};
