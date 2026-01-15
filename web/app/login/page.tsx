"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import AuthModal from '@/components/AuthModal';

export default function LoginPage() {
    const router = useRouter();

    const handleSuccess = () => {
        // Redirect to Chat with AMR
        router.push('/ai-advisor');
    };

    const handleClose = () => {
        // If they close the modal, go home because this IS the login page
        router.push('/');
    };

    return (
        <div className="relative min-h-screen w-full bg-slate-900">
            {/* Background with Cairo/Modern Aesthetic */}
            <div
                className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1663435860738-f9b699c647b0?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center opacity-50"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent" />

            {/* 
        We use the AuthModal in "Always Open" mode.
        The modal's internal backdrop will overlay our page background, 
        creating a focus effect.
      */}
            <AuthModal
                isOpen={true}
                onClose={handleClose}
                onSuccess={handleSuccess}
            />

            {/* Branding / Footer if needed behind modal (will be covered by modal backdrop though) */}
            <div className="absolute bottom-10 left-0 right-0 text-center text-white/40 text-sm z-0">
                &copy; 2026 Osool Real Estate. Powered by AI.
            </div>
        </div>
    );
}
