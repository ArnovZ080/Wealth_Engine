'use client';

import React, { useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { api } from '@/lib/api';

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (isRegister) {
        // Register flow
        await api.post('/auth/register', {
          email,
          password,
          display_name: displayName,
          invite_code: inviteCode,
        });
        // Auto login after register
        const data = await api.post<{ access_token: string }>('/auth/login', {
          email, // Backend uses 'email' in the JSON body
          password,
        });
        await login(data.access_token);
      } else {
        // Login flow
        // The backend expects OAuth2 Password flow (form-data or json depending on implementation)
        // Usually it's URL encoded, but our apiFetch handles JSON.
        // Let's check the backend auth/routes.py if possible, but standard is username/password.
        const data = await api.post<{ access_token: string }>('/auth/login', {
          email,
          password,
        });
        await login(data.access_token);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-height-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-md space-y-8 p-8 border border-border bg-card rounded-xl shadow-2xl">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">🌳 Wealth Engine</h1>
          <p className="mt-2 text-muted-foreground">
            {isRegister ? 'Enter invite code to join the forest' : 'Access your recursive wealth engine'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
              {error}
            </div>
          )}

          <div className="space-y-4">
            {isRegister && (
              <div>
                <label className="text-sm font-medium">Display Name</label>
                <input
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="mt-1 w-full p-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring outline-none"
                />
              </div>
            )}

            <div>
              <label className="text-sm font-medium">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full p-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring outline-none"
              />
            </div>

            <div>
              <label className="text-sm font-medium">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full p-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring outline-none"
              />
            </div>

            {isRegister && (
              <div>
                <label className="text-sm font-medium">Invite Code</label>
                <input
                  type="text"
                  required
                  value={inviteCode}
                  onChange={(e) => setInviteCode(e.target.value)}
                  className="mt-1 w-full p-2 bg-background border border-border rounded-md focus:ring-2 focus:ring-ring outline-none"
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full p-3 bg-primary text-primary-foreground font-semibold rounded-md hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isRegister ? 'Register' : 'Sign In')}
          </button>
        </form>

        <div className="text-center text-sm">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Use invite code"}
          </button>
        </div>
      </div>
    </div>
  );
}
