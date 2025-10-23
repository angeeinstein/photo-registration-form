# 🚀 Quick Start: OAuth 2.0 Setup

## Prerequisites
- Photo registration app is running
- You have admin access
- Google Cloud project with Drive API enabled

---

## 5-Minute Setup

### 1️⃣ Install Required Package (30 seconds)

```powershell
pip install requests
```

### 2️⃣ Run Database Migration (30 seconds)

```powershell
python migrate_oauth.py
```

Expected output:
```
Creating DriveOAuthToken table...
✅ Migration complete!
```

### 3️⃣ Create OAuth Credentials (2 minutes)

1. Open [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth 2.0 Client ID"**
3. Application type: **Web application**
4. Name: `Photo Registration`
5. Authorized JavaScript origins:
   - Local: `http://localhost:5000`
   - Production: `https://yourdomain.com`
6. Click **CREATE**
7. Copy **Client ID** and **Client Secret**

### 4️⃣ Update .env File (1 minute)

Add to your `.env` file:

```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-abcd1234efgh5678ijkl
GOOGLE_OAUTH_REDIRECT_URI=postmessage
```

### 5️⃣ Restart Application (30 seconds)

```powershell
# If using gunicorn with systemd:
sudo systemctl restart photo-registration

# Or if running directly:
# Stop with Ctrl+C, then:
python app.py
```

### 6️⃣ Connect Your Google Account (1 minute)

1. Login to admin dashboard
2. Click **"🔐 Drive OAuth"** in the header
3. Click **"Connect Google Drive"**
4. Sign in with YOUR Google account
5. Click **"Allow"**
6. ✅ Done!

---

## Verify It Works

1. Go to **"📸 Upload Photos"**
2. Upload a batch of photos with QR codes
3. Click **"Start Processing"**
4. Check your Google Drive - folders should appear!

---

## Troubleshooting

### "OAuth credentials not configured"
→ Check `.env` file has correct Client ID and Secret
→ Restart application

### "Failed to connect"
→ Check browser console (F12) for errors
→ Ensure JavaScript origins are correct in Google Console

### "Import requests could not be resolved"
→ Run: `pip install requests`

### Still not working?
→ Check `OAUTH_IMPLEMENTATION.md` for detailed guide
→ Review application logs

---

## Next Steps

- Review `OAUTH_IMPLEMENTATION.md` for full details
- Read code comments in `drive_uploader.py`
- Test with real photo batch

---

**That's it!** You now have OAuth 2.0 working. Photos will upload to YOUR Google Drive! 🎉
