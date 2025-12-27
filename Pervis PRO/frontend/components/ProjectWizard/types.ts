/**
 * 项目立项向导 - 类型定义
 * Phase 5: 前端向导组件
 */

// 向导步骤
export enum WizardStep {
  BASIC_INFO = 1,
  SCRIPT = 2,
  CHARACTERS = 3,
  SCENES = 4,
  REFERENCES = 5,
  CONFIRM = 6
}

// 项目类型
export type ProjectType = 'short_film' | 'advertisement' | 'music_video' | 'feature_film' | 'custom';

// 项目类型配置
export const PROJECT_TYPE_CONFIG: Record<ProjectType, {
  label: string;
  icon: string;
  defaultDuration: number;
  description: string;
}> = {
  short_film: {
    label: '短片',
    icon: '🎬',
    defaultDuration: 15,
    description: '15分钟以内的叙事短片'
  },
  advertisement: {
    label: '广告',
    icon: '📺',
    defaultDuration: 1,
    description: '商业广告、宣传片'
  },
  music_video: {
    label: 'MV',
    icon: '🎵',
    defaultDuration: 4,
    description: '音乐视频'
  },
  feature_film: {
    label: '长片',
    icon: '🎥',
    defaultDuration: 90,
    description: '60分钟以上的长片'
  },
  custom: {
    label: '自定义',
    icon: '✨',
    defaultDuration: 10,
    description: '自定义项目类型'
  }
};

// 画幅比例选项
export const ASPECT_RATIO_OPTIONS = [
  { value: '16:9', label: '16:9 (宽屏)', description: '标准高清' },
  { value: '2.39:1', label: '2.39:1 (变形宽银幕)', description: '电影院标准' },
  { value: '1.85:1', label: '1.85:1 (学院宽银幕)', description: '美国电影标准' },
  { value: '4:3', label: '4:3 (标准)', description: '传统电视' },
  { value: '1:1', label: '1:1 (方形)', description: '社交媒体' },
  { value: '9:16', label: '9:16 (竖屏)', description: '短视频' }
];

// 帧率选项
export const FRAME_RATE_OPTIONS = [
  { value: 24, label: '24 fps', description: '电影标准' },
  { value: 25, label: '25 fps', description: 'PAL 标准' },
  { value: 30, label: '30 fps', description: 'NTSC 标准' },
  { value: 60, label: '60 fps', description: '高帧率' }
];

// 分辨率选项
export const RESOLUTION_OPTIONS = [
  { value: '1920x1080', label: '1080p (Full HD)', description: '1920×1080' },
  { value: '3840x2160', label: '4K (UHD)', description: '3840×2160' },
  { value: '2560x1440', label: '2K (QHD)', description: '2560×1440' },
  { value: '1280x720', label: '720p (HD)', description: '1280×720' }
];

// 基本信息表单数据
export interface BasicInfoData {
  title: string;
  projectType: ProjectType;
  durationMinutes: number;
  aspectRatio: string;
  frameRate: number;
  resolution: string;
  logline: string;
}

// 场次信息
export interface SceneInfo {
  sceneId: string;
  sceneNumber: number;
  heading: string;
  location: string;
  timeOfDay: string;
  description: string;
  characters: string[];
  estimatedDuration: number;
}

// 角色信息
export interface CharacterInfo {
  id: string;
  name: string;
  dialogueCount: number;
  firstAppearance: number;
  tags: Record<string, string>;
  bio?: string;
  generatedImage?: string;      // AI 生成的人设图 URL
  thumbnailImage?: string;      // 缩略图路径
}

// 剧本数据
export interface ScriptData {
  content: string;
  scenes: SceneInfo[];
  characters: CharacterInfo[];
  logline?: string;
  synopsis?: string;
  parseStatus: 'idle' | 'parsing' | 'success' | 'error';
  parseError?: string;
}

// 参考资料
export interface ReferenceAsset {
  id: string;
  path: string;
  filename: string;
  category: 'character' | 'scene' | 'reference';
  confidence: number;
  tags: string[];
  thumbnailUrl?: string;
  uploadStatus: 'pending' | 'uploading' | 'processing' | 'done' | 'error';
  error?: string;
}

// Agent 状态
export interface AgentStatus {
  agentName: string;
  status: 'idle' | 'working' | 'reviewing' | 'completed' | 'failed';
  message: string;
  progress: number;
}

// 验证错误
export interface ValidationError {
  field: string;
  message: string;
  severity: 'error' | 'warning';
}

// 向导状态
export interface WizardState {
  currentStep: WizardStep;
  basicInfo: BasicInfoData;
  script: ScriptData;
  characters: CharacterInfo[];
  scenes: SceneInfo[];
  references: ReferenceAsset[];
  agentStatuses: AgentStatus[];
  validationErrors: ValidationError[];
  completionPercentage: number;
  isDirty: boolean;
  projectId?: string;
}

// 向导上下文
export interface WizardContextType {
  state: WizardState;
  setStep: (step: WizardStep) => void;
  updateBasicInfo: (data: Partial<BasicInfoData>) => void;
  updateScript: (data: Partial<ScriptData>) => void;
  updateCharacters: (characters: CharacterInfo[]) => void;
  updateScenes: (scenes: SceneInfo[]) => void;
  addReference: (asset: ReferenceAsset) => void;
  removeReference: (id: string) => void;
  updateReference: (id: string, data: Partial<ReferenceAsset>) => void;
  setAgentStatus: (agentName: string, status: Partial<AgentStatus>) => void;
  validate: () => Promise<boolean>;
  submit: () => Promise<string | null>;
  reset: () => void;
}

// 默认初始状态
export const DEFAULT_WIZARD_STATE: WizardState = {
  currentStep: WizardStep.BASIC_INFO,
  basicInfo: {
    title: '',
    projectType: 'short_film',
    durationMinutes: 15,
    aspectRatio: '16:9',
    frameRate: 24,
    resolution: '1920x1080',
    logline: ''
  },
  script: {
    content: '',
    scenes: [],
    characters: [],
    parseStatus: 'idle'
  },
  characters: [],
  scenes: [],
  references: [],
  agentStatuses: [],
  validationErrors: [],
  completionPercentage: 0,
  isDirty: false
};
