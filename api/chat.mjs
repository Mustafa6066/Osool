// Advanced Real Estate AI Agent for Vercel
// Implements: Property Search, Client Profiling, Conversation State

// Change to ESM imports to match package.json "type": "module"
import fs from 'fs';
import path from 'path';

// Load property data from public/assets/js/data.js (PRIMARY source)
let propertyData;
try {
    // Primary source: public/assets/js/data.js (authoritative data)
    const dataPath = path.join(process.cwd(), 'public', 'assets', 'js', 'data.js');
    if (fs.existsSync(dataPath)) {
        // Read the file content
        const fileContent = fs.readFileSync(dataPath, 'utf8');
        // Remove the "window.egyptianData = " prefix and any trailing semicolon
        const jsonContent = fileContent.replace('window.egyptianData = ', '').replace(/;\s*$/, '');
        propertyData = JSON.parse(jsonContent);
        console.log(`✅ Loaded ${propertyData.properties?.length || 0} properties from public/assets/js/data.js`);
    } else {
        throw new Error(`Property file not found at ${dataPath}`);
    }
} catch (e) {
    console.error('CRITICAL: Failed to load primary property data from public/assets/js/data.js.', e);
    // Fallback to empty data to prevent crash
    propertyData = { properties: [], metadata: {} };
}

export default async function handler(req, res) {
    // Ensure ALL responses are JSON
    res.setHeader('Content-Type', 'application/json');

    try {
        // CORS
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        if (req.method === 'OPTIONS') return res.status(200).end();
        if (req.method !== 'POST') return res.status(405).json({ error: 'Method Not Allowed' });

        const { message, conversationHistory = [], clientProfile = {} } = req.body || {};

        if (!message) {
            return res.status(400).json({ error: 'Missing message', reply: 'معلش يا باشا، مفيش رسالة. قولي إيه اللي عايزه؟' });
        }

        const API_KEY = process.env.OPENAI_API_KEY;

        if (!API_KEY) {
            return res.status(500).json({
                error: 'Missing API Key',
                reply: 'عذراً، السيستم مش جاهز دلوقتي. جرب تاني كمان شوية!'
            });
        }
        // 1. Analyze user intent
        const analysis = await analyzeUserIntent(API_KEY, message, clientProfile);

        // 2. Update client profile
        const updatedProfile = { ...clientProfile, ...analysis };

        // 3. Search for matching properties if criteria exist
        let matchedProperties = [];
        if (shouldShowProperties(updatedProfile, conversationHistory)) {
            matchedProperties = searchProperties(propertyData.properties, updatedProfile);
        }

        // 4. Generate AI response
        const response = await generateAgentResponse(
            API_KEY,
            message,
            conversationHistory,
            updatedProfile,
            matchedProperties
        );

        return res.status(200).json({
            reply: response.message,
            properties: matchedProperties.slice(0, 3).map(p => ({
                id: p.id,
                title: p.title,
                type: p.type,
                location: p.location,
                compound: p.compound,
                price: p.price,
                area: p.area,
                bedrooms: p.bedrooms,
                bathrooms: p.bathrooms,
                image: p.image,
                matchScore: p.matchScore,
                paymentPlan: p.paymentPlan
            })),
            clientProfile: updatedProfile,
            conversationState: response.state
        });

    } catch (error) {
        console.error('Agent Error:', error);
        return res.status(500).json({
            error: 'حدث خطأ. حاول مرة أخرى.',
            reply: 'عذراً يا باشا، في مشكلة صغيرة. ممكن تعيد السؤال؟',
            details: error.message
        });
    }
};

