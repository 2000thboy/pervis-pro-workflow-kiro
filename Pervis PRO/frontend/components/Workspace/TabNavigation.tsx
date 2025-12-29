import React from 'react';
import { FileText, LayoutDashboard, Play } from 'lucide-react';
import { TabType, TABS } from './types';

interface TabNavigationProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const iconMap = {
  FileText,
  LayoutDashboard,
  Play,
};

export const TabNavigation: React.FC<TabNavigationProps> = ({ activeTab, onTabChange }) => {
  const labels: Record<TabType, string> = {
    info: '立项信息',
    beatboard: 'Beatboard',
    preview: '预演模式',
  };

  return (
    <div className="flex border-b border-zinc-800 bg-zinc-950">
      {TABS.map((tab) => {
        const Icon = iconMap[tab.icon as keyof typeof iconMap];
        const isActive = activeTab === tab.id;
        
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`
              flex items-center gap-2 px-6 py-3 text-sm font-medium transition-all
              border-b-2 -mb-[1px]
              ${isActive 
                ? 'border-yellow-500 text-yellow-500 bg-zinc-900/50' 
                : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/30'
              }
            `}
            title={tab.shortcut}
          >
            <Icon size={16} />
            <span>{labels[tab.id]}</span>
          </button>
        );
      })}
    </div>
  );
};
