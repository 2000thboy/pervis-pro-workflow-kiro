
import { Project, ProjectAsset, UserSettings, VideoMetadata, Asset } from '../types';
import { db } from './db';
import { videoProcessor } from './videoProcessor';
import { generateAssetDescription, analyzeVideoContent } from './geminiService';

// Global fetch interceptor to handle missing API key errors
const originalFetch = window.fetch.bind(window);
window.fetch = async (input: RequestInfo, init?: RequestInit) => {
    const response = await originalFetch(input, init);
    if (!response.ok) {
        try {
            const txt = await response.clone().text();
            if (response.status === 400 && txt.includes('MISSING_API_KEY')) {
                const evt = new CustomEvent('missing-api-key', { detail: { message: txt } });
                window.dispatchEvent(evt);
            }
        } catch (e) {
            console.warn('Failed to process fetch error response', e);
        }
    }
    return response;
};
// Simple embedding function for MVP
const generateEmbedding = async (text: string): Promise<number[]> => {
    // Simple hash-based embedding for MVP
    const hash = text.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
    }, 0);

    // Generate a 128-dimensional vector based on the hash
    const vector = [];
    for (let i = 0; i < 128; i++) {
        vector.push(Math.sin(hash + i) * 0.5 + 0.5);
    }
    return vector;
};

const STORAGE_KEY_PROJECTS = 'previs_pro_projects_v1';
const STORAGE_KEY_SETTINGS = 'previs_pro_settings_v1';

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

const defaultSettings: UserSettings = {
    dna: { style: '', formatting: '', donts: '', persona: '' },
    localServer: { baseUrl: '' }
};

// Helper: Hydrate assets with fresh blob URLs from IndexedDB
const hydrateProject = async (project: Project): Promise<Project> => {
    // 1. Hydrate Library
    const hydratedLibrary = await Promise.all(project.library.map(async (asset) => {
        if (asset.source === 'upload') {
            try {
                const mediaFile = await db.getFile(asset.id);
                const thumbFile = await db.getFile(asset.id + '_thumb');

                let mediaUrl = asset.mediaUrl;
                let thumbnailUrl = asset.thumbnailUrl;

                if (mediaFile) {
                    mediaUrl = URL.createObjectURL(mediaFile.blob);
                }
                if (thumbFile) {
                    thumbnailUrl = URL.createObjectURL(thumbFile.blob);
                }
                // Fallback for image: if no thumb file, maybe it is the media file (legacy or image opt)
                if (!thumbFile && asset.mimeType.startsWith('image/') && mediaFile) {
                    thumbnailUrl = mediaUrl;
                }

                return { ...asset, mediaUrl, thumbnailUrl };
            } catch (e) {
                console.warn(`Failed to hydrate asset ${asset.id}`, e);
                return asset;
            }
        }
        return asset;
    }));

    // 2. Hydrate Beats (Assets inside beats)
    // We look up the fresh URLs from the hydratedLibrary to keep them in sync
    const hydratedBeats = project.beats.map(beat => {
        const hydratedBeatAssets = beat.assets.map(beatAsset => {
            const libraryAsset = hydratedLibrary.find(la => la.id === beatAsset.projectAssetId);
            if (libraryAsset) {
                return {
                    ...beatAsset,
                    mediaUrl: libraryAsset.mediaUrl,
                    thumbnailUrl: libraryAsset.thumbnailUrl
                };
            }
            return beatAsset;
        });

        const hydratedCandidates = beat.candidates?.map(cand => {
            const libraryAsset = hydratedLibrary.find(la => la.id === cand.projectAssetId);
            if (libraryAsset) {
                return {
                    ...cand,
                    mediaUrl: libraryAsset.mediaUrl,
                    thumbnailUrl: libraryAsset.thumbnailUrl
                };
            }
            return cand;
        }) || [];

        return { ...beat, assets: hydratedBeatAssets, candidates: hydratedCandidates };
    });

    return { ...project, library: hydratedLibrary, beats: hydratedBeats };
};

