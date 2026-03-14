// api/chat.mjs
// PROXY: Forwards frontend requests to the Python Wolf Brain

export default async function handler(req, res) {
    // 1. Get the Python Backend URL from environment variables
    // If running locally, usually http://localhost:8000
    // If deployed, use your Railway/Render URL
    const BACKEND_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const API_ENDPOINT = `${BACKEND_URL}/api/chat`; // Ensure this matches your Python route

    console.log(`🔀 Proxying chat request to: ${API_ENDPOINT}`);

    // CORS headers - restrict to known origins
    const ALLOWED_ORIGINS = [
        'https://osool.vercel.app',
        'https://osoool.vercel.app',
        'https://osool-one.vercel.app',
        'https://osool-ten.vercel.app',
        'https://osool.eg',
        'http://localhost:3000',
    ];
    const origin = req.headers.origin || '';
    const isVercelPreview = /^https:\/\/osool-[a-z0-9]+-mustafas-projects-[a-z0-9]+\.vercel\.app$/.test(origin);
    if (ALLOWED_ORIGINS.includes(origin) || isVercelPreview) {
        res.setHeader('Access-Control-Allow-Origin', origin);
    }
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        // 2. Forward the request to Python
        const backendResponse = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Forward auth tokens if you have them
                'Authorization': req.headers.authorization || '',
            },
            body: JSON.stringify(req.body),
        });

        // 3. Handle errors from Python
        if (!backendResponse.ok) {
            const errorText = await backendResponse.text();
            console.error('❌ Python Backend Error:', backendResponse.status, errorText);
            return res.status(backendResponse.status).json({
                error: 'Brain malfunction',
                details: errorText,
                reply: 'عذراً، حدث خطأ في الاتصال بالخادم. جرب مرة تانية.'
            });
        }

        // 4. Return the data to the frontend
        // Python returns: { response, charts, properties, strategy, psychology, ... }
        const data = await backendResponse.json();

        // Map 'response' to 'reply' for frontend compatibility
        return res.status(200).json({
            reply: data.response || data.reply,
            properties: data.properties || [],
            charts: data.charts || data.ui_actions || [],
            clientProfile: data.psychology || {},
            strategy: data.strategy || {},
            source_model: data.source_model || 'Wolf Brain V7'
        });

    } catch (error) {
        console.error('❌ Proxy Error:', error);
        return res.status(500).json({
            error: 'Failed to connect to AI Core',
            details: error.message,
            reply: 'عذراً، مفيش اتصال بالسيرفر دلوقتي. تأكد إن الـ Backend شغال.'
        });
    }
}
