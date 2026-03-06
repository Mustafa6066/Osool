'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Shield, Users, MessageSquare, Building2, TrendingUp,
    Loader2, ChevronRight, Search, RefreshCw, Eye,
    Activity, Clock, ArrowLeft, Bot, User as UserIcon,
    Database, Zap, AlertCircle
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
    AdminDashboardData,
    AdminUser,
    AdminConversation,
    AdminMessage,
} from '@/lib/api';

type Tab = 'overview' | 'conversations' | 'users' | 'scrapers';

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

    const [loadingData, setLoadingData] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [scraperStatus, setScraperStatus] = useState<string | null>(null);

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
            }
        } catch (err) {
            console.error('Failed to load admin data:', err);
        } finally {
            setLoadingData(false);
        }
    }, [activeTab, isAdmin]);

    useEffect(() => {
        if (isAdmin) loadTabData();
    }, [isAdmin, loadTabData]);

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
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredUsers.map(u => (
                                                <tr key={u.id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-surface)] transition-colors">
                                                    <td className="py-2.5 px-3">
                                                        <div className="text-[var(--color-text-primary)] font-medium">{u.full_name || '-'}</div>
                                                        <div className="text-[11px] text-[var(--color-text-muted)]">{u.email}</div>
                                                    </td>
                                                    <td className="py-2.5 px-3">
                                                        <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                                                            u.role === 'admin'
                                                                ? 'bg-emerald-500/10 text-emerald-500'
                                                                : 'bg-blue-500/10 text-blue-500'
                                                        }`}>
                                                            {u.role}
                                                        </span>
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
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
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
