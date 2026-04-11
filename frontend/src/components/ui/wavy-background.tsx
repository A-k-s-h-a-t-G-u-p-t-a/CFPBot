"use client";
import { cn } from "@/src/lib/utils";
import React, { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { createNoise3D } from "simplex-noise";

export const WavyBackground = ({
  children,
  className,
  containerClassName,
  colors,
  waveWidth,
  backgroundFill,
  blur = 10,
  speed = "fast",
  waveOpacity = 0.5,
  ...props
}: {
  children?: React.ReactNode;
  className?: string;
  containerClassName?: string;
  colors?: string[];
  waveWidth?: number;
  backgroundFill?: string;
  blur?: number;
  speed?: "slow" | "fast";
  waveOpacity?: number;
  [key: string]: unknown;
}) => {
  const noise = createNoise3D();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationIdRef = useRef<number | undefined>(undefined);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const dimensionsRef = useRef({ w: 0, h: 0, nt: 0, i: 0, x: 0 });
  
  const getSpeed = useCallback(() => {
    switch (speed) {
      case "slow":
        return 0.001;
      case "fast":
        return 0.002;
      default:
        return 0.001;
    }
  }, [speed]);

  const waveColors = useMemo(() => colors ?? [
    "#38bdf8",
    "#818cf8",
    "#c084fc",
    "#e879f9",
    "#22d3ee",
  ], [colors]);
  
  const drawWave = useCallback((n: number) => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    
    const dims = dimensionsRef.current;
    dims.nt += getSpeed();
    
    for (dims.i = 0; dims.i < n; dims.i++) {
      ctx.beginPath();
      ctx.lineWidth = waveWidth || 50;
      ctx.strokeStyle = waveColors[dims.i % waveColors.length];
      for (dims.x = 0; dims.x < dims.w; dims.x += 5) {
        const y = noise(dims.x / 800, 0.3 * dims.i, dims.nt) * 100;
        ctx.lineTo(dims.x, y + dims.h * 0.5);
      }
      ctx.stroke();
      ctx.closePath();
    }
  }, [getSpeed, waveWidth, waveColors, noise]);

  const render = useCallback(() => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    
    const dims = dimensionsRef.current;
    ctx.fillStyle = backgroundFill || "black";
    ctx.globalAlpha = waveOpacity || 0.5;
    ctx.fillRect(0, 0, dims.w, dims.h);
    drawWave(5);
    animationIdRef.current = requestAnimationFrame(render);
  }, [backgroundFill, waveOpacity, drawWave]);

  const init = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    
    ctxRef.current = ctx;
    const dims = dimensionsRef.current;
    dims.w = ctx.canvas.width = window.innerWidth;
    dims.h = ctx.canvas.height = window.innerHeight;
    ctx.filter = `blur(${blur}px)`;
    dims.nt = 0;
    
    window.onresize = function () {
      const currentCtx = ctxRef.current;
      if (!currentCtx) return;
      const currentDims = dimensionsRef.current;
      currentDims.w = currentCtx.canvas.width = window.innerWidth;
      currentDims.h = currentCtx.canvas.height = window.innerHeight;
      currentCtx.filter = `blur(${blur}px)`;
    };
    render();
  }, [blur, render]);

  useEffect(() => {
    init();
    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };
  }, [init]);

  const [isSafari, setIsSafari] = useState(false);
  useEffect(() => {
    // I'm sorry but i have got to support it on safari.
    setIsSafari(
      typeof window !== "undefined" &&
        navigator.userAgent.includes("Safari") &&
        !navigator.userAgent.includes("Chrome")
    );
  }, []);

  return (
    <div
      className={cn(
        "h-screen flex flex-col items-center justify-center",
        containerClassName
      )}
    >
      <canvas
        className="absolute inset-0 z-0"
        ref={canvasRef}
        id="canvas"
        style={{
          ...(isSafari ? { filter: `blur(${blur}px)` } : {}),
        }}
      ></canvas>
      <div className={cn("relative z-10", className)} {...props}>
        {children}
      </div>
    </div>
  );
};
