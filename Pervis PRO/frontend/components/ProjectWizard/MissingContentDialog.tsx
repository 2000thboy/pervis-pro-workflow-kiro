/**
 * 缺失内容对话框
 * 显示缺失字段列表，提供处理选项
 */

import React, { useState } from 'react';
import { 
  AlertTriangle, 
  X, 
  Sparkles, 
  Edit3, 
  FileQuestion,
  Check,
  Loader2
} from 'lucide-react';

interface MissingField {
  field: string;
  label: string;
  required: boolean;
}

interface MissingContentDialogProps {
  isOpen: boolean;
  onClose: () => void;
  missingFields: MissingField[];
  onAction: (field: string, action: 'placeholder' | 'generate' | 'manual') => Promise<void>;
}

type ActionType = 'placeholder' | 'generate' | 'manual';

export const MissingContentDialog: React.FC<MissingContentDialogProps> = ({
  isOpen,
  onClose,
  missingFields,
  onAction
}) => {
  const [selectedActions, setSelectedActions] = useState<Record<string, ActionType>>({});
  const [processing, setProcessing] = useState<string | null>(null);
  const [completed, setCompleted] = useState<string[]>([]);

  if (!isOpen) return null;

  // 选择操作
  const handleSelectAction = (field: string, action: ActionType) => {
    setSelectedActions(prev => ({ ...prev, [field]: action }));
  };

  // 执行单个操作
  const handleExecute = async (field: string) => {
    const action = selectedActions[field];
    if (!action) return;

    setProcessing(field);
    try {
      await onAction(field, action);
      setCompleted(prev => [...prev, field]);
    } catch (error) {
      console.error(`处理 ${field} 失败:`, error);
    } finally {
      setProcessing(null);
    }
  };

  // 批量执行
  const handleExecuteAll = async () => {
    for (const field of missingFields) {
      const action = selectedActions[field.field];
      if (action && !completed.includes(field.field)) {
        await handleExecute(field.field);
      }
    }
  };

  // 全选操作
  const handleSelectAll = (action: ActionType) => {
    const newSelections: Record<string, ActionType> = {};
    missingFields.forEach(f => {
      if (!completed.includes(f.field)) {
        newSelections[f.field] = action;
      }
    });
    setSelectedActions(prev => ({ ...prev, ...newSelections }));
  };

  const pendingCount = missingFields.filter(f => !completed.includes(f.field)).length;
  const hasSelections = Object.keys(selectedActions).some(
    k => !completed.includes(k) && selectedActions[k]
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-xl shadow-2xl">
        {/* 头部 */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-500/20 rounded-lg">
              <AlertTriangle className="text-yellow-500" size={20} />
            </div>
            <div>
              <h3 className="text-base font-medium text-white">缺失内容</h3>
              <p className="text-xs text-zinc-500">
                {pendingCount} 个字段需要处理
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* 批量操作 */}
        <div className="p-4 border-b border-zinc-800 bg-zinc-900/50">
          <div className="text-xs text-zinc-500 mb-2">批量选择处理方式</div>
          <div className="flex gap-2">
            <button
              onClick={() => handleSelectAll('placeholder')}
              className="flex-1 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-xs text-zinc-300 transition-colors"
            >
              <FileQuestion size={14} className="mx-auto mb-1" />
              全部占位符
            </button>
            <button
              onClick={() => handleSelectAll('generate')}
              className="flex-1 px-3 py-2 bg-amber-500/20 hover:bg-amber-500/30 rounded-lg text-xs text-amber-400 transition-colors"
            >
              <Sparkles size={14} className="mx-auto mb-1" />
              全部 AI 生成
            </button>
            <button
              onClick={() => handleSelectAll('manual')}
              className="flex-1 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-xs text-zinc-300 transition-colors"
            >
              <Edit3 size={14} className="mx-auto mb-1" />
              全部手动输入
            </button>
          </div>
        </div>

        {/* 字段列表 */}
        <div className="max-h-80 overflow-y-auto p-4 space-y-3">
          {missingFields.map((field) => {
            const isCompleted = completed.includes(field.field);
            const isProcessing = processing === field.field;
            const selectedAction = selectedActions[field.field];

            return (
              <div
                key={field.field}
                className={`p-3 rounded-lg border transition-colors ${
                  isCompleted
                    ? 'bg-emerald-500/10 border-emerald-500/30'
                    : 'bg-zinc-800/50 border-zinc-800'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {isCompleted ? (
                      <Check size={14} className="text-emerald-400" />
                    ) : field.required ? (
                      <span className="text-red-400 text-xs">*</span>
                    ) : null}
                    <span className="text-sm text-zinc-300">{field.label}</span>
                  </div>
                  {isProcessing && (
                    <Loader2 size={14} className="text-amber-500 animate-spin" />
                  )}
                </div>

                {!isCompleted && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSelectAction(field.field, 'placeholder')}
                      className={`flex-1 px-2 py-1.5 rounded text-xs transition-colors ${
                        selectedAction === 'placeholder'
                          ? 'bg-zinc-700 text-white'
                          : 'bg-zinc-800 text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      占位符
                    </button>
                    <button
                      onClick={() => handleSelectAction(field.field, 'generate')}
                      className={`flex-1 px-2 py-1.5 rounded text-xs transition-colors ${
                        selectedAction === 'generate'
                          ? 'bg-amber-500/30 text-amber-400'
                          : 'bg-zinc-800 text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      AI 生成
                    </button>
                    <button
                      onClick={() => handleSelectAction(field.field, 'manual')}
                      className={`flex-1 px-2 py-1.5 rounded text-xs transition-colors ${
                        selectedAction === 'manual'
                          ? 'bg-zinc-700 text-white'
                          : 'bg-zinc-800 text-zinc-500 hover:text-zinc-300'
                      }`}
                    >
                      手动
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* 底部操作 */}
        <div className="flex items-center justify-between p-4 border-t border-zinc-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
          >
            稍后处理
          </button>
          <button
            onClick={handleExecuteAll}
            disabled={!hasSelections || processing !== null}
            className="flex items-center gap-2 px-6 py-2 bg-amber-500 hover:bg-amber-400 text-black font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {processing ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                <span>处理中...</span>
              </>
            ) : (
              <>
                <Check size={16} />
                <span>执行选中操作</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MissingContentDialog;
