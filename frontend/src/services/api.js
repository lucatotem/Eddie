import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API functions - now working with file-based configs
export const onboardingAPI = {
  // Config management
  listConfigs: async () => {
    const response = await api.get('/api/onboarding/configs');
    return response.data;
  },

  getConfig: async (configId) => {
    const response = await api.get(`/api/onboarding/configs/${configId}`);
    return response.data;
  },

  createConfig: async (configData) => {
    const response = await api.post('/api/onboarding/configs', configData);
    return response.data;
  },

  updateConfig: async (configId, configData) => {
    const response = await api.put(`/api/onboarding/configs/${configId}`, configData);
    return response.data;
  },

  deleteConfig: async (configId) => {
    const response = await api.delete(`/api/onboarding/configs/${configId}`);
    return response.data;
  },

  // Course data (using file-based configs)
  getCourse: async (configId) => {
    const response = await api.get(`/api/onboarding/course/${configId}`);
    return response.data;
  },

  // Get summary of the course
  getCourseSummary: async (configId) => {
    const response = await api.get(`/api/onboarding/summary/${configId}`);
    return response.data;
  },

  // Generate quiz for the entire course
  generateCourseQuiz: async (configId, questionCount = 5) => {
    const response = await api.get(`/api/onboarding/quiz/${configId}`, {
      params: { question_count: questionCount }
    });
    return response.data;
  },
};

export const confluenceAPI = {
  // Get single page
  getPage: async (pageId) => {
    const response = await api.get(`/api/confluence/page/${pageId}`);
    return response.data;
  },

  // Search pages by label
  searchPages: async (label, limit = 50) => {
    const response = await api.get(`/api/confluence/search`, {
      params: { label, limit }
    });
    return response.data;
  },
};

export default api;
