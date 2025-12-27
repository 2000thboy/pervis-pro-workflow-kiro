/**
 * 项目立项向导 - 上下文管理
 * Phase 5: 前端向导组件
 */

import React, { createContext, useContext, useReducer, useCallback } from 'react';
import {
  WizardState,
  WizardContextType,
  WizardStep,
  BasicInfoData,
  ScriptData,
  CharacterInfo,
  SceneInfo,
  ReferenceAsset,
  AgentStatus,
  DEFAULT_WIZARD_STATE
} from './types';
import { wizardApi } from './api';

// Action 类型
type WizardAction =
  | { type: 'SET_STEP'; payload: WizardStep }
  | { type: 'UPDATE_BASIC_INFO'; payload: Partial<BasicInfoData> }
  | { type: 'UPDATE_SCRIPT'; payload: Partial<ScriptData> }
  | { type: 'UPDATE_CHARACTERS'; payload: CharacterInfo[] }
  | { type: 'UPDATE_SCENES'; payload: SceneInfo[] }
  | { type: 'ADD_REFERENCE'; payload: ReferenceAsset }
  | { type: 'REMOVE_REFERENCE'; payload: string }
  | { type: 'UPDATE_REFERENCE'; payload: { id: string; data: Partial<ReferenceAsset> } }
  | { type: 'SET_AGENT_STATUS'; payload: { agentName: string; status: Partial<AgentStatus> } }
  | { type: 'SET_VALIDATION_ERRORS'; payload: { errors: any[]; completion: number } }
  | { type: 'SET_PROJECT_ID'; payload: string }
  | { type: 'RESET' };

// Reducer
function wizardReducer(state: WizardState, action: WizardAction): WizardState {
  switch (action.type) {
    case 'SET_STEP':
      return { ...state, currentStep: action.payload };

    case 'UPDATE_BASIC_INFO':
      return {
        ...state,
        basicInfo: { ...state.basicInfo, ...action.payload },
        isDirty: true
      };

    case 'UPDATE_SCRIPT':
      return {
        ...state,
        script: { ...state.script, ...action.payload },
        isDirty: true
      };

    case 'UPDATE_CHARACTERS':
      return {
        ...state,
        characters: action.payload,
        isDirty: true
      };

    case 'UPDATE_SCENES':
      return {
        ...state,
        scenes: action.payload,
        isDirty: true
      };

    case 'ADD_REFERENCE':
      return {
        ...state,
        references: [...state.references, action.payload],
        isDirty: true
      };

    case 'REMOVE_REFERENCE':
      return {
        ...state,
        references: state.references.filter(r => r.id !== action.payload),
        isDirty: true
      };

    case 'UPDATE_REFERENCE':
      return {
        ...state,
        references: state.references.map(r =>
          r.id === action.payload.id ? { ...r, ...action.payload.data } : r
        ),
        isDirty: true
      };

    case 'SET_AGENT_STATUS': {
      const existingIndex = state.agentStatuses.findIndex(
        a => a.agentName === action.payload.agentName
      );
      const newStatuses = [...state.agentStatuses];
      
      if (existingIndex >= 0) {
        newStatuses[existingIndex] = {
          ...newStatuses[existingIndex],
          ...action.payload.status
        };
      } else {
        newStatuses.push({
          agentName: action.payload.agentName,
          status: 'idle',
          message: '',
          progress: 0,
          ...action.payload.status
        });
      }
      
      return { ...state, agentStatuses: newStatuses };
    }

    case 'SET_VALIDATION_ERRORS':
      return {
        ...state,
        validationErrors: action.payload.errors,
        completionPercentage: action.payload.completion
      };

    case 'SET_PROJECT_ID':
      return { ...state, projectId: action.payload, isDirty: false };

    case 'RESET':
      return DEFAULT_WIZARD_STATE;

    default:
      return state;
  }
}

// Context
const WizardContext = createContext<WizardContextType | null>(null);

