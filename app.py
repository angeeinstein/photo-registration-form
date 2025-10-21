from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import wraps
from send_email import send_confirmation_email, send_photos_email, create_email_sender_from_env, test_email_configuration

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
database_uri = os.environ.get('DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'registrations.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)

# Database Model
class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    registered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    confirmation_sent = db.Column(db.Boolean, default=False)
    photos_sent = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Registration {self.first_name} {self.last_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'registered_at': self.registered_at.isoformat(),
            'confirmation_sent': self.confirmation_sent,
            'photos_sent': self.photos_sent
        }

# Admin settings model (stored in database)
class AdminSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    
    @staticmethod
    def get_setting(key, default=None):
        setting = AdminSettings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value):
        setting = AdminSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = AdminSettings(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

# Email accounts model (multiple SMTP accounts)
class EmailAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Friendly name (e.g., "Main Gmail", "Support Email")
    smtp_server = db.Column(db.String(200), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False, default=587)
    smtp_username = db.Column(db.String(200), nullable=False)
    smtp_password = db.Column(db.String(500), nullable=False)  # Should be encrypted in production
    use_tls = db.Column(db.Boolean, default=True)
    use_ssl = db.Column(db.Boolean, default=False)
    from_email = db.Column(db.String(200), nullable=False)
    from_name = db.Column(db.String(100), nullable=False, default='Photo Registration')
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EmailAccount {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'smtp_username': self.smtp_username,
            'from_email': self.from_email,
            'from_name': self.from_name,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }
    
    @staticmethod
    def get_default():
        """Get the default email account"""
        account = EmailAccount.query.filter_by(is_default=True, is_active=True).first()
        if not account:
            # If no default, get the first active account
            account = EmailAccount.query.filter_by(is_active=True).first()
        return account
    
    @staticmethod
    def set_default(account_id):
        """Set an account as default"""
        # Remove default from all accounts
        EmailAccount.query.update({EmailAccount.is_default: False})
        # Set new default
        account = EmailAccount.query.get(account_id)
        if account:
            account.is_default = True
            db.session.commit()
            return True
        return False

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Disable caching for all HTML responses to ensure fresh CSS/JS
@app.after_request
def add_header(response):
    """Add headers to prevent caching of HTML pages"""
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# Routes
@app.route('/')
def index():
    """Display the registration form"""
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Handle registration form submission"""
    try:
        data = request.form
        
        # Validate required fields
        if not data.get('first_name') or not data.get('last_name') or not data.get('email'):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Create new registration
        registration = Registration(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            email=data['email'].strip().lower()
        )
        
        db.session.add(registration)
        db.session.commit()
        
        # Send confirmation email if enabled
        send_confirmation = os.getenv('SEND_CONFIRMATION_EMAIL', 'true').lower() == 'true'
        email_sent = False
        
        if send_confirmation:
            try:
                # Use default email account from database
                default_account = EmailAccount.get_default()
                email_sent = send_confirmation_email(
                    registration.email,
                    registration.first_name,
                    registration.last_name,
                    account=default_account
                )
                if email_sent:
                    registration.confirmation_sent = True
                    db.session.commit()
            except Exception as e:
                app.logger.error(f'Failed to send confirmation email: {str(e)}')
        
        response_message = 'Registration successful!'
        if email_sent:
            response_message += ' A confirmation email has been sent to your address.'
        else:
            response_message += ' You will receive your photos via email.'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'data': registration.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Registration error: {str(e)}')
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@app.route('/registrations', methods=['GET'])
def list_registrations():
    """List all registrations (admin view)"""
    try:
        registrations = Registration.query.order_by(Registration.registered_at.desc()).all()
        return jsonify({
            'success': True,
            'count': len(registrations),
            'registrations': [reg.to_dict() for reg in registrations]
        })
    except Exception as e:
        app.logger.error(f'Error fetching registrations: {str(e)}')
        return jsonify({'error': 'Failed to fetch registrations'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/registrations/updates', methods=['GET'])
@login_required
def get_registration_updates():
    """API endpoint for live dashboard updates"""
    try:
        registrations = Registration.query.order_by(Registration.registered_at.desc()).all()
        
        stats = {
            'total_registrations': len(registrations),
            'confirmation_sent': sum(1 for r in registrations if r.confirmation_sent),
            'photos_sent': sum(1 for r in registrations if r.photos_sent),
        }
        
        return jsonify({
            'success': True,
            'stats': stats,
            'registrations': [reg.to_dict() for reg in registrations]
        })
    except Exception as e:
        app.logger.error(f'Error fetching updates: {str(e)}')
        return jsonify({'error': 'Failed to fetch updates'}), 500

# Admin Routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
        
        if username == admin_username and password == admin_password:
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Successfully logged out', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    registrations = Registration.query.order_by(Registration.registered_at.desc()).all()
    
    # Get email accounts
    email_accounts = EmailAccount.query.filter_by(is_active=True).all()
    default_account = EmailAccount.get_default()
    email_configured = default_account is not None
    
    send_confirmation = os.getenv('SEND_CONFIRMATION_EMAIL', 'true').lower() == 'true'
    
    stats = {
        'total_registrations': len(registrations),
        'confirmation_sent': sum(1 for r in registrations if r.confirmation_sent),
        'photos_sent': sum(1 for r in registrations if r.photos_sent),
        'email_configured': email_configured,
        'auto_confirmation': send_confirmation
    }
    
    return render_template('admin_dashboard.html', 
                         registrations=registrations, 
                         stats=stats,
                         email_accounts=email_accounts,
                         default_account=default_account)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Admin settings configuration"""
    if request.method == 'POST':
        # Only update confirmation email setting
        send_confirmation = request.form.get('send_confirmation', 'false')
        AdminSettings.set_setting('SEND_CONFIRMATION_EMAIL', send_confirmation)
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    # Load current confirmation setting
    send_confirmation = AdminSettings.get_setting('SEND_CONFIRMATION_EMAIL', os.getenv('SEND_CONFIRMATION_EMAIL', 'true'))
    
    return render_template('admin_settings.html', send_confirmation=send_confirmation)

@app.route('/admin/send-photos/<int:registration_id>', methods=['POST'])
@login_required
def admin_send_photos(registration_id):
    """Send photos email to a specific registration"""
    try:
        registration = Registration.query.get_or_404(registration_id)
        photos_link = request.form.get('photos_link', '')
        account_id = request.form.get('account_id')
        
        # Get selected account or use default
        if account_id:
            account = EmailAccount.query.get(int(account_id))
        else:
            account = EmailAccount.get_default()
        
        if not account:
            flash('No email account configured', 'error')
            return redirect(url_for('admin_dashboard'))
        
        success = send_photos_email(
            registration.email,
            registration.first_name,
            photos_link=photos_link if photos_link else None,
            account=account
        )
        
        if success:
            registration.photos_sent = True
            db.session.commit()
            flash(f'Photos email sent to {registration.email} from "{account.name}"', 'success')
        else:
            flash(f'Failed to send email to {registration.email}', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-bulk-photos', methods=['POST'])
@login_required
def admin_send_bulk_photos():
    """Send photos email to all registrations"""
    photos_link = request.form.get('photos_link', '')
    account_id = request.form.get('account_id')
    sent_count = 0
    failed_count = 0
    
    # Get selected account or use default
    if account_id:
        account = EmailAccount.query.get(int(account_id))
    else:
        account = EmailAccount.get_default()
    
    if not account:
        flash('No email account configured', 'error')
        return redirect(url_for('admin_dashboard'))
    
    registrations = Registration.query.filter_by(photos_sent=False).all()
    
    for registration in registrations:
        try:
            success = send_photos_email(
                registration.email,
                registration.first_name,
                photos_link=photos_link if photos_link else None,
                account=account
            )
            
            if success:
                registration.photos_sent = True
                sent_count += 1
            else:
                failed_count += 1
        except Exception as e:
            app.logger.error(f'Failed to send to {registration.email}: {str(e)}')
            failed_count += 1
    
    db.session.commit()
    
    flash(f'Bulk send complete using "{account.name}": {sent_count} sent, {failed_count} failed', 'success')
    return redirect(url_for('admin_dashboard'))

# Email Account Management Routes
@app.route('/admin/email-accounts')
@login_required
def admin_email_accounts():
    """List all email accounts"""
    accounts = EmailAccount.query.all()
    return render_template('email_accounts.html', accounts=accounts)

@app.route('/admin/email-accounts/add', methods=['GET', 'POST'])
@login_required
def admin_add_email_account():
    """Add new email account"""
    if request.method == 'POST':
        try:
            # If this is the first account, make it default
            is_first_account = EmailAccount.query.count() == 0
            
            account = EmailAccount(
                name=request.form['name'],
                smtp_server=request.form['smtp_server'],
                smtp_port=int(request.form['smtp_port']),
                smtp_username=request.form['smtp_username'],
                smtp_password=request.form['smtp_password'],
                use_tls=request.form.get('use_tls') == 'on',
                use_ssl=request.form.get('use_ssl') == 'on',
                from_email=request.form['from_email'],
                from_name=request.form.get('from_name', ''),
                is_active=True,
                is_default=is_first_account
            )
            
            db.session.add(account)
            db.session.commit()
            
            flash(f'Email account "{account.name}" added successfully!', 'success')
            return redirect(url_for('admin_email_accounts'))
        except Exception as e:
            flash(f'Error adding account: {str(e)}', 'error')
    
    return render_template('email_account_form.html', account=None, action='Add')

@app.route('/admin/email-accounts/edit/<int:account_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_email_account(account_id):
    """Edit existing email account"""
    account = EmailAccount.query.get_or_404(account_id)
    
    if request.method == 'POST':
        try:
            account.name = request.form['name']
            account.smtp_server = request.form['smtp_server']
            account.smtp_port = int(request.form['smtp_port'])
            account.smtp_username = request.form['smtp_username']
            
            # Only update password if provided
            if request.form.get('smtp_password'):
                account.smtp_password = request.form['smtp_password']
            
            account.use_tls = request.form.get('use_tls') == 'on'
            account.use_ssl = request.form.get('use_ssl') == 'on'
            account.from_email = request.form['from_email']
            account.from_name = request.form.get('from_name', '')
            
            db.session.commit()
            
            flash(f'Email account "{account.name}" updated successfully!', 'success')
            return redirect(url_for('admin_email_accounts'))
        except Exception as e:
            flash(f'Error updating account: {str(e)}', 'error')
    
    return render_template('email_account_form.html', account=account, action='Edit')

@app.route('/admin/email-accounts/delete/<int:account_id>', methods=['POST'])
@login_required
def admin_delete_email_account(account_id):
    """Delete email account"""
    account = EmailAccount.query.get_or_404(account_id)
    
    if account.is_default:
        flash('Cannot delete the default email account. Set another account as default first.', 'error')
        return redirect(url_for('admin_email_accounts'))
    
    try:
        db.session.delete(account)
        db.session.commit()
        flash(f'Email account "{account.name}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting account: {str(e)}', 'error')
    
    return redirect(url_for('admin_email_accounts'))

@app.route('/admin/email-accounts/set-default/<int:account_id>', methods=['POST'])
@login_required
def admin_set_default_account(account_id):
    """Set an account as default"""
    try:
        EmailAccount.set_default(account_id)
        flash('Default email account updated!', 'success')
    except Exception as e:
        flash(f'Error setting default: {str(e)}', 'error')
    
    return redirect(url_for('admin_email_accounts'))

@app.route('/admin/email-accounts/toggle/<int:account_id>', methods=['POST'])
@login_required
def admin_toggle_account(account_id):
    """Toggle account active status"""
    account = EmailAccount.query.get_or_404(account_id)
    
    if account.is_default and account.is_active:
        flash('Cannot deactivate the default account. Set another account as default first.', 'error')
        return redirect(url_for('admin_email_accounts'))
    
    try:
        account.is_active = not account.is_active
        db.session.commit()
        
        status = 'activated' if account.is_active else 'deactivated'
        flash(f'Email account "{account.name}" {status}!', 'success')
    except Exception as e:
        flash(f'Error toggling account: {str(e)}', 'error')
    
    return redirect(url_for('admin_email_accounts'))

@app.route('/admin/email-accounts/test/<int:account_id>', methods=['POST'])
@login_required
def admin_test_account(account_id):
    """Test email account configuration"""
    account = EmailAccount.query.get_or_404(account_id)
    
    # Get custom test email from form, or use account's from_email as default
    test_email = request.form.get('test_email', '').strip()
    if not test_email:
        test_email = account.from_email
    
    try:
        success = test_email_configuration(account, test_email)
        
        if success:
            flash(f'Test email sent successfully from "{account.name}" to {test_email}!', 'success')
        else:
            flash(f'Failed to send test email from "{account.name}". Check configuration.', 'error')
    except Exception as e:
        flash(f'Error testing account: {str(e)}', 'error')
    
    return redirect(url_for('admin_email_accounts'))

# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")
        
        # Migrate email configuration from .env if no accounts exist
        migrate_email_config_from_env()

def migrate_email_config_from_env():
    """Migrate email configuration from .env to database (one-time migration)"""
    # Check if any email accounts already exist
    if EmailAccount.query.count() > 0:
        print("Email accounts already exist in database, skipping migration.")
        return
    
    # Check if .env has email configuration
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_username = os.getenv('SMTP_USERNAME')
    
    if not smtp_server or not smtp_username:
        print("No email configuration found in .env file.")
        return
    
    try:
        # Create email account from .env settings
        account = EmailAccount(
            name='Migrated from .env',
            smtp_server=smtp_server,
            smtp_port=int(os.getenv('SMTP_PORT', 587)),
            smtp_username=smtp_username,
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            use_ssl=os.getenv('SMTP_USE_SSL', 'false').lower() == 'true',
            from_email=os.getenv('SMTP_FROM_EMAIL', smtp_username),
            from_name=os.getenv('SMTP_FROM_NAME', ''),
            is_active=True,
            is_default=True
        )
        
        db.session.add(account)
        db.session.commit()
        
        print(f"✅ Migrated email configuration from .env to database!")
        print(f"   Account: {account.name}")
        print(f"   SMTP: {account.smtp_server}:{account.smtp_port}")
        print(f"   From: {account.from_email}")
        print()
        print("💡 You can now manage email accounts from the admin panel.")
        print("   Navigate to: Admin Dashboard → Email Accounts")
    except Exception as e:
        print(f"❌ Error migrating email config: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