// ═══════════════════════════════════════════════════════════════════════════
// INTENT ANALYSIS
// ═══════════════════════════════════════════════════════════════════════════
async function analyzeUserIntent(apiKey, message, currentProfile) {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
            model: 'gpt-4o-mini',
            messages: [
                {
                    role: 'system',
                    content: `أنت محلل طلبات عقارية. حلل طلب العميل واستخرج المعلومات التالية بصيغة JSON:
{
    "budget_min": number أو null,
    "budget_max": number أو null,
    "property_type": "Apartment" | "Villa" | "Townhouse" | "Twinhouse" | "Duplex" | "Penthouse" | "Office" | null,
    "location": "New Cairo" | "Mostakbal City" | "6th of October" | "Sheikh Zayed" | null,
    "bedrooms": number أو null,
    "purpose": "سكن" | "استثمار" | null,
    "urgency": "استفسار" | "جاد" | "مستعجل" | null,
    "special_requirements": string أو null
}
الميزانيات المصرية: مليون = 1000000، 2 مليون = 2000000، 5 مليون = 5000000
إذا لم تجد معلومة، اتركها null. فقط أرجع JSON.`
                },
                {
                    role: 'user',
                    content: `الطلب: "${message}"\nالملف الحالي: ${JSON.stringify(currentProfile)}`
                }
            ],
            temperature: 0.2,
            response_format: { type: 'json_object' }
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error('OpenAI API Error:', response.status, errorText);
        throw new Error(`OpenAI API Error: ${response.status}`);
    }

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);

    try {
        const parsed = JSON.parse(data.choices[0].message.content);

        // Merge with existing profile (don't overwrite with null)
        const merged = { ...currentProfile };
        for (const [key, value] of Object.entries(parsed)) {
            if (value !== null && value !== undefined) {
                merged[key] = value;
            }
        }

        return merged;
    } catch (e) {
        console.error('Failed to parse analysis:', e);
        return currentProfile;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// PROPERTY SEARCH ENGINE
// ═══════════════════════════════════════════════════════════════════════════
function searchProperties(properties, criteria) {
    if (!properties || !Array.isArray(properties)) return [];

    let results = [...properties];

    // Filter by budget
    if (criteria.budget_min) {
        results = results.filter(p => p.price >= criteria.budget_min);
    }
    if (criteria.budget_max) {
        results = results.filter(p => p.price <= criteria.budget_max);
    }

    // Filter by type
    if (criteria.property_type) {
        results = results.filter(p =>
            p.type && p.type.toLowerCase().includes(criteria.property_type.toLowerCase())
        );
    }

    // Filter by location
    if (criteria.location) {
        const loc = criteria.location.toLowerCase();
        results = results.filter(p =>
            (p.location && p.location.toLowerCase().includes(loc)) ||
            (p.compound && p.compound.toLowerCase().includes(loc))
        );
    }

    // Filter by bedrooms
    if (criteria.bedrooms) {
        results = results.filter(p => p.bedrooms >= criteria.bedrooms);
    }

    // Score and rank results
    results = results.map(p => ({
        ...p,
        matchScore: calculateMatchScore(p, criteria)
    }));

    // Sort by match score
    results.sort((a, b) => b.matchScore - a.matchScore);

    return results.slice(0, 10);
}

function calculateMatchScore(property, criteria) {
    let score = 50; // Base score

    // Price match
    if (criteria.budget_max) {
        const priceRatio = property.price / criteria.budget_max;
        if (priceRatio <= 0.8) score += 25;
        else if (priceRatio <= 1) score += 20;
        else if (priceRatio <= 1.1) score += 10;
    }

    // Type exact match
    if (criteria.property_type && property.type &&
        property.type.toLowerCase() === criteria.property_type.toLowerCase()) {
        score += 15;
    }

    // Location exact match
    if (criteria.location && property.location &&
        property.location.toLowerCase().includes(criteria.location.toLowerCase())) {
        score += 15;
    }

    // Bedroom match
    if (criteria.bedrooms && property.bedrooms === criteria.bedrooms) {
        score += 10;
    }

    // Investment bonus
    if (criteria.purpose === 'استثمار' && property.pricePerSqm) {
        const avgPricePerSqm = 150000;
        if (property.pricePerSqm < avgPricePerSqm * 0.9) {
            score += 10; // Good value
        }
    }

    return Math.min(score, 100);
}

// ═══════════════════════════════════════════════════════════════════════════
// CONVERSATION STATE MANAGEMENT
// ═══════════════════════════════════════════════════════════════════════════
function shouldShowProperties(profile, history) {
    // Need at least one criteria to show properties
    const hasCriteria = profile.budget_min || profile.budget_max ||
        profile.property_type || profile.location ||
        profile.bedrooms;

    // Show properties immediately if user has specific search criteria
    // This allows first-message searches like "apartments in New Cairo" to work
    return hasCriteria;
}

// ═══════════════════════════════════════════════════════════════════════════
// AI RESPONSE GENERATOR
// ═══════════════════════════════════════════════════════════════════════════
async function generateAgentResponse(apiKey, userMessage, history, profile, properties) {
    const systemPrompt = createSystemPrompt(profile, properties, propertyData.metadata);

    const messages = [
        { role: 'system', content: systemPrompt },
        ...history.slice(-8), // Last 8 messages for context
        { role: 'user', content: userMessage }
    ];

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
        },
        body: JSON.stringify({
            model: 'gpt-4o-mini',
            messages,
            temperature: 0.8,
            max_tokens: 800
        })
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error('OpenAI API Error:', response.status, errorText);
        throw new Error(`OpenAI API Error: ${response.status}`);
    }

    const data = await response.json();
    if (data.error) throw new Error(data.error.message);

    return {
        message: data.choices[0].message.content,
        state: determineConversationState(profile)
    };
}

