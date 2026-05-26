'use client';

import { useState } from 'react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import { Mail, Phone, MapPin, Send, MessageCircle } from 'lucide-react';

export default function ContactPage() {
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // TODO: wire to backend API when available
    setSubmitted(true);
  };

  return (
    <AppShell>
      <div className="h-full overflow-y-auto bg-[var(--color-background)]" dir={isRTL ? 'rtl' : 'ltr'}>
        <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 sm:py-14">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_80px_rgba(0,0,0,0.04)] sm:p-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
              <MessageCircle className="h-3.5 w-3.5" />
              {isRTL ? 'تواصل' : 'Contact'}
            </div>
            <h1 className="mt-5 text-3xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
              {isRTL ? 'اتصل بنا' : 'Contact Us'}
            </h1>
            <p className="mt-2 text-[var(--color-text-secondary)]">
              {isRTL
                ? 'نحن هنا لمساعدتك في رحلتك العقارية في مصر.'
                : 'We\'re here to help with your Egyptian real estate journey.'}
            </p>

            <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_1.2fr]">
              {/* Contact Info */}
              <div className="space-y-6">
                <ContactCard
                  icon={<Mail className="h-5 w-5" />}
                  label={isRTL ? 'البريد الإلكتروني' : 'Email'}
                  value="hello@osool.ai"
                  href="mailto:hello@osool.ai"
                />
                <ContactCard
                  icon={<Phone className="h-5 w-5" />}
                  label={isRTL ? 'الهاتف' : 'Phone'}
                  value="+20 100 000 0000"
                  href="tel:+201000000000"
                />
                <ContactCard
                  icon={<MapPin className="h-5 w-5" />}
                  label={isRTL ? 'الموقع' : 'Location'}
                  value={isRTL ? 'القاهرة، مصر' : 'Cairo, Egypt'}
                />
              </div>

              {/* Contact Form */}
              {submitted ? (
                <div className="flex flex-col items-center justify-center rounded-[28px] border border-emerald-500/20 bg-emerald-500/5 p-8 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
                    <Send className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <p className="mt-4 text-lg font-semibold text-[var(--color-text-primary)]">
                    {isRTL ? 'تم الإرسال!' : 'Message Sent!'}
                  </p>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
                    {isRTL ? 'سنتواصل معك قريبًا.' : 'We\'ll get back to you shortly.'}
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-[var(--color-text-primary)]">
                      {isRTL ? 'الاسم' : 'Name'}
                    </label>
                    <input
                      id="name"
                      name="name"
                      type="text"
                      required
                      className="mt-1 block w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2.5 text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      placeholder={isRTL ? 'اسمك الكامل' : 'Your full name'}
                    />
                  </div>
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-[var(--color-text-primary)]">
                      {isRTL ? 'البريد الإلكتروني' : 'Email'}
                    </label>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      required
                      className="mt-1 block w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2.5 text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      placeholder={isRTL ? 'بريدك الإلكتروني' : 'your@email.com'}
                    />
                  </div>
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-[var(--color-text-primary)]">
                      {isRTL ? 'الرسالة' : 'Message'}
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      required
                      rows={4}
                      className="mt-1 block w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2.5 text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 resize-none"
                      placeholder={isRTL ? 'كيف يمكننا مساعدتك؟' : 'How can we help you?'}
                    />
                  </div>
                  <button
                    type="submit"
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                  >
                    <Send className="h-4 w-4" />
                    {isRTL ? 'إرسال الرسالة' : 'Send Message'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function ContactCard({ icon, label, value, href }: { icon: React.ReactNode; label: string; value: string; href?: string }) {
  const content = (
    <div className="flex items-start gap-4 rounded-[20px] border border-[var(--color-border)] bg-[var(--color-background)] p-4 transition-colors hover:bg-[var(--color-surface-elevated)]">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
        {icon}
      </div>
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-[var(--color-text-secondary)]">{label}</p>
        <p className="mt-0.5 text-sm font-semibold text-[var(--color-text-primary)]">{value}</p>
      </div>
    </div>
  );
  return href ? <a href={href}>{content}</a> : content;
}
