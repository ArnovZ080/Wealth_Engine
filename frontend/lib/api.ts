/**
 * API Client — Centralized fetch wrapper with auth and error handling.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  // Get token from localStorage (fallback for MVP)
  // In production, use httpOnly cookies via Next.js Server Actions/Middleware
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Clear token on auth failure
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API Error: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(endpoint: string, options?: RequestInit) => 
    apiFetch<T>(endpoint, { ...options, method: 'GET' }),
  
  post: <T>(endpoint: string, body?: any, options?: RequestInit) => 
    apiFetch<T>(endpoint, { 
      ...options, 
      method: 'POST', 
      body: body ? JSON.stringify(body) : undefined 
    }),
  
  put: <T>(endpoint: string, body?: any, options?: RequestInit) => 
    apiFetch<T>(endpoint, { 
      ...options, 
      method: 'PUT', 
      body: body ? JSON.stringify(body) : undefined 
    }),
  
  delete: <T>(endpoint: string, options?: RequestInit) => 
    apiFetch<T>(endpoint, { ...options, method: 'DELETE' }),
};
