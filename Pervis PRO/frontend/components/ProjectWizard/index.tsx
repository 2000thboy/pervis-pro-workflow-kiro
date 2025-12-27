/**
 * 项目立项向导 - 主组件
 * Phase 5: 前端向导组件
 * 
 * 功能：
 * - 步骤导航和进度显示
 * - 完成度百分比显示
 * - AI 处理状态显示
 * - 步骤间自由跳转
 */

import React, { useEffect, useState } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Check,
  FileText,
  Users,
  Film,
  Image,
  CheckCircle,
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { WizardProvider, useWizard } from './WizardContext';
import { WizardStep, PROJECT_TYPE_CONFIG } from './types';
import { WizardStep1_BasicInfo } from './WizardStep1_BasicInfo';
import { WizardStep2_Script } from './WizardStep2_Script';
import { WizardStep3_Characters } from './WizardStep3_Characters';
import { WizardStep4_Scenes } from './WizardStep4_Scenes';
import { WizardStep5_References } from './WizardStep5_References';
import { WizardStep6_Confirm } from './WizardStep6_Confirm';
import { AgentStatusPanel } from './AgentStatusPanel';

// 步骤配置
const STEPS = [
  { step: WizardStep.BASIC_INFO, label: '基本信息', icon: FileText, description: '项目名称、类型、规格' },
  { step: WizardStep.SCRIPT, label: '剧本导入', icon: FileText, description: '上传或粘贴剧本' },
  { step: WizardStep.CHARACTERS, label: '角色设定', icon: Users, description: '确认角色和标签' },
  { step: WizardStep.SCENES, label: '场次规划', icon: Film, description: '场次列表和时长' },
  { step: WizardStep.REFERENCES, label: '参考资料', icon: Image, description: '上传参考图片' },
  { step: WizardStep.CONFIRM, label: '确认提交', icon: CheckCircle, description: '预览并创建项目' }
];

interface ProjectWizardProps {
  onClose: () => void;
  onComplete: (projectId: string) => void;
}

