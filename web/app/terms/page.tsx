'use client';

import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import { Scale } from 'lucide-react';

export default function TermsPage() {
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';

  return (
    <AppShell>
      <div className="h-full overflow-y-auto bg-[var(--color-background)]" dir={isRTL ? 'rtl' : 'ltr'}>
        <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 shadow-[0_30px_80px_rgba(0,0,0,0.04)] sm:p-10">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
              <Scale className="h-3.5 w-3.5" />
              {isRTL ? 'قانوني' : 'Legal'}
            </div>
            <h1 className="mt-5 text-3xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
              {isRTL ? 'شروط الخدمة' : 'Terms of Service'}
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              {isRTL ? 'آخر تحديث: يوليو ٢٠٢٥' : 'Last updated: July 2025'}
            </p>

            <div className="mt-8 space-y-8 text-[var(--color-text-secondary)] leading-relaxed">
              <Section
                title={isRTL ? '١. قبول الشروط' : '1. Acceptance of Terms'}
                content={isRTL
                  ? 'باستخدام منصة أصول، فإنك توافق على الالتزام بهذه الشروط. إذا كنت لا توافق، يُرجى عدم استخدام المنصة.'
                  : 'By using the Osool platform, you agree to be bound by these terms. If you do not agree, please do not use the platform.'}
              />
              <Section
                title={isRTL ? '٢. وصف الخدمة' : '2. Service Description'}
                content={isRTL
                  ? 'أصول منصة عقارية مدعومة بالذكاء الاصطناعي توفر معلومات السوق، تحليل الأسعار، مقارنات المطورين، وتوصيات الاستثمار للسوق العقاري المصري. المنصة ليست مستشارًا ماليًا مرخصًا.'
                  : 'Osool is an AI-powered real estate platform providing market intelligence, price analysis, developer comparisons, and investment recommendations for the Egyptian real estate market. The platform is not a licensed financial advisor.'}
              />
              <Section
                title={isRTL ? '٣. حسابات المستخدمين' : '3. User Accounts'}
                content={isRTL
                  ? 'أنت مسؤول عن الحفاظ على سرية بيانات حسابك. يجب أن تكون المعلومات المقدمة دقيقة وحديثة. نحتفظ بالحق في تعليق أو إنهاء الحسابات التي تنتهك هذه الشروط.'
                  : 'You are responsible for maintaining the confidentiality of your account credentials. Information provided must be accurate and current. We reserve the right to suspend or terminate accounts that violate these terms.'}
              />
              <Section
                title={isRTL ? '٤. إخلاء المسؤولية عن الذكاء الاصطناعي' : '4. AI Disclaimer'}
                content={isRTL
                  ? 'تحليلات الذكاء الاصطناعي والتوصيات المقدمة هي لأغراض إعلامية فقط ولا تشكل نصيحة مالية أو قانونية. الأداء السابق لا يضمن النتائج المستقبلية. استشر متخصصين مؤهلين قبل اتخاذ قرارات الاستثمار.'
                  : 'AI analyses and recommendations are for informational purposes only and do not constitute financial or legal advice. Past performance does not guarantee future results. Consult qualified professionals before making investment decisions.'}
              />
              <Section
                title={isRTL ? '٥. الملكية الفكرية' : '5. Intellectual Property'}
                content={isRTL
                  ? 'جميع المحتويات والتكنولوجيا والعلامات التجارية على منصة أصول مملوكة لنا أو مرخصة لنا. لا يجوز نسخ أو توزيع أو تعديل أي محتوى دون إذن كتابي مسبق.'
                  : 'All content, technology, and trademarks on the Osool platform are owned by or licensed to us. No content may be copied, distributed, or modified without prior written permission.'}
              />
              <Section
                title={isRTL ? '٦. الامتثال التنظيمي' : '6. Regulatory Compliance'}
                content={isRTL
                  ? 'جميع المعاملات على المنصة تلتزم بقانون البنك المركزي المصري رقم ١٩٤/٢٠٢٠ (المدفوعات بالجنيه المصري عبر InstaPay/Fawry)، قرار الهيئة العامة للرقابة المالية رقم ١٢٥/٢٠٢٥ (الملكية الجزئية)، والقانون المدني المصري ١٣١.'
                  : 'All transactions on the platform comply with CBE Law 194/2020 (EGP-only payments via InstaPay/Fawry), FRA Decision 125/2025 (fractional ownership), and Egyptian Civil Code 131.'}
              />
              <Section
                title={isRTL ? '٧. تحديد المسؤولية' : '7. Limitation of Liability'}
                content={isRTL
                  ? 'أصول غير مسؤولة عن أي خسائر ناتجة عن قرارات استثمارية مبنية على معلومات المنصة. المنصة تقدم أدوات تحليلية فقط ولا تضمن دقة البيانات أو نتائج الاستثمار.'
                  : 'Osool is not liable for any losses resulting from investment decisions based on platform information. The platform provides analytical tools only and does not guarantee data accuracy or investment outcomes.'}
              />
              <Section
                title={isRTL ? '٨. القانون الحاكم' : '8. Governing Law'}
                content={isRTL
                  ? 'تخضع هذه الشروط وتُفسر وفقًا لقوانين جمهورية مصر العربية. أي نزاع ينشأ عن هذه الشروط يخضع للاختصاص الحصري للمحاكم المصرية.'
                  : 'These terms are governed by and construed in accordance with the laws of the Arab Republic of Egypt. Any disputes arising from these terms are subject to the exclusive jurisdiction of Egyptian courts.'}
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
