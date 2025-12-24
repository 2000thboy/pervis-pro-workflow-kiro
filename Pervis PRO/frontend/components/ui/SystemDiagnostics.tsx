import React, { useState, useEffect } from 'react';
import { 
  Monitor, 
  HardDrive, 
  Cpu, 
  Memory, 
  Wifi, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  Info,
  Settings
} from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';
import FFmpegStatusComponent from './FFmpegStatus';

interface SystemInfo {
  os: string;
  platform: string;
  cpu_count: number;
  memory_total_gb: number;
  memory_available_gb: number;
  disk_total_gb: number;
  disk_free_gb: number;
  network_connected: boolean;
}

interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'critical';
  checks: {
    name: string;
    status: 'pass' | 'warning' | 'fail';
    message: string;
    details?: string;
  }[];
  recommendations: string[];
}

interface SystemDiagnosticsProps {
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export const SystemDiagnostics: React.FC<SystemDiagnosticsProps> = ({
  className = '',
  autoRefresh = false,
  refreshInterval = 30000
}) => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchSystemInfo = async () => {
    try {
      const response = await fetch('/api/system/info');
      const data = await response.json();
      setSystemInfo(data);
    } catch (error) {
      console.error('Failed to fetch system info:', error);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch('/api/system/health');
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('Failed to fetch system health:', error);
    }
  };

  const refreshData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchSystemInfo(), fetchSystemHealth()]);
      setLastUpdate(new Date());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(refreshData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case 'fail':
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default:
        return <Info className="w-5 h-5 text-gray-500" />;
    }
  };

  const getOverallHealthColor = () => {
    if (!systemHealth) return 'border-gray-200 bg-gray-50';
    
    switch (systemHealth.overall_status) {
      case 'healthy':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'critical':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes.toFixed(1)} GB`;
    return `${(bytes / 1024).toFixed(1)} TB`;
  };

  const getUsagePercentage = (used: number, total: number) => {
    return ((used / total) * 100).toFixed(1);
  };

  const getUsageColor = (percentage: number) => {
    if (percentage > 90) return 'bg-red-500';
    if (percentage > 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 标题和刷新按钮 */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">系统诊断</h2>
        <div className="flex items-center space-x-3">
          {lastUpdate && (
            <span className="text-sm text-gray-500">
              最后更新: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={refreshData}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* FFmpeg 状态 */}
      <FFmpegStatusComponent />

      {/* 系统健康状态 */}
      {systemHealth && (
        <Card className={`p-4 ${getOverallHealthColor()}`}>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                系统健康状态
              </h3>
              <div className="flex items-center space-x-2">
                {systemHealth.overall_status === 'healthy' && (
                  <CheckCircle className="w-6 h-6 text-green-500" />
                )}
                {systemHealth.overall_status === 'warning' && (
                  <AlertTriangle className="w-6 h-6 text-yellow-500" />
                )}
                {systemHealth.overall_status === 'critical' && (
                  <AlertTriangle className="w-6 h-6 text-red-500" />
                )}
                <span className="font-medium capitalize">
                  {systemHealth.overall_status === 'healthy' ? '健康' :
                   systemHealth.overall_status === 'warning' ? '警告' : '严重'}
                </span>
              </div>
            </div>

            {/* 健康检查项 */}
            <div className="space-y-2">
              {systemHealth.checks.map((check, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-white rounded-lg">
                  {getHealthIcon(check.status)}
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-gray-900">{check.name}</h4>
                      <span className={`text-sm px-2 py-1 rounded-full ${
                        check.status === 'pass' ? 'bg-green-100 text-green-800' :
                        check.status === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {check.status === 'pass' ? '通过' :
                         check.status === 'warning' ? '警告' : '失败'}
                      </span>
                    </div>
                    <p className="text-gray-600 mt-1">{check.message}</p>
                    {check.details && (
                      <p className="text-sm text-gray-500 mt-1">{check.details}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* 推荐建议 */}
            {systemHealth.recommendations.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">优化建议:</h4>
                <ul className="space-y-1">
                  {systemHealth.recommendations.map((recommendation, index) => (
                    <li key={index} className="text-sm text-blue-800 flex items-start">
                      <span className="w-2 h-2 bg-blue-400 rounded-full mt-2 mr-3 flex-shrink-0" />
                      {recommendation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* 系统信息 */}
      {systemInfo && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* 系统概览 */}
          <Card className="p-4">
            <div className="flex items-center space-x-3 mb-4">
              <Monitor className="w-6 h-6 text-blue-500" />
              <h3 className="text-lg font-semibold text-gray-900">系统信息</h3>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">操作系统:</span>
                <span className="font-medium">{systemInfo.os}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">平台:</span>
                <span className="font-medium">{systemInfo.platform}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">CPU 核心:</span>
                <span className="font-medium">{systemInfo.cpu_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">网络连接:</span>
                <div className="flex items-center space-x-2">
                  <Wifi className={`w-4 h-4 ${systemInfo.network_connected ? 'text-green-500' : 'text-red-500'}`} />
                  <span className="font-medium">
                    {systemInfo.network_connected ? '已连接' : '未连接'}
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* 资源使用情况 */}
          <Card className="p-4">
            <div className="flex items-center space-x-3 mb-4">
              <Settings className="w-6 h-6 text-green-500" />
              <h3 className="text-lg font-semibold text-gray-900">资源使用</h3>
            </div>
            <div className="space-y-4">
              {/* 内存使用 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Memory className="w-4 h-4 text-blue-500" />
                    <span className="text-gray-600">内存</span>
                  </div>
                  <span className="text-sm font-medium">
                    {formatBytes(systemInfo.memory_available_gb)} / {formatBytes(systemInfo.memory_total_gb)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(
                      parseFloat(getUsagePercentage(
                        systemInfo.memory_total_gb - systemInfo.memory_available_gb,
                        systemInfo.memory_total_gb
                      ))
                    )}`}
                    style={{
                      width: `${getUsagePercentage(
                        systemInfo.memory_total_gb - systemInfo.memory_available_gb,
                        systemInfo.memory_total_gb
                      )}%`
                    }}
                  />
                </div>
              </div>

              {/* 磁盘使用 */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="w-4 h-4 text-purple-500" />
                    <span className="text-gray-600">磁盘</span>
                  </div>
                  <span className="text-sm font-medium">
                    {formatBytes(systemInfo.disk_free_gb)} / {formatBytes(systemInfo.disk_total_gb)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getUsageColor(
                      parseFloat(getUsagePercentage(
                        systemInfo.disk_total_gb - systemInfo.disk_free_gb,
                        systemInfo.disk_total_gb
                      ))
                    )}`}
                    style={{
                      width: `${getUsagePercentage(
                        systemInfo.disk_total_gb - systemInfo.disk_free_gb,
                        systemInfo.disk_total_gb
                      )}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default SystemDiagnostics;