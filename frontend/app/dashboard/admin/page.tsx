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
  AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

type PlatformRevenue = {
  total_collected?: number;
};

type AdminUser = {
  id: string;
  display_name: string;
  deposit_reference?: string;
  role: string;
  platform_fee_rate: number;
  is_active: boolean;
};

type Invite = {
  id: string;
  code: string;
  claimed_by?: string | null;
  claimed_at?: string | null;
  created_at: string;
};

export default function AdminPanel() {
  const { user } = useAuth();
  const router = useRouter();
  const [revenue, setRevenue] = useState<PlatformRevenue | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [invites, setInvites] = useState<Invite[]>([]);
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
          api.get<PlatformRevenue>('/admin/platform-revenue'),
          api.get<AdminUser[]>('/admin/users'),
          api.get<Invite[]>('/admin/invites')
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
      await api.post('/funding/deposits/confirm', {
        user_id: depositUserId,
        zar_amount: Number(depositAmount),
        bank_reference: depositBankRef
      });
      alert('Deposit confirmed and balance credited!');
      setDepositAmount('');
      setDepositBankRef('');
    } catch {
      alert('Confirmation failed');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const handleGenerateInvite = async () => {
    try {
      await api.post('/admin/invites', {});
      const data = await api.get<Invite[]>('/admin/invites');
      setInvites(data);
    } catch {
      alert('Failed to generate invite');
    }
  };

  if (loading) return <div>Authenticating Master access...</div>;

  return (
    <div className="space-y-8">
      <header className="flex items-center gap-4">
        <div className="w-12 h-12 bg-candle-red/10 border border-candle-red/25 rounded-full flex items-center justify-center text-candle-red">
          <ShieldAlert size={24} />
        </div>
        <div>
          <div className="section-label">Master</div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">Master Operations</h1>
          <p className="mt-3 text-text-secondary">Global oversight for the Recursive Fractal Wealth Engine.</p>
        </div>
      </header>

      {/* Revenue Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass rv">
          <div className="gc p-6 space-y-2">
          <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">Total Platform Fees</p>
          <div className="flex items-center gap-2">
             <DollarSign className="text-candle-green" size={20} />
             <p className="font-heading text-3xl font-bold gradient-text-green">{formatCurrency(revenue?.total_collected || 0)}</p>
          </div>
          <p className="text-xs text-candle-green font-bold">+12% vs last month</p>
          </div>
        </div>
        
        <div className="glass rv">
          <div className="gc p-6 space-y-2">
           <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">Active Users</p>
           <div className="flex items-center gap-2">
              <Users className="text-text-muted" size={20} />
              <p className="font-heading text-3xl font-bold">{users.length}</p>
           </div>
           <p className="text-xs text-text-secondary">{invites.filter(i => i.claimed_by).length} invited successfully</p>
          </div>
        </div>

        <div className="glass rv">
          <div className="gc p-6 space-y-2">
           <p className="text-xs uppercase tracking-widest text-text-muted font-semibold">Invite Management</p>
           <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                  <Ticket className="text-candle-green" size={20} />
                  <p className="font-heading text-3xl font-bold">{invites.filter(i => !i.claimed_by).length} Available</p>
              </div>
              <Button onClick={handleGenerateInvite} size="sm">
                Generate New
              </Button>
           </div>
           
           <div className="mt-6 space-y-3 max-h-[150px] overflow-y-auto pr-2 custom-scrollbar">
              {invites.map(i => (
                <div key={i.id} className={cn(
                  "flex items-center justify-between p-2 rounded-lg border text-xs",
                  i.claimed_by ? "bg-white/2 border-white/5 opacity-50" : "bg-white/5 border-white/10"
                )}>
                  <div className="flex flex-col gap-0.5">
                    <span className="font-mono font-bold tracking-tight">{i.code}</span>
                    <span className="text-[9px] text-text-muted">
                      {i.claimed_by ? `Claimed ${new Date(i.claimed_at!).toLocaleDateString()}` : 'Unclaimed'}
                    </span>
                  </div>
                  {!i.claimed_by && (
                    <div className="flex gap-1">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-6 px-2 text-[9px]"
                        onClick={() => copyToClipboard(i.code)}
                      >
                        Code
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-6 px-2 text-[9px]"
                        onClick={() => copyToClipboard(`https://wealth.theaicrucible.com/register?invite=${i.code}`)}
                      >
                        Link
                      </Button>
                    </div>
                  )}
                </div>
              ))}
           </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Manual Deposit Confirmation */}
        <div className="glass rv">
          <div className="gc p-6 space-y-6">
           <h2 className="text-xl font-bold flex items-center gap-2 uppercase tracking-tight">
              <Zap className="text-candle-green" size={20} />
              Confirm External P2P Deposit
           </h2>
           
           <form onSubmit={handleConfirmDeposit} className="space-y-4">
              <div className="space-y-4 p-4 bg-white/5 border border-white/10 rounded-xl">
                 <div>
                    <label className="text-xs font-bold uppercase tracking-widest text-text-muted">Select User</label>
                    <select 
                      value={depositUserId} 
                      onChange={(e) => setDepositUserId(e.target.value)}
                      className="w-full mt-2 p-3 bg-white/5 border border-white/12 rounded-xl outline-none text-sm"
                    >
                       <option value="">Select a user...</option>
                       {users.map(u => (
                         <option key={u.id} value={u.id}>{u.display_name} ({u.deposit_reference})</option>
                       ))}
                    </select>
                 </div>
                 <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-xs font-bold uppercase tracking-widest text-text-muted">Amount (ZAR)</label>
                        <Input
                          type="number" 
                          value={depositAmount}
                          onChange={(e) => setDepositAmount(e.target.value)}
                          className="mt-2"
                          placeholder="0.00"
                        />
                    </div>
                    <div>
                        <label className="text-xs font-bold uppercase tracking-widest text-text-muted">Bank Ref (Optional)</label>
                        <Input
                          type="text" 
                          value={depositBankRef}
                          onChange={(e) => setDepositBankRef(e.target.value)}
                          className="mt-2"
                          placeholder="ABC-123..."
                        />
                    </div>
                 </div>
              </div>

              <div className="flex gap-3 p-3 bg-candle-red/5 border border-candle-red/20 rounded-xl text-candle-red">
                 <AlertCircle size={18} className="shrink-0 text-candle-red" />
                 <p className="text-[10px] leading-relaxed italic">
                    By confirming, you verify that ZAR has been received in the Capitec Business account. USDT will be credited to the user&apos;s internal allocation at the current Binance market rate.
                 </p>
              </div>

              <Button type="submit" className="w-full">
                Confirm Receipt & Credit USDT
              </Button>
           </form>
          </div>
        </div>

        {/* User Management */}
        <div className="glass rv">
          <div className="gc p-6">
           <h2 className="font-heading text-3xl font-bold mb-6">User Registry</h2>
           <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
              {users.map(u => (
                <div key={u.id} className="flex items-center justify-between p-3 border-b border-white/10 last:border-0">
                   <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center font-bold text-xs uppercase">
                        {u.display_name[0]}
                      </div>
                      <div>
                         <p className="text-sm font-bold">{u.display_name}</p>
                         <p className="text-[10px] text-text-muted uppercase tracking-widest">{u.role} • Fee: {u.platform_fee_rate * 100}%</p>
                      </div>
                   </div>
                   <div className="text-right">
                      <p className="text-xs font-bold">{u.deposit_reference || 'NO REF'}</p>
                      <span className={cn(
                        "text-[10px] px-1.5 py-0.5 rounded font-bold uppercase",
                        u.is_active ? "bg-candle-green/10 text-candle-green" : "bg-candle-red/10 text-candle-red"
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
    </div>
  );
}