// ═══════════════════════════════════════════════════════════════════════════
// CUSTOMER SEGMENT DETECTION
// ═══════════════════════════════════════════════════════════════════════════
function detectCustomerSegment(profile) {
    const budget = profile.budget_max || profile.budget_min || 0;

    if (profile.purpose === 'استثمار' || profile.purpose === 'investment') {
        return 'investor';
    }
    if (budget >= 10000000) {
        return 'luxury';
    }
    if (budget >= 2000000) {
        return 'middle_class';
    }
    return 'first_time_buyer';
}

// ═══════════════════════════════════════════════════════════════════════════
// SEGMENT-SPECIFIC COMMUNICATION STYLES
// ═══════════════════════════════════════════════════════════════════════════
function getSegmentGuidance(segment) {
    const styles = {
        luxury: `
【أسلوب التواصل - عميل الفخامة】
- استخدم لغة راقية ومصطلحات استثمارية
- امزج بين العربية والإنجليزية بشكل طبيعي (code-switching)
- ركز على: الخصوصية، التميز، العائد على الاستثمار، الإرث العائلي
- مثال: "This compound offers exceptional privacy and a projected 18% ROI."`,

        middle_class: `
【أسلوب التواصل - الطبقة الوسطى】
- استخدم لغة عملية ودافئة
- تحدث عن راحة العيلة، المدارس، المواصلات، المستقبل
- مثال: "المنطقة دي هادية وآمنة، والمدارس الخاصة على بُعد 10 دقايق."`,

        first_time_buyer: `
【أسلوب التواصل - المشتري لأول مرة】
- استخدم لغة بسيطة وشرح كل خطوة
- طمئنه وشجعه
- مثال: "مفيش حاجة اسمها سؤال غبي - كل الأسئلة مرحب بيها."`,

        investor: `
【أسلوب التواصل - المستثمر】
- قدم أرقام وبيانات
- تحدث عن العائد والنمو والسوق
- مثال: "Based on current trajectory, this area shows 15% YoY appreciation. Rental yield sits at 7.2%"`
    };

    return styles[segment] || styles.middle_class;
}

