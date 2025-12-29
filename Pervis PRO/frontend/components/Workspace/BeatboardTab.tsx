import React from 'react';
import { Project, Beat, SceneGroup } from '../../types';
import { StepBeatBoard } from '../StepBeatBoard';

interface BeatboardTabProps {
  project: Project;
  onUpdateBeats: (beats: Beat[]) => void;
}

export const BeatboardTab: React.FC<BeatboardTabProps> = ({ project, onUpdateBeats }) => {
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

  const handleUpdateBeat = (updatedBeat: Beat) => {
    const newBeats = project.beats.map(b => b.id === updatedBeat.id ? updatedBeat : b);
    onUpdateBeats(newBeats);
  };

  return (
    <div className="h-full">
      <StepBeatBoard
        scenes={getScenes()}
        beats={project.beats}
        projectId={project.id}
        onUpdateBeat={handleUpdateBeat}
        onNext={() => {}} // Tab 模式下不需要 onNext
      />
    </div>
  );
};
