# 🎯 OAuth 2.0 Implementation Checklist

Use this checklist to verify everything is working correctly.

---

## 📦 Pre-Installation

- [ ] Python 3.8+ installed
- [ ] Flask application running
- [ ] Admin dashboard accessible
- [ ] Google Cloud project exists
- [ ] Google Drive API enabled in Cloud Console

---

## 🔧 Installation Steps

### Step 1: Install Dependencies
- [ ] Run: `pip install requests`
- [ ] Verify: `pip list | grep requests` shows version
- [ ] No import errors when restarting app

### Step 2: Database Migration
- [ ] Run: `python migrate_oauth.py`
- [ ] See: "Creating DriveOAuthToken table..."
- [ ] See: "✅ Migration complete!"
- [ ] No error messages

### Step 3: Google Cloud Console Setup
- [ ] Navigate to: https://console.cloud.google.com/apis/credentials
- [ ] Select correct project
- [ ] Click "+ CREATE CREDENTIALS"
- [ ] Select "OAuth 2.0 Client ID"
- [ ] Choose "Web application"
- [ ] Name: "Photo Registration OAuth"
- [ ] Add authorized JavaScript origins:
  - [ ] Local: `http://localhost:5000` (if testing locally)
  - [ ] Production: `https://yourdomain.com`
- [ ] Leave redirect URIs empty (for popup flow)
- [ ] Click "CREATE"
- [ ] Copy Client ID
- [ ] Copy Client Secret

### Step 4: Environment Configuration
- [ ] Open `.env` file
- [ ] Add `GOOGLE_OAUTH_CLIENT_ID=<your-client-id>`
- [ ] Add `GOOGLE_OAUTH_CLIENT_SECRET=<your-client-secret>`
- [ ] Add `GOOGLE_OAUTH_REDIRECT_URI=postmessage`
- [ ] Save file
- [ ] Verify no syntax errors (no extra spaces, quotes correct)

### Step 5: Application Restart
- [ ] Stop application (Ctrl+C or `systemctl stop`)
- [ ] Clear any cached files if needed
- [ ] Start application (`python app.py` or `systemctl start`)
- [ ] Check logs show no errors
- [ ] Verify app is accessible

---

## 🔐 OAuth Connection Test

### Step 1: Access OAuth Page
- [ ] Login to admin dashboard
- [ ] See "🔐 Drive OAuth" button in header
- [ ] Click "🔐 Drive OAuth"
- [ ] OAuth page loads without errors
- [ ] Status shows "Not Connected"

### Step 2: Connect Google Account
- [ ] Click "Connect Google Drive" button
- [ ] Google popup window opens
- [ ] Sign in with YOUR Google account
- [ ] See permission request for Drive access
- [ ] Click "Allow" to grant permissions
- [ ] Popup closes automatically
- [ ] Status updates to "Connected"
- [ ] Your email is displayed
- [ ] Token expiry time shown
- [ ] "Disconnect" button appears

### Step 3: Verify Connection
- [ ] Status badge shows green "Connected"
- [ ] Your Google email displayed
- [ ] Expiry time is ~1 hour in future
- [ ] No error messages
- [ ] Browser console (F12) shows no errors

---

## 📸 Photo Upload Test

### Step 1: Prepare Test Batch
- [ ] Have 3-5 test photos with QR codes
- [ ] QR codes contain registration data
- [ ] Photos are JPG/PNG format
- [ ] File sizes reasonable (<10MB each)

### Step 2: Upload Batch
- [ ] Click "📸 Upload Photos" in dashboard
- [ ] Create new batch
- [ ] Upload test photos
- [ ] All photos appear in list
- [ ] File sizes shown correctly
- [ ] Click "Finish Upload"

### Step 3: Process Batch
- [ ] Click "Start Processing"
- [ ] Processing starts
- [ ] See progress updates
- [ ] QR codes detected
- [ ] People identified
- [ ] Photos grouped by person

### Step 4: Verify Drive Upload
- [ ] Open YOUR Google Drive (in new tab)
- [ ] Refresh Drive page
- [ ] See new folder(s) created
- [ ] Folder names match: FirstName_LastName
- [ ] Open folder
- [ ] See photos inside
- [ ] Photos viewable and correct
- [ ] Files owned by YOU (not a service account)

---

## 🔄 Token Refresh Test

### Step 1: Wait or Fast-Forward (Optional)
- [ ] Wait 1+ hours for token to expire
- OR
- [ ] Manually update `token_expiry` in database to past time
- [ ] Reload OAuth status page

### Step 2: Verify Auto-Refresh
- [ ] Status shows "Token Expired" badge
- [ ] Click "Refresh Token" button
- [ ] Status updates to "Connected"
- [ ] New expiry time shown
- [ ] No errors

### Step 3: Test Upload with Refresh
- [ ] Upload another batch
- [ ] Start processing (with expired token)
- [ ] Token refreshes automatically
- [ ] Upload succeeds
- [ ] Photos appear in Drive

---

## 🔌 Disconnect Test

### Step 1: Disconnect
- [ ] Go to OAuth page
- [ ] Click "Disconnect" button
- [ ] Confirmation dialog appears
- [ ] Confirm disconnect
- [ ] Status changes to "Not Connected"
- [ ] Email removed from display
- [ ] "Connect" button reappears

### Step 2: Verify Revocation
- [ ] Go to: https://myaccount.google.com/permissions
- [ ] "Photo Registration" app removed from list
- OR still shows but can be manually revoked

