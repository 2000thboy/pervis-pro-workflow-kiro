import React, { forwardRef, useState } from 'react';
import { Eye, EyeOff, AlertCircle, Check } from 'lucide-react';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  description?: string;
  error?: string;
  success?: string;
  leftIcon?: React.ComponentType<{ size?: number; className?: string }>;
  rightIcon?: React.ComponentType<{ size?: number; className?: string }>;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'filled' | 'outlined';
  fullWidth?: boolean;
}

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  description?: string;
  error?: string;
  success?: string;
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
  fullWidth?: boolean;
}

const sizeStyles = {
  sm: 'px-3 py-2 text-sm min-h-[36px]',
  md: 'px-4 py-2.5 text-sm min-h-[42px]',
  lg: 'px-4 py-3 text-base min-h-[48px]'
};

const variantStyles = {
  default: `
    bg-zinc-900/50 backdrop-blur-sm
    border border-zinc-700/50
    focus:border-amber-500/50 focus:bg-zinc-900/70
  `,
  
  filled: `
    bg-zinc-800/80
    border border-transparent
    focus:border-amber-500/50 focus:bg-zinc-800
  `,
  
  outlined: `
    bg-transparent
    border border-zinc-600
    focus:border-amber-500 focus:bg-zinc-900/30
  `
};

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  description,
  error,
  success,
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  size = 'md',
  variant = 'default',
  fullWidth = true,
  type = 'text',
  className = '',
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  
  const isPassword = type === 'password';
  const inputType = isPassword && showPassword ? 'text' : type;
  
  const hasError = !!error;
  const hasSuccess = !!success && !hasError;
  
  const baseStyles = `
    w-full rounded-lg
    text-white placeholder-zinc-500
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:ring-offset-2 focus:ring-offset-black
    disabled:opacity-50 disabled:cursor-not-allowed
  `;
  
  const stateStyles = hasError 
    ? 'border-red-500/50 focus:border-red-500 focus:ring-red-500/30'
    : hasSuccess
    ? 'border-emerald-500/50 focus:border-emerald-500 focus:ring-emerald-500/30'
    : '';
  
  const widthStyles = fullWidth ? 'w-full' : '';
  
  const inputClassName = [
    baseStyles,
    variantStyles[variant],
    sizeStyles[size],
    stateStyles,
    LeftIcon ? 'pl-10' : '',
    (RightIcon || isPassword) ? 'pr-10' : '',
    className
  ].join(' ').replace(/\s+/g, ' ').trim();

  return (
    <div className={`space-y-2 ${widthStyles}`}>
      {/* 标签 */}
      {label && (
        <label className="block text-sm font-medium text-zinc-300">
          {label}
        </label>
      )}
      
      {/* 输入框容器 */}
      <div className="relative">
        {/* 左侧图标 */}
        {LeftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500">
            <LeftIcon size={16} />
          </div>
        )}
        
        {/* 输入框 */}
        <input
          ref={ref}
          type={inputType}
          className={inputClassName}
          onFocus={(e) => {
            setIsFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            props.onBlur?.(e);
          }}
          {...props}
        />
        
        {/* 右侧图标 */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {/* 状态图标 */}
          {hasError && (
            <AlertCircle size={16} className="text-red-500" />
          )}
          {hasSuccess && (
            <Check size={16} className="text-emerald-500" />
          )}
          
          {/* 密码切换 */}
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          )}
          
          {/* 自定义右侧图标 */}
          {RightIcon && !isPassword && (
            <RightIcon size={16} className="text-zinc-500" />
          )}
        </div>
        
        {/* 焦点指示器 */}
        {isFocused && (
          <div className="absolute inset-0 rounded-lg border-2 border-amber-500/30 pointer-events-none animate-pulse" />
        )}
      </div>
      
      {/* 描述文本 */}
      {description && !error && !success && (
        <p className="text-xs text-zinc-500">
          {description}
        </p>
      )}
      
      {/* 错误信息 */}
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <AlertCircle size={12} />
          {error}
        </p>
      )}
      
      {/* 成功信息 */}
      {success && !error && (
        <p className="text-xs text-emerald-400 flex items-center gap-1">
          <Check size={12} />
          {success}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  label,
  description,
  error,
  success,
  resize = 'vertical',
  fullWidth = true,
  className = '',
  ...props
}, ref) => {
  const [isFocused, setIsFocused] = useState(false);
  
  const hasError = !!error;
  const hasSuccess = !!success && !hasError;
  
  const baseStyles = `
    w-full px-4 py-3 rounded-lg
    bg-zinc-900/50 backdrop-blur-sm
    border border-zinc-700/50
    text-white placeholder-zinc-500
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:ring-offset-2 focus:ring-offset-black
    focus:border-amber-500/50 focus:bg-zinc-900/70
    disabled:opacity-50 disabled:cursor-not-allowed
    min-h-[100px]
  `;
  
  const resizeStyles = {
    none: 'resize-none',
    vertical: 'resize-y',
    horizontal: 'resize-x',
    both: 'resize'
  };
  
  const stateStyles = hasError 
    ? 'border-red-500/50 focus:border-red-500 focus:ring-red-500/30'
    : hasSuccess
    ? 'border-emerald-500/50 focus:border-emerald-500 focus:ring-emerald-500/30'
    : '';
  
  const widthStyles = fullWidth ? 'w-full' : '';
  
  const textareaClassName = [
    baseStyles,
    resizeStyles[resize],
    stateStyles,
    className
  ].join(' ').replace(/\s+/g, ' ').trim();

  return (
    <div className={`space-y-2 ${widthStyles}`}>
      {/* 标签 */}
      {label && (
        <label className="block text-sm font-medium text-zinc-300">
          {label}
        </label>
      )}
      
      {/* 文本域容器 */}
      <div className="relative">
        <textarea
          ref={ref}
          className={textareaClassName}
          onFocus={(e) => {
            setIsFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            props.onBlur?.(e);
          }}
          {...props}
        />
        
        {/* 状态图标 */}
        <div className="absolute top-3 right-3">
          {hasError && (
            <AlertCircle size={16} className="text-red-500" />
          )}
          {hasSuccess && (
            <Check size={16} className="text-emerald-500" />
          )}
        </div>
        
        {/* 焦点指示器 */}
        {isFocused && (
          <div className="absolute inset-0 rounded-lg border-2 border-amber-500/30 pointer-events-none animate-pulse" />
        )}
      </div>
      
      {/* 描述文本 */}
      {description && !error && !success && (
        <p className="text-xs text-zinc-500">
          {description}
        </p>
      )}
      
      {/* 错误信息 */}
      {error && (
        <p className="text-xs text-red-400 flex items-center gap-1">
          <AlertCircle size={12} />
          {error}
        </p>
      )}
      
      {/* 成功信息 */}
      {success && !error && (
        <p className="text-xs text-emerald-400 flex items-center gap-1">
          <Check size={12} />
          {success}
        </p>
      )}
    </div>
  );
});

Textarea.displayName = 'Textarea';

export default Input;