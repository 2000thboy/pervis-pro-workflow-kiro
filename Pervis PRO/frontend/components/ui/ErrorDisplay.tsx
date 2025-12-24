import React, { useState } from 'react';
import { 
  AlertTriangle, 
  XCircle, 
  Info, 
  ChevronDown, 
  ChevronUp, 
  Copy, 
  ExternalLink,
  RefreshCw
} from 'lucide-react';
import { Button } from './Button';
import { Card } from './Card';

export interface UserFriendlyError {
  error_code: string;
  title: string;
  message: string;
  solutions: string[];
  documentation_link?: string;
  is_recoverable: boolean;
  technical_details?: string;
  timestamp?: string;
}

interface ErrorDisplayProps {
  error: UserFriendlyError;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
  showTechnicalDetails?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  onDismiss,
  className = '',
  showTechnicalDetails = false
}) => {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const getErrorIcon = () => {
    switch (error.error_code.split('_')[0]) {
      case 'FFMPEG':
        return <XCircle className="w-6 h-6 text-red-500" />;
      case 'VALIDATION':
        return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
      case 'SYSTEM':
        return <AlertTriangle className="w-6 h-6 text-orange-500" />;
      default:
        return <Info className="w-6 h-6 text-blue-500" />;
    }
  };

  const getErrorColor = () => {
    if (error.is_recoverable) {
      return 'border-yellow-200 bg-yellow-50';
    }
    return 'border-red-200 bg-red-50';
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const formatTechnicalDetails = () => {
    const details = [
      `错误代码: ${error.error_code}`,
      `时间: ${error.timestamp || new Date().toISOString()}`,
      `可恢复: ${error.is_recoverable ? '是' : '否'}`,
      error.technical_details ? `技术详情: ${error.technical_details}` : null
    ].filter(Boolean).join('\n');
    
    return details;
  };

  return (
    <Card className={`${getErrorColor()} ${className}`}>
      <div className="p-4">
        {/* 错误标题和图标 */}
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            {getErrorIcon()}
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-1">
                {error.title}
              </h3>
              <p className="text-gray-700 mb-3">
                {error.message}
              </p>
            </div>
          </div>
          
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </Button>
          )}
        </div>

        {/* 解决方案 */}
        {error.solutions.length > 0 && (
          <div className="mb-4">
            <h4 className="font-medium text-gray-900 mb-2">解决方案:</h4>
            <ul className="space-y-2">
              {error.solutions.map((solution, index) => (
                <li key={index} className="flex items-start">
                  <span className="inline-block w-6 h-6 bg-blue-100 text-blue-800 text-xs font-medium rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                    {index + 1}
                  </span>
                  <span className="text-gray-700">{solution}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex items-center justify-between">
          <div className="flex space-x-2">
            {error.is_recoverable && onRetry && (
              <Button
                variant="primary"
                size="sm"
                onClick={onRetry}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                重试
              </Button>
            )}
            
            {error.documentation_link && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => window.open(error.documentation_link, '_blank')}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                查看文档
              </Button>
            )}
          </div>

          {(showTechnicalDetails || error.technical_details) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              技术详情
              {expanded ? (
                <ChevronUp className="w-4 h-4 ml-2" />
              ) : (
                <ChevronDown className="w-4 h-4 ml-2" />
              )}
            </Button>
          )}
        </div>

        {/* 技术详情 */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="bg-gray-900 text-gray-300 p-4 rounded-lg font-mono text-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400">技术详情</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(formatTechnicalDetails())}
                  className="text-gray-400 hover:text-gray-200"
                >
                  <Copy className="w-4 h-4" />
                  {copied ? '已复制' : '复制'}
                </Button>
              </div>
              <pre className="whitespace-pre-wrap text-xs">
                {formatTechnicalDetails()}
              </pre>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

// 错误通知组件
interface ErrorNotificationProps {
  errors: UserFriendlyError[];
  onRetry?: (errorCode: string) => void;
  onDismiss?: (errorCode: string) => void;
  className?: string;
}

export const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  errors,
  onRetry,
  onDismiss,
  className = ''
}) => {
  if (errors.length === 0) return null;

  return (
    <div className={`space-y-3 ${className}`}>
      {errors.map((error) => (
        <ErrorDisplay
          key={error.error_code}
          error={error}
          onRetry={() => onRetry?.(error.error_code)}
          onDismiss={() => onDismiss?.(error.error_code)}
        />
      ))}
    </div>
  );
};

export default ErrorDisplay;