# Osool Admin API Guide

## Overview

This guide explains how administrators can access and monitor user chats and activity on the Osool platform.

---

## Authentication

All admin endpoints require the `X-Admin-Key` header with the value of the `ADMIN_API_KEY` environment variable.

```bash
# Example header
X-Admin-Key: your-admin-api-key-here
```

---

## Admin Endpoints

### 1. Get All Users with Chat Statistics

**Endpoint:** `GET /api/admin/users`

Returns a list of all registered users with their chat activity statistics.

```bash
curl -X GET "https://your-api.com/api/admin/users" \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

**Response:**
```json
{
  "total_users": 14,
  "users": [
    {
      "id": 1,
      "email": "mustafa@osool.eg",
      "full_name": "Mustafa",
      "role": "admin",
      "created_at": "2025-01-19T10:00:00Z",
      "message_count": 45,
      "last_activity": "2025-01-19T14:30:00Z"
    },
    ...
  ]
}
```

---

### 2. Get All Recent Chat Messages

**Endpoint:** `GET /api/admin/chats?limit=100`

Returns the most recent chat messages across all users.

```bash
curl -X GET "https://your-api.com/api/admin/chats?limit=100" \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

**Response:**
```json
{
  "total_messages": 100,
  "messages": [
    {
      "id": 1234,
      "session_id": "abc123",
      "user_id": 1,
      "user_email": "mustafa@osool.eg",
      "user_name": "Mustafa",
      "role": "user",
      "content": "عاوز شقه في التجمع",
      "created_at": "2025-01-19T14:30:00Z",
      "has_properties": false
    },
    {
      "id": 1235,
      "session_id": "abc123",
      "user_id": 1,
      "user_email": "mustafa@osool.eg",
      "user_name": "Mustafa",
      "role": "assistant",
      "content": "اهلا بيك في أصول يا باشا!...",
      "created_at": "2025-01-19T14:30:05Z",
      "has_properties": true
    }
  ]
}
```

---

### 3. Get Specific User's Chat History

**Endpoint:** `GET /api/admin/chats/{user_id}`

Returns all chat sessions and messages for a specific user.

```bash
curl -X GET "https://your-api.com/api/admin/chats/1" \
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "mustafa@osool.eg",
    "full_name": "Mustafa",
    "role": "admin"
  },
  "total_sessions": 3,
  "total_messages": 45,
  "sessions": [
    {
      "session_id": "abc123",
      "messages": [
        {
          "id": 1,
          "role": "user",
          "content": "عاوز شقه في التجمع",
          "created_at": "2025-01-19T10:00:00Z",
          "has_properties": false
        },
        {
          "id": 2,
          "role": "assistant",
          "content": "اهلا بيك في أصول...",
          "created_at": "2025-01-19T10:00:05Z",
          "has_properties": true
        }
      ],
      "message_count": 12,
      "first_message_at": "2025-01-19T10:00:00Z",
      "last_message_at": "2025-01-19T10:15:00Z"
    }
  ]
}
```

---

## Database Direct Access

For more advanced queries, you can connect directly to the PostgreSQL database.

### Connect to Railway PostgreSQL

```bash
# Using Railway CLI
railway connect postgres

# Or using psql directly
psql $DATABASE_URL
```

### Useful SQL Queries

**View all chat messages with user info:**
```sql
SELECT
    cm.id,
    cm.session_id,
    cm.role,
    cm.content,
    cm.created_at,
    u.email,
    u.full_name
FROM chat_messages cm
LEFT JOIN users u ON cm.user_id = u.id
ORDER BY cm.created_at DESC
LIMIT 100;
```

**Get message count per user:**
```sql
SELECT
    u.id,
    u.email,
    u.full_name,
    COUNT(cm.id) as message_count,
    MAX(cm.created_at) as last_activity
FROM users u
LEFT JOIN chat_messages cm ON u.id = cm.user_id
GROUP BY u.id
ORDER BY message_count DESC;
```

**Get all sessions for a specific user:**
```sql
SELECT
    session_id,
    COUNT(*) as message_count,
    MIN(created_at) as started_at,
    MAX(created_at) as last_message
FROM chat_messages
WHERE user_id = 1
GROUP BY session_id
ORDER BY last_message DESC;
```

---

## Beta User Credentials

### Admin Accounts (Core Team)

| Email | Password |
|-------|----------|
| mustafa@osool.eg | Mustafa@Osool2025! |
| hani@osool.eg | Hani@Osool2025! |
| abady@osool.eg | Abady@Osool2025! |
| sama@osool.eg | Sama@Osool2025! |

### Tester Accounts

| Email | Password |
|-------|----------|
| tester1@osool.eg | Tester1@Beta2025 |
| tester2@osool.eg | Tester2@Beta2025 |
| tester3@osool.eg | Tester3@Beta2025 |
| tester4@osool.eg | Tester4@Beta2025 |
| tester5@osool.eg | Tester5@Beta2025 |
| tester6@osool.eg | Tester6@Beta2025 |
| tester7@osool.eg | Tester7@Beta2025 |
| tester8@osool.eg | Tester8@Beta2025 |
| tester9@osool.eg | Tester9@Beta2025 |
| tester10@osool.eg | Tester10@Beta2025 |

---

## Running the Seed Script

To create/update beta user accounts:

```bash
# Local development
cd backend
python scripts/seed_beta_users.py

# Railway production
railway run -s Osool python backend/scripts/seed_beta_users_standalone.py
```

---

## Security Notes

1. **Never share the ADMIN_API_KEY** - It provides full access to all user data
2. **Rotate the key regularly** - Update in Railway environment variables
3. **Use HTTPS only** - Never call admin endpoints over HTTP
4. **Audit access** - Consider logging admin API calls for compliance
