/**
 * 向导步骤2 - 剧本导入
 * 支持文件上传（TXT、PDF、DOCX、FDX）和文本粘贴
 * 显示 Script_Agent 解析状态和 Director_Agent 审核状态
 */

import React, { useState, useCallback } from 'react';
import { 
  Upload, 
  FileText, 
  Sparkles, 
  AlertCircle, 
  CheckCircle,
  Loader2,
  RefreshCw,
  Copy,
  Trash2
} from 'lucide-react';
import { useWizard } from './WizardContext';
import { wizardApi } from './api';

export const WizardStep2_Script: React.FC = () => {
  const { state, updateScript, updateCharacters, updateScenes, setAgentStatus, updateBasicInfo } = useWizard();
  const { script, basicInfo } = state;
  
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // 处理文件上传
  const handleFileUpload = useCallback(async (file: File) => {
    setUploadError(null);
    
    // 验证文件类型
    const validTypes = ['.txt', '.pdf', '.docx', '.fdx'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!validTypes.includes(ext)) {
      setUploadError(`不支持的文件格式。支持: ${validTypes.join(', ')}`);
      return;
    }

    try {
      // 读取文件内容
      const text = await file.text();
      updateScript({ content: text, parseStatus: 'idle' });
    } catch (error) {
      setUploadError('文件读取失败');
    }
  }, [updateScript]);

  // 拖拽处理
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  // 解析剧本
  const handleParseScript = async () => {
    if (!script.content.trim()) {
      setUploadError('请先输入或上传剧本内容');
      return;
    }

    updateScript({ parseStatus: 'parsing', parseError: undefined });
    setAgentStatus('Script_Agent', { status: 'working', message: '正在解析剧本...', progress: 0 });

    try {
      const result = await wizardApi.parseScript({
        script_content: script.content,
        project_id: state.projectId
      });

      if (result.status === 'failed') {
        throw new Error(result.error || '解析失败');
      }

      // 更新解析结果
      updateScript({
        parseStatus: 'success',
        scenes: result.scenes.map(s => ({
          sceneId: s.scene_id,
          sceneNumber: s.scene_number,
          heading: s.heading,
          location: s.location,
          timeOfDay: s.time_of_day,
          description: s.description,
          characters: s.characters,
          estimatedDuration: s.estimated_duration
        })),
        characters: result.characters.map(c => ({
          id: `char_${c.name}`,
          name: c.name,
          dialogueCount: c.dialogue_count,
          firstAppearance: c.first_appearance,
          tags: c.tags
        })),
        logline: result.logline,
        synopsis: result.synopsis
      });

      // 同步到全局状态
      updateCharacters(result.characters.map(c => ({
        id: `char_${c.name}`,
        name: c.name,
        dialogueCount: c.dialogue_count,
        firstAppearance: c.first_appearance,
        tags: c.tags
      })));

      updateScenes(result.scenes.map(s => ({
        sceneId: s.scene_id,
        sceneNumber: s.scene_number,
        heading: s.heading,
        location: s.location,
        timeOfDay: s.time_of_day,
        description: s.description,
        characters: s.characters,
        estimatedDuration: s.estimated_duration
      })));

      // 如果有 logline，更新基本信息
      if (result.logline && !basicInfo.logline) {
        updateBasicInfo({ logline: result.logline });
      }

      setAgentStatus('Script_Agent', { status: 'completed', message: '解析完成', progress: 100 });
      setAgentStatus('Director_Agent', { status: 'completed', message: '审核通过', progress: 100 });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '解析失败';
      updateScript({ parseStatus: 'error', parseError: errorMessage });
      setAgentStatus('Script_Agent', { status: 'failed', message: errorMessage, progress: 0 });
    }
  };

  // 清空剧本
  const handleClear = () => {
    updateScript({
      content: '',
      scenes: [],
      characters: [],
      logline: undefined,
      synopsis: undefined,
      parseStatus: 'idle',
      parseError: undefined
    });
    updateCharacters([]);
    updateScenes([]);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 上传区域 */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
          isDragging
            ? 'border-amber-500 bg-amber-500/10'
            : 'border-zinc-700 hover:border-zinc-600'
        }`}
      >
        <input
          type="file"
          accept=".txt,.pdf,.docx,.fdx"
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <Upload className={`mx-auto mb-4 ${isDragging ? 'text-amber-500' : 'text-zinc-500'}`} size={40} />
        <div className="text-zinc-300 mb-2">拖拽文件到此处，或点击上传</div>
        <div className="text-xs text-zinc-500">支持 TXT、PDF、DOCX、FDX 格式</div>
      </div>

      {uploadError && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          <AlertCircle size={16} />
          <span>{uploadError}</span>
        </div>
      )}

      {/* 剧本编辑区 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-zinc-300">剧本内容</label>
          <div className="flex items-center gap-2">
            {script.content && (
              <button
                onClick={handleClear}
                className="flex items-center gap-1 px-2 py-1 text-xs text-zinc-500 hover:text-red-400 transition-colors"
              >
                <Trash2 size={12} />
                <span>清空</span>
              </button>
            )}
            <span className="text-xs text-zinc-500">
              {script.content.length} 字符
            </span>
          </div>
        </div>
        <textarea
          value={script.content}
          onChange={(e) => updateScript({ content: e.target.value, parseStatus: 'idle' })}
          placeholder="在此粘贴剧本内容...

示例格式：
INT. 咖啡馆 - 日

小明坐在窗边，看着窗外的雨。

小明
（自言自语）
今天的雨下得真大..."
          rows={12}
          className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-600 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none transition-colors resize-none font-mono text-sm"
        />
      </div>

      {/* AI 解析按钮 */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleParseScript}
          disabled={!script.content.trim() || script.parseStatus === 'parsing'}
          className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 text-black font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {script.parseStatus === 'parsing' ? (
            <>
              <Loader2 size={18} className="animate-spin" />
              <span>AI 解析中...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>AI 智能解析</span>
            </>
          )}
        </button>

        {script.parseStatus === 'success' && (
          <button
            onClick={handleParseScript}
            className="flex items-center gap-2 px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
          >
            <RefreshCw size={14} />
            <span>重新解析</span>
          </button>
        )}
      </div>

      {/* 解析状态 */}
      {script.parseStatus === 'error' && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-red-400 flex-shrink-0" size={20} />
            <div>
              <div className="text-sm font-medium text-red-400 mb-1">解析失败</div>
              <div className="text-xs text-red-300">{script.parseError}</div>
              <div className="text-xs text-zinc-500 mt-2">
                您可以手动在下一步添加角色和场次信息
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 解析结果预览 */}
      {script.parseStatus === 'success' && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle size={18} />
            <span className="text-sm font-medium">解析成功</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 场次统计 */}
            <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <FileText size={16} className="text-amber-500" />
                <span className="text-sm font-medium text-zinc-300">场次</span>
                <span className="ml-auto text-lg font-bold text-white">{script.scenes.length}</span>
              </div>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {script.scenes.slice(0, 5).map((scene, i) => (
                  <div key={i} className="text-xs text-zinc-500 truncate">
                    {scene.sceneNumber}. {scene.heading}
                  </div>
                ))}
                {script.scenes.length > 5 && (
                  <div className="text-xs text-zinc-600">...还有 {script.scenes.length - 5} 个场次</div>
                )}
              </div>
            </div>

            {/* 角色统计 */}
            <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
              <div className="flex items-center gap-2 mb-3">
                <FileText size={16} className="text-amber-500" />
                <span className="text-sm font-medium text-zinc-300">角色</span>
                <span className="ml-auto text-lg font-bold text-white">{script.characters.length}</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {script.characters.slice(0, 8).map((char, i) => (
                  <span key={i} className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                    {char.name}
                  </span>
                ))}
                {script.characters.length > 8 && (
                  <span className="px-2 py-0.5 text-xs text-zinc-600">+{script.characters.length - 8}</span>
                )}
              </div>
            </div>
          </div>

          {/* Logline 和 Synopsis */}
          {(script.logline || script.synopsis) && (
            <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl space-y-3">
              {script.logline && (
                <div>
                  <div className="text-xs text-zinc-500 mb-1">Logline</div>
                  <div className="text-sm text-zinc-300 italic">"{script.logline}"</div>
                </div>
              )}
              {script.synopsis && (
                <div>
                  <div className="text-xs text-zinc-500 mb-1">Synopsis</div>
                  <div className="text-sm text-zinc-400">{script.synopsis}</div>
                </div>
              )}
            </div>
          )}

          {/* 预计时长 */}
          <div className="text-sm text-zinc-500">
            预计总时长: {Math.round(script.scenes.reduce((sum, s) => sum + s.estimatedDuration, 0) / 60)} 分钟
          </div>
        </div>
      )}

      {/* 提示信息 */}
      {script.parseStatus === 'idle' && !script.content && (
        <div className="p-4 bg-zinc-900/30 border border-zinc-800 rounded-xl">
          <div className="text-sm text-zinc-400 mb-2">💡 提示</div>
          <ul className="text-xs text-zinc-500 space-y-1">
            <li>• 支持标准剧本格式（场景标题、角色名、对话）</li>
            <li>• AI 会自动识别场次、角色、对话和动作描述</li>
            <li>• 解析后可以在后续步骤中手动调整</li>
            <li>• 如果没有剧本，可以跳过此步骤手动添加信息</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default WizardStep2_Script;
