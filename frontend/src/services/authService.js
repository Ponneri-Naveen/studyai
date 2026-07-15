import api from './api';
import { API_ENDPOINTS } from '../constants';

export const authService = {
  login: async (email, password) => {
    try {
      // Call mock or real Flask login endpoint
      const response = await api.post(API_ENDPOINTS.AUTH.LOGIN, { email, password });
      
      // Simulate/construct auth session data since backend is currently stubbed
      const user = {
        email,
        name: email.split('@')[0], // Use local part of email as username placeholder
        createdAt: new Date().toISOString(),
      };
      const token = response.data.token || 'stubbed-jwt-token-response';
      
      return { user, token };
    } catch (error) {
      console.warn('Backend auth request failed or offline. Simulating offline login...');
      // Fallback for visual mock testing:
      if (email && password) {
        return {
          user: { email, name: email.split('@')[0], createdAt: new Date().toISOString() },
          token: 'offline-mock-token',
        };
      }
      throw error;
    }
  },

  register: async (name, email, password) => {
    try {
      const response = await api.post(API_ENDPOINTS.AUTH.REGISTER, { name, email, password });
      const user = {
        email,
        name,
        createdAt: new Date().toISOString(),
      };
      const token = 'stubbed-jwt-token-response';
      return { user, token };
    } catch (error) {
      console.warn('Backend auth request failed or offline. Simulating offline registration...');
      if (name && email && password) {
        return {
          user: { name, email, createdAt: new Date().toISOString() },
          token: 'offline-mock-token',
        };
      }
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post(API_ENDPOINTS.AUTH.LOGOUT);
    } catch (error) {
      console.warn('Backend logout failed or offline. Proceeding to clear local session.');
    }
    // Clean up is handled by AuthContext
    return true;
  },
};
