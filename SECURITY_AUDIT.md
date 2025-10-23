# Security Audit Report
**Photo Registration Form Application**  
**Audit Date:** October 23, 2025  
**Scope:** Complete server-side security review  
**Risk Level:** Low (Event-based, occasional use)

---

## Executive Summary

✅ **Overall Status: SECURE with minor recommendations**

The application has **good security practices** in place for a small-scale, event-based use case. Most critical vulnerabilities are already mitigated. Below are findings categorized by severity.

---

## 🔴 CRITICAL (Must Fix Immediately)

### None Found! ✅

All critical security measures are in place.

---

## 🟡 HIGH (Recommended Fixes)

### 1. Plain-Text Password Comparison (Timing Attack Risk)
**Location:** `app.py:583`
```python
if username == admin_username and password == admin_password:
```

**Issue:** Direct string comparison is vulnerable to timing attacks, where attackers can measure response time to guess passwords character by character.

**Risk:** Low for your use case (events a few times per year), but best practice to fix.

**Fix:**
```python
from werkzeug.security import check_password_hash, generate_password_hash

# On first run or password change, hash the password:
# hashed = generate_password_hash('your-password')
# Store hashed password in environment variable

# In login function:
if username == admin_username and check_password_hash(admin_password_hash, password):
    # Login success
```

**Alternative (Simpler):** Use `secrets.compare_digest()` for constant-time comparison:
```python
import secrets

if secrets.compare_digest(username, admin_username) and \
   secrets.compare_digest(password, admin_password):
    # Login success
```

---

### 2. SMTP Password Stored in Plain Text in Database
**Location:** `app.py:269`
```python
smtp_password = db.Column(db.String(500), nullable=False)  # Should be encrypted
```

**Issue:** Email passwords stored in plain text in the database. If database is compromised, attacker gets email credentials.

**Risk:** Medium - Database compromise would expose email credentials.

**Fix:** Encrypt passwords before storing:
```python
from cryptography.fernet import Fernet

# Generate and store encryption key securely (environment variable)
ENCRYPTION_KEY = os.environ.get('DB_ENCRYPTION_KEY')
cipher = Fernet(ENCRYPTION_KEY)

# Before storing:
encrypted_password = cipher.encrypt(password.encode()).decode()

# When retrieving:
decrypted_password = cipher.decrypt(encrypted_password.encode()).decode()
```

---

### 3. Session Cookie Secure Flag Disabled by Default
**Location:** `app.py:32`
```python
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
```

**Issue:** Session cookies not marked as Secure by default. This means cookies can be sent over HTTP, risking session hijacking.

**Risk:** Medium if using HTTP, Low if using HTTPS everywhere (which you should be).

**Fix:**
```python
# Default to True for production
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
```

**AND** add to `.env.example`:
```bash
# Force secure cookies in production (requires HTTPS)
SESSION_COOKIE_SECURE=True
```

---

## 🟢 MEDIUM (Good to Fix)

### 4. Rate Limiting Uses In-Memory Storage
**Location:** `app.py:64`
```python
storage_uri="memory://",
```

**Issue:** Rate limits reset when the application restarts. Attacker could bypass limits by forcing restarts.

**Risk:** Low - Would require server access or ability to crash the app.

**Fix:** Use Redis for persistent rate limiting:
```python
# Install: pip install redis
storage_uri="redis://localhost:6379",
```

**Decision:** For your use case (events a few times per year), in-memory is probably fine. Only fix if you notice abuse.

---

### 5. No Account Lockout After Failed Login Attempts
**Location:** `app.py:572-590`

**Issue:** Rate limiting prevents brute force, but doesn't lock accounts. Persistent attacker could still try 5 passwords per minute indefinitely.

**Risk:** Low with rate limiting in place.

**Fix:** Add temporary account lockout after X failed attempts:
```python
from flask_limiter import Limiter

# In login route
failed_attempts = cache.get(f'failed_login_{username}', 0)
if failed_attempts >= 5:
    return jsonify({'error': 'Account temporarily locked. Try again in 15 minutes'}), 429

# On failed login
cache.set(f'failed_login_{username}', failed_attempts + 1, timeout=900)  # 15 min

# On successful login
cache.delete(f'failed_login_{username}')
```

**Decision:** Your current rate limiting (5/minute) is sufficient for your use case.

---

### 6. No HTTPS Redirect Enforcement
**Issue:** Application doesn't force HTTPS connections.

**Risk:** Man-in-the-middle attacks possible if accessed over HTTP.

**Current Mitigation:** HSTS header is set, but this only works after first HTTPS visit.

**Fix:** Add HTTPS redirect in nginx (recommended) or Flask:

**nginx.conf:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

