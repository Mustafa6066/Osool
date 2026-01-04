import EliteAdvisorChat from "@/components/EliteAdvisorChat";

export default function Home() {
  return (
    <main className="min-h-screen relative overflow-hidden flex items-center justify-center p-4">
      {/* Background Decor */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-gold/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-teal/10 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl w-full grid md:grid-cols-2 gap-12 items-center relative z-10">
        {/* Left Side: Hero Text */}
        <div className="text-right space-y-8 md:order-2">
          <h1 className="text-5xl md:text-7xl font-bold leading-tight">
            <span className="text-white block">مستقبل العقارات</span>
            <span className="text-gold-gradient block mt-2">بين يديك</span>
          </h1>
          <p className="text-white/70 text-lg md:text-xl leading-relaxed max-w-xl ml-auto">
            أصول تقدم لك تجربة استثمار عقاري فاخرة مدعومة بالذكاء الاصطناعي.
            احصل على استشارات دقيقة، وتحليلات استثمارية، وعقارات موثوقة عبر الـ Blockchain.
          </p>

          <div className="flex gap-4 justify-end">
            <button className="px-8 py-3 rounded-full bg-transparent border border-gold text-gold hover:bg-gold/10 transition-colors">
              اكتشف المزيد
            </button>
            <button className="px-8 py-3 rounded-full bg-gold text-navy font-bold hover:shadow-lg hover:shadow-gold/20 transition-all">
              ابدأ الآن
            </button>
          </div>
        </div>

        {/* Right Side: AI Chat Demo */}
        <div className="md:order-1 flex justify-center">
          <EliteAdvisorChat />
        </div>
      </div>
    </main>
  );
}
