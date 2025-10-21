# 📧 Email System - Quick Summary

## ✅ What Was Created

### 1. **Email Module** (`send_email.py`)
Generic email sending with:
- SMTP configuration support (Gmail, Outlook, Yahoo, SendGrid, custom)
- TLS/SSL support
- Template-based emails with variable replacement
- File attachments support
- Helper functions for confirmation and photos emails

### 2. **Email Templates** (`email_templates/`)
Three beautiful HTML templates:
- `confirmation_email.html` - Sent when someone registers
- `photos_email.html` - Sent with photos or photo links
- `custom_email.html` - General purpose template

### 3. **Admin Panel**
Complete admin interface with:
- **Login page** (`/admin/login`) - Secure authentication
- **Dashboard** (`/admin`) - View registrations, send emails
- **Settings** (`/admin/settings`) - Configure SMTP, templates, auto-send

### 4. **Database Updates**
New fields in Registration model:
- `confirmation_sent` - Track if confirmation email was sent
- `photos_sent` - Track if photos email was sent

New AdminSettings model:
- Store runtime configuration
- Override .env settings without restart

### 5. **Environment Configuration** (`.env.example`)
Added complete SMTP settings:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SEND_CONFIRMATION_EMAIL=true
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change-me
```

## 🎯 Key Features

### Automatic Confirmation Emails
✅ Sent immediately when someone registers
✅ Beautiful HTML template with gradient design
✅ Enable/disable via admin panel or .env

### Manual Photo Sending
✅ Send to individual registrant from dashboard
✅ Include Dropbox/Google Drive link
✅ Or attach photo files directly

### Bulk Photo Sending
✅ Send to all registrants at once
✅ Perfect for after the event
✅ Tracks who already received photos

### Admin Configuration
✅ No code editing needed
✅ Test email with one click
✅ Common SMTP providers included
✅ Template management

## 🚀 Quick Start

### 1. Configure Email (Choose one method)

**Method A: Admin Panel (Easiest)**
1. Visit `http://your-domain.com/admin/login`
2. Login with credentials from .env
3. Go to Settings
4. Fill in SMTP details
5. Click "Send Test Email"

**Method B: Edit .env file**
```bash
sudo nano /opt/photo-registration-form/.env

# Add these lines:
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password  # Gmail app password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Fair Photos
SEND_CONFIRMATION_EMAIL=true

# Restart service
sudo systemctl restart photo-registration
```

### 2. Set Admin Password

```bash
sudo nano /opt/photo-registration-form/.env

# Change these:
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourSecurePassword123!

# Restart
sudo systemctl restart photo-registration
```

### 3. Test It!

1. Register on your form
2. Check your email for confirmation
3. Login to admin panel: `/admin/login`
4. See the registration with "✓ Confirmed" badge

## 📊 Admin Panel Features

### Dashboard (`/admin`)
- View all registrations in table
- See email status (confirmed/pending, photos sent/not sent)
- Send photos to individual person
- Bulk send photos to everyone
- Statistics: total registrations, emails sent, etc.

### Settings (`/admin/settings`)
- Configure SMTP server
- Enable/disable auto-confirmation
- Customize email subjects
- Test email configuration
- View available templates
- Common SMTP providers reference

## 💡 Common Workflows

### Workflow 1: During the Event
1. Enable auto-confirmation in admin settings
2. People register → automatically get confirmation email
3. Monitor dashboard to see registrations coming in

### Workflow 2: After the Event
1. Upload photos to Dropbox/Google Drive
2. Get shareable link
3. Login to admin panel
4. Go to "Bulk Send Photos"
5. Paste link, click "Send to All"
6. Everyone gets email with link to photos

### Workflow 3: Individual Resend
1. Someone didn't get their email
2. Login to admin panel
3. Find their registration
4. Enter photos link
5. Click "Send Photos" for that row
6. Email sent immediately

## 🔧 Gmail Setup (Most Common)

### Step 1: Enable 2-Step Verification
1. Go to https://myaccount.google.com/security
2. Click "2-Step Verification"
3. Follow the setup process

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Enter "Photo Registration"
4. Click "Generate"
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Use in Configuration
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # Paste the app password
SMTP_USE_TLS=true
```

## 📝 Email Templates

### Location
```
photo-registration-form/
└── email_templates/
    ├── confirmation_email.html
    ├── photos_email.html
    └── custom_email.html
```

### Variables You Can Use
```html
{{first_name}}     - First name
{{last_name}}      - Last name
{{full_name}}      - Full name  
{{email}}          - Email address
{{photos_link}}    - Link to photos
```

### Example Template Edit
```bash
sudo nano /opt/photo-registration-form/email_templates/confirmation_email.html

# Change the text, save, and emails will use new version immediately
```

## 🐛 Troubleshooting

### Email Not Sending?
```bash
# Check logs
sudo journalctl -u photo-registration -n 50 | grep -i email

# Test from command line
cd /opt/photo-registration-form
source venv/bin/activate
python3 -c "from send_email import test_email_configuration; test_email_configuration()"
```

### Gmail "Authentication Failed"?
- Use App Password, not regular password
- Enable 2-Step Verification first
- Check username is full email address

### Emails Going to Spam?
- Check "From" name and email are correct
- Ask recipients to mark as "Not Spam"
- Consider using professional email service (SendGrid, etc.)

## 📚 Full Documentation

For complete details, see: **[EMAIL-SYSTEM.md](EMAIL-SYSTEM.md)**

Includes:
- All SMTP providers (Gmail, Outlook, Yahoo, SendGrid, custom)
- Programming API for developers
- Advanced template customization
- Security best practices
- Complete troubleshooting guide
- Email deliverability tips

## ✨ Summary

You now have a complete email system that:
- ✅ Automatically confirms registrations
- ✅ Sends photos after the event
- ✅ Has a beautiful admin panel
- ✅ Supports any SMTP provider
- ✅ Uses customizable templates
- ✅ Tracks email delivery
- ✅ Works with bulk or individual sending

**Everything is configured through the admin panel - no coding required!** 🎉
