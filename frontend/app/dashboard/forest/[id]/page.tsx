'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { Seed, Tree, TradeDecision } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  ArrowLeft, 
  Sprout, 
  History, 
  Zap, 
  AlertCircle,
  Crosshair
} from 'lucide-react';
import Link from 'next/link';

export default function SeedDetailPage() {
  const params = useParams();
  const treeId = params.id as string;
  const [tree, setTree] = useState<Tree | null>(null);
  const [seeds, setSeeds] = useState<Seed[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [treeData, seedsData, stateData] = await Promise.all([
          api.get<Tree>(`/trees/${treeId}`),
          api.get<Seed[]>(`/trees/${treeId}/seeds`),
          api.get<any>('/state')
        ]);
        setTree(treeData);
        setSeeds(seedsData);
        if (stateData?.usd_zar_rate) {
           (window as any).usd_zar_rate = stateData.usd_zar_rate;
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
      <Link href="/dashboard/forest" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft size={16} />
        Back to Forest
      </Link>

      <header className="flex justify-between items-start">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold">{tree?.name}</h1>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
             <span>{tree?.seed_count} Active Seeds</span>
             <span>•</span>
             <span className="text-emerald-500 font-bold uppercase">Alpha-Bayesian Strategy</span>
          </div>
        </div>
        <button className="px-4 py-2 bg-primary text-primary-foreground rounded-md font-bold text-sm">
           Spawn New Seed
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {seeds.map((seed) => (
          <div key={seed.id} className={cn(
            "bg-card border rounded-xl overflow-hidden group",
            seed.ground_zero_triggered ? "border-destructive/50" : "border-border"
          )}>
            <div className="p-4 border-b border-border bg-muted/30 flex justify-between items-center">
               <div className="flex items-center gap-2">
                 <div className="w-6 h-6 rounded bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                    <Sprout size={14} />
                 </div>
                 <span className="font-mono text-xs font-bold uppercase tracking-widest">{seed.id.slice(0, 8)}</span>
               </div>
               {seed.strike_count > 0 && (
                 <div className="flex gap-1">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className={cn(
                        "w-2 h-2 rounded-full",
                        i < seed.strike_count ? "bg-destructive shadow-[0_0_8px_rgba(239,68,68,0.5)]" : "bg-muted"
                      )} />
                    ))}
                 </div>
               )}
            </div>

            <div className="p-6 space-y-4">
               <div>
                  <p className="text-xs text-muted-foreground font-bold uppercase">Current Exposure</p>
                  <div className="flex flex-col">
                     <p className="text-2xl font-black font-mono text-foreground">{formatCurrency(seed.current_value, 'ZAR')}</p>
                     <p className="text-xs font-medium text-muted-foreground">
                        ~{formatCurrency(seed.current_value / ((window as any).usd_zar_rate || 18.50))}
                     </p>
                  </div>
               </div>

               <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground uppercase font-bold">Floor (GZ)</span>
                    <span className="font-bold tracking-tight">R850 / <span className="text-muted-foreground font-normal">~{formatCurrency(850 / ((window as any).usd_zar_rate || 18.50))}</span></span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
                     <div 
                      className={cn(
                        "h-full transition-all duration-500",
                        seed.current_value < 900 ? "bg-destructive" : "bg-emerald-500"
                      )} 
                      style={{ width: `${Math.max(0, Math.min(100, ((seed.current_value - 850) / 150) * 100))}%` }} 
                     />
                  </div>
               </div>

               <div className="pt-4 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Crosshair size={14} />
                    <span>Kelly Size: 2.5%</span>
                  </div>
                  {seed.ground_zero_triggered ? (
                     <span className="flex items-center gap-1 text-[10px] text-destructive font-black uppercase">
                        <AlertCircle size={10} /> Ground Zero
                     </span>
                  ) : (
                     <span className="flex items-center gap-1 text-[10px] text-emerald-500 font-black uppercase">
                        <Zap size={10} /> Active
                     </span>
                  )}
               </div>
            </div>

            <div className="px-6 py-3 bg-muted/10 border-t border-border flex justify-end">
               <button className="text-xs font-bold hover:underline text-muted-foreground hover:text-foreground">
                  Trade DNA →
               </button>
            </div>
          </div>
        ))}
        
        {seeds.length === 0 && (
          <div className="col-span-full py-24 text-center space-y-4">
             <div className="w-16 h-16 bg-secondary rounded-full mx-auto flex items-center justify-center text-muted-foreground">
                <Sprout size={32} />
             </div>
             <p className="text-muted-foreground italic">No active seeds spawned in this tree.</p>
          </div>
        )}
      </div>
    </div>
  );
}
