
import React, { useState, useEffect } from 'react';
import { X, Feather, FileType, Ban, Bot, Settings, Save, HardDrive, Info, Loader2 } from 'lucide-react';
import { useLanguage } from './LanguageContext';
import { api } from '../services/api';
import { UserSettings } from '../types';

interface SettingsModalProps {
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ onClose }) => {
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  const [settings, setSettings] = useState<UserSettings>({
      dna: { style: '', formatting: '', donts: '', persona: '' },
      localServer: { baseUrl: '' }
  });

  useEffect(() => {
    const load = async () => {
        setLoading(true);
        try {
            const data = await api.getSettings();
            setSettings(data);
        } catch(e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };
    load();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
        await api.saveSettings(settings);
        onClose();
    } catch(e) {
        console.error("Failed to save", e);
    } finally {
        setSaving(false);
    }
  };

  const updateDna = (key: keyof UserSettings['dna'], val: string) => {
      setSettings(prev => ({ ...prev, dna: { ...prev.dna, [key]: val } }));
  };

  if (loading) {
      return (
          <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm">
              <Loader2 className="animate-spin text-zinc-500" size={32} />
          </div>
      );
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in zoom-in-95 duration-200">
      <div className="w-[900px] bg-zinc-950 border border-zinc-800 rounded-xl shadow-2xl flex flex-col overflow-hidden max-h-[90vh]">
        
        {/* Header */}
        <div className="p-6 border-b border-zinc-800 flex items-start justify-between bg-zinc-900/30">
            <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span className="text-yellow-500">✨</span> System & Writer's DNA
                </h2>
                <p className="text-xs text-zinc-500 mt-1">
                    系统偏好与本地环境配置
                </p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-zinc-800 rounded-full text-zinc-500 hover:text-white transition-colors">
                <X size={20} />
            </button>
        </div>

        {/* Content Grid */}
        <div className="p-6 overflow-y-auto space-y-6">
            
            {/* SECTION 1: Local Assets */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-5">
                <h3 className="text-sm font-bold text-blue-400 mb-2 flex items-center gap-2">
                    <HardDrive size={16} /> {t('settings.local_server')}
                </h3>
                <p className="text-[10px] text-zinc-400 mb-3 leading-relaxed">
                    {t('settings.local_server_desc')}
                </p>
                <div className="flex gap-2">
                    <input 
                        type="text"
                        className="flex-1 bg-black border border-zinc-700 rounded p-2 text-xs text-zinc-200 placeholder:text-zinc-700 focus:border-blue-500 focus:outline-none font-mono"
                        placeholder={t('settings.local_server_placeholder')}
                        value={settings.localServer.baseUrl}
                        onChange={(e) => setSettings({...settings, localServer: { baseUrl: e.target.value }})}
                    />
                </div>
                <div className="mt-2 flex items-start gap-2 text-[10px] text-zinc-500 bg-zinc-900 p-2 rounded">
                    <Info size={12} className="mt-0.5 flex-shrink-0" />
                    <span>
                        提示：请确保本地服务允许跨域 (CORS)。<br/>
                        推荐命令 (Node.js): <code className="text-zinc-300">npx http-server ./MyAssets --cors -p 8080</code>
                    </span>
                </div>
            </div>

            <hr className="border-zinc-800" />

            {/* SECTION 2: AI DNA */}
            <div className="grid grid-cols-2 gap-4">
                {/* Card 1: Style */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 group hover:border-zinc-600 transition-colors">
                    <h3 className="text-sm font-bold text-yellow-500 mb-2 flex items-center gap-2">
                        <Feather size={16} /> 文字风格 (Style)
                    </h3>
                    <textarea 
                        className="w-full h-20 bg-black border border-zinc-800 rounded p-3 text-xs text-zinc-300 resize-none focus:border-yellow-500/50 focus:outline-none placeholder:text-zinc-700" 
                        placeholder="例如：请保持文字冷峻、克制。"
                        value={settings.dna.style}
                        onChange={(e) => updateDna('style', e.target.value)}
                    ></textarea>
                </div>

                {/* Card 2: Formatting */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 group hover:border-zinc-600 transition-colors">
                    <h3 className="text-sm font-bold text-indigo-400 mb-2 flex items-center gap-2">
                        <FileType size={16} /> 格式规范 (Formatting)
                    </h3>
                    <textarea 
                        className="w-full h-20 bg-black border border-zinc-800 rounded p-3 text-xs text-zinc-300 resize-none focus:border-indigo-500/50 focus:outline-none placeholder:text-zinc-700"
                        placeholder="例如：场景标题统一使用中文。"
                        value={settings.dna.formatting}
                        onChange={(e) => updateDna('formatting', e.target.value)}
                    ></textarea>
                </div>

                {/* Card 3: Don'ts */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 group hover:border-zinc-600 transition-colors">
                    <h3 className="text-sm font-bold text-red-400 mb-2 flex items-center gap-2">
                        <Ban size={16} /> 创作禁忌 (Don'ts)
                    </h3>
                    <textarea 
                        className="w-full h-20 bg-black border border-zinc-800 rounded p-3 text-xs text-zinc-300 resize-none focus:border-red-500/50 focus:outline-none placeholder:text-zinc-700"
                        placeholder='例如：不要使用画外音(V.O.)。'
                        value={settings.dna.donts}
                        onChange={(e) => updateDna('donts', e.target.value)}
                    ></textarea>
                </div>

                {/* Card 4: Persona */}
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 group hover:border-zinc-600 transition-colors">
                    <h3 className="text-sm font-bold text-emerald-400 mb-2 flex items-center gap-2">
                        <Bot size={16} /> AI 人设 (Persona)
                    </h3>
                    <textarea 
                        className="w-full h-20 bg-black border border-zinc-800 rounded p-3 text-xs text-zinc-300 resize-none focus:border-emerald-500/50 focus:outline-none placeholder:text-zinc-700"
                        placeholder="专业、客观的资深剧本顾问"
                        value={settings.dna.persona}
                        onChange={(e) => updateDna('persona', e.target.value)}
                    ></textarea>
                </div>
            </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/50 flex justify-end items-center gap-2">
            <button onClick={onClose} className="px-4 py-2 text-xs text-zinc-400 hover:text-white transition-colors">{t('common.cancel')}</button>
            <button 
                onClick={handleSave} 
                disabled={saving}
                className="px-6 py-2 bg-yellow-600 hover:bg-yellow-500 text-black text-xs font-bold rounded transition-colors flex items-center gap-2 disabled:opacity-50"
            >
                {saving && <Loader2 size={12} className="animate-spin"/>}
                <Save size={14} /> {t('common.confirm')}
            </button>
        </div>
      </div>
    </div>
  );
};
