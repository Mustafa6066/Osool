'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, Loader2, Send, AlertTriangle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import SmartNav from '@/components/SmartNav';
import Link from 'next/link';
import { createTicket } from '@/lib/api';

const CATEGORIES = [
    { value: 'general', label: 'General Inquiry' },
    { value: 'payment', label: 'Payment Issue' },
    { value: 'property', label: 'Property Related' },
    { value: 'technical', label: 'Technical Problem' },
    { value: 'account', label: 'Account & Profile' },
];

const PRIORITIES = [
    { value: 'low', label: 'Low', description: 'General question, no rush' },
    { value: 'medium', label: 'Medium', description: 'Needs attention soon' },
    { value: 'high', label: 'High', description: 'Important, blocking issue' },
    { value: 'urgent', label: 'Urgent', description: 'Critical, immediate attention needed' },
];

export default function NewTicketPage() {
    const { isAuthenticated, loading: authLoading } = useAuth();
    const router = useRouter();

    const [subject, setSubject] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('general');
    const [priority, setPriority] = useState('medium');
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!authLoading && !isAuthenticated) {
            router.push('/login');
        }
    }, [isAuthenticated, authLoading, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (subject.trim().length < 3) {
            setError('Subject must be at least 3 characters.');
            return;
        }
        if (description.trim().length < 10) {
            setError('Description must be at least 10 characters.');
            return;
        }

        setSubmitting(true);
        try {
            const ticket = await createTicket({
                subject: subject.trim(),
                description: description.trim(),
                category,
                priority,
            });
            router.push(`/tickets/${ticket.id}`);
        } catch (err: any) {
            setError(err?.response?.data?.detail || 'Failed to create ticket. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    if (authLoading) {
        return (
            <SmartNav>
                <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
                </div>
            </SmartNav>
        );
    }

    return (
        <SmartNav>
            <div className="flex flex-col h-full overflow-hidden">
                {/* Header */}
                <div className="px-4 md:px-6 py-3 border-b border-[var(--color-border)] bg-[var(--color-background)]">
                    <div className="max-w-2xl mx-auto flex items-center gap-3">
                        <Link
                            href="/tickets"
                            className="p-1.5 rounded-lg hover:bg-[var(--color-surface)] transition-colors text-[var(--color-text-muted)]"
                        >
                            <ArrowLeft className="w-4 h-4" />
                        </Link>
                        <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">New Support Ticket</h1>
                    </div>
                </div>

                {/* Form */}
                <div className="flex-1 overflow-y-auto px-4 md:px-6 py-6">
                    <motion.form
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        onSubmit={handleSubmit}
                        className="max-w-2xl mx-auto space-y-5"
                    >
                        {/* Error */}
                        {error && (
                            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                                {error}
                            </div>
                        )}

                        {/* Subject */}
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1.5">
                                Subject <span className="text-red-500">*</span>
                            </label>
                            <input
                                type="text"
                                value={subject}
                                onChange={(e) => setSubject(e.target.value)}
                                maxLength={200}
                                placeholder="Brief summary of your issue"
                                className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-emerald-500/50 transition-colors"
                            />
                        </div>

                        {/* Category & Priority Row */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1.5">
                                    Category
                                </label>
                                <select
                                    title="Select ticket category"
                                    value={category}
                                    onChange={(e) => setCategory(e.target.value)}
                                    className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-emerald-500/50 transition-colors appearance-none"
                                >
                                    {CATEGORIES.map(c => (
                                        <option key={c.value} value={c.value}>{c.label}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1.5">
                                    Priority
                                </label>
                                <select
                                    title="Select ticket priority"
                                    value={priority}
                                    onChange={(e) => setPriority(e.target.value)}
                                    className="w-full px-4 py-2.5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text-primary)] focus:outline-none focus:border-emerald-500/50 transition-colors appearance-none"
                                >
                                    {PRIORITIES.map(p => (
                                        <option key={p.value} value={p.value}>{p.label} &mdash; {p.description}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Description */}
                        <div>
                            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1.5">
                                Description <span className="text-red-500">*</span>
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                maxLength={5000}
                                rows={8}
                                placeholder="Describe your issue in detail. Include any relevant information like order IDs, property names, error messages, etc."
                                className="w-full px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] text-sm text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:outline-none focus:border-emerald-500/50 transition-colors resize-none"
                            />
                            <p className="text-xs text-[var(--color-text-muted)] mt-1 text-right">
                                {description.length}/5000
                            </p>
                        </div>

                        {/* Submit */}
                        <div className="flex items-center justify-end gap-3 pt-2">
                            <Link
                                href="/tickets"
                                className="px-4 py-2.5 rounded-xl border border-[var(--color-border)] text-sm text-[var(--color-text-muted)] hover:bg-[var(--color-surface)] transition-colors"
                            >
                                Cancel
                            </Link>
                            <button
                                type="submit"
                                disabled={submitting}
                                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {submitting ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Send className="w-4 h-4" />
                                )}
                                Submit Ticket
                            </button>
                        </div>
                    </motion.form>
                </div>
            </div>
        </SmartNav>
    );
}
