'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import {
    ArrowLeft, Loader2, Send, Clock, CheckCircle,
    AlertCircle, XCircle, Shield, User as UserIcon, MessageSquare
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import SmartNav from '@/components/SmartNav';
import Link from 'next/link';
import { getTicketDetail, addTicketReply, TicketDetail, TicketReply } from '@/lib/api';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
    open: { label: 'Open', color: 'text-blue-500', bg: 'bg-blue-500/10 border-blue-500/20', icon: AlertCircle },
    in_progress: { label: 'In Progress', color: 'text-amber-500', bg: 'bg-amber-500/10 border-amber-500/20', icon: Clock },
    resolved: { label: 'Resolved', color: 'text-emerald-500', bg: 'bg-emerald-500/10 border-emerald-500/20', icon: CheckCircle },
    closed: { label: 'Closed', color: 'text-gray-500', bg: 'bg-gray-500/10 border-gray-500/20', icon: XCircle },
};

const PRIORITY_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
    low: { label: 'Low', color: 'text-gray-400', dot: 'bg-gray-400' },
    medium: { label: 'Medium', color: 'text-blue-400', dot: 'bg-blue-400' },
    high: { label: 'High', color: 'text-orange-500', dot: 'bg-orange-500' },
    urgent: { label: 'Urgent', color: 'text-red-500', dot: 'bg-red-500' },
};

const CATEGORY_LABELS: Record<string, string> = {
    general: 'General',
    payment: 'Payment',
    property: 'Property',
    technical: 'Technical',
    account: 'Account',
};

