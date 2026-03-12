import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('king_klub_token'));
  const [loading, setLoading] = useState(true);

  // Set up axios defaults
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Fetch user on mount if token exists
  useEffect(() => {
    const fetchUser = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await axios.get(`${API}/auth/me`);
        setUser(response.data);
      } catch (error) {
        console.error('Failed to fetch user:', error);
        localStorage.removeItem('king_klub_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [token]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData } = response.data;
    
    localStorage.setItem('king_klub_token', newToken);
    setToken(newToken);
    setUser(userData);
    
    return userData;
  };

  const register = async (email, password, displayName, titlePreference = 'male') => {
    const response = await axios.post(`${API}/auth/register`, {
      email,
      password,
      display_name: displayName,
      title_preference: titlePreference
    });
    const { token: newToken, user: userData } = response.data;
    
    localStorage.setItem('king_klub_token', newToken);
    setToken(newToken);
    setUser(userData);
    
    return userData;
  };

  const updateTitlePreference = async (titlePreference) => {
    const response = await axios.put(`${API}/auth/title-preference`, {
      title_preference: titlePreference
    });
    setUser(prev => ({ ...prev, title_preference: titlePreference }));
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('king_klub_token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    refreshUser,
    updateTitlePreference,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
