'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Tree } from '@/lib/types';
import { formatPercent, cn } from '@/lib/utils';
import { Sprout, BarChart3, ChevronRight, Play, Pause } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function ForestPage() {
  const [trees, setTrees] = useState<Tree[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTrees() {
      try {
        const data = await api.get<Tree[]>('/trees');
        console.log('ForestPage: Received raw trees data:', data);
        setTrees(data);
      } catch (err) {
        console.error('Failed to fetch trees', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTrees();
  }, []);

  if (loading) return <div>Fertilising soil...</div>;

  return (
    <div className="space-y-8">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="rv">
          <div className="section-label">Active Seeds</div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">
            Your <span className="text-candle-green">Trading Forest</span>
          </h1>
          <p className="mt-3 text-text-secondary">
            Managing {trees.length} active trees across multiple exchanges.
          </p>
        </div>
        <div className="rv">
          <Button variant="outline" className="gap-2">
            <Sprout size={18} />
            Plant New Tree
          </Button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {trees.map((tree) => (
          <div
            key={tree.id}
            className={cn(
              "rv group relative overflow-hidden",
              tree.is_active ? "glass" : "glass-red"
            )}
          >
            <div className="gc p-6">
              <div className={cn(
                "absolute top-0 right-0 w-16 h-16 opacity-5 pointer-events-none transition-transform group-hover:scale-110",
                tree.is_active ? "text-candle-green" : "text-candle-red"
              )}>
                <Sprout size={64} />
              </div>
              <div className="flex justify-between items-start mb-4">
                <div className="space-y-1">
                  <h3 className="font-heading font-semibold text-xl">{tree.name}</h3>
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider",
                    tree.is_active ? "bg-candle-green/10 text-candle-green" : "bg-candle-red/10 text-candle-red"
                  )}>
                    {tree.is_active ? 'Active' : 'Paused'}
                  </span>
                </div>
                <div className="flex gap-1">
                  <button className="p-2 hover:bg-white/5 rounded-md text-text-muted hover:text-text-primary">
                    {tree.is_active ? <Pause size={16} /> : <Play size={16} />}
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 py-4">
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">Seeds</p>
                  <p className="font-heading font-bold text-lg">{tree.seed_count} / 100</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">30D ROI</p>
                  <p className={cn(
                    "font-heading font-bold text-lg",
                    (tree.performance_30d || 0) >= 0 ? "text-candle-green" : "text-candle-red"
                  )}>
                    {formatPercent(tree.performance_30d || 0)}
                  </p>
                </div>
              </div>
              <div className="pt-4 border-t border-border flex justify-between items-center">
                <div className="flex items-center gap-2 text-text-secondary">
                  <BarChart3 size={14} />
                  <span className="text-xs font-medium">Aggressive-Beta Strategy</span>
                </div>
                <Link
                  href={`/dashboard/forest/${tree.id}`}
                  className="text-candle-green hover:underline text-sm font-bold flex items-center gap-1"
                >
                  Inspect Tree
                  <ChevronRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        ))}

        {trees.length === 0 && (
          <div className="col-span-full glass rv">
            <div className="gc p-12 flex flex-col items-center justify-center text-center space-y-4">
              <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-full flex items-center justify-center text-text-muted">
                <Sprout size={32} />
              </div>
              <div className="space-y-1">
                <h3 className="font-heading font-semibold text-xl">The soil is ready</h3>
                <p className="text-text-secondary max-w-sm">
                  No active trees yet. Your first tree will be planted when the nursery threshold is reached (ZAR 1,000).
                </p>
              </div>
              <Link href="/dashboard/funding">
                <Button>Get Started</Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
