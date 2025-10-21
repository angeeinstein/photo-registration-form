# 📧 Email Accounts Management

## Overview

The Photo Registration Form now supports **multiple email accounts** stored in the database, allowing you to:

- ✅ Add/edit/delete multiple SMTP accounts
- ✅ Set one account as default
- ✅ Switch between accounts without restarting
- ✅ Test each account individually
- ✅ Track last usage for each account
- ✅ Activate/deactivate accounts

## Quick Start

### 1. Access Email Accounts

Navigate to: **Admin Dashboard → Email Accounts** (`/admin/email-accounts`)

### 2. Add Your First Account

Click **"Add New Account"** and fill in:

**Account Information:**
- **Account Name**: Friendly name (e.g., "Gmail Account", "Office 365")
- **From Email**: The email address that appears as sender
- **From Name**: Display name in emails (optional)

**SMTP Configuration:**
- **SMTP Server**: Your mail server (e.g., `smtp.gmail.com`)
- **SMTP Port**: Usually 587 (TLS) or 465 (SSL)
- **Username**: Your email or SMTP username
- **Password**: Your password or app password

**Security Settings:**
- **Use TLS**: For port 587 (recommended)
- **Use SSL**: For port 465

### 3. Test the Connection

After adding an account, click **"Test Connection"** to verify it works.

### 4. Set as Default

The first account is automatically set as default. For additional accounts, click **"Set as Default"** to use it for automated emails.

## Common SMTP Settings

### Gmail
```
SMTP Server: smtp.gmail.com
Port: 587
Security: TLS
Note: Use App Password, not regular password
Enable: https://myaccount.google.com/apppasswords
```

### Outlook/Office 365
```
SMTP Server: smtp.office365.com
Port: 587
Security: TLS
Username: Your full email address
```

### Yahoo
```
SMTP Server: smtp.mail.yahoo.com
Port: 587
Security: TLS
Note: Enable "Allow apps that use less secure sign in"
```

### SendGrid
```
SMTP Server: smtp.sendgrid.net
Port: 587
Security: TLS
Username: apikey
Password: Your SendGrid API key
```

### Amazon SES
```
SMTP Server: email-smtp.[region].amazonaws.com
Port: 587
Security: TLS
Username: Your SMTP username
Password: Your SMTP password
```

### Custom SMTP Server
```
SMTP Server: mail.yourdomain.com
Port: 587 or 465
Security: TLS or SSL
Username: Your email address
Password: Your mailbox password
```

## Account Management

### Edit Account

Click **"Edit"** to modify:
- Account name
- SMTP settings
- From email/name
- Security settings

**Note:** Leave password blank to keep existing password.

### Activate/Deactivate

Click **"Deactivate"** to temporarily disable an account without deleting it.
Click **"Activate"** to re-enable.

**Restriction:** Cannot deactivate the default account.

### Delete Account

Click **"Delete"** to permanently remove an account.

**Restriction:** Cannot delete the default account. Set another as default first.

### Set Default

Click **"Set as Default"** to make an account the default for:
- Automatic confirmation emails on registration
- Photo emails (unless specified otherwise)

Only **one account** can be default at a time.

## Migration from .env

If you have existing email configuration in your `.env` file, it will be **automatically migrated** to the database on first run:

1. Run the application: `python app.py`
2. The system detects `.env` email settings
3. Creates account named "Migrated from .env"
4. Sets it as default and active
5. You can now manage it from the admin panel

**After Migration:**
- Email settings in `.env` become optional
- Database accounts take priority
- You can delete `.env` email settings if desired

## Features

### Per-Account Tracking

Each account tracks:
- **Created At**: When the account was added
- **Last Used**: When it was last used to send an email
- **Status**: Active or Inactive
- **Default**: Whether it's the default account

### Account Information Display

The account list shows:
- 📌 Account name with status badges
- 📧 From email and display name
- 🔧 SMTP server and port
- 👤 Username
- 🔒 Security protocol (TLS/SSL)
- 📅 Last used timestamp

### Test Function

