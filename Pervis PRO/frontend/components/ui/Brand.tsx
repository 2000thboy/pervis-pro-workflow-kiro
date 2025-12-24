import React from 'react';
import { Film, Sparkles, Play, Zap } from 'lucide-react';

export interface BrandLogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'full' | 'icon' | 'text';
  animated?: boolean;
  className?: string;
}

export interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'processing' | 'error' | 'warning';
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'brand';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const logoSizes = {
  xs: { icon: 16, text: 'text-sm' },
  sm: { icon: 20, text: 'text-base' },
  md: { icon: 24, text: 'text-lg' },
  lg: { icon: 32, text: 'text-xl' },
  xl: { icon: 40, text: 'text-2xl' }
};

// 品牌Logo组件
export const BrandLogo: React.FC<BrandLogoProps> = ({
  size = 'md',
  variant = 'full',
  animated = false,
  className = ''
}) => {
  const { icon: iconSize, text: textSize } = logoSizes[size];
  
  const IconComponent = () => (
    <div className={`relative ${animated ? 'group' : ''}`}>
      <div className="relative">
        <Film 
          size={iconSize} 
          className={`text-amber-500 ${animated ? 'group-hover:text-amber-400 transition-colors duration-300' : ''}`} 
        />
        <Sparkles 
          size={iconSize * 0.4} 
          className={`absolute -top-1 -right-1 text-yellow-400 ${animated ? 'animate-pulse group-hover:animate-bounce' : ''}`} 
        />
      </div>
      {animated && (
        <div className="absolute inset-0 bg-amber-500/20 rounded-full blur-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 animate-pulse" />
      )}
    </div>
  );
  
  const TextComponent = () => (
    <div className={`font-serif font-black tracking-tight ${textSize}`}>
      <span className="text-white">PreVis</span>
      <span className="gradient-text ml-1">Pro</span>
    </div>
  );
  
  if (variant === 'icon') {
    return (
      <div className={className}>
        <IconComponent />
      </div>
    );
  }
  
  if (variant === 'text') {
    return (
      <div className={className}>
        <TextComponent />
      </div>
    );
  }
  
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <IconComponent />
      <TextComponent />
    </div>
  );
};

// 状态指示器组件
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  size = 'md',
  showText = false,
  className = ''
}) => {
  const sizeStyles = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };
  
  const textSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base'
  };
  
  const statusConfig = {
    online: {
      color: 'bg-emerald-500',
      text: '在线',
      animation: 'animate-pulse'
    },
    offline: {
      color: 'bg-zinc-500',
      text: '离线',
      animation: ''
    },
    processing: {
      color: 'bg-amber-500',
      text: '处理中',
      animation: 'animate-pulse'
    },
    error: {
      color: 'bg-red-500',
      text: '错误',
      animation: 'animate-bounce'
    },
    warning: {
      color: 'bg-orange-500',
      text: '警告',
      animation: 'animate-pulse'
    }
  };
  
  const config = statusConfig[status];
  
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`${sizeStyles[size]} ${config.color} rounded-full ${config.animation}`} />
      {showText && (
        <span className={`${textSizes[size]} text-zinc-400 font-medium`}>
          {config.text}
        </span>
      )}
    </div>
  );
};

// 徽章组件
export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = ''
}) => {
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm'
  };
  
  const variantStyles = {
    default: 'bg-zinc-800 text-zinc-300 border-zinc-700',
    success: 'bg-emerald-900/50 text-emerald-400 border-emerald-700/50',
    warning: 'bg-orange-900/50 text-orange-400 border-orange-700/50',
    error: 'bg-red-900/50 text-red-400 border-red-700/50',
    info: 'bg-blue-900/50 text-blue-400 border-blue-700/50',
    brand: 'bg-amber-900/50 text-amber-400 border-amber-700/50'
  };
  
  return (
    <span className={`
      inline-flex items-center font-medium rounded-full border
      ${sizeStyles[size]}
      ${variantStyles[variant]}
      ${className}
    `}>
      {children}
    </span>
  );
};

// 版本标识组件
export const VersionBadge: React.FC<{
  version: string;
  label?: string;
  className?: string;
}> = ({ version, label = 'v', className = '' }) => (
  <Badge variant="brand" size="sm" className={className}>
    {label}{version}
  </Badge>
);

// 进度指示器组件
export const ProgressIndicator: React.FC<{
  progress: number;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
}> = ({ progress, size = 'md', showText = false, className = '' }) => {
  const sizeStyles = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  };
  
  const clampedProgress = Math.max(0, Math.min(100, progress));
  
  return (
    <div className={`space-y-1 ${className}`}>
      {showText && (
        <div className="flex justify-between text-xs text-zinc-400">
          <span>进度</span>
          <span>{Math.round(clampedProgress)}%</span>
        </div>
      )}
      <div className={`w-full bg-zinc-800 rounded-full overflow-hidden ${sizeStyles[size]}`}>
        <div 
          className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 transition-all duration-500 ease-out"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
};

// 分隔符组件
export const Divider: React.FC<{
  orientation?: 'horizontal' | 'vertical';
  variant?: 'solid' | 'dashed' | 'gradient';
  className?: string;
}> = ({ orientation = 'horizontal', variant = 'solid', className = '' }) => {
  const baseStyles = orientation === 'horizontal' 
    ? 'w-full h-px' 
    : 'h-full w-px';
  
  const variantStyles = {
    solid: 'bg-zinc-800',
    dashed: 'border-dashed border-t border-zinc-800',
    gradient: 'bg-gradient-to-r from-transparent via-zinc-700 to-transparent'
  };
  
  return (
    <div className={`${baseStyles} ${variantStyles[variant]} ${className}`} />
  );
};

// 装饰性元素组件
export const DecorativeElement: React.FC<{
  type: 'glow' | 'grid' | 'dots' | 'lines';
  className?: string;
}> = ({ type, className = '' }) => {
  switch (type) {
    case 'glow':
      return (
        <div className={`absolute inset-0 bg-gradient-radial from-amber-500/10 via-transparent to-transparent pointer-events-none ${className}`} />
      );
      
    case 'grid':
      return (
        <div className={`absolute inset-0 opacity-5 pointer-events-none ${className}`}>
          <div className="w-full h-full" style={{
            backgroundImage: `
              linear-gradient(rgba(245, 158, 11, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(245, 158, 11, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px'
          }} />
        </div>
      );
      
    case 'dots':
      return (
        <div className={`absolute inset-0 opacity-10 pointer-events-none ${className}`}>
          <div className="w-full h-full" style={{
            backgroundImage: `radial-gradient(circle, rgba(245, 158, 11, 0.3) 1px, transparent 1px)`,
            backgroundSize: '20px 20px'
          }} />
        </div>
      );
      
    case 'lines':
      return (
        <div className={`absolute inset-0 opacity-5 pointer-events-none ${className}`}>
          <div className="w-full h-full" style={{
            backgroundImage: `repeating-linear-gradient(
              45deg,
              transparent,
              transparent 10px,
              rgba(245, 158, 11, 0.1) 10px,
              rgba(245, 158, 11, 0.1) 11px
            )`
          }} />
        </div>
      );
      
    default:
      return null;
  }
};

export default BrandLogo;