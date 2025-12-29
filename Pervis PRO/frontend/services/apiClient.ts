/**
 * Pervis PRO 导演工作台 API 客户端
 * Phase 3: 替换geminiService，使用后端API
 */

import { Beat, Character, Asset, VideoMetadata, FeedbackType } from "../types";

// API配置
const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// 通用API请求函数
async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail || 
        errorData.message || 
        `API请求失败: ${response.status} ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error(`API请求失败 [${endpoint}]:`, error);
    throw error;
  }
}

// 文件上传专用函数
async function uploadFile(file: File): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/assets/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || 
      `文件上传失败: ${response.status} ${response.statusText}`
    );
  }

  return await response.json();
}

// 剧本分析结果接口
interface ScriptAnalysisResult {
  beats: Beat[];
  characters: Character[];
  meta: {
    logline: string;
    synopsis: string;
  };
}

// 搜索结果接口
interface SearchResult {
  asset_id: string;
  segment_id: string;
  match_score: number;
  match_reason: string;
  preview_url: string;
  thumbnail_url?: string;
  tags_matched: string[];
}

interface SearchResponse {
  results: SearchResult[];
  total_matches: number;
  search_time: number;
  query_info?: any;
}

// P0 Fix: 轮询配置接口
interface PollingOptions {
  maxAttempts?: number;
  initialDelay?: number;
  maxDelay?: number;
  backoffFactor?: number;
}

// 资产状态接口
interface AssetStatus {
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  progress: number;
  proxy_url?: string;
  thumbnail_url?: string;
  segments?: Array<{
    id: string;
    start_time: number;
    end_time: number;
    description: string;
    tags: {
      emotions: string[];
      scenes: string[];
      actions: string[];
      cinematography: string[];
    };
  }>;
  error_message?: string;
}

/**
 * P0 Fix: 统一的状态轮询函数
 */
export const pollAssetStatus = async (
  assetId: string,
  options: PollingOptions = {}
): Promise<AssetStatus> => {
  const {
    maxAttempts = 20,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 1.5
  } = options;

  let attempts = 0;
  let delay = initialDelay;

  while (attempts < maxAttempts) {
    try {
      const status = await getAssetStatus(assetId);
      
      // 如果处理完成或出错，直接返回
      if (status.status === 'completed' || status.status === 'error') {
        return status;
      }
      
      // 如果还在处理中，等待后继续轮询
      if (attempts < maxAttempts - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
        
        // P0 Fix: 指数退避，但不超过最大延迟
        delay = Math.min(delay * backoffFactor, maxDelay);
      }
      
      attempts++;
      
    } catch (error) {
      console.error(`轮询第${attempts + 1}次失败:`, error);
      attempts++;
      
      if (attempts >= maxAttempts) {
        throw new Error(`轮询失败，已重试${maxAttempts}次`);
      }
      
      // 出错时也要等待
      await new Promise(resolve => setTimeout(resolve, delay));
      delay = Math.min(delay * backoffFactor, maxDelay);
    }
  }
  
  throw new Error(`轮询超时，已尝试${maxAttempts}次`);
};

/**
 * 剧本分析 - 替换 analyzeScriptToStructure
 */
export const analyzeScriptToStructure = async (
  scriptText: string,
  title: string = "未命名项目",
  logline?: string
): Promise<ScriptAnalysisResult> => {
  try {
    const response = await apiRequest<{
      status: string;
      beats: any[];
      characters: any[];
      processing_time: number;
      project_id: string;
    }>('/api/script/analyze', {
      method: 'POST',
      body: JSON.stringify({
        script_text: scriptText,
        title,
        logline,
        mode: 'parse'
      }),
    });

    if (response.status !== 'success') {
      throw new Error('剧本分析失败');
    }

    // 转换后端数据格式为前端格式
    const beats: Beat[] = response.beats.map((beat: any, index: number) => ({
      id: beat.id,
      order: index,
      content: beat.content,
      tags: {
        scene_slug: beat.scene_tags?.[0] || '',
        location_type: 'INT',
        time_of_day: 'DAY',
        primary_emotion: beat.emotion_tags?.[0] || '',
        key_action: beat.action_tags?.[0] || '',
        visual_notes: beat.cinematography_tags?.join(', ') || '',
        shot_type: 'WIDE'
      },
      candidates: [],
      assets: [],
      duration: beat.duration_estimate || 2.0,
      userNotes: ''
    }));

    const characters: Character[] = response.characters.map((char: any) => ({
      id: char.id,
      name: char.name,
      role: char.role,
      description: char.description,
      traits: []
    }));

    return {
      beats,
      characters,
      meta: {
        logline: logline || "AI生成的故事概述",
        synopsis: "基于剧本分析生成的故事梗概"
      }
    };

  } catch (error) {
    console.error('剧本分析失败:', error);
    throw new Error(`剧本分析失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

