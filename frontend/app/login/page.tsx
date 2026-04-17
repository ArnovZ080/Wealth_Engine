'use client';

import React, { useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { api } from '@/lib/api';
import { EmberField } from '@/components/ui/EmberField';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Authentication failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center px-4 py-16">
      <EmberField count={90} />
      <div className="orb orb-green w-[520px] h-[520px] top-[-180px] right-[-180px]" />
      <div
        className="orb orb-red w-[420px] h-[420px] bottom-[-200px] left-[-200px]"
        style={{ animationDelay: "-8s" }}
      />

      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="section-label justify-center">
            <span className="bdot" />
            Live
          </div>
          <h1 className="font-heading text-5xl font-bold tracking-tight leading-tight">
            <span className="gradient-text-green">Wealth Engine</span>
          </h1>
          <p className="mt-3 text-text-secondary leading-relaxed">
            {isRegister
              ? "Enter invite code to join the forest."
              : "Access your autonomous trading forest."}
          </p>
        </div>

        <div className="glass">
          <div className="gc p-8 space-y-6">
            {error && (
              <div className="glass-red">
                <div className="gc p-4 text-sm text-text-primary">{error}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
              {isRegister && (
                <div className="space-y-2">
                  <label className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                    Display Name
                  </label>
                  <Input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="e.g. Arno VZ"
                  />
                </div>
              )}

              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                  Email Address
                </label>
                <Input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@domain.com"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                  Password
                </label>
                <Input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>

              {isRegister && (
                <div className="space-y-2">
                  <label className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                    Invite Code
                  </label>
                  <Input
                    type="text"
                    required
                    value={inviteCode}
                    onChange={(e) => setInviteCode(e.target.value)}
                    placeholder="FOREST-XXXXX"
                  />
                </div>
              )}

              <Button type="submit" disabled={loading} className="w-full">
                {loading ? "Processing..." : isRegister ? "Register" : "Sign In"}
              </Button>
            </form>

            <div className="text-center text-sm">
              <button
                onClick={() => setIsRegister(!isRegister)}
                className="text-text-secondary hover:text-text-primary transition-colors"
              >
                {isRegister
                  ? "Already have an account? Sign in"
                  : "Don't have an account? Use invite code"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
