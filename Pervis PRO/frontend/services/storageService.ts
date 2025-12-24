
import { Project } from '../types';

const STORAGE_KEY = 'previs_pro_projects_v1';

export const storageService = {
  // Load all projects
  getAllProjects: (): Project[] => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const projects = JSON.parse(raw);
      // Sort by last modified (using createdAt for now, ideally update time)
      return projects.sort((a: Project, b: Project) => b.createdAt - a.createdAt);
    } catch (e) {
      console.error("Failed to load projects", e);
      return [];
    }
  },

  // Save or Update a project
  saveProject: (project: Project): void => {
    try {
      const projects = storageService.getAllProjects();
      const index = projects.findIndex(p => p.id === project.id);
      
      if (index >= 0) {
        // Update existing
        projects[index] = project;
      } else {
        // Create new
        projects.push(project);
      }
      
      localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
    } catch (e) {
      console.error("Failed to save project", e);
    }
  },

  // Delete a project
  deleteProject: (id: string): void => {
    try {
      const projects = storageService.getAllProjects();
      const filtered = projects.filter(p => p.id !== id);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    } catch (e) {
      console.error("Failed to delete project", e);
    }
  },

  // Get single project
  getProject: (id: string): Project | null => {
    const projects = storageService.getAllProjects();
    return projects.find(p => p.id === id) || null;
  }
};
