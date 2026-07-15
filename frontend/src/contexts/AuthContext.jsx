import React, { createContext, useState, useEffect } from 'react';
import { authService } from '../services/authService';
import { STORAGE_KEYS } from '../constants';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already authenticated from previous session
    const storedUser = localStorage.getItem(STORAGE_KEYS.AUTH_USER);
    const storedToken = localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN);
    
    if (storedUser && storedToken) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse stored user session.', e);
        localStorage.removeItem(STORAGE_KEYS.AUTH_USER);
        localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const { user: loggedInUser, token } = await authService.login(email, password);
      localStorage.setItem(STORAGE_KEYS.AUTH_USER, JSON.stringify(loggedInUser));
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
      setUser(loggedInUser);
      return loggedInUser;
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      const { user: registeredUser, token } = await authService.register(name, email, password);
      localStorage.setItem(STORAGE_KEYS.AUTH_USER, JSON.stringify(registeredUser));
      localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token);
      setUser(registeredUser);
      return registeredUser;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
    } finally {
      localStorage.removeItem(STORAGE_KEYS.AUTH_USER);
      localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN);
      setUser(null);
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
