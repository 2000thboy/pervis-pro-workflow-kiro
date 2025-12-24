import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

// Button变体类型
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'outline';
export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
  children?: React.ReactNode;
}

// 样式映射
const variantStyles: Record<ButtonVariant, string> = {
  primary: `
    bg-gradient-to-r from-amber-500 to-yellow-500 
    hover:from-amber-400 hover:to-yellow-400 
    active:from-amber-600 active:to-yellow-600
    text-black font-semibold
    shadow-lg shadow-amber-500/25 
    hover:shadow-xl hover:shadow-amber-500/30
    border border-amber-400/50
    hover:border-amber-300
  `,
  
  secondary: `
    bg-zinc-800 hover:bg-zinc-700 active:bg-zinc-900
    text-zinc-200 hover:text-white
    border border-zinc-700 hover:border-zinc-600
    shadow-md shadow-black/20
  `,
  
  ghost: `
    bg-transparent hover:bg-zinc-800/50 active:bg-zinc-800/70
    text-zinc-400 hover:text-zinc-200
    border border-transparent hover:border-zinc-700
  `,
  
  outline: `
    bg-transparent hover:bg-amber-500/10 active:bg-amber-500/20
    text-amber-500 hover:text-amber-400
    border border-amber-500/50 hover:border-amber-400
  `,
  
  danger: `
    bg-gradient-to-r from-red-600 to-red-500
    hover:from-red-500 hover:to-red-400
    active:from-red-700 active:to-red-600
    text-white font-semibold
    shadow-lg shadow-red-500/25
    hover:shadow-xl hover:shadow-red-500/30
    border border-red-500/50
  `,
  
  success: `
    bg-gradient-to-r from-emerald-600 to-emerald-500
    hover:from-emerald-500 hover:to-emerald-400
    active:from-emerald-700 active:to-emerald-600
    text-white font-semibold
    shadow-lg shadow-emerald-500/25
    hover:shadow-xl hover:shadow-emerald-500/30
    border border-emerald-500/50
  `
};

const sizeStyles: Record<ButtonSize, string> = {
  xs: 'px-2 py-1 text-xs rounded-md min-h-[24px]',
  sm: 'px-3 py-1.5 text-sm rounded-md min-h-[32px]',
  md: 'px-4 py-2 text-sm rounded-lg min-h-[40px]',
  lg: 'px-6 py-3 text-base rounded-lg min-h-[48px]',
  xl: 'px-8 py-4 text-lg rounded-xl min-h-[56px]'
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon: Icon,
  iconPosition = 'left',
  fullWidth = false,
  disabled,
  className = '',
  children,
  ...props
}, ref) => {
  const isDisabled = disabled || loading;
  
  const baseStyles = `
    inline-flex items-center justify-center gap-2
    font-medium tracking-wide
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:ring-offset-2 focus:ring-offset-black
    disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
    relative overflow-hidden
    select-none
  `;
  
  const widthStyles = fullWidth ? 'w-full' : '';
  
  const combinedClassName = [
    baseStyles,
    variantStyles[variant],
    sizeStyles[size],
    widthStyles,
    className
  ].join(' ').replace(/\s+/g, ' ').trim();

  return (
    <button
      ref={ref}
      className={combinedClassName}
      disabled={isDisabled}
      {...props}
    >
      {/* 悬停光效 */}
      <div className="absolute inset-0 bg-white/10 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-500 skew-x-12 opacity-0 hover:opacity-100" />
      
      {/* 内容 */}
      <div className="relative flex items-center gap-2">
        {loading ? (
          <Loader2 size={size === 'xs' ? 12 : size === 'sm' ? 14 : size === 'lg' ? 18 : size === 'xl' ? 20 : 16} className="animate-spin" />
        ) : Icon && iconPosition === 'left' ? (
          <Icon size={size === 'xs' ? 12 : size === 'sm' ? 14 : size === 'lg' ? 18 : size === 'xl' ? 20 : 16} />
        ) : null}
        
        {children && <span>{children}</span>}
        
        {Icon && iconPosition === 'right' && !loading && (
          <Icon size={size === 'xs' ? 12 : size === 'sm' ? 14 : size === 'lg' ? 18 : size === 'xl' ? 20 : 16} />
        )}
      </div>
    </button>
  );
});

Button.displayName = 'Button';

// 预设按钮组件
export const PrimaryButton = (props: Omit<ButtonProps, 'variant'>) => (
  <Button variant="primary" {...props} />
);

export const SecondaryButton = (props: Omit<ButtonProps, 'variant'>) => (
  <Button variant="secondary" {...props} />
);

export const GhostButton = (props: Omit<ButtonProps, 'variant'>) => (
  <Button variant="ghost" {...props} />
);

export const DangerButton = (props: Omit<ButtonProps, 'variant'>) => (
  <Button variant="danger" {...props} />
);

export const SuccessButton = (props: Omit<ButtonProps, 'variant'>) => (
  <Button variant="success" {...props} />
);

export const OutlineButton = (props: Omit<ButtonProps, 'variant'>) => (
  <Button variant="outline" {...props} />
);

export default Button;