**OR in app.py:**
```python
@app.before_request
def before_request():
    if not request.is_secure and not app.debug:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

---

## ✅ GOOD PRACTICES ALREADY IN PLACE

### ✓ Input Validation & Sanitization
- ✅ Email validation with regex
- ✅ Name validation (letters, spaces, hyphens, apostrophes only)
- ✅ XSS protection through sanitization
- ✅ SQL injection protection (using SQLAlchemy ORM, not raw queries)

### ✓ File Upload Security
- ✅ Magic byte validation (checks actual file content, not just extension)
- ✅ File size limits (50MB per file, 100MB total)
- ✅ `secure_filename()` used to prevent path traversal
- ✅ Files validated as JPEG before acceptance
- ✅ Admin-only upload access

### ✓ Authentication & Authorization
- ✅ Login required decorator for admin routes
- ✅ Rate limiting on login (5 attempts/minute)
- ✅ Session timeout (1 hour)
- ✅ CSRF protection enabled globally
- ✅ Admin credentials from environment variables

### ✓ Security Headers
- ✅ `X-Content-Type-Options: nosniff` (prevent MIME sniffing)
- ✅ `X-Frame-Options: DENY` (prevent clickjacking)
- ✅ `X-XSS-Protection` (browser XSS filter)
- ✅ `Strict-Transport-Security` (HSTS - force HTTPS)
- ✅ Content Security Policy (CSP)
- ✅ `Referrer-Policy`
- ✅ `Permissions-Policy`

### ✓ Session Management
- ✅ HTTPOnly cookies (prevent JavaScript access)
- ✅ SameSite=Lax (CSRF protection)
- ✅ Session timeout (1 hour)
- ✅ Secure session keys

### ✓ Error Handling
- ✅ Generic error messages (no stack traces to users)
- ✅ Proper HTTP status codes
- ✅ Logging of internal errors

### ✓ Rate Limiting
- ✅ Global limits (200/day, 50/hour)
- ✅ Login endpoint (5/minute)
- ✅ Registration endpoint (10/minute)
- ✅ Real IP detection (handles Cloudflare/proxies)

---

## 🔵 LOW (Optional Enhancements)

### 7. No Content-Length Limit on Non-Upload Routes
**Fix:** Already handled by Flask's `MAX_CONTENT_LENGTH`, no action needed.

### 8. Database Backups
**Recommendation:** Implement automated backups if using SQLite in production:
```bash
# Cron job for daily backups
0 2 * * * cp /opt/photo-registration-form/registrations.db /backups/registrations_$(date +\%Y\%m\%d).db
```

### 9. Security Monitoring
**Recommendation:** Add basic intrusion detection:
```python
# Log suspicious activities
- Multiple failed logins from same IP
- Unusual upload patterns
- Database errors (potential SQL injection attempts)
```

---

## Priority Fixes for Your Use Case

Given your context (small events, a few times per year):

### **Immediate (Before Next Event):**
1. ✅ **Fix #3:** Enable `SESSION_COOKIE_SECURE=True` (requires HTTPS)
2. ✅ **Fix #6:** Add HTTPS redirect in nginx

### **Soon (Next Few Weeks):**
3. 🟡 **Fix #1:** Use `secrets.compare_digest()` for password comparison
4. 🟡 **Fix #2:** Encrypt SMTP passwords in database

### **Eventually (Nice to Have):**
5. 🔵 **Fix #4:** Use Redis for rate limiting (only if you scale up)
6. 🔵 **Fix #5:** Add account lockout (only if you see abuse)

---

## Configuration Recommendations

### Update `.env` File
```bash
# SECURITY SETTINGS

# Generate strong secret key (run this command):
# python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<your-64-character-hex-key>

# Strong admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<long-random-password>

# Force HTTPS (requires SSL certificate)
SESSION_COOKIE_SECURE=True

# Optional: Database encryption key for SMTP passwords
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
DB_ENCRYPTION_KEY=<your-encryption-key>
```

### Nginx Configuration
```nginx
# Force HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    
    # Your existing proxy settings...
}
```

---

## Compliance & Best Practices

### GDPR/Privacy Considerations
- ✅ Collect minimal data (name, email only)
- ✅ No tracking cookies
- ⚠️ Consider adding privacy policy page
- ⚠️ Consider adding data deletion functionality

### Recommendations:
1. Add `/privacy` route with privacy policy
2. Add admin function to delete user data (right to be forgotten)
3. Add email unsubscribe functionality

---

## Testing Recommendations

### Before Next Event:
1. **Test login rate limiting:**
   ```bash
   # Try 10 failed logins quickly
   for i in {1..10}; do curl -X POST https://your-domain/admin/login -d "username=admin&password=wrong"; done
   ```

2. **Test HTTPS redirect:**
   ```bash
   curl -I http://your-domain.com
   # Should see: 301 Moved Permanently, Location: https://...
   ```

3. **Test file upload limits:**
   - Upload a 51MB file (should fail)
   - Upload a non-JPEG file (should fail)
   - Upload a valid JPEG (should succeed)

4. **Test CSRF protection:**
   - Try submitting a form without CSRF token (should fail)

---

## Summary Score

**Security Rating: 8/10** ✅

### Strengths:
- Strong input validation
- Comprehensive security headers
- Good authentication practices
- Rate limiting in place
- CSRF protection enabled
- No SQL injection vulnerabilities
- Secure file upload handling

### Areas for Improvement:
- Password hashing/comparison
- SMTP password encryption
- Force HTTPS by default
- Consider Redis for rate limiting (if scaling)

### Bottom Line:
**Your application is secure for your use case.** The recommended fixes are best practices that would make it even more robust, but you're already protecting against the most common attacks (SQL injection, XSS, CSRF, file upload attacks, brute force).

For events running a few times per year with limited exposure, your current security is **more than adequate**. Implement the "Immediate" fixes before your next event, and you'll be in excellent shape.
