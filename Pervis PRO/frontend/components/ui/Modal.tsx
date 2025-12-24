import React, { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { Button } from './Button';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  showCloseButton?: boolean;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
  className?: string;
}

const sizeStyles = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-7xl'
};

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  size = 'lg',
  showCloseButton = true,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  className = ''
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const overlayRef = useRef<HTMLDivElement>(null);

  // 处理ESC键关闭
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeOnEscape, onClose]);

  // 处理body滚动锁定
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // 处理点击遮罩关闭
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === overlayRef.current) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 遮罩层 */}
      <div
        ref={overlayRef}
        className="absolute inset-0 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
        onClick={handleOverlayClick}
      />

      {/* 模态窗口 */}
      <div
        ref={modalRef}
        className={`
          relative w-full ${sizeStyles[size]} max-h-[90vh]
          bg-zinc-900/95 backdrop-blur-xl
          border border-zinc-700/50
          rounded-2xl shadow-2xl shadow-black/50
          animate-in zoom-in-95 fade-in duration-200
          ${className}
        `}
      >
        {/* 头部 */}
        {(title || subtitle || showCloseButton) && (
          <div className="flex items-start justify-between p-6 border-b border-zinc-800/50">
            <div className="flex-1 min-w-0">
              {title && (
                <h2 className="text-xl font-semibold text-white mb-1">
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="text-sm text-zinc-400">
                  {subtitle}
                </p>
              )}
            </div>

            {showCloseButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="ml-4 flex-shrink-0"
                icon={X}
              />
            )}
          </div>
        )}

        {/* 内容区域 */}
        <div className="flex-1 overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  );
};

// 模态窗口头部组件
export const ModalHeader: React.FC<{
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
}> = ({ title, subtitle, actions, children, className = '' }) => (
  <div className={`p-6 border-b border-zinc-800/50 ${className}`}>
    <div className="flex items-start justify-between">
      <div className="flex-1 min-w-0">
        {title && (
          <h2 className="text-xl font-semibold text-white mb-1">
            {title}
          </h2>
        )}
        {subtitle && (
          <p className="text-sm text-zinc-400">
            {subtitle}
          </p>
        )}
        {children}
      </div>

      {actions && (
        <div className="ml-4 flex-shrink-0">
          {actions}
        </div>
      )}
    </div>
  </div>
);

// 模态窗口内容组件
export const ModalContent: React.FC<{
  children: React.ReactNode;
  className?: string;
  scrollable?: boolean;
}> = ({ children, className = '', scrollable = true }) => (
  <div className={`
    p-6 
    ${scrollable ? 'overflow-y-auto max-h-[60vh]' : ''}
    ${className}
  `}>
    {children}
  </div>
);

// 模态窗口底部组件
export const ModalFooter: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div className={`
    p-6 border-t border-zinc-800/50
    flex items-center justify-end gap-3
    ${className}
  `}>
    {children}
  </div>
);

export default Modal;