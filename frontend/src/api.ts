import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = (data: URLSearchParams) => {
  return api.post('/auth/login', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
};

export const register = (data: any) => {
  return api.post('/auth/register', data);
};

export const getMe = () => {
  return api.get('/auth/me');
};

export const submitGovernanceRequest = (request_text: string) => {
  return api.post('/governance/request', { request_text });
};

export const getAuditLogs = () => {
  return api.get('/governance/audit');
};

export default api;
