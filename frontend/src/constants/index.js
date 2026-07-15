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