### Step 3: Reconnect
- [ ] Click "Connect Google Drive" again
- [ ] Complete OAuth flow
- [ ] Connection restored
- [ ] Status shows "Connected"
- [ ] Upload test works again

---

## 🐛 Error Handling Tests

### Test 1: Invalid Client ID
- [ ] Change Client ID in .env to invalid value
- [ ] Restart app
- [ ] Try to connect
- [ ] See appropriate error message
- [ ] Restore correct Client ID

### Test 2: Missing Environment Variable
- [ ] Remove Client ID from .env
- [ ] Restart app
- [ ] OAuth page shows "OAuth Not Configured"
- [ ] Setup steps displayed
- [ ] Connect button disabled
- [ ] Restore Client ID

### Test 3: Network Error
- [ ] Disconnect internet (temporarily)
- [ ] Try to connect
- [ ] See network error message
- [ ] Reconnect internet
- [ ] Connection works again

### Test 4: Expired Token Upload
- [ ] Set token expiry to past
- [ ] Try to upload photos
- [ ] Token auto-refreshes
- [ ] Upload succeeds
- [ ] No user intervention needed

---

## 📊 Status Indicators

### OAuth Page Status Checks

**Connected (Green Badge):**
- [ ] Badge says "Connected"
- [ ] Background is green
- [ ] Email displayed
- [ ] Expiry time shown
- [ ] "Disconnect" button present

**Token Expired (Yellow Badge):**
- [ ] Badge says "Token Expired"
- [ ] Background is yellow
- [ ] Email still displayed
- [ ] "Refresh Token" button present
- [ ] "Disconnect" button present

**Not Connected (Red Badge):**
- [ ] Badge says "Not Connected"
- [ ] Background is red
- [ ] Message: "No Google account connected"
- [ ] "Connect Google Drive" button present

**OAuth Not Configured:**
- [ ] Badge says "Not Connected"
- [ ] Setup instructions displayed
- [ ] "Connect" button disabled
- [ ] Links to Google Console shown

---

## 🔍 Browser Console Checks (F12)

### During Connection
- [ ] No JavaScript errors
- [ ] "Google OAuth initialized" logged
- [ ] Token exchange succeeds
- [ ] "Successfully connected as <email>" shown

### During Upload
- [ ] No fetch errors
- [ ] API calls succeed (200 status)
- [ ] No CORS errors
- [ ] No authentication failures

---

## 🗄️ Database Verification

### Using SQLite Browser or Query
```sql
-- Check DriveOAuthToken table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='drive_oauth_token';

-- Check token record
SELECT user_identifier, email, token_expiry FROM drive_oauth_token;
```

- [ ] Table `drive_oauth_token` exists
- [ ] Record for 'admin' user exists when connected
- [ ] Email field populated
- [ ] Token expiry is valid datetime
- [ ] Access token and refresh token are non-null

---

## 📝 Application Logs

### Success Messages to Look For:
```
✅ "Drive service initialized successfully"
✅ "Using OAuth 2.0 credentials for Drive access"
✅ "OAuth tokens saved successfully for <email>"
✅ "OAuth token refreshed successfully"
✅ "Person folder created: <name>"
✅ "Uploaded photo: <filename>"
```

### Warning Messages (OK):
```
⚠️  "Access token expired, refreshing..."
⚠️  "Token is still valid, no refresh needed"
```

### Error Messages (Need Attention):
```
❌ "OAuth credentials not configured in environment"
❌ "Failed to exchange authorization code"
❌ "No OAuth token found"
❌ "Failed to refresh OAuth token"
❌ "Import requests could not be resolved"
```

---

## ✅ Final Verification

### System Working When:
- [ ] OAuth status shows "Connected" with your email
- [ ] Test photo batch uploads successfully
- [ ] Folders appear in YOUR Google Drive
- [ ] Photos viewable in Drive folders
- [ ] Token refreshes automatically
- [ ] No errors in application logs
- [ ] Disconnect/reconnect works
- [ ] Multiple batches can be processed

### Performance Checks:
- [ ] OAuth page loads quickly (<2 seconds)
- [ ] Connection popup appears instantly
- [ ] Token exchange completes quickly (<3 seconds)
- [ ] File uploads are reasonably fast
- [ ] No timeouts or hanging requests

### Security Checks:
- [ ] Client secret not visible in frontend
- [ ] CSRF tokens present on all POST forms
- [ ] OAuth routes require login
- [ ] Tokens stored in database (not filesystem)
- [ ] Disconnect revokes access

---

## 🎉 Success Criteria

**All checkboxes checked = OAuth 2.0 is fully working!**

You should be able to:
1. ✅ Connect your Google account with one click
2. ✅ Upload photos that appear in YOUR Drive
3. ✅ See folders created automatically
4. ✅ Have tokens refresh automatically
5. ✅ Disconnect and reconnect easily
6. ✅ Process multiple batches successfully

---

## 📞 If Checklist Fails

### First, Check:
1. Application logs for specific errors
2. Browser console (F12) for JavaScript errors
3. `.env` file for correct credentials
4. Google Cloud Console for API status
5. Database for DriveOAuthToken table

### Then, Review:
- README_OAUTH.md - Full setup guide
- OAUTH_QUICKSTART.md - Quick troubleshooting
- OAUTH_IMPLEMENTATION.md - Technical details
- Application logs - Detailed error messages

### Still Stuck?
- Verify ALL environment variables are set
- Ensure Google Drive API is enabled
- Check authorized JavaScript origins match your domain
- Try disconnect/reconnect cycle
- Review this checklist from the start

---

**Good luck! 🍀 Follow this checklist step-by-step and you'll have OAuth working perfectly!**
