'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { FundingTransaction } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  Building2, 
  Copy, 
  ArrowUpCircle, 
  ArrowDownCircle,
  Clock,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

type DepositInstructions = {
  bank_name?: string;
  branch_code?: string;
  account_number?: string;
  reference?: string;
};

type WithdrawalPreview = {
  breakdown: Array<{ source: string; amount_usdt: number }>;
  fulfillable_usdt: number;
};

export default function FundingPage() {
  const [instructions, setInstructions] = useState<DepositInstructions | null>(null);
  const [transactions, setTransactions] = useState<FundingTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [preview, setPreview] = useState<WithdrawalPreview | null>(null);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [instData, txData] = await Promise.all([
          api.get<DepositInstructions>('/funding/deposit-instructions'),
          api.get<FundingTransaction[]>('/funding/transactions'),
        ]);
        setInstructions(instData);
        setTransactions(txData);
      } catch (err) {
        console.error('Failed to fetch funding data', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handlePreview = async () => {
    if (!withdrawAmount || isNaN(Number(withdrawAmount))) return;
    try {
      const data = await api.post<WithdrawalPreview>('/funding/withdraw/preview', {
        zar_amount: Number(withdrawAmount),
      });
      setPreview(data);
    } catch {
      alert('Failed to calculate preview');
    }
  };

  const handleExecute = async () => {
    if (!withdrawAmount) return;
    setExecuting(true);
    try {
      await api.post('/funding/withdraw/execute', {
        zar_amount: Number(withdrawAmount)
      });
      alert('Withdrawal request submitted!');
      setWithdrawAmount('');
      setPreview(null);
      // Refresh history
      const txData = await api.get<FundingTransaction[]>('/funding/transactions');
      setTransactions(txData);
    } catch {
      alert('Execution failed');
    } finally {
      setExecuting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied: ' + text);
  };

  if (loading) return <div>Fueling the pipeline...</div>;

  return (
    <div className="space-y-8">
      <header>
        <div className="section-label">Funding</div>
        <h1 className="font-heading text-4xl font-bold tracking-tight">Funding & Liquidation</h1>
        <p className="mt-3 text-text-secondary">Manage your ZAR lifecycle and any-time cash-out hierarchical liquidation.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Deposit Side */}
        <div className="space-y-6">
          <div className="glass rv">
            <div className="gc p-6 space-y-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <ArrowUpCircle className="text-candle-green" size={24} />
              Deposit Funds
            </h2>
            
            <div className="bg-candle-green/5 border border-candle-green/20 p-4 rounded-xl space-y-4">
               <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-candle-green/10 rounded-full flex items-center justify-center text-candle-green flex-shrink-0">
                    <Building2 size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold">Capitec Business Bank Details</h3>
                    <p className="text-sm text-text-secondary">Transfer ZAR to your unique ref for automated allocation.</p>
                  </div>
               </div>

               <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                  <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                     <p className="text-xs text-text-muted font-semibold uppercase tracking-widest">Bank Name</p>
                     <p className="font-bold">{instructions?.bank_name}</p>
                  </div>
                  <div className="p-3 bg-white/5 border border-white/10 rounded-xl">
                     <p className="text-xs text-text-muted font-semibold uppercase tracking-widest">Branch Code</p>
                     <p className="font-bold">{instructions?.branch_code}</p>
                  </div>
                  <div className="p-3 bg-white/5 border border-white/10 rounded-xl col-span-2 relative group">
                     <p className="text-xs text-text-muted font-semibold uppercase tracking-widest">Account Number</p>
                     <p className="font-bold font-mono">{instructions?.account_number}</p>
                     <button 
                      onClick={() => {
                        if (instructions?.account_number) copyToClipboard(instructions.account_number);
                      }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-muted-foreground/10 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                     >
                        <Copy size={16} />
                     </button>
                  </div>
                  <div className="p-4 rounded-xl col-span-2 relative group shadow-lg bg-gradient-to-br from-candle-green to-candle-green-dark text-white border border-candle-green/30">
                     <p className="text-xs text-white/70 font-bold uppercase tracking-widest">MANDATORY REFERENCE</p>
                     <p className="text-xl font-black font-mono mt-1">{instructions?.reference}</p>
                     <button 
                      onClick={() => {
                        if (instructions?.reference) copyToClipboard(instructions.reference);
                      }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-2 hover:bg-black/10 rounded"
                     >
                        <Copy size={18} />
                     </button>
                  </div>
               </div>
            </div>

            <p className="text-xs text-text-secondary italic leading-relaxed">
              * Payments without the correct reference will be flagged for manual review and may take up to 5 business days to credit.
            </p>
            </div>
          </div>

          <div className="glass rv">
            <div className="gc p-6">
            <h2 className="font-heading text-3xl font-bold mb-6">Recent Transactions</h2>
            <div className="space-y-4 text-sm">
               {transactions.map(tx => (
                 <div key={tx.id} className="flex items-center justify-between p-3 border-b border-white/10 last:border-0 hover:bg-white/5 rounded-xl transition-colors">
                    <div className="flex items-center gap-3">
                       <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center",
                          tx.type === 'deposit' ? "bg-candle-green/10 text-candle-green" : "bg-candle-red/10 text-candle-red"
                       )}>
                          {tx.type === 'deposit' ? <ArrowUpCircle size={14} /> : <ArrowDownCircle size={14} />}
                       </div>
                       <div>
                          <p className="font-bold capitalize">{tx.type}</p>
                          <p className="text-[10px] text-text-muted">{new Date(tx.created_at).toLocaleDateString()}</p>
                       </div>
                    </div>
                    <div className="text-right">
                       <p className="font-bold">{formatCurrency(tx.zar_amount, 'ZAR')}</p>
                       <div className="flex items-center justify-end gap-1 text-[10px]">
                          {tx.status === 'completed' || tx.status === 'credited' ? (
                            <span className="flex items-center gap-0.5 text-candle-green">
                               <CheckCircle2 size={10} /> Completed
                            </span>
                          ) : (
                            <span className="flex items-center gap-0.5 text-text-secondary">
                               <Clock size={10} /> {tx.status}
                            </span>
                          )}
                       </div>
                    </div>
                 </div>
               ))}
               {transactions.length === 0 && (
                  <p className="text-center py-6 text-text-secondary italic">No transaction history found.</p>
               )}
            </div>
            </div>
          </div>
        </div>

        {/* Withdrawal Side */}
        <div className="space-y-6">
           <div className="glass-red rv">
             <div className="gc p-6 space-y-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <ArrowDownCircle className="text-candle-red" size={24} />
                Request Withdrawal
              </h2>

              <div className="space-y-4">
                 <div>
                    <label className="text-xs uppercase tracking-widest text-text-muted font-semibold mb-2 block">Amount (ZAR)</label>
                    <div className="relative">
                       <span className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted font-bold">R</span>
                       <Input
                         type="number"
                         value={withdrawAmount}
                         onChange={(e) => setWithdrawAmount(e.target.value)}
                         placeholder="0.00"
                         className="pl-8 font-heading font-bold text-lg"
                       />
                    </div>
                 </div>

                 <Button onClick={handlePreview} variant="outline" className="w-full">
                   Preview Hierarchical Liquidation
                 </Button>
              </div>

              {preview && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-300">
                   <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-widest text-text-muted">Liquidation Breakdown</h4>
                      {preview.breakdown.map((item, idx: number) => (
                        <div key={idx} className="flex justify-between items-center text-sm">
                           <div className="flex items-center gap-2">
                              {idx === 0 ? <CheckCircle2 size={14} className="text-candle-green" /> : <Clock size={14} className="text-text-muted" />}
                              <span className="font-medium">{item.source}</span>
                           </div>
                           <span className="font-mono font-bold">{formatCurrency(item.amount_usdt, 'USDT')}</span>
                        </div>
                      ))}

                      <div className="pt-3 border-t border-white/10 mt-3">
                         <div className="flex justify-between items-center">
                            <span className="font-bold">Total Fulfillable</span>
                            <span className="font-bold text-lg">{formatCurrency(preview.fulfillable_usdt, 'USDT')}</span>
                         </div>
                         <p className="text-[10px] text-text-secondary mt-1">
                            Estimated settlement: 1-2 business days for banking clearance.
                         </p>
                      </div>
                   </div>

                   <div className="p-4 bg-candle-red/5 border border-candle-red/20 rounded-xl flex gap-3">
                      <AlertCircle className="text-candle-red shrink-0" size={18} />
                      <p className="text-xs leading-relaxed text-text-secondary">
                         Any-Time Cash-Out protocol: Tiers are exhausted sequentially to preserve yield-bearing assets. Seed closing is the last resort.
                      </p>
                   </div>

                   <Button
                     onClick={handleExecute}
                     disabled={executing}
                     variant="destructive"
                     className="w-full h-12 text-base uppercase tracking-widest font-black"
                   >
                     {executing ? 'Processing...' : 'Confirm Withdrawal'}
                   </Button>
                </div>
              )}
              </div>
           </div>

           <div className="glass rv">
             <div className="gc p-6 space-y-4">
              <h3 className="font-heading text-xl font-semibold">Your Bank Details</h3>
              <p className="text-xs text-text-secondary">Withdrawals are sent to this account. Ensure details are correct to avoid reversal fees.</p>
              
              <div className="space-y-3">
                 <div className="grid grid-cols-3 gap-2 text-[10px] items-center">
                    <span className="text-text-muted uppercase tracking-widest font-semibold">Bank Name</span>
                    <span className="col-span-2 font-medium">Standard Bank (Retail)</span>
                 </div>
                 <div className="grid grid-cols-3 gap-2 text-[10px] items-center">
                    <span className="text-text-muted uppercase tracking-widest font-semibold">Acc Number</span>
                    <span className="col-span-2 font-mono">**** 5542</span>
                 </div>
                 <button className="text-xs text-candle-green font-bold hover:underline">Update Banking →</button>
              </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
