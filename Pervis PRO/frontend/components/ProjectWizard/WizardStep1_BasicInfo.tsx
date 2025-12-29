/**
 * 向导步骤1 - 基本信息
 * 项目名称、类型、时长、画幅、帧率、分辨率
 * 支持 AI 生成项目名称和 Logline（Demo 演示用）
 */

import React, { useState } from 'react';
import { Clock, Monitor, Zap, Maximize2, Sparkles, Loader2, Wand2 } from 'lucide-react';
import { useWizard } from './WizardContext';
import {
  PROJECT_TYPE_CONFIG,
  ASPECT_RATIO_OPTIONS,
  FRAME_RATE_OPTIONS,
  RESOLUTION_OPTIONS,
  ProjectType
} from './types';
import { wizardApi } from './api';

// Demo 用的示例项目名称
const DEMO_PROJECT_NAMES: Record<ProjectType, string[]> = {
  short_film: ['城市边缘', '最后一班地铁', '咖啡馆的秘密', '雨中的告别', '时间旅行者'],
  feature_film: ['星际迷途', '暗夜追踪', '命运交叉点', '最后的守护者', '时空裂缝'],
  advertisement: ['未来科技', '品质生活', '绿色家园', '智能出行', '健康新选择'],
  music_video: ['夜空中的星', '城市节拍', '心跳旋律', '追梦人', '光影交错'],
  custom: ['创意项目', '实验短片', '艺术探索', '概念演示', '视觉实验']
};

// Demo 用的示例 Logline
const DEMO_LOGLINES: Record<ProjectType, string[]> = {
  short_film: [
    '一个孤独的程序员在深夜的咖啡馆遇见了改变他人生的神秘女子。',
    '当最后一班地铁驶入站台，两个陌生人的命运开始交织。',
    '一封迟到十年的信，揭开了一段被遗忘的爱情故事。'
  ],
  feature_film: [
    '一位失忆的宇航员必须在外星球上找回记忆，才能拯救地球。',
    '当城市陷入黑暗，一个普通人发现自己是唯一能阻止灾难的人。',
    '两个来自不同时空的人相遇，却发现他们的命运早已注定。'
  ],
  advertisement: [
    '科技改变生活，让每一天都充满可能。',
    '品质源于细节，生活因此不同。',
    '绿色出行，为地球减负，为未来加分。'
  ],
  music_video: [
    '在霓虹闪烁的城市中，寻找属于自己的节奏。',
    '每一个音符都是一段故事，每一段旋律都是一次心跳。',
    '当音乐响起，所有的距离都不再遥远。'
  ],
  custom: [
    '打破常规，探索视觉艺术的无限可能。',
    '用镜头语言讲述独特的故事。',
    '创意无界，想象力是唯一的限制。'
  ]
};

