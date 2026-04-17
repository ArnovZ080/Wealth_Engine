"use client";
import { useEffect, useRef } from "react";

interface EmberFieldProps {
  count?: number;
  className?: string;
}

export function EmberField({ count = 90, className = "" }: EmberFieldProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const c = canvas;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    const context = ctx;

    const section = c.parentElement;
    if (!section) return;
    const host = section;

    let W = 0,
      H = 0,
      running = false,
      rafId = 0;

    // Trading candle palette: green, red, white
    const COLORS = [
      "34,197,94", // candle green
      "239,68,68", // candle red
      "240,245,255", // pure white
      "34,197,94", // green (weighted)
      "239,68,68", // red (weighted)
      "180,200,220", // pale grey-white
    ];

    interface Point {
      x: number;
      y: number;
      vx: number;
      vy: number;
      r: number;
      base: number;
      t: number;
      ts: number;
      col: string;
      swayAmp: number;
      swayFreq: number;
      swayOff: number;
    }

    const pts: Point[] = [];
    for (let i = 0; i < count; i++) {
      pts.push({
        x: Math.random(),
        y: Math.random(),
        vx: (Math.random() - 0.5) * 0.00018,
        vy: -(Math.random() * 0.00025 + 0.00008),
        r: Math.random() * 2.0 + 0.6,
        base: Math.random() * 0.7 + 0.3,
        t: Math.random() * Math.PI * 2,
        ts: Math.random() * 0.022 + 0.006,
        col: COLORS[Math.floor(Math.random() * COLORS.length)],
        swayAmp: (Math.random() - 0.5) * 0.00012,
        swayFreq: Math.random() * 0.04 + 0.01,
        swayOff: Math.random() * Math.PI * 2,
      });
    }

    function setSize() {
      const sw = host.scrollWidth || window.innerWidth;
      const sh = host.scrollHeight || 600;
      if (sw === W && sh === H) return;
      W = c.width = sw;
      H = c.height = sh;
    }

    function draw() {
      setSize();
      context.clearRect(0, 0, W, H);
      pts.forEach((p) => {
        p.y += p.vy;
        if (p.y < -0.02) p.y = 1.02;
        p.x += p.vx + Math.sin(p.t * p.swayFreq + p.swayOff) * p.swayAmp;
        p.x = ((p.x % 1) + 1) % 1;
        p.t += p.ts;
        const flicker = 0.35 + 0.65 * Math.abs(Math.sin(p.t));
        const a = p.base * flicker;
        const px = p.x * W,
          py = p.y * H;

        // Outer glow halo
        const g = context.createRadialGradient(px, py, 0, px, py, p.r * 6);
        g.addColorStop(0, `rgba(${p.col},${a * 0.45})`);
        g.addColorStop(1, `rgba(${p.col},0)`);
        context.beginPath();
        context.arc(px, py, p.r * 6, 0, Math.PI * 2);
        context.fillStyle = g;
        context.fill();

        // Bright core
        context.beginPath();
        context.arc(px, py, p.r, 0, Math.PI * 2);
        context.fillStyle = `rgba(${p.col},${Math.min(a * 1.4, 1)})`;
        context.shadowColor = `rgba(${p.col},0.9)`;
        context.shadowBlur = 8;
        context.fill();
        context.shadowBlur = 0;
      });
      rafId = requestAnimationFrame(draw);
    }

    const ro = new ResizeObserver(() => {
      setSize();
      if (!running) {
        running = true;
        draw();
      }
    });
    ro.observe(host);
    const timeoutId = setTimeout(() => {
      setSize();
      if (!running) {
        running = true;
        draw();
      }
    }, 300);

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
      clearTimeout(timeoutId);
    };
  }, [count]);

  return (
    <canvas
      ref={canvasRef}
      className={`absolute inset-0 pointer-events-none z-0 ${className}`}
    />
  );
}

