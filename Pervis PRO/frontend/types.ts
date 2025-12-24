
export enum WorkflowStage {
  SETUP = 'SETUP',
  ANALYSIS = 'ANALYSIS',
  BOARD = 'BOARD',
  TIMELINE = 'TIMELINE',
  LIBRARY = 'LIBRARY'
}

export interface TagSchema {
  scene_slug?: string;
  location_type?: string; // 'INT' | 'EXT'
  time_of_day?: string;
  primary_emotion?: string;
  key_action?: string;
  visual_notes?: string;
  shot_type?: string;
}

export interface Character {
  id: string;
  name: string;
  role: 'Protagonist' | 'Antagonist' | 'Supporting' | 'Extra';
  description: string;
  traits: string[];
  avatarUrl?: string;
}

export interface VideoGlobalTags {
  characters: Array<{ label: string; weight: number }>;
  actions: Array<{ label: string; weight: number }>;
  scenes: Array<{ label: string; weight: number }>;
  emotions: Array<{ label: string; weight: number }>;
  props: Array<{ label: string; weight: number }>;
}

export interface VideoLogEntry {
  time: number;
  description: string;
  tags: string[];
}

export type FeedbackType = 'explicit_accept' | 'explicit_reject' | 'implicit_ignore';

export interface FeedbackRecord {
  timestamp: number;
  type: FeedbackType;
  queryContext: string;
  reason?: string;
}

export type ProcessingStatus = 'pending' | 'processing' | 'done' | 'error';

export interface VideoMetadata {
  processingStatus: ProcessingStatus;
  globalTags?: VideoGlobalTags;
  timeLog?: VideoLogEntry[];
  
  assetTrustScore: number;
  feedbackHistory: FeedbackRecord[]; 
}

export interface ProjectAsset {
  id: string;              
  projectId: string;       
  
  mediaUrl: string;        // Blob URL for playback/original (or external URL)
  thumbnailUrl: string;    // Blob URL for display/grid (or external URL)
  
  filename: string;
  mimeType: string;        
  source: 'upload' | 'external' | 'generated' | 'local';
  tags?: Record<string, any>; 
  metadata?: VideoMetadata;
  createdAt: number;
}

export interface Asset {
  id: string;              
  projectAssetId: string;  
  
  mediaUrl: string;        // Blob URL
  thumbnailUrl: string;    // Blob URL
  
  type: 'image' | 'video';
  name: string;
  source: 'upload' | 'library' | 'local'; 
  notes?: string;
  
  inPoint?: number;  // seconds
  outPoint?: number; // seconds
}

export interface Beat {
  id: string;
  order: number;
  content: string;
  
  tags: TagSchema;
  candidates: Asset[];
  mainAssetId?: string;
  
  duration: number;        
  userNotes?: string;
  assets: Asset[];
}

export interface ProjectSpecs {
  totalDuration: number;
  fps: 24 | 25 | 30 | 60;
  aspectRatio: '16:9' | '9:16' | '4:3' | '2.35:1' | '1:1';
}

export interface Project {
  id: string;
  title: string;
  logline?: string;
  synopsis?: string;
  scriptRaw: string;
  beats: Beat[];
  characters: Character[];
  library: ProjectAsset[]; 
  specs?: ProjectSpecs;
  createdAt: number;
  
  currentStage: WorkflowStage;
}

export interface SceneGroup {
  id: string;
  title: string; 
  beats: Beat[];
  startTime: number;
  duration: number;
}

export interface UserSettings {
  dna: {
    style: string;
    formatting: string;
    donts: string;
    persona: string;
  };
  localServer: {
    baseUrl: string;
  };
}
