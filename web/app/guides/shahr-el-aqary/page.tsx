import type { Metadata } from 'next';
import Link from 'next/link';
import AppShell from '@/components/nav/AppShell';

export const revalidate = 86400; // static content, refresh daily

export const metadata: Metadata = {
  title: 'دليل الشهر العقاري: خطوات تسجيل العقار في مصر | Osool',
  description:
    'دليل عملي خطوة بخطوة لتسجيل عقارك في الشهر العقاري في مصر: المستندات المطلوبة، الرسوم، صحة التوقيع، ودعوى صحة ونفاذ — بالعربي والإنجليزي.',
  alternates: { canonical: '/guides/shahr-el-aqary' },
};

const STEPS = [
  {
    ar: 'اجمع مستندات الملكية: عقد البيع الابتدائي، سند ملكية البائع (عقد مسجل أو حكم صحة ونفاذ)، وكشف رسمي حديث من الشهر العقاري.',
    en: 'Gather ownership documents: the preliminary sale contract, the seller’s title (registered deed or a validity judgment), and a recent official extract from the registry.',
  },
  {
    ar: 'تأكد من تسلسل الملكية: كل بائع في السلسلة لازم يكون مالكًا قانونيًا — أي حلقة مكسورة بتعطل التسجيل.',
    en: 'Verify the chain of title: every seller in the chain must be a legal owner — one broken link blocks registration.',
  },
  {
    ar: 'قدّم طلب الشهر بمكتب الشهر العقاري المختص جغرافيًا بالعقار، وادفع رسوم الفحص.',
    en: 'File the registration application at the registry office covering the property’s district and pay the examination fee.',
  },
  {
    ar: 'يفحص المكتب المستندات ويصدر مطالبة بالرسوم النهائية (سقفها القانوني محدد بحد أقصى حسب شرائح المساحة).',
    en: 'The office examines the documents and issues the final fee demand (legally capped by area brackets).',
  },
  {
    ar: 'وقّع العقد النهائي أمام الموظف المختص، وبعد الشهر تستلم نسختك المسجلة — دي الحماية القانونية الكاملة لملكيتك.',
    en: 'Sign the final deed before the registrar; after registration you receive your recorded copy — full legal protection of your ownership.',
  },
];

const FEES = [
  { bracket: { ar: 'حتى ١٠٠ م²', en: 'Up to 100 m²' }, fee: { ar: '٥٠٠ جنيه', en: 'EGP 500' } },
  { bracket: { ar: '١٠١–٢٠٠ م²', en: '101–200 m²' }, fee: { ar: '١٠٠٠ جنيه', en: 'EGP 1,000' } },
  { bracket: { ar: '٢٠١–٣٠٠ م²', en: '201–300 m²' }, fee: { ar: '١٥٠٠ جنيه', en: 'EGP 1,500' } },
  { bracket: { ar: 'أكثر من ٣٠٠ م²', en: 'Over 300 m²' }, fee: { ar: '٢٠٠٠ جنيه', en: 'EGP 2,000' } },
];

const FAQS = [
  {
    q: 'هل عقد البيع الابتدائي يحمي ملكيتي؟',
    a: 'العقد الابتدائي ينقل حق شخصي وليس عيني — الملكية القانونية الكاملة لا تنتقل إلا بالتسجيل في الشهر العقاري أو حكم صحة ونفاذ مسجل.',
  },
  {
    q: 'ما الفرق بين صحة التوقيع وصحة ونفاذ؟',
    a: 'صحة التوقيع تثبت فقط أن التوقيع صادر من البائع، ولا تنقل الملكية. دعوى صحة ونفاذ حكمها قابل للتسجيل وينقل الملكية بعد شهره.',
  },
  {
    q: 'كم تستغرق إجراءات التسجيل؟',
    a: 'تختلف حسب اكتمال المستندات وسلامة سلسلة الملكية؛ عمليًا من عدة أسابيع إلى عدة أشهر. اكتمال الأوراق من أول مرة يختصر الوقت كثيرًا.',
  },
  {
    q: 'هل وحدات المطورين في المدن الجديدة تُسجل بنفس الطريقة؟',
    a: 'وحدات هيئة المجتمعات العمرانية الجديدة تمر بمسار تخصيص وتسجيل خاص عبر الهيئة قبل الشهر العقاري — اسأل المطور عن موقف الأرض والتسجيل قبل التعاقد.',
  },
];

