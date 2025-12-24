/**
 * 简化版 Gemini Service - 调用真实后端 AI API
 * 所有 AI 功能通过 apiClient 调用后端 API，不返回 Mock 数据
 */

import { Beat, TagSchema, Asset, VideoMetadata, Character, ProjectAsset, FeedbackType } from "../types";
import { api } from "./api";
import * as apiClient from "./apiClient";

// --- 脚本分析结果接口 ---
interface ScriptAnalysisResult {
    beats: Beat[];
    characters: Character[];
    meta: {
        logline: string;
        synopsis: string;
    }
}

// --- 真实的脚本分析 (Real API Call) ---
export const analyzeScriptToStructure = async (scriptText: string): Promise<ScriptAnalysisResult> => {
    // Call the Bridge
    const result = await api.remoteAnalyzeScript(scriptText, 'parse');

    // Transform Backend Response to Frontend Model
    // Assuming Backend returns { beats: [], characters: [], meta: {} } matching our need
    // If backend keys differ, map them here.
    return {
        beats: result.beats || [],
        characters: result.characters || [],
        meta: result.meta || { logline: '', synopsis: '' }
    };
};

// --- 真实的视觉搜索 (Real API Call) ---
export const searchVisualAssets = async (query: string): Promise<Asset[]> => {
    const response = await api.remoteSearchAssets(query);

    // Map Backend SearchResult to Frontend Asset
    if (response.results) {
        return response.results.map((r: any) => ({
            id: `search-res-${r.asset_id}-${Date.now()}`, // Temporary View ID
            projectAssetId: r.asset_id,
            mediaUrl: r.preview_url || '', // Should be a valid URL from backend static
            thumbnailUrl: r.thumbnail_url || '',
            type: 'video',
            name: `Match: ${r.match_score.toFixed(2)}`,
            source: 'library',
            notes: r.match_reason
        }));
    }
    return [];
};

// --- 真实的视频分析 - 调用后端 AI API ---
export const analyzeVideoContent = async (fileBlob: Blob, filename: string): Promise<VideoMetadata> => {
    // 调用 apiClient 中的真实实现
    return await apiClient.analyzeVideoContent(fileBlob, filename);
};

// --- 真实的资产描述生成 - 调用后端 AI API ---
export const generateAssetDescription = async (fileBlob: Blob, filename: string): Promise<string> => {
    // 调用 apiClient 中的真实实现
    return await apiClient.generateAssetDescription(fileBlob, filename);
};

// --- 真实的标签重新生成 - 调用后端 AI API ---
export const regenerateBeatTags = async (content: string): Promise<TagSchema> => {
    // 调用 apiClient 中的真实实现
    const result = await apiClient.regenerateBeatTags(content);
    return result as TagSchema;
};

export const generateStructureFromSynopsis = async (title: string, logline: string, synopsis: string): Promise<ScriptAnalysisResult> => {
    const fullScript = `标题: ${title}\n概述: ${logline}\n\n${synopsis}`;
    return await analyzeScriptToStructure(fullScript);
};

export const smartBuildScript = async (novelText: string): Promise<ScriptAnalysisResult> => {
    // Call the Bridge (Creative Mode)
    const result = await api.remoteAnalyzeScript(novelText, 'smart');
    return {
        beats: result.beats || [],
        characters: result.characters || [],
        meta: result.meta || { logline: '', synopsis: '' }
    };
};

// --- 真实的反馈记录 - 调用后端 API ---
export const recordAssetFeedback = async (projectId: string, assetId: string, type: FeedbackType, queryContext: string): Promise<void> => {
    // 调用 apiClient 中的真实实现
    await apiClient.recordAssetFeedback(projectId, assetId, type, queryContext);
};

// --- 真实的 AI 粗剪 - 调用后端 AI API ---
export const performAIRoughCut = async (scriptContent: string, metadata: VideoMetadata): Promise<{
    inPoint: number;
    outPoint: number;
    confidence: number;
    reason: string;
}> => {
    // 调用 apiClient 中的真实实现
    return await apiClient.performAIRoughCut(scriptContent, metadata);
};