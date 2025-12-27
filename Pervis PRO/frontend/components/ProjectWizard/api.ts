/**
 * 项目立项向导 - API 客户端
 * Phase 7: 前端 API 集成
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

// 通用请求函数
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API 请求失败: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// 类型定义
// ============================================================================

export interface ParseScriptRequest {
  script_content: string;
  project_id?: string;
  options?: Record<string, any>;
}

export interface SceneInfo {
  scene_id: string;
  scene_number: number;
  heading: string;
  location: string;
  time_of_day: string;
  description: string;
  characters: string[];
  estimated_duration: number;
}

export interface CharacterInfo {
  name: string;
  dialogue_count: number;
  first_appearance: number;
  tags: Record<string, string>;
}

export interface ParseScriptResponse {
  task_id: string;
  status: string;
  scenes: SceneInfo[];
  characters: CharacterInfo[];
  total_scenes: number;
  estimated_duration: number;
  logline?: string;
  synopsis?: string;
  source: string;
  error?: string;
}

export interface GenerateContentRequest {
  project_id: string;
  content_type: string;
  context: Record<string, any>;
  entity_name?: string;
}

export interface GenerateContentResponse {
  task_id: string;
  status: string;
  content_type: string;
  content: any;
  source: string;
  review_status?: string;
  suggestions: string[];
  error?: string;
}

export interface ProcessAssetsRequest {
  project_id: string;
  asset_paths: string[];
  auto_classify?: boolean;
}

export interface AssetProcessResult {
  asset_path: string;
  category: string;
  confidence: number;
  tags: string[];
  error?: string;
}

export interface ProcessAssetsResponse {
  task_id: string;
  status: string;
  results: AssetProcessResult[];
  total_processed: number;
  success_count: number;
  failed_count: number;
  source: string;
  error?: string;
}

export interface RecallAssetsRequest {
  scene_id: string;
  query: string;
  tags?: string[];
  strategy?: string;
}

export interface AssetCandidate {
  candidate_id: string;
  asset_id: string;
  asset_path: string;
  score: number;
  rank: number;
  tags: string[];
  match_reason: string;
}

export interface RecallAssetsResponse {
  scene_id: string;
  candidates: AssetCandidate[];
  total_searched: number;
  has_match: boolean;
  placeholder_message: string;
  error?: string;
}

export interface CreateProjectRequest {
  title: string;
  project_type: string;
  duration_minutes?: number;
  aspect_ratio?: string;
  frame_rate?: number;
  resolution?: string;
  script_content?: string;
  synopsis?: string;
  logline?: string;
  template_id?: string;
}

export interface CreateProjectResponse {
  success: boolean;
  project_id?: string;
  message: string;
  validation_errors: string[];
  warnings: string[];
}

export interface ValidateProjectRequest {
  title?: string;
  project_type?: string;
  duration_minutes?: number;
  aspect_ratio?: string;
  frame_rate?: number;
  resolution?: string;
  script_content?: string;
  synopsis?: string;
}

export interface ValidationError {
  field: string;
  message: string;
  severity: string;
}

export interface ValidateProjectResponse {
  is_valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  completion_percentage: number;
  missing_required: string[];
}

export interface ReviewContentRequest {
  project_id: string;
  content: any;
  content_type: string;
}

export interface ReviewContentResponse {
  status: string;
  passed_checks: string[];
  failed_checks: string[];
  suggestions: string[];
  reason: string;
  confidence: number;
}

export interface TaskStatusResponse {
  task_id: string;
  status: string;
  progress: number;
  message: string;
  result?: any;
  created_at: string;
  updated_at: string;
  error?: string;
}

export interface VersionInfo {
  version_id: string;
  version_name: string;
  version_number: number;
  content_type: string;
  entity_id?: string;
  entity_name?: string;
  source: string;
  status: string;
  created_at: string;
}

export interface AgentHealthStatus {
  status: string;
  agents: Record<string, string>;
  timestamp: string;
}

export interface MarketAnalysis {
  project_id: string;
  is_dynamic: boolean;
  target_audience?: {
    demographics?: string;
    psychographics?: string;
    viewing_habits?: string;
  };
  market_positioning?: {
    unique_selling_points?: string[];
    market_gap?: string;
  };
  competitor_analysis?: {
    similar_projects?: string[];
    differentiation?: string;
  };
  distribution_channels?: {
    primary?: string[];
    secondary?: string[];
    strategy?: string;
  };
}

// 图片生成相关类型
export interface GenerateCharacterImageRequest {
  character_name: string;
  character_bio?: string;
  tags?: Record<string, string>;
  style?: 'realistic' | 'anime' | 'concept_art' | 'cinematic' | 'illustration';
  character_id?: string;
}

export interface GenerateSceneImageRequest {
  scene_name: string;
  scene_description?: string;
  time_of_day?: string;
  style?: 'realistic' | 'anime' | 'concept_art' | 'cinematic' | 'illustration';
  scene_id?: string;
}

export interface ImageGenerationResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  image_url?: string;
  local_path?: string;
  thumbnail_path?: string;
  prompt: string;
  image_type: string;
  entity_id?: string;
  entity_name?: string;
  error?: string;
}

export interface ImageServiceStatus {
  configured: boolean;
  provider: string;
  message: string;
}

// ============================================================================
// API 函数
// ============================================================================

export const wizardApi = {
  // 剧本解析
  parseScript: (request: ParseScriptRequest): Promise<ParseScriptResponse> =>
    apiRequest('/api/wizard/parse-script', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 内容生成
  generateContent: (request: GenerateContentRequest): Promise<GenerateContentResponse> =>
    apiRequest('/api/wizard/generate-content', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 素材处理
  processAssets: (request: ProcessAssetsRequest): Promise<ProcessAssetsResponse> =>
    apiRequest('/api/wizard/process-assets', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 素材召回
  recallAssets: (request: RecallAssetsRequest): Promise<RecallAssetsResponse> =>
    apiRequest('/api/wizard/recall-assets', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 候选切换
  switchCandidate: (sceneId: string, fromRank: number, toRank: number): Promise<{
    success: boolean;
    candidate?: AssetCandidate;
    error?: string;
  }> =>
    apiRequest('/api/wizard/switch-candidate', {
      method: 'POST',
      body: JSON.stringify({
        scene_id: sceneId,
        from_rank: fromRank,
        to_rank: toRank,
      }),
    }),

  // 获取缓存候选
  getCachedCandidates: (sceneId: string): Promise<RecallAssetsResponse> =>
    apiRequest(`/api/wizard/cached-candidates/${sceneId}`),

  // 内容审核
  reviewContent: (request: ReviewContentRequest): Promise<ReviewContentResponse> =>
    apiRequest('/api/wizard/review-content', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 任务状态
  getTaskStatus: (taskId: string): Promise<TaskStatusResponse> =>
    apiRequest(`/api/wizard/task-status/${taskId}`),

  // 项目创建
  createProject: (request: CreateProjectRequest): Promise<CreateProjectResponse> =>
    apiRequest('/api/wizard/create-project', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 项目验证
  validateProject: (request: ValidateProjectRequest): Promise<ValidateProjectResponse> =>
    apiRequest('/api/wizard/validate-project', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 获取项目
  getProject: (projectId: string): Promise<any> =>
    apiRequest(`/api/wizard/project/${projectId}`),

  // 更新项目
  updateProject: (projectId: string, updates: Record<string, any>): Promise<any> =>
    apiRequest(`/api/wizard/project/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    }),

  // 删除项目
  deleteProject: (projectId: string): Promise<any> =>
    apiRequest(`/api/wizard/project/${projectId}`, {
      method: 'DELETE',
    }),

  // 列出项目
  listProjects: (params?: { status?: string; project_type?: string; limit?: number }): Promise<{
    projects: any[];
    total: number;
  }> => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.project_type) searchParams.set('project_type', params.project_type);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return apiRequest(`/api/wizard/projects${query ? `?${query}` : ''}`);
  },

  // 记录版本
  recordVersion: (request: {
    project_id: string;
    content_type: string;
    content: any;
    entity_id?: string;
    entity_name?: string;
    source?: string;
  }): Promise<{
    success: boolean;
    version?: VersionInfo;
    error?: string;
  }> =>
    apiRequest('/api/wizard/record-version', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 获取版本历史
  getVersionHistory: (projectId: string, params?: {
    content_type?: string;
    entity_id?: string;
    limit?: number;
  }): Promise<{
    versions: VersionInfo[];
    total: number;
  }> => {
    const searchParams = new URLSearchParams();
    if (params?.content_type) searchParams.set('content_type', params.content_type);
    if (params?.entity_id) searchParams.set('entity_id', params.entity_id);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const query = searchParams.toString();
    return apiRequest(`/api/wizard/version-history/${projectId}${query ? `?${query}` : ''}`);
  },

  // 健康检查
  checkHealth: (): Promise<AgentHealthStatus> =>
    apiRequest('/api/wizard/health'),

  // 市场分析
  analyzeMarket: (request: {
    project_id: string;
    project_type?: string;
    genre?: string;
  }): Promise<MarketAnalysis> =>
    apiRequest('/api/wizard/market-analysis', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 获取市场分析
  getMarketAnalysis: (projectId: string): Promise<MarketAnalysis> =>
    apiRequest(`/api/wizard/market-analysis/${projectId}`),

  // ============================================================================
  // 图片生成 API
  // ============================================================================

  // 检查图片生成服务状态
  getImageServiceStatus: (): Promise<ImageServiceStatus> =>
    apiRequest('/api/image-generation/status'),

  // 生成角色人设图
  generateCharacterImage: (request: GenerateCharacterImageRequest): Promise<ImageGenerationResponse> =>
    apiRequest('/api/image-generation/character', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 生成场景概念图
  generateSceneImage: (request: GenerateSceneImageRequest): Promise<ImageGenerationResponse> =>
    apiRequest('/api/image-generation/scene', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 获取图片生成任务状态
  getImageTaskStatus: (taskId: string): Promise<ImageGenerationResponse> =>
    apiRequest(`/api/image-generation/task/${taskId}`),

  // 草稿保存
  saveDraft: (draftId: string, data: {
    current_step: number;
    form_data: Record<string, any>;
    field_status?: Record<string, string>;
  }): Promise<{
    success: boolean;
    draft_id: string;
    updated_at: string;
  }> =>
    apiRequest(`/api/wizard/draft/${draftId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 草稿恢复
  loadDraft: (draftId: string): Promise<{
    draft_id: string;
    current_step: number;
    form_data: Record<string, any>;
    field_status: Record<string, string>;
    completion_percentage: number;
    created_at: string;
    updated_at: string;
  }> =>
    apiRequest(`/api/wizard/draft/${draftId}`),

  // 创建草稿
  createDraft: (projectId?: string): Promise<{
    draft_id: string;
    project_id?: string;
    created_at: string;
  }> =>
    apiRequest('/api/wizard/draft', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId }),
    }),

  // 轮询任务状态
  pollTaskStatus: async (
    taskId: string,
    options: {
      maxAttempts?: number;
      interval?: number;
      onProgress?: (status: TaskStatusResponse) => void;
    } = {}
  ): Promise<TaskStatusResponse> => {
    const { maxAttempts = 60, interval = 1000, onProgress } = options;
    
    for (let i = 0; i < maxAttempts; i++) {
      const status = await wizardApi.getTaskStatus(taskId);
      
      if (onProgress) {
        onProgress(status);
      }
      
      if (status.status === 'completed' || status.status === 'failed') {
        return status;
      }
      
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    
    throw new Error('任务轮询超时');
  },

  // ============================================================================
  // Phase 9: 视觉标签分析 API
  // ============================================================================

  // 分析参考图像
  analyzeImages: (request: {
    draft_id: string;
    images: Array<{
      image_id: string;
      image_path: string;
      image_type: 'character' | 'scene';
      related_id: string;
    }>;
  }): Promise<{
    task_id: string;
    status: string;
    agent: string;
    message: string;
  }> =>
    apiRequest('/api/wizard/analyze-images', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // 获取 AI 生成的标签
  getSuggestedTags: (draftId: string): Promise<{
    draft_id: string;
    character_tags: Array<{
      character_id: string;
      image_path: string;
      tags: Record<string, any>;
      confidence: number;
      confirmed: boolean;
    }>;
    scene_tags: Array<{
      scene_id: string;
      image_path: string;
      tags: Record<string, any>;
      confidence: number;
      confirmed: boolean;
    }>;
    status: string;
    error?: string;
  }> =>
    apiRequest(`/api/wizard/draft/${draftId}/suggested-tags`),

  // 确认标签
  confirmTags: (draftId: string, request: {
    character_tags: Array<{
      entity_id: string;
      image_path: string;
      tags: Record<string, any>;
      confirmed: boolean;
    }>;
    scene_tags: Array<{
      entity_id: string;
      image_path: string;
      tags: Record<string, any>;
      confirmed: boolean;
    }>;
  }): Promise<{
    success: boolean;
    message: string;
    asset_ids: string[];
    error?: string;
  }> =>
    apiRequest(`/api/wizard/draft/${draftId}/confirm-tags`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
};

export default wizardApi;
