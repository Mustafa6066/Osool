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
        <div className="min-h-screen bg-[#f9fafa] dark:bg-[#121416] text-[#111418] dark:text-[#DCE0E2] font-body selection:bg-[#267360] selection:text-white">
            {/* Top Navigation */}
            <header className="sticky top-0 z-50 w-full border-b border-[#2c3533] bg-[#121416]/80 backdrop-blur-md">
                <div className="max-w-[1400px] mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/" className="size-8 text-[#267360]">
                            <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                                <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor"></path>
                            </svg>
                        </Link>
                        <h2 className="text-white text-xl font-bold tracking-tight font-display">AMR Dashboard</h2>
                    </div>
                    <nav className="hidden md:flex items-center gap-8">
                        <Link href="/chat" className="text-[#9CA3AF] hover:text-white text-sm font-medium transition-colors">Chat with AMR</Link>
                        <Link href="/dashboard" className="text-white text-sm font-medium transition-colors border-b-2 border-[#267360] pb-5 mt-5">Referrals</Link>
                        <Link href="/market" className="text-[#9CA3AF] hover:text-white text-sm font-medium transition-colors">Market Insights</Link>
                    </nav>
                    <div className="flex items-center gap-4">
                        <div className="h-8 w-[1px] bg-[#323639]"></div>
                        <div className="flex items-center gap-3 pl-2 cursor-pointer group">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-medium text-white leading-none">
                                    {(() => {
                                        const email = user?.email?.toLowerCase();
                                        if (email === 'mustafa@osool.eg') return 'Mustafa';
                                        if (email === 'hani@osool.eg') return 'Hani';
                                        if (email === 'abady@osool.eg') return 'Abady';
                                        if (email === 'sama@osool.eg') return 'Mrs. Mustafa';
                                        return user?.full_name || 'User';
                                    })()}
                                </p>
                                <p className="text-xs text-[#8D764D] mt-1 leading-none">{isUnlimited ? 'VIP Agent' : 'Member'}</p>
                            </div>
                            <div className="size-9 rounded-full bg-[#267360] flex items-center justify-center text-white font-bold ring-2 ring-[#323639] group-hover:ring-[#267360] transition-all">
                                {user?.full_name?.[0] || user?.email?.[0] || 'U'}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 w-full max-w-[1400px] mx-auto px-6 py-8">
                {/* Page Header */}
                <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-800 dark:text-white mb-2 font-display">Referral Hub</h1>
                        <p className="text-slate-500 dark:text-[#9CA3AF] text-lg font-light max-w-xl">Manage your exclusive network invitations and track your referral impact.</p>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-[#9CA3AF] bg-white dark:bg-[#26292B] px-3 py-1.5 rounded-full border border-slate-200 dark:border-[#323639]/50 shadow-sm">
                        <span className="size-2 rounded-full bg-green-500 animate-pulse"></span>
                        System Operational
                    </div>
                </div>

                {/* Bento Grid Layout */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-8">
                    {/* Hero Status Card (Spans 8 cols) */}
                    <div className="md:col-span-8 bg-white dark:bg-[#26292B] rounded-xl p-0 relative overflow-hidden shadow-card group border border-slate-200 dark:border-[#323639]/30">
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
                                    <h2 className="text-3xl font-display font-bold text-slate-900 dark:text-white mb-2">
                                        {isUnlimited ? 'Unlimited Invitation Links' : `${invitationsData?.invitations_remaining} Invitations Remaining`}
                                    </h2>
                                    <p className="text-slate-500 dark:text-[#9CA3AF] max-w-md">
                                        {isUnlimited
                                            ? 'As a top-tier partner, you have uncapped potential to grow your network. Share the power of AMR without restrictions.'
                                            : 'Invite friends to verify properties. Each link is single-use and exclusive.'}
                                    </p>
                                </div>
                                <div className="hidden lg:flex size-24 rounded-full bg-gradient-to-br from-[#267360] to-[#121416] border-4 border-white dark:border-[#26292B] shadow-2xl items-center justify-center">
                                    <Users className="text-white text-4xl" />
                                </div>
                            </div>
                            <div className="mt-8 flex gap-4">
                                <Link href="/chat" className="px-5 py-2.5 rounded-lg bg-[#26292B] dark:bg-[#121416] text-white text-sm font-bold border border-slate-200 dark:border-[#323639] hover:border-[#267360] transition-colors">
                                    Go to Chat Agent
                                </Link>
                            </div>
                        </div>
                    </div>

                    {/* Stats Column (Spans 4 cols) */}
                    <div className="md:col-span-4 grid grid-cols-2 gap-4 h-full">
                        <div className="col-span-2 bg-white dark:bg-[#26292B] rounded-xl p-6 border border-slate-200 dark:border-[#323639]/30 shadow-card flex items-center justify-between">
                            <div>
                                <p className="text-slate-500 dark:text-[#9CA3AF] text-sm font-medium mb-1">Total Generated</p>
                                <p className="text-slate-900 dark:text-white text-3xl font-display font-bold">{totalInvites}</p>
                            </div>
                            <div className="p-3 bg-[#267360]/10 rounded-lg text-[#267360]">
                                <Gift />
                            </div>
                        </div>
                        <div className="bg-white dark:bg-[#26292B] rounded-xl p-6 border border-slate-200 dark:border-[#323639]/30 shadow-card flex flex-col justify-between">
                            <div className="p-2 w-fit bg-[#8D764D]/10 rounded-lg text-[#8D764D] mb-3">
                                <UserCheck size={20} />
                            </div>
                            <div>
                                <p className="text-slate-900 dark:text-white text-2xl font-display font-bold">{usedCount}</p>
                                <p className="text-slate-500 dark:text-[#9CA3AF] text-xs font-medium">Joined Users</p>
                            </div>
                        </div>
                        <div className="bg-white dark:bg-[#26292B] rounded-xl p-6 border border-slate-200 dark:border-[#323639]/30 shadow-card flex flex-col justify-between">
                            <div className="p-2 w-fit bg-slate-100 dark:bg-[#323639] rounded-lg text-slate-500 dark:text-[#DCE0E2] mb-3">
                                <Clock size={20} />
                            </div>
                            <div>
                                <p className="text-[#8D764D] text-2xl font-display font-bold">{pendingCount}</p>
                                <p className="text-slate-500 dark:text-[#9CA3AF] text-xs font-medium">Pending</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action & Table Section */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Generate Link Action (Left Column) */}
                    <div className="lg:col-span-1">
                        <div className="sticky top-24">
                            <div className="bg-white dark:bg-[#26292B] rounded-xl p-6 border border-slate-200 dark:border-[#323639]/30 shadow-card">
                                <h3 className="text-xl text-slate-900 dark:text-white font-bold mb-6 flex items-center gap-2">
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
                                                    className="flex items-center gap-2 bg-white dark:bg-[#121416] p-3 rounded-lg border border-green-200 dark:border-green-800 cursor-pointer hover:border-[#267360] transition-colors"
                                                >
                                                    <div className="flex-1 truncate font-mono text-xs text-slate-600 dark:text-slate-300">
                                                        {generatedInvite.invitation_link}
                                                    </div>
                                                    <span className="text-[#9CA3AF]">
                                                        {copySuccess === 'new' ? <Check size={16} className="text-green-500" /> : <Copy size={16} />}
                                                    </span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => setGeneratedInvite(null)}
                                                className="w-full bg-slate-100 dark:bg-[#323639] hover:bg-slate-200 dark:hover:bg-[#323639]/80 text-slate-700 dark:text-white font-medium py-3 px-4 rounded-lg transition-all"
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
                                <p className="text-sm text-[#9CA3AF] leading-relaxed">
                                    <span className="text-[#8D764D] font-bold">Pro Tip:</span> {' '}
                                    Trusted invites help build the community. Verify your referrals personally.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Table Section (Right 2 Columns) */}
                    <div className="lg:col-span-2">
                        <div className="bg-white dark:bg-[#26292B] rounded-xl border border-slate-200 dark:border-[#323639]/30 shadow-card overflow-hidden flex flex-col min-h-[500px]">
                            <div className="p-6 border-b border-slate-200 dark:border-[#323639] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                                <h3 className="text-xl text-slate-900 dark:text-white font-bold">Invitation History</h3>
                                <div className="flex items-center gap-2">
                                    <div className="relative">
                                        <Search className="absolute left-2.5 top-2.5 text-[#9CA3AF]" size={18} />
                                        <input
                                            type="text"
                                            placeholder="Search code..."
                                            className="bg-slate-50 dark:bg-[#121416] border border-slate-200 dark:border-[#323639] rounded-lg pl-9 pr-3 py-2 text-sm text-slate-900 dark:text-white placeholder-[#9CA3AF] focus:ring-1 focus:ring-[#267360] focus:border-[#267360] outline-none w-full sm:w-64"
                                        />
                                    </div>
                                    <button className="p-2 border border-slate-200 dark:border-[#323639] rounded-lg text-[#9CA3AF] hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-[#323639] transition-colors">
                                        <Filter size={20} />
                                    </button>
                                </div>
                            </div>

                            <div className="overflow-x-auto flex-1">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-slate-200 dark:border-[#323639] bg-slate-50 dark:bg-[#323639]/30">
                                            <th className="p-4 text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">Status</th>
                                            <th className="p-4 text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">Link Code</th>
                                            <th className="p-4 text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">Date Created</th>
                                            <th className="p-4 text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider">Date Used</th>
                                            <th className="p-4 text-xs font-semibold text-[#9CA3AF] uppercase tracking-wider text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-[#323639]/50">
                                        {isLoading ? (
                                            <tr>
                                                <td colSpan={5} className="p-8 text-center text-[#9CA3AF]">Loading invitations...</td>
                                            </tr>
                                        ) : invitationsData?.invitations.length === 0 ? (
                                            <tr>
                                                <td colSpan={5} className="p-8 text-center text-[#9CA3AF]">
                                                    No invitations generated yet. Create your first one!
                                                </td>
                                            </tr>
                                        ) : (
                                            invitationsData?.invitations.map((invite, idx) => (
                                                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-[#323639]/20 transition-colors group">
                                                    <td className="p-4">
                                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${invite.is_used
                                                                ? 'bg-[#267360]/20 text-[#267360] border-[#267360]/20'
                                                                : 'bg-[#8D764D]/10 text-[#8D764D] border-[#8D764D]/20'
                                                            }`}>
                                                            <span className={`size-1.5 rounded-full ${invite.is_used ? 'bg-[#267360]' : 'bg-[#8D764D]'}`}></span>
                                                            {invite.is_used ? 'Used' : 'Pending'}
                                                        </span>
                                                    </td>
                                                    <td className="p-4 text-sm font-mono text-[#9CA3AF]">{invite.code}</td>
                                                    <td className="p-4 text-sm text-[#9CA3AF]">{formatDate(invite.created_at)}</td>
                                                    <td className="p-4 text-sm text-[#9CA3AF]">{formatDate(invite.used_at)}</td>
                                                    <td className="p-4 text-right">
                                                        <button
                                                            onClick={() => handleCopy(`${window.location.origin}/signup?invite=${invite.code}`, invite.code)}
                                                            className="text-[#9CA3AF] hover:text-slate-900 dark:hover:text-white transition-colors p-2 rounded hover:bg-slate-100 dark:hover:bg-[#323639]"
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
            </main>
        </div>
    );
}
