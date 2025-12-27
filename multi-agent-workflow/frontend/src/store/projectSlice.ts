/**
 * 项目状态管理 Slice
 * 
 * Feature: multi-agent-workflow-core
 * 验证需求: Requirements 8.1, 8.3
 */
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Project, ProjectStatus } from '../types';
import { projectApi } from '../services/api';

interface ProjectSliceState {
  projects: Project[];
  selectedProject: Project | null;
  loading: boolean;
  error: string | null;
}

const initialState: ProjectSliceState = {
  projects: [],
  selectedProject: null,
  loading: false,
  error: null,
};

export const fetchAllProjects = createAsyncThunk(
  'projects/fetchAll',
  async (_, { rejectWithValue }) => {
    const response = await projectApi.getAllProjects();
    if (response.success && response.data) {
      return response.data;
    }
    return rejectWithValue(response.error || '获取项目列表失败');
  }
);

export const createProject = createAsyncThunk(
  'projects/create',
  async (projectData: Partial<Project>, { rejectWithValue }) => {
    const response = await projectApi.createProject(projectData);
    if (response.success && response.data) {
      return response.data;
    }
    return rejectWithValue(response.error || '创建项目失败');
  }
);

const projectSlice = createSlice({
  name: 'projects',
  initialState,
  reducers: {
    selectProject: (state, action: PayloadAction<string | null>) => {
      state.selectedProject = action.payload
        ? state.projects.find((p) => p.id === action.payload) || null
        : null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchAllProjects.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchAllProjects.fulfilled, (state, action) => {
        state.loading = false;
        state.projects = action.payload;
      })
      .addCase(fetchAllProjects.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      .addCase(createProject.fulfilled, (state, action) => {
        state.projects.push(action.payload);
        state.selectedProject = action.payload;
      });
  },
});

export const { selectProject, clearError } = projectSlice.actions;
export default projectSlice.reducer;
