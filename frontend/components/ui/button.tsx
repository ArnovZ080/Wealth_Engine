"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type ButtonVariant =
  | "default"
  | "destructive"
  | "outline"
  | "secondary"
  | "ghost"
  | "link";

export type ButtonSize = "default" | "sm" | "lg" | "icon";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const variants: Record<ButtonVariant, string> = {
  default:
    "bg-gradient-to-br from-candle-green to-candle-green-dark text-white shadow-[0_0_35px_rgba(34,197,94,0.38)] hover:shadow-[0_0_70px_rgba(34,197,94,0.65)] hover:-translate-y-0.5 border border-candle-green/30",
  destructive:
    "bg-gradient-to-br from-candle-red to-candle-red-dark text-white shadow-[0_0_35px_rgba(239,68,68,0.38)] hover:shadow-[0_0_70px_rgba(239,68,68,0.65)] hover:-translate-y-0.5 border border-candle-red/30",
  outline:
    "bg-white/5 border border-white/15 text-text-primary hover:border-candle-green hover:bg-candle-green/10 hover:-translate-y-0.5 backdrop-blur-sm",
  secondary:
    "bg-card border border-border-subtle text-text-primary hover:border-border-hover",
  ghost: "hover:bg-candle-green/10 text-text-primary",
  link: "text-candle-green underline-offset-4 hover:underline",
};

const sizes: Record<ButtonSize, string> = {
  default: "h-11 px-5 py-2.5 text-sm",
  sm: "h-9 px-3.5 text-sm",
  lg: "h-12 px-7 text-base",
  icon: "h-10 w-10",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-300 ease-out disabled:pointer-events-none disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-[rgba(34,197,94,0.65)] focus-visible:ring-offset-2 focus-visible:ring-offset-void",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

