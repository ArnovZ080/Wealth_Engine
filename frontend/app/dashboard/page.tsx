'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { api } from '@/lib/api';
import { UserForestState } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  TrendingUp, 
  Wallet, 
  Sprout, 
  Activity,
  AlertTriangle,
  Play,
  Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

type SchedulerStatus = {
  running?: boolean;
  last_run?: {
    trading_cycle?: string;
  };
};

type ForestPortfolio = {
  total_value_zar?: number;
  total_value_usd?: number;
};

type ForestStateWithPortfolio = UserForestState & {
  usd_zar_rate?: number;
  portfolio?: ForestPortfolio;
  trees?: { id: string; status: string; active_seeds_count: number; seed_count: number }[];
};

export default function DashboardHome() {
  const { user } = useAuth();
  const [forest, setForest] = useState<ForestStateWithPortfolio | null>(null);
  const groundZeroSeeds = (forest?.trees || []).reduce((acc: number, tree: { active_seeds_count: number; seed_count: number }) => acc + (tree.active_seeds_count || tree.seed_count || 0), 0) > 0
    ? (forest?.trees || []).filter((t: { status: string }) => t.status === 'ground_zero').length
    : 0;
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [forestData, schedulerData] = await Promise.all([
          api.get<ForestStateWithPortfolio>('/state'),
          api.get<SchedulerStatus>('/scheduler/status'),
        ]);
        setForest(forestData);
        setSchedulerStatus(schedulerData);
      } catch (err) {
        console.error('Failed to fetch dashboard data', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const totalPortfolio = forest ? (
    forest.shared_reservoir_balance + 
    forest.shared_nursery_balance + 
    forest.vault_tier1_buidl + 
    forest.vault_tier2_etfs + 
    forest.vault_tier3_realestate
  ) : 0;

  if (loading) return <div>Loading Summary...</div>;

  return (
    <div className="space-y-10">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="rv">
          <div className="section-label">Your Forest</div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">
            Good morning,{" "}
            <span className="gradient-text-green">
              {user?.display_name.split(" ")[0]}
            </span>
          </h1>
          <p className="mt-3 text-text-secondary max-w-2xl">
            Your autonomous trading engine has been running since last login.
          </p>
          {forest?.usd_zar_rate && (
            <div className="mt-4 inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs font-semibold text-text-secondary">
              <span className="bdot" />
              USD/ZAR: {Number(forest.usd_zar_rate).toFixed(2)}
            </div>
          )}
        </div>
        <div className="rv">
          <Button className="gap-2">
            <Play size={16} />
            Run Cycle Now
          </Button>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="glass rv">
          <div className="gc p-6 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                Total Portfolio
              </p>
              <Wallet className="text-text-muted" size={18} />
            </div>
            <div className="flex flex-col gap-0.5">
              <p className="font-heading text-2xl font-bold gradient-text-green">
                {formatCurrency(forest?.portfolio?.total_value_zar ?? totalPortfolio, "ZAR")}
              </p>
              <p className="text-xs font-semibold text-text-secondary">
                {formatCurrency(forest?.portfolio?.total_value_usd ?? totalPortfolio)}
              </p>
            </div>
            <div className="text-xs flex items-center gap-1 text-candle-green font-semibold">
              <TrendingUp size={12} />
              +4.2% (7d)
            </div>
          </div>
        </div>

        <div className="glass rv">
          <div className="gc p-6 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                Available Reservoir
              </p>
              <Activity className="text-text-muted" size={18} />
            </div>
            <p className="font-heading text-2xl font-bold">
              {formatCurrency(forest?.shared_reservoir_balance || 0)}
            </p>
            <p className="text-xs text-text-secondary font-semibold">
              Next Seed: Ready
            </p>
          </div>
        </div>

        <div className="glass rv">
          <div className="gc p-6 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                Active Seeds
              </p>
              <Sprout className="text-text-muted" size={18} />
            </div>
            <p className="font-heading text-2xl font-bold">12 / 100</p>
            <p className="text-xs text-text-secondary font-semibold">
              Capacity: 12% utilized
            </p>
          </div>
        </div>

        <div className={cn("glass rv", schedulerStatus?.running ? "" : "glass-red")}>
          <div className="gc p-6 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">
                Engine Status
              </p>
              <Zap
                className={cn(
                  "text-text-muted",
                  schedulerStatus?.running ? "text-candle-green" : "text-candle-red"
                )}
                size={18}
              />
            </div>
            <p className={cn(
              "font-heading text-2xl font-bold",
              schedulerStatus?.running ? "text-candle-green" : "text-candle-red"
            )}>
              {schedulerStatus?.running ? "Operational" : "Standby"}
            </p>
            <p className="text-xs text-text-secondary font-semibold truncate">
              Last Cycle:{" "}
              {schedulerStatus?.last_run?.trading_cycle
                ? new Date(
                    schedulerStatus.last_run.trading_cycle
                  ).toLocaleTimeString()
                : "Never"}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Balance Breakdown Chart would go here */}
        <div className="glass rv lg:col-span-2 min-h-[400px]">
          <div className="gc p-6">
          <div className="section-label">Allocation</div>
          <h2 className="font-heading text-3xl font-bold mb-8">
            Tiered <span className="text-candle-green">Distribution</span>
          </h2>
          <div className="space-y-6 mt-12">
             {[
               { label: 'Reservoir (BUIDL)', value: forest?.shared_reservoir_balance || 0, color: 'bg-emerald-500' },
               { label: 'Nursery (USDC)', value: forest?.shared_nursery_balance || 0, color: 'bg-blue-500' },
               { label: 'Vault T1 (BUIDL)', value: forest?.vault_tier1_buidl || 0, color: 'bg-primary' },
               { label: 'Vault T2 (ETFs)', value: forest?.vault_tier2_etfs || 0, color: 'bg-amber-500' },
               { label: 'Vault T3 (RE)', value: forest?.vault_tier3_realestate || 0, color: 'bg-indigo-500' },
             ].map((tier) => (
               <div key={tier.label} className="space-y-2">
                 <div className="flex justify-between text-sm">
                   <span className="font-medium">{tier.label}</span>
                   <span className="text-text-secondary">{formatCurrency(tier.value)}</span>
                 </div>
                 <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                   <div 
                    className={cn("h-full", tier.color)} 
                    style={{ width: `${totalPortfolio > 0 ? (tier.value / totalPortfolio * 100) : 0}%` }}
                   />
                 </div>
               </div>
             ))}
          </div>
          </div>
        </div>

        {/* Quick Help / Alerts */}
        <div className="space-y-6">
          {groundZeroSeeds > 0 && (
          <div className="glass-red rv">
            <div className="gc p-6 space-y-4">
            <div className="flex items-center gap-2 text-candle-red font-bold">
              <AlertTriangle size={20} />
              <span>Ground Zero Alert</span>
            </div>
            <p className="text-sm text-text-secondary leading-relaxed">
              {groundZeroSeeds} seed{groundZeroSeeds > 1 ? 's are' : ' is'} approaching Ground Zero (R850 floor). Autonomous liquidation is on standby.
            </p>
            <Link href="/dashboard/forest" className="text-sm font-bold text-candle-red hover:underline">
              Review Seeds →
            </Link>
            </div>
          </div>
          )}

          <div className="glass rv">
            <div className="gc p-6 space-y-4">
            <h3 className="font-heading text-xl font-semibold">Next Milestone</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1 space-y-1">
                <p className="text-sm text-text-secondary">Vault Tier 2 — ETF Allocation</p>
                <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
                   <div className="h-full bg-candle-green" style={{ width: `${Math.min(100, ((forest?.vault_tier2_etfs || 0) / 50000) * 100).toFixed(1)}%` }} />
                </div>
              </div>
              <span className="font-bold">{Math.min(100, ((forest?.vault_tier2_etfs || 0) / 50000) * 100).toFixed(1)}%</span>
            </div>
            <p className="text-xs text-text-secondary">
              Vault Tier 2 capacity: ${Number(forest?.vault_tier2_etfs || 0).toFixed(2)} / $50,000
            </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
