# Quick Security Checklist (Cloudflare Tunnel Setup)

This is a simplified checklist for your specific setup using Cloudflare Tunnel.

## ✅ MUST DO Before Next Event (5 minutes)

### 1. Strong Admin Credentials
```bash
# Edit your .env file on the server:
cd /opt/photo-registration-form
nano .env

# Update these (example commands to generate strong values):
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('ADMIN_PASSWORD=' + secrets.token_urlsafe(24))"

# Also change ADMIN_USERNAME to something not obvious (not "admin")
```

**Your `.env` should look like:**
```bash
SECRET_KEY=a1b2c3d4e5f6... (64 characters)
ADMIN_USERNAME=your-custom-name  # NOT "admin"
ADMIN_PASSWORD=XyZ123abc... (20+ characters, random)
SESSION_COOKIE_SECURE=False  # ← This is CORRECT for Cloudflare Tunnel
```

### 2. Verify Cloudflare Settings
- Go to your Cloudflare Dashboard
- SSL/TLS → Overview → Set to "Flexible" or "Full"
- SSL/TLS → Edge Certificates → "Always Use HTTPS" should be ON

### 3. Restart Your Service
```bash
sudo systemctl restart photo-registration
```

## ✅ Already Protected (Nothing to Do)

These are already built-in and working:
- ✅ CSRF protection (forms protected)
- ✅ Rate limiting (10 login attempts, then blocked)
- ✅ SQL injection protection (parameterized queries)
- ✅ Path traversal protection (secure filenames)
- ✅ File upload validation (JPEG only, max 100MB)
- ✅ Admin authentication (login required)
- ✅ Session management (1 hour timeout)
- ✅ Cloudflare HTTPS (encrypts all traffic to users)

## ⚠️ Things You DON'T Need to Do

### ❌ Don't configure nginx with SSL certificates
Your setup: Cloudflare Tunnel → nginx (HTTP) → Flask (HTTP)
- nginx should stay HTTP-only
- Cloudflare handles HTTPS at the edge

### ❌ Don't set SESSION_COOKIE_SECURE=True
- This would break your app with Cloudflare Tunnel
- `False` is the correct setting for your architecture

### ❌ Don't try to force HTTPS redirect in nginx
- Cloudflare already forces HTTPS for users
- Local connection (nginx → Flask) should stay HTTP

## 🧪 Quick Security Tests (Optional)

### Test 1: Admin Login Rate Limiting
```bash
# Try logging in with wrong password 11 times
# Should get blocked after 10 attempts
for i in {1..11}; do
  curl -X POST https://your-domain.com/admin/login \
    -d "username=admin&password=wrong"
  echo " - Attempt $i"
done
# Expected: First 10 fail, 11th says "Too many requests"
```

### Test 2: CSRF Protection
```bash
# Try to register without CSRF token
curl -X POST https://your-domain.com/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","first_name":"Test"}'
# Expected: "CSRF token missing" error
```

### Test 3: Admin Panel Protected
```bash
# Try accessing admin without login
curl -I https://your-domain.com/admin
# Expected: 302 redirect to login page
```

## 📊 Risk Assessment for Your Use Case

**Your threat model (event once every few months):**
- Low risk of targeted attacks
- Main risks: Script kiddies, automated bots

**Your protections (good enough for this):**
- ✅ Strong passwords → Prevents brute force
- ✅ Rate limiting → Stops automated attacks
- ✅ CSRF protection → Prevents form hijacking
- ✅ SQL injection prevention → Database safe
- ✅ Cloudflare HTTPS → Traffic encrypted

**What you're NOT protected against (acceptable risk):**
- ❌ Advanced persistent threats (APTs)
- ❌ Zero-day exploits in Flask/dependencies
- ❌ Physical access to server
- ❌ Compromised user devices

**For your use case, this is appropriate security!**

## 🚨 What to Do If Something Goes Wrong

### If admin panel won't load:
```bash
# Check if service is running
sudo systemctl status photo-registration

# Check logs
journalctl -u photo-registration -n 50

# Restart service
sudo systemctl restart photo-registration
```

### If rate limiting blocks legitimate users:
```bash
# View current rate limits
grep -r "Limiter" /opt/photo-registration-form/app.py

# Temporary: Restart service to clear rate limit memory
sudo systemctl restart photo-registration
```

### If login fails with correct password:
```bash
# Check environment variables loaded
sudo -u www-data /opt/photo-registration-form/venv/bin/python -c \
  "from dotenv import load_dotenv; import os; load_dotenv(); \
   print('Username:', os.getenv('ADMIN_USERNAME')); \
   print('Has password:', bool(os.getenv('ADMIN_PASSWORD')))"
```

## 📝 Pre-Event Checklist

**1 day before event:**
- [ ] Changed admin password (if using same as last time)
- [ ] Tested admin login works
- [ ] Confirmed site loads over HTTPS
- [ ] Checked disk space: `df -h`
- [ ] Checked service running: `systemctl status photo-registration`

**After event:**
- [ ] Backup database: `cp registrations.db registrations_backup_$(date +%Y%m%d).db`
- [ ] Optional: Change admin password again
- [ ] Optional: Review logs for any suspicious activity: `journalctl -u photo-registration --since "1 day ago"`

## 📖 More Information

- Full security details: [SECURITY.md](SECURITY.md)
- Cloudflare Tunnel specific: [CLOUDFLARE_TUNNEL_SECURITY.md](CLOUDFLARE_TUNNEL_SECURITY.md)
- Detailed audit: [SECURITY_AUDIT.md](SECURITY_AUDIT.md)

---

**Bottom line:** Change the 3 values in `.env` (SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD) and you're good to go! 🎉