function createSystemPrompt(profile, properties, metadata) {
    const totalProps = metadata?.totalProperties || 3274;
    const segment = detectCustomerSegment(profile);
    const segmentGuidance = getSegmentGuidance(segment);

    let prompt = `أنت "مستشار النخبة العقاري" - مستشار عقاري مصري محترف يتمتع بخبرة واسعة في سوق العقارات المصري.

═══════════════════════════════════════════════════════════════
                        هويتك وشخصيتك
═══════════════════════════════════════════════════════════════

【الاسم】 مستشار النخبة | Elite Advisor
【الدور】 مستشار عقاري شخصي يعمل بالذكاء الاصطناعي
【اللغة】 ثنائي اللغة - عربي مصري وإنجليزي
【الأسلوب】 محترم، ودود، صبور، وعملي

═══════════════════════════════════════════════════════════════
                     مبادئك الأساسية
═══════════════════════════════════════════════════════════════

1. 【لا ضغط أبداً】
   - أنت مستشار، لست بائع
   - قراراتهم تحتاج وقت وهذا طبيعي
   - العميل يجب أن يشعر بالراحة التامة

2. 【افهم أولاً، اقترح ثانياً】
   - اسأل أسئلة ذكية لفهم احتياجاتهم الحقيقية
   - لا تقترح عقارات قبل فهم: الميزانية، الغرض، الموقع المفضل، الأولويات

3. 【كل العملاء مهمين】
   - سواء الميزانية مليون أو عشرين مليون
   - عامل الجميع باحترام متساوي
   - كل عميل يستحق أفضل نصيحة

4. 【الصدق والشفافية】
   - لا تخفي عيوب أي عقار
   - وضّح المخاطر والفرص بصراحة
   - الثقة أهم من البيع

═══════════════════════════════════════════════════════════════
                    ممنوعات صارمة
═══════════════════════════════════════════════════════════════

❌ لا تقدم خصومات أو عروض (ممنوع تماماً)
❌ لا تضغط على العميل للشراء
❌ لا تبالغ في وصف العقارات
❌ لا تتجاهل مخاوف العميل
❌ لا تقارن العملاء ببعض
❌ لا تستخدم لغة بيعية مبتذلة
❌ لا تعد بما لا يمكن تحقيقه

═══════════════════════════════════════════════════════════════
                    أسلوب المحادثة
═══════════════════════════════════════════════════════════════

【البداية - الترحيب】
"أهلاً وسهلاً! 👋 أنا مستشارك العقاري الشخصي.
مهمتي إني أساعدك تلاقي المكان اللي يناسبك ويناسب حياتك.
قبل ما نبدأ، حابب أعرفك أكتر - إيه اللي جابك النهارده؟"

【مرحلة الاستكشاف - أسئلة ذكية】
- "بتدور على سكن ليك ولعيلتك، ولا استثمار؟"
- "في منطقة معينة في بالك؟ ولا مفتوح للاقتراحات؟"
- "إيه أهم حاجة ليك - المساحة، الموقع، السعر، ولا الجودة؟"
- "عندك أطفال؟ المدارس عامل مهم؟"

【مرحلة التقديم - عرض الخيارات】
- قدم 2-3 خيارات فقط (لا تُربك العميل)
- اشرح لماذا كل خيار يناسب احتياجاته
- كن صريحاً عن المميزات والعيوب

【التعامل مع التردد】
- "طبيعي جداً إنك تاخد وقتك. قرار زي ده محتاج تفكير."
- "لو حابب تزور المكان مع حد من العيلة، أنا أرتبلك."
- "مفيش استعجال - خدلك راحتك."

${segmentGuidance}

═══════════════════════════════════════════════════════════════
                      بيانات العقارات
═══════════════════════════════════════════════════════════════

لديك قاعدة بيانات بها ${totalProps} عقار في:
- القاهرة الجديدة (New Cairo)
- مدينة المستقبل (Mostakbal City)
- التجمع الخامس
- الشيخ زايد
- 6 أكتوبر

النطاق السعري: من 1 مليون إلى 150 مليون جنيه
أنواع العقارات: شقق، فيلات، تاون هاوس، توين هاوس، دوبلكس، بنتهاوس، مكاتب
`;

    // Add client profile context
    if (Object.keys(profile).length > 0) {
        prompt += `\n\n📋 ملف العميل الحالي (الشريحة: ${segment}):\n`;
        if (profile.budget_max) prompt += `- الميزانية: حتى ${(profile.budget_max / 1000000).toFixed(1)} مليون جنيه\n`;
        if (profile.budget_min) prompt += `- الحد الأدنى: ${(profile.budget_min / 1000000).toFixed(1)} مليون جنيه\n`;
        if (profile.property_type) prompt += `- نوع العقار: ${profile.property_type}\n`;
        if (profile.location) prompt += `- المنطقة: ${profile.location}\n`;
        if (profile.bedrooms) prompt += `- الغرف: ${profile.bedrooms} غرف نوم\n`;
        if (profile.purpose) prompt += `- الغرض: ${profile.purpose}\n`;
        if (profile.urgency) prompt += `- مرحلة الشراء: ${profile.urgency}\n`;
    }

    // Add matching properties
    if (properties && properties.length > 0) {
        prompt += `\n\n🏠 عقارات مناسبة للعرض:\n`;
        properties.slice(0, 5).forEach((p, i) => {
            const priceM = (p.price / 1000000).toFixed(2);
            const installment = p.paymentPlan?.monthlyInstallment?.toLocaleString() || 'N/A';

            prompt += `
${i + 1}. ${p.title}
   - النوع: ${p.type} | ${p.bedrooms} غرف | ${p.bathrooms} حمام
   - الكمبوند: ${p.compound}
   - الموقع: ${p.location}
   - المساحة: ${p.area} م²
   - السعر: ${priceM} مليون جنيه
   - المقدم: ${p.paymentPlan?.downPayment || 10}%
   - القسط الشهري: ${installment} جنيه
   - التسليم: ${p.deliveryDate}
   - نسبة التطابق: ${p.matchScore}%
`;
        });

        prompt += `\n⚡ عند عرض العقارات، اذكر المميزات بطريقة جذابة ومقنعة.`;
    } else {
        prompt += `\n\n📌 لم يتم تحديد معايير بحث محددة بعد. اسأل العميل عن احتياجاته (نوع العقار، الموقع، الميزانية) لتتمكن من البحث في قاعدة البيانات التي تحتوي على ${totalProps} عقار.`;
    }

    prompt += `\n\n═══════════════════════════════════════════════════════════════
                    هدفك النهائي
═══════════════════════════════════════════════════════════════

هدفك الحقيقي مش "البيع" - هدفك إنك تساعد الشخص ده يلاقي المكان 
الصح اللي هيكون فيه سعيد. لما تعمل ده صح، البيع بييجي لوحده.

تذكر: كل عميل راضي = عشرة عملاء جُدد بالتوصية.`;

    return prompt;
}

function determineConversationState(profile) {
    const filled = Object.values(profile).filter(v => v !== null && v !== undefined).length;

    if (filled === 0) return 'greeting';
    if (filled <= 2) return 'discovery';
    if (filled <= 4) return 'qualifying';
    return 'presentation';
}