Each account has a **"Test Connection"** button that:
- Attempts to connect to SMTP server
- Sends a test email to the account's email address
- Reports success or failure
- Helps verify configuration before use

## Using Multiple Accounts

### Use Cases

1. **Different Events**: Use different email accounts for different events
2. **Branding**: Different from-names for different purposes
3. **Failover**: If one account fails, switch to backup
4. **Rate Limits**: Distribute sending across multiple accounts
5. **Segmentation**: Use different accounts for different recipient groups

### Selecting Account

Currently, the **default account** is used for all automated emails:
- Registration confirmation emails
- Photo delivery emails (individual and bulk)

**Future Enhancement:** Allow selecting specific accounts per email action.

## Security

### Password Storage

- Passwords are stored in the database
- **Recommendation**: Use app-specific passwords when available
- **Future Enhancement**: Consider encrypting passwords at rest

### App Passwords (Gmail)

For Gmail accounts, use **App Passwords**:

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Generate password
4. Use generated password in SMTP settings

### Best Practices

- ✅ Use TLS/SSL when available
- ✅ Use app-specific passwords
- ✅ Don't share SMTP credentials
- ✅ Test new accounts before using in production
- ✅ Deactivate unused accounts
- ✅ Review "Last Used" to identify inactive accounts
- ✅ Keep backup account configured

## Troubleshooting

### Test Email Fails

1. **Check SMTP settings**: Server, port, username, password
2. **Verify security protocol**: TLS vs SSL
3. **Check firewall**: Ensure outbound SMTP is allowed
4. **Test credentials**: Try logging into webmail
5. **Check provider requirements**: Some require app passwords
6. **Review server logs**: Look for specific error messages

### Emails Not Sending

1. **Check default account**: Ensure an account is set as default
2. **Verify account is active**: Deactivated accounts won't send
3. **Test connection**: Use "Test Connection" button
4. **Check email settings**: In Admin → Settings
5. **Review application logs**: Look for error messages

### Cannot Delete Account

- **Default accounts** cannot be deleted
- **Solution**: Set another account as default first

### Cannot Deactivate Account

- **Default accounts** cannot be deactivated
- **Solution**: Set another account as default first

## API Reference

### EmailAccount Model

```python
EmailAccount(
    name='Account Name',
    smtp_server='smtp.example.com',
    smtp_port=587,
    smtp_username='username',
    smtp_password='password',
    use_tls=True,
    use_ssl=False,
    from_email='noreply@example.com',
    from_name='Event Registration',
    is_active=True,
    is_default=False
)
```

### Getting Default Account

```python
from app import EmailAccount

default_account = EmailAccount.get_default()
```

### Setting Default Account

```python
EmailAccount.set_default(account_id)
```

### Sending with Specific Account

```python
from send_email import send_confirmation_email
from app import EmailAccount

account = EmailAccount.query.get(account_id)
send_confirmation_email(
    to_email='user@example.com',
    first_name='John',
    last_name='Doe',
    account=account  # Optional, uses default if not provided
)
```

## Admin Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/admin/email-accounts` | GET | List all accounts |
| `/admin/email-accounts/add` | GET, POST | Add new account |
| `/admin/email-accounts/edit/<id>` | GET, POST | Edit existing account |
| `/admin/email-accounts/delete/<id>` | POST | Delete account |
| `/admin/email-accounts/set-default/<id>` | POST | Set as default |
| `/admin/email-accounts/toggle/<id>` | POST | Activate/deactivate |
| `/admin/email-accounts/test/<id>` | POST | Test connection |

## Future Enhancements

Planned features:

- 🔐 Password encryption at rest
- 📊 Usage statistics per account
- 🔄 Automatic failover to backup account
- 📧 Account selection in email sending forms
- 📈 Send rate tracking and limits
- 🎯 Account assignment per template
- 📝 Account usage audit log
- ⚡ Bulk account import from CSV
- 🔔 Email quota notifications

## Support

For issues or questions:
- Check application logs
- Review EMAIL-SYSTEM.md for general email setup
- Test SMTP settings with external tools
- Verify provider requirements and limits
