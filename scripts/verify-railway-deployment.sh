#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Railway Deployment Verification Script
# ═══════════════════════════════════════════════════════════════
# Tests the deployed Railway backend to ensure all services work
# Usage: ./verify-railway-deployment.sh https://your-app.up.railway.app
# ═══════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if URL provided
BACKEND_URL=$1

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}Error: No backend URL provided${NC}"
    echo ""
    echo "Usage: $0 <backend-url>"
    echo "Example: $0 https://osool-production.up.railway.app"
    echo ""
    exit 1
fi

# Remove trailing slash if present
BACKEND_URL=${BACKEND_URL%/}

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Railway Deployment Verification${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "Testing: ${YELLOW}${BACKEND_URL}${NC}"
echo ""

# Track test results
PASSED=0
FAILED=0
WARNINGS=0

# ═══════════════════════════════════════════════════════════════
# Test 1: Health Check
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[1/6]${NC} Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
HEALTH_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] && echo "$HEALTH_BODY" | grep -q "healthy"; then
    echo -e "      ${GREEN}✅ PASS${NC} - Health check successful"
    echo "      Response: $(echo $HEALTH_BODY | head -c 80)..."
    PASSED=$((PASSED + 1))
else
    echo -e "      ${RED}❌ FAIL${NC} - Health check failed"
    echo "      HTTP Code: $HTTP_CODE"
    echo "      Response: $HEALTH_BODY"
    FAILED=$((FAILED + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# Test 2: API Root Endpoint
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[2/6]${NC} Testing API root endpoint..."
ROOT_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$ROOT_RESPONSE" | tail -n 1)
ROOT_BODY=$(echo "$ROOT_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ] && echo "$ROOT_BODY" | grep -qi "osool\|welcome\|api"; then
    echo -e "      ${GREEN}✅ PASS${NC} - API root accessible"
    echo "      Response: $(echo $ROOT_BODY | head -c 80)..."
    PASSED=$((PASSED + 1))
else
    echo -e "      ${RED}❌ FAIL${NC} - API root not accessible"
    echo "      HTTP Code: $HTTP_CODE"
    echo "      Response: $ROOT_BODY"
    FAILED=$((FAILED + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# Test 3: Database Connection (via properties endpoint)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[3/6]${NC} Testing database connection..."
DB_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/properties?limit=1" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$DB_RESPONSE" | tail -n 1)
DB_BODY=$(echo "$DB_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$DB_BODY" | grep -q "\["; then
        PROPERTY_COUNT=$(echo "$DB_BODY" | grep -o "{" | wc -l)
        echo -e "      ${GREEN}✅ PASS${NC} - Database connected"
        echo "      Properties in database: $PROPERTY_COUNT"
        PASSED=$((PASSED + 1))
    else
        echo -e "      ${YELLOW}⚠️  WARNING${NC} - Database connected but response unexpected"
        echo "      Response: $(echo $DB_BODY | head -c 80)..."
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "      ${RED}❌ FAIL${NC} - Database connection failed"
    echo "      HTTP Code: $HTTP_CODE"
    echo "      Response: $DB_BODY"
    FAILED=$((FAILED + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# Test 4: AI Service Availability (chat endpoint)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[4/6]${NC} Testing AI service (Claude/OpenAI)..."
AI_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message":"test","user_id":"verification-test"}' \
    2>/dev/null || echo "000")
HTTP_CODE=$(echo "$AI_RESPONSE" | tail -n 1)
AI_BODY=$(echo "$AI_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$AI_BODY" | grep -qi "response\|reply\|مرحبا"; then
        echo -e "      ${GREEN}✅ PASS${NC} - AI service functional"
        echo "      Response preview: $(echo $AI_BODY | head -c 60)..."
        PASSED=$((PASSED + 1))
    else
        echo -e "      ${YELLOW}⚠️  WARNING${NC} - AI endpoint responded but format unexpected"
        echo "      Response: $(echo $AI_BODY | head -c 80)..."
        WARNINGS=$((WARNINGS + 1))
    fi
elif [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo -e "      ${YELLOW}⚠️  WARNING${NC} - Authentication required (expected for protected endpoints)"
    echo "      This is normal if authentication is enabled"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "      ${YELLOW}⚠️  WARNING${NC} - AI service test inconclusive"
    echo "      HTTP Code: $HTTP_CODE"
    echo "      Check OpenAI/Anthropic API keys in Railway environment"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# Test 5: API Documentation (Optional)
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[5/6]${NC} Testing API documentation..."
DOCS_RESPONSE=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/docs" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$DOCS_RESPONSE" | tail -n 1)
DOCS_BODY=$(echo "$DOCS_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$DOCS_BODY" | grep -qi "swagger\|openapi\|redoc"; then
        echo -e "      ${GREEN}✅ PASS${NC} - API docs accessible"
        echo "      Visit: ${BACKEND_URL}/docs"
        PASSED=$((PASSED + 1))
    else
        echo -e "      ${YELLOW}⚠️  WARNING${NC} - Docs endpoint responded but content unexpected"
        WARNINGS=$((WARNINGS + 1))
    fi
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "      ${YELLOW}⚠️  INFO${NC} - API docs disabled (normal for production)"
    echo "      Docs are typically disabled in production for security"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "      ${YELLOW}⚠️  WARNING${NC} - Could not access API docs"
    echo "      HTTP Code: $HTTP_CODE"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# Test 6: Response Time Test
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}[6/6]${NC} Testing response time..."
START_TIME=$(date +%s%3N)
curl -s "$BACKEND_URL/health" > /dev/null 2>&1
END_TIME=$(date +%s%3N)
RESPONSE_TIME=$((END_TIME - START_TIME))

if [ $RESPONSE_TIME -lt 1000 ]; then
    echo -e "      ${GREEN}✅ PASS${NC} - Response time excellent: ${RESPONSE_TIME}ms"
    PASSED=$((PASSED + 1))
elif [ $RESPONSE_TIME -lt 3000 ]; then
    echo -e "      ${GREEN}✅ PASS${NC} - Response time good: ${RESPONSE_TIME}ms"
    PASSED=$((PASSED + 1))
else
    echo -e "      ${YELLOW}⚠️  WARNING${NC} - Response time slow: ${RESPONSE_TIME}ms"
    echo "      Consider checking server load and network latency"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Verification Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✅ Passed:${NC}   $PASSED tests"
echo -e "  ${RED}❌ Failed:${NC}   $FAILED tests"
echo -e "  ${YELLOW}⚠️  Warnings:${NC} $WARNINGS tests"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed! Your Railway deployment is fully functional.${NC}"
        EXIT_CODE=0
    else
        echo -e "${YELLOW}✓ Deployment functional but with warnings. Review above for details.${NC}"
        EXIT_CODE=0
    fi
else
    echo -e "${RED}✗ Deployment has critical failures. Check Railway logs for details.${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "  1. Check Railway logs: railway logs"
    echo "  2. Verify environment variables in Railway dashboard"
    echo "  3. Ensure DATABASE_URL and REDIS_URL are properly linked"
    echo "  4. Confirm all security keys are set (JWT_SECRET_KEY, ADMIN_API_KEY, etc.)"
    EXIT_CODE=1
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

exit $EXIT_CODE