export const api = {

    // --- Projects ---

    async getProjects(): Promise<Project[]> {
        await delay(100);
        try {
            const raw = localStorage.getItem(STORAGE_KEY_PROJECTS);
            if (!raw) return [];
            const projects = JSON.parse(raw) as Project[];

            // Hydrate all projects on load to ensure valid Blob URLs
            const hydratedProjects = await Promise.all(projects.map(p => hydrateProject(p)));

            return hydratedProjects.sort((a, b) => b.createdAt - a.createdAt);
        } catch (e) {
            console.error("API: Failed to load projects", e);
            return [];
        }
    },

    async getProject(id: string): Promise<Project | null> {
        await delay(100);
        const projects = await this.getProjects(); // already hydrated
        return projects.find(p => p.id === id) || null;
    },

    async createProject(project: Project): Promise<Project> {
        await delay(100);
        // Save raw (without blobs, though JSON.stringify handles that naturally by ignoring blob refs if they were blobs, but here they are strings)
        // Note: Blob URLs are strings. Saving them to localStorage is fine, but they expire.
        // We rely on getProjects() to regenerate them.
        const projects = await this.getProjects();
        projects.unshift(project);
        // We persist the structure. The Blob URLs stored will be dead next reload, but IDs remain.
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
        return project;
    },

    async updateProject(id: string, updates: Partial<Project>): Promise<Project> {
        await delay(50);
        const projects = await this.getProjects();
        const index = projects.findIndex(p => p.id === id);

        if (index === -1) throw new Error(`Project ${id} not found`);

        const updatedProject = { ...projects[index], ...updates };
        projects[index] = updatedProject;
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));

        return updatedProject;
    },

    async remoteGetAsset(id: string): Promise<any> {
        // Implement GET /api/assets/{id}
        return {};
    },

    async remoteExportScript(projectId: string, format: 'docx' | 'pdf' | 'md'): Promise<any> {
        const response = await fetch(`http://localhost:8000/api/export/script`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId, format })
        });
        if (!response.ok) throw new Error(`Export Failed: ${response.statusText}`);
        return await response.json();
    },

    async remoteExportNLE(projectId: string, format: 'fcpxml' | 'edl'): Promise<any> {
        const response = await fetch(`http://localhost:8000/api/export/nle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_id: projectId, format, frame_rate: "24" })
        });
        if (!response.ok) throw new Error(`Export Failed: ${response.statusText}`);
        return await response.json();
    },

    async deleteProject(id: string): Promise<void> {
        await delay(100);
        const projects = await this.getProjects();
        const projectToDelete = projects.find(p => p.id === id);

        // Cleanup assets
        if (projectToDelete && projectToDelete.library) {
            for (const asset of projectToDelete.library) {
                if (asset.source === 'upload') {
                    await db.deleteFile(asset.id);
                    await db.deleteFile(asset.id + '_thumb');
                    await db.deleteVector(asset.id);
                }
            }
        }

        const filtered = projects.filter(p => p.id !== id);
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(filtered));
    },

    // --- Assets (Advanced Pipeline) ---

    async getProjectAssetById(assetId: string): Promise<ProjectAsset | null> {
        const projects = await this.getProjects();
        let foundAsset: ProjectAsset | undefined;

        for (const p of projects) {
            foundAsset = p.library?.find(a => a.id === assetId);
            if (foundAsset) break;
        }

        if (!foundAsset) return null;
        // The project is already hydrated by getProjects(), so foundAsset has valid URLs if they exist
        return foundAsset;
    },

    async updateAssetMetadata(projectId: string, assetId: string, metadataUpdates: Partial<VideoMetadata>): Promise<void> {
        const projects = await this.getProjects();
        const pIndex = projects.findIndex(p => p.id === projectId);
        if (pIndex === -1) return;

        const project = projects[pIndex];
        const aIndex = project.library.findIndex(a => a.id === assetId);
        if (aIndex === -1) return;

        // Merge Metadata
        const currentMeta = project.library[aIndex].metadata || { processingStatus: 'done', assetTrustScore: 0.5, feedbackHistory: [] };
        const newMeta = { ...currentMeta, ...metadataUpdates };

        project.library[aIndex].metadata = newMeta as VideoMetadata;

        // Persist
        projects[pIndex] = project;
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
    },

    async deleteAsset(projectId: string, assetId: string): Promise<void> {
        const projects = await this.getProjects();
        const pIndex = projects.findIndex(p => p.id === projectId);
        if (pIndex === -1) return;

        const project = projects[pIndex];
        const asset = project.library.find(a => a.id === assetId);

        if (asset && asset.source === 'upload') {
            await db.deleteFile(asset.id);
            await db.deleteFile(asset.id + '_thumb');
            await db.deleteVector(asset.id);
        }

        // Remove from library
        project.library = project.library.filter(a => a.id !== assetId);

        // Remove from Beats? Optional logic: keep but mark as missing, or remove. 
        // For now, let's leave beats referencing it (will show broken link) or filter.
        // Better to filter out of beats to avoid crash.
        project.beats = project.beats.map(b => ({
            ...b,
            assets: b.assets.filter(a => a.projectAssetId !== assetId),
            candidates: b.candidates?.filter(c => c.projectAssetId !== assetId) || [],
            mainAssetId: b.mainAssetId === assetId ? undefined : b.mainAssetId // Reset main if deleted
        }));

        projects[pIndex] = project;
        localStorage.setItem(STORAGE_KEY_PROJECTS, JSON.stringify(projects));
    },

    /**
     * Intelligent Asset Ingestion Pipeline:
     * 1. Check Restrictions (Time > 5min)
     * 2. Store Raw File (IndexedDB)
     * 3. Store Thumbnail (IndexedDB)
     * 4. AI Analysis
     */
    async uploadAsset(file: File, projectId: string, onProgress?: (status: string) => void): Promise<ProjectAsset> {

        // 0. RESTRICTION CHECK
        if (file.type.startsWith('video') && file.size > 200 * 1024 * 1024) {
            throw new Error("文件过大。MVP 阶段仅支持 200MB (约5分钟) 以下的素材。");
        }

        const assetId = `asset-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;

        // Initial Metadata State
        let metadata: VideoMetadata = {
            processingStatus: 'pending',
            assetTrustScore: 0.5,
            feedbackHistory: []
        };

        // 1. Store Media File
        if (onProgress) onProgress("Saving media to Local DB...");
        await db.saveFile({
            id: assetId,
            blob: file,
            mimeType: file.type,
            filename: file.name,
            createdAt: Date.now()
        });
        const mediaUrl = URL.createObjectURL(file);

        let thumbnailUrl = mediaUrl; // Default for images

        // 2. Video Processing (Thumbnail)
        if (file.type.startsWith('video')) {
            if (onProgress) onProgress("Generating Thumbnail...");
            try {
                const thumbnailBlob = await videoProcessor.generateThumbnail(file, 1.0);
                thumbnailUrl = URL.createObjectURL(thumbnailBlob);

                // Save Thumbnail to DB
                await db.saveFile({
                    id: assetId + '_thumb',
                    blob: thumbnailBlob,
                    mimeType: 'image/jpeg',
                    filename: file.name + '_thumb.jpg',
                    createdAt: Date.now()
                });

            } catch (e) {
                console.warn("Thumbnail failed", e);
                // Fallback: thumbnailUrl remains mediaUrl (browser might render video frame or icon)
            }

            // 3a. Video Semantic Analysis
            if (onProgress) onProgress("AI Analyzing Video Structure...");
            try {
                metadata.processingStatus = 'processing';
                const analysisResult = await analyzeVideoContent(file, file.name);
                metadata = { ...metadata, ...analysisResult };

                // 4. Vector Embedding
                if (onProgress) onProgress("Generating Embeddings...");
                const globalTags = analysisResult.globalTags;
                let descriptionForEmbedding = file.name;
                if (globalTags) {
                    const charStr = globalTags.characters?.map(c => c.label).join(', ') || '';
                    const actionStr = globalTags.actions?.map(c => c.label).join(', ') || '';
                    const sceneStr = globalTags.scenes?.map(c => c.label).join(', ') || '';
                    const moodStr = globalTags.emotions?.map(c => c.label).join(', ') || '';
                    descriptionForEmbedding = `Subject: ${charStr}. Action: ${actionStr}. Scene: ${sceneStr}. Mood: ${moodStr}. Filename: ${file.name}`;
                }

                const vector = await generateEmbedding(descriptionForEmbedding);
                await db.saveVector({ id: assetId, vector, text: descriptionForEmbedding });
            } catch (e) {
                console.error("Video Analysis Pipeline failed", e);
                metadata.processingStatus = 'error';
            }

        } else {
            // Image Processing
            if (onProgress) onProgress("AI Tagging Image...");
            try {
                metadata.processingStatus = 'processing';
                const description = await generateAssetDescription(file, file.name);
                metadata.processingStatus = 'done';

                const vector = await generateEmbedding(description);
                await db.saveVector({ id: assetId, vector, text: description });
            } catch (e) {
                metadata.processingStatus = 'error';
            }
        }

        const newAsset: ProjectAsset = {
            id: assetId,
            projectId,
            mediaUrl,
            thumbnailUrl,
            filename: file.name,
            mimeType: file.type,
            source: 'upload',
            metadata: metadata,
            createdAt: Date.now()
        };

        return newAsset;
    },

    // --- Settings ---

    async getSettings(): Promise<UserSettings> {
        await delay(100);
        try {
            const raw = localStorage.getItem(STORAGE_KEY_SETTINGS);
            if (!raw) return defaultSettings;
            return { ...defaultSettings, ...JSON.parse(raw) };
        } catch (e) {
            return defaultSettings;
        }
    },

    async saveSettings(settings: UserSettings): Promise<UserSettings> {
        await delay(200);
        localStorage.setItem(STORAGE_KEY_SETTINGS, JSON.stringify(settings));
        return settings;
    },

    // --- Remote Backend Integration (The Bridge) ---

    async remoteAnalyzeScript(content: string, mode: 'parse' | 'smart'): Promise<any> {
        try {
            const response = await fetch('http://localhost:8000/api/script/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: content,
                    mode: mode === 'smart' ? 'creative' : 'analytical',
                    project_id: 'temp_session' // In real flow, pass actual ID
                })
            });
            if (!response.ok) throw new Error(`Backend Error: ${response.statusText}`);
            return await response.json();
        } catch (e) {
            console.error("Remote Analysis Failed", e);
            throw e;
        }
    },

    async remoteSearchAssets(query: string, beatId?: string): Promise<any> {
        try {
            const response = await fetch('http://localhost:8000/api/search/semantic', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query_text: query,
                    beat_id: beatId || 'default_beat',
                    limit: 10
                })
            });
            if (!response.ok) throw new Error(`Backend Error: ${response.statusText}`);
            return await response.json();
        } catch (e) {
            console.error("Remote Search Failed", e);
            throw e;
        }
    },

    async remoteGenerateDemoScript(topic: string = 'random'): Promise<{
        title: string;
        logline: string;
        synopsis: string;
        script_content: string;
    }> {
        const response = await fetch('http://localhost:8000/api/script/demo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        if (!response.ok) {
            try {
                const errJson = await response.json();
                return errJson;
            } catch (e) {
                throw new Error("API Failure: " + response.statusText);
            }
        }
        return await response.json();
    },

    async checkBackendHealth(): Promise<boolean> {
        try {
            const res = await fetch('http://localhost:8000/api/health');
            return res.ok;
        } catch (e) {
            return false;
        }
    }
};
