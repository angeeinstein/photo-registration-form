# OAuth 2.0 Architecture Diagram

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         PHOTO REGISTRATION APP                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐         ┌──────────────┐      ┌─────────────┐│
│  │   Frontend   │         │   Backend    │      │  Database   ││
│  │              │         │              │      │             ││
│  │ - admin_drive│◄───────►│ - OAuth      │◄────►│ DriveOAuth  ││
│  │   _oauth.html│         │   endpoints  │      │   Token     ││
│  │              │         │              │      │             ││
│  │ - Google     │         │ - Token      │      │             ││
│  │   Identity   │         │   exchange   │      │             ││
│  │   Services   │         │              │      │             ││
│  └──────────────┘         └──────────────┘      └─────────────┘│
│         │                        │                               │
│         │                        │                               │
└─────────┼────────────────────────┼───────────────────────────────┘
          │                        │
          │                        │
          ▼                        ▼
┌─────────────────────┐  ┌──────────────────────┐
│   Google OAuth 2.0  │  │  Google Drive API    │
│                     │  │                      │
│ - Authorization     │  │ - Folder creation    │
│ - Token exchange    │  │ - File uploads       │
│ - Token refresh     │  │ - Share links        │
└─────────────────────┘  └──────────────────────┘
```

---

## OAuth Connection Flow

```
ADMIN USER                FRONTEND                BACKEND              GOOGLE
    │                        │                       │                   │
    │  1. Click "Connect"    │                       │                   │
    ├───────────────────────►│                       │                   │
    │                        │                       │                   │
    │                        │  2. Initialize GSI    │                   │
    │                        │       popup           │                   │
    │                        ├──────────────────────────────────────────►│
    │                        │                       │                   │
    │  3. Sign in & Grant    │                       │   4. Auth code    │
    │        permissions     │◄──────────────────────────────────────────┤
    │◄───────────────────────┤                       │                   │
    │                        │                       │                   │
    │                        │  5. POST code to      │                   │
    │                        │     /oauth/exchange   │                   │
    │                        ├──────────────────────►│                   │
    │                        │                       │                   │
    │                        │                       │  6. Exchange code │
    │                        │                       │     for tokens    │
    │                        │                       ├──────────────────►│
    │                        │                       │                   │
    │                        │                       │ 7. Access token + │
    │                        │                       │    Refresh token  │
    │                        │                       │◄──────────────────┤
    │                        │                       │                   │
    │                        │                       │  8. Save to DB    │
    │                        │                       ├────────┐          │
    │                        │                       │        │          │
    │                        │                       │◄───────┘          │
    │                        │                       │                   │
    │                        │   9. Success response │                   │
    │  10. "Connected!"      │◄──────────────────────┤                   │
    │◄───────────────────────┤                       │                   │
    │                        │                       │                   │
