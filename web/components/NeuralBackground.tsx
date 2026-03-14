'use client';

import React, { useEffect, useRef, useMemo } from 'react';

/**
 * NeuralBackground V6 — Ultra Minimal Ambient
 * ------------------------------------------------
 * Slow-moving gradient orbs only. No dot grid.
 * Barely perceptible — creates depth without distraction.
 */
export default function NeuralBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>(0);

    const orbs = useMemo(() => [
        { x: 0.15, y: 0.25, radius: 400, speed: 0.00015, phase: 0 },
        { x: 0.75, y: 0.65, radius: 350, speed: 0.0002, phase: 2.5 },
    ], []);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let width = 0;
        let height = 0;

        const resize = () => {
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            width = window.innerWidth;
            height = window.innerHeight;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            canvas.style.width = `${width}px`;
            canvas.style.height = `${height}px`;
            ctx.scale(dpr, dpr);
        };

        resize();
        window.addEventListener('resize', resize);

        const isDark = () => {
            return document.documentElement.classList.contains('dark') ||
                document.documentElement.getAttribute('data-theme') === 'dark';
        };

        const draw = (timestamp: number) => {
            ctx.clearRect(0, 0, width, height);
            const dark = isDark();

            orbs.forEach((orb) => {
                const ox = orb.x * width + Math.sin(timestamp * orb.speed + orb.phase) * 60;
                const oy = orb.y * height + Math.cos(timestamp * orb.speed * 0.7 + orb.phase) * 40;
                const pulse = 0.85 + Math.sin(timestamp * 0.0006 + orb.phase) * 0.15;
                const r = orb.radius * pulse;

                const gradient = ctx.createRadialGradient(ox, oy, 0, ox, oy, r);
                if (dark) {
                    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.018)');
                    gradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.008)');
                    gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');
                } else {
                    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.012)');
                    gradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.005)');
                    gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');
                }

                ctx.beginPath();
                ctx.arc(ox, oy, r, 0, Math.PI * 2);
                ctx.fillStyle = gradient;
                ctx.fill();
            });

            animationRef.current = requestAnimationFrame(draw);
        };

        animationRef.current = requestAnimationFrame(draw);

        const observer = new MutationObserver(() => {});
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class', 'data-theme']
        });

        return () => {
            cancelAnimationFrame(animationRef.current);
            window.removeEventListener('resize', resize);
            observer.disconnect();
        };
    }, [orbs]);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 z-0 pointer-events-none"
            aria-hidden="true"
        />
    );
}
