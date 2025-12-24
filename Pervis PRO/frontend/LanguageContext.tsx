
import React, { createContext, useState, useContext, ReactNode } from 'react';

type Language = 'zh' | 'en';

interface LanguageContextType {
  language: Language;
  toggleLanguage: () => void;
  t: (key: string) => string;
}

const translations: Record<Language, Record<string, string>> = {
  zh: {
    // Sidebar
    'sidebar.tools': '生产工具',
    'sidebar.resources': '资源管理',
    'sidebar.script': '剧本 & 拆解',
    'sidebar.board': '故事板', // Renamed
    'sidebar.timeline': '粗剪时间线',
    'sidebar.assets': '项目素材库',
    'sidebar.ai_ready': 'AI 就绪',
    'sidebar.settings': '系统设置',
    'sidebar.exit': '退出项目',
    'sidebar.current_project': '当前项目',
    
    // Stages
    'stage.analysis': '剧本分析',
    'stage.board': '故事板', // Renamed
    'stage.timeline': '粗剪预览',
    'stage.library': '素材库',

    // Landing
    'landing.recent': '最近项目',
    'landing.start': '开始新项目',
    'landing.subtitle': '深度解析剧本结构，自动拆解场次与节拍。\n所见即所得，一键生成动态故事板 (Animatic)。',
    'landing.step1': '结构分析',
    'landing.step2': '故事板 & RAG', // Renamed
    'landing.step3': '时间线组装',

    // BeatBoard
    'board.title': '故事板 (Storyboard)', // Renamed
    'board.progress': '进度',
    'board.enter_timeline': '进入剪辑台',
    'board.scene': '第',
    'board.shots': '个镜头',
    'board.ai_library': 'AI 素材库',
    'board.rag_prompt': '检索提示词 (RAG)',
    'board.candidates': '备选素材',
    'board.click_drag': '点击或拖拽上墙',
    'board.searching': '正在搜索向量库...',
    'board.no_result': '暂无推荐结果',
    'board.no_beat': '未选择节拍',
    'board.no_beat_desc': '请在左侧看板中点击任意镜头卡片，AI 将为您自动匹配参考素材。',

    // Timeline
    'timeline.current_shot': '当前镜头',
    'timeline.duration': '时长',
    'timeline.global_in': '全局入点',
    'timeline.seq_settings': '序列设置',
    'timeline.export': '导出成片',
    'timeline.track.scene': '场次结构',
    'timeline.track.video': '视频轨道 1',
    'timeline.track.audio': '音频轨道 1',

    // Common
    'common.next': '下一步',
    'common.export': '导出',
    'common.cancel': '取消',
    'common.confirm': '确认',
    'common.sync_mode': '同步模式',

    // Settings & Assets
    'settings.local_server': '本地素材服务器 (Local Assets)',
    'settings.local_server_desc': '配置本地 HTTP 服务器地址，允许直接引用 NAS 或本地硬盘中的高清素材。',
    'settings.local_server_placeholder': '例如: http://localhost:8080/assets/',
    'asset.link_local': '链接本地文件',
    'asset.enter_filename': '请输入文件名 (需位于本地服务器根目录下):',
    'asset.server_not_configured': '未配置本地服务器地址。请前往“系统设置”进行配置。',
  },
  en: {
    // Sidebar
    'sidebar.tools': 'Production Tools',
    'sidebar.resources': 'Resources',
    'sidebar.script': 'Script & Breakdown',
    'sidebar.board': 'Storyboard', // Renamed
    'sidebar.timeline': 'Rough Cut',
    'sidebar.assets': 'Asset Library',
    'sidebar.ai_ready': 'AI Ready',
    'sidebar.settings': 'Settings',
    'sidebar.exit': 'Exit Project',
    'sidebar.current_project': 'Current Project',

    // Stages
    'stage.analysis': 'Script Analysis',
    'stage.board': 'Storyboard', // Renamed
    'stage.timeline': 'Rough Cut',
    'stage.library': 'Asset Library',

    // Landing
    'landing.recent': 'Recent Projects',
    'landing.start': 'Start New Project',
    'landing.subtitle': 'Deep script structure analysis, automatic scene & beat breakdown.\nWhat You See Is What You Get, one-click animatic generation.',
    'landing.step1': 'Structure Analysis',
    'landing.step2': 'Storyboard & RAG', // Renamed
    'landing.step3': 'Timeline Assembly',

    // BeatBoard
    'board.title': 'Storyboard', // Renamed
    'board.progress': 'Progress',
    'board.enter_timeline': 'Enter Timeline',
    'board.scene': 'Scene',
    'board.shots': 'Shots',
    'board.ai_library': 'AI Asset Library',
    'board.rag_prompt': 'RAG Prompt',
    'board.candidates': 'Candidates',
    'board.click_drag': 'Click or Drag',
    'board.searching': 'Searching Vector DB...',
    'board.no_result': 'No Results Found',
    'board.no_beat': 'No Beat Selected',
    'board.no_beat_desc': 'Select any shot card on the left board, AI will automatically match reference assets.',

    // Timeline
    'timeline.current_shot': 'Current Shot',
    'timeline.duration': 'Duration',
    'timeline.global_in': 'Global In',
    'timeline.seq_settings': 'Sequence Settings',
    'timeline.export': 'Export Render',
    'timeline.track.scene': 'SCENE',
    'timeline.track.video': 'VIDEO 1',
    'timeline.track.audio': 'AUDIO 1',

    // Common
    'common.next': 'Next',
    'common.export': 'Export',
    'common.cancel': 'Cancel',
    'common.confirm': 'Confirm',
    'common.sync_mode': 'Sync Mode',

    // Settings & Assets
    'settings.local_server': 'Local Asset Server',
    'settings.local_server_desc': 'Configure a local HTTP server to reference assets directly from NAS or local drives.',
    'settings.local_server_placeholder': 'e.g., http://localhost:8080/assets/',
    'asset.link_local': 'Link Local File',
    'asset.enter_filename': 'Enter filename (must be in server root):',
    'asset.server_not_configured': 'Local server not configured. Please go to Settings.',
  }
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('zh');

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'zh' ? 'en' : 'zh');
  };

  const t = (key: string) => {
    return translations[language][key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