// 内部向导内容组件
const WizardContent: React.FC<ProjectWizardProps> = ({ onClose, onComplete }) => {
  const { state, setStep, validate, submit } = useWizard();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAgentPanel, setShowAgentPanel] = useState(false);

  const currentStepIndex = STEPS.findIndex(s => s.step === state.currentStep);
  const currentStepConfig = STEPS[currentStepIndex];

  // 计算步骤完成状态
  const getStepStatus = (step: WizardStep): 'completed' | 'current' | 'upcoming' => {
    if (step < state.currentStep) return 'completed';
    if (step === state.currentStep) return 'current';
    return 'upcoming';
  };

  // 导航到上一步
  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setStep(STEPS[currentStepIndex - 1].step);
    }
  };

  // 导航到下一步
  const handleNext = async () => {
    if (currentStepIndex < STEPS.length - 1) {
      setStep(STEPS[currentStepIndex + 1].step);
    }
  };

  // 提交项目
  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      const isValid = await validate();
      if (!isValid) {
        setIsSubmitting(false);
        return;
      }

      const projectId = await submit();
      if (projectId) {
        onComplete(projectId);
      }
    } catch (error) {
      console.error('提交失败:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // 渲染当前步骤内容
  const renderStepContent = () => {
    switch (state.currentStep) {
      case WizardStep.BASIC_INFO:
        return <WizardStep1_BasicInfo />;
      case WizardStep.SCRIPT:
        return <WizardStep2_Script />;
      case WizardStep.CHARACTERS:
        return <WizardStep3_Characters />;
      case WizardStep.SCENES:
        return <WizardStep4_Scenes />;
      case WizardStep.REFERENCES:
        return <WizardStep5_References />;
      case WizardStep.CONFIRM:
        return <WizardStep6_Confirm />;
      default:
        return null;
    }
  };

  // 检查是否有活跃的 Agent
  const hasActiveAgent = state.agentStatuses.some(
    a => a.status === 'working' || a.status === 'reviewing'
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="relative w-full max-w-6xl h-[90vh] bg-zinc-950 border border-zinc-800 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        
        {/* 头部 */}
        <header className="flex-shrink-0 h-16 px-6 flex items-center justify-between border-b border-zinc-800 bg-zinc-900/50">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Sparkles className="text-amber-500" size={20} />
              <h1 className="text-lg font-bold text-white">新建项目</h1>
            </div>
            {state.basicInfo.title && (
              <span className="text-sm text-zinc-500">· {state.basicInfo.title}</span>
            )}
          </div>
          
          <div className="flex items-center gap-4">
            {/* 完成度 */}
            <div className="flex items-center gap-2">
              <div className="w-24 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 transition-all duration-300"
                  style={{ width: `${state.completionPercentage}%` }}
                />
              </div>
              <span className="text-xs text-zinc-500">{Math.round(state.completionPercentage)}%</span>
            </div>

            {/* Agent 状态按钮 */}
            {state.agentStatuses.length > 0 && (
              <button
                onClick={() => setShowAgentPanel(!showAgentPanel)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                  hasActiveAgent 
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' 
                    : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                }`}
              >
                <Sparkles size={14} className={hasActiveAgent ? 'animate-pulse' : ''} />
                <span>AI 状态</span>
              </button>
            )}

            {/* 关闭按钮 */}
            <button
              onClick={onClose}
              className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </header>

        {/* 步骤导航 */}
        <nav className="flex-shrink-0 px-6 py-4 border-b border-zinc-800/50 bg-zinc-900/30">
          <div className="flex items-center justify-between">
            {STEPS.map((stepConfig, index) => {
              const status = getStepStatus(stepConfig.step);
              const Icon = stepConfig.icon;
              
              return (
                <React.Fragment key={stepConfig.step}>
                  <button
                    onClick={() => setStep(stepConfig.step)}
                    className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all ${
                      status === 'current'
                        ? 'bg-amber-500/20 border border-amber-500/30'
                        : status === 'completed'
                        ? 'bg-zinc-800/50 hover:bg-zinc-800'
                        : 'opacity-50 cursor-not-allowed'
                    }`}
                    disabled={status === 'upcoming'}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      status === 'current'
                        ? 'bg-amber-500 text-black'
                        : status === 'completed'
                        ? 'bg-emerald-500 text-white'
                        : 'bg-zinc-700 text-zinc-400'
                    }`}>
                      {status === 'completed' ? (
                        <Check size={16} />
                      ) : (
                        <Icon size={16} />
                      )}
                    </div>
                    <div className="text-left hidden lg:block">
                      <div className={`text-sm font-medium ${
                        status === 'current' ? 'text-amber-400' : 'text-zinc-300'
                      }`}>
                        {stepConfig.label}
                      </div>
                      <div className="text-xs text-zinc-500">{stepConfig.description}</div>
                    </div>
                  </button>
                  
                  {index < STEPS.length - 1 && (
                    <div className={`flex-1 h-px mx-2 ${
                      status === 'completed' ? 'bg-emerald-500' : 'bg-zinc-800'
                    }`} />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </nav>

        {/* 主内容区 */}
        <main className="flex-1 overflow-hidden flex">
          {/* 步骤内容 */}
          <div className="flex-1 overflow-y-auto p-6">
            {renderStepContent()}
          </div>

          {/* Agent 状态面板 */}
          {showAgentPanel && (
            <aside className="w-80 border-l border-zinc-800 bg-zinc-900/50 overflow-y-auto">
              <AgentStatusPanel onClose={() => setShowAgentPanel(false)} />
            </aside>
          )}
        </main>

        {/* 底部导航 */}
        <footer className="flex-shrink-0 h-16 px-6 flex items-center justify-between border-t border-zinc-800 bg-zinc-900/50">
          <button
            onClick={handlePrev}
            disabled={currentStepIndex === 0}
            className="flex items-center gap-2 px-4 py-2 text-sm text-zinc-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft size={16} />
            <span>上一步</span>
          </button>

          <div className="flex items-center gap-2 text-sm text-zinc-500">
            <span>步骤 {currentStepIndex + 1} / {STEPS.length}</span>
          </div>

          {state.currentStep === WizardStep.CONFIRM ? (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || state.validationErrors.some(e => e.severity === 'error')}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-black font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                  <span>创建中...</span>
                </>
              ) : (
                <>
                  <Check size={16} />
                  <span>创建项目</span>
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-black font-semibold rounded-lg transition-all"
            >
              <span>下一步</span>
              <ChevronRight size={16} />
            </button>
          )}
        </footer>

        {/* 验证错误提示 */}
        {state.validationErrors.filter(e => e.severity === 'error').length > 0 && (
          <div className="absolute bottom-20 left-6 right-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
              <div>
                <div className="text-sm font-medium text-red-400 mb-1">请修正以下问题</div>
                <ul className="text-xs text-red-300 space-y-1">
                  {state.validationErrors
                    .filter(e => e.severity === 'error')
                    .map((error, i) => (
                      <li key={i}>· {error.message}</li>
                    ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 导出的主组件（包含 Provider）
export const ProjectWizard: React.FC<ProjectWizardProps> = (props) => {
  return (
    <WizardProvider>
      <WizardContent {...props} />
    </WizardProvider>
  );
};

export default ProjectWizard;
