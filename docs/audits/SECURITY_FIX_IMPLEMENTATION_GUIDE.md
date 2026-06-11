# SECURITY FIXES IMPLEMENTATION GUIDE
## Osool Platform - March 6, 2026

This document provides instructions for implementing all security fixes identified in the comprehensive audit.

---

## 📁 NEW FILES CREATED

### Backend Security Modules

1. **`backend/app/middleware/csrf_protection.py`**
   - CSRF protection middleware
   - Double submit cookie pattern
   - Origin/Referer validation
   - Token rotation

2. **`backend/app/auth_cookies.py`**
   - Cookie-based authentication (replaces localStorage)
   - httpOnly cookies for access tokens
   - Refresh token rotation
   - Backward compatibility with Bearer tokens

3. **`backend/app/security/input_validation.py`**
   - Comprehensive input sanitization
   - XSS prevention
   - SQL injection prevention
   - Strong password validation
   - Path traversal protection

4. **`backend/app/security/account_lockout.py`**
   - Brute force protection
   - Progressive delays (exponential backoff)
   - Account lockout after N failed attempts
   - Redis-backed storage (distributed-safe)

5. **`backend/app/security/audit_logging.py`**
   - Structured audit logging
   - GDPR compliance
   - PII redaction
   - Tamper-evident logging

### Frontend Security Modules

6. **`web/lib/api-secure.ts`**
   - Secure API client with cookie auth
   - CSRF token management
   - Automatic token refresh
   - No localStorage usage

---

## 🔧 INTEGRATION STEPS

### Step 1: Update Backend Main Application

Edit `backend/app/main.py`:

```python
# Add at top of file
from app.middleware.csrf_protection import CSRFProtectionMiddleware
from app.auth_cookies import CookieOrBearerAuth

# Add after SecurityHeadersMiddleware (before CORS)
app.add_middleware(CSRFProtectionMiddleware, allowed_origins=origins)

# Update CORS to allow credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://osool-[a-z0-9]+-mustafas-projects-[a-z0-9]+\.vercel\.app",
    allow_credentials=True,  # CRITICAL: Must be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 2: Update Authentication Endpoints

Edit `backend/app/api/auth_endpoints.py`:

```python
from fastapi import Response
from app.auth_cookies import (
    create_access_token_cookie,
    create_refresh_token_cookie,
    clear_auth_cookies
)
from app.security.account_lockout import (
    check_account_lockout,
    record_login_failure,
    record_login_success
)
from app.security.audit_logging import (
    audit_login_success,
    audit_login_failed,
    audit_logout
)
from app.security.input_validation import SecureSignupRequest

@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Secure login with cookie-based auth."""
    email = form_data.username
    
    # Check account lockout BEFORE attempting authentication
    await check_account_lockout(request, email)
    
    from sqlalchemy import select
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        # Log failed attempt
        await record_login_failure(request, email)
        audit_login_failed(request, email, "invalid_credentials")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Reset lockout on successful login
    await record_login_success(email)
    
    # Create cookies (NOT returning token in body)
    token_data = {"sub": user.email, "role": user.role}
    create_access_token_cookie(response, token_data)
    create_refresh_token_cookie(response, token_data)
    
    # Audit log
    audit_login_success(request, user.id, user.email)
    
    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email
    }

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Logout and clear cookies."""
    # Invalidate token (blacklist)
    token = request.cookies.get("access_token")
    if token:
        from app.auth import invalidate_token
        invalidate_token(token)
    
    # Clear cookies
    clear_auth_cookies(response)
    
    # Audit log
    audit_logout(request, current_user.id, current_user.email)
    
    return {"status": "logged_out"}

@router.post("/signup")
async def signup(
    request: Request,
    response: Response,
    req: SecureSignupRequest,  # Use secure validation model
    db: AsyncSession = Depends(get_db)
):
    """Secure signup with validation."""
    # All validation done by SecureSignupRequest Pydantic model
    # ... rest of signup logic
```

### Step 3: Add CSRF Token Endpoint

Add to `backend/app/api/auth_endpoints.py`:

```python
@router.get("/csrf-token")
async def get_csrf_token(request: Request):
    """
    Get CSRF token for SPA initialization.
    Token is also set in cookie by middleware.
    """
    csrf_token = request.headers.get("X-CSRF-Token") or "pending"
    return {"csrf_token": csrf_token}

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user info (for authentication check)."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified
    }