export const WizardStep1_BasicInfo: React.FC = () => {
  const { state, updateBasicInfo, setAgentStatus } = useWizard();
  const { basicInfo } = state;
  
  const [isGeneratingName, setIsGeneratingName] = useState(false);
  const [isGeneratingLogline, setIsGeneratingLogline] = useState(false);

  // AI 生成项目名称（Demo 用）
  const handleGenerateName = async () => {
    setIsGeneratingName(true);
    setAgentStatus('PM_Agent', { status: 'working', message: '正在生成项目名称...', progress: 50 });
    
    try {
      // 尝试调用 API
      const result = await wizardApi.generateContent({
        project_id: state.projectId || 'temp',
        content_type: 'project_name',
        context: { project_type: basicInfo.projectType }
      });
      
      if (result.content?.name) {
        updateBasicInfo({ title: result.content.name });
      } else {
        // 使用本地 Demo 数据
        const names = DEMO_PROJECT_NAMES[basicInfo.projectType];
        const randomName = names[Math.floor(Math.random() * names.length)];
        updateBasicInfo({ title: randomName });
      }
      setAgentStatus('PM_Agent', { status: 'completed', message: '项目名称生成完成', progress: 100 });
    } catch {
      // API 失败时使用本地 Demo 数据
      const names = DEMO_PROJECT_NAMES[basicInfo.projectType];
      const randomName = names[Math.floor(Math.random() * names.length)];
      updateBasicInfo({ title: randomName });
      setAgentStatus('PM_Agent', { status: 'completed', message: '使用示例名称', progress: 100 });
    } finally {
      setIsGeneratingName(false);
    }
  };

  // AI 生成 Logline（Demo 用）
  const handleGenerateLogline = async () => {
    setIsGeneratingLogline(true);
    setAgentStatus('Script_Agent', { status: 'working', message: '正在生成 Logline...', progress: 50 });
    
    try {
      const result = await wizardApi.generateContent({
        project_id: state.projectId || 'temp',
        content_type: 'logline',
        context: { 
          project_type: basicInfo.projectType,
          title: basicInfo.title 
        }
      });
      
      if (result.content?.logline) {
        updateBasicInfo({ logline: result.content.logline });
      } else {
        // 使用本地 Demo 数据
        const loglines = DEMO_LOGLINES[basicInfo.projectType];
        const randomLogline = loglines[Math.floor(Math.random() * loglines.length)];
        updateBasicInfo({ logline: randomLogline });
      }
      setAgentStatus('Script_Agent', { status: 'completed', message: 'Logline 生成完成', progress: 100 });
    } catch {
      // API 失败时使用本地 Demo 数据
      const loglines = DEMO_LOGLINES[basicInfo.projectType];
      const randomLogline = loglines[Math.floor(Math.random() * loglines.length)];
      updateBasicInfo({ logline: randomLogline });
      setAgentStatus('Script_Agent', { status: 'completed', message: '使用示例 Logline', progress: 100 });
    } finally {
      setIsGeneratingLogline(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* 项目标题 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-300">
          项目名称 <span className="text-red-400">*</span>
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={basicInfo.title}
            onChange={(e) => updateBasicInfo({ title: e.target.value })}
            placeholder="输入项目名称..."
            className="flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none transition-colors"
          />
          <button
            onClick={handleGenerateName}
            disabled={isGeneratingName}
            className="flex items-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-all"
            title="AI 生成项目名称"
          >
            {isGeneratingName ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Wand2 size={16} />
            )}
            <span className="hidden sm:inline">AI 生成</span>
          </button>
        </div>
      </div>

      {/* 项目类型 */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-zinc-300">
          项目类型 <span className="text-red-400">*</span>
        </label>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {(Object.keys(PROJECT_TYPE_CONFIG) as ProjectType[]).map((type) => {
            const config = PROJECT_TYPE_CONFIG[type];
            const isSelected = basicInfo.projectType === type;
            
            return (
              <button
                key={type}
                onClick={() => updateBasicInfo({ 
                  projectType: type,
                  durationMinutes: config.defaultDuration
                })}
                className={`p-4 rounded-xl border transition-all text-left ${
                  isSelected
                    ? 'bg-amber-500/20 border-amber-500/50 ring-1 ring-amber-500/30'
                    : 'bg-zinc-900 border-zinc-700 hover:border-zinc-600'
                }`}
              >
                <div className="text-2xl mb-2">{config.icon}</div>
                <div className={`text-sm font-medium ${isSelected ? 'text-amber-400' : 'text-zinc-300'}`}>
                  {config.label}
                </div>
                <div className="text-xs text-zinc-500 mt-1">{config.description}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 时长 */}
      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
          <Clock size={16} className="text-zinc-500" />
          预计时长（分钟）
        </label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="1"
            max="180"
            value={basicInfo.durationMinutes}
            onChange={(e) => updateBasicInfo({ durationMinutes: parseInt(e.target.value) })}
            className="flex-1 h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
          />
          <input
            type="number"
            min="1"
            max="300"
            value={basicInfo.durationMinutes}
            onChange={(e) => updateBasicInfo({ durationMinutes: parseInt(e.target.value) || 1 })}
            className="w-20 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-white text-center focus:border-amber-500 outline-none"
          />
          <span className="text-sm text-zinc-500">分钟</span>
        </div>
        <div className="text-xs text-zinc-500">
          约 {Math.floor(basicInfo.durationMinutes / 60)} 小时 {basicInfo.durationMinutes % 60} 分钟
        </div>
      </div>

      {/* 技术规格 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 画幅比例 */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
            <Maximize2 size={16} className="text-zinc-500" />
            画幅比例
          </label>
          <select
            value={basicInfo.aspectRatio}
            onChange={(e) => updateBasicInfo({ aspectRatio: e.target.value })}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none cursor-pointer"
          >
            {ASPECT_RATIO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* 帧率 */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
            <Zap size={16} className="text-zinc-500" />
            帧率
          </label>
          <select
            value={basicInfo.frameRate}
            onChange={(e) => updateBasicInfo({ frameRate: parseInt(e.target.value) })}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none cursor-pointer"
          >
            {FRAME_RATE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label} - {option.description}
              </option>
            ))}
          </select>
        </div>

        {/* 分辨率 */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-sm font-medium text-zinc-300">
            <Monitor size={16} className="text-zinc-500" />
            分辨率
          </label>
          <select
            value={basicInfo.resolution}
            onChange={(e) => updateBasicInfo({ resolution: e.target.value })}
            className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white focus:border-amber-500 outline-none cursor-pointer"
          >
            {RESOLUTION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Logline */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="block text-sm font-medium text-zinc-300">
            一句话概要（Logline）
          </label>
          <button
            onClick={handleGenerateLogline}
            disabled={isGeneratingLogline}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-black text-xs font-medium rounded-lg disabled:opacity-50 transition-all"
            title="AI 生成 Logline"
          >
            {isGeneratingLogline ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Sparkles size={12} />
            )}
            <span>AI 生成</span>
          </button>
        </div>
        <textarea
          value={basicInfo.logline}
          onChange={(e) => updateBasicInfo({ logline: e.target.value })}
          placeholder="用一句话描述你的故事..."
          rows={2}
          className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none transition-colors resize-none"
        />
        <div className="text-xs text-zinc-500">
          可选，点击 AI 生成按钮快速创建，或在下一步由 AI 自动生成
        </div>
      </div>

      {/* 预览卡片 */}
      <div className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
        <div className="text-xs text-zinc-500 mb-3">项目预览</div>
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-amber-500/20 to-yellow-500/20 rounded-lg flex items-center justify-center text-3xl">
            {PROJECT_TYPE_CONFIG[basicInfo.projectType].icon}
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white">
              {basicInfo.title || '未命名项目'}
            </h3>
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                {PROJECT_TYPE_CONFIG[basicInfo.projectType].label}
              </span>
              <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                {basicInfo.durationMinutes} 分钟
              </span>
              <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                {basicInfo.aspectRatio}
              </span>
              <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                {basicInfo.frameRate} fps
              </span>
              <span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">
                {basicInfo.resolution}
              </span>
            </div>
            {basicInfo.logline && (
              <p className="text-sm text-zinc-400 mt-2 italic">"{basicInfo.logline}"</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WizardStep1_BasicInfo;
