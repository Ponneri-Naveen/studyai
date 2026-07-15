import axios from 'axios';
import { STORAGE_KEYS } from '../constants';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Simple client-side GET cache storage
const getCache = new Map();
const CACHE_TTL = 15000; // 15 seconds cache lifetime

// Request interceptor to attach Bearer token and serve from cache if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Check cache for GET requests unless X-Bypass-Cache is requested
    if (config.method === 'get') {
      const bypass = config.headers['X-Bypass-Cache'] === 'true';
      const cacheKey = config.url + (config.params ? JSON.stringify(config.params) : '');
      
      if (bypass) {
        getCache.delete(cacheKey);
      } else {
        const cachedEntry = getCache.get(cacheKey);
        if (cachedEntry && (Date.now() - cachedEntry.timestamp < CACHE_TTL)) {
          // Serve from memory cache immediately using adapter injection
          config.adapter = () => {
            return Promise.resolve({
              data: cachedEntry.data,
              status: 200,
              statusText: 'OK',
              headers: {},
              config,
            });
          };
        }
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for unified error parsing and saving response cache snapshots
api.interceptors.response.use(
  (response) => {
    const { config } = response;
    
    // Save GET response data into cache if successful and not bypassed
    if (config.method === 'get' && config.headers['X-Bypass-Cache'] !== 'true') {
      const cacheKey = config.url + (config.params ? JSON.stringify(config.params) : '');
      getCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      });
    }
    
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(STORAGE_KEYS.AUTH_USER);
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
    }
    return Promise.reject(error);
  }
);

export default api;
