'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield, Users, MessageSquare, Building2, TrendingUp,
    Loader2, ChevronRight, Search, RefreshCw, Eye,
    Activity, Clock, ArrowLeft, Bot, User as UserIcon,
    Database, Zap, AlertCircle, Ticket as TicketIcon, Send
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import SmartNav from '@/components/SmartNav';
import {
    checkAdmin,
    getAdminDashboard,
    getAdminUsers,
    getAdminConversations,
    getAdminConversation,
    triggerPropertyScraper,
    triggerEconomicScraper,
    getAdminMarketIndicators,
    updateUserRole,
    blockUser,
    getAdminTickets,
    getAdminTicketDetail,
    getTicketStats,
    updateTicketStatus,
    addAdminTicketReply,
    AdminDashboardData,
    AdminUser,
    AdminConversation,
    AdminMessage,
    AdminTicket,
    AdminTicketDetail,
    TicketStats,
} from '@/lib/api';

type Tab = 'overview' | 'conversations' | 'users' | 'scrapers' | 'tickets';

export default function AdminPage() {
    const { user, isAuthenticated, loading: authLoading } = useAuth();
    const router = useRouter();

    const [isAdmin, setIsAdmin] = useState(false);
    const [checking, setChecking] = useState(true);
    const [activeTab, setActiveTab] = useState<Tab>('overview');

    // Data states
    const [dashboard, setDashboard] = useState<AdminDashboardData | null>(null);
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [conversations, setConversations] = useState<AdminConversation[]>([]);
    const [selectedConversation, setSelectedConversation] = useState<{
        session_id: string;
        user: { id: number; email: string; full_name: string; role: string } | null;
        messages: AdminMessage[];
    } | null>(null);
    const [indicators, setIndicators] = useState<any[]>([]);

    // Ticket states
    const [adminTickets, setAdminTickets] = useState<AdminTicket[]>([]);
    const [ticketStats, setTicketStats] = useState<TicketStats | null>(null);
    const [selectedTicket, setSelectedTicket] = useState<AdminTicketDetail | null>(null);
    const [ticketStatusFilter, setTicketStatusFilter] = useState<string>('');
    const [ticketReplyContent, setTicketReplyContent] = useState('');
    const [ticketReplying, setTicketReplying] = useState(false);

    const [loadingData, setLoadingData] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [scraperStatus, setScraperStatus] = useState<string | null>(null);
    const [loadError, setLoadError] = useState<string | null>(null);
    const [roleUpdating, setRoleUpdating] = useState<number | null>(null);
    const [blockUpdating, setBlockUpdating] = useState<number | null>(null);

    const isSuperAdmin = user?.email?.toLowerCase() === 'mustafa@osool.eg';

    const handleRoleChange = async (userId: number, newRole: string) => {
        setRoleUpdating(userId);
        try {
            const updated = await updateUserRole(userId, newRole);
            setUsers(prev => prev.map(u => u.id === userId ? { ...u, role: updated.role } : u));
        } catch (err) {
            console.error('Failed to update role:', err);
        } finally {
            setRoleUpdating(null);
        }
    };

    const handleBlockToggle = async (userId: number, currentlyBlocked: boolean) => {
        setBlockUpdating(userId);
        try {
            await blockUser(userId, !currentlyBlocked);
            setUsers(prev => prev.map(u => u.id === userId
                ? { ...u, role: !currentlyBlocked ? 'blocked' : 'investor' }
                : u
            ));
        } catch (err) {
            console.error('Failed to toggle block:', err);
        } finally {
            setBlockUpdating(null);
        }
    };

    // Check admin access
    useEffect(() => {
        if (authLoading) return;
        if (!isAuthenticated) {
            router.push('/login');
            return;
        }
        checkAdmin()
            .then(() => { setIsAdmin(true); setChecking(false); })
            .catch(() => { setIsAdmin(false); setChecking(false); });
    }, [isAuthenticated, authLoading, router]);

    // Load data for active tab
    const loadTabData = useCallback(async () => {
        if (!isAdmin) return;
        setLoadingData(true);
        setLoadError(null);
        try {
            switch (activeTab) {
                case 'overview':
                    const d = await getAdminDashboard();
                    setDashboard(d);
                    break;
                case 'conversations':
                    const c = await getAdminConversations(100);
                    setConversations(c.sessions);
                    break;
                case 'users':
                    const u = await getAdminUsers(200);
                    setUsers(u.users);
                    break;
                case 'scrapers':
                    const m = await getAdminMarketIndicators();
                    setIndicators(m.indicators);
                    break;
                case 'tickets':
                    const [ts, tl] = await Promise.all([
                        getTicketStats(),
                        getAdminTickets({ status: ticketStatusFilter || undefined }),
                    ]);
                    setTicketStats(ts);
                    setAdminTickets(tl.tickets);
                    break;
            }
        } catch (err) {
            console.error('Failed to load admin data:', err);
            setLoadError(activeTab === 'users' ? 'Failed to load users. Please refresh or check backend logs.' : 'Failed to load admin data.');
        } finally {
            setLoadingData(false);
        }
    }, [activeTab, isAdmin]);

    useEffect(() => {
        if (isAdmin) loadTabData();
    }, [activeTab, isAdmin]);

    // Reload tickets when status filter changes
    useEffect(() => {
        if (isAdmin && activeTab === 'tickets') loadTabData();
    }, [ticketStatusFilter]);

    const openConversation = async (sessionId: string) => {
        setLoadingData(true);
        try {
            const data = await getAdminConversation(sessionId);
            setSelectedConversation(data);
        } catch (err) {
            console.error('Failed to load conversation:', err);
        } finally {
            setLoadingData(false);
        }
    };

    const handleTriggerScraper = async (type: 'properties' | 'economic') => {
        setScraperStatus(`Running ${type} scraper...`);
        try {
            if (type === 'properties') {
                await triggerPropertyScraper();
            } else {
                await triggerEconomicScraper();
            }
            setScraperStatus(`${type} scraper completed successfully.`);
            if (activeTab === 'scrapers') loadTabData();
        } catch (err) {
            setScraperStatus(`${type} scraper failed. Check logs.`);
        }
        setTimeout(() => setScraperStatus(null), 5000);
    };

    const handleAdminReply = async () => {
        if (!ticketReplyContent.trim() || ticketReplying || !selectedTicket) return;
        setTicketReplying(true);
        try {
            const newReply = await addAdminTicketReply(selectedTicket.id, ticketReplyContent.trim());
            setSelectedTicket(prev => prev ? { ...prev, replies: [...prev.replies, newReply] } : prev);
            setTicketReplyContent('');
        } catch (err) {
            console.error('Failed to send admin reply:', err);
        } finally {
            setTicketReplying(false);
        }
    };

    // Loading & Access Denied states
    if (authLoading || checking) {
        return (
            <SmartNav>
                <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
                </div>
            </SmartNav>
        );
    }

    if (!isAdmin) {
        return (
            <SmartNav>
                <div className="flex flex-col items-center justify-center h-full gap-4 px-4">
                    <Shield className="w-16 h-16 text-red-500/60" />
                    <h1 className="text-xl font-semibold text-[var(--color-text-primary)]">Access Denied</h1>
                    <p className="text-[var(--color-text-muted)] text-center max-w-md">
                        This area is restricted to authorized administrators only.
                    </p>
                    <button
                        onClick={() => router.push('/chat')}
                        className="mt-4 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
                    >
                        Back to Chat
                    </button>
                </div>
            </SmartNav>
        );
    }

    const filteredConversations = conversations.filter(c =>
        !searchQuery ||
        c.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.user_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.preview?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredUsers = users.filter(u =>
        !searchQuery ||
        u.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.full_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
        { key: 'overview', label: 'Overview', icon: Activity },
        { key: 'conversations', label: 'Conversations', icon: MessageSquare },
        { key: 'users', label: 'Users', icon: Users },
        { key: 'tickets', label: 'Tickets', icon: TicketIcon },
        { key: 'scrapers', label: 'Scrapers & Data', icon: Database },
    ];

    return (
        <SmartNav>
            <div className="flex flex-col h-full overflow-hidden">
                {/* Admin Header */}
                <div className="px-4 md:px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                    <div className="max-w-[1440px] mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Shield className="w-5 h-5 text-emerald-500" />
                            <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">Admin Dashboard</h1>
                        </div>
                        <div className="flex items-center gap-2">
                            {scraperStatus && (
                                <span className="text-xs text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded-full">
                                    {scraperStatus}
                                </span>
                            )}
                            <button
                                onClick={loadTabData}
                                disabled={loadingData}
                                title="Refresh data"
                                className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] transition-colors disabled:opacity-50"
                            >
                                <RefreshCw className={`w-4 h-4 ${loadingData ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Tab Bar */}
                <div className="px-4 md:px-6 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                    <div className="max-w-[1440px] mx-auto flex gap-0.5 overflow-x-auto">
                        {TABS.map(tab => {
                            const Icon = tab.icon;
                            const isActive = activeTab === tab.key;
                            return (
                                <button
                                    key={tab.key}
                                    onClick={() => { setActiveTab(tab.key); setSelectedConversation(null); setSearchQuery(''); }}
                                    className={`flex items-center gap-1.5 px-3 py-2.5 text-[13px] font-medium border-b-2 transition-colors whitespace-nowrap
                                        ${isActive
                                            ? 'border-emerald-500 text-emerald-500'
                                            : 'border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                                        }`}
                                >
                                    <Icon className="w-3.5 h-3.5" />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Main Content */}
                <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4">
                    <div className="max-w-[1440px] mx-auto">

                        {/* OVERVIEW TAB */}
                        {activeTab === 'overview' && dashboard && (
                            <>
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                {[
                                    { label: 'Total Users', value: dashboard.overview.total_users, icon: Users, color: 'text-blue-500' },
                                    { label: 'Total Messages', value: dashboard.overview.total_messages, icon: MessageSquare, color: 'text-emerald-500' },
                                    { label: 'Properties', value: dashboard.overview.total_properties, icon: Building2, color: 'text-purple-500' },
                                    { label: 'Active Listings', value: dashboard.overview.active_properties, icon: TrendingUp, color: 'text-amber-500' },
                                    { label: 'Chat Sessions', value: dashboard.overview.total_sessions, icon: Activity, color: 'text-cyan-500' },
                                    { label: 'Transactions', value: dashboard.overview.total_transactions, icon: Zap, color: 'text-rose-500' },
                                    { label: 'New Users (7d)', value: dashboard.recent_activity.new_users_7d, icon: UserIcon, color: 'text-indigo-500' },
                                    { label: 'Messages (24h)', value: dashboard.recent_activity.messages_24h, icon: Clock, color: 'text-teal-500' },
                                ].map((stat, i) => {
                                    const Icon = stat.icon;
                                    return (
                                        <motion.div
                                            key={stat.label}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4"
                                        >
                                            <div className="flex items-center gap-2 mb-2">
                                                <Icon className={`w-4 h-4 ${stat.color}`} />
                                                <span className="text-xs text-[var(--color-text-muted)]">{stat.label}</span>
                                            </div>
                                            <div className="text-2xl font-bold text-[var(--color-text-primary)]">
                                                {stat.value.toLocaleString()}
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </div>

                            {/* Dual-Engine Quick Links */}
                            <div className="mt-4 grid grid-cols-1 sm:grid-cols-4 gap-3">
                                {[
                                    { label: 'Analytics Dashboard', desc: 'Lead intelligence & intent trends', href: '/admin/analytics', color: 'text-purple-500' },
                                    { label: 'Lead Pipeline', desc: 'Manage leads from chat', href: '/admin/leads', color: 'text-red-500' },
                                    { label: 'Ad Campaigns', desc: 'Meta & Google ad management', href: '/admin/campaigns', color: 'text-blue-500' },
                                ].map((link) => (
                                    <a
                                        key={link.href}
                                        href={link.href}
                                        target={link.external ? "_blank" : "_self"}
                                        rel={link.external ? "noopener noreferrer" : undefined}
                                        className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 hover:border-emerald-500/50 transition-all group"
                                    >
                                        <p className={`text-sm font-semibold group-hover:text-emerald-500 transition-colors ${link.color}`}>{link.label}</p>
                                        <p className="text-xs text-[var(--color-text-muted)] mt-1">{link.desc}</p>
                                    </a>
                                ))}
                                <a
                                    href={process.env.NEXT_PUBLIC_ADMIN_URL || 'https://osooladmin-production.up.railway.app'}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 hover:border-emerald-500/50 transition-all group"
                                >
                                    <p className="text-sm font-semibold group-hover:text-emerald-500 transition-colors text-emerald-500">Advanced SEO Engine ↗</p>
                                    <p className="text-xs text-[var(--color-text-muted)] mt-1">Manage Keywords, Funnels, and Agent specific intents</p>
                                </a>
                            </div>
                            </>
                        )}

                        {/* CONVERSATIONS TAB */}
                        {activeTab === 'conversations' && !selectedConversation && (
                            <div>
                                {/* Search */}
                                <div className="mb-4 relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={e => setSearchQuery(e.target.value)}
                                        placeholder="Search by user name, email, or message..."
                                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                    />
                                </div>

                                {/* Conversation List */}
                                <div className="space-y-2">
                                    {filteredConversations.map((conv, i) => (
                                        <motion.button
                                            key={conv.session_id}
                                            initial={{ opacity: 0, y: 5 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.02 }}
                                            onClick={() => openConversation(conv.session_id)}
                                            className="w-full text-left bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 hover:bg-[var(--color-surface-elevated)] transition-colors"
                                        >
                                            <div className="flex items-center justify-between mb-1">
                                                <div className="flex items-center gap-2">
                                                    <UserIcon className="w-4 h-4 text-[var(--color-text-muted)]" />
                                                    <span className="text-sm font-medium text-[var(--color-text-primary)]">
                                                        {conv.user_name || conv.user_email || 'Anonymous'}
                                                    </span>
                                                    {conv.user_email && (
                                                        <span className="text-[11px] text-[var(--color-text-muted)]">
                                                            {conv.user_email}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-[11px] text-[var(--color-text-muted)] bg-[var(--color-background)] px-2 py-0.5 rounded-full">
                                                        {conv.message_count} msgs
                                                    </span>
                                                    <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)]" />
                                                </div>
                                            </div>
                                            {conv.preview && (
                                                <p className="text-xs text-[var(--color-text-muted)] mt-1 line-clamp-1">{conv.preview}</p>
                                            )}
                                            <div className="text-[10px] text-[var(--color-text-muted)] mt-2">
                                                {conv.last_message_at ? new Date(conv.last_message_at).toLocaleString() : 'No activity'}
                                            </div>
                                        </motion.button>
                                    ))}
                                    {filteredConversations.length === 0 && !loadingData && (
                                        <div className="text-center py-12 text-[var(--color-text-muted)] text-sm">
                                            No conversations found.
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* CONVERSATION DETAIL */}
                        {activeTab === 'conversations' && selectedConversation && (
                            <div>
                                <button
                                    onClick={() => setSelectedConversation(null)}
                                    className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] mb-4 transition-colors"
                                >
                                    <ArrowLeft className="w-4 h-4" />
                                    Back to conversations
                                </button>

                                {selectedConversation.user && (
                                    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-3 mb-4">
                                        <div className="flex items-center gap-2">
                                            <UserIcon className="w-4 h-4 text-emerald-500" />
                                            <span className="text-sm font-medium text-[var(--color-text-primary)]">
                                                {selectedConversation.user.full_name}
                                            </span>
                                            <span className="text-[11px] text-[var(--color-text-muted)]">
                                                ({selectedConversation.user.email})
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Messages */}
                                <div className="space-y-3">
                                    {selectedConversation.messages.map((msg) => (
                                        <div
                                            key={msg.id}
                                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                        >
                                            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                                                msg.role === 'user'
                                                    ? 'bg-emerald-600 text-white'
                                                    : 'bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-primary)]'
                                            }`}>
                                                <div className="flex items-center gap-1.5 mb-1">
                                                    {msg.role === 'user'
                                                        ? <UserIcon className="w-3 h-3 opacity-70" />
                                                        : <Bot className="w-3 h-3 text-emerald-500" />
                                                    }
                                                    <span className="text-[10px] opacity-70 uppercase font-medium">
                                                        {msg.role === 'user' ? 'Customer' : 'CoInvestor'}
                                                    </span>
                                                    <span className="text-[10px] opacity-50 ml-auto">
                                                        {msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : ''}
                                                    </span>
                                                </div>
                                                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                                                {msg.properties && msg.properties.length > 0 && (
                                                    <div className="mt-2 text-[10px] opacity-70">
                                                        [{msg.properties.length} properties recommended]
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* USERS TAB */}
                        {activeTab === 'users' && (
                            <div>
                                {loadError && (
                                    <div className="mb-4 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
                                        <AlertCircle className="w-4 h-4" />
                                        <span>{loadError}</span>
                                    </div>
                                )}
                                <div className="mb-4 relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
                                    <input
                                        type="text"
                                        value={searchQuery}
                                        onChange={e => setSearchQuery(e.target.value)}
                                        placeholder="Search users..."
                                        className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                    />
                                </div>

                                <div className="overflow-x-auto">
                                    <table className="w-full text-left text-sm">
                                        <thead>
                                            <tr className="border-b border-[var(--color-border)]">
                                                <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">User</th>
                                                <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Role</th>
                                                <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Messages</th>
                                                <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">KYC</th>
                                                <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Joined</th>
                                                <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Last Active</th>
                                                {isSuperAdmin && <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Actions</th>}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredUsers.map(u => {
                                                const isOsoolAdmin = u.email === 'mustafa@osool.eg' || u.email === 'hani@osool.eg';
                                                const isBlocked = u.role === 'blocked';
                                                return (
                                                <tr key={u.id} className={`border-b border-[var(--color-border)] transition-colors ${isBlocked ? 'opacity-50' : 'hover:bg-[var(--color-surface)]'}`}>
                                                    <td className="py-2.5 px-3">
                                                        <div className="text-[var(--color-text-primary)] font-medium">{u.full_name || '-'}</div>
                                                        <div className="text-[11px] text-[var(--color-text-muted)]">{u.email}</div>
                                                    </td>
                                                    <td className="py-2.5 px-3">
                                                        {isOsoolAdmin ? (
                                                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500">
                                                                admin
                                                            </span>
                                                        ) : isBlocked ? (
                                                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">
                                                                blocked
                                                            </span>
                                                        ) : isSuperAdmin ? (
                                                            <select
                                                                title="Change user role"
                                                                value={u.role}
                                                                disabled={roleUpdating === u.id}
                                                                onChange={e => handleRoleChange(u.id, e.target.value)}
                                                                className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 border-none outline-none cursor-pointer disabled:opacity-50"
                                                            >
                                                                <option value="investor">investor</option>
                                                                <option value="agent">agent</option>
                                                                <option value="analyst">analyst</option>
                                                                <option value="admin">admin</option>
                                                            </select>
                                                        ) : (
                                                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500">
                                                                {u.role}
                                                            </span>
                                                        )}
                                                    </td>
                                                    <td className="py-2.5 px-3 text-[var(--color-text-muted)]">{u.message_count}</td>
                                                    <td className="py-2.5 px-3">
                                                        <span className={`text-[11px] ${
                                                            u.kyc_status === 'verified' ? 'text-emerald-500' : 'text-amber-500'
                                                        }`}>
                                                            {u.kyc_status}
                                                        </span>
                                                    </td>
                                                    <td className="py-2.5 px-3 text-[11px] text-[var(--color-text-muted)]">
                                                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}
                                                    </td>
                                                    <td className="py-2.5 px-3 text-[11px] text-[var(--color-text-muted)]">
                                                        {u.last_activity ? new Date(u.last_activity).toLocaleDateString() : 'Never'}
                                                    </td>
                                                    {isSuperAdmin && (
                                                        <td className="py-2.5 px-3">
                                                            {!isOsoolAdmin && (
                                                                <button
                                                                    disabled={blockUpdating === u.id}
                                                                    onClick={() => handleBlockToggle(u.id, isBlocked)}
                                                                    className={`text-[11px] px-2 py-0.5 rounded-full border transition-colors disabled:opacity-50 ${
                                                                        isBlocked
                                                                            ? 'border-emerald-500/40 text-emerald-500 hover:bg-emerald-500/10'
                                                                            : 'border-red-500/40 text-red-400 hover:bg-red-500/10'
                                                                    }`}
                                                                >
                                                                    {blockUpdating === u.id ? '...' : isBlocked ? 'Unblock' : 'Block'}
                                                                </button>
                                                            )}
                                                        </td>
                                                    )}
                                                </tr>
                                                );
                                            })}
                                            {!loadingData && filteredUsers.length === 0 && (
                                                <tr>
                                                    <td colSpan={6} className="py-6 px-3 text-center text-sm text-[var(--color-text-muted)]">
                                                        No users found.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* TICKETS TAB */}
                        {activeTab === 'tickets' && (
                            <div className="space-y-4">
                                {/* Ticket Stats */}
                                {ticketStats && !selectedTicket && (
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                                        {[
                                            { label: 'Open', value: ticketStats.open, color: 'text-blue-500', bg: 'bg-blue-500/10' },
                                            { label: 'In Progress', value: ticketStats.in_progress, color: 'text-amber-500', bg: 'bg-amber-500/10' },
                                            { label: 'Resolved', value: ticketStats.resolved, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
                                            { label: 'Closed', value: ticketStats.closed, color: 'text-gray-500', bg: 'bg-gray-500/10' },
                                            { label: 'Total', value: ticketStats.total, color: 'text-purple-500', bg: 'bg-purple-500/10' },
                                        ].map(s => (
                                            <div key={s.label} className={`${s.bg} rounded-xl p-3 text-center`}>
                                                <p className={`text-lg font-bold ${s.color}`}>{s.value}</p>
                                                <p className="text-[11px] text-[var(--color-text-muted)]">{s.label}</p>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* Selected Ticket Detail */}
                                {selectedTicket ? (
                                    <div className="space-y-4">
                                        <button
                                            onClick={() => setSelectedTicket(null)}
                                            className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                                        >
                                            <ArrowLeft className="w-4 h-4" />
                                            Back to Tickets
                                        </button>

                                        {/* Ticket Info Card */}
                                        <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
                                            <div className="flex items-start justify-between gap-3">
                                                <div>
                                                    <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">{selectedTicket.subject}</h3>
                                                    <div className="flex items-center gap-2 mt-1 text-xs text-[var(--color-text-muted)]">
                                                        <span>#{selectedTicket.id}</span>
                                                        <span>{selectedTicket.user?.name} ({selectedTicket.user?.email})</span>
                                                        <span>{selectedTicket.category}</span>
                                                        <span className={selectedTicket.priority === 'urgent' ? 'text-red-500 font-medium' : selectedTicket.priority === 'high' ? 'text-orange-500' : ''}>{selectedTicket.priority}</span>
                                                        {selectedTicket.created_at && <span>{new Date(selectedTicket.created_at).toLocaleDateString()}</span>}
                                                    </div>
                                                </div>
                                                {/* Status dropdown */}
                                                <select
                                                    title="Change ticket status"
                                                    value={selectedTicket.status}
                                                    onChange={async (e) => {
                                                        const newStatus = e.target.value;
                                                        try {
                                                            await updateTicketStatus(selectedTicket.id, newStatus);
                                                            setSelectedTicket(prev => prev ? { ...prev, status: newStatus } : prev);
                                                            setAdminTickets(prev => prev.map(t => t.id === selectedTicket.id ? { ...t, status: newStatus } : t));
                                                        } catch (err) { console.error('Failed to update status:', err); }
                                                    }}
                                                    className="text-xs px-2 py-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text-primary)]"
                                                >
                                                    <option value="open">Open</option>
                                                    <option value="in_progress">In Progress</option>
                                                    <option value="resolved">Resolved</option>
                                                    <option value="closed">Closed</option>
                                                </select>
                                            </div>

                                            {/* Description */}
                                            <div className="mt-3 p-3 rounded-lg bg-[var(--color-background)] text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap">
                                                {selectedTicket.description}
                                            </div>
                                        </div>

                                        {/* Replies Thread */}
                                        <div className="space-y-3">
                                            {selectedTicket.replies.map(reply => (
                                                <div key={reply.id} className={`p-3 rounded-xl border ${reply.is_admin_reply ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-[var(--color-border)] bg-[var(--color-surface)]'}`}>
                                                    <div className="flex items-center gap-2 mb-1.5">
                                                        <span className={`text-xs font-medium ${reply.is_admin_reply ? 'text-emerald-500' : 'text-[var(--color-text-primary)]'}`}>
                                                            {reply.user_name} {reply.is_admin_reply && '(Admin)'}
                                                        </span>
                                                        {reply.created_at && <span className="text-[11px] text-[var(--color-text-muted)]">{new Date(reply.created_at).toLocaleString()}</span>}
                                                    </div>
                                                    <p className="text-sm text-[var(--color-text-secondary)] whitespace-pre-wrap">{reply.content}</p>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Admin Reply Input */}
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={ticketReplyContent}
                                                onChange={(e) => setTicketReplyContent(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter' && !e.shiftKey && ticketReplyContent.trim()) {
                                                        e.preventDefault();
                                                        handleAdminReply();
                                                    }
                                                }}
                                                placeholder="Reply as admin..."
                                                className="flex-1 px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-emerald-500/50"
                                            />
                                            <button
                                                onClick={handleAdminReply}
                                                disabled={!ticketReplyContent.trim() || ticketReplying}
                                                className="px-3 py-2 rounded-xl bg-emerald-600 text-white text-sm hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1.5"
                                            >
                                                {ticketReplying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                                                Reply
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        {/* Status Filter */}
                                        <div className="flex gap-1">
                                            {[
                                                { key: '', label: 'All' },
                                                { key: 'open', label: 'Open' },
                                                { key: 'in_progress', label: 'In Progress' },
                                                { key: 'resolved', label: 'Resolved' },
                                                { key: 'closed', label: 'Closed' },
                                            ].map(f => (
                                                <button
                                                    key={f.key}
                                                    onClick={() => setTicketStatusFilter(f.key)}
                                                    className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors ${ticketStatusFilter === f.key ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] border border-transparent'}`}
                                                >
                                                    {f.label}
                                                </button>
                                            ))}
                                        </div>

                                        {/* Tickets Table */}
                                        {adminTickets.length > 0 ? (
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-left text-sm">
                                                    <thead>
                                                        <tr className="border-b border-[var(--color-border)]">
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">ID</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Subject</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">User</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Category</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Priority</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Status</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Replies</th>
                                                            <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Created</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {adminTickets.map(ticket => {
                                                            const priorityColors: Record<string, string> = { low: 'text-gray-400', medium: 'text-blue-400', high: 'text-orange-500', urgent: 'text-red-500 font-medium' };
                                                            const statusColors: Record<string, string> = { open: 'text-blue-500 bg-blue-500/10', in_progress: 'text-amber-500 bg-amber-500/10', resolved: 'text-emerald-500 bg-emerald-500/10', closed: 'text-gray-500 bg-gray-500/10' };
                                                            const statusLabel: Record<string, string> = { open: 'Open', in_progress: 'In Progress', resolved: 'Resolved', closed: 'Closed' };

                                                            return (
                                                                <tr
                                                                    key={ticket.id}
                                                                    onClick={async () => {
                                                                        try {
                                                                            const detail = await getAdminTicketDetail(ticket.id);
                                                                            setSelectedTicket(detail);
                                                                            setTicketReplyContent('');
                                                                        } catch (err) { console.error('Failed to load ticket:', err); }
                                                                    }}
                                                                    className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface)] transition-colors cursor-pointer"
                                                                >
                                                                    <td className="py-2 px-3 text-[var(--color-text-muted)] text-xs">#{ticket.id}</td>
                                                                    <td className="py-2 px-3 text-[var(--color-text-primary)] font-medium max-w-[200px] truncate">{ticket.subject}</td>
                                                                    <td className="py-2 px-3">
                                                                        <div className="text-xs text-[var(--color-text-primary)]">{ticket.user_name}</div>
                                                                        <div className="text-[11px] text-[var(--color-text-muted)]">{ticket.user_email}</div>
                                                                    </td>
                                                                    <td className="py-2 px-3 text-xs text-[var(--color-text-muted)] capitalize">{ticket.category}</td>
                                                                    <td className={`py-2 px-3 text-xs capitalize ${priorityColors[ticket.priority] || ''}`}>{ticket.priority}</td>
                                                                    <td className="py-2 px-3">
                                                                        <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[ticket.status] || ''}`}>
                                                                            {statusLabel[ticket.status] || ticket.status}
                                                                        </span>
                                                                    </td>
                                                                    <td className="py-2 px-3 text-xs text-[var(--color-text-muted)]">{ticket.replies_count}</td>
                                                                    <td className="py-2 px-3 text-[11px] text-[var(--color-text-muted)]">{ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : '-'}</td>
                                                                </tr>
                                                            );
                                                        })}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ) : !loadingData ? (
                                            <div className="text-center py-12">
                                                <TicketIcon className="w-10 h-10 mx-auto text-[var(--color-text-muted)] opacity-30 mb-3" />
                                                <p className="text-sm text-[var(--color-text-muted)]">No tickets found</p>
                                            </div>
                                        ) : null}
                                    </>
                                )}
                            </div>
                        )}

                        {/* SCRAPERS TAB */}
                        {activeTab === 'scrapers' && (
                            <div className="space-y-6">
                                {/* Scraper Controls */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <Building2 className="w-5 h-5 text-purple-500" />
                                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Property Scraper</h3>
                                        </div>
                                        <p className="text-xs text-[var(--color-text-muted)] mb-3">
                                            Scrapes Nawy.com for new property listings. Runs automatically every week.
                                        </p>
                                        <button
                                            onClick={() => handleTriggerScraper('properties')}
                                            className="px-3 py-1.5 rounded-lg bg-purple-600 text-white text-xs font-medium hover:bg-purple-700 transition-colors"
                                        >
                                            Run Now
                                        </button>
                                    </div>

                                    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4">
                                        <div className="flex items-center gap-2 mb-2">
                                            <TrendingUp className="w-5 h-5 text-amber-500" />
                                            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Economic Scraper</h3>
                                        </div>
                                        <p className="text-xs text-[var(--color-text-muted)] mb-3">
                                            Fetches USD/EGP rate, inflation, gold prices, and banking rates.
                                        </p>
                                        <button
                                            onClick={() => handleTriggerScraper('economic')}
                                            className="px-3 py-1.5 rounded-lg bg-amber-600 text-white text-xs font-medium hover:bg-amber-700 transition-colors"
                                        >
                                            Run Now
                                        </button>
                                    </div>
                                </div>

                                {/* Market Indicators Table */}
                                {indicators.length > 0 && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">Current Market Indicators</h3>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-left text-sm">
                                                <thead>
                                                    <tr className="border-b border-[var(--color-border)]">
                                                        <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Indicator</th>
                                                        <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Value</th>
                                                        <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Source</th>
                                                        <th className="py-2 px-3 text-[11px] font-semibold text-[var(--color-text-muted)] uppercase">Updated</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {indicators.map((ind: any) => (
                                                        <tr key={ind.key} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface)] transition-colors">
                                                            <td className="py-2 px-3 text-[var(--color-text-primary)] font-medium">{ind.key.replace(/_/g, ' ')}</td>
                                                            <td className="py-2 px-3 text-[var(--color-text-primary)] font-mono">
                                                                {ind.value < 1 ? `${(ind.value * 100).toFixed(1)}%` : ind.value.toLocaleString()}
                                                            </td>
                                                            <td className="py-2 px-3 text-[11px] text-[var(--color-text-muted)]">{ind.source}</td>
                                                            <td className="py-2 px-3 text-[11px] text-[var(--color-text-muted)]">
                                                                {ind.last_updated ? new Date(ind.last_updated).toLocaleDateString() : '-'}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Loading indicator */}
                        {loadingData && (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </SmartNav>
    );
}