```

---

## Photo Upload Flow (with OAuth)

```
PHOTO PROCESSOR          DRIVE UPLOADER           DATABASE            GOOGLE DRIVE
      │                        │                       │                    │
      │  1. Initialize with    │                       │                    │
      │     use_oauth=True     │                       │                    │
      ├───────────────────────►│                       │                    │
      │                        │                       │                    │
      │                        │  2. Get OAuth tokens  │                    │
      │                        ├──────────────────────►│                    │
      │                        │                       │                    │
      │                        │  3. Access token +    │                    │
      │                        │     Refresh token     │                    │
      │                        │◄──────────────────────┤                    │
      │                        │                       │                    │
      │                        │  4. Check if expired  │                    │
      │                        ├────────┐              │                    │
      │                        │        │              │                    │
      │                        │◄───────┘              │                    │
      │                        │                       │                    │
      │                        │ IF EXPIRED:           │                    │
      │                        │  5a. Refresh token    │                    │
      │                        ├───────────────────────────────────────────►│
      │                        │                       │                    │
      │                        │  5b. New access token │                    │
      │                        │◄───────────────────────────────────────────┤
      │                        │                       │                    │
      │                        │  5c. Update DB        │                    │
      │                        ├──────────────────────►│                    │
      │                        │                       │                    │
      │                        │  6. Build Drive       │                    │
      │                        │     service           │                    │
      │                        ├────────┐              │                    │
      │                        │        │              │                    │
      │                        │◄───────┘              │                    │
      │                        │                       │                    │
      │  7. Create folder      │                       │                    │
      ├───────────────────────►│  8. API call          │                    │
      │                        ├───────────────────────────────────────────►│
      │                        │                       │                    │
      │                        │  9. Folder ID         │                    │
      │  10. Folder ID         │◄───────────────────────────────────────────┤
      │◄───────────────────────┤                       │                    │
      │                        │                       │                    │
      │  11. Upload photos     │                       │                    │
      ├───────────────────────►│  12. Upload files     │                    │
      │                        ├───────────────────────────────────────────►│
      │                        │                       │                    │
      │                        │  13. Success          │                    │
      │  14. Success           │◄───────────────────────────────────────────┤
      │◄───────────────────────┤                       │                    │
      │                        │                       │                    │
```

---

## Token Lifecycle

```
┌──────────────┐
│              │
│ User Clicks  │
│  "Connect"   │
│              │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│              │
│   Google     │
│    OAuth     │
│   Popup      │
│              │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│                          │
│  Authorization Code      │
│  (one-time use, 10min)   │
│                          │
└────────┬─────────────────┘
         │
         ▼ Exchange
┌────────────────────────────────┐
│                                │
│  Access Token (1 hour)         │
│  + Refresh Token (no expiry)   │
│                                │
└────────┬───────────────────────┘
         │
         ▼ Store in DB
┌────────────────────────────────┐
│                                │
│  DriveOAuthToken Table         │
│  - access_token                │
│  - refresh_token               │
│  - token_expiry                │
│  - email                       │
│  - scope                       │
│                                │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│                                │
│  Upload Photos to Drive        │
│  (using access_token)          │
│                                │
└────────┬───────────────────────┘
         │
         │ After 1 hour...
         ▼
