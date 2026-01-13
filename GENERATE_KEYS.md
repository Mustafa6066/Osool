# 🔐 Generate Production Security Keys

Before deploying to Railway and Vercel, you need to generate secure keys. Follow these steps:

---

## 1️⃣ Generate JWT Secret Key

### Windows (PowerShell)
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

### Linux/Mac (Terminal)
```bash
openssl rand -hex 32
```

### Alternative (Any OS with Python)
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Save the output** - You'll need this for Railway's `JWT_SECRET_KEY`

---

## 2️⃣ Generate Wallet Encryption Key

### Any OS (Python required)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Expected output format:**
```
gAAAAABhZXl0aGlz...base64_string...
```

**Save the output** - You'll need this for Railway's `WALLET_ENCRYPTION_KEY`

---

## 3️⃣ Get API Keys

### OpenAI API Key
1. Go to: https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Name it: `Osool Production`
4. Copy the key (starts with `sk-proj-...`)

### Anthropic API Key (for AMR Agent)
1. Go to: https://console.anthropic.com/settings/keys
2. Click **"Create Key"**
3. Name it: `Osool Production AMR`
4. Copy the key (starts with `sk-ant-api03-...`)

### Supabase Credentials
1. Go to your Supabase project
2. Navigate to: **Project Settings** → **API**
3. Copy:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Anon/Public Key**: Long string (safe to use in frontend)

### ThirdWeb Client ID
1. Go to: https://thirdweb.com/dashboard
2. Select your project (or create new)
3. Go to **Settings** → **API Keys**
4. Copy the **Client ID**

---

## 4️⃣ Organize Your Keys

Create a secure note in your password manager with this template:

```
OSOOL PRODUCTION KEYS
=====================

JWT Secret:
[paste generated key]

Wallet Encryption:
[paste generated key]

OpenAI API Key:
sk-proj-[paste key]

Anthropic API Key:
sk-ant-api03-[paste key]

Supabase URL:
https://[your-project].supabase.co

Supabase Key:
[paste key]

ThirdWeb Client ID:
[paste key]

Generated on: 2026-01-13
```

---

## ⚠️ Security Best Practices

1. **NEVER commit these keys to Git**
2. **Store in a password manager** (1Password, LastPass, Bitwarden)
3. **Rotate keys every 90 days**
4. **Use different keys for dev and production**
5. **Enable 2FA on all service accounts**

---

## 🎯 Next Steps

After generating all keys:
1. Open `RAILWAY_ENV_TEMPLATE.txt`
2. Replace all placeholder values
3. Copy to Railway dashboard
4. Proceed with deployment!

---

**Security Note:** These keys grant access to your production environment and AI services. Treat them like passwords and never share them publicly.
