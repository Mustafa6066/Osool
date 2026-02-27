'use client';

import React, { useEffect, useRef, useMemo } from 'react';

/**
 * NeuralBackground V5 — AI Agency Ambient Canvas
 * ------------------------------------------------
 * Subtle animated dot grid with floating gradient orbs.
 * Gives the feeling of "AI breathing" in the background.
 *
 * Light mode: Faint zinc dots on white
 * Dark mode: Dim zinc dots on true black + emerald glow orbs
 */
export default function NeuralBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animationRef = useRef<number>(0);
    const timeRef = useRef(0);

    // Generate stable orb positions
    const orbs = useMemo(() => [
        { x: 0.2, y: 0.3, radius: 300, speed: 0.0003, phase: 0 },
        { x: 0.7, y: 0.6, radius: 250, speed: 0.0004, phase: 2 },
        { x: 0.5, y: 0.8, radius: 200, speed: 0.0005, phase: 4 },
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
            timeRef.current = timestamp;
            ctx.clearRect(0, 0, width, height);

            const dark = isDark();
            const dotSpacing = 40;
            const cols = Math.ceil(width / dotSpacing) + 1;
            const rows = Math.ceil(height / dotSpacing) + 1;

            // Draw dot grid
            for (let i = 0; i < cols; i++) {
                for (let j = 0; j < rows; j++) {
                    const x = i * dotSpacing;
                    const y = j * dotSpacing;

                    // Subtle wave animation — dots breathe
                    const wave = Math.sin(timestamp * 0.001 + i * 0.3 + j * 0.3) * 0.5 + 0.5;
                    const baseOpacity = dark ? 0.06 : 0.04;
                    const opacity = baseOpacity + wave * (dark ? 0.04 : 0.02);
                    const radius = 1 + wave * 0.3;

                    ctx.beginPath();
                    ctx.arc(x, y, radius, 0, Math.PI * 2);
                    ctx.fillStyle = dark
                        ? `rgba(161, 161, 170, ${opacity})`  // zinc-400
                        : `rgba(113, 113, 122, ${opacity})`;  // zinc-500
                    ctx.fill();
                }
            }

            // Draw floating gradient orbs (AI presence)
            orbs.forEach((orb) => {
                const ox = orb.x * width + Math.sin(timestamp * orb.speed + orb.phase) * 80;
                const oy = orb.y * height + Math.cos(timestamp * orb.speed * 0.7 + orb.phase) * 60;
                const pulse = 0.8 + Math.sin(timestamp * 0.0008 + orb.phase) * 0.2;
                const r = orb.radius * pulse;

                const gradient = ctx.createRadialGradient(ox, oy, 0, ox, oy, r);
                if (dark) {
                    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.03)');  // emerald core
                    gradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.015)');
                    gradient.addColorStop(1, 'rgba(16, 185, 129, 0)');
                } else {
                    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.02)');
                    gradient.addColorStop(0.5, 'rgba(16, 185, 129, 0.008)');
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

        // Listen for theme changes
        const observer = new MutationObserver(() => {
            // Theme changed — next frame will pick it up
        });
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
