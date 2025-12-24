import React from 'react';
import { Loader2, Film, Sparkles } from 'lucide-react';

export interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse' | 'bars' | 'film';
  text?: string;
  fullScreen?: boolean;
  className?: string;
}

export interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  animate?: boolean;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
}

const sizeStyles = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6', 
  lg: 'w-8 h-8',
  xl: 'w-12 h-12'
};

const textSizes = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
  xl: 'text-lg'
};

// 主Loading组件
export const Loading: React.FC<LoadingProps> = ({
  size = 'md',
  variant = 'spinner',
  text,
  fullScreen = false,
  className = ''
}) => {
  const renderLoader = () => {
    switch (variant) {
      case 'spinner':
        return (
          <Loader2 
            className={`${sizeStyles[size]} animate-spin text-amber-500`} 
          />
        );
        
      case 'film':
        return (
          <div className="relative">
            <Film 
              className={`${sizeStyles[size]} text-amber-500 animate-pulse`} 
            />
            <Sparkles 
              className="absolute -top-1 -right-1 w-3 h-3 text-yellow-400 animate-bounce" 
            />
          </div>
        );
        
      case 'dots':
        return (
          <div className="flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className={`w-2 h-2 bg-amber-500 rounded-full animate-bounce`}
                style={{ animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
        );
        
      case 'pulse':
        return (
          <div className={`${sizeStyles[size]} bg-amber-500 rounded-full animate-pulse`} />
        );
        
      case 'bars':
        return (
          <div className="flex items-end gap-1">
            {[0, 1, 2, 3].map((i) => (
              <div
                key={i}
                className="w-1 bg-amber-500 rounded-full animate-pulse"
                style={{ 
                  height: `${12 + (i % 2) * 8}px`,
                  animationDelay: `${i * 0.1}s` 
                }}
              />
            ))}
          </div>
        );
        
      default:
        return (
          <Loader2 
            className={`${sizeStyles[size]} animate-spin text-amber-500`} 
          />
        );
    }
  };

  const content = (
    <div className={`flex flex-col items-center gap-3 ${className}`}>
      {renderLoader()}
      {text && (
        <p className={`${textSizes[size]} text-zinc-400 font-medium animate-pulse`}>
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-zinc-900/90 backdrop-blur-md border border-zinc-800 rounded-xl p-8 shadow-2xl">
          {content}
        </div>
      </div>
    );
  }

  return content;
};

// Skeleton组件
export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  className = '',
  animate = true,
  variant = 'rectangular'
}) => {
  const baseStyles = `
    bg-gradient-to-r from-zinc-800 via-zinc-700 to-zinc-800
    ${animate ? 'animate-pulse' : ''}
  `;
  
  const variantStyles = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: '',
    rounded: 'rounded-lg'
  };
  
  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height
  };

  return (
    <div 
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      style={style}
    />
  );
};

// 预设Skeleton组件
export const TextSkeleton: React.FC<{ lines?: number; className?: string }> = ({ 
  lines = 3, 
  className = '' 
}) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton
        key={i}
        height="1rem"
        width={i === lines - 1 ? '75%' : '100%'}
        variant="text"
      />
    ))}
  </div>
);

export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`p-4 border border-zinc-800 rounded-xl bg-zinc-900/40 ${className}`}>
    <div className="flex items-start gap-4">
      <Skeleton width={48} height={48} variant="circular" />
      <div className="flex-1 space-y-2">
        <Skeleton height="1.25rem" width="60%" />
        <Skeleton height="1rem" width="40%" />
      </div>
    </div>
    <div className="mt-4 space-y-2">
      <TextSkeleton lines={2} />
    </div>
  </div>
);

export const BeatCardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`p-4 border border-zinc-800 rounded-xl bg-zinc-900/40 ${className}`}>
    {/* 缩略图骨架 */}
    <Skeleton height="8rem" className="mb-4 rounded-lg" />
    
    {/* 标题骨架 */}
    <Skeleton height="1.25rem" width="80%" className="mb-2" />
    
    {/* 标签骨架 */}
    <div className="flex gap-2 mb-3">
      <Skeleton height="1.5rem" width="4rem" variant="rounded" />
      <Skeleton height="1.5rem" width="3rem" variant="rounded" />
    </div>
    
    {/* 元数据骨架 */}
    <div className="flex justify-between">
      <Skeleton height="1rem" width="3rem" />
      <Skeleton height="1rem" width="4rem" />
    </div>
  </div>
);

export const ProjectCardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`border border-zinc-800 rounded-xl bg-zinc-900/40 overflow-hidden ${className}`}>
    {/* 缩略图骨架 */}
    <Skeleton height="8rem" className="rounded-none" />
    
    <div className="p-4">
      {/* 标题骨架 */}
      <Skeleton height="1.25rem" width="70%" className="mb-2" />
      
      {/* 副标题骨架 */}
      <Skeleton height="1rem" width="50%" className="mb-3" />
      
      {/* 进度条骨架 */}
      <div className="flex items-center gap-2">
        <Skeleton height="0.75rem" width="2rem" />
        <Skeleton height="0.25rem" className="flex-1 rounded-full" />
      </div>
    </div>
  </div>
);

// 页面级Loading组件
export const PageLoading: React.FC<{ message?: string }> = ({ 
  message = "加载中..." 
}) => (
  <div className="flex-1 flex items-center justify-center min-h-[400px]">
    <Loading 
      size="lg" 
      variant="film" 
      text={message}
      className="text-center"
    />
  </div>
);

// 内联Loading组件
export const InlineLoading: React.FC<{ 
  text?: string;
  size?: 'sm' | 'md';
}> = ({ text, size = 'sm' }) => (
  <div className="flex items-center gap-2 text-zinc-400">
    <Loader2 className={`${sizeStyles[size]} animate-spin`} />
    {text && <span className={textSizes[size]}>{text}</span>}
  </div>
);

// 按钮Loading状态
export const ButtonLoading: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ 
  size = 'md' 
}) => (
  <Loader2 className={`${sizeStyles[size]} animate-spin`} />
);

export default Loading;