'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Ticket as TicketIcon, Plus, Loader2, Filter,
    Clock, CheckCircle, AlertCircle, XCircle, ChevronRight,
    MessageSquare
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import SmartNav from '@/components/SmartNav';
import Link from 'next/link';
import { getMyTickets, Ticket } from '@/lib/api';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
    open: { label: 'Open', color: 'text-blue-500', bg: 'bg-blue-500/10', icon: AlertCircle },
    in_progress: { label: 'In Progress', color: 'text-amber-500', bg: 'bg-amber-500/10', icon: Clock },
    resolved: { label: 'Resolved', color: 'text-emerald-500', bg: 'bg-emerald-500/10', icon: CheckCircle },
    closed: { label: 'Closed', color: 'text-gray-500', bg: 'bg-gray-500/10', icon: XCircle },
};

const PRIORITY_CONFIG: Record<string, { label: string; color: string }> = {
    low: { label: 'Low', color: 'text-gray-400' },
    medium: { label: 'Medium', color: 'text-blue-400' },
    high: { label: 'High', color: 'text-orange-500' },
    urgent: { label: 'Urgent', color: 'text-red-500' },
};

const CATEGORY_LABELS: Record<string, string> = {
    general: 'General',
    payment: 'Payment',
    property: 'Property',
    technical: 'Technical',
    account: 'Account',
};

export default function TicketsPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
    const router = useRouter();

    const [tickets, setTickets] = useState<Ticket[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, authLoading, router]);

    const loadTickets = useCallback(async () => {
        if (!isAuthenticated) return;
        setLoading(true);
        try {
            const data = await getMyTickets(statusFilter);
            setTickets(data.tickets);
            setTotal(data.total);
        } catch (err) {
            console.error('Failed to load tickets:', err);
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated, statusFilter]);

    useEffect(() => {
        loadTickets();
    }, [loadTickets]);

    if (authLoading) {
        return (
            <SmartNav>
                <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
                </div>
            </SmartNav>
        );
    }

    const statusFilters = [
        { key: undefined, label: 'All' },
        { key: 'open', label: 'Open' },
        { key: 'in_progress', label: 'In Progress' },
        { key: 'resolved', label: 'Resolved' },
        { key: 'closed', label: 'Closed' },
    ];

    return (
        <SmartNav>
            <div className="flex flex-col h-full overflow-hidden">
                {/* Header */}
                <div className="px-4 md:px-6 py-4 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                    <div className="max-w-4xl mx-auto flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <TicketIcon className="w-5 h-5 text-emerald-500" />
                            <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">Support Tickets</h1>
                            {total > 0 && (
                                <span className="text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] px-2 py-0.5 rounded-full">
                                    {total}
                                </span>
                            )}
                        </div>
                        <Link
                            href="/tickets/new"
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                            New Ticket
                        </Link>
                    </div>
                </div>

                {/* Status Filter Bar */}
                <div className="px-4 md:px-6 py-2 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                    <div className="max-w-4xl mx-auto flex gap-1 overflow-x-auto">
                        {statusFilters.map(f => (
                            <button
                                key={f.key ?? 'all'}
                                onClick={() => setStatusFilter(f.key)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-full transition-colors whitespace-nowrap
                                    ${statusFilter === f.key
                                        ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30'
                                        : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] border border-transparent'
                                    }`}
                            >
                                {f.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Ticket List */}
                <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4">
                    <div className="max-w-4xl mx-auto space-y-2">
                        {loading ? (
                            <div className="flex items-center justify-center py-20">
                                <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
                            </div>
                        ) : tickets.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-center py-20"
                            >
                                <TicketIcon className="w-12 h-12 mx-auto text-[var(--color-text-muted)] opacity-30 mb-4" />
                                <p className="text-[var(--color-text-muted)] text-sm">
                                    {statusFilter ? 'No tickets with this status.' : 'No support tickets yet.'}
                                </p>
                                <Link
                                    href="/tickets/new"
                                    className="inline-flex items-center gap-1.5 mt-4 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors"
                                >
                                    <Plus className="w-4 h-4" />
                                    Create Your First Ticket
                                </Link>
                            </motion.div>
                        ) : (
                            <AnimatePresence mode="popLayout">
                                {tickets.map((ticket, i) => {
                                    const statusCfg = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
                                    const priorityCfg = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
                                    const StatusIcon = statusCfg.icon;

                                    return (
                                        <motion.div
                                            key={ticket.id}
                                            initial={{ opacity: 0, y: 8 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -8 }}
                                            transition={{ delay: i * 0.03 }}
                                        >
                                            <Link href={`/tickets/${ticket.id}`}>
                                                <div className="group p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/30 hover:bg-emerald-500/5 transition-all cursor-pointer">
                                                    <div className="flex items-start justify-between gap-3">
                                                        <div className="flex-1 min-w-0">
                                                            <div className="flex items-center gap-2 mb-1.5">
                                                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusCfg.color} ${statusCfg.bg}`}>
                                                                    {statusCfg.label}
                                                                </span>
                                                                <span className={`text-xs ${priorityCfg.color}`}>
                                                                    {priorityCfg.label}
                                                                </span>
                                                                <span className="text-xs text-[var(--color-text-muted)]">
                                                                    {CATEGORY_LABELS[ticket.category] || ticket.category}
                                                                </span>
                                                            </div>
                                                            <h3 className="text-sm font-medium text-[var(--color-text-primary)] truncate group-hover:text-emerald-500 transition-colors">
                                                                {ticket.subject}
                                                            </h3>
                                                            <div className="flex items-center gap-3 mt-2 text-xs text-[var(--color-text-muted)]">
                                                                <span>#{ticket.id}</span>
                                                                {ticket.created_at && (
                                                                    <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                                                                )}
                                                                {ticket.replies_count > 0 && (
                                                                    <span className="flex items-center gap-1">
                                                                        <MessageSquare className="w-3 h-3" />
                                                                        {ticket.replies_count}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] group-hover:text-emerald-500 transition-colors mt-1 flex-shrink-0" />
                                                    </div>
                                                </div>
                                            </Link>
                                        </motion.div>
                                    );
                                })}
                            </AnimatePresence>
                        )}
                    </div>
                </div>
            </div>
        </SmartNav>
    );
}
