'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MessageCircle, Phone, Send, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

interface WhatsAppHandoffModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** Pre-filled context (property name, chat summary, etc.) */
  context?: {
    propertyTitle?: string;
    propertyLocation?: string;
    propertyPrice?: string;
    chatSummary?: string;
  };
}

const WA_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '201000000000';

export default function WhatsAppHandoffModal({ isOpen, onClose, context }: WhatsAppHandoffModalProps) {
  const { t, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [note, setNote] = useState('');
  const [step, setStep] = useState<'form' | 'sent'>('form');

  const overlayRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Build the WhatsApp message
  const buildMessage = useCallback(() => {
    const parts: string[] = [];
    if (context?.propertyTitle) {
      parts.push(`🏠 ${context.propertyTitle}`);
      if (context.propertyLocation) parts.push(`📍 ${context.propertyLocation}`);
      if (context.propertyPrice) parts.push(`💰 ${context.propertyPrice}`);
    }
    if (name) parts.push(`👤 ${name}`);
    if (phone) parts.push(`📞 ${phone}`);
    if (note) parts.push(`💬 ${note}`);
    if (context?.chatSummary) parts.push(`\n🤖 ${t('whatsapp.fromChat')}: ${context.chatSummary}`);
    return parts.join('\n');
  }, [context, name, phone, note, t]);

  const handleSend = () => {
    const message = encodeURIComponent(buildMessage());
    window.open(`https://wa.me/${WA_NUMBER}?text=${message}`, '_blank', 'noopener,noreferrer');
    setStep('sent');
  };

  // Reset on close
  useEffect(() => {
    if (!isOpen) {
      const timer = setTimeout(() => {
        setStep('form');
        setName('');
        setPhone('');
        setNote('');
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Focus trap + Escape key
  useEffect(() => {
    if (!isOpen) return;

    // Focus first input on open
    const timer = setTimeout(() => firstInputRef.current?.focus(), 100);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      // Trap focus within modal
      if (e.key === 'Tab') {
        const focusable = overlayRef.current?.querySelectorAll<HTMLElement>(
          'input, button, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (!focusable || focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    return () => {
      clearTimeout(timer);
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={overlayRef}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
          role="dialog"
          aria-modal="true"
          aria-label={t('whatsapp.title')}
          onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="w-full max-w-md rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] shadow-2xl overflow-hidden"
            dir={isRTL ? 'rtl' : 'ltr'}
          >
            {/* Header */}
            <div className="flex items-center justify-between gap-3 border-b border-[var(--color-border)] px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#25D366]/15">
                  <MessageCircle className="h-5 w-5 text-[#25D366]" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
                    {t('whatsapp.title')}
                  </h2>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    {t('whatsapp.subtitle')}
                  </p>
                </div>
              </div>
              <button
                ref={closeButtonRef}
                onClick={onClose}
                aria-label={t('whatsapp.close')}
                className="rounded-full p-2 text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-background)] hover:text-[var(--color-text-primary)]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {step === 'form' ? (
              <div className="px-6 py-5 space-y-4">
                {/* Property context preview */}
                {context?.propertyTitle && (
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-1">
                      {t('whatsapp.regarding')}
                    </p>
                    <p className="text-sm font-semibold text-[var(--color-text-primary)]">{context.propertyTitle}</p>
                    {context.propertyLocation && (
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{context.propertyLocation}</p>
                    )}
                    {context.propertyPrice && (
                      <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5">{context.propertyPrice}</p>
                    )}
                  </div>
                )}

                {/* Name */}
                <div>
                  <label htmlFor="wa-name" className="block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">
                    {t('whatsapp.name')}
                  </label>
                  <input
                    ref={firstInputRef}
                    id="wa-name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={t('whatsapp.namePlaceholder')}
                    className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2.5 text-sm text-[var(--color-text-primary)] outline-none transition-colors focus-visible:border-[var(--color-primary)]/50 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/20"
                    autoComplete="name"
                  />
                </div>

                {/* Phone */}
                <div>
                  <label htmlFor="wa-phone" className="block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">
                    {t('whatsapp.phone')}
                  </label>
                  <div className="relative">
                    <Phone className={`absolute top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)] ${isRTL ? 'right-3' : 'left-3'}`} />
                    <input
                      id="wa-phone"
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder={t('whatsapp.phonePlaceholder')}
                      className={`w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] py-2.5 text-sm text-[var(--color-text-primary)] outline-none transition-colors focus-visible:border-[var(--color-primary)]/50 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/20 ${isRTL ? 'pr-10 pl-4' : 'pl-10 pr-4'}`}
                      autoComplete="tel"
                      dir="ltr"
                    />
                  </div>
                </div>

                {/* Note */}
                <div>
                  <label htmlFor="wa-note" className="block text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">
                    {t('whatsapp.note')}
                  </label>
                  <textarea
                    id="wa-note"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder={t('whatsapp.notePlaceholder')}
                    rows={2}
                    className="w-full rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2.5 text-sm text-[var(--color-text-primary)] outline-none transition-colors focus-visible:border-[var(--color-primary)]/50 focus-visible:ring-2 focus-visible:ring-[var(--color-primary)]/20 resize-none"
                  />
                </div>

                {/* Send button */}
                <button
                  onClick={handleSend}
                  className="w-full flex items-center justify-center gap-2 rounded-full bg-[#25D366] px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#1ebe5c] active:bg-[#1aa84f]"
                >
                  <Send className="h-4 w-4" />
                  {t('whatsapp.sendBtn')}
                </button>

                <p className="text-center text-[10px] text-[var(--color-text-muted)] leading-relaxed">
                  {t('whatsapp.disclaimer')}
                </p>
              </div>
            ) : (
              /* Success state */
              <div className="px-6 py-10 text-center space-y-4">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[#25D366]/15">
                  <CheckCircle2 className="h-8 w-8 text-[#25D366]" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">
                  {t('whatsapp.sentTitle')}
                </h3>
                <p className="text-sm text-[var(--color-text-secondary)] max-w-xs mx-auto">
                  {t('whatsapp.sentDesc')}
                </p>
                <button
                  onClick={onClose}
                  className="inline-flex rounded-full border border-[var(--color-border)] px-5 py-2.5 text-sm font-semibold text-[var(--color-text-primary)] transition-colors hover:bg-[var(--color-background)]"
                >
                  {t('whatsapp.done')}
                </button>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
