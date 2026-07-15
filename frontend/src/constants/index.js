/**
 * StudyAI Frontend — Global Constants
 */

export const ROUTES = {
  DASHBOARD: '/',
  UPLOAD: '/upload',
  SUMMARY: '/summary',
  FLASHCARDS: '/flashcards',
  QUIZ: '/quiz',
  SCHEDULE: '/schedule',
  ANALYTICS: '/analytics',
  LOGIN: '/login',
  REGISTER: '/register',
  PROFILE: '/profile',
};

export const API_ENDPOINTS = {
  HEALTH: '/health',
  AUTH: {
    REGISTER: '/auth/register',
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
  },
  MATERIALS: {
    BASE: '/v1/materials',
    UPLOAD: '/v1/materials/upload',
    TEXT: '/v1/materials/text',
  },
  AI: {
    HEALTH: '/v1/ai/health',
    TEST: '/v1/ai/test',
  },
  SUMMARY: {
    GENERATE: '/v1/summary/generate',
    BASE: '/v1/summary',
  },
  FLASHCARDS: {
    GENERATE: '/v1/flashcards/generate',
    BASE: '/v1/flashcards',
  },
  QUIZZES: {
    GENERATE: '/v1/quizzes/generate',
    BASE: '/v1/quizzes',
  },
  ANALYSIS: {
    GENERATE: '/v1/analysis/generate',
    BASE: '/v1/analysis',
  },
  PLANS: {
    GENERATE: '/v1/plans/generate',
    BASE: '/v1/plans',
  },
};

export const STORAGE_KEYS = {
  AUTH_USER: 'studyai_user',
  AUTH_TOKEN: 'studyai_token',
};

export const MESSAGES = {
  ERR_NETWORK: 'Failed to connect to the server. Please check your connection or verify if the backend is running.',
  ERR_GENERIC: 'Something went wrong. Please try again.',
  ERR_AUTH_REQUIRED: 'Please login to access this page.',
};
