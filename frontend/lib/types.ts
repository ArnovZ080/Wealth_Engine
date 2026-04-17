/**
 * Shared Type Definitions for Recursive Fractal Wealth Engine Frontend.
 */

export type UserRole = 'master' | 'member';

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
  is_active: boolean;
  deposit_reference?: string;
  platform_fee_rate: number;
  last_heartbeat: string;
}

export interface UserForestState {
  user_id: string;
  shared_reservoir_balance: number;
  shared_nursery_balance: number;
  vault_tier1_buidl: number;
  vault_tier2_etfs: number;
  vault_tier3_realestate: number;
  kill_switch_status: 'active' | 'paused' | 'global_pause';
  total_platform_fees_paid: number;
  usd_zar_rate?: number;
  portfolio?: {
    total_value_usd: number;
    total_value_zar: number;
    reservoir_zar: number;
    nursery_zar: number;
    vault_zar: number;
    reinvestment_zar: number;
  };
}

export interface Tree {
  id: string;
  name: string;
  is_active: boolean;
  user_id: string;
  seed_count: number;
  performance_30d?: number;
}

export interface Seed {
  id: string;
  tree_id: string;
  strategy_type: string;
  current_value: number;
  strike_count: number;
  is_active: boolean;
  ground_zero_triggered: boolean;
  created_at: string;
}

export interface TradeDecision {
  id: string;
  seed_id: string;
  ticker: string;
  direction: 'long' | 'short';
  entry_price: number;
  exit_price?: number;
  status: 'open' | 'closed';
  realized_pnl?: number;
  exit_reason?: string;
  created_at: string;
  confidence: number;
  exchange: string;
}

export interface FundingTransaction {
  id: string;
  type: 'deposit' | 'withdrawal';
  zar_amount: number;
  fx_rate_used?: number;
  usd_amount?: number;
  status: 'pending' | 'confirmed' | 'credited' | 'liquidating' | 'processing' | 'completed' | 'failed';
  reference_code: string;
  created_at: string;
  completed_at?: string;
  manual_review_flag: boolean;
}
