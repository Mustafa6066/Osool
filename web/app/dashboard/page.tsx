'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    Gift,
    Copy,
    Check,
    Loader2,
    Users,
    Clock,
    UserCheck,
    Search,
    Filter,
    MoreHorizontal,
    Plus,
    X,
    ShieldCheck,
    AlertCircle
} from 'lucide-react';
import { generateInvitation, getMyInvitations, MyInvitationsResponse, getCurrentUserFromToken, InvitationResponse } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';

export default function DashboardPage() {
    const { user, isAuthenticated, loading } = useAuth();
    const router = useRouter();
    const [invitationsData, setInvitationsData] = useState<MyInvitationsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedInvite, setGeneratedInvite] = useState<InvitationResponse | null>(null);
    const [copySuccess, setCopySuccess] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Redirect if not authenticated
    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, loading, router]);

    // Fetch data
    useEffect(() => {
        if (isAuthenticated) {
            fetchInvitations();
        }
    }, [isAuthenticated]);

    const fetchInvitations = async () => {
        try {
            const data = await getMyInvitations();
            setInvitationsData(data);
        } catch (err) {
            console.error('Failed to fetch invitations:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);
        try {
            const data = await generateInvitation();
            setGeneratedInvite(data);
            await fetchInvitations(); // Refresh list
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to generate invitation');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCopy = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopySuccess(id);
        setTimeout(() => setCopySuccess(null), 2000);
    };

    const formatDate = (dateString: string | null) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    };

    if (loading || !isAuthenticated) {
        return (
            <div className="min-h-screen bg-[#121416] flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            </div>
        );
    }

    const usedCount = invitationsData?.invitations.filter(i => i.is_used).length || 0;
    const pendingCount = invitationsData?.invitations.filter(i => !i.is_used).length || 0;
    const totalInvites = invitationsData?.total_invitations || 0;
    const isUnlimited = invitationsData?.invitations_remaining === 'unlimited';

    return (
        <div className="flex h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] font-sans overflow-hidden">
            {/* Sidebar */}
            <Sidebar activePage="dashboard" />

            {/* Main Content */}
            <main className="flex-1 flex flex-col h-full overflow-hidden relative">
                <div className="flex-1 overflow-y-auto p-6 md:p-12 scrollbar-hide">
                    <div className="max-w-[1400px] mx-auto space-y-8">
                        {/* Page Header */}
                        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
                            <div>
                                <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-[var(--color-text-primary)] mb-2 font-display">Referral Hub</h1>
                                <p className="text-[var(--color-text-muted)] text-lg font-light max-w-xl">Manage your exclusive network invitations and track your referral impact.</p>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)] bg-[var(--color-surface)] px-3 py-1.5 rounded-full border border-[var(--color-border)] shadow-sm">
                                <span className="size-2 rounded-full bg-green-500 animate-pulse"></span>
                                System Operational
                            </div>
                        </div>

                        {/* Bento Grid Layout */}
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-8">
                            {/* Hero Status Card (Spans 8 cols) */}
                            <div className="md:col-span-8 bg-[var(--color-surface)] rounded-xl p-0 relative overflow-hidden shadow-card group border border-[var(--color-border)]">
                                <div className="absolute inset-0 bg-gradient-to-br from-[#323639]/5 to-transparent z-0"></div>
                                {/* Abstract Pattern */}
                                <div className="absolute right-0 top-0 h-full w-1/2 opacity-10 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#267360 1px, transparent 1px)', backgroundSize: '24px 24px' }}></div>

                                <div className="relative z-10 p-8 h-full flex flex-col justify-between">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-bold uppercase tracking-wider mb-4 
                                        ${isUnlimited
                                                    ? 'bg-[#8D764D]/10 border-[#8D764D]/20 text-[#8D764D]'
                                                    : 'bg-blue-500/10 border-blue-500/20 text-blue-500'}`}>
                                                <ShieldCheck size={14} />
                                                {isUnlimited ? 'VIP Access' : 'Standard Access'}
                                            </div>
                                            <h2 className="text-3xl font-display font-bold text-[var(--color-text-primary)] mb-2">
                                                {isUnlimited ? 'Unlimited Invitation Links' : `${invitationsData?.invitations_remaining} Invitations Remaining`}
                                            </h2>
                                            <p className="text-[var(--color-text-muted)] max-w-md">
                                                {isUnlimited
                                                    ? 'As a top-tier partner, you have uncapped potential to grow your network. Share the power of AMR without restrictions.'
                                                    : 'Invite friends to verify properties. Each link is single-use and exclusive.'}
                                            </p>
                                        </div>
                                        <div className="hidden lg:flex size-24 rounded-full bg-gradient-to-br from-[#267360] to-[#121416] border-4 border-[var(--color-surface)] shadow-2xl items-center justify-center">
                                            <Users className="text-white text-4xl" />
                                        </div>
                                    </div>
                                    <div className="mt-8 flex gap-4">
                                        <Link href="/chat" className="px-5 py-2.5 rounded-lg bg-[var(--color-surface-elevated)] text-white text-sm font-bold border border-[var(--color-border)] hover:border-[#267360] transition-colors">
                                            Go to Chat Agent
                                        </Link>
                                    </div>
                                </div>
                            </div>

                            {/* Stats Column (Spans 4 cols) */}
                            <div className="md:col-span-4 grid grid-cols-2 gap-4 h-full">
                                <div className="col-span-2 bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)] shadow-card flex items-center justify-between">
                                    <div>
                                        <p className="text-[var(--color-text-muted)] text-sm font-medium mb-1">Total Generated</p>
                                        <p className="text-[var(--color-text-primary)] text-3xl font-display font-bold">{totalInvites}</p>
                                    </div>
                                    <div className="p-3 bg-[#267360]/10 rounded-lg text-[#267360]">
                                        <Gift />
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)] shadow-card flex flex-col justify-between">
                                    <div className="p-2 w-fit bg-[#8D764D]/10 rounded-lg text-[#8D764D] mb-3">
                                        <UserCheck size={20} />
                                    </div>
                                    <div>
                                        <p className="text-[var(--color-text-primary)] text-2xl font-display font-bold">{usedCount}</p>
                                        <p className="text-[var(--color-text-muted)] text-xs font-medium">Joined Users</p>
                                    </div>
                                </div>
                                <div className="bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)] shadow-card flex flex-col justify-between">
                                    <div className="p-2 w-fit bg-[var(--color-surface-elevated)] rounded-lg text-[var(--color-text-muted)] mb-3">
                                        <Clock size={20} />
                                    </div>
                                    <div>
                                        <p className="text-[#8D764D] text-2xl font-display font-bold">{pendingCount}</p>
                                        <p className="text-[var(--color-text-muted)] text-xs font-medium">Pending</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Action & Table Section */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Generate Link Action (Left Column) */}
                            <div className="lg:col-span-1">
                                <div className="sticky top-24">
                                    <div className="bg-[var(--color-surface)] rounded-xl p-6 border border-[var(--color-border)] shadow-card">
                                        <h3 className="text-xl text-[var(--color-text-primary)] font-bold mb-6 flex items-center gap-2">
                                            <span className="p-1.5 bg-[#267360]/10 rounded-lg text-[#267360]"><Plus size={18} /></span>
                                            Create Invite
                                        </h3>

                                        {error && (
                                            <div className="p-3 mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                                                <AlertCircle size={16} />
                                                <span>{error}</span>
                                            </div>
                                        )}

                                        <div className="space-y-5">
                                            {generatedInvite ? (
                                                <div className="animate-in fade-in zoom-in-95">
                                                    <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg mb-4">
                                                        <p className="text-sm font-medium text-green-700 dark:text-green-400 mb-2 flex items-center gap-2">
                                                            <Check size={16} /> Generated Successfully
                                                        </p>
                                                        <div
                                                            onClick={() => handleCopy(generatedInvite.invitation_link, 'new')}
                                                            className="flex items-center gap-2 bg-[var(--color-surface-elevated)] p-3 rounded-lg border border-green-200 dark:border-green-800 cursor-pointer hover:border-[#267360] transition-colors"
                                                        >
                                                            <div className="flex-1 truncate font-mono text-xs text-[var(--color-text-muted)]">
                                                                {generatedInvite.invitation_link}
                                                            </div>
                                                            <span className="text-[var(--color-text-muted)]">
                                                                {copySuccess === 'new' ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <button
                                                        onClick={() => setGeneratedInvite(null)}
                                                        className="w-full bg-[var(--color-surface-elevated)] hover:bg-[var(--color-surface)] text-[var(--color-text-primary)] font-medium py-3 px-4 rounded-lg transition-all"
                                                    >
                                                        Generate Another
                                                    </button>
                                                </div>
                                            ) : (
                                                <button
                                                    onClick={handleGenerate}
                                                    disabled={isGenerating || (!isUnlimited && invitationsData?.invitations_remaining === 0)}
                                                    className="w-full bg-[#267360] hover:bg-[#1e5b4c] text-white font-medium py-3.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_-5px_rgba(38,115,96,0.3)] disabled:opacity-50 disabled:cursor-not-allowed group"
                                                >
                                                    {isGenerating ? <Loader2 size={20} className="animate-spin" /> : (
                                                        <>
                                                            <Users size={20} />
                                                            Generate New Link
                                                        </>
                                                    )}
                                                </button>
                                            )}

                                            {!isUnlimited && invitationsData?.invitations_remaining === 0 && !generatedInvite && (
                                                <p className="text-xs text-center text-amber-600 dark:text-amber-400">
                                                    Limit reached. Contact admin for more.
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Quick Tip */}
                                    <div className="mt-6 bg-[#8D764D]/5 border border-[#8D764D]/10 rounded-xl p-4 flex gap-3">
                                        <span className="p-1 bg-[#8D764D]/10 rounded text-[#8D764D] h-fit"><Users size={16} /></span>
                                        <p className="text-sm text-[var(--color-text-muted)] leading-relaxed">
                                            <span className="text-[#8D764D] font-bold">Pro Tip:</span> {' '}
                                            Trusted invites help build the community. Verify your referrals personally.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Table Section (Right 2 Columns) */}
                            <div className="lg:col-span-2">
                                <div className="bg-[var(--color-surface)] rounded-xl border border-[var(--color-border)] shadow-card overflow-hidden flex flex-col min-h-[500px]">
                                    <div className="p-6 border-b border-[var(--color-border)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                        <h3 className="text-xl text-[var(--color-text-primary)] font-bold">Invitation History</h3>
                                        <div className="flex items-center gap-2">
                                            <div className="relative">
                                                <Search className="absolute left-2.5 top-2.5 text-[var(--color-text-muted)]" size={18} />
                                                <input
                                                    type="text"
                                                    placeholder="Search code..."
                                                    className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-lg pl-9 pr-3 py-2 text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-1 focus:ring-[#267360] focus:border-[#267360] outline-none w-full sm:w-64"
                                                />
                                            </div>
                                            <button className="p-2 border border-[var(--color-border)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors">
                                                <Filter size={20} />
                                            </button>
                                        </div>
                                    </div>

                                    <div className="overflow-x-auto flex-1">
                                        <table className="w-full text-left border-collapse">
                                            <thead>
                                                <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface-elevated)]">
                                                    <th className="p-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Status</th>
                                                    <th className="p-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Link Code</th>
                                                    <th className="p-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Date Created</th>
                                                    <th className="p-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Date Used</th>
                                                    <th className="p-4 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider text-right">Actions</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-[var(--color-border)]">
                                                {isLoading ? (
                                                    <tr>
                                                        <td colSpan={5} className="p-8 text-center text-[var(--color-text-muted)]">Loading invitations...</td>
                                                    </tr>
                                                ) : invitationsData?.invitations.length === 0 ? (
                                                    <tr>
                                                        <td colSpan={5} className="p-8 text-center text-[var(--color-text-muted)]">
                                                            No invitations generated yet. Create your first one!
                                                        </td>
                                                    </tr>
                                                ) : (
                                                    invitationsData?.invitations.map((invite, idx) => (
                                                        <tr key={idx} className="hover:bg-[var(--color-surface-elevated)] transition-colors group">
                                                            <td className="p-4">
                                                                <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${invite.is_used
                                                                    ? 'bg-[#267360]/20 text-[#267360] border-[#267360]/20'
                                                                    : 'bg-[#8D764D]/10 text-[#8D764D] border-[#8D764D]/20'
                                                                    }`}>
                                                                    <span className={`size-1.5 rounded-full ${invite.is_used ? 'bg-[#267360]' : 'bg-[#8D764D]'}`}></span>
                                                                    {invite.is_used ? 'Used' : 'Pending'}
                                                                </span>
                                                            </td>
                                                            <td className="p-4 text-sm font-mono text-[var(--color-text-muted)]">{invite.code}</td>
                                                            <td className="p-4 text-sm text-[var(--color-text-muted)]">{formatDate(invite.created_at)}</td>
                                                            <td className="p-4 text-sm text-[var(--color-text-muted)]">{formatDate(invite.used_at)}</td>
                                                            <td className="p-4 text-right">
                                                                <button
                                                                    onClick={() => handleCopy(`${window.location.origin}/signup?invite=${invite.code}`, invite.code)}
                                                                    className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors p-2 rounded hover:bg-[var(--color-surface-elevated)]"
                                                                    title="Copy Link"
                                                                >
                                                                    {copySuccess === invite.code ? <Check size={18} className="text-green-500" /> : <Copy size={18} />}
                                                                </button>
                                                            </td>
                                                        </tr>
                                                    ))
                                                )}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
