import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Download, ExternalLink, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

interface FFmpegStatus {
  is_installed: boolean;
  version?: string;
  path?: string;
  is_version_supported: boolean;
  installation_guide?: {
    os_type: string;
    method: string;
    commands: string[];
    download_url?: string;
    notes: string[];
  };
}

interface FFmpegStatusProps {
  onStatusChange?: (status: FFmpegStatus) => void;
  className?: string;
}

export const FFmpegStatusComponent: React.FC<FFmpegStatusProps> = ({
  onStatusChange,
  className = ''
}) => {
  const [status, setStatus] = useState<FFmpegStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [showGuide, setShowGuide] = useState(false);

  const checkFFmpegStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/system/ffmpeg-status');
      const data = await response.json();
      setStatus(data);
      onStatusChange?.(data);
    } catch (error) {
      console.error('Failed to check FFmpeg status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkFFmpegStatus();
  }, []);

  const getStatusIcon = () => {
    if (loading) {
      return <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />;
    }
    
    if (!status?.is_installed) {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    }
    
    if (!status.is_version_supported) {
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
    
    return <CheckCircle className="w-5 h-5 text-green-500" />;
  };

  const getStatusText = () => {
    if (loading) return '检查中...';
    
    if (!status?.is_installed) {
      return 'FFmpeg 未安装';
    }
    
    if (!status.is_version_supported) {
      return `FFmpeg 版本过低 (${status.version})`;
    }
    
    return `FFmpeg 已安装 (${status.version})`;
  };

  const getStatusColor = () => {
    if (loading) return 'border-blue-200 bg-blue-50';
    
    if (!status?.is_installed) {
      return 'border-red-200 bg-red-50';
    }
    
    if (!status.is_version_supported) {
      return 'border-yellow-200 bg-yellow-50';
    }
    
    return 'border-green-200 bg-green-50';
  };

  return (
    <div className={`space-y-4 ${className}`}>
      <Card className={`p-4 ${getStatusColor()}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <h3 className="font-medium text-gray-900">{getStatusText()}</h3>
              {status?.path && (
                <p className="text-sm text-gray-600">路径: {status.path}</p>
              )}
            </div>
          </div>
          
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={checkFFmpegStatus}
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
            
            {(!status?.is_installed || !status.is_version_supported) && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowGuide(!showGuide)}
              >
                <Download className="w-4 h-4 mr-2" />
                安装指南
              </Button>
            )}
          </div>
        </div>
      </Card>

      {showGuide && status?.installation_guide && (
        <Card className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-semibold text-gray-900">
                FFmpeg 安装指南 ({status.installation_guide.os_type})
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowGuide(false)}
              >
                ×
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <h5 className="font-medium text-gray-900 mb-2">安装方法: {status.installation_guide.method}</h5>
                
                {status.installation_guide.download_url && (
                  <div className="mb-4">
                    <a
                      href={status.installation_guide.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 hover:text-blue-800"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      下载 FFmpeg
                    </a>
                  </div>
                )}

                {status.installation_guide.commands.length > 0 && (
                  <div>
                    <h6 className="font-medium text-gray-700 mb-2">执行命令:</h6>
                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
                      {status.installation_guide.commands.map((command, index) => (
                        <div key={index} className="mb-1">
                          <span className="text-gray-500">$ </span>
                          {command}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {status.installation_guide.notes.length > 0 && (
                  <div className="mt-4">
                    <h6 className="font-medium text-gray-700 mb-2">注意事项:</h6>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                      {status.installation_guide.notes.map((note, index) => (
                        <li key={index}>{note}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5 mr-3 flex-shrink-0" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-1">安装完成后:</p>
                  <p>请重启应用程序或点击"刷新"按钮来检测 FFmpeg 安装状态。</p>
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default FFmpegStatusComponent;