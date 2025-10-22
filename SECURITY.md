# Security Features

This document outlines the security measures implemented in the Photo Registration Form application.

## 🔒 Security Features Implemented

### 1. CSRF Protection
- **Flask-WTF CSRF Protection**: All forms include CSRF tokens to prevent Cross-Site Request Forgery attacks
- **Token Validation**: All POST requests are validated for CSRF tokens
- **Auto-Generated Tokens**: CSRF tokens are automatically injected into all templates
- **Protected Routes**: All form submissions require valid CSRF tokens

### 2. Secure Session Cookies
- **HTTP Only**: Cookies cannot be accessed via JavaScript (`SESSION_COOKIE_HTTPONLY = True`)
- **Secure Flag**: Cookies only sent over HTTPS when enabled (`SESSION_COOKIE_SECURE`)
- **SameSite**: Protection against CSRF attacks (`SESSION_COOKIE_SAMESITE = 'Lax'`)
- **Session Timeout**: Sessions expire after 1 hour of inactivity (`PERMANENT_SESSION_LIFETIME = 3600`)

### 3. Input Validation
- **Name Validation**: Only allows letters, spaces, hyphens, apostrophes, and accented characters
- **Email Validation**: Proper email format validation using regex
- **Length Limits**: Maximum lengths enforced (100 chars for names, 120 chars for emails)
- **Sanitization**: HTML tags and dangerous characters are stripped from inputs
- **Required Fields**: All critical fields are validated before processing

### 4. Security Headers
All responses include comprehensive security headers:

- **X-Content-Type-Options**: `nosniff` - Prevents MIME type sniffing
- **X-Frame-Options**: `DENY` - Prevents clickjacking attacks
- **X-XSS-Protection**: `1; mode=block` - Enables XSS filtering
- **Strict-Transport-Security**: Forces HTTPS connections (HSTS)
- **Content-Security-Policy**: Restricts resource loading to prevent XSS
- **Referrer-Policy**: Controls referrer information leakage
- **Permissions-Policy**: Restricts access to sensitive browser features

### 5. Rate Limiting
- **Global Limits**: 200 requests per day, 50 requests per hour per IP
- **Registration Endpoint**: 10 registrations per minute per IP
- **Login Endpoint**: 5 login attempts per minute per IP
- **Memory-based Storage**: Uses in-memory storage for rate limiting
- **Automatic Blocking**: IPs exceeding limits receive 429 (Too Many Requests) responses
- **Cloudflare Compatible**: Uses `CF-Connecting-IP` header to get real client IP behind Cloudflare
- **Proxy Support**: Falls back to `X-Forwarded-For` and `X-Real-IP` for nginx/Apache reverse proxies

### 6. Error Handling
- **CSRF Error Handler**: Custom handler for CSRF validation failures
- **Rate Limit Handler**: User-friendly messages for rate limit violations
- **Generic Error Handler**: Prevents information disclosure in error messages
- **No Stack Traces**: Production errors don't expose internal details

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file for enhanced security:

```bash
# Secret key for sessions (change in production!)
SECRET_KEY=your-secure-random-secret-key-here

# Enable secure cookies over HTTPS (set to true in production)
SESSION_COOKIE_SECURE=true

# Admin credentials
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
```

### Generate a Secure Secret Key

```python
import secrets
print(secrets.token_hex(32))
```

## 🛡️ Security Best Practices

### For Production Deployment

1. **Change Default Credentials**
   - Update `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`
   - Use strong, unique passwords

2. **Enable HTTPS**
   - Configure nginx/Apache with SSL/TLS certificates
   - Set `SESSION_COOKIE_SECURE=true` in `.env`

3. **Set Secure Secret Key**
   - Generate a random secret key (see above)
   - Never commit secret keys to version control

4. **File Permissions**
   - `.env` file should be `640` (readable by owner and group only)
   - Application files should be owned by `www-data:www-data`
   - Database file should be `644` or `640`

5. **Regular Updates**
   - Keep Python packages updated: `pip install -r requirements.txt --upgrade`
   - Monitor for security advisories

6. **Database Security**
   - Consider encrypting sensitive data (email passwords)
   - Regular backups
   - Limit database access

7. **Cloudflare/Proxy Configuration**
   - Rate limiting automatically uses real client IPs from Cloudflare headers
   - Supports `CF-Connecting-IP`, `X-Forwarded-For`, and `X-Real-IP` headers
   - No additional configuration needed if using Cloudflare Tunnel or nginx proxy

## 🌐 Cloudflare & Reverse Proxy Support

The application automatically detects the real client IP when behind:
- **Cloudflare**: Uses `CF-Connecting-IP` header
- **Nginx**: Uses `X-Forwarded-For` or `X-Real-IP` headers  
- **Other Proxies**: Falls back to standard proxy headers

This ensures rate limiting works correctly even when all requests appear to come from Cloudflare's IPs.

### Nginx Configuration (Optional)
If you're using nginx without Cloudflare, ensure these headers are set:

```nginx
location / {
    proxy_pass http://localhost:8000;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $host;
}
```

## 🔍 Security Testing

### Test CSRF Protection
```bash
# Try submitting without CSRF token (should fail)
curl -X POST http://your-domain/register \
  -d "first_name=Test&last_name=User&email=test@example.com"
```

### Test Rate Limiting
```bash
# Try multiple rapid requests (should get 429 after limit)
for i in {1..20}; do
  curl -X POST http://your-domain/register \
    -d "first_name=Test&last_name=User&email=test@example.com"
done
```

### Test Security Headers
```bash
# Check security headers
curl -I http://your-domain
```

## 📋 Security Checklist

- [x] CSRF protection enabled on all forms
- [x] Secure session cookies configured
- [x] Input validation and sanitization
- [x] Security headers implemented
- [x] Rate limiting active
- [x] Error handlers implemented
- [ ] HTTPS enabled (deployment-specific)
- [ ] Secure secret key set (deployment-specific)
- [ ] Default credentials changed (deployment-specific)

## 🚨 Reporting Security Issues

If you discover a security vulnerability, please email the maintainer directly rather than using the issue tracker.

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/)
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)
