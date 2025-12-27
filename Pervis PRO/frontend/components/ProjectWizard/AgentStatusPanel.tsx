/**
 * Agent 状态面板
 * 显示当前活跃的 Agent 列表和工作状态
 */

import React from 'react';
import { 
  X, 
  Sparkles, 
  CheckCircle, 
  AlertCircle, 
  Loader2,
  FileText,
  Palette,
  Eye,
  ClipboardList,
  Film,
  TrendingUp,
  Shield
} from 'lucide-react';
import { useWizard } from './WizardContext';

interface AgentStatusPanelProps {
  onClose: () => void;
}

// Agent 配置
const AGENT_CONFIG: Record<string, {
  name: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
  description: string;
}> = {
  'Script_Agent': {
    name: '编剧 Agent',
    icon: FileText,
    color: 'text-blue-400',
    description: '剧本解析、Logline/Synopsis 生成'
  },
  'Art_Agent': {
    name: '美术 Agent',
    icon: Palette,
    color: 'text-purple-400',
    description: '素材分类、标签生成'
  },
  'Director_Agent': {
    name: '导演 Agent',
    icon: Eye,
    color: 'text-amber-400',
    description: '内容审核、风格一致性检查'
  },
  'PM_Agent': {
    name: '项目管理 Agent',
    icon: ClipboardList,
    color: 'text-green-400',
    description: '版本管理、决策记录'
  },
  'Storyboard_Agent': {
    name: '故事板 Agent',
    icon: Film,
    color: 'text-pink-400',
    description: '素材召回、候选推荐'
  },
  'Market_Agent': {
    name: '市场分析 Agent',
    icon: TrendingUp,
    color: 'text-cyan-400',
    description: '市场定位、受众分析'
  },
  'System_Agent': {
    name: '系统校验 Agent',
    icon: Shield,
    color: 'text-red-400',
    description: '标签一致性、导出前校验'
  }
};

export const AgentStatusPanel: React.FC<AgentStatusPanelProps> = ({ onClose }) => {
  const { state } = useWizard();
  const { agentStatuses } = state;

  // 状态图标
  const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
      case 'working':
        return <Loader2 size={14} className="text-amber-400 animate-spin" />;
      case 'reviewing':
        return <Eye size={14} className="text-blue-400 animate-pulse" />;
      case 'completed':
        return <CheckCircle size={14} className="text-emerald-400" />;
      case 'failed':
        return <AlertCircle size={14} className="text-red-400" />;
      default:
        return <div className="w-3.5 h-3.5 rounded-full bg-zinc-600" />;
    }
  };

  // 状态标签
  const statusLabels: Record<string, string> = {
    idle: '待命',
    working: '工作中',
    reviewing: '审核中',
    completed: '已完成',
    failed: '失败'
  };

  return (
    <div className="h-full flex flex-col">
      {/* 头部 */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Sparkles className="text-amber-500" size={18} />
          <span className="text-sm font-medium text-white">AI Agent 状态</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Agent 列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {agentStatuses.length === 0 ? (
          <div className="text-center py-8">
            <Sparkles className="mx-auto text-zinc-700 mb-3" size={32} />
            <div className="text-sm text-zinc-500">暂无活跃的 Agent</div>
            <div className="text-xs text-zinc-600 mt-1">执行操作时 Agent 会自动启动</div>
          </div>
        ) : (
          agentStatuses.map((agent) => {
            const config = AGENT_CONFIG[agent.agentName] || {
              name: agent.agentName,
              icon: Sparkles,
              color: 'text-zinc-400',
              description: ''
            };
            const Icon = config.icon;

            return (
              <div
                key={agent.agentName}
                className={`p-3 rounded-lg border transition-colors ${
                  agent.status === 'working' || agent.status === 'reviewing'
                    ? 'bg-amber-500/5 border-amber-500/30'
                    : agent.status === 'completed'
                    ? 'bg-emerald-500/5 border-emerald-500/30'
                    : agent.status === 'failed'
                    ? 'bg-red-500/5 border-red-500/30'
                    : 'bg-zinc-900/50 border-zinc-800'
                }`}
              >
                {/* Agent 头部 */}
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-1.5 rounded-lg bg-zinc-800 ${config.color}`}>
                    <Icon size={16} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white">{config.name}</div>
                    <div className="text-xs text-zinc-500 truncate">{config.description}</div>
                  </div>
                  <StatusIcon status={agent.status} />
                </div>

                {/* 状态信息 */}
                <div className="flex items-center justify-between text-xs">
                  <span className={`px-2 py-0.5 rounded ${
                    agent.status === 'working' ? 'bg-amber-500/20 text-amber-400' :
                    agent.status === 'reviewing' ? 'bg-blue-500/20 text-blue-400' :
                    agent.status === 'completed' ? 'bg-emerald-500/20 text-emerald-400' :
                    agent.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                    'bg-zinc-800 text-zinc-500'
                  }`}>
                    {statusLabels[agent.status] || agent.status}
                  </span>
                  {agent.progress > 0 && agent.progress < 100 && (
                    <span className="text-zinc-500">{agent.progress}%</span>
                  )}
                </div>

                {/* 消息 */}
                {agent.message && (
                  <div className="mt-2 text-xs text-zinc-400 truncate">
                    {agent.message}
                  </div>
                )}

                {/* 进度条 */}
                {(agent.status === 'working' || agent.status === 'reviewing') && (
                  <div className="mt-2 h-1 bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full transition-all duration-300 ${
                        agent.status === 'reviewing' ? 'bg-blue-500' : 'bg-amber-500'
                      }`}
                      style={{ width: `${agent.progress}%` }}
                    />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* 底部说明 */}
      <div className="p-4 border-t border-zinc-800">
        <div className="text-xs text-zinc-500 space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-500" />
            <span>工作中 - Agent 正在处理任务</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            <span>审核中 - Director_Agent 审核输出</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>已完成 - 任务成功完成</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentStatusPanel;
