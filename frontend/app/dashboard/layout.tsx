'use client';

import React, { useEffect } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/dashboard/Sidebar';
import { EmberField } from '@/components/ui/EmberField';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse flex flex-col items-center">
          <div className="text-4xl">🌳</div>
          <div className="mt-4 text-muted-foreground font-medium">Initialising Forest...</div>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="relative flex min-h-screen bg-void text-text-primary">
      <EmberField count={60} />
      <div className="orb orb-green w-[460px] h-[460px] top-[-140px] right-[-160px]" />
      <div
        className="orb orb-red w-[360px] h-[360px] bottom-[-140px] left-[-160px]"
        style={{ animationDelay: "-8s" }}
      />

      <div className="relative z-10 flex w-full">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-4 md:p-10">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
