/**
 * TaskList - 任务列表组件
 * 
 * 显示当前运行的后台任务和 Agent 状态
 */

import React from 'react';
import type { BackgroundTask, AgentStatus } from './types';
import {
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Film,
  Download,
  Sparkles,
  Image,
  User,
  Palette,
  FileText,
  Eye
} from 'lucide-react';

interface TaskListProps {
  tasks: BackgroundTask[];
  agents: AgentStatus[];
}

// 任务类型图标
const getTaskIcon = (type: string) => {
  switch (type) {
    case 'render': return <Film size={14} className="text-purple-400" />;
    case 'export': return <Download size={14} className="text-blue-400" />;
    case 'ai_generate': return <Sparkles size={14} className="text-yellow-400" />;
    case 'asset_process': return <Image size={14} className="text-green-400" />;
    default: return <Clock size={14} className="text-zinc-400" />;
  }
};

// Agent 类型图标
const getAgentIcon = (agentType: string) => {
  switch (agentType) {
    case 'script_agent': return <FileText size={14} className="text-blue-400" />;
    case 'art_agent': return <Palette size={14} className="text-pink-400" />;
    case 'director_agent': return <Eye size={14} className="text-purple-400" />;
    case 'market_agent': return <User size={14} className="text-green-400" />;
    default: return <Sparkles size={14} className="text-yellow-400" />;
  }
};

// Agent 名称映射
const agentNames: Record<string, string> = {
  script_agent: '编剧 Agent',
  art_agent: '美术 Agent',
  director_agent: '导演 Agent',
  market_agent: '市场 Agent',
  storyboard_agent: '分镜 Agent',
  system_agent: '系统 Agent'
};

// 状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'running':
    case 'working': return 'text-blue-400';
    case 'reviewing': return 'text-yellow-400';
    case 'completed': return 'text-green-400';
    case 'failed': return 'text-red-400';
    default: return 'text-zinc-400';
  }
};

// 单个任务项
function TaskItem({ task }: { task: BackgroundTask }) {
  const isRunning = task.status === 'running';
  
  return (
    <div className="px-4 py-3 border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/30 transition-colors">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getTaskIcon(task.type)}
          <span className="text-xs font-medium text-white">{task.name}</span>
        </div>
        <div className="flex items-center gap-2">
          {isRunning ? (
            <Loader2 size={12} className="text-blue-400 animate-spin" />
          ) : task.status === 'completed' ? (
            <CheckCircle size={12} className="text-green-400" />
          ) : task.status === 'failed' ? (
            <XCircle size={12} className="text-red-400" />
          ) : (
            <Clock size={12} className="text-zinc-500" />
          )}
          <span className={`text-[10px] ${getStatusColor(task.status)}`}>
            {task.status === 'running' ? `${task.progress}%` : 
             task.status === 'completed' ? '完成' :
             task.status === 'failed' ? '失败' : '等待中'}
          </span>
        </div>
      </div>
      
      {/* 进度条 */}
      {isRunning && (
        <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${task.progress}%` }}
          />
        </div>
      )}
      
      {/* 预计时间 */}
      {isRunning && task.estimatedDuration && (
        <div className="mt-1 text-[10px] text-zinc-500">
          预计剩余: {Math.ceil(task.estimatedDuration * (1 - task.progress / 100))}秒
        </div>
      )}
    </div>
  );
}

// 单个 Agent 状态项
function AgentItem({ agent }: { agent: AgentStatus }) {
  return (
    <div className="px-4 py-3 border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/30 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getAgentIcon(agent.agentType)}
          <span className="text-xs font-medium text-white">
            {agentNames[agent.agentType] || agent.agentType}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {agent.status === 'working' || agent.status === 'reviewing' ? (
            <Loader2 size={12} className={getStatusColor(agent.status)} style={{ animation: 'spin 1s linear infinite' }} />
          ) : agent.status === 'completed' ? (
            <CheckCircle size={12} className="text-green-400" />
          ) : (
            <XCircle size={12} className="text-red-400" />
          )}
          <span className={`text-[10px] ${getStatusColor(agent.status)}`}>
            {agent.status === 'working' ? '工作中' :
             agent.status === 'reviewing' ? '审核中' :
             agent.status === 'completed' ? '完成' : '失败'}
          </span>
        </div>
      </div>
      
      {/* Agent 消息 */}
      {agent.message && (
        <div className="mt-1 text-[10px] text-zinc-500 truncate">
          {agent.message}
        </div>
      )}
    </div>
  );
}

export function TaskList({ tasks, agents }: TaskListProps) {
  const hasContent = tasks.length > 0 || agents.length > 0;
  
  if (!hasContent) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
        <CheckCircle size={32} className="mb-3 opacity-30" />
        <span className="text-xs">暂无运行中的任务</span>
        <span className="text-[10px] opacity-50 mt-1">系统空闲中</span>
      </div>
    );
  }

  return (
    <div>
      {/* Agent 状态 */}
      {agents.length > 0 && (
        <div>
          <div className="px-4 py-2 text-[10px] font-bold text-zinc-500 uppercase tracking-wider bg-zinc-800/30">
            Agent 状态
          </div>
          {agents.map((agent, i) => (
            <AgentItem key={`${agent.agentType}-${i}`} agent={agent} />
          ))}
        </div>
      )}
      
      {/* 后台任务 */}
      {tasks.length > 0 && (
        <div>
          <div className="px-4 py-2 text-[10px] font-bold text-zinc-500 uppercase tracking-wider bg-zinc-800/30">
            后台任务
          </div>
          {tasks.map(task => (
            <TaskItem key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
