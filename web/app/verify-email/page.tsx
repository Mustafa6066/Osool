"use client";

import { useSearchParams } from 'next/navigation';
import { useState, useEffect, useRef, Suspense } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Loader2, Mail, ArrowRight } from 'lucide-react';
import api from '@/lib/api';

function VerifyEmailContent() {
    const searchParams = useSearchParams();
    const { language } = useLanguage();
    const token = searchParams.get('token');
    const verifiedRef = useRef(false);

    const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'no-token'>('loading');
    const [message, setMessage] = useState('');

    useEffect(() => {
        if (!token) {
            setStatus('no-token');
            setMessage(
                language === 'ar'
                    ? 'رابط التحقق غير صالح. تأكد من الرابط الذي تلقيته بالبريد.'
                    : 'Invalid verification link. Please check the link from your email.'
            );
            return;
        }

        // Prevent duplicate verification calls (React Strict Mode)
        if (verifiedRef.current) return;
        verifiedRef.current = true;

        const verify = async () => {
            try {
                const res = await api.get(`/api/auth/verify-email?token=${encodeURIComponent(token)}`);
                if (res.data.status === 'verified') {
                    setStatus('success');
                    setMessage(
                        language === 'ar'
                            ? 'تم تأكيد بريدك الإلكتروني بنجاح! يمكنك الآن الاستمتاع بجميع مميزات أصول.'
                            : 'Your email has been verified successfully! You can now enjoy all Osool features.'
                    );
                } else {
                    setStatus('error');
                    setMessage(res.data.message || (language === 'ar' ? 'حدث خطأ' : 'An error occurred'));
                }
            } catch (err: any) {
                setStatus('error');
                const detail = err?.response?.data?.detail;
                setMessage(
                    detail ||
                    (language === 'ar'
                        ? 'رابط التحقق غير صالح أو منتهي الصلاحية. يرجى طلب رابط جديد.'
                        : 'Invalid or expired verification token. Please request a new one.')
                );
            }
        };

        verify();
    }, [token, language]);

    const iconMap = {
        loading: <Loader2 className="w-16 h-16 text-[var(--color-primary)] animate-spin" />,
        success: <CheckCircle2 className="w-16 h-16 text-green-500" />,
        error: <XCircle className="w-16 h-16 text-red-400" />,
        'no-token': <Mail className="w-16 h-16 text-amber-400" />,
    };

    const titleMap = {
        loading: language === 'ar' ? 'جارٍ التحقق...' : 'Verifying...',
        success: language === 'ar' ? 'تم التحقق ✓' : 'Email Verified ✓',
        error: language === 'ar' ? 'فشل التحقق' : 'Verification Failed',
        'no-token': language === 'ar' ? 'رابط غير صالح' : 'Invalid Link',
    };

    return (
        <main className="min-h-screen flex items-center justify-center bg-[var(--color-background)] px-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md text-center"
            >
                {/* Logo */}
                <div className="mb-8">
                    <Link href="/">
                        <span className="text-3xl font-bold bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] bg-clip-text text-transparent">
                            Osool
                        </span>
                    </Link>
                </div>

                {/* Card */}
                <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl p-8 shadow-xl">
                    <motion.div
                        key={status}
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: 'spring', stiffness: 200 }}
                        className="flex justify-center mb-6"
                    >
                        {iconMap[status]}
                    </motion.div>

                    <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mb-3">
                        {titleMap[status]}
                    </h1>

                    <p className="text-[var(--color-text-secondary)] mb-8 leading-relaxed">
                        {message}
                    </p>

                    {status === 'success' && (
                        <Link
                            href="/dashboard"
                            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-secondary)] text-white font-semibold hover:opacity-90 transition-opacity"
                        >
                            {language === 'ar' ? 'إلى لوحة التحكم' : 'Go to Dashboard'}
                            <ArrowRight className="w-4 h-4" />
                        </Link>
                    )}

                    {(status === 'error' || status === 'no-token') && (
                        <div className="space-y-3">
                            <Link
                                href="/dashboard"
                                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[var(--color-surface-elevated)] text-[var(--color-text-primary)] font-semibold hover:opacity-80 transition-opacity"
                            >
                                {language === 'ar' ? 'إلى لوحة التحكم' : 'Go to Dashboard'}
                            </Link>
                            <p className="text-xs text-[var(--color-text-muted)]">
                                {language === 'ar'
                                    ? 'يمكنك إعادة إرسال رابط التحقق من إعدادات حسابك'
                                    : 'You can resend the verification link from your account settings'}
                            </p>
                        </div>
                    )}
                </div>
            </motion.div>
        </main>
    );
}

export default function VerifyEmailPage() {
    return (
        <Suspense fallback={
            <main className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
                <Loader2 className="w-10 h-10 text-[var(--color-primary)] animate-spin" />
            </main>
        }>
            <VerifyEmailContent />
        </Suspense>
    );
}
