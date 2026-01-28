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
// CHAT INPUT TRANSITIONS
// ============================================

/**
 * Animate welcome section fade out when first message is sent
 */
export const welcomeFadeOut = (target: string | HTMLElement, onComplete?: () => void) => {
    return anime({
        targets: target,
        opacity: [1, 0],
        translateY: [0, -30],
        scale: [1, 0.98],
        easing: 'easeOutExpo',
        duration: 400,
        complete: onComplete,
    });
};

/**
 * Animate input container from centered position to bottom
 */
export const inputSlideToBottom = (target: string | HTMLElement, onComplete?: () => void) => {
    return anime({
        targets: target,
        opacity: [1, 1],
        easing: 'easeOutExpo',
        duration: 500,
        complete: onComplete,
    });
};

/**
 * Combined animation for transitioning from empty state to chat state
 * Fades out welcome, then slides input to bottom
 */
export const emptyChatToActiveTransition = (
    welcomeTarget: HTMLElement | null,
    inputTarget: HTMLElement | null,
    onComplete?: () => void
) => {
    const timeline = anime.timeline({
        easing: 'easeOutExpo',
        complete: onComplete,
    });

    // Fade out welcome section
    if (welcomeTarget) {
        timeline.add({
            targets: welcomeTarget,
            opacity: [1, 0],
            translateY: [0, -40],
            scale: [1, 0.95],
            duration: 350,
        });
    }

    // Input transition happens via CSS class change after welcome fades
    if (inputTarget) {
        timeline.add({
            targets: inputTarget,
            opacity: [0.8, 1],
            duration: 200,
        }, '-=100');
    }

    return timeline;
};

// ============================================
// CONTEXTUAL PANE ANIMATIONS
// ============================================

/**
 * Animate contextual pane content update
 */
export const contextualPaneUpdate = (target: string | HTMLElement, delay = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [20, 0],
        easing: 'easeOutExpo',
        duration: 400,
        delay,
    });
};

/**
 * Staggered animation for contextual pane items
 */
export const contextualItemsStagger = (targets: string | HTMLElement[], delay = 0) => {
    return anime({
        targets,
        opacity: [0, 1],
        translateY: [15, 0],
        delay: anime.stagger(80, { start: delay }),
        easing: 'easeOutExpo',
        duration: 350,
    });
};

/**
 * Visualization card entrance animation
 */
export const visualizationEnter = (target: string | HTMLElement, index = 0) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [30, 0],
        scale: [0.95, 1],
        easing: 'easeOutExpo',
        duration: 500,
        delay: 100 + (index * 100),
    });
};

/**
 * Staggered visualization cards entrance
 */
export const visualizationsStaggerEnter = (targets: string | HTMLElement[]) => {
    return anime({
        targets,
        opacity: [0, 1],
        translateY: [40, 0],
        scale: [0.9, 1],
        delay: anime.stagger(150, { start: 200 }),
        easing: 'spring(1, 80, 10, 0)',
    });
};

// ============================================
// MESSAGE ANIMATIONS
// ============================================

/**
 * User message slide in from right
 */
export const userMessageEnter = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [30, 0],
        easing: 'easeOutExpo',
        duration: 400,
    });
};

/**
 * AI message slide in from left
 */
export const aiMessageEnter = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: [-30, 0],
        easing: 'easeOutExpo',
        duration: 400,
    });
};

/**
 * Property card entrance with spring effect
 */
export const propertyCardEnter = (target: string | HTMLElement) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [50, 0],
        scale: [0.9, 1],
        easing: 'spring(1, 80, 10, 0)',
        duration: 800,
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

// ============================================
// CHAT ENHANCED ANIMATIONS
// ============================================

/**
 * Welcome screen entrance with staggered elements
 */
