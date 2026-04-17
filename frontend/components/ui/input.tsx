"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        ref={ref}
        type={type}
        className={cn(
          "flex h-11 w-full rounded-xl border border-white/12 bg-white/5 px-3 py-2 text-sm text-text-primary placeholder:text-text-muted shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgba(34,197,94,0.65)] focus-visible:ring-offset-2 focus-visible:ring-offset-void",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

