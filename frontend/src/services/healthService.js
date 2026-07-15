import api from './api';
import { API_ENDPOINTS } from '../constants';

export const healthService = {
  checkHealth: async () => {
    const response = await api.get(API_ENDPOINTS.HEALTH);
    return response.data;
  },
};
