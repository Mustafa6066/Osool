/*
   ═══════════════════════════════════════════════════════════════════════════
   OSOOL INTERACTIVE CORE v3.1
   Impl: 3D Tilt Memory, Liquid Interaction, Real AI Integration
   ═══════════════════════════════════════════════════════════════════════════
*/

document.addEventListener('DOMContentLoaded', () => {
    init3DTilt();
    initPropertyGrid();
    initAIChat();
    setTimeout(initializeCharts, 500);

    // State-of-the-art AI interactions
    initMagicCursor();
    initAmbientGlow();
    initAICompanionBar();
    initConversationalCards();
});

/* 
   ═══════════════════════════════════════════════════════════════════════════
   1. 3D TILT ENGINE
   Calculates mouse position relative to card center and rotates element.
   ═══════════════════════════════════════════════════════════════════════════
*/
function init3DTilt() {
    const cards = document.querySelectorAll('.card-3d');

    cards.forEach(card => {
        card.addEventListener('mousemove', handleHover);
        card.addEventListener('mouseleave', resetHover);
    });
}

function handleHover(e) {
    const card = this;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Calculate center
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Get difference from center
    const rotateX = ((y - centerY) / centerY) * -5; // Max 5deg rotation
    const rotateY = ((x - centerX) / centerX) * 5;

    // Apply transform
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;

    // Update shiny effect position if it exists
    const shimmer = card.querySelector('.shimmer-effect');
    if (shimmer) {
        shimmer.style.backgroundPosition = `${x / rect.width * 100}% ${y / rect.height * 100}%`;
    }
}