const faqJsonLd = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: FAQS.map((f) => ({
    '@type': 'Question',
    name: f.q,
    acceptedAnswer: { '@type': 'Answer', text: f.a },
  })),
};

export default function ShahrElAqaryGuidePage() {
  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
        />
        <article dir="rtl" className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
            دليل مجاني
          </div>
          <h1 className="mt-5 text-3xl font-bold tracking-tight sm:text-4xl">
            الشهر العقاري: إزاي تسجل عقارك في مصر خطوة بخطوة
          </h1>
          <p className="mt-3 text-lg leading-relaxed text-[var(--color-text-secondary)]">
            التسجيل في الشهر العقاري هو الحماية القانونية الوحيدة الكاملة لملكيتك — وبيمنع
            أخطر مشكلة في السوق المصري: بيع نفس الوحدة مرتين. الدليل ده بيشرح المستندات
            والرسوم والخطوات بالتفصيل.
          </p>

          <h2 className="mt-10 text-2xl font-semibold">الخطوات</h2>
          <ol className="mt-4 space-y-4">
            {STEPS.map((step, i) => (
              <li key={i} className="flex gap-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-sm font-bold text-white">
                  {i + 1}
                </span>
                <div>
                  <p className="leading-relaxed">{step.ar}</p>
                  <p dir="ltr" className="mt-2 text-sm leading-relaxed text-[var(--color-text-muted)]">
                    {step.en}
                  </p>
                </div>
              </li>
            ))}
          </ol>

          <h2 className="mt-10 text-2xl font-semibold">رسوم التسجيل (قانون ١٨٦ لسنة ٢٠٢٠)</h2>
          <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
            رسوم مقطوعة حسب مساحة الوحدة — وليست نسبة من الثمن:
          </p>
          <div className="mt-4 overflow-hidden rounded-2xl border border-[var(--color-border)]">
            <table className="w-full text-sm">
              <thead className="bg-[var(--color-surface)] text-start">
                <tr>
                  <th className="px-4 py-3 text-start font-semibold">المساحة</th>
                  <th className="px-4 py-3 text-start font-semibold">الرسم</th>
                </tr>
              </thead>
              <tbody>
                {FEES.map((row, i) => (
                  <tr key={i} className="border-t border-[var(--color-border)]">
                    <td className="px-4 py-3">{row.bracket.ar} <span dir="ltr" className="text-[var(--color-text-muted)]">({row.bracket.en})</span></td>
                    <td className="px-4 py-3">{row.fee.ar} <span dir="ltr" className="text-[var(--color-text-muted)]">({row.fee.en})</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 className="mt-10 text-2xl font-semibold">أسئلة شائعة</h2>
          <div className="mt-4 space-y-3">
            {FAQS.map((faq, i) => (
              <details key={i} className="group rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                <summary className="cursor-pointer font-semibold marker:content-none">
                  {faq.q}
                </summary>
                <p className="mt-3 leading-relaxed text-[var(--color-text-secondary)]">{faq.a}</p>
              </details>
            ))}
          </div>

          <div className="mt-10 rounded-2xl border border-emerald-500/30 bg-emerald-500/[0.06] p-6">
            <h2 className="text-xl font-semibold">قبل ما تشتري أصلاً…</h2>
            <p className="mt-2 leading-relaxed text-[var(--color-text-secondary)]">
              اتأكد إن سعر الوحدة عادل وإن العرض مش فيه فخاخ تمويل مخفية. مستشار أصول الذكي
              بيفحص عرضك مجانًا في دقيقة.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Link
                href="/chat"
                className="rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-600"
              >
                افحص عرضك مجانًا
              </Link>
              <Link
                href="/tools/mortgage"
                className="rounded-2xl border border-[var(--color-border)] px-5 py-3 text-sm font-semibold"
              >
                حاسبة التمويل العقاري
              </Link>
            </div>
          </div>

          <p className="mt-8 text-xs leading-relaxed text-[var(--color-text-muted)]">
            هذا الدليل للتوعية العامة وليس استشارة قانونية. الرسوم والإجراءات تتغير بقرارات
            رسمية — راجع مكتب الشهر العقاري المختص أو محاميك قبل التعاقد. آخر مراجعة: يونيو ٢٠٢٦.
          </p>
        </article>
      </main>
    </AppShell>
  );
}