┌────────────────────────────────┐
│                                │
│  Access Token Expired          │
│  → Auto-refresh with           │
│     refresh_token              │
│  → Get new access_token        │
│  → Update database             │
│  → Continue uploading          │
│                                │
└────────────────────────────────┘
```

---

## Database Schema

```sql
CREATE TABLE drive_oauth_token (
    id INTEGER PRIMARY KEY,
    user_identifier VARCHAR(100) UNIQUE NOT NULL,  -- 'admin'
    access_token TEXT NOT NULL,                     -- Current access token
    refresh_token TEXT NOT NULL,                    -- Never expires
    token_expiry DATETIME NOT NULL,                 -- When access_token expires
    scope TEXT,                                     -- Granted scopes
    email VARCHAR(200),                             -- Google account email
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## File Structure

```
photo-registration-form/
│
├── app.py                          # Main Flask app
│   ├── DriveOAuthToken model       # Database model
│   ├── /admin/drive/oauth          # OAuth connection page
│   ├── /admin/drive/oauth/status   # Check connection
│   ├── /admin/drive/oauth/exchange # Token exchange
│   ├── /admin/drive/oauth/disconnect
│   └── /admin/drive/oauth/refresh
│
├── drive_uploader.py               # Drive operations
│   └── DriveUploader class
│       ├── __init__(use_oauth=True)
│       ├── OAuth credential loading
│       ├── Auto token refresh
│       └── Drive API operations
│
├── drive_credentials_manager.py    # Credential management
│   ├── get_oauth_credentials()
│   ├── refresh_oauth_token()
│   └── is_oauth_configured()
│
├── templates/
│   ├── admin_drive_oauth.html      # OAuth UI
│   │   ├── Google Identity Services
│   │   ├── Connection status
│   │   └── Connect/Disconnect buttons
│   │
│   └── admin_dashboard.html        # Dashboard
│       └── "🔐 Drive OAuth" link
│
├── .env                            # Environment variables
│   ├── GOOGLE_OAUTH_CLIENT_ID
│   ├── GOOGLE_OAUTH_CLIENT_SECRET
│   └── GOOGLE_OAUTH_REDIRECT_URI
│
├── requirements.txt                # Dependencies
│   └── requests>=2.31.0
│
├── migrate_oauth.py                # Database migration
│
└── Documentation/
    ├── OAUTH_QUICKSTART.md         # 5-minute setup
    ├── OAUTH_IMPLEMENTATION.md     # Full docs
    ├── OAUTH_SUMMARY.md            # Summary
    └── OAUTH_ARCHITECTURE.md       # This file
```

---

## Security Layers

```
┌─────────────────────────────────────────┐
│     ENVIRONMENT VARIABLES (.env)        │
│  - OAuth Client ID (public)             │
│  - OAuth Client Secret (secret)         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         APPLICATION LAYER               │
│  - CSRF Protection on all POST routes   │
│  - Login required for OAuth routes      │
│  - Server-side token validation         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         DATABASE LAYER                  │
│  - Encrypted at rest (filesystem)       │
│  - Access tokens expire (1 hour)        │
│  - Refresh tokens stored securely       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         GOOGLE LAYER                    │
│  - OAuth 2.0 standard protocol          │
│  - Token revocation support             │
│  - Scope-limited permissions            │
└─────────────────────────────────────────┘
```

---

## Comparison: Service Account vs OAuth

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE ACCOUNT (Old)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐  │
│  │   App    │──JSON───►│ Service  │──API────►│  Google  │  │
│  │          │   Key    │ Account  │   Call   │  Drive   │  │
│  └──────────┘          └──────────┘          └──────────┘  │
│                                                              │
│  ❌ No storage quota (fails immediately)                     │
│  ❌ Complex file sharing required                            │
│  ❌ Service account owns files                               │
│  ❌ Manual JSON key management                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                      OAUTH 2.0 (New)                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐          ┌──────────┐          ┌──────────┐  │
│  │   App    │──OAuth──►│   Your   │──API────►│  Google  │  │
│  │          │  Token   │ Account  │   Call   │  Drive   │  │
│  └──────────┘          └──────────┘          └──────────┘  │
│                                                              │
│  ✅ Uses your Drive quota                                    │
│  ✅ Direct upload to your Drive                              │
│  ✅ You own all files                                        │
│  ✅ One-click connect/disconnect                             │
│  ✅ Automatic token refresh                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### GET /admin/drive/oauth
Returns the OAuth connection page with status display

### GET /admin/drive/oauth/status
```json
Response (connected):
{
    "connected": true,
    "email": "user@gmail.com",
    "expires_at": "2025-10-22T14:30:00",
    "is_expired": false
}

Response (not connected):
{
    "connected": false
}
```

### POST /admin/drive/oauth/exchange
```json
Request:
{
    "code": "4/0AY0e-g7X..."
}

Response:
{
    "success": true,
    "email": "user@gmail.com",
    "expires_at": "2025-10-22T14:30:00"
}
```

### POST /admin/drive/oauth/disconnect
```json
Response:
{
    "success": true,
    "message": "Disconnected successfully"
}
```

### POST /admin/drive/oauth/refresh
```json
Response:
{
    "success": true,
    "expires_at": "2025-10-22T15:30:00"
}
```

---

## Dependencies

```
google-api-python-client    # Drive API client
google-auth                # OAuth credential handling
requests                   # HTTP requests for token exchange
Flask                      # Web framework
Flask-SQLAlchemy          # Database ORM
Flask-WTF                 # CSRF protection
```

---

This architecture provides a secure, user-friendly OAuth 2.0 implementation that allows direct uploads to personal Google Drive accounts with automatic token management and refresh.
