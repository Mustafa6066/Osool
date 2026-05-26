import os
import json
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import MarketingMaterial
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_openai_api_key = os.getenv("OPENAI_API_KEY")


def _get_openai_client():
    """Lazy-init OpenAI client so missing key doesn't crash on import."""
    from openai import AsyncOpenAI
    key = _openai_api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=key)

SEED_QUESTIONS = [
    {
        "category": "Investment Fundamentals",
        "question_en": "What's a reasonable down payment percentage for Egyptian real estate?",
        "question_ar": "ما هي نسبة الدفعة الأولى المعقولة للعقارات المصرية؟"
    },
    {
        "category": "Investment Fundamentals",
        "question_en": "How long does it typically take to deliver a property in Egypt?",
        "question_ar": "كم من الوقت يستغرق تسليم العقار عادة في مصر؟"
    },
    {
        "category": "Investment Fundamentals",
        "question_en": "What are the best neighborhoods to invest in around Cairo?",
        "question_ar": "ما هي أفضل الأحياء للاستثمار حول القاهرة؟"
    },
    {
        "category": "Investment Fundamentals",
        "question_en": "How does property appreciation work in Egypt's real estate market?",
        "question_ar": "كيف يعمل التقدير العقاري في سوق العقارات المصرية؟"
    },
    {
        "category": "Investment Fundamentals",
        "question_en": "What documents do I need to complete a property purchase in Egypt?",
        "question_ar": "ما هي المستندات التي أحتاجها لإتمام عملية شراء عقار في مصر؟"
    },
    {
        "category": "Financial Planning",
        "question_en": "What's the difference between rental yield and capital appreciation?",
        "question_ar": "ما الفرق بين العائد الإيجاري والتقدير الرأسمالي؟"
    },
    {
        "category": "Financial Planning",
        "question_en": "How does inflation affect property investment returns?",
        "question_ar": "كيف يؤثر التضخم على عوائد الاستثمار العقاري؟"
    },
    {
        "category": "Financial Planning",
        "question_en": "What's the current CBE interest rate and how does it impact real estate?",
        "question_ar": "ما هو سعر الفائدة الحالي للبنك المركزي المصري وكيف يؤثر على العقارات؟"
    },
    {
        "category": "Financial Planning",
        "question_en": "Should I invest in completed or under-construction properties?",
        "question_ar": "هل يجب أن أستثمر في عقارات مكتملة أم قيد الإنشاء؟"
    },
    {
        "category": "Financial Planning",
        "question_en": "How much liquidity do I need for a real estate investment?",
        "question_ar": "ما مقدار السيولة التي أحتاجها للاستثمار العقاري؟"
    },
    {
        "category": "Developer & Project Evaluation",
        "question_en": "How do I evaluate a developer's delivery track record?",
        "question_ar": "كيف أقيم السجل التسليمي للمطور؟"
    },
    {
        "category": "Developer & Project Evaluation",
        "question_en": "What makes a real estate project high-quality vs. mediocre?",
        "question_ar": "ما الذي يجعل المشروع العقاري عالي الجودة مقابل متوسط؟"
    },
    {
        "category": "Developer & Project Evaluation",
        "question_en": "Which Egyptian developers have the best payment flexibility?",
        "question_ar": "أي المطورين المصريين لديهم أفضل مرونة في الدفع؟"
    },
    {
        "category": "Developer & Project Evaluation",
        "question_en": "How do I compare two similar properties in different areas?",
        "question_ar": "كيف أقارن بين عقارين متشابهين في مناطق مختلفة؟"
    },
    {
        "category": "Developer & Project Evaluation",
        "question_en": "What's the average resale value retention for Egyptian compounds?",
        "question_ar": "ما هو متوسط الاحتفاظ بقيمة إعادة البيع للمجمعات المصرية؟"
    },
    {
        "category": "Market Trends & Timing",
        "question_en": "Is it a good time to buy property in Egypt right now?",
        "question_ar": "هل هذا الوقت المناسب لشراء العقارات في مصر الآن؟"
    },
    {
        "category": "Market Trends & Timing",
        "question_en": "How do geopolitical events affect Egyptian real estate prices?",
        "question_ar": "كيف تؤثر الأحداث الجيوسياسية على أسعار العقارات المصرية؟"
    },
    {
        "category": "Market Trends & Timing",
        "question_en": "What's the impact of currency fluctuations on property investment?",
        "question_ar": "ما هو تأثير تقلبات العملات على الاستثمار العقاري؟"
    },
    {
        "category": "Market Trends & Timing",
        "question_en": "How can I identify emerging neighborhoods before prices surge?",
        "question_ar": "كيف يمكنني تحديد الأحياء الناشئة قبل ارتفاع الأسعار؟"
    },
    {
        "category": "Market Trends & Timing",
        "question_en": "What's the difference between New Cairo, 6th of October, and North Coast investments?",
        "question_ar": "ما الفرق بين الاستثمارات في القاهرة الجديدة والقاهرة الجديدة والساحل الشمالي؟"
    },
    {
        "category": "Dual-Engine Capabilities",
        "question_en": "How do recent CBE policy changes and USD/EGP spreads impact my 5-year ROI forecast?",
        "question_ar": "كيف تؤثر تغييرات السياسة النقدية الحديثة للبنك المركزي المصري وفروقات الدولار/الجنيه على توقعات العائد على الاستثمار لمدة 5 سنوات؟"
    },
    {
        "category": "Dual-Engine Capabilities",
        "question_en": "How does Osool's AI cross-validate property valuations using both market data and geopolitical event modeling?",
        "question_ar": "كيف يتحقق ذكاء Osool من تقييمات العقارات باستخدام بيانات السوق ونمذجة الأحداث الجيوسياسية؟"
    },
    {
        "category": "Dual-Engine Capabilities",
        "question_en": "What's the predicted 5-year ROI for New Cairo villas given current inflation trajectories and regional stability assessments?",
        "question_ar": "ما هو العائد على الاستثمار المتوقع لمدة 5 سنوات لفلل القاهرة الجديدة مع مسارات التضخم الحالية وتقييمات الاستقرار الإقليمي؟"
    },
    {
        "category": "Dual-Engine Capabilities",
        "question_en": "How does Osool combine XGBoost price prediction with Claude-powered narrative analysis for property valuations?",
        "question_ar": "كيف يجمع Osool بين التنبؤ بالأسعار بواسطة XGBoost والتحليل السردي الذي تعتمده Claude لتقييمات العقارات؟"
    },
    {
        "category": "Dual-Engine Capabilities",
        "question_en": "If CBE rates drop 2%, parallel USD spreads widen, and a new metro station opens nearby, how does Osool recalculate my property's expected returns?",
        "question_ar": "إذا انخفضت أسعار البنك المركزي المصري بنسبة 2%، وتوسعت فروقات الدولار الموازي، وفُتحت محطة مترو جديدة بالقرب من العقار، كيف تعيد Osool حساب العائدات المتوقعة للعقار؟"
    },
    {
        "category": "Price Discovery",
        "question_en": "What is the lowest-priced apartment in Tagamoa (New Cairo)?",
        "question_ar": "قولي ايه اقل سعر شقه في التجمع"
    },
    {
        "category": "Price Discovery",
        "question_en": "What is the lowest-priced apartment in Mostakbal City?",
        "question_ar": "قولي ايه اقل سعر شقه في المستقبل"
    },
    {
        "category": "Price Discovery",
        "question_en": "What is the highest-value apartment in Tagamoa (New Cairo)?",
        "question_ar": "قولي ايه اعلى قيمه شقه في التجمع"
    },
    {
        "category": "Size & Space",
        "question_en": "What is the largest apartment available?",
        "question_ar": "قولي اكبر مساحه لشقه"
    },
    {
        "category": "Size & Space",
        "question_en": "What is the smallest villa available?",
        "question_ar": "قولي ايه اصغر مساحه لفيلا"
    }
]

