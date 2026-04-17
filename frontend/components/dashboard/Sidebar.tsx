'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/auth/AuthProvider';
import { 
  LayoutDashboard, 
  Trees, 
  History, 
  Wallet, 
  Settings, 
  LogOut, 
  ShieldCheck,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Forest', href: '/dashboard/forest', icon: Trees },
  { name: 'Research', href: '/dashboard/research', icon: Zap },
  { name: 'Trade Log', href: '/dashboard/trades', icon: History },
  { name: 'Funding', href: '/dashboard/funding', icon: Wallet },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-72 border-r border-white/10 bg-[rgba(13,22,40,0.55)] backdrop-blur-xl flex flex-col h-screen sticky top-0 hidden md:flex">
      <div className="p-7">
        <div className="space-y-1">
          <div className="font-heading font-bold tracking-tight text-xl text-text-primary">
            WEALTH ENGINE
          </div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-text-muted font-semibold">
            AUTONOMOUS TRADING
          </div>
          <div className="mt-4 inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-text-secondary">
            <span className="bdot" />
            Live
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center justify-between gap-3 px-4 py-3 rounded-xl transition-all font-semibold",
                isActive 
                  ? "bg-candle-green/12 border border-candle-green/25 text-text-primary shadow-[0_0_28px_rgba(34,197,94,0.18)]"
                  : "border border-transparent text-text-secondary hover:text-text-primary hover:bg-white/5"
              )}
            >
              <span className="flex items-center gap-3">
                <item.icon
                  size={18}
                  className={cn(
                    "transition-colors",
                    isActive ? "text-candle-green" : "text-text-muted group-hover:text-candle-green"
                  )}
                />
                <span className="nav-underline">{item.name}</span>
              </span>
              {isActive && (
                <span className="h-1.5 w-1.5 rounded-full bg-candle-green shadow-[0_0_18px_rgba(34,197,94,0.65)]" />
              )}
            </Link>
          );
        })}

        <div className="pt-4 mt-4 border-t border-border">
          <Link
            href="/dashboard/settings"
            className={cn(
              "group flex items-center justify-between gap-3 px-4 py-3 rounded-xl transition-all font-semibold",
              pathname.includes('/settings') 
                ? "bg-candle-green/12 border border-candle-green/25 text-text-primary shadow-[0_0_28px_rgba(34,197,94,0.18)]"
                : "border border-transparent text-text-secondary hover:text-text-primary hover:bg-white/5"
            )}
          >
            <span className="flex items-center gap-3">
              <Settings
                size={18}
                className={cn(
                  "transition-colors",
                  pathname.includes("/settings")
                    ? "text-candle-green"
                    : "text-text-muted group-hover:text-candle-green"
                )}
              />
              <span className="nav-underline">Settings</span>
            </span>
            {pathname.includes("/settings") && (
              <span className="h-1.5 w-1.5 rounded-full bg-candle-green shadow-[0_0_18px_rgba(34,197,94,0.65)]" />
            )}
          </Link>

          {user?.role === 'master' && (
            <Link
              href="/dashboard/admin"
              className={cn(
                "group flex items-center justify-between gap-3 px-4 py-3 rounded-xl transition-all font-semibold mt-2",
                pathname.includes('/admin') 
                  ? "bg-candle-red/10 border border-candle-red/25 text-text-primary shadow-[0_0_28px_rgba(239,68,68,0.18)]"
                  : "border border-transparent text-text-secondary hover:text-text-primary hover:bg-white/5"
              )}
            >
              <span className="flex items-center gap-3">
                <ShieldCheck
                  size={18}
                  className={cn(
                    "transition-colors",
                    pathname.includes("/admin")
                      ? "text-candle-red"
                      : "text-text-muted group-hover:text-candle-red"
                  )}
                />
                <span className="nav-underline">Admin Panel</span>
              </span>
              {pathname.includes("/admin") && (
                <span className="h-1.5 w-1.5 rounded-full bg-candle-red shadow-[0_0_18px_rgba(239,68,68,0.55)]" />
              )}
            </Link>
          )}
        </div>
      </nav>

      <div className="p-5 border-t border-white/10 space-y-4">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center font-bold text-xs">
            {user?.display_name[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.display_name}</p>
            <p className="text-xs text-text-muted truncate capitalize">{user?.role}</p>
          </div>
        </div>

        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 w-full text-text-secondary hover:text-candle-red transition-colors text-sm font-semibold"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