export default function TicketDetailPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
    const router = useRouter();
    const params = useParams();
    const ticketId = Number(params.id);

    const [ticket, setTicket] = useState<TicketDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [replyContent, setReplyContent] = useState('');
    const [sending, setSending] = useState(false);
    const repliesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, authLoading, router]);

    useEffect(() => {
        if (isAuthenticated && ticketId) {
            loadTicket();
        }
    }, [isAuthenticated, ticketId]);

    const loadTicket = async () => {
        setLoading(true);
        try {
            const data = await getTicketDetail(ticketId);
            setTicket(data);
        } catch (err) {
            console.error('Failed to load ticket:', err);
            router.push('/tickets');
        } finally {
            setLoading(false);
        }
    };

    const handleSendReply = async () => {
        if (!replyContent.trim() || sending) return;
        setSending(true);
        try {
            const newReply = await addTicketReply(ticketId, replyContent.trim());
            setTicket(prev => prev ? { ...prev, replies: [...prev.replies, newReply] } : prev);
            setReplyContent('');
            setTimeout(() => repliesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
        } catch (err) {
            console.error('Failed to send reply:', err);
        } finally {
            setSending(false);
        }
    };

    if (authLoading || loading) {
        return (
            <SmartNav>
                <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
                </div>
            </SmartNav>
        );
    }

    if (!ticket) {
        return (
            <SmartNav>
                <div className="flex flex-col items-center justify-center h-full gap-3">
                    <p className="text-[var(--color-text-muted)]">Ticket not found</p>
                    <Link href="/tickets" className="text-emerald-500 text-sm hover:underline">
                        Back to Tickets
                    </Link>
                </div>
            </SmartNav>
        );
    }

    const statusCfg = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
    const priorityCfg = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
    const StatusIcon = statusCfg.icon;
    const isClosed = ticket.status === 'closed';

    return (
        <SmartNav>
            <div className="flex flex-col h-full overflow-hidden">
                {/* Header */}
                <div className="px-4 md:px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                    <div className="max-w-4xl mx-auto">
                        <div className="flex items-center gap-3 mb-2">
                            <Link
                                href="/tickets"
                                className="p-1.5 rounded-lg hover:bg-[var(--color-surface)] transition-colors text-[var(--color-text-muted)]"
                            >
                                <ArrowLeft className="w-4 h-4" />
                            </Link>
                            <span className="text-xs text-[var(--color-text-muted)]">Ticket #{ticket.id}</span>
                            <span className={`text-xs px-2 py-0.5 rounded-full font-medium border ${statusCfg.color} ${statusCfg.bg}`}>
                                <StatusIcon className="w-3 h-3 inline mr-1" />
                                {statusCfg.label}
                            </span>
                        </div>
                        <h1 className="text-base font-semibold text-[var(--color-text-primary)]">{ticket.subject}</h1>
                        <div className="flex items-center gap-3 mt-1 text-xs text-[var(--color-text-muted)]">
                            <span className="flex items-center gap-1">
                                <span className={`w-1.5 h-1.5 rounded-full ${priorityCfg.dot}`}></span>
                                {priorityCfg.label} Priority
                            </span>
                            <span>{CATEGORY_LABELS[ticket.category] || ticket.category}</span>
                            {ticket.created_at && (
                                <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Thread */}
                <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4">
                    <div className="max-w-4xl mx-auto space-y-4">
                        {/* Original Description */}
                        <motion.div
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]"
                        >
                            <div className="flex items-center gap-2 mb-2">
                                <div className="w-6 h-6 rounded-full bg-blue-500/10 flex items-center justify-center">
                                    <UserIcon className="w-3.5 h-3.5 text-blue-500" />
                                </div>
                                <span className="text-xs font-medium text-[var(--color-text-primary)]">You</span>
                                {ticket.created_at && (
                                    <span className="text-xs text-[var(--color-text-muted)]">
                                        {new Date(ticket.created_at).toLocaleString()}
                                    </span>
                                )}
                            </div>
                            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed whitespace-pre-wrap">
                                {ticket.description}
                            </p>
                        </motion.div>

                        {/* Replies */}
                        {ticket.replies.map((reply, i) => (
                            <motion.div
                                key={reply.id}
                                initial={{ opacity: 0, y: 8 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }}
                                className={`p-4 rounded-xl border ${
                                    reply.is_admin_reply
                                        ? 'border-emerald-500/20 bg-emerald-500/5'
                                        : 'border-[var(--color-border)] bg-[var(--color-surface)]'
                                }`}
                            >
                                <div className="flex items-center gap-2 mb-2">
                                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                        reply.is_admin_reply ? 'bg-emerald-500/10' : 'bg-blue-500/10'
                                    }`}>
                                        {reply.is_admin_reply
                                            ? <Shield className="w-3.5 h-3.5 text-emerald-500" />
                                            : <UserIcon className="w-3.5 h-3.5 text-blue-500" />
                                        }
                                    </div>
                                    <span className="text-xs font-medium text-[var(--color-text-primary)]">
                                        {reply.user_name}
                                        {reply.is_admin_reply && (
                                            <span className="ml-1 text-emerald-500">(Admin)</span>
                                        )}
                                    </span>
                                    {reply.created_at && (
                                        <span className="text-xs text-[var(--color-text-muted)]">
                                            {new Date(reply.created_at).toLocaleString()}
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed whitespace-pre-wrap">
                                    {reply.content}
                                </p>
                            </motion.div>
                        ))}
                        <div ref={repliesEndRef} />
                    </div>
                </div>

                {/* Reply Input */}
                {!isClosed ? (
                    <div className="px-4 md:px-6 py-3 border-t border-[var(--color-border)] bg-[var(--color-background)]">
                        <div className="max-w-4xl mx-auto flex gap-2">
                            <input
                                type="text"
                                value={replyContent}
                                onChange={(e) => setReplyContent(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendReply()}
                                placeholder="Type your reply..."
                                className="flex-1 px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-emerald-500/50 transition-colors"
                            />
                            <button
                                onClick={handleSendReply}
                                disabled={!replyContent.trim() || sending}
                                className="px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
                            >
                                {sending ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Send className="w-4 h-4" />
                                )}
                                Send
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="px-4 md:px-6 py-3 border-t border-[var(--color-border)] bg-[var(--color-background)]">
                        <div className="max-w-4xl mx-auto text-center">
                            <p className="text-xs text-[var(--color-text-muted)]">
                                This ticket is closed. Create a new ticket if you need further assistance.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </SmartNav>
    );
}
