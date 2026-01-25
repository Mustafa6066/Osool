'use client';

import anime from 'animejs';

/**
 * Osool Animation Utilities
 * Centralized anime.js utilities for smooth UI transitions
 */

// ============================================
// PAGE & COMPONENT TRANSITIONS
// ============================================

export const fadeIn = (target: string | HTMLElement, delay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [20, 0],
        easing: 'easeOutExpo',
        duration: 600,
        delay,
    });
};

export const slideInFromRight = (target: string | HTMLElement, delay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [50, 0],
        easing: 'easeOutExpo',
        duration: 600,
        delay,
    });
};

export const slideInFromLeft = (target: string | HTMLElement, delay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [-50, 0],
        easing: 'easeOutExpo',
        duration: 600,
        delay,
    });
};

export const staggerFadeIn = (target: string | HTMLElement[], startDelay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [20, 0],
        delay: anime.stagger(100, { start: startDelay }),
        easing: 'easeOutExpo',
        duration: 500,
    });
};

// ============================================
// CHART & VISUALIZATION ANIMATIONS
// ============================================

export const drawLine = (path: SVGPathElement, duration = 1500) => {
    const length = path.getTotalLength();
    path.style.strokeDasharray = `${length}`;
    path.style.strokeDashoffset = `${length}`;

    return anime({
        targets: path,
        strokeDashoffset: [length, 0],
        easing: 'easeOutExpo',
        duration,
    });
};

export const growBar = (target: string | HTMLElement, delay = 0) => {
    return anime({
        targets: target,
        scaleY: [0, 1],
        easing: 'easeOutExpo',
        duration: 800,
        delay,
    });
};

export const countUp = (
    target: HTMLElement,
    endValue: number,
    duration = 1500,
    suffix = ''
) => {
    return anime({
        targets: target,
        innerHTML: [0, endValue],
        round: 1,
        easing: 'easeOutExpo',
        duration,
        update: function () {
            if (suffix) {
                target.innerHTML = target.innerHTML + suffix;
            }
        }
    });
};

// ============================================
// PROPERTY CARD ANIMATIONS
// ============================================

export const cardEnter = (target: string | HTMLElement, index = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [-80, 0],
        scale: [0.9, 1],
        easing: 'spring(1, 80, 10, 0)',
        delay: 100 + (index * 150),
    });
};

export const cardHover = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        scale: 1.02,
        boxShadow: '0 20px 40px rgba(0, 0, 0, 0.15)',
        easing: 'easeOutExpo',
        duration: 300,
    });
};

export const cardUnhover = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        scale: 1,
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.03)',
        easing: 'easeOutExpo',
        duration: 300,
    });
};

// ============================================
// PANE & PANEL ANIMATIONS
// ============================================

export const panelSlideIn = (target: string | HTMLElement, from: 'left' | 'right' = 'right') => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [from === 'right' ? 100 : -100, 0],
        easing: 'easeOutExpo',
        duration: 500,
    });
};

export const sectionReveal = (target: string | HTMLElement[], delay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [30, 0],
        delay: anime.stagger(80, { start: delay }),
        easing: 'easeOutExpo',
        duration: 400,
    });
};

// ============================================
// TYPEWRITER EFFECT
// ============================================

export interface TypewriterConfig {
    text: string;
    element: HTMLElement;
    speed?: number;
    onComplete?: () => void;
}

export const typewriter = async ({
    text,
    element,
    speed = 20,
    onComplete
}: TypewriterConfig): Promise<void> => {
    element.textContent = '';

    for (let i = 0; i < text.length; i++) {
        element.textContent += text[i];
        await new Promise(resolve => setTimeout(resolve, speed));
    }

    onComplete?.();
};

// ============================================
// LOADING STATES
// ============================================

export const pulseLoader = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        opacity: [0.5, 1, 0.5],
        scale: [0.98, 1, 0.98],
        easing: 'easeInOutSine',
        duration: 1500,
        loop: true,
    });
};

export const spinLoader = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        rotate: 360,
        easing: 'linear',
        duration: 2000,
        loop: true,
    });
};

// ============================================
// ANALYTICS & INSIGHT ANIMATIONS
// ============================================

export const insightReveal = (target: string | HTMLElement, delay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [20, 0],
        scale: [0.95, 1],
        easing: 'easeOutExpo',
        duration: 600,
        delay,
    });
};

export const chartPointPop = (target: string | HTMLElement[], delay = 0) => {
    return anime({
        targets: target,
        scale: [0, 1],
        opacity: [0, 1],
        delay: anime.stagger(50, { start: delay }),
        easing: 'easeOutBack',
        duration: 400,
    });
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

export const stopAnimation = (animation: anime.AnimeInstance) => {
    animation.pause();
};

export const cleanupAnimations = () => {
    anime.remove('*');
};
