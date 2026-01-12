# Google OAuth Setup Guide

## Phase 2 Authentication - Google OAuth Integration

The backend is ready and AuthModal has the handler. Follow these steps to complete the integration:

### Step 1: Install Package

```bash
cd d:\Osool\web
npm install @react-oauth/google
```

### Step 2: Get Google Client ID

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Application type: "Web application"
6. Authorized JavaScript origins:
   - `http://localhost:3000` (development)
   - `https://osool.com` (production)
7. Authorized redirect URIs:
   - `http://localhost:3000` (development)
   - `https://osool.com` (production)
8. Copy the **Client ID** and **Client Secret**

### Step 3: Update Environment Variables

**.env.local** (frontend):
```bash
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
```

**backend/.env** (backend):
```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

### Step 4: Wrap App with GoogleOAuthProvider

**Option A: In `web/app/layout.tsx`** (Recommended):

```typescript
import { GoogleOAuthProvider } from '@react-oauth/google';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
          {children}
        </GoogleOAuthProvider>
      </body>
    </html>
  )
}
```

**Option B: In `web/app/page.tsx`**:

```typescript
import { GoogleOAuthProvider } from '@react-oauth/google';

export default function Home() {
  return (
    <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID!}>
      <main className="min-h-screen...">
        {/* Existing content */}
      </main>
    </GoogleOAuthProvider>
  );
}
```

### Step 5: Replace Placeholder in AuthModal.tsx

Find this section (around line 479-487):
```typescript
{/* Google Sign-In Button Placeholder */}
<div className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-center">
  <p className="text-sm text-gray-600">
    <strong>Google OAuth Integration:</strong> Install...
  </p>
</div>
```

Replace with:
```typescript
import { GoogleLogin } from '@react-oauth/google';

// In the component (add this import at top)

// Replace the placeholder div with:
<GoogleLogin
  onSuccess={handleGoogleSuccess}
  onError={() => setError("Google authentication failed")}
  useOneTap
  theme="outline"
  size="large"
  text="signin_with"
  shape="rectangular"
/>
```

### Step 6: Test the Integration

1. Start the backend: `cd backend && python main.py`
2. Start the frontend: `cd web && npm run dev`
3. Open AuthModal → Email tab → Click "Google Sign In"
4. Verify:
   - Google consent screen appears
   - After consent, user is logged in
   - Token is saved to `localStorage.access_token`
   - User is redirected to dashboard

### Backend Endpoint

The backend endpoint is already implemented at `backend/app/api/auth_endpoints.py:255-302`:

```python
@router.post("/google", response_model=AuthResponse)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    # Verify Google token
    user_info = await verify_google_token(request.id_token)

    # Get or create user
    user = get_or_create_user_by_email(db, user_info['email'], user_info['name'])

    # Return JWT
    access_token = create_access_token(data={
        "sub": user.email,
        "wallet": user.wallet_address,
        "role": user.role
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "is_new_user": user.full_name == 'Google User'
    }
```

### Flow Diagram

```
User clicks "Sign in with Google"
    ↓
Google OAuth popup opens
    ↓
User grants permission
    ↓
Frontend receives `credential` (ID token)
    ↓
Frontend sends to `/api/auth/google`
    ↓
Backend verifies with Google servers
    ↓
Backend creates/gets user from database
    ↓
Backend returns JWT access_token
    ↓
Frontend saves token + redirects to dashboard
```

### Troubleshooting

**Error: "Token verification failed"**
- Check `GOOGLE_CLIENT_ID` matches in both frontend and backend
- Ensure the token hasn't expired (< 1 hour old)

**Error: "redirect_uri_mismatch"**
- Add your domain to Authorized redirect URIs in Google Console
- Include both http://localhost:3000 and production URL

**No popup appears**
- Check browser popup blocker
- Try incognito mode
- Verify NEXT_PUBLIC_GOOGLE_CLIENT_ID is set

### Security Notes

- Never commit GOOGLE_CLIENT_SECRET to Git
- Use environment variables for all secrets
- Rotate client secret periodically (every 90 days)
- Monitor usage in Google Cloud Console

---

**Status**: Backend ✅ Complete | Frontend ⚠️ Requires package installation
