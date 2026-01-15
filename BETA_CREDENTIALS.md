# Osool Phase 1 - Beta Test Credentials

**CONFIDENTIAL - Do not share publicly**

## Overview

This document contains login credentials for 14 beta test accounts created for Osool Phase 1 launch.
All accounts are pre-verified and ready to use immediately.

## Core Team Accounts (4)

| Name | Email | Password | Role | Purpose |
|------|-------|----------|------|---------|
| Mustafa | mustafa@osool.eg | Osool2025 | Admin | Product Lead - Full access |
| Hani | hani@osool.eg | Osool2025 | Admin | Tech Lead - Full access |
| Abady | abady@osool.eg | Osool2025 | Admin | Business - Full access |
| Sama | sama@osool.eg | Osool2025 | Admin | Design - Full access |

## Beta Tester Accounts (10)

| # | Email | Password | Purpose |
|---|-------|----------|---------|
| 1 | tester1@osool.eg | Osool2025 | General testing & QA |
| 2 | tester2@osool.eg | Osool2025 | Arabic language testing |
| 3 | tester3@osool.eg | Osool2025 | Mobile device testing |
| 4 | tester4@osool.eg | Osool2025 | English language testing |
| 5 | tester5@osool.eg | Osool2025 | Investor persona testing |
| 6 | tester6@osool.eg | Osool2025 | First-time buyer persona |
| 7 | tester7@osool.eg | Osool2025 | Load testing & performance |
| 8 | tester8@osool.eg | Osool2025 | Edge case testing |
| 9 | tester9@osool.eg | Osool2025 | Investor demo account |
| 10 | tester10@osool.eg | Osool2025 | Spare / backup account |

---

## Test Scenarios

### Scenario 1: First-Time Buyer Journey (Arabic)

**Account**: tester2@osool.eg
**Objective**: Test Arabic language support and first-time buyer experience

**Test Steps**:
1. Sign in at https://osool.vercel.app/login
2. Navigate to "Chat with AMR"
3. Type in Arabic: "عايز شقة في التجمع الخامس 3 غرف بحدود 3 مليون جنيه"
4. Verify AMR responds in Egyptian Arabic
5. Check that property cards appear inline in chat
6. Ask for payment plan: "خطة الدفع"
7. Verify payment timeline visualization appears
8. Ask for investment analysis: "تحليل الاستثمار"
9. Verify investment scorecard appears

**Expected Results**:
- ✅ AMR responds entirely in Arabic
- ✅ Property recommendations match budget (3M EGP) and location (5th Settlement)
- ✅ Payment timeline shows down payment, monthly installments, total cost
- ✅ Investment scorecard shows ROI, match score, risk level

---

### Scenario 2: Investor Journey (English)

**Account**: tester5@osool.eg
**Objective**: Test English language support and investor-focused features

**Test Steps**:
1. Sign in
2. Go to "Chat with AMR"
3. Type: "Show me investment properties in New Cairo under 5M EGP with good ROI"
4. Verify AMR responds in English
5. Check property recommendations
6. Ask: "What's the ROI on the first property?"
7. Verify investment scorecard appears automatically
8. Ask: "Compare the top 3 properties"
9. Verify comparison matrix appears

**Expected Results**:
- ✅ AMR responds in professional English
- ✅ Recommendations focus on investment potential
- ✅ Investment scorecard shows rental yield, appreciation forecast
- ✅ Comparison matrix shows side-by-side property comparison

---

### Scenario 3: Proactive Recommendation Test

**Account**: tester6@osool.eg
**Objective**: Test AMR's proactive recommendation feature

**Test Steps**:
1. Sign in
2. Chat: "I'm looking for a property"
3. AMR asks clarifying questions
4. Respond: "3 bedrooms, family-friendly, around 4M"
5. AMR shows properties
6. Say: "I like the first one"
7. **Expected**: AMR proactively suggests "Let me compare this with 2 similar options" WITHOUT being asked

**Expected Results**:
- ✅ AMR doesn't just confirm, but proactively suggests comparison
- ✅ Comparison matrix appears automatically
- ✅ AMR suggests next steps (payment plan, investment analysis)

---

### Scenario 4: Market Intelligence Test

**Account**: tester4@osool.eg
**Objective**: Test market analysis and visualization features

**Test Steps**:
1. Sign in
2. Chat: "What's the market trend in New Cairo?"
3. Verify market trend chart appears with:
   - Historical price data
   - Growth percentage
   - Future forecast
4. Ask: "Compare New Cairo vs Sheikh Zayed"
5. Verify area comparison visualization

**Expected Results**:
- ✅ Market trend chart shows meaningful data
- ✅ AMR explains trends in context (e.g., "New Cairo growing 12% annually")
- ✅ Area comparison is data-driven with clear insights

---

### Scenario 5: Mobile Experience

**Account**: tester3@osool.eg
**Objective**: Test mobile responsiveness

**Test Device**: iPhone or Android phone
**Test Steps**:
1. Open https://osool.vercel.app on mobile browser
2. Sign in
3. Navigate through: Home → Chat with AMR → Properties
4. Start a chat with AMR
5. Check that visualizations render correctly on mobile

