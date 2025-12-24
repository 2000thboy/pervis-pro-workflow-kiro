import React, { forwardRef } from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  description?: string;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
  selected?: boolean;
}

const variantStyles = {
  default: `
    bg-zinc-900/40 backdrop-blur-sm
    border border-zinc-800/50
    shadow-lg shadow-black/20
  `,
  
  elevated: `
    bg-zinc-900/60 backdrop-blur-md
    border border-zinc-700/50
    shadow-xl shadow-black/30
  `,
  
  outlined: `
    bg-transparent
    border border-zinc-700
    shadow-none
  `,
  
  glass: `
    bg-white/5 backdrop-blur-xl
    border border-white/10
    shadow-2xl shadow-black/40
  `
};

const paddingStyles = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6'
};

export const Card = forwardRef<HTMLDivElement, CardProps>(({
  title,
  subtitle,
  description,
  actions,
  children,
  variant = 'default',
  padding = 'md',
  hover = false,
  selected = false,
  className = '',
  ...props
}, ref) => {
  const baseStyles = `
    rounded-xl
    transition-all duration-300 ease-out
    relative overflow-hidden
  `;
  
  const hoverStyles = hover ? `
    hover:scale-[1.02] hover:shadow-2xl hover:shadow-black/40
    hover:border-amber-500/30
    cursor-pointer
  ` : '';
  
  const selectedStyles = selected ? `
    border-amber-500/50 bg-amber-500/5
    shadow-xl shadow-amber-500/20
  ` : '';
  
  const combinedClassName = [
    baseStyles,
    variantStyles[variant],
    paddingStyles[padding],
    hoverStyles,
    selectedStyles,
    className
  ].join(' ').replace(/\s+/g, ' ').trim();

  return (
    <div
      ref={ref}
      className={combinedClassName}
      {...props}
    >
      {/* 选中状态指示器 */}
      {selected && (
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-yellow-500" />
      )}
      
      {/* 头部区域 */}
      {(title || subtitle || actions) && (
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            {title && (
              <h3 className="text-lg font-semibold text-white mb-1 truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-sm text-zinc-400 truncate">
                {subtitle}
              </p>
            )}
            {description && (
              <p className="text-sm text-zinc-500 mt-2 line-clamp-2">
                {description}
              </p>
            )}
          </div>
          
          {actions && (
            <div className="flex items-center gap-2 ml-4 flex-shrink-0">
              {actions}
            </div>
          )}
        </div>
      )}
      
      {/* 内容区域 */}
      {children && (
        <div className="relative">
          {children}
        </div>
      )}
    </div>
  );
});

Card.displayName = 'Card';

// 卡片头部组件
export const CardHeader = forwardRef<HTMLDivElement, {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}>(({ title, subtitle, actions, children, className = '' }, ref) => (
  <div ref={ref} className={`flex items-start justify-between mb-4 ${className}`}>
    <div className="flex-1 min-w-0">
      {title && (
        <h3 className="text-lg font-semibold text-white mb-1 truncate">
          {title}
        </h3>
      )}
      {subtitle && (
        <p className="text-sm text-zinc-400 truncate">
          {subtitle}
        </p>
      )}
      {children}
    </div>
    
    {actions && (
      <div className="flex items-center gap-2 ml-4 flex-shrink-0">
        {actions}
      </div>
    )}
  </div>
));

CardHeader.displayName = 'CardHeader';

// 卡片内容组件
export const CardContent = forwardRef<HTMLDivElement, {
  children: React.ReactNode;
  className?: string;
}>(({ children, className = '' }, ref) => (
  <div ref={ref} className={`relative ${className}`}>
    {children}
  </div>
));

CardContent.displayName = 'CardContent';

// 卡片底部组件
export const CardFooter = forwardRef<HTMLDivElement, {
  children: React.ReactNode;
  className?: string;
}>(({ children, className = '' }, ref) => (
  <div ref={ref} className={`mt-4 pt-4 border-t border-zinc-800/50 ${className}`}>
    {children}
  </div>
));

CardFooter.displayName = 'CardFooter';

// 预设卡片组件
export const ProjectCard = forwardRef<HTMLDivElement, {
  title: string;
  subtitle?: string;
  thumbnail?: string;
  progress?: number;
  lastModified?: string;
  onClick?: () => void;
  onDelete?: () => void;
  className?: string;
}>(({ 
  title, 
  subtitle, 
  thumbnail, 
  progress = 0, 
  lastModified, 
  onClick, 
  onDelete,
  className = '' 
}, ref) => (
  <Card
    ref={ref}
    variant="elevated"
    hover
    onClick={onClick}
    className={`group cursor-pointer ${className}`}
  >
    {/* 缩略图区域 */}
    <div className="relative h-32 -m-4 mb-4 rounded-t-xl overflow-hidden bg-gradient-to-br from-zinc-800 to-zinc-900">
      {thumbnail ? (
        <img 
          src={thumbnail} 
          alt={title}
          className="w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-500 to-yellow-500 flex items-center justify-center text-black font-bold text-lg">
            {title.charAt(0)}
          </div>
        </div>
      )}
      
      {/* 渐变遮罩 */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
      
      {/* 进度指示 */}
      {progress > 0 && (
        <div className="absolute bottom-2 left-2 right-2">
          <div className="flex items-center gap-2 text-xs text-white/80">
            <span>{progress}%</span>
            <div className="flex-1 h-1 bg-black/30 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
    
    {/* 内容区域 */}
    <div>
      <h3 className="font-semibold text-white group-hover:text-amber-400 transition-colors truncate">
        {title}
      </h3>
      {subtitle && (
        <p className="text-sm text-zinc-400 mt-1 truncate">
          {subtitle}
        </p>
      )}
      {lastModified && (
        <p className="text-xs text-zinc-500 mt-2">
          {lastModified}
        </p>
      )}
    </div>
  </Card>
));

ProjectCard.displayName = 'ProjectCard';

export default Card;