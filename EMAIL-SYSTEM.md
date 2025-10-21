# 📧 Email System Documentation

Complete guide to the email functionality in the Photo Registration Form application.

## 🎯 Overview

The email system allows you to:
- ✅ Send **automatic confirmation emails** when someone registers
- 📷 Send **photos or photo links** to registrants after the event
- 🎨 Use **customizable HTML templates**
- ⚙️ **Configure everything** via the admin panel or `.env` file
- 📤 **Bulk send** emails to multiple registrants

## 🚀 Quick Start

### 1. Configure SMTP Settings

Edit your `.env` file:

```bash
# Gmail Example
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Photo Registration

# Enable automatic confirmation emails
SEND_CONFIRMATION_EMAIL=true
```

### 2. Set Admin Credentials

```bash
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
```

### 3. Access Admin Panel

Visit: `http://your-domain.com/admin/login`

## 📋 Features

### 1. Automatic Confirmation Emails

When someone registers, they automatically receive a confirmation email.

**Enable/Disable:**
- Admin Panel: Settings → Check "Send Automatic Confirmation Emails"
- `.env`: `SEND_CONFIRMATION_EMAIL=true`

**Template:** `email_templates/confirmation_email.html`

**Variables available:**
- `{{first_name}}` - First name
- `{{last_name}}` - Last name
- `{{full_name}}` - Full name
- `{{email}}` - Email address

### 2. Photos Emails

Send photos or links to photos after the event.

**Send to individual:**
1. Go to Admin Dashboard
2. Find the registration
3. Enter photos link (optional)
4. Click "Send Photos"

**Send to all registrants:**
1. Go to Admin Dashboard
2. Scroll to "Bulk Send Photos"
3. Enter photos link (e.g., Dropbox, Google Drive)
4. Click "Send to All"

**Template:** `email_templates/photos_email.html`

**Variables available:**
- `{{first_name}}` - First name
- `{{photos_link}}` - Link to photos
- `{{has_link}}` - true/false if link provided
- `{{has_attachments}}` - true/false if files attached

### 3. Custom Email Templates

Create your own templates in `email_templates/` directory.

**Template Syntax:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>{{subject}}</title>
</head>
<body>
    <h1>Hello {{first_name}}!</h1>
    <p>{{custom_message}}</p>
</body>
</html>
```

**Use variables:** `{{variable_name}}`

## ⚙️ SMTP Configuration

### Gmail

**Settings:**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
```

**Important:** Use an **App Password**, not your regular password!

**How to get App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to "App passwords"
4. Generate a new app password
5. Copy the 16-character password

### Outlook/Office 365

```bash
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
```

### Yahoo Mail

```bash
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

### SendGrid (Professional)

```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

### Custom SMTP Server

```bash
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true  # or false
SMTP_USE_SSL=false  # or true for port 465
```

## 🎨 Email Templates

### Available Templates

1. **confirmation_email.html** - Registration confirmation
2. **photos_email.html** - Photos delivery
3. **custom_email.html** - General purpose template

### Template Location

```
photo-registration-form/
└── email_templates/
    ├── confirmation_email.html
    ├── photos_email.html
    └── custom_email.html
```

### Creating Custom Templates

