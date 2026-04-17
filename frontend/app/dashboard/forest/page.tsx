'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { Tree } from '@/lib/types';
import { formatCurrency, formatPercent, cn } from '@/lib/utils';
import { Sprout, BarChart3, ChevronRight, Play, Pause } from 'lucide-react';
import Link from 'next/link';

export default function ForestPage() {
  const [trees, setTrees] = useState<Tree[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTrees() {
      try {
        const data = await api.get<Tree[]>('/trees');
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
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Your Forest</h1>
          <p className="text-muted-foreground">Managing {trees.length} active trees across multiple exchanges.</p>
        </div>
        <button className="px-4 py-2 bg-secondary border border-border rounded-md font-medium hover:bg-secondary/80 flex items-center gap-2">
           <Sprout size={18} />
           Plant New Tree
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {trees.map((tree) => (
          <div key={tree.id} className="bg-card border border-border rounded-xl p-6 hover:shadow-lg transition-all group relative overflow-hidden">
            <div className={cn(
               "absolute top-0 right-0 w-16 h-16 opacity-5 pointer-events-none transition-transform group-hover:scale-110",
               tree.is_active ? "text-emerald-500" : "text-amber-500"
            )}>
               <Sprout size={64} />
            </div>

            <div className="flex justify-between items-start mb-4">
              <div className="space-y-1">
                <h3 className="font-bold text-xl">{tree.name}</h3>
                <span className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wider",
                  tree.is_active ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"
                )}>
                  {tree.is_active ? 'Active' : 'Paused' }
                </span>
              </div>
              <div className="flex gap-1">
                 <button className="p-2 hover:bg-secondary rounded-md text-muted-foreground hover:text-foreground">
                    {tree.is_active ? <Pause size={16} /> : <Play size={16} />}
                 </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 py-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase font-bold tracking-tighter">Seeds</p>
                <p className="font-mono text-lg">{tree.seed_count} / 100</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase font-bold tracking-tighter">30D ROI</p>
                <p className={cn(
                  "font-mono text-lg",
                  (tree.performance_30d || 0) >= 0 ? "text-emerald-500" : "text-destructive"
                )}>
                  {formatPercent(tree.performance_30d || 0)}
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-border flex justify-between items-center">
               <div className="flex items-center gap-2 text-muted-foreground">
                  <BarChart3 size={14} />
                  <span className="text-xs font-medium">Aggressive-Beta Strategy</span>
               </div>
               <Link 
                href={`/dashboard/forest/${tree.id}`}
                className="text-primary hover:underline text-sm font-bold flex items-center gap-1"
               >
                 Inspect Tree
                 <ChevronRight size={14} />
               </Link>
            </div>
          </div>
        ))}

        {/* Placeholder for planting new trees */}
        {trees.length === 0 && (
          <div className="col-span-full border-2 border-dashed border-border rounded-xl p-12 flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-16 h-16 bg-secondary rounded-full flex items-center justify-center text-muted-foreground">
               <Sprout size={32} />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-xl">The soil is ready</h3>
              <p className="text-muted-foreground max-w-sm">
                You haven't planted any trees yet. Deposit ZAR to start allocating capital to autonomous trading strategies.
              </p>
            </div>
            <Link href="/dashboard/funding" className="px-6 py-2 bg-primary text-primary-foreground rounded-md font-bold">
               Get Started
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