export const welcomeScreenEnter = (container: HTMLElement) => {
    const avatar = container.querySelector('.welcome-avatar');
    const title = container.querySelector('.welcome-title');
    const subtitle = container.querySelector('.welcome-subtitle');
    const suggestions = container.querySelectorAll('.welcome-suggestion');
    const input = container.querySelector('.welcome-input');

    const tl = anime.timeline({
        easing: 'easeOutExpo',
    });

    if (avatar) {
        tl.add({
            targets: avatar,
            opacity: [0, 1],
            scale: [0.5, 1],
            duration: 600,
        });
    }

    if (title) {
        tl.add({
            targets: title,
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 500,
        }, '-=300');
    }

    if (subtitle) {
        tl.add({
            targets: subtitle,
            opacity: [0, 1],
            translateY: [15, 0],
            duration: 400,
        }, '-=200');
    }

    if (suggestions.length > 0) {
        tl.add({
            targets: suggestions,
            opacity: [0, 1],
            translateY: [30, 0],
            scale: [0.9, 1],
            delay: anime.stagger(100),
            duration: 500,
        }, '-=200');
    }

    if (input) {
        tl.add({
            targets: input,
            opacity: [0, 1],
            translateY: [20, 0],
            duration: 400,
        }, '-=300');
    }

    return tl;
};

/**
 * Input focus glow pulse animation
 */
export const inputGlowPulse = (target: HTMLElement) => {
    return anime({
        targets: target,
        boxShadow: [
            '0 0 0 0 rgba(18, 71, 89, 0)',
            '0 0 20px 4px rgba(18, 71, 89, 0.15)',
            '0 0 0 0 rgba(18, 71, 89, 0)'
        ],
        easing: 'easeInOutSine',
        duration: 2000,
        loop: true,
    });
};

/**
 * Send button press animation
 */
export const sendButtonPress = (target: HTMLElement) => {
    return anime({
        targets: target,
        scale: [1, 0.85, 1.1, 1],
        rotate: [0, -5, 5, 0],
        duration: 400,
        easing: 'easeOutElastic(1, .5)',
    });
};

/**
 * Message bubble pop-in animation
 */
export const messageBubbleEnter = (target: HTMLElement, isUser: boolean) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateX: isUser ? [40, 0] : [-40, 0],
        translateY: [10, 0],
        scale: [0.9, 1],
        easing: 'spring(1, 80, 10, 0)',
        duration: 600,
    });
};

/**
 * Typing indicator dots animation
 */
export const typingDotsAnimate = (dots: NodeListOf<HTMLElement> | HTMLElement[]) => {
    return anime({
        targets: dots,
        translateY: [-3, 0, -3],
        opacity: [0.4, 1, 0.4],
        delay: anime.stagger(150),
        duration: 600,
        loop: true,
        easing: 'easeInOutSine',
    });
};

/**
 * Scroll indicator bounce animation
 */
export const scrollIndicatorBounce = (target: HTMLElement) => {
    return anime({
        targets: target,
        translateY: [0, 8, 0],
        opacity: [0.5, 1, 0.5],
        duration: 1500,
        loop: true,
        easing: 'easeInOutSine',
    });
};

/**
 * Suggestion card hover effect
 */
export const suggestionCardHover = (target: HTMLElement) => {
    return anime({
        targets: target,
        scale: 1.05,
        translateY: -5,
        boxShadow: '0 15px 35px rgba(18, 71, 89, 0.15)',
        duration: 300,
        easing: 'easeOutExpo',
    });
};

/**
 * Suggestion card unhover effect
 */
export const suggestionCardUnhover = (target: HTMLElement) => {
    return anime({
        targets: target,
        scale: 1,
        translateY: 0,
        boxShadow: '0 4px 15px rgba(0, 0, 0, 0.05)',
        duration: 300,
        easing: 'easeOutExpo',
    });
};

/**
 * AI thinking shimmer effect
 */
export const thinkingShimmer = (target: HTMLElement) => {
    return anime({
        targets: target,
        backgroundPosition: ['200% 0', '-200% 0'],
        duration: 2000,
        loop: true,
        easing: 'linear',
    });
};

/**
 * Quick action buttons stagger entrance
 */
export const quickActionsEnter = (targets: NodeListOf<HTMLElement> | HTMLElement[]) => {
    return anime({
        targets,
        opacity: [0, 1],
        scale: [0.8, 1],
        translateY: [15, 0],
        delay: anime.stagger(80),
        duration: 400,
        easing: 'easeOutBack',
    });
};

/**
 * Chat header slide down animation
 */
export const headerSlideDown = (target: HTMLElement) => {
    return anime({
        targets: target,
        opacity: [0, 1],
        translateY: [-20, 0],
        duration: 500,
        easing: 'easeOutExpo',
    });
};

/**
 * New message notification pop
 */
export const notificationPop = (target: HTMLElement) => {
    return anime({
        targets: target,
        scale: [0, 1.2, 1],
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutBack',
    });
};
