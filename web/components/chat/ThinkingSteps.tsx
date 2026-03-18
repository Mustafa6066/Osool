'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Search, MapPin, Sparkles, BarChart2, Shield, MessageSquare, Check,
} from 'lucide-react';
import { AgentAvatar } from '@/components/chat/ChatMessage';
import { isArabic } from '@/lib/chat-utils';

interface ThinkingStep {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  duration: number;
}

export default function ThinkingSteps({ lastUserMessage }: { lastUserMessage: string }) {
  const [visibleSteps, setVisibleSteps] = useState(0);
  const msgIsArabic = isArabic(lastUserMessage);

  const steps = useMemo(() => {
    const content = (lastUserMessage || '').toLowerCase();
    const baseSteps: ThinkingStep[] = [];

    if (msgIsArabic) {
      baseSteps.push({ label: 'تحليل الطلب...', icon: Search, duration: 1200 });
      if (content.includes('عقار') || content.includes('شقة') || content.includes('فيلا') || content.includes('سعر')) {
        baseSteps.push({ label: 'البحث في قاعدة العقارات...', icon: MapPin, duration: 3000 });
        baseSteps.push({ label: 'تصفية أفضل الخيارات...', icon: Sparkles, duration: 5000 });
      } else if (content.includes('استثمار') || content.includes('عائد') || content.includes('roi') || content.includes('تضخم') || content.includes('فلوس')) {
        baseSteps.push({ label: 'تحليل بيانات الاستثمار...', icon: BarChart2, duration: 3000 });
        baseSteps.push({ label: 'حساب العوائد المتوقعة...', icon: BarChart2, duration: 5000 });
      } else if (content.includes('مطور') || content.includes('شركة') || content.includes('تسليم')) {
        baseSteps.push({ label: 'فحص سجل المطورين...', icon: Shield, duration: 3000 });
        baseSteps.push({ label: 'تقييم المخاطر...', icon: BarChart2, duration: 5000 });
      } else {
        baseSteps.push({ label: 'فحص بيانات السوق...', icon: BarChart2, duration: 3000 });
        baseSteps.push({ label: 'استخراج الأفكار والتوصيات...', icon: Sparkles, duration: 5000 });
      }
      baseSteps.push({ label: 'صياغة الرد...', icon: MessageSquare, duration: 7500 });
    } else {
      baseSteps.push({ label: 'Understanding request...', icon: Search, duration: 1200 });
      if (content.includes('property') || content.includes('apartment') || content.includes('villa') || content.includes('price')) {
        baseSteps.push({ label: 'Scanning properties inventory...', icon: MapPin, duration: 3000 });
        baseSteps.push({ label: 'Filtering best matches...', icon: Sparkles, duration: 5000 });
      } else if (content.includes('invest') || content.includes('roi') || content.includes('yield') || content.includes('inflation') || content.includes('money')) {
        baseSteps.push({ label: 'Analyzing investment data...', icon: BarChart2, duration: 3000 });
        baseSteps.push({ label: 'Calculating projected returns...', icon: BarChart2, duration: 5000 });
      } else if (content.includes('developer') || content.includes('company') || content.includes('delivery')) {
        baseSteps.push({ label: 'Auditing developer record...', icon: Shield, duration: 3000 });
        baseSteps.push({ label: 'Evaluating risk factors...', icon: BarChart2, duration: 5000 });
      } else {
        baseSteps.push({ label: 'Scanning market trends...', icon: BarChart2, duration: 3000 });
        baseSteps.push({ label: 'Extracting insights...', icon: Sparkles, duration: 5000 });
      }
      baseSteps.push({ label: 'Drafting response...', icon: MessageSquare, duration: 7500 });
    }
    return baseSteps;
  }, [lastUserMessage, msgIsArabic]);

  useEffect(() => {
    const resetTimer = window.setTimeout(() => setVisibleSteps(0), 0);
    const timers = steps.map((step, i) =>
      window.setTimeout(() => setVisibleSteps(i + 1), step.duration)
    );
    return () => {
      window.clearTimeout(resetTimer);
      timers.forEach(window.clearTimeout);
    };
  }, [steps]);

  return (
    <div className="flex gap-4 mb-6 animate-fade-in" dir={msgIsArabic ? 'rtl' : 'ltr'}>
      <AgentAvatar thinking />
      <div className="flex-1 flex flex-col gap-2 pt-1">
        {steps.map((step, i) => {
          const Icon = step.icon;
          const isVisible = i < visibleSteps;
          const isCurrent = i === visibleSteps - 1;
          const isPending = i >= visibleSteps;

          if (isPending && i > visibleSteps) return null;

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: isVisible ? 1 : 0.4, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex items-center gap-2.5 text-[13px] ${
                isCurrent
                  ? 'text-emerald-600 dark:text-emerald-400 font-medium'
                  : isVisible
                    ? 'text-[var(--color-text-muted)]'
                    : 'text-[var(--color-text-muted)]/40'
              }`}
            >
              {isCurrent ? (
                <div className="w-4 h-4 rounded-full border-2 border-emerald-500/30 border-t-emerald-500 animate-spin flex-shrink-0" />
              ) : isVisible ? (
                <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
              ) : (
                <Icon className="w-4 h-4 flex-shrink-0 opacity-40" />
              )}
              <span>{step.label}</span>
            </motion.div>
          );
        })}

        {visibleSteps === 0 && (
          <div className="flex items-center gap-1.5 pt-1">
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '0ms' }} />
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '150ms' }} />
            <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-text-muted)] animate-pulse" style={{ animationDelay: '300ms' }} />
          </div>
        )}
      </div>
    </div>
  );
}
