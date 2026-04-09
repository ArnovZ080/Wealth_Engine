'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { TradeDecision } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  Filter, 
  Download,
  ChevronLeft,
  ChevronRight,
  Search
} from 'lucide-react';

export default function TradesPage() {
  const [trades, setTrades] = useState<TradeDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<'all' | 'open' | 'closed'>('all');

  useEffect(() => {
    async function fetchTrades() {
      try {
        const data = await api.get<TradeDecision[]>('/api/v1/trades/history');
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
          <h1 className="text-3xl font-bold">Decision DNA</h1>
          <p className="text-muted-foreground">Historical trail of autonomous agent operations.</p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-3 py-2 bg-secondary border border-border rounded-md text-sm font-medium">
             <Download size={16} />
             Export CSV
          </button>
        </div>
      </header>

      {/* Filters Bar */}
      <div className="flex flex-col md:flex-row gap-4 justify-between bg-card border border-border p-4 rounded-xl">
        <div className="flex bg-secondary p-1 rounded-lg">
           {(['all', 'open', 'closed'] as const).map((s) => (
             <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={cn(
                "px-4 py-1.5 rounded-md text-sm font-medium capitalize transition-all",
                filterStatus === s ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground"
              )}
             >
               {s}
             </button>
           ))}
        </div>
        
        <div className="relative flex-1 max-w-sm">
           <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
           <input 
            type="text" 
            placeholder="Search ticker (e.g. BTC/USDT)..." 
            className="w-full pl-10 pr-4 py-2 bg-secondary border border-border rounded-lg outline-none focus:ring-1 focus:ring-primary text-sm"
           />
        </div>
      </div>

      {/* Trades Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Symbol</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Type</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Entry Price</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Exit Price</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">P&L</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-muted-foreground">Agent Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredTrades.map((trade) => (
                <tr key={trade.id} className="hover:bg-muted/10 transition-colors">
                  <td className="px-6 py-4 font-bold">{trade.ticker}</td>
                  <td className="px-6 py-4">
                    <span className={cn(
                      "inline-flex items-center gap-1 font-medium",
                      trade.direction === 'long' ? "text-emerald-500" : "text-amber-500"
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
                        trade.realized_pnl >= 0 ? "text-emerald-500" : "text-destructive"
                      )}>
                        {trade.realized_pnl >= 0 ? '+' : ''}{formatCurrency(trade.realized_pnl)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground text-sm italic">Floating...</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                     <span className={cn(
                        "px-2 py-1 rounded text-[10px] font-bold uppercase",
                        trade.status === 'open' ? "bg-emerald-500/10 text-emerald-500" : "bg-muted text-muted-foreground"
                     )}>
                       {trade.status}
                     </span>
                  </td>
                  <td className="px-6 py-4 text-xs text-muted-foreground max-w-xs truncate">
                    Confidence: {(trade.confidence * 100).toFixed(0)}% — {trade.exit_reason || "Position active"}
                  </td>
                </tr>
              ))}
              {filteredTrades.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-muted-foreground italic">
                     No decision records found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex justify-between items-center text-sm">
        <p className="text-muted-foreground">Showing {filteredTrades.length} decisions</p>
        <div className="flex gap-2">
           <button className="p-2 border border-border rounded-md hover:bg-secondary disabled:opacity-30" disabled>
              <ChevronLeft size={16} />
           </button>
           <button className="p-2 border border-border rounded-md hover:bg-secondary disabled:opacity-30" disabled>
              <ChevronRight size={16} />
           </button>
        </div>
      </div>
    </div>
  );
}
