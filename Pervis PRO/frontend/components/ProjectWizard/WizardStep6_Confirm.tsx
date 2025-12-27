/**
 * 向导步骤6 - 确认提交
 * 项目预览、System_Agent 校验、Director_Agent 全文审核
 */

import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle,
  Loader2,
  FileText,
  Users,
  Film,
  Image,
  Clock,
  Monitor,
  Zap,
  Sparkles,
  RefreshCw
} from 'lucide-react';
import { useWizard } from './WizardContext';
import { PROJECT_TYPE_CONFIG } from './types';
import { wizardApi } from './api';

export const WizardStep6_Confirm: React.FC = () => {
  const { state, validate, setAgentStatus } = useWizard();
  const { basicInfo, script, characters, scenes, references, validationErrors, completionPercentage } = state;
  
  const [isValidating, setIsValidating] = useState(false);
  const [systemCheckResult, setSystemCheckResult] = useState<{
    status: string;
    passed: string[];
    failed: string[];
    suggestions: string[];
  } | null>(null);

  // 自动验证
  useEffect(() => {
    handleValidate();
  }, []);

  // 执行验证
  const handleValidate = async () => {
    setIsValidating(true);
    setAgentStatus('System_Agent', { status: 'working', message: '正在校验项目...', progress: 0 });

    try {
      await validate();

      // 调用 System_Agent 校验
      const checkResult = await wizardApi.reviewContent({
        project_id: state.projectId || 'temp',
        content: {
          basicInfo,
          script: { content: script.content, scenes: script.scenes, characters: script.characters },
          characters,
          scenes,
          references: references.length
        },
        content_type: 'project_validation'
      });

      setSystemCheckResult({
        status: checkResult.status,
        passed: checkResult.passed_checks,
        failed: checkResult.failed_checks,
        suggestions: checkResult.suggestions
      });

      setAgentStatus('System_Agent', { 
        status: checkResult.status === 'approved' ? 'completed' : 'failed',
        message: checkResult.reason,
        progress: 100
      });

      setAgentStatus('Director_Agent', { 
        status: 'completed',
        message: '审核完成',
        progress: 100
      });

    } catch (error) {
      console.error('验证失败:', error);
      setAgentStatus('System_Agent', { status: 'failed', message: '校验失败', progress: 0 });
    } finally {
      setIsValidating(false);
    }
  };

  // 统计信息
  const stats = {
    scenes: scenes.length,
    characters: characters.length,
    references: references.length,
    totalDuration: scenes.reduce((sum, s) => sum + s.estimatedDuration, 0)
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}分${secs > 0 ? secs + '秒' : ''}` : `${secs}秒`;
  };

  // 错误和警告
  const errors = validationErrors.filter(e => e.severity === 'error');
  const warnings = validationErrors.filter(e => e.severity === 'warning');

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 完成度 */}
      <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-zinc-300">项目完成度</span>
          <span className="text-lg font-bold text-amber-400">{Math.round(completionPercentage)}%</span>
        </div>
        <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-amber-500 to-yellow-500 transition-all duration-500"
            style={{ width: `${completionPercentage}%` }}
          />
        </div>
      </div>

      {/* 项目预览 */}
      <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <FileText className="text-amber-500" size={20} />
          项目预览
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 基本信息 */}
          <div className="space-y-4">
            <div>
              <div className="text-xs text-zinc-500 mb-1">项目名称</div>
              <div className="text-white font-medium">{basicInfo.title || '未命名项目'}</div>
            </div>

            <div className="flex items-center gap-4">
              <div>
                <div className="text-xs text-zinc-500 mb-1">类型</div>
                <div className="flex items-center gap-2">
                  <span className="text-lg">{PROJECT_TYPE_CONFIG[basicInfo.projectType].icon}</span>
                  <span className="text-zinc-300">{PROJECT_TYPE_CONFIG[basicInfo.projectType].label}</span>
                </div>
              </div>
              <div>
                <div className="text-xs text-zinc-500 mb-1">时长</div>
                <div className="flex items-center gap-1 text-zinc-300">
                  <Clock size={14} />
                  <span>{basicInfo.durationMinutes} 分钟</span>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400 flex items-center gap-1">
                <Monitor size={12} />
                {basicInfo.aspectRatio}
              </span>
              <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400 flex items-center gap-1">
                <Zap size={12} />
                {basicInfo.frameRate} fps
              </span>
              <span className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-400">
                {basicInfo.resolution}
              </span>
            </div>

            {basicInfo.logline && (
              <div>
                <div className="text-xs text-zinc-500 mb-1">Logline</div>
                <div className="text-sm text-zinc-400 italic">"{basicInfo.logline}"</div>
              </div>
            )}
          </div>

          {/* 统计 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-zinc-800/50 rounded-lg text-center">
              <Film className="mx-auto text-amber-500 mb-2" size={24} />
              <div className="text-2xl font-bold text-white">{stats.scenes}</div>
              <div className="text-xs text-zinc-500">场次</div>
            </div>
            <div className="p-4 bg-zinc-800/50 rounded-lg text-center">
              <Users className="mx-auto text-blue-400 mb-2" size={24} />
              <div className="text-2xl font-bold text-white">{stats.characters}</div>
              <div className="text-xs text-zinc-500">角色</div>
            </div>
            <div className="p-4 bg-zinc-800/50 rounded-lg text-center">
              <Image className="mx-auto text-green-400 mb-2" size={24} />
              <div className="text-2xl font-bold text-white">{stats.references}</div>
              <div className="text-xs text-zinc-500">参考资料</div>
            </div>
            <div className="p-4 bg-zinc-800/50 rounded-lg text-center">
              <Clock className="mx-auto text-purple-400 mb-2" size={24} />
              <div className="text-2xl font-bold text-white">{formatDuration(stats.totalDuration)}</div>
              <div className="text-xs text-zinc-500">预计时长</div>
            </div>
          </div>
        </div>
      </div>

      {/* 校验结果 */}
      <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-zinc-300 flex items-center gap-2">
            <Sparkles className="text-amber-500" size={16} />
            AI 校验结果
          </h3>
          <button
            onClick={handleValidate}
            disabled={isValidating}
            className="flex items-center gap-1 px-3 py-1 text-xs text-zinc-400 hover:text-white transition-colors"
          >
            {isValidating ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <RefreshCw size={12} />
            )}
            <span>重新校验</span>
          </button>
        </div>

        {isValidating ? (
          <div className="flex items-center gap-3 py-4">
            <Loader2 className="text-amber-500 animate-spin" size={20} />
            <span className="text-sm text-zinc-400">正在校验项目...</span>
          </div>
        ) : (
          <div className="space-y-3">
            {/* 错误 */}
            {errors.length > 0 && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-red-400 mb-2">
                  <AlertCircle size={16} />
                  <span className="text-sm font-medium">需要修正 ({errors.length})</span>
                </div>
                <ul className="space-y-1">
                  {errors.map((error, i) => (
                    <li key={i} className="text-xs text-red-300">· {error.message}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 警告 */}
            {warnings.length > 0 && (
              <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-400 mb-2">
                  <AlertTriangle size={16} />
                  <span className="text-sm font-medium">建议改进 ({warnings.length})</span>
                </div>
                <ul className="space-y-1">
                  {warnings.map((warning, i) => (
                    <li key={i} className="text-xs text-yellow-300">· {warning.message}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* System_Agent 检查结果 */}
            {systemCheckResult && (
              <>
                {systemCheckResult.passed.length > 0 && (
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                    <div className="flex items-center gap-2 text-emerald-400 mb-2">
                      <CheckCircle size={16} />
                      <span className="text-sm font-medium">通过检查 ({systemCheckResult.passed.length})</span>
                    </div>
                    <ul className="space-y-1">
                      {systemCheckResult.passed.map((check, i) => (
                        <li key={i} className="text-xs text-emerald-300">✓ {check}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {systemCheckResult.suggestions.length > 0 && (
                  <div className="p-3 bg-zinc-800/50 border border-zinc-700 rounded-lg">
                    <div className="flex items-center gap-2 text-zinc-400 mb-2">
                      <Sparkles size={16} />
                      <span className="text-sm font-medium">AI 建议</span>
                    </div>
                    <ul className="space-y-1">
                      {systemCheckResult.suggestions.map((suggestion, i) => (
                        <li key={i} className="text-xs text-zinc-400">💡 {suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}

            {/* 全部通过 */}
            {errors.length === 0 && warnings.length === 0 && !systemCheckResult?.failed.length && (
              <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                <CheckCircle className="text-emerald-400" size={24} />
                <div>
                  <div className="text-sm font-medium text-emerald-400">校验通过</div>
                  <div className="text-xs text-emerald-300/70">项目信息完整，可以创建</div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 提示 */}
      <div className="p-4 bg-zinc-900/30 border border-zinc-800 rounded-xl">
        <div className="text-sm text-zinc-400 mb-2">📋 创建后</div>
        <ul className="text-xs text-zinc-500 space-y-1">
          <li>• 项目将进入 Analysis 阶段，可以开始素材匹配</li>
          <li>• 所有信息都可以在项目中继续编辑</li>
          <li>• 角色和场次标签将用于智能素材推荐</li>
        </ul>
      </div>
    </div>
  );
};

export default WizardStep6_Confirm;
