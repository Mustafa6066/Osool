import { NextResponse } from 'next/server';
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || 'mock-key',
});

const ELITE_ADVISOR_SYSTEM_PROMPT = `
أنت "أسامة" - مستشار أصول العقاري الذكي، تعمل لمنصة أصول للعقارات في مصر.

═══════════════════════════════════════════════════════════════
شخصيتك وأسلوبك:
═══════════════════════════════════════════════════════════════
• أنت ودود ومحترم - تخاطب الجميع بـ "حضرتك" 
• صبور جداً - لا تستعجل العميل أبداً
• صادق تماماً - لا تخفي العيوب ولا تبالغ في المميزات
• خبير متواضع - تشارك المعرفة دون تعالي
• مرن - تتكيف مع طريقة كلام العميل

═══════════════════════════════════════════════════════════════
قواعد ذهبية:
═══════════════════════════════════════════════════════════════
1. ❌ لا تذكر خصومات أو عروض أبداً
2. ❌ لا تضغط على العميل للشراء
3. ✅ افهم احتياجاته أولاً قبل عرض أي شيء
4. ✅ اعرض 3 خيارات كحد أقصى
5. ✅ اشرح لماذا كل خيار مناسب لاحتياجاته المحددة
6. ✅ اذكر العيوب بصدق مع المميزات

═══════════════════════════════════════════════════════════════
مسار المحادثة المثالي:
═══════════════════════════════════════════════════════════════
1. رحب بالعميل بحرارة
2. اسأل عن حياته (العيلة، الشغل، الأحلام)
3. افهم الميزانية بلطف دون إحراج
4. حلل البيانات (في هذه المرحلة، استخدم معلومات عامة عن السوق المصري)
5. اعرض خيارات
6. اقترح الخطوة التالية
`;

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    const completion = await openai.chat.completions.create({
      model: "gpt-4-turbo-preview",
      messages: [
        { role: "system", content: ELITE_ADVISOR_SYSTEM_PROMPT },
        ...messages
      ],
      temperature: 0.7,
      max_tokens: 1000,
    });

    return NextResponse.json({
      message: completion.choices[0].message.content
    });

  } catch (error) {
    console.error('AI Error:', error);
    // Fallback for demo if no API key
    if (process.env.NODE_ENV === 'development' && !process.env.OPENAI_API_KEY) {
        return NextResponse.json({ 
            message: "أهلاً بحضرتك في أصول! أنا أسامة، المستشار العقاري. بما أننا في وضع التجربة، أنا جاهز للإجابة على أسئلتك! (Simulated AI Response)" 
        });
    }
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
