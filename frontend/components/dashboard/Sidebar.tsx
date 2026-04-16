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
import { cn } from '@/lib/utils'; // I'll need to create lib/utils.ts

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
    <aside className="w-64 border-r border-border bg-card flex flex-col h-screen sticky top-0 hidden md:flex">
      <div className="p-6">
        <div className="flex items-center gap-2 text-primary font-bold text-xl">
          <span className="text-2xl">🌳</span>
          <span>WE ENGINE</span>
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
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors font-medium",
                isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:text-foreground hover:bg-secondary"
              )}
            >
              <item.icon size={20} />
              {item.name}
            </Link>
          );
        })}

        <div className="pt-4 mt-4 border-t border-border">
          <Link
            href="/dashboard/settings"
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md transition-colors font-medium",
              pathname.includes('/settings') 
                ? "bg-primary text-primary-foreground" 
                : "text-muted-foreground hover:text-foreground hover:bg-secondary"
            )}
          >
            <Settings size={20} />
            Settings
          </Link>

          {user?.role === 'master' && (
            <Link
              href="/dashboard/admin"
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md transition-colors font-medium mt-2",
                pathname.includes('/admin') 
                  ? "bg-amber-500 text-black" 
                  : "text-amber-500/70 hover:text-amber-500 hover:bg-amber-500/10"
              )}
            >
              <ShieldCheck size={20} />
              Admin Panel
            </Link>
          )}
        </div>
      </nav>

      <div className="p-4 border-t border-border space-y-4">
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center font-bold text-xs">
            {user?.display_name[0].toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">{user?.display_name}</p>
            <p className="text-xs text-muted-foreground truncate capitalize">{user?.role}</p>
          </div>
        </div>

        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 w-full text-muted-foreground hover:text-destructive transition-colors text-sm font-medium"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
