# OAuth Troubleshooting: "Google OAuth not initialized"

## Common Causes & Solutions

### 1. ✅ Did you restart the application after updating .env?

**The most common issue!** Environment variables are only read when the app starts.

**Solution:**
```powershell
# Stop the application
# Then restart it:
python app.py

# OR if using systemd:
sudo systemctl restart photo-registration
```

After restarting, refresh the OAuth page in your browser.

---

### 2. ✅ Check your .env file format

Your `.env` file should have these EXACT lines (replace with your actual values):

```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-your-secret-here
GOOGLE_OAUTH_REDIRECT_URI=postmessage
```

**Common mistakes:**
- ❌ Extra spaces around the `=` sign
- ❌ Quotes around values (don't use quotes!)
- ❌ Wrong file (make sure it's `.env`, not `.env.example`)
- ❌ File in wrong location (should be in project root)

**Correct format:**
```bash
GOOGLE_OAUTH_CLIENT_ID=your-id-here
```

**Wrong format:**
```bash
GOOGLE_OAUTH_CLIENT_ID = "your-id-here"  ❌ No spaces, no quotes!
```

---

### 3. ✅ Verify Client ID is loaded

1. Open the OAuth page: `/admin/drive/oauth`
2. Open browser console (F12)
3. Look for the debug output:

```
=== OAuth Debug Info ===
Client ID from server: 123456789-abc...
Client ID length: 72
Is empty? false
Google script loaded? true
========================
```

**If you see:**
- `Client ID from server:` (empty) → .env not loaded, restart app
- `Is empty? true` → .env file incorrect or app not restarted
- `Google script loaded? false` → Internet connection issue or script blocked

---

### 4. ✅ Check Configuration Status on Page

The OAuth page now shows a **Configuration Status** section at the top:

- **OAuth Client ID:** Should show ✓ Configured
- **Google Script:** Should show ✓ Loaded  
- **Current Origin:** Should show your site URL

**If any show ✗:**
- Client ID not configured → Check .env and restart
- Google Script not loaded → Check internet connection
- Wrong origin → Update in Google Console

---

### 5. ✅ Verify Authorized JavaScript Origins

In [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Click on your OAuth 2.0 Client ID
2. Check **Authorized JavaScript origins**
3. Must EXACTLY match your site URL:
   - ✅ `http://localhost:5000` (for local testing)
   - ✅ `https://yourdomain.com` (for production)
   - ❌ `http://localhost:5000/` (no trailing slash!)
   - ❌ `localhost:5000` (include http://)

**Get your exact origin:**
- The OAuth page shows your current origin
- Or check browser console: `window.location.origin`

---

### 6. ✅ Browser Console Errors

Open browser console (F12) and look for errors:

**Common errors:**

```
Failed to load resource: net::ERR_BLOCKED_BY_CLIENT
```
→ Ad blocker blocking Google scripts. Disable ad blocker for your site.

```
Refused to load the script 'https://accounts.google.com/gsi/client'
```
→ Content Security Policy issue or firewall blocking Google.

```
google is not defined
```
→ Google Identity Services script didn't load. Check internet connection.

```
Invalid client_id
```
→ Client ID incorrect. Check .env file.

---

### 7. ✅ Clear Browser Cache

Sometimes old JavaScript is cached:

1. Open DevTools (F12)
2. Right-click the refresh button
3. Select **"Empty Cache and Hard Reload"**
4. Or: Ctrl+Shift+Delete → Clear cache

---

### 8. ✅ Test with Simple Check

Run this in browser console (F12):

```javascript
// Check if Client ID is loaded
console.log('Client ID:', OAUTH_CLIENT_ID);

// Check if Google script loaded
console.log('Google loaded:', typeof google !== 'undefined');

// Check if OAuth API available
console.log('OAuth API:', typeof google !== 'undefined' && google.accounts && google.accounts.oauth2);

// Try to initialize manually
if (typeof google !== 'undefined' && google.accounts) {
    console.log('Calling initGoogleOAuth()...');
    initGoogleOAuth();
    console.log('Token client:', tokenClient);
}
```

---

### 9. ✅ Check .env File Location

```powershell
# Make sure .env is in the project root
# Check if it exists:
ls .env

# View contents (PowerShell):
Get-Content .env

# View contents (Linux/Mac):
cat .env
```

The file should be in the same directory as `app.py`.

---

### 10. ✅ Restart Checklist

**After making ANY changes to .env:**

1. ✅ Stop the application
2. ✅ Verify .env file has correct format (no spaces, no quotes)
3. ✅ Start the application
4. ✅ Check application logs for startup messages
5. ✅ Refresh browser (Ctrl+F5 for hard refresh)
6. ✅ Check browser console for errors
7. ✅ Look at Configuration Status section on page

---

## Quick Diagnostic Commands

```powershell
# Check if .env file exists
Test-Path .env

# Show .env contents
Get-Content .env | Select-String OAUTH

# Check if app is reading environment variables
# (While app is running, in Python console:)
import os
print(os.environ.get('GOOGLE_OAUTH_CLIENT_ID'))
```

---

## Still Not Working?

### Enable Debug Mode:

1. Open OAuth page
2. Open browser console (F12)
3. Run these commands:

```javascript
// Show all config
console.log('=== Full Debug ===');
console.log('Client ID:', OAUTH_CLIENT_ID);
console.log('Token Client:', tokenClient);
console.log('Google Object:', google);
console.log('OAuth API:', google?.accounts?.oauth2);

// Try manual initialization
if (OAUTH_CLIENT_ID && OAUTH_CLIENT_ID !== '') {
    try {
        const client = google.accounts.oauth2.initCodeClient({
            client_id: OAUTH_CLIENT_ID,
            scope: 'openid email profile https://www.googleapis.com/auth/drive.file',
            ux_mode: 'popup',
            callback: (response) => console.log('Auth response:', response)
        });
        console.log('Manual init successful:', client);
    } catch (e) {
        console.error('Manual init failed:', e);
    }
} else {
    console.error('Client ID is empty!');
}
```

---

## Expected Behavior

When everything is working correctly:

1. ✅ Page loads with Configuration Status showing all green checkmarks
2. ✅ Console shows: `Google OAuth initialized successfully`
3. ✅ "Connect Google Drive" button is clickable
4. ✅ Clicking button opens Google popup
5. ✅ After authorization, status shows "Connected"

---

## Next Steps

1. **Restart your application** (most important!)
2. **Check Configuration Status** section on OAuth page
3. **Check browser console** for debug output
4. **Verify .env file** format is correct
5. **Check authorized origins** in Google Console match exactly

If still having issues after trying all of the above, share:
- Browser console output (F12)
- Configuration Status (from OAuth page)
- .env file contents (hide the secret!)
- Application logs