// Provider
export const WizardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(wizardReducer, DEFAULT_WIZARD_STATE);

  const setStep = useCallback((step: WizardStep) => {
    dispatch({ type: 'SET_STEP', payload: step });
  }, []);

  const updateBasicInfo = useCallback((data: Partial<BasicInfoData>) => {
    dispatch({ type: 'UPDATE_BASIC_INFO', payload: data });
  }, []);

  const updateScript = useCallback((data: Partial<ScriptData>) => {
    dispatch({ type: 'UPDATE_SCRIPT', payload: data });
  }, []);

  const updateCharacters = useCallback((characters: CharacterInfo[]) => {
    dispatch({ type: 'UPDATE_CHARACTERS', payload: characters });
  }, []);

  const updateScenes = useCallback((scenes: SceneInfo[]) => {
    dispatch({ type: 'UPDATE_SCENES', payload: scenes });
  }, []);

  const addReference = useCallback((asset: ReferenceAsset) => {
    dispatch({ type: 'ADD_REFERENCE', payload: asset });
  }, []);

  const removeReference = useCallback((id: string) => {
    dispatch({ type: 'REMOVE_REFERENCE', payload: id });
  }, []);

  const updateReference = useCallback((id: string, data: Partial<ReferenceAsset>) => {
    dispatch({ type: 'UPDATE_REFERENCE', payload: { id, data } });
  }, []);

  const setAgentStatus = useCallback((agentName: string, status: Partial<AgentStatus>) => {
    dispatch({ type: 'SET_AGENT_STATUS', payload: { agentName, status } });
  }, []);

  const validate = useCallback(async (): Promise<boolean> => {
    try {
      const result = await wizardApi.validateProject({
        title: state.basicInfo.title,
        project_type: state.basicInfo.projectType,
        duration_minutes: state.basicInfo.durationMinutes,
        aspect_ratio: state.basicInfo.aspectRatio,
        frame_rate: state.basicInfo.frameRate,
        resolution: state.basicInfo.resolution,
        script_content: state.script.content,
        synopsis: state.script.synopsis
      });

      dispatch({
        type: 'SET_VALIDATION_ERRORS',
        payload: {
          errors: [...result.errors, ...result.warnings],
          completion: result.completion_percentage
        }
      });

      return result.is_valid;
    } catch (error) {
      console.error('验证失败:', error);
      return false;
    }
  }, [state.basicInfo, state.script]);

  const submit = useCallback(async (): Promise<string | null> => {
    try {
      const result = await wizardApi.createProject({
        title: state.basicInfo.title,
        project_type: state.basicInfo.projectType,
        duration_minutes: state.basicInfo.durationMinutes,
        aspect_ratio: state.basicInfo.aspectRatio,
        frame_rate: state.basicInfo.frameRate,
        resolution: state.basicInfo.resolution,
        script_content: state.script.content,
        synopsis: state.script.synopsis,
        logline: state.basicInfo.logline || state.script.logline
      });

      if (result.success && result.project_id) {
        dispatch({ type: 'SET_PROJECT_ID', payload: result.project_id });
        return result.project_id;
      }

      return null;
    } catch (error) {
      console.error('提交失败:', error);
      return null;
    }
  }, [state.basicInfo, state.script]);

  const reset = useCallback(() => {
    dispatch({ type: 'RESET' });
  }, []);

  const contextValue: WizardContextType = {
    state,
    setStep,
    updateBasicInfo,
    updateScript,
    updateCharacters,
    updateScenes,
    addReference,
    removeReference,
    updateReference,
    setAgentStatus,
    validate,
    submit,
    reset
  };

  return (
    <WizardContext.Provider value={contextValue}>
      {children}
    </WizardContext.Provider>
  );
};

// Hook
export const useWizard = (): WizardContextType => {
  const context = useContext(WizardContext);
  if (!context) {
    throw new Error('useWizard must be used within a WizardProvider');
  }
  return context;
};
