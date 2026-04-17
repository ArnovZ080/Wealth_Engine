'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { TradeDecision } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  Download,
  ChevronLeft,
  ChevronRight,
  Search
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

export default function TradesPage() {
  const [trades, setTrades] = useState<TradeDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<'all' | 'open' | 'closed'>('all');

  useEffect(() => {
    async function fetchTrades() {
      try {
        const data = await api.get<TradeDecision[]>('/trades/history');
        setTrades(data);
      } catch (err) {
        console.error('Failed to fetch trades', err);
      } finally {
        setLoading(false);
      }
    }
    fetchTrades();
  }, []);

  const filteredTrades = trades.filter(t => 
    filterStatus === 'all' ? true : t.status === filterStatus
  );

  if (loading) return <div>Reading the decision DNA...</div>;

  return (
    <div className="space-y-8">
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="section-label">Trade Log</div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">Decision DNA</h1>
          <p className="mt-3 text-text-secondary">Historical trail of autonomous agent operations.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="gap-2">
             <Download size={16} />
             Export CSV
          </Button>
        </div>
      </header>

      {/* Filters Bar */}
      <div className="glass rv">
        <div className="gc p-4 flex flex-col md:flex-row gap-4 justify-between">
        <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
           {(['all', 'open', 'closed'] as const).map((s) => (
             <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-semibold capitalize transition-all",
                filterStatus === s
                  ? "bg-candle-green/18 text-text-primary shadow-[0_0_22px_rgba(34,197,94,0.18)]"
                  : "text-text-secondary hover:text-text-primary"
              )}
             >
               {s}
             </button>
           ))}
        </div>
        
        <div className="relative flex-1 max-w-sm">
           <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
           <Input
             type="text"
             placeholder="Search ticker (e.g. BTC/USDT)..."
             className="pl-10"
           />
        </div>
        </div>
      </div>

      {/* Trades Table */}
      <div className="glass rv overflow-hidden">
        <div className="gc p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/10 bg-white/5">
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">Symbol</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">Type</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">Entry Price</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">Exit Price</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">P&L</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">Status</th>
                <th className="px-6 py-4 text-xs font-semibold uppercase tracking-widest text-text-muted">Agent Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {filteredTrades.map((trade) => (
                <tr key={trade.id} className="hover:bg-white/3 transition-colors">
                  <td className="px-6 py-4 font-bold">{trade.ticker}</td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "inline-flex items-center gap-1 font-medium",
                      trade.direction === 'long' ? "text-candle-green" : "text-candle-red"
                    )}>
                      {trade.direction === 'long' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                      {trade.direction.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-mono text-sm">{formatCurrency(trade.entry_price, '')}</td>
                  <td className="px-6 py-4 font-mono text-sm">{trade.exit_price ? formatCurrency(trade.exit_price, '') : '—'}</td>
                  <td className="px-6 py-4">
                    {trade.realized_pnl ? (
                      <span className={cn(
                        "font-bold font-mono",
                        trade.realized_pnl >= 0 ? "text-candle-green" : "text-candle-red"
                      )}>
                        {trade.realized_pnl >= 0 ? '+' : ''}{formatCurrency(trade.realized_pnl)}
                      </span>
                    ) : (
                      <span className="text-text-muted text-sm italic">Floating...</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                     <span className={cn(
                        "px-2 py-1 rounded text-[10px] font-bold uppercase",
                        trade.status === 'open'
                          ? "bg-candle-green/10 text-candle-green"
                          : "bg-white/5 text-text-muted border border-white/10"
                     )}>
                       {trade.status}
                     </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-text-secondary max-w-xs truncate">
                    Confidence: {(trade.confidence * 100).toFixed(0)}% — {trade.exit_reason || "Position active"}
                  </td>
                </tr>
              ))}
              {filteredTrades.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-text-secondary italic">
                     No decision records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        </div>
      </div>

      <div className="flex justify-between items-center text-sm">
        <p className="text-text-secondary">Showing {filteredTrades.length} decisions</p>
        <div className="flex gap-2">
           <button className="p-2 border border-white/10 rounded-xl hover:bg-white/5 disabled:opacity-30" disabled>
              <ChevronLeft size={16} />
           </button>
           <button className="p-2 border border-white/10 rounded-xl hover:bg-white/5 disabled:opacity-30" disabled>
              <ChevronRight size={16} />
           </button>
        </div>
      </div>
    </div>
  );
}
