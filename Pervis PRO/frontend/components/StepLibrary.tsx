
import React, { useState, useRef, useMemo } from 'react';
import { Project, ProjectAsset } from '../types';
import { api } from '../services/api';
import { 
  Upload, 
  Search, 
  Trash2, 
  FileVideo, 
  ImageIcon, 
  HardDrive, 
  Loader2,
  Plus,
  BrainCircuit,
  CheckCircle,
  AlertCircle,
  Network
} from 'lucide-react';
import { useLanguage } from './LanguageContext';

interface StepLibraryProps {
  project: Project;
  onUpdateProject: (updates: Partial<Project>) => void;
}

export const StepLibrary: React.FC<StepLibraryProps> = ({ project, onUpdateProject }) => {
  const { t } = useLanguage();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'video' | 'image'>('all');
  const [isDragging, setIsDragging] = useState(false);
  const [uploadQueue, setUploadQueue] = useState<{name: string, progress: number, status: string}[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Filter Assets
  const filteredAssets = useMemo(() => {
      return (project.library || []).filter(asset => {
          const matchesSearch = asset.filename.toLowerCase().includes(searchQuery.toLowerCase());
          const matchesType = filterType === 'all' 
              ? true 
              : filterType === 'video' 
                  ? asset.mimeType.startsWith('video') 
                  : asset.mimeType.startsWith('image');
          return matchesSearch && matchesType;
      }).sort((a, b) => b.createdAt - a.createdAt);
  }, [project.library, searchQuery, filterType]);

  // Upload Logic
  const handleFiles = async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      
      const newAssets: ProjectAsset[] = [];
      const queueItems = Array.from(files).map(f => ({ name: f.name, progress: 0, status: 'Starting...' }));
      
      setUploadQueue(queueItems);

      for (let i = 0; i < files.length; i++) {
          const file = files[i];
          
          setUploadQueue(prev => prev.map((item, idx) => idx === i ? { ...item, progress: 10, status: 'Uploading...' } : item));
          
          try {
              const asset = await api.uploadAsset(file, project.id, (status) => {
                  setUploadQueue(prev => prev.map((item, idx) => idx === i ? { ...item, progress: 50, status } : item));
              });
              newAssets.push(asset);
              
              setUploadQueue(prev => prev.map((item, idx) => idx === i ? { ...item, progress: 100, status: 'Complete' } : item));
          } catch (e) {
              console.error("Upload failed", e);
              setUploadQueue(prev => prev.map((item, idx) => idx === i ? { ...item, progress: 0, status: 'Failed' } : item));
          }
      }

      // Update Project
      const updatedLibrary = [...(project.library || []), ...newAssets];
      onUpdateProject({ library: updatedLibrary });
      
      setTimeout(() => setUploadQueue([]), 4000); // Keep status longer to show success
  };

  const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
  };

  const handleDelete = async (assetId: string) => {
      if(!confirm("确定要从项目中移除此素材吗？")) return;
      
      await api.deleteAsset(project.id, assetId);
      
      // Update local state by removing from library
      const updatedLibrary = project.library.filter(a => a.id !== assetId);
      onUpdateProject({ library: updatedLibrary });
  };

  const loadDemoAssets = () => {
      const demoAssets: ProjectAsset[] = [
          {
              id: `demo-vid-1-${Date.now()}`,
              projectId: project.id,
              mediaUrl: "https://videos.pexels.com/video-files/5532766/5532766-hd_1920_1080_25fps.mp4",
              thumbnailUrl: "https://images.pexels.com/videos/5532766/pictures/preview-0.jpg",
              filename: "cyberpunk_city_rain_night.mp4",
              mimeType: "video/mp4",
              source: "external",
              createdAt: Date.now(),
              metadata: { processingStatus: 'done', assetTrustScore: 0.8, feedbackHistory: [] }
          },
          {
              id: `demo-vid-2-${Date.now()}`,
              projectId: project.id,
              mediaUrl: "https://videos.pexels.com/video-files/3121459/3121459-hd_1920_1080_25fps.mp4",
              thumbnailUrl: "https://images.pexels.com/videos/3121459/pictures/preview-0.jpg",
              filename: "motorcycle_chase_action.mp4",
              mimeType: "video/mp4",
              source: "external",
              createdAt: Date.now(),
              metadata: { processingStatus: 'done', assetTrustScore: 0.7, feedbackHistory: [] }
          },
          {
              id: `demo-img-1-${Date.now()}`,
              projectId: project.id,
              mediaUrl: "https://images.unsplash.com/photo-1514337894902-6e2c36606fb3?q=80&w=600&auto=format&fit=crop",
              thumbnailUrl: "https://images.unsplash.com/photo-1514337894902-6e2c36606fb3?q=80&w=200&auto=format&fit=crop",
              filename: "neon_ramen_shop_interior.jpg",
              mimeType: "image/jpeg",
              source: "external",
              createdAt: Date.now(),
              metadata: { processingStatus: 'done', assetTrustScore: 0.9, feedbackHistory: [] }
          },
          {
              id: `demo-img-2-${Date.now()}`,
              projectId: project.id,
              mediaUrl: "https://images.unsplash.com/photo-1621251336056-11f84852084c?q=80&w=600&auto=format&fit=crop",
              thumbnailUrl: "https://images.unsplash.com/photo-1621251336056-11f84852084c?q=80&w=200&auto=format&fit=crop",
              filename: "dark_alley_rain.jpg",
              mimeType: "image/jpeg",
              source: "external",
              createdAt: Date.now(),
              metadata: { processingStatus: 'done', assetTrustScore: 0.6, feedbackHistory: [] }
          },
          {
              id: `demo-img-3-${Date.now()}`,
              projectId: project.id,
              mediaUrl: "https://images.unsplash.com/photo-1555680202-c86f0e12f086?q=80&w=600&auto=format&fit=crop",
              thumbnailUrl: "https://images.unsplash.com/photo-1555680202-c86f0e12f086?q=80&w=200&auto=format&fit=crop",
              filename: "surveillance_drone_view.jpg",
              mimeType: "image/jpeg",
              source: "external",
              createdAt: Date.now(),
              metadata: { processingStatus: 'done', assetTrustScore: 0.85, feedbackHistory: [] }
          }
      ];

      const updatedLibrary = [...(project.library || []), ...demoAssets];
      onUpdateProject({ library: updatedLibrary });
      alert("Successfully simulated importing 5 assets from local network path //192.168.1.100/assets");
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 text-zinc-200"
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
    >
        {/* Drop Zone Overlay */}
        {isDragging && (
            <div className="absolute inset-0 z-50 bg-indigo-500/20 backdrop-blur-sm border-4 border-indigo-500 border-dashed m-4 rounded-xl flex items-center justify-center pointer-events-none">
                <div className="text-center animate-bounce">
                    <Upload size={48} className="mx-auto text-indigo-400 mb-2" />
                    <h3 className="text-2xl font-bold text-white">释放以添加素材</h3>
                </div>
            </div>
        )}

        {/* Header Toolbar */}
        <div className="h-16 border-b border-zinc-800 flex items-center justify-between px-6 bg-zinc-900/50">
            <div className="flex items-center gap-4">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <HardDrive size={20} className="text-indigo-500" />
                    素材中心
                </h2>
                <div className="h-4 w-px bg-zinc-700"></div>
                <div className="text-xs text-zinc-500">
                    共 {project.library?.length || 0} 个文件
                </div>
            </div>

            <div className="flex items-center gap-3">
                <div className="relative group">
                    <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-indigo-400" />
                    <input 
                        type="text" 
                        placeholder="搜索文件名或 AI 标签..." 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-64 bg-zinc-900 border border-zinc-700 rounded-full pl-8 pr-4 py-1.5 text-xs focus:outline-none focus:border-indigo-500 transition-all"
                    />
                </div>

                <div className="flex bg-zinc-900 rounded-lg p-1 border border-zinc-800">
                    <button onClick={() => setFilterType('all')} className={`px-3 py-1 text-xs rounded-md transition-colors ${filterType === 'all' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>全部</button>
                    <button onClick={() => setFilterType('video')} className={`px-3 py-1 text-xs rounded-md transition-colors ${filterType === 'video' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>视频</button>
                    <button onClick={() => setFilterType('image')} className={`px-3 py-1 text-xs rounded-md transition-colors ${filterType === 'image' ? 'bg-zinc-700 text-white' : 'text-zinc-500 hover:text-zinc-300'}`}>图片</button>
                </div>

                <div className="h-6 w-px bg-zinc-800 mx-2"></div>

                <button 
                    onClick={loadDemoAssets}
                    className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 px-4 py-1.5 rounded-full text-xs font-bold transition-all"
                    title="Simulate importing assets from a local network share"
                >
                    <Network size={14} /> 模拟局域网导入
                </button>

                <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-1.5 rounded-full text-xs font-bold transition-all shadow-lg shadow-indigo-900/20"
                >
                    <Plus size={14} /> 上传素材
                </button>
                <input type="file" multiple ref={fileInputRef} className="hidden" onChange={(e) => handleFiles(e.target.files)} />
            </div>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-zinc-800">
            
            {/* Upload Queue */}
            {uploadQueue.length > 0 && (
                <div className="mb-6 space-y-2">
                    {uploadQueue.map((item, idx) => (
                        <div key={idx} className="bg-zinc-800 border border-zinc-700 rounded p-3 flex items-center gap-3 w-full max-w-md animate-in slide-in-from-top-2">
                            <Loader2 size={16} className={`animate-spin ${item.status === 'Complete' ? 'text-green-500' : 'text-indigo-500'}`} />
                            <div className="flex-1">
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-zinc-300 truncate font-bold">{item.name}</span>
                                    <span className="text-zinc-500 text-[10px] uppercase">{item.status}</span>
                                </div>
                                <div className="h-1 bg-zinc-900 rounded-full overflow-hidden">
                                    <div className="h-full bg-indigo-500 transition-all duration-300" style={{ width: `${item.progress}%` }}></div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Grid */}
            {filteredAssets.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
                    {filteredAssets.map(asset => (
                        <div key={asset.id} className="group relative aspect-square bg-zinc-900 rounded-lg border border-zinc-800 hover:border-zinc-600 overflow-hidden transition-all hover:shadow-xl cursor-pointer">
                            
                            {/* Content */}
                            {asset.mimeType.startsWith('video') ? (
                                <video src={asset.thumbnailUrl} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" muted />
                            ) : (
                                <img src={asset.thumbnailUrl} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                            )}

                            {/* Overlays */}
                            <div className="absolute top-2 left-2 bg-black/60 p-1 rounded backdrop-blur-sm text-white">
                                {asset.mimeType.startsWith('video') ? <FileVideo size={12} /> : <ImageIcon size={12} />}
                            </div>
                            
                            {/* AI Processing Status */}
                            <div className="absolute top-2 right-2 backdrop-blur-sm text-white p-1 rounded">
                                {asset.metadata?.processingStatus === 'processing' && (
                                    <div title="AI Analysis in Progress" className="bg-yellow-500/80 p-1 rounded">
                                        <Loader2 size={12} className="animate-spin text-black" />
                                    </div>
                                )}
                                {asset.metadata?.processingStatus === 'done' && (
                                    <div title="Semantic Index Ready" className="bg-indigo-500/80 p-1 rounded">
                                        <BrainCircuit size={12} />
                                    </div>
                                )}
                                {asset.metadata?.processingStatus === 'error' && (
                                    <div title="Analysis Failed" className="bg-red-500/80 p-1 rounded">
                                        <AlertCircle size={12} />
                                    </div>
                                )}
                            </div>

                            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-3 translate-y-full group-hover:translate-y-0 transition-transform">
                                <h4 className="text-xs font-bold text-white truncate mb-0.5" title={asset.filename}>{asset.filename}</h4>
                                <div className="flex justify-between items-center text-[9px] text-zinc-400 font-mono">
                                    <span>{new Date(asset.createdAt).toLocaleDateString()}</span>
                                    <button onClick={(e) => { e.stopPropagation(); handleDelete(asset.id); }} className="p-1 hover:bg-red-500/20 hover:text-red-400 rounded transition-colors"><Trash2 size={12} /></button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="h-full flex flex-col items-center justify-center text-zinc-600 pb-20">
                    <div className="w-24 h-24 bg-zinc-900 rounded-full flex items-center justify-center mb-6 border border-zinc-800">
                        <Upload size={48} className="opacity-20" />
                    </div>
                    <h3 className="text-xl font-bold text-zinc-400 mb-2">项目素材库为空</h3>
                    <p className="text-sm text-zinc-500 max-w-sm text-center leading-relaxed mb-4">
                        您可以直接拖拽上传，或连接局域网服务器。
                    </p>
                     <button 
                        onClick={loadDemoAssets}
                        className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 px-6 py-2 rounded-full text-sm font-bold transition-all"
                    >
                        <Network size={16} /> 连接本地/局域网素材 (Demo)
                    </button>
                </div>
            )}
        </div>
    </div>
  );
};