# Once seeding succeeds, skip DB check on subsequent requests in the same process.
_questions_seeded = False

async def ensure_seeded_questions(db: AsyncSession) -> int:
    global _questions_seeded
    if _questions_seeded:
        return 0

    result = await db.execute(select(MarketingMaterial.question_en))
    existing_questions = set(result.scalars().all())

    created_count = 0
    for question in SEED_QUESTIONS:
        if question["question_en"] in existing_questions:
            continue

        db.add(
            MarketingMaterial(
                category=question["category"],
                question_ar=question["question_ar"],
                question_en=question["question_en"],
            )
        )
        existing_questions.add(question["question_en"])
        created_count += 1

    if created_count:
        await db.commit()

    _questions_seeded = True
    return created_count

async def generate_single_answer(question_en: str, question_ar: str, context_details: str) -> dict:
    prompt = f"""You are an expert real estate AI assistant for Osool, serving the Egyptian market. 
Please provide a professional, data-backed answer to the following question.

Use this market context to inform your answer:
{context_details}

Question (EN): {question_en}
Question (AR): {question_ar}

Return a JSON with exactly two keys: "answer_en" and "answer_ar"."""
    try:
        client = _get_openai_client()
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You output JSON with English and Arabic answers for real estate marketing."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        logger.error("Failed to generate answer for: %s. Error: %s", question_en, e)
        return {"answer_en": None, "answer_ar": None}

async def generate_marketing_answers(db: AsyncSession):
    """Generate AI answers for all unanswered marketing questions."""
    await ensure_seeded_questions(db)

    market_context = "Current CBE Rate: 27.25%, USD/EGP Parallel: ~48, Inflation: trending down to ~25%."

    result = await db.execute(
        select(MarketingMaterial).order_by(MarketingMaterial.category, MarketingMaterial.id)
    )
    questions = result.scalars().all()

    updated_count = 0
    failed_count = 0
    for q in questions:
        # Skip already-answered questions unless explicitly regenerating
        try:
            answers = await generate_single_answer(q.question_en, q.question_ar, market_context)
            if answers.get("answer_en") and answers.get("answer_ar"):
                q.answer_en = answers["answer_en"]
                q.answer_ar = answers["answer_ar"]
                q.last_updated = datetime.now(timezone.utc)
                q.last_run_status = "SUCCESS"
                updated_count += 1
            else:
                q.last_run_status = "FAILED"
                failed_count += 1
            # Commit after each question so partial progress is saved
            await db.commit()
        except Exception as e:
            logger.error("Error generating answer for id=%s: %s", q.id, e)
            q.last_run_status = "FAILED"
            failed_count += 1
            try:
                await db.commit()
            except Exception:
                await db.rollback()

    logger.info("Marketing generation complete: %d updated, %d failed", updated_count, failed_count)
    return updated_count