1. Create new `.html` file in `email_templates/`
2. Use `{{variable_name}}` for dynamic content
3. Style with inline CSS (most email clients don't support external CSS)

**Example:**
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
</head>
<body style="font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #667eea;">Hello {{first_name}}!</h1>
        <p>{{message}}</p>
        <a href="{{link}}" style="display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 5px;">
            Click Here
        </a>
    </div>
</body>
</html>
```

## 🔧 Admin Panel

### Accessing Admin Panel

1. Visit: `http://your-domain.com/admin/login`
2. Enter username and password from `.env`
3. Default: username=`admin`, password=`admin` (⚠️ Change this!)

### Admin Features

#### Dashboard
- View all registrations
- See email status (sent/pending)
- Send photos to individual registrants
- Bulk send photos to all

#### Settings
- Configure SMTP server
- Enable/disable auto-confirmation
- Customize email subjects
- Test email configuration
- View available templates

### Admin Routes

```
/admin/login          - Login page
/admin                - Dashboard
/admin/settings       - Email settings
/admin/test-email     - Send test email
/admin/send-photos/<id> - Send photos to one person
/admin/send-bulk-photos - Send photos to all
/admin/logout         - Logout
```

## 📊 Database Schema

### Registration Model

```python
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    registered_at = db.Column(db.DateTime, nullable=False)
    confirmation_sent = db.Column(db.Boolean, default=False)  # ← New
    photos_sent = db.Column(db.Boolean, default=False)        # ← New
```

### AdminSettings Model

Stores runtime configuration in database.

```python
class AdminSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True)
    value = db.Column(db.String(500))
```

## 💻 Programming API

### Send Confirmation Email

```python
from send_email import send_confirmation_email

success = send_confirmation_email(
    to_email="user@example.com",
    first_name="John",
    last_name="Doe"
)
```

### Send Photos Email

```python
from send_email import send_photos_email

# With link
success = send_photos_email(
    to_email="user@example.com",
    first_name="John",
    photos_link="https://photos.example.com/event123"
)

# With attachments
success = send_photos_email(
    to_email="user@example.com",
    first_name="John",
    photo_files=["photo1.jpg", "photo2.jpg"]
)
```

### Custom Email with Template

```python
from send_email import EmailSender

sender = EmailSender(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",
    use_tls=True
)

sender.send_template_email(
    to_email="user@example.com",
    template_path="email_templates/custom_email.html",
    subject="Custom Subject",
    variables={
        'first_name': 'John',
        'message': 'Your custom message',
        'link': 'https://example.com'
    }
)
```

### Test Email Configuration

```python
from send_email import test_email_configuration

if test_email_configuration():
    print("Email is configured correctly!")
else:
    print("Email configuration failed!")
```

## 🐛 Troubleshooting

### Issue: Emails Not Sending

**Solution:**
1. Check SMTP configuration in admin panel
2. Test email: Admin Panel → Settings → Send Test Email
3. Check logs: `sudo journalctl -u photo-registration -n 50`

### Issue: Gmail "Less Secure Apps" Error

**Solution:**
Use an **App Password** instead of your regular password.
- Enable 2-Step Verification
- Generate App Password
- Use the 16-character password

### Issue: Connection Timeout

**Solution:**
1. Check if port is correct (587 for TLS, 465 for SSL)
2. Check firewall: `sudo ufw allow 587/tcp`
3. Verify SMTP server address

### Issue: Authentication Failed

**Solution:**
1. Verify username and password
2. Check if 2FA is enabled (use app password)
3. For Gmail: Enable "Less secure app access" or use App Password
4. Check if account is locked or requires verification

### Issue: Template Variables Not Replaced

**Solution:**
- Ensure variables use double curly braces: `{{variable_name}}`
- Check variable spelling matches exactly
- Verify variables are passed in the `variables` dictionary

## 📚 Environment Variables Reference

```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com          # SMTP server hostname
SMTP_PORT=587                       # SMTP port (587=TLS, 465=SSL)
SMTP_USERNAME=email@example.com     # SMTP login username
SMTP_PASSWORD=your-password         # SMTP login password
SMTP_USE_TLS=true                   # Use STARTTLS (port 587)
SMTP_USE_SSL=false                  # Use SSL (port 465)
SMTP_FROM_EMAIL=email@example.com   # From email address
SMTP_FROM_NAME=Photo Registration   # From display name

# Email Features
SEND_CONFIRMATION_EMAIL=true        # Auto-send confirmation
CONFIRMATION_EMAIL_SUBJECT=...      # Confirmation subject line
PHOTOS_EMAIL_SUBJECT=...            # Photos email subject line
TEST_EMAIL=test@example.com         # Test email recipient

# Admin Panel
ADMIN_USERNAME=admin                # Admin panel username
ADMIN_PASSWORD=secure-password      # Admin panel password
ADMIN_SESSION_SECRET=secret-key     # Session encryption key
```

## 🔒 Security Best Practices

1. **Change Default Admin Password**
   ```bash
   ADMIN_PASSWORD=use-a-strong-unique-password
   ```

2. **Use App Passwords**
   - Never use your main email password
   - Generate app-specific passwords

3. **Secure .env File**
   ```bash
   chmod 600 /opt/photo-registration-form/.env
   ```

4. **Enable HTTPS**
   - Admin panel should only be accessed over HTTPS
   - Configure SSL certificate in Nginx

5. **Restrict Admin Access**
   - Use firewall to limit admin panel access
   - Consider VPN for admin access

## 📖 Examples

### Example 1: Basic Setup (Gmail)

```bash
# .env configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=myevent@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 16-char app password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=myevent@gmail.com
SMTP_FROM_NAME=Fair Photo Event
SEND_CONFIRMATION_EMAIL=true
CONFIRMATION_EMAIL_SUBJECT=Thank you for registering!
PHOTOS_EMAIL_SUBJECT=Your photos from our event
ADMIN_USERNAME=admin
ADMIN_PASSWORD=MySecurePass123!
```

### Example 2: Bulk Send After Event

1. Event is over, photos are uploaded to Dropbox
2. Get shareable link: `https://www.dropbox.com/sh/abc123/photos`
3. Login to admin panel
4. Go to "Bulk Send Photos"
5. Paste link and click "Send to All"
6. All registrants receive email with link

### Example 3: Individual Photo Send

1. Specific guest wants photos resent
2. Login to admin panel
3. Find their registration in the table
4. Enter photos link in the text field
5. Click "Send Photos" for that row
6. Email sent immediately

## 🎓 Best Practices

1. **Test Before Event**
   - Send test emails to yourself
   - Verify templates display correctly
   - Check spam folder

2. **During Event**
   - Keep auto-confirmation enabled
   - Monitor admin dashboard periodically

3. **After Event**
   - Upload photos to cloud storage
   - Get shareable link
   - Use bulk send feature
   - Check delivery statistics

4. **Template Design**
   - Keep it simple and clean
   - Use inline CSS
   - Test on multiple email clients
   - Include plain text version

5. **Email Deliverability**
   - Use proper From name and address
   - Include unsubscribe link if required
   - Don't send too many emails too quickly
   - Monitor bounce rates

## 🆘 Support

### Check Logs

```bash
# Application logs
sudo journalctl -u photo-registration -f

# Check specific errors
sudo journalctl -u photo-registration | grep -i email
```

### Test SMTP Connection

```bash
# Test from command line
python3 -c "from send_email import test_email_configuration; print(test_email_configuration())"
```

### Verify Database

```bash
# Check email status
sqlite3 /opt/photo-registration-form/registrations.db "SELECT email, confirmation_sent, photos_sent FROM registration;"
```

## 📊 Email Statistics

Track email performance in the admin dashboard:
- **Total Registrations** - How many people registered
- **Confirmations Sent** - How many confirmation emails sent
- **Photos Sent** - How many photo emails sent
- **Email Status** - Is SMTP configured correctly?
- **Auto-confirm** - Is automatic confirmation enabled?

---

**Need help?** Check the [main README](README.md) or open an issue on GitHub!