**Expected Results**:
- ✅ All pages are responsive
- ✅ Chat interface works on mobile (no horizontal scroll)
- ✅ Visualizations scale to fit mobile screen
- ✅ CTA buttons are easily tappable

---

## Investor Demo Scenario

**Demo Account**: tester9@osool.eg
**Duration**: 10 minutes
**Audience**: Potential investors

### Demo Script

**1. Landing Page (30 seconds)**
- Show professional hero section
- Highlight stats: "3,274 Properties | AI-Powered | 24/7 Available"
- Point out bilingual support (Arabic + English)

**2. AMR Chat - Arabic (2 minutes)**
- Click "Chat with AMR"
- Type: "عايز شقة في التجمع 3 غرف بحدود 4 مليون"
- Show instant AI response in Egyptian Arabic
- Property cards appear inline
- Investment scorecard appears automatically
- **Key point**: "AMR calculated ROI without being asked - that's proactive AI"

**3. Proactive Recommendations (1 minute)**
- Type: "أكمل" (continue)
- AMR suggests: "Let me compare with 2 similar options"
- Comparison matrix appears
- **Key point**: "AMR doesn't wait for instructions - it thinks ahead"

**4. Payment Planning (1 minute)**
- Type: "خطة الدفع"
- Payment timeline visualization appears
- Show: Down payment, monthly installments, total cost
- **Key point**: "All calculations use real CBE interest rates"

**5. Market Intelligence (30 seconds)**
- Type: "Market trends in New Cairo"
- Market trend chart appears
- Show historical data + forecast
- **Key point**: "Powered by 3,000+ transaction data points and XGBoost ML model"

**6. Switch to English (30 seconds)**
- Open new chat or continue
- Type in English: "What's the ROI on this property?"
- AMR switches to English seamlessly
- **Key point**: "Language detection is automatic - no manual switching"

**7. Competitive Advantage (1 minute)**
Show slide comparing Osool vs Nawy.com:
- Language: Nawy (English only) vs Osool (Bilingual with Egyptian dialect)
- AI: Nawy (Algorithm) vs Osool (Claude 3.5 + XGBoost + GPT-4o)
- Analysis: Nawy (None) vs Osool (4 visualization types)
- Proactivity: Nawy (Passive) vs Osool (Proactive recommendations)

**8. Technical Architecture (1 minute)**
- Backend: Railway Pro (PostgreSQL + Redis + FastAPI)
- Frontend: Vercel Pro (Next.js 16 + React 19)
- AI: Claude 3.5 Sonnet + XGBoost + GPT-4o (hybrid brain)
- Database: 3,274 properties with semantic search (pgvector)
- **Key point**: "Production-ready, scalable infrastructure"

**9. Traction & Next Steps (1 minute)**
- Phase 1: AI-first, launched
- Database: 3,274 properties
- Technology: State-of-the-art AI stack
- Target: 1,000 users, 50 transactions in Q1 2025
- Funding need: Phase 2 expansion (payment gateway, mobile app, KYC)

**10. Q&A (2 minutes)**
- Answer investor questions
- Provide demo credentials for hands-on testing
- Share technical architecture docs

---

## Security Notes

⚠️ **Important Security Measures**:

1. **Password Policy**: All beta accounts use the same password (Osool2025) for convenience. In production, enforce strong unique passwords.

2. **Access Control**: Core team accounts have admin role for full access. Tester accounts have investor role with limited permissions.

3. **Data Privacy**: Beta testers should not upload sensitive personal information. All test data may be reviewed by the core team.

4. **Account Expiry**: These accounts are for Phase 1 beta testing only. They may be deactivated after beta period ends.

5. **Credential Sharing**: Do NOT share these credentials publicly. Only provide to authorized beta testers and investors.

---

## Troubleshooting

### Issue: "Invalid email or password"
**Solution**:
- Verify email is exactly as shown (e.g., `tester1@osool.eg`)
- Password is case-sensitive: `Osool2025`
- Check if backend database has been seeded (run `python scripts/seed_beta_users.py`)

### Issue: "AMR not responding"
**Solution**:
- Check backend is running on Railway
- Verify ANTHROPIC_API_KEY is set in Railway environment variables
- Check backend logs for errors

### Issue: "Properties not loading"
**Solution**:
- Verify property database has been seeded
- Check `/api/properties` endpoint returns data
- Verify DATABASE_URL is correctly configured

### Issue: "Visualizations not appearing"
**Solution**:
- Check browser console for errors
- Verify response from `/api/chat` includes `visualizations` field
- Try refreshing the page

---

## Support Contacts

**Technical Issues**: hani@osool.eg
**Product Questions**: mustafa@osool.eg
**Access Issues**: sama@osool.eg

---

## Change Log

**2025-01-14**: Initial beta credentials created for Phase 1 launch
- Created 4 admin accounts (core team)
- Created 10 investor accounts (beta testers)
- All accounts pre-verified and ready to use
- Documented test scenarios and demo script

---

**Last Updated**: January 14, 2025
**Document Version**: 1.0
**Status**: Active
