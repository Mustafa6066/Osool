'use client';

import React, { useEffect, useRef } from 'react';
import type { NeuralPhase } from '@/components/chat/neural-signals';

interface NeuralBackgroundProps {
    phase?: NeuralPhase;
    intensity?: number;
}

const PHASE_COLORS: Record<NeuralPhase, { primary: string; secondary: string; tertiary: string }> = {
    idle: { primary: '16, 185, 129', secondary: '13, 148, 136', tertiary: '99, 102, 241' },
    routing: { primary: '45, 212, 191', secondary: '16, 185, 129', tertiary: '139, 92, 246' },
    searching: { primary: '14, 165, 233', secondary: '45, 212, 191', tertiary: '16, 185, 129' },
    analyzing: { primary: '139, 92, 246', secondary: '16, 185, 129', tertiary: '245, 158, 11' },
    responding: { primary: '16, 185, 129', secondary: '52, 211, 153', tertiary: '14, 165, 233' },
    complete: { primary: '34, 197, 94', secondary: '16, 185, 129', tertiary: '45, 212, 191' },
    error: { primary: '248, 113, 113', secondary: '245, 158, 11', tertiary: '139, 92, 246' },
};

const NODES = [
    { x: 0.14, y: 0.22, drift: 0.9 },
    { x: 0.28, y: 0.38, drift: 1.2 },
    { x: 0.42, y: 0.18, drift: 0.7 },
    { x: 0.56, y: 0.48, drift: 1.1 },
    { x: 0.72, y: 0.30, drift: 0.85 },
    { x: 0.84, y: 0.62, drift: 1.3 },
    { x: 0.34, y: 0.72, drift: 1.05 },
    { x: 0.62, y: 0.82, drift: 0.95 },
];

const EDGES = [
    [0, 1], [1, 2], [1, 3], [2, 4], [3, 4], [3, 6], [4, 5], [5, 7], [6, 7], [3, 7],
] as const;

function clampIntensity(value: number) {
    return Math.max(0.12, Math.min(1, value));
}

function isDarkMode() {
    return document.documentElement.classList.contains('dark') ||
        document.documentElement.getAttribute('data-theme') === 'dark';
}

export default function NeuralBackground({ phase = 'idle', intensity = 0.22 }: NeuralBackgroundProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>(0);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d', { alpha: true });
        if (!ctx) return;

        const reduceMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        const palette = PHASE_COLORS[phase];
        const signal = clampIntensity(intensity);
        let width = 0;
        let height = 0;
        let dpr = 1;

        const resize = () => {
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            width = window.innerWidth;
            height = window.innerHeight;
            canvas.width = Math.floor(width * dpr);
            canvas.height = Math.floor(height * dpr);
            canvas.style.width = `${width}px`;
            canvas.style.height = `${height}px`;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        };

        const drawBackgroundField = (timestamp: number, dark: boolean) => {
            const alphaBase = dark ? 0.08 : 0.055;
            const sweep = (Math.sin(timestamp * 0.00018) + 1) / 2;

            const field = ctx.createLinearGradient(0, 0, width, height);
            field.addColorStop(0, `rgba(${palette.primary}, ${alphaBase * signal})`);
            field.addColorStop(0.45, `rgba(${palette.secondary}, ${alphaBase * 0.55 * signal})`);
            field.addColorStop(1, `rgba(${palette.tertiary}, ${alphaBase * 0.38 * signal})`);
            ctx.fillStyle = field;
            ctx.fillRect(0, 0, width, height);

            const band = ctx.createLinearGradient(width * (0.15 + sweep * 0.35), 0, width * (0.65 + sweep * 0.25), height);
            band.addColorStop(0, `rgba(${palette.tertiary}, 0)`);
            band.addColorStop(0.48, `rgba(${palette.tertiary}, ${0.035 * signal})`);
            band.addColorStop(1, `rgba(${palette.tertiary}, 0)`);
            ctx.fillStyle = band;
            ctx.fillRect(0, 0, width, height);
        };

        const drawMesh = (timestamp: number, dark: boolean) => {
            const t = reduceMotionQuery.matches ? 0 : timestamp;
            const points = NODES.map((node, index) => ({
                x: node.x * width + Math.sin(t * 0.00018 * node.drift + index) * 18 * signal,
                y: node.y * height + Math.cos(t * 0.00015 * node.drift + index * 0.7) * 14 * signal,
            }));

            EDGES.forEach(([from, to], edgeIndex) => {
                const a = points[from];
                const b = points[to];
                const pulse = (Math.sin(t * 0.001 + edgeIndex * 0.8) + 1) / 2;
                ctx.beginPath();
                ctx.moveTo(a.x, a.y);
                ctx.lineTo(b.x, b.y);
                ctx.lineWidth = 1;
                ctx.strokeStyle = `rgba(${edgeIndex % 3 === 0 ? palette.primary : palette.secondary}, ${(dark ? 0.18 : 0.12) * signal * (0.42 + pulse * 0.58)})`;
                ctx.stroke();
            });

            points.forEach((point, index) => {
                const pulse = 0.55 + Math.sin(t * 0.0012 + index) * 0.45;
                const radius = 1.4 + signal * 2.2 + pulse * 1.2;
                ctx.beginPath();
                ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${index % 2 ? palette.primary : palette.tertiary}, ${(dark ? 0.34 : 0.24) * signal})`;
                ctx.fill();
            });
        };

        const draw = (timestamp: number) => {
            ctx.clearRect(0, 0, width, height);
            const dark = isDarkMode();
            drawBackgroundField(timestamp, dark);
            drawMesh(timestamp, dark);

            if (!reduceMotionQuery.matches) {
                animationRef.current = requestAnimationFrame(draw);
            }
        };

        resize();
        window.addEventListener('resize', resize);

        const redraw = () => {
            cancelAnimationFrame(animationRef.current);
            animationRef.current = requestAnimationFrame(draw);
        };

        redraw();
        reduceMotionQuery.addEventListener('change', redraw);

        const observer = new MutationObserver(redraw);
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class', 'data-theme'],
        });

        return () => {
            cancelAnimationFrame(animationRef.current);
            window.removeEventListener('resize', resize);
            reduceMotionQuery.removeEventListener('change', redraw);
            observer.disconnect();
        };
    }, [phase, intensity]);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 z-0 pointer-events-none opacity-80 mix-blend-normal"
            aria-hidden="true"
        />
    );
}
