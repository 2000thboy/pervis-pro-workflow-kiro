import React, { useState } from 'react';
import { Project, Character, Beat } from '../../types';
import { 
  FileText, Users, Film, Image, Edit2, Save, Clock, 
  ChevronDown, ChevronRight, Ratio, Clapperboard
} from 'lucide-react';

interface ProjectInfoTabProps {
  project: Project;
  onUpdate: (updates: Partial<Project>) => void;
}

// 可折叠的 Section 组件
const Section: React.FC<{
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}> = ({ title, icon, children, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  
  return (
    <div className="border border-zinc-800 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-zinc-900/50 hover:bg-zinc-900 transition-colors"
      >
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        {icon}
        <span className="font-medium text-sm">{title}</span>
      </button>
      {isOpen && (
        <div className="p-4 bg-zinc-950/50">
          {children}
        </div>
      )}
    </div>
  );
};

// 基本信息 Section
const BasicInfoSection: React.FC<{ project: Project; onUpdate: (updates: Partial<Project>) => void }> = ({ project, onUpdate }) => {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(project.title);

  const handleSave = () => {
    onUpdate({ title });
    setEditing(false);
  };

  return (
    <Section title="基本信息" icon={<Clapperboard size={16} className="text-yellow-500" />}>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-zinc-500 block mb-1">项目标题</label>
          {editing ? (
            <div className="flex gap-2">
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm"
              />
              <button onClick={handleSave} className="p-1.5 bg-yellow-600 rounded hover:bg-yellow-500">
                <Save size={14} />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-white font-medium">{project.title}</span>
              <button onClick={() => setEditing(true)} className="p-1 hover:bg-zinc-800 rounded">
                <Edit2 size={12} className="text-zinc-500" />
              </button>
            </div>
          )}
        </div>
        
        <div>
          <label className="text-xs text-zinc-500 block mb-1">项目类型</label>
          <span className="text-white">短片</span>
        </div>
        
        <div className="flex items-center gap-2">
          <Clock size={14} className="text-zinc-500" />
          <div>
            <label className="text-xs text-zinc-500 block">时长</label>
            <span className="text-white">{project.specs?.totalDuration || 0}秒</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Ratio size={14} className="text-zinc-500" />
          <div>
            <label className="text-xs text-zinc-500 block">画幅</label>
            <span className="text-white">{project.specs?.aspectRatio || '16:9'}</span>
          </div>
        </div>
      </div>
    </Section>
  );
};

// 剧本 Section
const ScriptSection: React.FC<{ project: Project }> = ({ project }) => {
  return (
    <Section title="剧本信息" icon={<FileText size={16} className="text-blue-500" />}>
      <div className="space-y-4">
        {project.logline && (
          <div>
            <label className="text-xs text-zinc-500 block mb-1">Logline</label>
            <p className="text-sm text-zinc-300 bg-zinc-900 rounded p-3">{project.logline}</p>
          </div>
        )}
        {project.synopsis && (
          <div>
            <label className="text-xs text-zinc-500 block mb-1">Synopsis</label>
            <p className="text-sm text-zinc-300 bg-zinc-900 rounded p-3 whitespace-pre-wrap">{project.synopsis}</p>
          </div>
        )}
        {!project.logline && !project.synopsis && (
          <p className="text-sm text-zinc-500 italic">暂无剧本信息</p>
        )}
      </div>
    </Section>
  );
};

// 角色 Section
const CharactersSection: React.FC<{ characters: Character[] }> = ({ characters }) => {
  return (
    <Section title={`角色列表 (${characters.length})`} icon={<Users size={16} className="text-green-500" />}>
      {characters.length > 0 ? (
        <div className="grid grid-cols-2 gap-3">
          {characters.map((char, idx) => (
            <div key={idx} className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
              <div className="font-medium text-white text-sm">{char.name}</div>
              {char.description && (
                <p className="text-xs text-zinc-400 mt-1 line-clamp-2">{char.description}</p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 italic">暂无角色信息</p>
      )}
    </Section>
  );
};

// 场次 Section
const ScenesSection: React.FC<{ beats: Beat[] }> = ({ beats }) => {
  // 按场景分组
  const scenes = beats.reduce((acc, beat) => {
    const slug = beat.tags?.scene_slug || 'SCENE 1';
    if (!acc[slug]) acc[slug] = [];
    acc[slug].push(beat);
    return acc;
  }, {} as Record<string, Beat[]>);

  return (
    <Section title={`场次列表 (${Object.keys(scenes).length})`} icon={<Film size={16} className="text-purple-500" />}>
      {Object.keys(scenes).length > 0 ? (
        <div className="space-y-2">
          {Object.entries(scenes).map(([slug, sceneBeats], idx) => (
            <div key={idx} className="bg-zinc-900 rounded-lg p-3 border border-zinc-800">
              <div className="flex justify-between items-center">
                <span className="font-medium text-white text-sm">{slug}</span>
                <span className="text-xs text-zinc-500">{sceneBeats.length} 个节拍</span>
              </div>
              <div className="text-xs text-zinc-400 mt-1">
                总时长: {sceneBeats.reduce((sum, b) => sum + b.duration, 0)}秒
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 italic">暂无场次信息</p>
      )}
    </Section>
  );
};

// 参考资料 Section
const ReferencesSection: React.FC<{ project: Project }> = ({ project }) => {
  // 从 beats 中提取有素材的
  const assetsWithThumbnails = project.beats
    .filter(b => b.assets && b.assets.length > 0)
    .flatMap(b => b.assets || [])
    .slice(0, 8);

  return (
    <Section title="参考资料" icon={<Image size={16} className="text-orange-500" />} defaultOpen={false}>
      {assetsWithThumbnails.length > 0 ? (
        <div className="grid grid-cols-4 gap-2">
          {assetsWithThumbnails.map((asset, idx) => (
            <div key={idx} className="aspect-video bg-zinc-900 rounded overflow-hidden">
              {asset.thumbnailUrl ? (
                <img src={asset.thumbnailUrl} alt="" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-zinc-600">
                  <Image size={20} />
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-zinc-500 italic">暂无参考资料</p>
      )}
    </Section>
  );
};

// 主组件
export const ProjectInfoTab: React.FC<ProjectInfoTabProps> = ({ project, onUpdate }) => {
  // 计算完成度
  const completionItems = [
    { name: '标题', done: !!project.title },
    { name: 'Logline', done: !!project.logline },
    { name: 'Synopsis', done: !!project.synopsis },
    { name: '角色', done: project.characters && project.characters.length > 0 },
    { name: '场次', done: project.beats && project.beats.length > 0 },
  ];
  const completionPercent = Math.round((completionItems.filter(i => i.done).length / completionItems.length) * 100);

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto space-y-4">
        {/* 完成度指示器 */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-zinc-300">项目完成度</span>
            <span className="text-sm font-bold text-yellow-500">{completionPercent}%</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-yellow-600 to-yellow-400 transition-all"
              style={{ width: `${completionPercent}%` }}
            />
          </div>
          <div className="flex gap-2 mt-2 flex-wrap">
            {completionItems.map((item, idx) => (
              <span 
                key={idx}
                className={`text-xs px-2 py-0.5 rounded ${item.done ? 'bg-green-900/50 text-green-400' : 'bg-zinc-800 text-zinc-500'}`}
              >
                {item.name}
              </span>
            ))}
          </div>
        </div>

        {/* 各个 Section */}
        <BasicInfoSection project={project} onUpdate={onUpdate} />
        <ScriptSection project={project} />
        <CharactersSection characters={project.characters || []} />
        <ScenesSection beats={project.beats || []} />
        <ReferencesSection project={project} />
      </div>
    </div>
  );
};
