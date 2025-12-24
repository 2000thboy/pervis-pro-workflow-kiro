import React from 'react';
import { 
  ChevronRight, 
  Save, 
  Share2, 
  Download, 
  Settings, 
  Bell,
  User,
  Clock,
  Zap,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { Button, IconButton, Badge, StatusIndicator, ProgressIndicator } from '../ui';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  active?: boolean;
}

export interface GlobalHeaderProps {
  // 面包屑导航
  breadcrumbs?: BreadcrumbItem[];
  
  // 页面标题和描述
  title?: string;
  subtitle?: string;
  
  // 进度指示
  progress?: {
    current: number;
    total: number;
    label?: string;
  };
  
  // 操作按钮
  actions?: React.ReactNode;
  
  // 系统状态
  systemStatus?: {
    aiService: 'online' | 'offline' | 'processing';
    lastSaved?: string;
    notifications?: number;
  };
  
  // 用户信息
  user?: {
    name: string;
    avatar?: string;
  };
  
  // 事件处理
  onSave?: () => void;
  onShare?: () => void;
  onExport?: () => void;
  onSettings?: () => void;
  onNotifications?: () => void;
  onUserMenu?: () => void;
  
  className?: string;
}

export const GlobalHeader: React.FC<GlobalHeaderProps> = ({
  breadcrumbs = [],
  title,
  subtitle,
  progress,
  actions,
  systemStatus,
  user,
  onSave,
  onShare,
  onExport,
  onSettings,
  onNotifications,
  onUserMenu,
  className = ''
}) => {
  return (
    <div className={`
      h-full flex items-center justify-between px-6 
      bg-zinc-950/95 backdrop-blur-sm border-b border-zinc-800
      ${className}
    `}>
      
      {/* 左侧：导航和标题 */}
      <div className="flex items-center gap-6 flex-1 min-w-0">
        
        {/* 面包屑导航 */}
        {breadcrumbs.length > 0 && (
          <nav className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((item, index) => (
              <React.Fragment key={index}>
                {index > 0 && (
                  <ChevronRight size={14} className="text-zinc-600" />
                )}
                <span className={`
                  ${item.active 
                    ? 'text-white font-medium' 
                    : 'text-zinc-500 hover:text-zinc-300 cursor-pointer'
                  }
                  transition-colors duration-200
                `}>
                  {item.label}
                </span>
              </React.Fragment>
            ))}
          </nav>
        )}
        
        {/* 页面标题 */}
        {title && (
          <div className="flex items-center gap-4 min-w-0">
            <div className="min-w-0">
              <h1 className="text-lg font-semibold text-white truncate">
                {title}
              </h1>
              {subtitle && (
                <p className="text-sm text-zinc-400 truncate">
                  {subtitle}
                </p>
              )}
            </div>
            
            {/* 进度指示器 */}
            {progress && (
              <div className="flex items-center gap-3">
                <div className="w-px h-6 bg-zinc-700" />
                <div className="flex items-center gap-2 text-sm text-zinc-400">
                  <span>{progress.label || '进度'}</span>
                  <Badge variant="brand" size="sm">
                    {progress.current}/{progress.total}
                  </Badge>
                  <ProgressIndicator 
                    progress={(progress.current / progress.total) * 100}
                    size="sm"
                    className="w-16"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 中间：自定义操作 */}
      {actions && (
        <div className="flex items-center gap-2 mx-6">
          {actions}
        </div>
      )}

      {/* 右侧：系统状态和用户操作 */}
      <div className="flex items-center gap-4 flex-shrink-0">
        
        {/* 系统状态 */}
        {systemStatus && (
          <div className="flex items-center gap-4">
            
            {/* AI服务状态 */}
            <div className="flex items-center gap-2">
              <StatusIndicator 
                status={systemStatus.aiService} 
                size="sm" 
              />
              <span className="text-xs text-zinc-500">
                AI {systemStatus.aiService === 'online' ? '就绪' : 
                     systemStatus.aiService === 'processing' ? '处理中' : '离线'}
              </span>
            </div>
            
            {/* 最后保存时间 */}
            {systemStatus.lastSaved && (
              <div className="flex items-center gap-2 text-xs text-zinc-500">
                <Clock size={12} />
                <span>已保存 {systemStatus.lastSaved}</span>
              </div>
            )}
            
            <div className="w-px h-6 bg-zinc-700" />
          </div>
        )}

        {/* 快捷操作按钮 */}
        <div className="flex items-center gap-1">
          
          {/* 保存 */}
          {onSave && (
            <IconButton
              icon={Save}
              size="sm"
              variant="ghost"
              tooltip="保存 (Ctrl+S)"
              onClick={onSave}
            />
          )}
          
          {/* 分享 */}
          {onShare && (
            <IconButton
              icon={Share2}
              size="sm"
              variant="ghost"
              tooltip="分享项目"
              onClick={onShare}
            />
          )}
          
          {/* 导出 */}
          {onExport && (
            <IconButton
              icon={Download}
              size="sm"
              variant="ghost"
              tooltip="导出项目"
              onClick={onExport}
            />
          )}
          
          {/* 设置 */}
          {onSettings && (
            <IconButton
              icon={Settings}
              size="sm"
              variant="ghost"
              tooltip="设置"
              onClick={onSettings}
            />
          )}
        </div>

        {/* 通知和用户 */}
        <div className="flex items-center gap-2">
          
          {/* 通知 */}
          {onNotifications && (
            <div className="relative">
              <IconButton
                icon={Bell}
                size="sm"
                variant="ghost"
                tooltip="通知"
                onClick={onNotifications}
              />
              {systemStatus?.notifications && systemStatus.notifications > 0 && (
                <Badge 
                  variant="error" 
                  size="sm"
                  className="absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center text-[10px] px-1"
                >
                  {systemStatus.notifications > 99 ? '99+' : systemStatus.notifications}
                </Badge>
              )}
            </div>
          )}
          
          {/* 用户菜单 */}
          {user && (
            <button
              onClick={onUserMenu}
              className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-zinc-800/50 transition-colors"
            >
              {user.avatar ? (
                <img 
                  src={user.avatar} 
                  alt={user.name}
                  className="w-6 h-6 rounded-full"
                />
              ) : (
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-amber-500 to-yellow-500 flex items-center justify-center text-black text-xs font-bold">
                  {user.name.charAt(0)}
                </div>
              )}
              <span className="text-sm text-zinc-300 hidden sm:block">
                {user.name}
              </span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// 预设头部组件
export const ProjectHeader: React.FC<{
  projectName: string;
  currentStage: string;
  progress?: { current: number; total: number };
  onSave?: () => void;
  onExport?: () => void;
}> = ({ projectName, currentStage, progress, onSave, onExport }) => (
  <GlobalHeader
    breadcrumbs={[
      { label: '项目', href: '/projects' },
      { label: projectName, active: true }
    ]}
    title={currentStage}
    progress={progress}
    systemStatus={{
      aiService: 'online',
      lastSaved: '2分钟前'
    }}
    user={{
      name: '导演'
    }}
    onSave={onSave}
    onExport={onExport}
  />
);

export const WorkflowHeader: React.FC<{
  workflow: string;
  step: string;
  stepNumber: number;
  totalSteps: number;
  actions?: React.ReactNode;
}> = ({ workflow, step, stepNumber, totalSteps, actions }) => (
  <GlobalHeader
    breadcrumbs={[
      { label: '工作流', href: '/workflow' },
      { label: workflow, active: true }
    ]}
    title={step}
    progress={{
      current: stepNumber,
      total: totalSteps,
      label: '步骤'
    }}
    actions={actions}
    systemStatus={{
      aiService: 'processing',
      lastSaved: '刚刚'
    }}
  />
);

export default GlobalHeader;