/**
 * 视频内容分析 - 替换 analyzeVideoContent
 */
export const analyzeVideoContent = async (
  fileBlob: Blob, 
  filename: string
): Promise<VideoMetadata> => {
  try {
    // 1. 上传文件
    const file = new File([fileBlob], filename, { type: fileBlob.type });
    const uploadResponse = await uploadFile(file);
    
    if (!uploadResponse.asset_id) {
      throw new Error('文件上传失败');
    }

    // 2. P0 Fix: 使用统一轮询函数
    const assetId = uploadResponse.asset_id;
    const finalStatus = await pollAssetStatus(assetId, {
      maxAttempts: 30,
      initialDelay: 2000,
      maxDelay: 8000,
      backoffFactor: 1.3
    });

    if (finalStatus.status === 'error') {
      throw new Error(finalStatus.error_message || '视频处理失败');
    }

    // 3. 转换为VideoMetadata格式
    return {
      processingStatus: 'done',
      globalTags: {
        characters: [],
        actions: [],
        scenes: [],
        emotions: [],
        props: []
      },
      timeLog: finalStatus.segments?.map(seg => ({
        time: seg.start_time,
        description: seg.description,
        tags: [
          ...seg.tags.emotions,
          ...seg.tags.scenes,
          ...seg.tags.actions,
          ...seg.tags.cinematography
        ]
      })) || [],
      assetTrustScore: 0.5,
      feedbackHistory: []
    };

  } catch (error) {
    console.error('视频分析失败:', error);
    throw new Error(`视频分析失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

/**
 * 获取资产处理状态
 */
export const getAssetStatus = async (assetId: string): Promise<AssetStatus> => {
  return await apiRequest<AssetStatus>(`/api/assets/${assetId}/status`);
};

/**
 * 语义搜索 - 替换 searchVisualAssets
 */
export const searchVisualAssets = async (
  query: string,
  beatId?: string,
  fuzziness: number = 0.7
): Promise<Asset[]> => {
  try {
    // 从查询文本中提取标签 (简化版本)
    const queryTags = extractTagsFromQuery(query);
    
    const response = await apiRequest<SearchResponse>('/api/search/semantic', {
      method: 'POST',
      body: JSON.stringify({
        beat_id: beatId || 'default_beat',
        query_tags: queryTags,
        fuzziness,
        limit: 10
      }),
    });

    // 转换搜索结果为Asset格式
    return response.results.map((result: SearchResult) => ({
      id: `search-${result.asset_id}-${result.segment_id}`,
      projectAssetId: result.asset_id,
      mediaUrl: result.preview_url,
      thumbnailUrl: result.thumbnail_url || '',
      type: 'video' as const,
      name: `匹配片段 (${(result.match_score * 100).toFixed(0)}%)`,
      source: 'library' as const,
      notes: result.match_reason
    }));

  } catch (error) {
    console.error('语义搜索失败:', error);
    // 返回空数组而不是抛出错误，保持UI稳定
    return [];
  }
};

/**
 * 从查询文本提取标签 (简化版本)
 */
function extractTagsFromQuery(query: string): {
  emotions: string[];
  scenes: string[];
  actions: string[];
  cinematography: string[];
} {
  const emotionKeywords = ['快乐', '悲伤', '愤怒', '恐惧', '惊讶', '厌恶', '紧张', '兴奋', '平静', '神秘'];
  const sceneKeywords = ['室内', '室外', '夜晚', '白天', '黄昏', '清晨', '街道', '房间', '办公室', '公园'];
  const actionKeywords = ['跑步', '走路', '说话', '战斗', '拥抱', '哭泣', '笑', '思考', '工作', '睡觉'];
  const cinematographyKeywords = ['特写', '中景', '远景', '俯拍', '仰拍', '跟拍', '推拉', '摇摆', '手持', '稳定'];

  return {
    emotions: emotionKeywords.filter(keyword => query.includes(keyword)),
    scenes: sceneKeywords.filter(keyword => query.includes(keyword)),
    actions: actionKeywords.filter(keyword => query.includes(keyword)),
    cinematography: cinematographyKeywords.filter(keyword => query.includes(keyword))
  };
}

/**
 * 记录反馈 - 替换 recordAssetFeedback
 */
export const recordAssetFeedback = async (
  projectId: string,
  assetId: string,
  type: FeedbackType,
  queryContext: string,
  segmentId?: string
): Promise<void> => {
  try {
    await apiRequest('/api/feedback/record', {
      method: 'POST',
      body: JSON.stringify({
        beat_id: projectId, // 使用projectId作为beat_id的临时方案
        asset_id: assetId,
        segment_id: segmentId || 'default_segment',
        action: type === 'explicit_accept' ? 'accept' : 'reject',
        context: queryContext
      }),
    });
  } catch (error) {
    console.error('反馈记录失败:', error);
    // 不抛出错误，避免影响用户体验
  }
};

/**
 * AI粗剪 - 调用真实后端 AI API
 */
export const performAIRoughCut = async (
  scriptContent: string,
  metadata: VideoMetadata
): Promise<{
  inPoint: number;
  outPoint: number;
  confidence: number;
  reason: string;
}> => {
  try {
    // 构建视频标签数据
    const videoTags = {
      globalTags: metadata.globalTags || {},
      timeLog: metadata.timeLog || [],
      assetTrustScore: metadata.assetTrustScore || 0.5
    };

    const response = await apiRequest<{
      status: string;
      inPoint?: number;
      outPoint?: number;
      confidence?: number;
      reason?: string;
      message?: string;
    }>('/api/ai/rough-cut', {
      method: 'POST',
      body: JSON.stringify({
        script_content: scriptContent,
        video_tags: videoTags
      }),
    });

    if (response.status === 'error') {
      throw new Error(response.message || 'AI粗剪分析失败');
    }

    return {
      inPoint: response.inPoint ?? 0,
      outPoint: response.outPoint ?? 5,
      confidence: response.confidence ?? 0.5,
      reason: response.reason ?? 'AI分析完成'
    };

  } catch (error) {
    console.error('AI粗剪失败:', error);
    throw new Error(`AI粗剪失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

/**
 * 生成资产描述 - 调用真实后端 AI API
 */
export const generateAssetDescription = async (
  _fileBlob: Blob,
  filename: string
): Promise<string> => {
  try {
    const response = await apiRequest<{
      status: string;
      description: string;
    }>('/api/ai/generate-description', {
      method: 'POST',
      body: JSON.stringify({
        asset_id: `temp-${Date.now()}`,
        filename: filename,
        metadata: {}
      }),
    });

    return response.description;

  } catch (error) {
    console.error('生成资产描述失败:', error);
    throw new Error(`生成资产描述失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

/**
 * 重新生成Beat标签 - 调用真实后端 AI API
 */
export const regenerateBeatTags = async (content: string): Promise<any> => {
  try {
    const response = await apiRequest<{
      status: string;
      data?: any;
      message?: string;
    }>('/api/ai/generate-tags', {
      method: 'POST',
      body: JSON.stringify({
        content: content
      }),
    });

    if (response.status === 'error') {
      throw new Error(response.message || '标签生成失败');
    }

    return response.data || {
      scene_slug: "INT. LOCATION - DAY",
      location_type: "INT",
      time_of_day: "DAY",
      primary_emotion: "neutral",
      key_action: "dialogue",
      visual_notes: "AI生成的视觉备注",
      shot_type: "MEDIUM"
    };

  } catch (error) {
    console.error('重新生成标签失败:', error);
    throw new Error(`重新生成标签失败: ${error instanceof Error ? error.message : '未知错误'}`);
  }
};

/**
 * 从概要生成结构 - 替换 generateStructureFromSynopsis
 */
export const generateStructureFromSynopsis = async (
  title: string,
  logline: string,
  synopsis: string
): Promise<ScriptAnalysisResult> => {
  const fullScript = `标题: ${title}\n概述: ${logline}\n\n${synopsis}`;
  return await analyzeScriptToStructure(fullScript, title, logline);
};

/**
 * 智能构建剧本 - 替换 smartBuildScript
 */
export const smartBuildScript = async (novelText: string): Promise<ScriptAnalysisResult> => {
  return await analyzeScriptToStructure(novelText, "智能构建项目");
};

/**
 * 健康检查
 */
export const checkHealth = async (): Promise<any> => {
  return await apiRequest('/api/health');
};

// 转录相关接口
interface TranscriptionData {
  asset_id: string;
  full_text: string;
  language: string;
  duration: number;
  segments: Array<{
    id: number;
    start_time: number;
    end_time: number;
    text: string;
    confidence: number;
    words: Array<{
      word: string;
      start: number;
      end: number;
      probability: number;
    }>;
  }>;
  statistics: {
    total_segments: number;
    total_words: number;
    average_confidence: number;
    words_per_minute: number;
  };
}

interface TranscriptionStatus {
  status: 'not_transcribed' | 'completed';
  has_transcription: boolean;
  language?: string;
  duration?: number;
  segments_count?: number;
  statistics?: any;
}

interface TranscriptionSearchResult {
  asset_id: string;
  filename: string;
  language: string;
  matching_segments: Array<{
    segment_id: number;
    start_time: number;
    end_time: number;
    text: string;
    confidence: number;
  }>;
}

/**
 * 为资产进行音频转录
 */
export const transcribeAsset = async (
  assetId: string,
  forceRetranscribe: boolean = false
): Promise<{
  status: string;
  transcription: TranscriptionData;
  processing_info: any;
}> => {
  return await apiRequest(`/api/transcription/transcribe/${assetId}`, {
    method: 'POST',
    body: JSON.stringify({
      asset_id: assetId,
      force_retranscribe: forceRetranscribe
    }),
  });
};

/**
 * 获取资产转录状态
 */
export const getTranscriptionStatus = async (assetId: string): Promise<TranscriptionStatus> => {
  return await apiRequest(`/api/transcription/status/${assetId}`);
};

/**
 * 获取资产转录数据
 */
export const getTranscriptionData = async (assetId: string): Promise<{
  status: string;
  transcription: TranscriptionData;
}> => {
  return await apiRequest(`/api/transcription/data/${assetId}`);
};

/**
 * 在转录文本中搜索关键词
 */
export const searchTranscriptionText = async (
  query: string,
  limit: number = 10
): Promise<{
  status: string;
  query: string;
  results: TranscriptionSearchResult[];
  total_matches: number;
}> => {
  return await apiRequest('/api/transcription/search', {
    method: 'POST',
    body: JSON.stringify({
      query,
      limit
    }),
  });
};

/**
 * 获取转录模型信息
 */
export const getTranscriptionModelInfo = async (): Promise<{
  status: string;
  model_info: {
    available: boolean;
    model_size: string;
    device: string;
    supported_languages: number;
    features: any;
  };
  supported_languages: string[];
}> => {
  return await apiRequest('/api/transcription/model/info');
};

/**
 * 估算转录处理时间
 */
export const estimateTranscriptionTime = async (duration: number): Promise<{
  status: string;
  audio_duration: number;
  estimated_processing_time: number;
  model_size: string;
}> => {
  return await apiRequest(`/api/transcription/estimate?duration=${duration}`, {
    method: 'POST',
  });
};

// 多模态搜索相关接口
interface MultimodalSearchRequest {
  query: string;
  beat_id?: string;
  search_modes?: string[];  // ['semantic', 'transcription', 'visual']
  weights?: { [key: string]: number };  // {'semantic': 0.4, 'transcription': 0.3, 'visual': 0.3}
  fuzziness?: number;
  limit?: number;
}

interface MultimodalSearchResult {
  asset_id: string;
  filename: string;
  final_score: number;
  match_modes: string[];
  match_details: { [key: string]: any };
  multimodal_reason: string;
  proxy_url?: string;
  thumbnail_url?: string;
}

/**
 * 多模态综合搜索
 */
export const multimodalSearch = async (request: MultimodalSearchRequest): Promise<{
  status: string;
  query: string;
  query_intent: any;
  search_modes: string[];
  weights: { [key: string]: number };
  results: MultimodalSearchResult[];
  total_matches: number;
  individual_results: { [key: string]: number };
}> => {
  return await apiRequest('/api/multimodal/search', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * 纯视觉特征搜索
 */
export const visualSearch = async (query: string, visualTags?: { [key: string]: string }, limit: number = 10): Promise<{
  status: string;
  query: string;
  results: any[];
  total_matches: number;
}> => {
  return await apiRequest('/api/multimodal/search/visual', {
    method: 'POST',
    body: JSON.stringify({
      query,
      visual_tags: visualTags,
      limit
    }),
  });
};

/**
 * 为资产进行视觉特征分析
 */
export const analyzeVisualFeatures = async (
  assetId: string,
  sampleInterval: number = 2.0,
  forceReanalyze: boolean = false
): Promise<{
  status: string;
  message: string;
  visual_analysis: any;
}> => {
  return await apiRequest(`/api/multimodal/analyze/visual/${assetId}`, {
    method: 'POST',
    body: JSON.stringify({
      asset_id: assetId,
      sample_interval: sampleInterval,
      force_reanalyze: forceReanalyze
    }),
  });
};

/**
 * 获取多模态模型信息
 */
export const getMultimodalModelInfo = async (): Promise<{
  status: string;
  multimodal_capabilities: any;
  supported_search_modes: string[];
  default_weights: { [key: string]: number };
}> => {
  return await apiRequest('/api/multimodal/model/info');
};

// 批量处理相关接口
interface BatchUploadResponse {
  task_ids: string[];
  total_files: number;
  estimated_processing_time: number;
}

interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  result?: any;
  error?: string;
  processing_time: number;
}

/**
 * 批量上传资产文件
 */
export const batchUploadAssets = async (
  files: File[],
  projectId: string,
  priority: string = "normal",
  enableTranscription: boolean = true,
  enableVisualAnalysis: boolean = true
): Promise<BatchUploadResponse> => {
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });
  
  formData.append('project_id', projectId);
  formData.append('priority', priority);
  formData.append('enable_transcription', enableTranscription.toString());
  formData.append('enable_visual_analysis', enableVisualAnalysis.toString());

  const response = await fetch(`${API_BASE_URL}/api/batch/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || 
      `批量上传失败: ${response.status} ${response.statusText}`
    );
  }

  return await response.json();
};

/**
 * 获取批量任务状态
 */
export const getBatchTaskStatus = async (taskId: string): Promise<TaskStatus> => {
  return await apiRequest(`/api/batch/task/${taskId}`);
};

/**
 * 取消批量任务
 */
export const cancelBatchTask = async (taskId: string): Promise<{
  status: string;
  message: string;
}> => {
  return await apiRequest(`/api/batch/task/${taskId}/cancel`, {
    method: 'POST',
  });
};

/**
 * 获取批量处理队列状态
 */
export const getBatchQueueStatus = async (): Promise<{
  status: string;
  queue_status: {
    queue_size: number;
    running_tasks: number;
    completed_tasks: number;
    stats: any;
    is_running: boolean;
    active_workers: number;
  };
}> => {
  return await apiRequest('/api/batch/queue/status');
};

/**
 * 获取批量任务历史
 */
export const getBatchTaskHistory = async (limit: number = 100): Promise<{
  status: string;
  tasks: any[];
  total_count: number;
}> => {
  return await apiRequest(`/api/batch/tasks/history?limit=${limit}`);
};

/**
 * 获取处理统计信息
 */
export const getProcessingStats = async (): Promise<{
  status: string;
  processing_stats: any;
  system_stats: {
    cpu_percent: number;
    memory_percent: number;
    disk_usage: number;
    load_average: number[];
  };
  queue_info: {
    queue_size: number;
    running_tasks: number;
    active_workers: number;
  };
}> => {
  return await apiRequest('/api/batch/stats');
};

/**
 * 处理单个资产
 */
export const processSingleAsset = async (
  assetId: string,
  taskType: string,  // 'video_processing', 'transcription', 'visual_analysis'
  priority: string = "normal",
  parameters?: { [key: string]: any }
): Promise<{
  status: string;
  task_id: string;
  message: string;
}> => {
  return await apiRequest(`/api/batch/process/asset/${assetId}`, {
    method: 'POST',
    body: JSON.stringify({
      task_type: taskType,
      priority,
      parameters
    }),
  });
};

// 为了向后兼容，提供一个简化的embedding生成
export const generateEmbedding = async (text: string): Promise<number[]> => {
  // 返回一个简单的哈希向量作为占位符
  const hash = text.split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
    return a & a;
  }, 0);
  
  // 生成一个384维的向量 (与all-MiniLM-L6-v2兼容)
  const vector = new Array(384).fill(0).map((_, i) => 
    Math.sin(hash + i) * 0.1
  );
  
  return vector;
};

// ==================== 导出功能 API ====================

interface ScriptExportRequest {
  project_id: string;
  format: 'docx' | 'pdf';
  include_beats?: boolean;
  include_tags?: boolean;
  include_metadata?: boolean;
  template?: string;
}

interface BeatBoardExportRequest {
  project_id: string;
  format: 'png' | 'jpg';
  width?: number;
  height?: number;
  quality?: number;
  beat_ids?: string[];
}

/**
 * 导出剧本文档
 */
export const exportScript = async (request: ScriptExportRequest): Promise<{
  status: string;
  export_id: string;
  file_path: string;
  file_size: number;
  download_url: string;
}> => {
  return await apiRequest('/api/export/script', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * 导出BeatBoard图片
 */
export const exportBeatBoard = async (request: BeatBoardExportRequest): Promise<{
  status: string;
  export_id: string;
  file_path: string;
  file_size: number;
  download_url: string;
}> => {
  return await apiRequest('/api/export/beatboard', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * 下载导出文件
 */
export const downloadExport = async (exportId: string): Promise<Blob> => {
  const response = await fetch(`${API_BASE_URL}/api/export/download/${exportId}`);
  
  if (!response.ok) {
    throw new Error(`下载失败: ${response.status} ${response.statusText}`);
  }
  
  return await response.blob();
};

/**
 * 获取导出历史
 */
export const getExportHistory = async (projectId: string): Promise<{
  status: string;
  project_id: string;
  history: Array<{
    id: string;
    export_type: string;
    file_format: string;
    file_size: number;
    status: string;
    created_at: string;
  }>;
}> => {
  return await apiRequest(`/api/export/history/${projectId}`);
};

// ==================== 标签管理 API ====================

interface TagHierarchyUpdate {
  asset_id: string;
  tag_id: string;
  parent_id?: string | null;
  order?: number;
}

interface TagWeightUpdate {
  asset_id: string;
  tag_id: string;
  weight: number;
}

interface BatchTagUpdate {
  asset_id: string;
  updates: Array<{
    tag_id: string;
    weight?: number;
    parent_id?: string | null;
    order?: number;
  }>;
}

/**
 * 获取视频标签
 */
export const getVideoTags = async (assetId: string): Promise<{
  status: string;
  asset_id: string;
  tags: any[];
}> => {
  return await apiRequest(`/api/tags/${assetId}`);
};

/**
 * 更新标签层级
 */
export const updateTagHierarchy = async (request: TagHierarchyUpdate): Promise<{
  status: string;
  message: string;
}> => {
  return await apiRequest('/api/tags/hierarchy', {
    method: 'PUT',
    body: JSON.stringify(request),
  });
};

/**
 * 更新标签权重
 */
export const updateTagWeight = async (request: TagWeightUpdate): Promise<{
  status: string;
  message: string;
}> => {
  return await apiRequest('/api/tags/weight', {
    method: 'PUT',
    body: JSON.stringify(request),
  });
};

/**
 * 批量更新标签
 */
export const batchUpdateTags = async (request: BatchTagUpdate): Promise<{
  status: string;
  message: string;
  updated_count: number;
}> => {
  return await apiRequest('/api/tags/batch-update', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// ==================== 向量分析 API ====================

interface SimilarityRequest {
  query: string;
  asset_ids?: string[];
  top_k?: number;
}

interface MatchExplanationRequest {
  query: string;
  asset_id: string;
}

interface SaveTestCaseRequest {
  name: string;
  query: string;
  expected_results: string[];
}

/**
 * 计算相似度
 */
export const calculateSimilarity = async (request: SimilarityRequest): Promise<{
  status: string;
  query: string;
  results: Array<{
    asset_id: string;
    filename: string;
    similarity_score: number;
    matched_tags: string[];
  }>;
  total_matches: number;
}> => {
  return await apiRequest('/api/vector/similarity', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * 解释匹配结果
 */
export const explainMatch = async (request: MatchExplanationRequest): Promise<{
  status: string;
  query: string;
  asset_id: string;
  explanation: string;
  matched_keywords: string[];
  tag_contributions: { [key: string]: number };
}> => {
  return await apiRequest('/api/vector/explain', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * 保存测试案例
 */
export const saveTestCase = async (request: SaveTestCaseRequest): Promise<{
  status: string;
  test_case_id: string;
  message: string;
}> => {
  return await apiRequest('/api/vector/test-case', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

/**
 * 获取所有测试案例
 */
export const getTestCases = async (): Promise<{
  status: string;
  test_cases: Array<{
    id: string;
    name: string;
    query: string;
    status: string;
    expected_count: number;
    actual_count: number;
    created_at: string;
  }>;
}> => {
  return await apiRequest('/api/vector/test-cases');
};


// ==================== AI 服务管理 API ====================

/**
 * AI 服务状态接口
 */
interface AIServiceInfo {
  status: 'available' | 'unavailable' | 'unknown';
  message: string;
  url?: string;
  model?: string;
  configured?: boolean;
}

interface AIServicesStatus {
  ollama: AIServiceInfo;
  gemini: AIServiceInfo;
  current_provider: string;
  auto_fallback: boolean;
}

/**
 * 获取所有 AI 服务的状态
 * 用于显示服务选择界面
 */
export const getAIServicesStatus = async (): Promise<{
  status: string;
  services: AIServicesStatus;
}> => {
  return await apiRequest('/api/ai/services');
};

/**
 * 切换 AI 服务提供者
 * @param provider 目标服务: 'ollama', 'gemini', 'auto'
 */
export const switchAIProvider = async (provider: 'ollama' | 'gemini' | 'auto'): Promise<{
  status: string;
  message: string;
  previous_provider: string;
  current_provider: string;
  note: string;
}> => {
  return await apiRequest('/api/ai/switch-provider', {
    method: 'POST',
    body: JSON.stringify({ provider }),
  });
};

/**
 * 检查 AI 服务健康状态
 */
export const checkAIHealth = async (): Promise<{
  status: 'healthy' | 'unhealthy';
  provider: string | null;
  message: string;
}> => {
  return await apiRequest('/api/ai/health');
};
