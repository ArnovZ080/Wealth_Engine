'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/components/auth/AuthProvider';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { formatCurrency, cn } from '@/lib/utils';
import { 
  Users, 
  Ticket, 
  ShieldAlert, 
  DollarSign, 
  Zap, 
  CheckCircle2, 
  AlertCircle
} from 'lucide-react';

export default function AdminPanel() {
  const { user } = useAuth();
  const router = useRouter();
  const [revenue, setRevenue] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [invites, setInvites] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Manual deposit confirmation form state
  const [depositUserId, setDepositUserId] = useState('');
  const [depositAmount, setDepositAmount] = useState('');
  const [depositBankRef, setDepositBankRef] = useState('');

  useEffect(() => {
    if (user?.role !== 'master') {
      router.push('/dashboard');
      return;
    }

    async function fetchAdminData() {
      try {
        const [revData, usersData, invitesData] = await Promise.all([
          api.get<any>('/admin/platform-revenue'),
          api.get<any[]>('/admin/users'),
          api.get<any[]>('/admin/invites')
        ]);
        setRevenue(revData);
        setUsers(usersData);
        setInvites(invitesData);
      } catch (err) {
        console.error('Failed to fetch admin data', err);
      } finally {
        setLoading(false);
      }
    }
    fetchAdminData();
  }, [user, router]);

  const handleConfirmDeposit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!depositUserId || !depositAmount) return;
    
    try {
      await api.post('/api/v1/funding/deposits/confirm', {
        user_id: depositUserId,
        amount_zar: Number(depositAmount),
        bank_reference: depositBankRef
      });
      alert('Deposit confirmed and balance credited!');
      setDepositAmount('');
      setDepositBankRef('');
    } catch (err) {
      alert('Confirmation failed');
    }
  };

  const handleGenerateInvite = async () => {
    try {
      await api.post('/admin/invites', {});
      const data = await api.get<any[]>('/admin/invites');
      setInvites(data);
    } catch (err) {
      alert('Failed to generate invite');
    }
  };

  if (loading) return <div>Authenticating Master access...</div>;

  return (
    <div className="space-y-8">
      <header className="flex items-center gap-4">
        <div className="w-12 h-12 bg-amber-500 rounded-full flex items-center justify-center text-black">
          <ShieldAlert size={24} />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Master Operations</h1>
          <p className="text-muted-foreground">Global oversight for the Recursive Fractal Wealth Engine.</p>
        </div>
      </header>

      {/* Revenue Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-card border border-border rounded-xl space-y-2">
          <p className="text-sm text-muted-foreground font-medium">Total Platform Fees</p>
          <div className="flex items-center gap-2">
             <DollarSign className="text-amber-500" size={24} />
             <p className="text-3xl font-black">{formatCurrency(revenue?.total_collected || 0)}</p>
          </div>
          <p className="text-xs text-emerald-500 font-bold">+12% vs last month</p>
        </div>
        
        <div className="p-6 bg-card border border-border rounded-xl space-y-2">
           <p className="text-sm text-muted-foreground font-medium">Active Users</p>
           <div className="flex items-center gap-2">
              <Users className="text-primary" size={24} />
              <p className="text-3xl font-black">{users.length}</p>
           </div>
           <p className="text-xs text-muted-foreground">{invites.filter(i => i.claimed_by).length} invited successfully</p>
        </div>

        <div className="p-6 bg-card border border-border rounded-xl space-y-2">
           <p className="text-sm text-muted-foreground font-medium">Available Invites</p>
           <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                  <Ticket className="text-blue-500" size={24} />
                  <p className="text-3xl font-black">{invites.filter(i => !i.claimed_by).length}</p>
              </div>
              <button 
                onClick={handleGenerateInvite}
                className="px-3 py-1 bg-blue-500 text-black text-xs font-bold rounded hover:opacity-90"
              >
                Generate +
              </button>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Manual Deposit Confirmation */}
        <div className="bg-card border border-border rounded-xl p-6 space-y-6 shadow-xl shadow-amber-500/5">
           <h2 className="text-xl font-bold flex items-center gap-2 uppercase tracking-tight">
              <Zap className="text-amber-500" size={20} />
              Confirm External P2P Deposit
           </h2>
           
           <form onSubmit={handleConfirmDeposit} className="space-y-4">
              <div className="space-y-4 p-4 bg-secondary/50 rounded-lg">
                 <div>
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Select User</label>
                    <select 
                      value={depositUserId} 
                      onChange={(e) => setDepositUserId(e.target.value)}
                      className="w-full mt-1 p-2 bg-background border border-border rounded-md outline-none text-sm"
                    >
                       <option value="">Select a user...</option>
                       {users.map(u => (
                         <option key={u.id} value={u.id}>{u.display_name} ({u.deposit_reference})</option>
                       ))}
                    </select>
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Amount (ZAR)</label>
                        <input 
                          type="number" 
                          value={depositAmount}
                          onChange={(e) => setDepositAmount(e.target.value)}
                          className="w-full mt-1 p-2 bg-background border border-border rounded-md outline-none text-sm"
                          placeholder="0.00"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Bank Ref (Optional)</label>
                        <input 
                          type="text" 
                          value={depositBankRef}
                          onChange={(e) => setDepositBankRef(e.target.value)}
                          className="w-full mt-1 p-2 bg-background border border-border rounded-md outline-none text-sm"
                          placeholder="ABC-123..."
                        />
                    </div>
                 </div>
              </div>

              <div className="flex gap-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-500">
                 <AlertCircle size={18} className="shrink-0" />
                 <p className="text-[10px] leading-relaxed italic">
                    By confirming, you verify that ZAR has been received in the Capitec Business account. USDT will be credited to the user's internal allocation at the current Binance market rate.
                 </p>
              </div>

              <button 
                type="submit"
                className="w-full py-3 bg-amber-500 text-black font-black uppercase tracking-widest rounded-md hover:opacity-90 transition-opacity"
              >
                Confirm Receipt & Credit USDT
              </button>
           </form>
        </div>

        {/* User Management */}
        <div className="bg-card border border-border rounded-xl p-6">
           <h2 className="text-xl font-bold mb-6">User Registry</h2>
           <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
              {users.map(u => (
                <div key={u.id} className="flex items-center justify-between p-3 border-b border-border last:border-0">
                   <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center font-bold text-xs uppercase">
                        {u.display_name[0]}
                      </div>
                      <div>
                         <p className="text-sm font-bold">{u.display_name}</p>
                         <p className="text-[10px] text-muted-foreground uppercase">{u.role} • Fee: {u.platform_fee_rate * 100}%</p>
                      </div>
                   </div>
                   <div className="text-right">
                      <p className="text-xs font-bold">{u.deposit_reference || 'NO REF'}</p>
                      <span className={cn(
                        "text-[10px] px-1.5 py-0.5 rounded font-bold uppercase",
                        u.is_active ? "bg-emerald-500/10 text-emerald-500" : "bg-destructive/10 text-destructive"
                      )}>
                        {u.is_active ? 'Online' : 'Restricted'}
                      </span>
                   </div>
                </div>
              ))}
           </div>
        </div>
      </div>
    </div>
  );
}