```

### Step 4: Update Frontend Auth Context

Replace `web/contexts/AuthContext.tsx`:

```typescript
"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getCurrentUser, login as apiLogin, logout as apiLogout } from '@/lib/api-secure';

interface User {
  id: string;
  email?: string;
  full_name?: string;
  role?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();
  }, []);

  const login = async (email: string, password: string) => {
    await apiLogin(email, password);
    await refreshUser();
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, loading, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### Step 5: Update All API Imports in Frontend

Replace all instances of:
```typescript
import api from '@/lib/api';
```

With:
```typescript
import api from '@/lib/api-secure';
```

### Step 6: Environment Variables

Add to backend `.env`:

```bash
# CSRF Protection
CSRF_SECRET_KEY=<generate with: openssl rand -hex 32>

# Audit Logging
AUDIT_LOG_DIR=/var/log/osool/audit

# Account Lockout
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
```

### Step 7: Database Migration (Optional)

If storing audit logs in database instead of files, create table:

```sql
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    user_id INTEGER REFERENCES users(id),
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    action VARCHAR(50),
    result VARCHAR(20),
    details JSONB,
    request_id VARCHAR(100),
    session_id VARCHAR(100)
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
```

---

## 🧪 TESTING

### Test 1: Cookie Authentication
```bash
# Login should set cookies
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePass123!" \
  -v

# Check for Set-Cookie headers in response
```

### Test 2: CSRF Protection
```bash
# Request without CSRF token should fail (403)
curl -X POST http://localhost:8000/api/some-endpoint \
  -H "Cookie: access_token=..." \
  -d '{"data": "value"}'

# Should return: {"error": "CSRF token missing or invalid"}
```

### Test 3: Account Lockout
```bash
# Try logging in 6 times with wrong password
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -d "username=test@example.com&password=wrong"
done

# 6th attempt should return 429 (account locked)
```

### Test 4: Input Validation
```python
import requests

# Test XSS injection
response = requests.post('http://localhost:8000/api/auth/signup', json={
    'full_name': '<script>alert("XSS")</script>',
    'email': 'test@example.com',
    'password': 'SecurePass123!',
    'phone_number': '+201234567890',
    'national_id': '12345678901234'
})

# Should return 400 with validation error
```

---

## 📊 MONITORING

### Check Audit Logs
```bash
tail -f /var/log/osool/audit/audit.log | jq .
```

### Check Critical Events
```bash
tail -f /var/log/osool/audit/critical.log | jq .
```

### Monitor Lockouts
```python
from app.security.account_lockout import lockout_manager

info = lockout_manager.get_lockout_info("test@example.com")
print(info)
# Output: {"is_locked": True, "locked_until": "2026-03-06T15:30:00", "failed_attempts": 5, "max_attempts": 5}
```

---

## 🔐 SECURITY CHECKLIST

After implementation, verify:

- [ ] JWT tokens NOT in localStorage
- [ ] Cookies have httpOnly flag
- [ ] Cookies have Secure flag (production)
- [ ] Cookies have SameSite=Strict
- [ ] CSRF token required for POST/PUT/DELETE
- [ ] Account locks after 5 failed attempts
- [ ] Passwords require 12+ chars with complexity
- [ ] All inputs validated and sanitized
- [ ] Audit logs being written
- [ ] No PII in JWT tokens
- [ ] No hardcoded secrets in code
- [ ] CORS allows credentials
- [ ] All endpoints authenticated (except public API docs)

---

## 🚨 ROLLBACK PLAN

If issues arise:

1. Remove CSRF middleware from main.py
2. Revert to old api.ts (with localStorage)
3. Disable account lockout in auth endpoints
4. Restore database backup if needed

---

## 📚 ADDITIONAL RESOURCES

- [OWASP JWT Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheatsheet.html)
- [CSRF Protection Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Input Validation Guide](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)

---

**Implementation Priority:**
1. CRITICAL (Week 1): Cookie auth, CSRF, Input validation
2. HIGH (Week 2): Account lockout, Audit logging
3. MEDIUM (Week 3): Additional security headers, monitoring
4. LOW (Week 4): Documentation, training

**Questions?** Review COMPREHENSIVE_SECURITY_AUDIT.md for full details.
