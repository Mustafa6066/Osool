'use client';

import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import { Shield } from 'lucide-react';

export default function PrivacyPage() {
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';

  return (
    <AppShell>
      <div className="h-full overflow-y-auto bg-[var(--color-background)]" dir={isRTL ? 'rtl' : 'ltr'}>
        <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_80px_rgba(0,0,0,0.04)] sm:p-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
              <Shield className="h-3.5 w-3.5" />
              {isRTL ? 'الخصوصية' : 'Privacy'}
            </div>
            <h1 className="mt-5 text-3xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
              {isRTL ? 'سياسة الخصوصية' : 'Privacy Policy'}
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              {isRTL ? 'آخر تحديث: يوليو ٢٠٢٥' : 'Last updated: July 2025'}
            </p>

            <div className="mt-8 space-y-8 text-[var(--color-text-secondary)] leading-relaxed">
              <Section
                title={isRTL ? '١. المعلومات التي نجمعها' : '1. Information We Collect'}
                content={isRTL
                  ? 'نجمع المعلومات التي تقدمها مباشرة عند استخدام منصة أصول، بما في ذلك: اسمك، بريدك الإلكتروني، رقم هاتفك، وتفضيلاتك العقارية. كما نجمع بيانات الاستخدام تلقائيًا مثل عنوان IP ونوع المتصفح وصفحات الزيارة.'
                  : 'We collect information you provide directly when using the Osool platform, including: your name, email address, phone number, and property preferences. We also automatically collect usage data such as IP address, browser type, and pages visited.'}
              />
              <Section
                title={isRTL ? '٢. كيف نستخدم معلوماتك' : '2. How We Use Your Information'}
                content={isRTL
                  ? 'نستخدم معلوماتك لتقديم توصيات عقارية مخصصة عبر الذكاء الاصطناعي، تحليل السوق والتقييم، التواصل معك بشأن استفساراتك العقارية، وتحسين خدماتنا.'
                  : 'We use your information to provide AI-powered personalized property recommendations, market analysis and valuation, communication regarding your property inquiries, and improvement of our services.'}
              />
              <Section
                title={isRTL ? '٣. معالجة الذكاء الاصطناعي' : '3. AI Processing'}
                content={isRTL
                  ? 'تستخدم منصة أصول نماذج الذكاء الاصطناعي (Claude وGPT-4o وXGBoost) لتحليل بيانات السوق وتقديم التوصيات. بيانات المحادثة تُعالج لتحسين تجربتك ولا تُستخدم لتدريب نماذج خارجية.'
                  : 'Osool uses AI models (Claude, GPT-4o, and XGBoost) to analyze market data and provide recommendations. Conversation data is processed to improve your experience and is not used to train external models.'}
              />
              <Section
                title={isRTL ? '٤. أمن البيانات' : '4. Data Security'}
                content={isRTL
                  ? 'نطبق تدابير أمنية متعددة لحماية بياناتك، بما في ذلك التشفير أثناء النقل والتخزين، المصادقة الآمنة عبر JWT، والتحقق من الهوية بخطوتين.'
                  : 'We implement multiple security measures to protect your data, including encryption in transit and at rest, secure JWT authentication, and two-factor identity verification.'}
              />
              <Section
                title={isRTL ? '٥. حقوقك' : '5. Your Rights'}
                content={isRTL
                  ? 'يحق لك الوصول إلى بياناتك الشخصية، تصحيحها، حذفها، أو تقييد معالجتها. للممارسة هذه الحقوق، تواصل معنا عبر صفحة الاتصال.'
                  : 'You have the right to access, correct, delete, or restrict processing of your personal data. To exercise these rights, contact us through our contact page.'}
              />
              <Section
                title={isRTL ? '٦. الامتثال القانوني' : '6. Legal Compliance'}
                content={isRTL
                  ? 'تلتزم أصول بقانون البنك المركزي المصري رقم ١٩٤ لسنة ٢٠٢٠ (المدفوعات بالجنيه المصري فقط)، وقرار هيئة الرقابة المالية رقم ١٢٥ لسنة ٢٠٢٥ (الملكية الجزئية)، والقانون المدني المصري ١٣١.'
                  : 'Osool complies with CBE Law 194/2020 (EGP-only payments), FRA Decision 125/2025 (fractional ownership), and Egyptian Civil Code 131.'}
              />
              <Section
                title={isRTL ? '٧. التواصل' : '7. Contact'}
                content={isRTL
                  ? 'لأي أسئلة حول سياسة الخصوصية، تواصل معنا على privacy@osool.ai'
                  : 'For any questions about this privacy policy, contact us at privacy@osool.ai'}
              />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Section({ title, content }: { title: string; content: string }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">{title}</h2>
      <p className="mt-2">{content}</p>
    </div>
  );
}