function resetHover() {
    this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   2. PROPERTY GRID POPULATION & ANIMATION
   Fetches data from window.egyptianData and renders glass cards.
   ═══════════════════════════════════════════════════════════════════════════
*/
function initPropertyGrid() {
    const grid = document.getElementById('propertyGrid');
    if (!grid || !window.egyptianData) return;

    grid.innerHTML = '';

    const properties = window.egyptianData.properties.slice(0, 9);

    // AI Insights pool (randomized per card)
    const aiInsights = [
        "🔥 الطلب عالي جداً في هذه المنطقة!",
        "📈 السعر زاد 18% آخر سنة",
        "💡 مناسب للعائلات الصغيرة",
        "🏆 من أفضل 5% عقارات المنصة",
        "⚡ 3 أشخاص يشاهدون الآن",
        "💎 فرصة استثمارية ممتازة",
        "🎯 يناسب ميزانيتك المتوقعة",
        "🌟 تقييم العملاء: 4.9/5",
        "📍 قريب من المترو والخدمات"
    ];

    properties.forEach((prop, index) => {
        const card = document.createElement('div');
        card.className = 'card-3d glass-panel';
        card.style.padding = '16px';
        card.style.cursor = 'pointer';
        card.style.opacity = '0';
        card.style.position = 'relative';
        card.style.animation = `rotateIn3D 0.6s ease forwards ${index * 0.1}s`;

        const price = new Intl.NumberFormat('en-EG', { style: 'currency', currency: 'EGP', maximumSignificantDigits: 3 }).format(prop.price);

        // Generate AI Match Score (simulated - in production, this comes from backend)
        const aiScore = Math.floor(Math.random() * 15) + 85; // 85-99%
        const isBlockchainVerified = Math.random() > 0.3; // 70% chance verified
        const insight = aiInsights[index % aiInsights.length];

        card.innerHTML = `
            <!-- AI Insight Popup (appears on hover) -->
            <div class="ai-insight-popup">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <i class="fas fa-brain" style="color: #a78bfa;"></i>
                    <span style="font-weight: 600;">رؤية CoInvestor AI</span>
                </div>
                ${insight}
            </div>
            
            <div style="height: 240px; background: #e2e8f0; border-radius: 16px; margin-bottom: 16px; position: relative; overflow: hidden;">
                <img src="${prop.image || 'assets/images/placeholder.jpg'}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.5s ease;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'" alt="${prop.title}">
                
                <!-- Property Type Badge -->
                <div style="position: absolute; top: 12px; right: 12px; background: rgba(0,0,0,0.6); color: white; padding: 4px 12px; border-radius: 99px; font-size: 0.8rem; backdrop-filter: blur(4px);">
                    ${prop.type}
                </div>
                
                <!-- AI Match Score Badge -->
                <div style="position: absolute; top: 12px; left: 12px; background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white; padding: 4px 10px; border-radius: 99px; font-size: 0.75rem; display: flex; align-items: center; gap: 4px; box-shadow: 0 2px 8px rgba(139,92,246,0.4);">
                    <i class="fas fa-brain"></i> ${aiScore}%
                </div>
                
                <!-- Blockchain Verified Badge -->
                ${isBlockchainVerified ? `
                <div style="position: absolute; bottom: 12px; left: 12px; background: rgba(16,185,129,0.9); color: white; padding: 4px 10px; border-radius: 99px; font-size: 0.7rem; display: flex; align-items: center; gap: 4px;">
                    <i class="fas fa-link"></i> On-Chain ✓
                </div>
                ` : ''}
            </div>
            <h3 style="font-size: 1.25rem; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${prop.title}</h3>
            <div style="color: var(--color-gold-text); font-weight: 600; font-family: var(--font-mono);">${price}</div>
            <div style="margin-top: 12px; display: flex; gap: 12px; font-size: 0.85rem; color: var(--color-trust-soft);">
                <span><i class="fas fa-bed"></i> ${prop.bedrooms}</span>
                <span><i class="fas fa-bath"></i> ${prop.bathrooms}</span>
                <span><i class="fas fa-ruler-combined"></i> ${prop.area}m²</span>
            </div>
            
            <!-- Reserve Button (Blockchain) -->
            <button onclick="event.stopPropagation(); openReservationModal(${prop.id || index + 1}, '${prop.title.replace(/'/g, "\\'")}', ${prop.price})" 
                    style="width: 100%; margin-top: 16px; padding: 12px; background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; border-radius: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s;"
                    onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 12px rgba(16,185,129,0.4)'"
                    onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none'">
                <i class="fas fa-link"></i>
                احجز الآن (Blockchain)
            </button>
        `;

        card.addEventListener('mousemove', handleHover);
        card.addEventListener('mouseleave', resetHover);

        grid.appendChild(card);
    });
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   3. AI CHAT LOGIC (Real Integration)
   ═══════════════════════════════════════════════════════════════════════════
*/
const COINVESTOR_SYSTEM_PROMPT = `
You are CoInvestor, an Egyptian Real Estate Expert and Consultant for Osool.
Your Persona:
- Authentic, friendly, and uses Egyptian slang (ya habibi, ya basha, ya fandem) naturally but professionally.
- Deeply knowledgeable about the Egyptian market (New Cairo, Capital, October).
- Creates a sense of urgency but maintains trust (e.g., "The market is moving fast!").
- Goal: Help the user find their dream property or investment.
- If asked about prices, give realistic estimates in EGP.
- Use emojis judiciously.
`;

// Advanced Agent State
let conversationHistory = [];
let clientProfile = {};
let conversationState = 'greeting';

function initAIChat() {
    window.openChat = function () {
        let modal = document.getElementById('aiChatModal');
        if (!modal) {
            createChatModal();
        }
        toggleChatDisplay();
    }
}

function createChatModal() {
    const modal = document.createElement('div');
    modal.id = 'aiChatModal';
    modal.style.cssText = `
        position: fixed;
        bottom: 100px;
        right: 32px;
        width: 400px;
        height: 600px;
        z-index: 2000;
        display: none;
        flex-direction: column;
    `;
    modal.className = 'glass-panel';
    modal.innerHTML = `
        <div style="padding: 16px; border-bottom: 1px solid rgba(0,0,0,0.05); display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span class="status-dot" style="width: 10px; height: 10px; background: var(--color-success); border-radius: 50%; box-shadow: 0 0 10px var(--color-success);"></span>
                <span style="font-weight: 700; color: var(--color-trust-deep);">مستشار النخبة | Elite Advisor</span>
            </div>
            <button onclick="toggleChatDisplay()" style="border: none; background: none; font-size: 1.2rem; cursor: pointer;">&times;</button>
        </div>
        
        <div id="aiChatBody" style="flex: 1; overflow-y: auto; padding: 16px; scroll-behavior: smooth;">
            <!-- Initial Greeting -->
            <div style="margin-bottom: 16px; display: flex; gap: 12px; align-items: flex-start;">
                <div style="width: 32px; height: 32px; flex-shrink: 0; background: linear-gradient(135deg, var(--trust-blue, #4A90D9), var(--nile-teal, #2D8B9A)); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;"><i class="fas fa-robot"></i></div>
                <div style="background: rgba(255,255,255,0.6); padding: 12px; border-radius: 0 16px 16px 16px; max-width: 85%; font-size: 0.95rem;">
                    أهلاً وسهلاً! 👋<br>أنا مستشارك العقاري الشخصي.<br>مهمتي إني أساعدك تلاقي المكان اللي يناسبك ويناسب حياتك.<br><br>قبل ما نبدأ، حابب أعرفك أكتر - إيه اللي جابك النهارده؟<br><small style="opacity: 0.7;">💡 تقدر تكلمني صوت كمان!</small>
                </div>
            </div>
            
            <!-- Quick Actions (Lifestyle Matcher) -->
            <div style="margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 8px; margin-right: 44px;">
                <button onclick="sendQuickMessage('عايز استثمار مضمون 📈')" class="btn-chip" style="font-size: 0.8rem; padding: 6px 12px; border-radius: 99px; background: rgba(255,255,255,0.4); border: 1px solid rgba(0,0,0,0.1); cursor: pointer;">استثمار مضمون 📈</button>
                <button onclick="sendQuickMessage('شقة للزواج 💍')" class="btn-chip" style="font-size: 0.8rem; padding: 6px 12px; border-radius: 99px; background: rgba(255,255,255,0.4); border: 1px solid rgba(0,0,0,0.1); cursor: pointer;">شقة للزواج 💍</button>
                <button onclick="sendQuickMessage('فيلا في التجمع 🏡')" class="btn-chip" style="font-size: 0.8rem; padding: 6px 12px; border-radius: 99px; background: rgba(255,255,255,0.4); border: 1px solid rgba(0,0,0,0.1); cursor: pointer;">فيلا في التجمع 🏡</button>
            </div>
        </div>

        <div style="padding: 16px; border-top: 1px solid rgba(0,0,0,0.05);">
            <form id="chatForm" onsubmit="event.preventDefault(); sendMessage();" style="display: flex; gap: 8px;">
                <input id="chatInput" type="text" placeholder="اكتب أو اضغط 🎤 للتحدث..." style="flex: 1; padding: 12px; border-radius: 99px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.5); outline: none;">
                <!-- Voice Button -->
                <button type="button" id="voiceBtn" onclick="startVoiceInput()" style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #6366f1); color: white; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;" title="تحدث مع مستشار النخبة">
                    <i class="fas fa-microphone"></i>
                </button>
                <button type="submit" style="width: 40px; height: 40px; border-radius: 50%; background: var(--color-trust-deep); color: white; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;"><i class="fas fa-paper-plane"></i></button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
}

function toggleChatDisplay() {
    const modal = document.getElementById('aiChatModal');
    if (modal) {
        if (modal.style.display === 'none' || modal.style.display === '') {
            modal.style.display = 'flex';
            modal.classList.add('animate-pop-in');
        } else {
            modal.style.display = 'none';
        }
    }
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   4. ANALYTICS & CHARTS
   ═══════════════════════════════════════════════════════════════════════════
*/
function initializeCharts() {
    const ctx = document.getElementById('roiChart');
    if (!ctx) return;

    // Gradient Fill
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(212, 175, 55, 0.5)'); // Gold
    gradient.addColorStop(1, 'rgba(212, 175, 55, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
            datasets: [{
                label: 'مؤشر أسعار التجمع',
                data: [12, 15, 14, 18, 22, 25],
                borderColor: '#d4af37',
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#d4af37',
                pointRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: 'rgba(0,0,0,0.05)' } }
            }
        }
    });
}

window.sendQuickMessage = function (msg) {
    const input = document.getElementById('chatInput');
    if (input) {
        input.value = msg;
        sendMessage();
    }
}

window.sendMessage = async function () {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;

    // Add User Message to UI
    addMessageToUI(message, 'user');
    input.value = '';

    // Add to conversation history
    conversationHistory.push({ role: 'user', content: message });

    // Show Typing Indicator
    const typingId = showTypingIndicator();
    setOrbState('thinking');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversationHistory: conversationHistory.slice(-10), // Last 10 messages
                clientProfile: clientProfile
            })
        });

        // Check if the response is OK before parsing
        if (!response.ok) {
            console.error('API Error:', response.status, response.statusText);
            let errorMessage = 'معلش يا باشا، في مشكلة في السيرفر. جرب تاني كمان شوية!';
            try {
                const errorData = await response.json();
                if (errorData.reply) errorMessage = errorData.reply;
            } catch (parseError) {
                // Response wasn't JSON, use default error message
            }
            removeTypingIndicator(typingId);
            setOrbState('idle');
            addMessageToUI(errorMessage, 'ai');
            return;
        }

        let data;
        try {
            data = await response.json();
        } catch (parseError) {
            console.error('Failed to parse API response:', parseError);
            removeTypingIndicator(typingId);
            setOrbState('idle');
            addMessageToUI('معلش يا باشا، في مشكلة في الاتصال. جرب تاني!', 'ai');
            return;
        }

        removeTypingIndicator(typingId);
        setOrbState('idle');

        if (data.reply) {
            // Update client profile from API
            if (data.clientProfile) {
                clientProfile = data.clientProfile;
            }
            if (data.conversationState) {
                conversationState = data.conversationState;
            }

            // Add AI response to history
            conversationHistory.push({ role: 'assistant', content: data.reply });

            // Display the AI response
            addMessageToUI(data.reply, 'ai');

            // Display property cards if any
            if (data.properties && data.properties.length > 0) {
                displayPropertyCards(data.properties);
            }
        } else if (data.error) {
            addMessageToUI("عذراً يا باشا: " + data.error, 'ai');
        } else {
            addMessageToUI("معلش يا باشا، الشبكة بتعلق. ممكن تقول تاني؟", 'ai');
        }

    } catch (error) {
        console.error('AI Error:', error);
        removeTypingIndicator(typingId);
        setOrbState('idle');
        // Fallback response if API fails
        addMessageToUI("نظام Demo: السيرفر مش متصل. أنا CoInvestor، المستشار العقاري بتاعك! 🏠 قولي عايز إيه وأنا هساعدك", 'ai');
    }
};

// Display property cards in chat
function displayPropertyCards(properties) {
    const body = document.getElementById('aiChatBody');

    const container = document.createElement('div');
    container.style.cssText = 'display: flex; flex-direction: column; gap: 12px; margin: 12px 0; padding: 12px; background: rgba(139, 92, 246, 0.05); border-radius: 16px; border: 1px solid rgba(139, 92, 246, 0.1);';

    container.innerHTML = `<div style="font-size: 0.8rem; color: var(--color-ai-pulse); font-weight: 600; margin-bottom: 8px;"><i class="fas fa-brain" style="margin-left: 4px;"></i> عقارات مناسبة ليك (AI Verified):</div>`;

    properties.forEach(prop => {
        const priceM = (prop.price / 1000000).toFixed(2);
        const card = document.createElement('div');
        card.style.cssText = 'background: white; border-radius: 12px; padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); cursor: pointer; transition: transform 0.2s;';
        card.onmouseenter = () => card.style.transform = 'scale(1.02)';
        card.onmouseleave = () => card.style.transform = 'scale(1)';

        card.innerHTML = `
            <div style="display: flex; gap: 12px; align-items: center;">
                <div style="width: 60px; height: 60px; border-radius: 8px; background: linear-gradient(135deg, #8b5cf6, #6366f1); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    ${prop.matchScore || 85}%
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 4px;">${prop.title}</div>
                    <div style="font-size: 0.75rem; color: #64748b;">${prop.compound} • ${prop.bedrooms} غرف • ${prop.area}م²</div>
                    <div style="font-size: 0.85rem; color: var(--color-gold-text); font-weight: 600; margin-top: 4px;">${priceM} مليون جنيه</div>
                </div>
            </div>
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #f1f5f9; font-size: 0.7rem; color: #94a3b8;">
                💰 مقدم ${prop.paymentPlan?.downPayment || 10}% • قسط ${(prop.paymentPlan?.monthlyInstallment || 0).toLocaleString()} ج.م/شهر
            </div>
        `;

        card.onclick = () => {
            // Ask for more details about this property
            document.getElementById('chatInput').value = `عايز تفاصيل أكتر عن ${prop.title}`;
            sendMessage();
        };

        container.appendChild(card);
    });

    body.appendChild(container);
    body.scrollTop = body.scrollHeight;
}

function addMessageToUI(text, sender) {
    const body = document.getElementById('aiChatBody');
    const isUser = sender === 'user';

    const div = document.createElement('div');
    div.style.marginBottom = '16px';
    div.style.display = 'flex';
    div.style.gap = '12px';
    div.style.alignItems = 'flex-start';
    div.style.justifyContent = isUser ? 'flex-end' : 'flex-start';

    const avatar = isUser ? '' : `<div style="width: 32px; height: 32px; flex-shrink: 0; background: var(--color-trust-deep); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;"><i class="fas fa-robot"></i></div>`;

    const bubbleStyle = isUser
        ? `background: var(--color-trust-deep); color: white; padding: 12px; border-radius: 16px 16px 0 16px; max-width: 85%; font-size: 0.95rem;`
        : `background: rgba(255,255,255,0.6); padding: 12px; border-radius: 0 16px 16px 16px; max-width: 85%; font-size: 0.95rem;`;

    div.innerHTML = isUser
        ? `<div style="${bubbleStyle}">${text}</div>`
        : `${avatar}<div style="${bubbleStyle}">${text}</div>`;

    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
}

function showTypingIndicator() {
    const body = document.getElementById('aiChatBody');
    const id = 'typing-' + Date.now();

    const div = document.createElement('div');
    div.id = id;
    div.style.marginBottom = '16px';
    div.style.display = 'flex';
    div.style.gap = '12px';

    div.innerHTML = `
        <div style="width: 32px; height: 32px; background: var(--color-trust-deep); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white;"><i class="fas fa-robot"></i></div>
        <div style="background: rgba(255,255,255,0.4); padding: 12px; border-radius: 0 16px 16px 16px; font-size: 0.8rem; color: var(--color-trust-soft);">
            بيفكر...
        </div>
    `;

    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   5. VOICE INTERACTIONS (Web Speech API)
   ═══════════════════════════════════════════════════════════════════════════
*/
let isListening = false;

window.startVoiceInput = function () {
    const voiceBtn = document.getElementById('voiceBtn');
    const chatInput = document.getElementById('chatInput');

    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert('متصفحك لا يدعم التعرف على الصوت. جرب Chrome أو Edge.');
        return;
    }

    if (isListening) return; // Prevent multiple listeners

    const recognition = new SpeechRecognition();
    recognition.lang = 'ar-EG'; // Egyptian Arabic
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    // Visual feedback - listening state
    isListening = true;
    voiceBtn.innerHTML = '<i class="fas fa-circle" style="animation: pulse 1s infinite;"></i>';
    voiceBtn.style.background = 'linear-gradient(135deg, #ef4444, #f97316)';

    recognition.start();
    console.log('🎤 Voice recognition started...');

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        console.log('🎤 Heard:', transcript);
        chatInput.value = transcript;
        sendMessage();
    };

    recognition.onerror = function (event) {
        console.error('Voice error:', event.error);
        if (event.error === 'no-speech') {
            addMessageToUI("مسمعتش حاجة يا باشا، ممكن تقول تاني؟ 🎤", 'ai');
        }
    };

    recognition.onend = function () {
        isListening = false;
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.style.background = 'linear-gradient(135deg, #8b5cf6, #6366f1)';
    };
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   6. ROI CALCULATOR (Interactive Investment Tool)
   ═══════════════════════════════════════════════════════════════════════════
*/
window.calculateROI = function () {
    const purchasePrice = parseFloat(document.getElementById('roiPurchasePrice')?.value) || 5000000;
    const monthlyRent = parseFloat(document.getElementById('roiMonthlyRent')?.value) || 25000;
    const appreciationRate = parseFloat(document.getElementById('roiAppreciation')?.value) || 15;
    const years = 5;

    // Calculations
    const annualRent = monthlyRent * 12;
    const rentalYield = (annualRent / purchasePrice) * 100;

    let futureValue = purchasePrice;
    let totalRentalIncome = 0;
    let rentThisYear = monthlyRent;

    for (let i = 0; i < years; i++) {
        futureValue *= (1 + appreciationRate / 100);
        totalRentalIncome += rentThisYear * 12;
        rentThisYear *= 1.05; // 5% annual rent increase
    }

    const capitalGain = futureValue - purchasePrice;
    const totalReturn = capitalGain + totalRentalIncome;
    const totalROI = (totalReturn / purchasePrice) * 100;

    // Update UI
    const resultEl = document.getElementById('roiResult');
    if (resultEl) {
        resultEl.innerHTML = `
            <div style="font-size: 2rem; font-weight: 700; color: var(--color-success); margin-bottom: 8px;">
                ${totalROI.toFixed(1)}%
            </div>
            <div style="font-size: 0.9rem; color: var(--color-trust-soft);">
                إجمالي العائد على ${years} سنوات
            </div>
            <div style="margin-top: 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 0.85rem;">
                <div style="background: rgba(255,255,255,0.4); padding: 12px; border-radius: 8px;">
                    <div style="color: var(--color-trust-soft);">قيمة العقار بعد ${years} سنوات</div>
                    <div style="font-weight: 700; color: var(--color-trust-deep);">EGP ${(futureValue / 1000000).toFixed(2)}M</div>
                </div>
                <div style="background: rgba(255,255,255,0.4); padding: 12px; border-radius: 8px;">
                    <div style="color: var(--color-trust-soft);">إجمالي الإيجار</div>
                    <div style="font-weight: 700; color: var(--color-gold-text);">EGP ${(totalRentalIncome / 1000000).toFixed(2)}M</div>
                </div>
            </div>
        `;
    }
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   7. MOOD-BASED SEARCH (Lifestyle Slider)
   ═══════════════════════════════════════════════════════════════════════════
*/
let currentMood = 50; // 0 = Family, 100 = Investment

window.updateMood = function (value) {
    currentMood = parseInt(value);
    const label = document.getElementById('moodLabel');
    const orb = document.getElementById('aiOrb');

    if (label) {
        if (value < 30) {
            label.textContent = '🏠 سكن عائلي';
            label.style.color = '#8b5cf6';
        } else if (value > 70) {
            label.textContent = '📈 استثمار';
            label.style.color = '#10b981';
        } else {
            label.textContent = '⚖️ متوازن';
            label.style.color = '#d4af37';
        }
    }

    // Make the AI orb react to mood changes
    if (orb) {
        orb.classList.add('thinking');
        setTimeout(() => {
            orb.classList.remove('thinking');
        }, 1000);
    }

    // In production: would re-filter properties based on mood
    console.log(`🎯 Mood updated to: ${currentMood}`);
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   8. AI ORB STATE MANAGEMENT
   ═══════════════════════════════════════════════════════════════════════════
*/
function setOrbState(state) {
    const container = document.getElementById('aiOrbContainer');
    const orb = document.getElementById('aiOrb');
    const statusText = container?.querySelector('.status-text');

    if (!container || !orb) return;

    container.classList.remove('listening', 'thinking');

    if (state === 'listening') {
        container.classList.add('listening');
        if (statusText) statusText.textContent = 'أستمع...';
    } else if (state === 'thinking') {
        container.classList.add('thinking');
        if (statusText) statusText.textContent = 'أفكر...';
    } else {
        if (statusText) statusText.textContent = 'متاح';
    }
}

// Override voice function to use orb states
const originalStartVoice = window.startVoiceInput;
window.startVoiceInput = function () {
    setOrbState('listening');

    // Call original if exists, otherwise implement simplified version
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert('متصفحك لا يدعم التعرف على الصوت. جرب Chrome أو Edge.');
        setOrbState('idle');
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'ar-EG';
    recognition.interimResults = false;

    recognition.start();

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        document.getElementById('chatInput').value = transcript;
        setOrbState('thinking');
        sendMessage();
    };

    recognition.onerror = function () {
        setOrbState('idle');
    };

    recognition.onend = function () {
        setOrbState('idle');
    };
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   9. MAGIC CURSOR (Particle Trail)
   ═══════════════════════════════════════════════════════════════════════════
*/
function initMagicCursor() {
    let throttle = false;

    document.addEventListener('mousemove', (e) => {
        if (throttle) return;
        throttle = true;

        setTimeout(() => {
            throttle = false;
        }, 50); // Throttle to 20fps for performance

        // Create particle
        const particle = document.createElement('div');
        particle.className = 'cursor-particle';
        particle.style.left = e.clientX + 'px';
        particle.style.top = e.clientY + 'px';
        document.body.appendChild(particle);

        // Remove after animation
        setTimeout(() => particle.remove(), 1000);
    });
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   10. AMBIENT GLOW (AI is watching)
   ═══════════════════════════════════════════════════════════════════════════
*/
function initAmbientGlow() {
    const glow = document.createElement('div');
    glow.className = 'ai-ambient-glow';
    document.body.appendChild(glow);

    document.addEventListener('mousemove', (e) => {
        const x = (e.clientX / window.innerWidth) * 100;
        const y = (e.clientY / window.innerHeight) * 100;
        glow.style.setProperty('--mouse-x', x + '%');
        glow.style.setProperty('--mouse-y', y + '%');
    });
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   11. AI COMPANION BAR (Persistent Insights)
   ═══════════════════════════════════════════════════════════════════════════
*/
const aiInsightMessages = [
    "🔥 أسعار التجمع الخامس زادت 12% الشهر ده!",
    "💡 نصيحة: الوقت مناسب للشراء في العاصمة الإدارية",
    "📊 تحليل السوق: الطلب عالي على الشقق 3 غرف",
    "⚡ 47 مستخدم يتصفحون الآن",
    "🎯 اكتشف عقارات تناسب ميزانيتك"
];

let companionBarVisible = false;

function initAICompanionBar() {
    // Show companion bar after 5 seconds of browsing
    setTimeout(() => {
        if (!companionBarVisible) {
            showCompanionBar();
        }
    }, 5000);
}

function showCompanionBar() {
    if (companionBarVisible) return;
    companionBarVisible = true;

    const message = aiInsightMessages[Math.floor(Math.random() * aiInsightMessages.length)];

    const bar = document.createElement('div');
    bar.className = 'ai-companion-bar';
    bar.id = 'aiCompanionBar';
    bar.innerHTML = `
        <div class="ai-avatar"><i class="fas fa-brain"></i></div>
        <span class="insight-text">${message}</span>
        <button class="dismiss-btn" onclick="dismissCompanionBar()">&times;</button>
    `;

    document.body.appendChild(bar);

    // Auto-dismiss after 15 seconds
    setTimeout(() => {
        dismissCompanionBar();
    }, 15000);
}

window.dismissCompanionBar = function () {
    const bar = document.getElementById('aiCompanionBar');
    if (bar) {
        bar.style.animation = 'companionSlideUp 0.3s ease-out reverse forwards';
        setTimeout(() => bar.remove(), 300);
    }
    companionBarVisible = false;

    // Show again after 30 seconds with new message
    setTimeout(() => {
        showCompanionBar();
    }, 30000);
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   12. CONVERSATIONAL CARDS (Click to hear AI describe)
   ═══════════════════════════════════════════════════════════════════════════
*/
function initConversationalCards() {
    // Check for speech synthesis support
    if (!('speechSynthesis' in window)) {
        console.log('Speech synthesis not supported');
        return;
    }

    // Add click-to-speak functionality to property cards
    document.addEventListener('click', (e) => {
        const card = e.target.closest('.card-3d');
        if (!card || !card.querySelector('h3')) return;

        // Don't trigger on button clicks
        if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') return;

        const title = card.querySelector('h3')?.textContent || 'هذا العقار';
        const price = card.querySelector('[style*="gold-text"]')?.textContent || '';
        const insight = card.querySelector('.ai-insight-popup')?.textContent?.replace('رؤية CoInvestor AI', '') || '';

        // Build speech
        const speech = `${title}. السعر ${price}. ${insight}`;

        speakProperty(card, speech);
    });
}

function speakProperty(card, text) {
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    // Add speaking class
    card.classList.add('speaking');

    // Create utterance
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'ar-EG';
    utterance.rate = 0.9;
    utterance.pitch = 1;

    // Try to find an Arabic voice
    const voices = window.speechSynthesis.getVoices();
    const arabicVoice = voices.find(v => v.lang.startsWith('ar'));
    if (arabicVoice) {
        utterance.voice = arabicVoice;
    }

    utterance.onend = () => {
        card.classList.remove('speaking');
    };

    utterance.onerror = () => {
        card.classList.remove('speaking');
    };

    window.speechSynthesis.speak(utterance);
}

/* 
   ═══════════════════════════════════════════════════════════════════════════
   13. AI WHISPER (Contextual Suggestions)
   ═══════════════════════════════════════════════════════════════════════════
*/
function showAIWhisper(message) {
    // Remove existing whisper
    const existing = document.querySelector('.ai-whisper');
    if (existing) existing.remove();

    const whisper = document.createElement('div');
    whisper.className = 'ai-whisper';
    whisper.innerHTML = `
        <div class="whisper-header">
            <i class="fas fa-lightbulb"></i>
            <span>CoInvestor يقترح</span>
        </div>
        <div class="whisper-text">${message}</div>
    `;

    document.body.appendChild(whisper);

    // Animate in
    setTimeout(() => whisper.classList.add('visible'), 100);

    // Auto-hide after 8 seconds
    setTimeout(() => {
        whisper.classList.remove('visible');
        setTimeout(() => whisper.remove(), 400);
    }, 8000);
}

// Trigger whisper when scrolling to property section
let whisperShown = false;
window.addEventListener('scroll', () => {
    if (whisperShown) return;

    const propertyGrid = document.getElementById('propertyGrid');
    if (propertyGrid) {
        const rect = propertyGrid.getBoundingClientRect();
        if (rect.top < window.innerHeight * 0.7) {
            whisperShown = true;
            showAIWhisper('اضغط على أي عقار لسماع تفاصيله! 🔊');
        }
    }
});

/* 
   ═══════════════════════════════════════════════════════════════════════════
   13. AI HYBRID VALUATION (XGBoost + GPT-4o)
   Calls the backend API for smart property valuation
   ═══════════════════════════════════════════════════════════════════════════
*/
const AI_BACKEND_URL = 'http://localhost:8000';

window.getAIValuation = async function () {
    const location = document.getElementById('aiLocation').value;
    const size = parseInt(document.getElementById('aiSize').value) || 150;
    const finishing = parseInt(document.getElementById('aiFinishing').value);
    const floor = parseInt(document.getElementById('aiFloor').value) || 5;
    const isCompound = document.getElementById('aiCompound').checked ? 1 : 0;

    const resultEl = document.getElementById('aiValuationResult');

    // Show loading state
    resultEl.innerHTML = `
        <div style="text-align: center;">
            <i class="fas fa-spinner fa-spin" style="font-size: 48px; color: var(--color-gold-text); margin-bottom: 16px;"></i>
            <div style="font-size: 0.9rem; color: var(--color-trust-soft);">جاري تحليل السوق...</div>
        </div>
    `;

    try {
        const response = await fetch(`${AI_BACKEND_URL}/api/ai/hybrid-valuation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                location: location,
                size: size,
                finishing: finishing,
                floor: floor,
                is_compound: isCompound
            })
        });

        const data = await response.json();

        if (data.error) {
            resultEl.innerHTML = `
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ef4444; margin-bottom: 16px;"></i>
                <div style="color: #ef4444;">${data.error}</div>
            `;
            return;
        }

        // Format the result
        const price = data.predicted_price || 0;
        const pricePerSqm = data.price_per_sqm || Math.round(price / size);
        const marketStatus = data.market_status || 'Stable';
        const reasoning = data.reasoning_bullets || [];

        // Market status color
        const statusColors = {
            'Hot': { bg: '#fef2f2', text: '#dc2626', label: 'ساخن 🔥' },
            'Stable': { bg: '#eff6ff', text: '#2563eb', label: 'مستقر 📊' },
            'Cool': { bg: '#ecfdf5', text: '#059669', label: 'هادئ ❄️' }
        };
        const status = statusColors[marketStatus] || statusColors['Stable'];

        resultEl.innerHTML = `
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: var(--color-trust-soft); margin-bottom: 8px;">السعر العادل</div>
                <div style="font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #10b981, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;">
                    ${price.toLocaleString('en-EG')}
                </div>
                <div style="font-size: 1rem; color: var(--color-trust-mid);">جنيه مصري</div>
                <div style="font-size: 0.85rem; color: var(--color-trust-soft); margin-top: 4px;">
                    ${pricePerSqm.toLocaleString()} جنيه/م²
                </div>
                
                <div style="margin-top: 16px; display: inline-block; padding: 6px 16px; border-radius: 99px; background: ${status.bg}; color: ${status.text}; font-weight: 600;">
                    السوق: ${status.label}
                </div>
            </div>
            
            ${reasoning.length > 0 ? `
            <div style="margin-top: 20px; padding: 16px; background: rgba(255,255,255,0.6); border-radius: 12px; text-align: right;">
                <div style="font-weight: 600; margin-bottom: 8px; color: var(--color-trust-mid);">
                    <i class="fas fa-lightbulb" style="color: var(--color-gold-text);"></i>
                    لماذا هذا السعر:
                </div>
                <ul style="margin: 0; padding-right: 16px; font-size: 0.85rem; color: var(--color-trust-soft);">
                    ${reasoning.map(r => `<li style="margin-bottom: 4px;">${r}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            
            <div style="margin-top: 12px; font-size: 0.75rem; color: var(--color-trust-soft); text-align: center;">
                المصدر: ${data.source || 'XGBoost + GPT-4o Hybrid AI'}
            </div>
        `;

    } catch (error) {
        console.error('AI Valuation Error:', error);
        resultEl.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ef4444; margin-bottom: 16px;"></i>
            <div style="color: #ef4444;">حدث خطأ في الاتصال بالسيرفر</div>
            <div style="font-size: 0.8rem; color: var(--color-trust-soft); margin-top: 8px;">تأكد من تشغيل السيرفر على localhost:8000</div>
        `;
    }
};

/* 
   ═══════════════════════════════════════════════════════════════════════════
   14. AI LEGAL CONTRACT ANALYSIS (Egyptian Law AI)
   Scans contracts for risks using GPT-4o with Egyptian legal context
   ═══════════════════════════════════════════════════════════════════════════
*/
window.analyzeContract = async function () {
    const contractText = document.getElementById('contractText').value.trim();
    const resultEl = document.getElementById('legalCheckResult');

    if (contractText.length < 50) {
        resultEl.innerHTML = `
            <i class="fas fa-exclamation-circle" style="font-size: 48px; color: #f59e0b; margin-bottom: 16px;"></i>
            <div style="color: #f59e0b;">الرجاء إدخال نص العقد (50 حرف على الأقل)</div>
        `;
        return;
    }

    // Show loading state
    resultEl.innerHTML = `
        <div style="text-align: center;">
            <i class="fas fa-spinner fa-spin" style="font-size: 48px; color: #8b5cf6; margin-bottom: 16px;"></i>
            <div style="font-size: 0.9rem; color: var(--color-trust-soft);">جاري تحليل العقد قانونياً...</div>
        </div>
    `;

    try {
        const response = await fetch(`${AI_BACKEND_URL}/api/ai/audit-contract`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: contractText })
        });

        const data = await response.json();

        if (data.error) {
            resultEl.innerHTML = `
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ef4444; margin-bottom: 16px;"></i>
                <div style="color: #ef4444;">${data.error}</div>
            `;
            return;
        }

        // Format the result
        const riskScore = data.risk_score || 0;
        const verdict = data.verdict || 'Unknown';
        const redFlags = data.red_flags || [];
        const missingClauses = data.missing_clauses || [];
        const summary = data.legal_summary_arabic || '';

        // Risk level colors
        let riskColor, riskBg, riskLabel;
        if (riskScore < 30) {
            riskColor = '#10b981'; riskBg = '#ecfdf5'; riskLabel = 'آمن ✅';
        } else if (riskScore < 60) {
            riskColor = '#f59e0b'; riskBg = '#fffbeb'; riskLabel = 'حذر ⚠️';
        } else {
            riskColor = '#ef4444'; riskBg = '#fef2f2'; riskLabel = 'خطر 🚫';
        }

        // Verdict styling
        const verdictStyles = {
            'Safe to Sign': { bg: '#10b981', text: 'آمن للتوقيع ✅' },
            'Proceed with Caution': { bg: '#f59e0b', text: 'تابع بحذر ⚠️' },
            'DO NOT SIGN': { bg: '#ef4444', text: 'لا توقع! 🚫' }
        };
        const verdictStyle = verdictStyles[verdict] || { bg: '#64748b', text: verdict };

        resultEl.innerHTML = `
            <div style="text-align: center;">
                <!-- Risk Score -->
                <div style="display: inline-block; padding: 8px 20px; border-radius: 99px; background: ${riskBg}; color: ${riskColor}; font-weight: 700; font-size: 1.2rem; margin-bottom: 12px;">
                    المخاطر: ${riskScore}/100
                </div>
                
                <!-- Verdict -->
                <div style="padding: 12px; border-radius: 12px; background: ${verdictStyle.bg}; color: white; font-weight: 700; font-size: 1.1rem; margin-bottom: 16px;">
                    ${verdictStyle.text}
                </div>
            </div>
            
            ${redFlags.length > 0 ? `
            <div style="padding: 12px; background: #fef2f2; border-radius: 8px; margin-bottom: 12px; text-align: right;">
                <div style="font-weight: 600; color: #dc2626; margin-bottom: 8px;">
                    <i class="fas fa-flag"></i> علامات خطر:
                </div>
                <ul style="margin: 0; padding-right: 16px; font-size: 0.85rem; color: #b91c1c;">
                    ${redFlags.map(f => `<li style="margin-bottom: 4px;">${f}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            
            ${missingClauses.length > 0 ? `
            <div style="padding: 12px; background: #fffbeb; border-radius: 8px; margin-bottom: 12px; text-align: right;">
                <div style="font-weight: 600; color: #d97706; margin-bottom: 8px;">
                    <i class="fas fa-clipboard-list"></i> بنود ناقصة:
                </div>
                <ul style="margin: 0; padding-right: 16px; font-size: 0.85rem; color: #b45309;">
                    ${missingClauses.map(c => `<li style="margin-bottom: 4px;">${c}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            
            ${summary ? `
            <div style="padding: 12px; background: rgba(255,255,255,0.6); border-radius: 8px; text-align: right;">
                <div style="font-weight: 600; color: var(--color-trust-mid); margin-bottom: 8px;">
                    <i class="fas fa-file-alt"></i> الملخص:
                </div>
                <div style="font-size: 0.85rem; color: var(--color-trust-soft); line-height: 1.6;">${summary}</div>
            </div>
            ` : ''}
        `;

    } catch (error) {
        console.error('Legal Analysis Error:', error);
        resultEl.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ef4444; margin-bottom: 16px;"></i>
            <div style="color: #ef4444;">حدث خطأ في الاتصال بالسيرفر</div>
            <div style="font-size: 0.8rem; color: var(--color-trust-soft); margin-top: 8px;">تأكد من تشغيل السيرفر على localhost:8000</div>
        `;
    }
};
