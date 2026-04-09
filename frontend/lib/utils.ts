import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, currency: string = 'USDT', precision: number = 2) {
  if (currency === 'ZAR') {
    return new Intl.NumberFormat('en-ZA', {
      style: 'currency',
      currency: 'ZAR',
      minimumFractionDigits: 2,
    }).format(amount);
  }
  
  return `${amount.toLocaleString(undefined, { minimumFractionDigits: precision, maximumFractionDigits: precision })} ${currency}`;
}

export function formatPercent(value: number) {
  return `${(value * 100).toFixed(2)}%`;
}
