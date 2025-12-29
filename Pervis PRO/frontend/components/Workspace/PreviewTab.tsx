import React from 'react';
import { Project, Beat, SceneGroup } from '../../types';
import { StepTimeline } from '../StepTimeline';

interface PreviewTabProps {
  project: Project;
  onUpdateBeats: (beats: Beat[]) => void;
}

export const PreviewTab: React.FC<PreviewTabProps> = ({ project, onUpdateBeats }) => {
  // 将 beats 分组为 scenes
  const getScenes = (): SceneGroup[] => {
    const scenes: SceneGroup[] = [];
    let currentScene: SceneGroup | null = null;
    let time = 0;
    
    project.beats.forEach((beat, idx) => {
      const slug = beat.tags?.scene_slug || "SCENE 1";
      if (!currentScene || currentScene.title !== slug) {
        if (currentScene) scenes.push(currentScene);
        currentScene = { id: `s-${idx}`, title: slug, beats: [], startTime: time, duration: 0 };
      }
      currentScene.beats.push(beat);
      currentScene.duration += beat.duration;
      time += beat.duration;
    });
    
    if (currentScene) scenes.push(currentScene);
    return scenes;
  };

  return (
    <div className="h-full">
      <StepTimeline
        project={project}
        scenes={getScenes()}
        onUpdateBeats={onUpdateBeats}
      />
    </div>
  );
};
