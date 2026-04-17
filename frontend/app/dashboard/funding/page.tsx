'use client';

import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { FundingTransaction } from '@/lib/types';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  Building2, 
  CreditCard, 
  Copy, 
  ArrowUpCircle, 
  ArrowDownCircle,
  Clock,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function FundingPage() {
  const [instructions, setInstructions] = useState<any>(null);
  const [transactions, setTransactions] = useState<FundingTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [preview, setPreview] = useState<any>(null);
  const [executing, setExecuting] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        const [instData, txData] = await Promise.all([
          api.get<any>('/api/v1/funding/deposit-instructions'),
          api.get<FundingTransaction[]>('/api/v1/funding/transactions')
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
      const data = await api.post<any>('/api/v1/funding/withdraw/preview', {
        amount_zar: Number(withdrawAmount)
      });
      setPreview(data);
    } catch (err) {
      alert('Failed to calculate preview');
    }
  };

  const handleExecute = async () => {
    if (!withdrawAmount) return;
    setExecuting(true);
    try {
      await api.post('/api/v1/funding/withdraw/execute', {
        amount_zar: Number(withdrawAmount)
      });
      alert('Withdrawal request submitted!');
      setWithdrawAmount('');
      setPreview(null);
      // Refresh history
      const txData = await api.get<FundingTransaction[]>('/api/v1/funding/transactions');
      setTransactions(txData);
    } catch (err) {
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
        <h1 className="text-3xl font-bold">Funding & Liquidation</h1>
        <p className="text-muted-foreground">Manage your ZAR lifecycle and any-time cash-out hierarchical liquidation.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Deposit Side */}
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 space-y-6">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <ArrowUpCircle className="text-emerald-500" size={24} />
              Deposit Funds
            </h2>
            
            <div className="bg-emerald-500/5 border border-emerald-500/20 p-4 rounded-lg space-y-4">
               <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500 flex-shrink-0">
                    <Building2 size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold">Capitec Business Bank Details</h3>
                    <p className="text-sm text-muted-foreground">Transfer ZAR to your unique ref for automated allocation.</p>
                  </div>
               </div>

               <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                  <div className="p-3 bg-secondary rounded-md">
                     <p className="text-xs text-muted-foreground font-medium uppercase">Bank Name</p>
                     <p className="font-bold">{instructions?.bank_name}</p>
                  </div>
                  <div className="p-3 bg-secondary rounded-md">
                     <p className="text-xs text-muted-foreground font-medium uppercase">Branch Code</p>
                     <p className="font-bold">{instructions?.branch_code}</p>
                  </div>
                  <div className="p-3 bg-secondary rounded-md col-span-2 relative group">
                     <p className="text-xs text-muted-foreground font-medium uppercase">Account Number</p>
                     <p className="font-bold font-mono">{instructions?.account_number}</p>
                     <button 
                      onClick={() => copyToClipboard(instructions?.account_number)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1 hover:bg-muted-foreground/10 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                     >
                        <Copy size={16} />
                     </button>
                  </div>
                  <div className="p-4 bg-primary text-primary-foreground rounded-md col-span-2 relative group shadow-lg">
                     <p className="text-xs text-primary-foreground/70 font-bold uppercase tracking-wider">MANDATORY REFERENCE</p>
                     <p className="text-xl font-black font-mono mt-1">{instructions?.reference}</p>
                     <button 
                      onClick={() => copyToClipboard(instructions?.reference)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-2 hover:bg-black/10 rounded"
                     >
                        <Copy size={18} />
                     </button>
                  </div>
               </div>
            </div>

            <p className="text-xs text-muted-foreground italic leading-relaxed">
              * Payments without the correct reference will be flagged for manual review and may take up to 5 business days to credit.
            </p>
          </div>

          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-xl font-bold mb-6">Recent Transactions</h2>
            <div className="space-y-4 text-sm">
               {transactions.map(tx => (
                 <div key={tx.id} className="flex items-center justify-between p-3 border-b border-border last:border-0 hover:bg-secondary/30 rounded-lg transition-colors">
                    <div className="flex items-center gap-3">
                       <div className={cn(
                          "w-8 h-8 rounded-full flex items-center justify-center",
                          tx.type === 'deposit' ? "bg-emerald-500/10 text-emerald-500" : "bg-amber-500/10 text-amber-500"
                       )}>
                          {tx.type === 'deposit' ? <ArrowUpCircle size={14} /> : <ArrowDownCircle size={14} />}
                       </div>
                       <div>
                          <p className="font-bold capitalize">{tx.type}</p>
                          <p className="text-[10px] text-muted-foreground">{new Date(tx.created_at).toLocaleDateString()}</p>
                       </div>
                    </div>
                    <div className="text-right">
                       <p className="font-bold">{formatCurrency(tx.amount_zar, 'ZAR')}</p>
                       <div className="flex items-center justify-end gap-1 text-[10px]">
                          {tx.status === 'completed' || tx.status === 'credited' ? (
                            <span className="flex items-center gap-0.5 text-emerald-500">
                               <CheckCircle2 size={10} /> Completed
                            </span>
                          ) : (
                            <span className="flex items-center gap-0.5 text-amber-500">
                               <Clock size={10} /> {tx.status}
                            </span>
                          )}
                       </div>
                    </div>
                 </div>
               ))}
               {transactions.length === 0 && (
                  <p className="text-center py-6 text-muted-foreground italic">No transaction history found.</p>
               )}
            </div>
          </div>
        </div>

        {/* Withdrawal Side */}
        <div className="space-y-6">
           <div className="bg-card border border-border rounded-xl p-6 space-y-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <ArrowDownCircle className="text-amber-500" size={24} />
                Request Withdrawal
              </h2>

              <div className="space-y-4">
                 <div>
                    <label className="text-sm font-medium mb-1 block">Amount (ZAR)</label>
                    <div className="relative">
                       <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground font-bold">R</span>
                       <input 
                        type="number" 
                        value={withdrawAmount}
                        onChange={(e) => setWithdrawAmount(e.target.value)}
                        placeholder="0.00"
                        className="w-full pl-8 pr-4 py-3 bg-secondary border border-border rounded-lg outline-none focus:ring-1 focus:ring-primary font-bold text-lg"
                       />
                    </div>
                 </div>

                 <button 
                  onClick={handlePreview}
                  className="w-full py-3 bg-secondary border border-border rounded-lg font-bold hover:bg-secondary/80 transition-colors"
                 >
                    Preview Hierarchical Liquidation
                 </button>
              </div>

              {preview && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-300">
                   <div className="p-4 bg-muted/30 border border-border rounded-lg space-y-3">
                      <h4 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">Liquidation Breakdown</h4>
                      {preview.breakdown.map((item: any, idx: number) => (
                        <div key={idx} className="flex justify-between items-center text-sm">
                           <div className="flex items-center gap-2">
                              {idx === 0 ? <CheckCircle2 size={14} className="text-emerald-500" /> : <Clock size={14} className="text-muted-foreground" />}
                              <span className="font-medium">{item.source}</span>
                           </div>
                           <span className="font-mono font-bold">{formatCurrency(item.amount_usdt, 'USDT')}</span>
                        </div>
                      ))}

                      <div className="pt-3 border-t border-border mt-3">
                         <div className="flex justify-between items-center">
                            <span className="font-bold">Total Fulfillable</span>
                            <span className="font-bold text-lg">{formatCurrency(preview.fulfillable_usdt, 'USDT')}</span>
                         </div>
                         <p className="text-[10px] text-muted-foreground mt-1">
                            Estimated settlement: 1-2 business days for banking clearance.
                         </p>
                      </div>
                   </div>

                   <div className="p-4 bg-amber-500/5 border border-amber-500/20 rounded-lg flex gap-3">
                      <AlertCircle className="text-amber-500 shrink-0" size={18} />
                      <p className="text-xs leading-relaxed text-amber-200/80">
                         Any-Time Cash-Out protocol: Tiers are exhausted sequentially to preserve yield-bearing assets. Seed closing is the last resort.
                      </p>
                   </div>

                   <button 
                    onClick={handleExecute}
                    disabled={executing}
                    className="w-full py-4 bg-primary text-primary-foreground rounded-lg font-black text-lg shadow-xl shadow-primary/10 hover:opacity-90 transition-opacity uppercase tracking-widest"
                   >
                      {executing ? 'Processing...' : 'Confirm Withdrawal'}
                   </button>
                </div>
              )}
           </div>

           <div className="bg-card border border-border rounded-xl p-6 space-y-4">
              <h3 className="font-bold">Your Bank Details</h3>
              <p className="text-xs text-muted-foreground">Withdrawals are sent to this account. Ensure details are correct to avoid reversal fees.</p>
              
              <div className="space-y-3">
                 <div className="grid grid-cols-3 gap-2 text-[10px] items-center">
                    <span className="text-muted-foreground uppercase font-bold">Bank Name</span>
                    <span className="col-span-2 font-medium">Standard Bank (Retail)</span>
                 </div>
                 <div className="grid grid-cols-3 gap-2 text-[10px] items-center">
                    <span className="text-muted-foreground uppercase font-bold">Acc Number</span>
                    <span className="col-span-2 font-mono">**** 5542</span>
                 </div>
                 <button className="text-xs text-primary font-bold hover:underline">Update Banking →</button>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}
