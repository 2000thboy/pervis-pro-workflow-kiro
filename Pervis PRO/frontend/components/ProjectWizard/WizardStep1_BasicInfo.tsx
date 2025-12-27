/**
 * 向导步骤1 - 基本信息
 * 项目名称、类型、时长、画幅、帧率、分辨率
 */

import React from 'react';
import { Film, Clock, Monitor, Zap, Maximize2 } from 'lucide-react';
import { useWizard } from './WizardContext';
import {
  PROJECT_TYPE_CONFIG,
  ASPECT_RATIO_OPTIONS,
  FRAME_RATE_OPTIONS,
  RESOLUTION_OPTIONS,
  ProjectType
} from './types';

export const WizardStep1_BasicInfo: React.FC = () => {
  const { state, updateBasicInfo } = useWizard();
  const { basicInfo } = state;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* 项目标题 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-300">
          项目名称 <span className="text-red-400">*</span>
        </label>
        <input
          type="text"
          value={basicInfo.title}
          onChange={(e) => updateBasicInfo({ title: e.target.value })}
          placeholder="输入项目名称..."
          className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none transition-colors"
        />
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
        <label className="block text-sm font-medium text-zinc-300">
          一句话概要（Logline）
        </label>
        <textarea
          value={basicInfo.logline}
          onChange={(e) => updateBasicInfo({ logline: e.target.value })}
          placeholder="用一句话描述你的故事..."
          rows={2}
          className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg text-white placeholder-zinc-500 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 outline-none transition-colors resize-none"
        />
        <div className="text-xs text-zinc-500">
          可选，也可以在下一步由 AI 自动生成
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
