"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

/**
 * ProtectedRoute Component
 * --------------------------
 * Wraps protected pages to ensure only authenticated users can access them.
 * Redirects to /login if user is not authenticated.
 */
export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        // Only redirect after loading is complete and user is not authenticated
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    // Show loading spinner while checking auth status
    if (loading) {
        return (
            <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
                    <p className="text-[var(--color-text-muted)] text-sm">Checking authentication...</p>
                </div>
            </div>
        );
    }

    // If not authenticated, show nothing (will redirect)
    if (!isAuthenticated) {
        return (
            <div className="min-h-screen bg-[var(--color-background)] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
                    <p className="text-[var(--color-text-muted)] text-sm">Redirecting to login...</p>
                </div>
            </div>
        );
    }

    // User is authenticated, render children
    return <>{children}</>;
}
