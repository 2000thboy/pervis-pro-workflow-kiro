/**
 * 数据类型指示器
 * 明确标注静态案例和动态数据
 */

import React from 'react';
import { 
  Database, 
  Sparkles, 
  FileText, 
  HelpCircle,
  Info
} from 'lucide-react';

export type DataType = 'static' | 'dynamic' | 'user' | 'ai_generated' | 'template';

interface DataTypeIndicatorProps {
  type: DataType;
  label?: string;
  showTooltip?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const typeConfig: Record<DataType, {
  icon: React.ReactNode;
  label: string;
  color: string;
  bgColor: string;
  description: string;
}> = {
  static: {
    icon: <FileText size={12} />,
    label: '静态案例',
    color: 'text-zinc-400',
    bgColor: 'bg-zinc-800',
    description: '预设的示例数据，仅供参考'
  },
  dynamic: {
    icon: <Database size={12} />,
    label: '动态数据',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/20',
    description: '基于实际项目数据生成'
  },
  user: {
    icon: <FileText size={12} />,
    label: '用户输入',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    description: '由用户手动输入的内容'
  },
  ai_generated: {
    icon: <Sparkles size={12} />,
    label: 'AI 生成',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
    description: '由 AI Agent 自动生成'
  },
  template: {
    icon: <FileText size={12} />,
    label: '模板预设',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    description: '来自项目模板的默认值'
  }
};

export const DataTypeIndicator: React.FC<DataTypeIndicatorProps> = ({
  type,
  label,
  showTooltip = true,
  size = 'sm',
  className = ''
}) => {
  const config = typeConfig[type];
  
  const sizeClasses = {
    sm: 'text-[10px] px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2 py-1 gap-1.5',
    lg: 'text-sm px-3 py-1.5 gap-2'
  };

  return (
    <div className={`relative group inline-flex ${className}`}>
      <span 
        className={`inline-flex items-center rounded ${sizeClasses[size]} ${config.bgColor} ${config.color}`}
      >
        {config.icon}
        <span>{label || config.label}</span>
      </span>
      
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-800 border border-zinc-700 rounded text-[10px] text-zinc-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
          {config.description}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-zinc-800"></div>
        </div>
      )}
    </div>
  );
};

/**
 * 数据来源标签组
 * 用于显示多个数据来源
 */
interface DataSourceBadgesProps {
  sources: DataType[];
  size?: 'sm' | 'md' | 'lg';
}

export const DataSourceBadges: React.FC<DataSourceBadgesProps> = ({
  sources,
  size = 'sm'
}) => {
  return (
    <div className="flex flex-wrap gap-1">
      {sources.map((source, index) => (
        <DataTypeIndicator key={index} type={source} size={size} />
      ))}
    </div>
  );
};

/**
 * 内容来源说明
 * 用于在内容旁边显示来源信息
 */
interface ContentSourceProps {
  type: DataType;
  agentName?: string;
  timestamp?: string;
  className?: string;
}

export const ContentSource: React.FC<ContentSourceProps> = ({
  type,
  agentName,
  timestamp,
  className = ''
}) => {
  const config = typeConfig[type];
  
  return (
    <div className={`flex items-center gap-2 text-[10px] text-zinc-500 ${className}`}>
      <DataTypeIndicator type={type} showTooltip={false} />
      {agentName && (
        <>
          <span>·</span>
          <span>{agentName}</span>
        </>
      )}
      {timestamp && (
        <>
          <span>·</span>
          <span>{timestamp}</span>
        </>
      )}
    </div>
  );
};

/**
 * 数据类型图例
 * 用于解释页面上使用的数据类型标记
 */
interface DataTypeLegendProps {
  types?: DataType[];
  compact?: boolean;
}

export const DataTypeLegend: React.FC<DataTypeLegendProps> = ({
  types = ['static', 'dynamic', 'user', 'ai_generated'],
  compact = false
}) => {
  return (
    <div className={`${compact ? 'flex flex-wrap gap-3' : 'space-y-2'}`}>
      {compact ? (
        types.map(type => (
          <DataTypeIndicator key={type} type={type} size="sm" />
        ))
      ) : (
        <>
          <div className="flex items-center gap-2 text-xs text-zinc-500 mb-2">
            <Info size={12} />
            <span>数据来源说明</span>
          </div>
          {types.map(type => {
            const config = typeConfig[type];
            return (
              <div key={type} className="flex items-center gap-2">
                <DataTypeIndicator type={type} showTooltip={false} />
                <span className="text-[10px] text-zinc-500">{config.description}</span>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
};

export default DataTypeIndicator;
