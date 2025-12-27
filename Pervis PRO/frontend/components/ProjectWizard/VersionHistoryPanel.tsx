/**
 * 版本历史面板
 * 显示当前版本号、修改历史、恢复历史版本
 */

import React, { useState, useEffect } from 'react';
import { 
  History, 
  Clock, 
  RotateCcw, 
  ChevronRight,
  User,
  Sparkles,
  FileText,
  Loader2
} from 'lucide-react';
import { wizardApi, VersionInfo } from './api';

interface VersionHistoryPanelProps {
  projectId: string;
  contentType?: string;
  entityId?: string;
  onRestore?: (version: VersionInfo) => void;
}

export const VersionHistoryPanel: React.FC<VersionHistoryPanelProps> = ({
  projectId,
  contentType,
  entityId,
  onRestore
}) => {
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);

  // 加载版本历史
  useEffect(() => {
    loadVersions();
  }, [projectId, contentType, entityId]);

  const loadVersions = async () => {
    setLoading(true);
    try {
      const result = await wizardApi.getVersionHistory(projectId, {
        content_type: contentType,
        entity_id: entityId,
        limit: 20
      });
      setVersions(result.versions || []);
    } catch (error) {
      console.error('加载版本历史失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 恢复版本
  const handleRestore = (version: VersionInfo) => {
    if (onRestore) {
      onRestore(version);
    }
  };

  // 来源图标
  const SourceIcon = ({ source }: { source: string }) => {
    switch (source) {
      case 'script_agent':
        return <FileText size={12} className="text-blue-400" />;
      case 'art_agent':
        return <Sparkles size={12} className="text-purple-400" />;
      case 'user':
        return <User size={12} className="text-green-400" />;
      default:
        return <FileText size={12} className="text-zinc-400" />;
    }
  };

  // 格式化时间
  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
    return date.toLocaleDateString();
  };

  return (
    <div className="h-full flex flex-col bg-zinc-900/50">
      {/* 头部 */}
      <div className="flex items-center gap-2 p-4 border-b border-zinc-800">
        <History className="text-amber-500" size={18} />
        <span className="text-sm font-medium text-white">版本历史</span>
        <span className="ml-auto text-xs text-zinc-500">{versions.length} 个版本</span>
      </div>

      {/* 版本列表 */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="text-zinc-500 animate-spin" size={24} />
          </div>
        ) : versions.length === 0 ? (
          <div className="text-center py-8">
            <History className="mx-auto text-zinc-700 mb-3" size={32} />
            <div className="text-sm text-zinc-500">暂无版本记录</div>
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {versions.map((version, index) => (
              <div
                key={version.version_id}
                className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                  selectedVersion === version.version_id
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-zinc-800/50 border-zinc-800 hover:border-zinc-700'
                }`}
                onClick={() => setSelectedVersion(
                  selectedVersion === version.version_id ? null : version.version_id
                )}
              >
                {/* 版本头部 */}
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-amber-400">
                    v{version.version_number}
                  </span>
                  <SourceIcon source={version.source} />
                  <span className="flex-1 text-xs text-zinc-400 truncate">
                    {version.version_name}
                  </span>
                  {index === 0 && (
                    <span className="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-400 text-[10px] rounded">
                      当前
                    </span>
                  )}
                </div>

                {/* 时间和类型 */}
                <div className="flex items-center gap-2 text-[10px] text-zinc-500">
                  <Clock size={10} />
                  <span>{formatTime(version.created_at)}</span>
                  <span>·</span>
                  <span>{version.content_type}</span>
                  {version.entity_name && (
                    <>
                      <span>·</span>
                      <span>{version.entity_name}</span>
                    </>
                  )}
                </div>

                {/* 展开的操作 */}
                {selectedVersion === version.version_id && index > 0 && (
                  <div className="mt-2 pt-2 border-t border-zinc-700">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRestore(version);
                      }}
                      className="flex items-center gap-2 px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 rounded text-xs text-zinc-300 transition-colors"
                    >
                      <RotateCcw size={12} />
                      <span>恢复此版本</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 底部提示 */}
      <div className="p-3 border-t border-zinc-800 text-[10px] text-zinc-600">
        版本由 PM_Agent 自动记录
      </div>
    </div>
  );
};

export default VersionHistoryPanel;
