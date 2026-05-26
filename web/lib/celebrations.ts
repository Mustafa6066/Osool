/**
 * Celebrations & Micro-Interactions Library
 * ------------------------------------------
 * Professional, subtle animations for gamification events.
 * All celebrations are brief (300-800ms) — professional, not toy-like.
 */

// XP Float Animation (CSS class injection)
export function showXPToast(amount: number, element?: HTMLElement) {
    if (typeof window === 'undefined') return;
    const toast = document.createElement('div');
    toast.className = 'xp-float-toast';
    toast.textContent = `+${amount} XP`;

    // Position near the source element or center of viewport
    if (element) {
        const rect = element.getBoundingClientRect();
        toast.style.left = `${rect.left + rect.width / 2}px`;
        toast.style.top = `${rect.top}px`;
    } else {
        toast.style.right = '24px';
        toast.style.bottom = '100px';
    }

    document.body.appendChild(toast);

    // Animate and remove
    requestAnimationFrame(() => {
        toast.classList.add('xp-float-animate');
    });

    setTimeout(() => {
        toast.remove();
    }, 1500);
}

// Achievement Unlock Sound (subtle click)
export function playAchievementSound() {
    if (typeof window === 'undefined') return;
    try {
        const AudioContextConstructor = window.AudioContext || (window as Window & typeof globalThis & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!AudioContextConstructor) {
            return;
        }

        const audioContext = new AudioContextConstructor();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(880, audioContext.currentTime); // A5
        oscillator.frequency.setValueAtTime(1108, audioContext.currentTime + 0.1); // C#6
        oscillator.frequency.setValueAtTime(1318, audioContext.currentTime + 0.2); // E6

        gainNode.gain.setValueAtTime(0.05, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.4);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.4);
    } catch {
        // Audio not supported or blocked - silent fail
    }
}

// Level Up Particle Effect
export function triggerLevelUpEffect() {
    if (typeof window === 'undefined') return;
    const container = document.createElement('div');
    container.className = 'level-up-overlay';

    // Create particles
    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.className = 'level-up-particle';
        particle.style.setProperty('--x', `${Math.random() * 100}vw`);
        particle.style.setProperty('--delay', `${Math.random() * 0.3}s`);
        particle.style.setProperty('--size', `${4 + Math.random() * 8}px`);
        particle.style.setProperty('--hue', `${150 + Math.random() * 30}`); // Teal-green range
        container.appendChild(particle);
    }

    document.body.appendChild(container);

    setTimeout(() => {
        container.remove();
    }, 2000);
}

// Streak Fire Effect (emoji burst)
export function triggerStreakCelebration(days: number) {
    if (typeof window === 'undefined') return;
    const emojis = days >= 90 ? ['💎', '👑', '🔥'] : days >= 30 ? ['🔥', '⚡', '🎯'] : ['🔥', '✨'];
    const container = document.createElement('div');
    container.className = 'streak-burst';

    emojis.forEach((emoji, i) => {
        const el = document.createElement('span');
        el.textContent = emoji;
        el.className = 'streak-emoji';
        el.style.setProperty('--i', `${i}`);
        container.appendChild(el);
    });

    document.body.appendChild(container);
    setTimeout(() => container.remove(), 1500);
}
