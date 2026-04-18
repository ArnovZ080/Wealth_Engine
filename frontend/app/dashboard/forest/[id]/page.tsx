'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Seed, Tree } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  ArrowLeft, 
  Sprout, 
  Zap, 
  AlertCircle,
  Crosshair
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function SeedDetailPage() {
  const params = useParams();
  const treeId = params.id as string;
  const [tree, setTree] = useState<Tree | null>(null);
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [loading, setLoading] = useState(true);

  type ForestStateRate = {
    usd_zar_rate?: number;
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [treeData, seedsData, stateData] = await Promise.all([
          api.get<Tree>(`/trees/${treeId}`),
          api.get<Seed[]>(`/trees/${treeId}/seeds`),
          api.get<ForestStateRate>('/state'),
        ]);
        setTree(treeData);
        setSeeds(seedsData);
        if (stateData?.usd_zar_rate) {
           (window as unknown as { usd_zar_rate?: number }).usd_zar_rate = stateData.usd_zar_rate;
        }
      } catch (err) {
        console.error('Failed to fetch seed details', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [treeId]);

  if (loading) return <div>Inspecting branches...</div>;

  return (
    <div className="space-y-8">
      <Link
        href="/dashboard/forest"
        className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft size={16} />
        Back to Forest
      </Link>

      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-1 rv">
          <div className="section-label">Tree Detail</div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">{tree?.name}</h1>
          <div className="flex items-center gap-4 text-sm text-text-secondary">
             <span>{tree?.seed_count} Active Seeds</span>
             <span>•</span>
             <span className="text-candle-green font-bold uppercase">Alpha-Bayesian Strategy</span>
          </div>
        </div>
        <div className="rv">
          <Button>Spawn New Seed</Button>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {seeds.map((seed) => (
          <div
            key={seed.id}
            className={cn(
              "rv overflow-hidden group",
              seed.current_value < 90 || seed.ground_zero_triggered ? "glass-red" : "glass"
            )}
          >
            <div className="gc p-0">
            <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
               <div className="flex items-center gap-2">
                 <div className={cn(
                   "w-6 h-6 rounded flex items-center justify-center",
                   seed.current_value < 90 || seed.ground_zero_triggered
                     ? "bg-candle-red/10 text-candle-red"
                     : "bg-candle-green/10 text-candle-green"
                 )}>
                    <Sprout size={14} />
                 </div>
                 <span className="font-mono text-xs font-bold uppercase tracking-widest">{seed.id.slice(0, 8)}</span>
               </div>
               {seed.strike_count > 0 && (
                 <div className="flex gap-1">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className={cn(
                        "w-2 h-2 rounded-full",
                        i < seed.strike_count ? "bg-candle-red shadow-[0_0_8px_rgba(239,68,68,0.5)]" : "bg-white/10"
                      )} />
                    ))}
                 </div>
               )}
            </div>

            <div className="p-6 space-y-4">
               <div>
                  <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">Current Exposure</p>
                  <div className="flex flex-col">
                    <p
                      className={cn(
                        "font-heading text-2xl font-bold",
                        seed.current_value < 900 || seed.ground_zero_triggered
                          ? "gradient-text-red"
                          : "gradient-text-green"
                      )}
                    >
                      {formatCurrency(seed.current_value, "ZAR")}
                    </p>
                    <p className="text-xs font-medium text-text-secondary">
                      ~
                      {formatCurrency(
                        seed.current_value / (Number((window as unknown as { usd_zar_rate?: number }).usd_zar_rate) || 18.5)
                      )}
                    </p>
                  </div>
               </div>

               <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-text-muted uppercase font-semibold tracking-widest">Floor (GZ)</span>
                    <span className="font-bold tracking-tight">
                      R850{" "}
                      <span className="text-text-muted font-semibold">
                        / ~
                        {formatCurrency(850 / (Number((window as unknown as { usd_zar_rate?: number }).usd_zar_rate) || 18.5))}
                      </span>
                    </span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                     <div 
                      className={cn(
                        "h-full transition-all duration-500",
                        seed.current_value < 900 ? "bg-candle-red" : "bg-candle-green"
                      )} 
                      style={{ width: `${Math.max(0, Math.min(100, ((seed.current_value - 850) / 150) * 100))}%` }} 
                     />
                  </div>
               </div>

               <div className="pt-4 flex items-center justify-between">
                 <div className="flex items-center gap-2 text-xs text-text-secondary">
                    <Crosshair size={14} />
                    <span>Kelly Size: 2.5%</span>
                  </div>
                  {seed.ground_zero_triggered ? (
                     <span className="flex items-center gap-1 text-[10px] text-candle-red font-black uppercase">
                        <AlertCircle size={10} /> Ground Zero
                     </span>
                  ) : (
                     <span className="flex items-center gap-1 text-[10px] text-candle-green font-black uppercase">
                        <Zap size={10} /> Active
                     </span>
                  )}
               </div>
            </div>

            <div className="px-6 py-3 bg-white/3 border-t border-white/10 flex justify-end">
               <button className="text-xs font-bold hover:underline text-text-secondary hover:text-text-primary">
                  Trade DNA →
               </button>
            </div>
            </div>
          </div>
        ))}
        
        {seeds.length === 0 && (
          <div className="col-span-full glass rv">
            <div className="gc py-24 text-center space-y-4">
             <div className="w-16 h-16 bg-white/5 border border-white/10 rounded-full mx-auto flex items-center justify-center text-text-muted">
                <Sprout size={32} />
             </div>
             <p className="text-text-secondary italic">No active seeds spawned in this tree.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
