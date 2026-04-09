'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { api } from '@/lib/api';
import { UserForestState, FundingTransaction } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  Sprout, 
  Activity,
  AlertTriangle,
  Play
} from 'lucide-react';

export default function DashboardHome() {
  const { user } = useAuth();
  const [forest, setForest] = useState<UserForestState | null>(null);
  const [schedulerStatus, setSchedulerStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [forestData, schedulerData] = await Promise.all([
          api.get<UserForestState>('/api/v1/forest/state'),
          api.get<any>('/api/v1/scheduler/status')
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
    <div className="space-y-8">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Good morning, {user?.display_name.split(' ')[0]}</h1>
          <p className="text-muted-foreground">Your recursive forest is hydrated and active.</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:opacity-90">
            <Play size={16} />
            Run Cycle Now
          </button>
        </div>
      </header>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground font-medium">Total Portfolio</p>
            <Wallet className="text-primary" size={20} />
          </div>
          <p className="text-2xl font-bold">{formatCurrency(totalPortfolio)}</p>
          <div className="text-xs flex items-center gap-1 text-emerald-500 font-medium">
            <TrendingUp size={12} />
            +4.2% (7d)
          </div>
        </div>

        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground font-medium">Available Reservior</p>
            <Activity className="text-primary" size={20} />
          </div>
          <p className="text-2xl font-bold">{formatCurrency(forest?.shared_reservoir_balance || 0)}</p>
          <p className="text-xs text-muted-foreground font-medium">Next Seed: Ready</p>
        </div>

        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground font-medium">Active Seeds</p>
            <Sprout className="text-primary" size={20} />
          </div>
          <p className="text-2xl font-bold">12 / 100</p>
          <p className="text-xs text-muted-foreground font-medium">Capacity: 12% utilized</p>
        </div>

        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground font-medium">Engine Status</p>
            <Zap className={cn("text-primary", schedulerStatus?.running ? "text-emerald-500" : "text-amber-500")} size={20} />
          </div>
          <p className="text-large font-bold">{schedulerStatus?.running ? "Operational" : "Standby"}</p>
          <p className="text-xs text-muted-foreground font-medium truncate">
            Last Cycle: {schedulerStatus?.last_run?.trading_cycle ? new Date(schedulerStatus.last_run.trading_cycle).toLocaleTimeString() : 'Never'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Balance Breakdown Chart would go here */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl p-6 min-h-[400px]">
          <h2 className="text-xl font-bold mb-6">Tiered Distribution</h2>
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
                   <span className="text-muted-foreground">{formatCurrency(tier.value)}</span>
                 </div>
                 <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
                   <div 
                    className={cn("h-full", tier.color)} 
                    style={{ width: `${totalPortfolio > 0 ? (tier.value / totalPortfolio * 100) : 0}%` }}
                   />
                 </div>
               </div>
             ))}
          </div>
        </div>

        {/* Quick Help / Alerts */}
        <div className="space-y-6">
          <div className="p-6 bg-amber-500/5 border border-amber-500/20 rounded-xl space-y-4">
            <div className="flex items-center gap-2 text-amber-500 font-bold">
              <AlertTriangle size={20} />
              <span>Ground Zero Alert</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              2 seeds are approaching Ground Zero ($85.00 floor). Autonomous liquidation is on standby.
            </p>
            <button className="text-sm font-bold text-amber-500 hover:underline">
              Review Seeds →
            </button>
          </div>

          <div className="p-6 bg-card border border-border rounded-xl space-y-4">
            <h3 className="font-bold">Next Milestone</h3>
            <div className="flex items-center gap-4">
              <div className="flex-1 space-y-1">
                <p className="text-sm text-muted-foreground">Level 2 Unlock</p>
                <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
                   <div className="h-full bg-primary" style={{ width: '65%' }} />
                </div>
              </div>
              <span className="font-bold">65%</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Profit needed for Tier 2 Auto-allocation: $1,420
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
