# Security Deployment Checklist

Use this checklist before your next event to ensure everything is configured securely.

## ✅ Pre-Event Security Checklist

### 1. Environment Variables (`.env` file)

```bash
# Check your .env file has these set:

□ SECRET_KEY is a 64-character random hex string (not the default)
   Generate with: python -c "import secrets; print(secrets.token_hex(32))"

□ ADMIN_USERNAME is not "admin" (use something less obvious)

□ ADMIN_PASSWORD is strong (20+ characters, random)
   Generate with: python -c "import secrets; print(secrets.token_urlsafe(24))"

□ SESSION_COOKIE_SECURE=True (requires HTTPS)
```

### 2. HTTPS Configuration

```bash
□ SSL certificate is installed and valid
   Test: curl -I https://your-domain.com

□ HTTP automatically redirects to HTTPS
   Test: curl -I http://your-domain.com
   Should see: 301 Moved Permanently

□ HSTS header is present
   Check browser dev tools → Network → Response Headers
   Should see: Strict-Transport-Security: max-age=31536000
```

### 3. Nginx Configuration

```bash
□ client_max_body_size is set (100M)
□ Timeouts are configured (300s)
□ HTTPS redirect is enabled

Test nginx config:
sudo nginx -t
```

### 4. Application Security

```bash
□ Admin login works with new credentials
□ Rate limiting is active (try 10 failed logins quickly)
□ CSRF protection is working (tokens present in forms)
□ File uploads validate JPEG magic bytes
□ All admin routes require authentication
```

### 5. Database & Backups

```bash
□ Database file has proper permissions (600)
   ls -la registrations.db

□ Backup script is set up (optional but recommended)
   
Add to crontab:
0 2 * * * cp /opt/photo-registration-form/registrations.db /backups/registrations_$(date +\%Y\%m\%d).db
```

### 6. Firewall & Network

```bash
□ Only necessary ports are open (80, 443, 22)
   Check: sudo ufw status

□ SSH key authentication is enabled (password auth disabled)
   Check: cat /etc/ssh/sshd_config | grep PasswordAuthentication

□ Fail2ban is installed (optional but recommended)
   Check: sudo systemctl status fail2ban
```

## 🔐 Quick Security Tests

### Test 1: Rate Limiting
```bash
# Try 10 failed logins quickly
for i in {1..10}; do 
  curl -X POST https://your-domain/admin/login \
    -d "username=admin&password=wrong"; 
done

# Should see "Too many requests" after 5 attempts
```

### Test 2: HTTPS Enforcement
```bash
# HTTP should redirect to HTTPS
curl -I http://your-domain.com
# Look for: 301 Moved Permanently, Location: https://...
```

### Test 3: File Upload Security
```bash
# Try uploading a non-JPEG file (should fail)
curl -X POST https://your-domain/admin/photos/upload-file \
  -F "file=@test.txt" \
  -F "batch_id=1" \
  -H "Cookie: session=..."

# Should see: "File is not a valid JPEG image"
```

### Test 4: CSRF Protection
```bash
# Try POST without CSRF token (should fail)
curl -X POST https://your-domain/register \
  -d "first_name=Test&last_name=User&email=test@example.com"

# Should see: 400 Bad Request (CSRF validation failed)
```

### Test 5: Admin Access
```bash
# Try accessing admin without login (should redirect)
curl -I https://your-domain/admin

# Should see: 302 Found, Location: /admin/login
```

## 📋 Day-of-Event Checklist

### Before Event Starts
```bash
□ Server is running and accessible
   systemctl status photo-registration

□ Admin panel is accessible
   Visit: https://your-domain/admin

□ Test registration form works
   Visit: https://your-domain/

□ Email sending works (send test email)

□ Google Drive connection works
   Check admin panel → Google Drive Settings
```

### During Event
```bash
□ Monitor logs for errors
   journalctl -u photo-registration -f

□ Check disk space periodically
   df -h

□ Verify registrations are being saved
   Check admin dashboard

□ Test photo upload with one batch
```

### After Event
```bash
□ Export CSV of registrations (backup)
   Admin Dashboard → Export CSV

□ Backup database
   cp registrations.db registrations_backup_$(date +%Y%m%d).db

□ Review logs for any security issues
   grep -i "error\|fail\|attack" /var/log/nginx/photo-registration-error.log

□ Optional: Clear old data after photos are delivered
```

## 🚨 Security Incidents

### If You Suspect a Breach:

1. **Immediately:**
   ```bash
   # Stop the service
   sudo systemctl stop photo-registration
   
   # Block suspicious IPs in firewall
   sudo ufw deny from <SUSPICIOUS_IP>
   ```

2. **Investigate:**
   ```bash
   # Check recent logins
   grep "admin_login" /var/log/photo-registration/app.log
   
   # Check nginx access logs
   tail -100 /var/log/nginx/photo-registration-access.log
   
   # Check for unusual activity
   grep -i "error\|fail\|attack" /var/log/nginx/photo-registration-error.log
   ```

3. **Recovery:**
   ```bash
   # Change admin password in .env
   # Regenerate SECRET_KEY
   # Clear all sessions
   # Restart service with new credentials
   ```

## 📚 Security Resources

### Generate Strong Passwords
```bash
# Admin password (24 characters)
python -c "import secrets; print(secrets.token_urlsafe(24))"

# Secret key (64 characters hex)
python -c "import secrets; print(secrets.token_hex(32))"
```

### Check Security Headers
```bash
# Online tool
https://securityheaders.com

# Command line
curl -I https://your-domain.com
```

### SSL Certificate Check
```bash
# Check expiry
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Test SSL configuration
https://www.ssllabs.com/ssltest/
```

## ✅ Deployment Checklist Summary

**Critical (Must Do):**
- [ ] Strong SECRET_KEY set
- [ ] Strong ADMIN_PASSWORD set
- [ ] HTTPS enabled with valid SSL certificate
- [ ] SESSION_COOKIE_SECURE=True
- [ ] HTTP redirects to HTTPS

**Recommended (Should Do):**
- [ ] Non-default ADMIN_USERNAME
- [ ] Database backups configured
- [ ] Firewall rules configured
- [ ] All security tests pass

**Optional (Nice to Have):**
- [ ] Fail2ban installed
- [ ] Monitoring/alerting set up
- [ ] Redis for rate limiting
- [ ] SMTP password encryption

---

## 🎯 Bottom Line

**Minimum for secure deployment:**
1. Change default admin credentials
2. Set strong SECRET_KEY
3. Enable HTTPS
4. Set SESSION_COOKIE_SECURE=True

Do these 4 things and you're 95% secure for your use case!
