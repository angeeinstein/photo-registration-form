from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from dotenv import load_dotenv
from functools import wraps
from send_email import send_confirmation_email, send_photos_email, create_email_sender_from_env, test_email_configuration
import re
import uuid

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
database_uri = os.environ.get('DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'registrations.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Security configurations
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Custom function to get real IP behind Cloudflare/proxy
def get_real_ip():
    """Get the real client IP, considering Cloudflare and reverse proxies"""
    # Cloudflare passes the real IP in CF-Connecting-IP header
    if 'CF-Connecting-IP' in request.headers:
        return request.headers['CF-Connecting-IP']
    # Standard proxy headers (nginx, etc.)
    if 'X-Forwarded-For' in request.headers:
        # X-Forwarded-For can contain multiple IPs, get the first (original client)
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    if 'X-Real-IP' in request.headers:
        return request.headers['X-Real-IP']
    # Fallback to remote address
    return request.remote_addr or '127.0.0.1'

# Initialize rate limiter with custom IP detection
limiter = Limiter(
    app=app,
    key_func=get_real_ip,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

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
    
    # Photo workflow fields
    qr_token = db.Column(db.String(100), unique=True, nullable=True)  # UUID for QR code
    photo_count = db.Column(db.Integer, default=0)  # Number of photos for this person
    drive_folder_id = db.Column(db.String(200), nullable=True)  # Google Drive folder ID
    drive_share_link = db.Column(db.String(500), nullable=True)  # Shareable link
    photos_email_sent = db.Column(db.Boolean, default=False)  # Track if Drive link was emailed
    photos_email_sent_at = db.Column(db.DateTime, nullable=True)  # When Drive email was sent
    
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
            'photos_sent': self.photos_sent,
            'qr_token': self.qr_token,
            'photo_count': self.photo_count,
            'drive_share_link': self.drive_share_link,
            'photos_email_sent': self.photos_email_sent,
            'photos_email_sent_at': self.photos_email_sent_at.isoformat() if self.photos_email_sent_at else None
        }

# PhotoBatch Model - Represents a batch of uploaded photos
class PhotoBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_name = db.Column(db.String(200), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    total_photos = db.Column(db.Integer, default=0)
    total_size_mb = db.Column(db.Float, default=0.0)
    processed_photos = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='uploading')  # uploading, uploaded, processing, completed, failed
    current_action = db.Column(db.String(500), nullable=True)  # Real-time status message
    people_found = db.Column(db.Integer, default=0)  # Number of people found during processing
    unmatched_photos = db.Column(db.Integer, default=0)  # Photos that couldn't be matched
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<PhotoBatch {self.batch_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_name': self.batch_name,
            'upload_time': self.upload_time.isoformat(),
            'total_photos': self.total_photos,
            'total_size_mb': self.total_size_mb,
            'processed_photos': self.processed_photos,
            'status': self.status,
            'current_action': self.current_action,
            'people_found': self.people_found,
            'unmatched_photos': self.unmatched_photos,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            'error_message': self.error_message
        }

# Photo Model - Individual photos in a batch
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('photo_batch.id'), nullable=False)
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'), nullable=True)
    filename = db.Column(db.String(500), nullable=False)
    original_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0)  # Size in bytes
    is_qr_code = db.Column(db.Boolean, default=False)  # True if this photo contains a QR code
    qr_data = db.Column(db.String(500), nullable=True)  # Parsed QR code data
    processed = db.Column(db.Boolean, default=False)
    uploaded_to_drive = db.Column(db.Boolean, default=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = db.relationship('PhotoBatch', backref='photos')
    registration = db.relationship('Registration', backref='photos')
    
    def __repr__(self):
        return f'<Photo {self.filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'registration_id': self.registration_id,
            'filename': self.filename,
            'file_size': self.file_size,
            'is_qr_code': self.is_qr_code,
            'qr_data': self.qr_data,
            'processed': self.processed,
            'uploaded_to_drive': self.uploaded_to_drive,
            'upload_time': self.upload_time.isoformat()
        }

# ProcessingLog Model - Detailed log of processing events
class ProcessingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('photo_batch.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(100), nullable=False)  # qr_detected, photos_assigned, upload_started, etc.
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), default='info')  # info, warning, error
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'), nullable=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photo.id'), nullable=True)
    
    # Relationships
    batch = db.relationship('PhotoBatch', backref='logs')
    registration = db.relationship('Registration', backref='processing_logs')
    photo = db.relationship('Photo', backref='logs')
    
    def __repr__(self):
        return f'<ProcessingLog {self.action} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'message': self.message,
            'level': self.level,
            'registration_id': self.registration_id,
            'photo_id': self.photo_id
        }

# Admin settings model (stored in database)
class AdminSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500), nullable=False)
    
    @staticmethod
    def get_setting(key, default=None):
        try:
            setting = AdminSettings.query.filter_by(key=key).first()
            return setting.value if setting else default
        except Exception:
            # Return default if table doesn't exist or query fails
            return default
    
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
        try:
            account = EmailAccount.query.filter_by(is_default=True, is_active=True).first()
            if not account:
                # If no default, get the first active account
                account = EmailAccount.query.filter_by(is_active=True).first()
            return account
        except Exception:
            # Return None if table doesn't exist or query fails
            return None
    
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

# Input validation functions
def validate_email(email):
    """Validate email format"""
    if not email or len(email) > 120:
        return False
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name(name):
    """Validate name input (letters, spaces, hyphens, apostrophes only)"""
    if not name or len(name) > 100 or len(name) < 1:
        return False
    # Allow letters, spaces, hyphens, apostrophes, and accented characters
    pattern = r"^[a-zA-ZÀ-ÿ\s'-]+$"
    return re.match(pattern, name) is not None

def sanitize_input(text):
    """Sanitize text input to prevent XSS"""
    if not text:
        return ""
    # Strip HTML tags and dangerous characters
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Add security headers and disable caching
@app.after_request
def add_header(response):
    """Add security headers and prevent caching of HTML pages"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Prevent caching of HTML pages
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# Context processor to inject CSRF token
@app.context_processor
def inject_csrf_token():
    """Make CSRF token available to all templates"""
    return dict(csrf_token=generate_csrf)

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    """Handle bad request errors (including CSRF failures)"""
    return jsonify({'error': 'Bad request. Please refresh the page and try again.'}), 400

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit errors"""
    return jsonify({'error': 'Too many requests. Please slow down and try again later.'}), 429

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    # Log the error
    app.logger.error(f'Internal error: {str(e)}')
    
    # Check if request expects JSON
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({'error': 'An internal error occurred. Please try again later.'}), 500
    
    # For HTML requests, return a proper error page
    error_message = 'An internal error occurred. Please try again later.'
    
    # Add helpful message for database errors
    if 'no such column' in str(e).lower() or 'operational error' in str(e).lower():
        error_message = 'Database error detected. Please run the migration script or contact the administrator.'
    
    return render_template('error.html', error=error_message), 500

# Routes
@app.route('/')
def index():
    """Display the registration form"""
    return render_template('index.html')

@app.route('/register', methods=['POST'])
@limiter.limit("10 per minute")  # Rate limit: 10 registrations per minute per IP
def register():
    """Handle registration form submission"""
    try:
        data = request.form
        
        # Validate required fields
        if not data.get('first_name') or not data.get('last_name') or not data.get('email'):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Sanitize and validate inputs
        first_name = sanitize_input(data['first_name'].strip())
        last_name = sanitize_input(data['last_name'].strip())
        email = data['email'].strip().lower()
        
        # Validate name formats
        if not validate_name(first_name):
            return jsonify({'error': 'Invalid first name format'}), 400
        
        if not validate_name(last_name):
            return jsonify({'error': 'Invalid last name format'}), 400
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Generate unique QR token for photo workflow
        qr_token = str(uuid.uuid4())
        
        # Create new registration
        registration = Registration(
            first_name=first_name,
            last_name=last_name,
            email=email,
            qr_token=qr_token
        )
        
        db.session.add(registration)
        db.session.commit()
        
        # Send confirmation email if enabled
        send_confirmation = os.getenv('SEND_CONFIRMATION_EMAIL', 'true').lower() == 'true'
        email_sent = False
        
        if send_confirmation:
            try:
                # Get default confirmation account from settings (safe fallback)
                confirmation_account_id = None
                try:
                    confirmation_account_id = AdminSettings.get_setting('DEFAULT_CONFIRMATION_ACCOUNT_ID', '')
                except Exception as settings_error:
                    app.logger.warning(f'Could not get settings: {str(settings_error)}')
                
                if confirmation_account_id:
                    # Use specified account from settings
                    default_account = EmailAccount.query.get(int(confirmation_account_id))
                else:
                    # Fallback to system default account
                    try:
                        default_account = EmailAccount.get_default()
                    except Exception:
                        default_account = None
                
                if default_account:
                    email_sent = send_confirmation_email(
                        to_email=registration.email,
                        first_name=registration.first_name,
                        last_name=registration.last_name,
                        registration_id=registration.id,
                        qr_token=registration.qr_token,
                        account=default_account
                    )
                    if email_sent:
                        registration.confirmation_sent = True
                        db.session.commit()
                else:
                    app.logger.warning('No email account configured for confirmations')
            except Exception as e:
                app.logger.error(f'Failed to send confirmation email: {str(e)}')
                import traceback
                app.logger.error(traceback.format_exc())
        
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
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

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
@limiter.limit("5 per minute")  # Rate limit: 5 login attempts per minute
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')
        
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
        
        if username == admin_username and password == admin_password:
            session['admin_logged_in'] = True
            session.permanent = True
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
    try:
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
    except Exception as e:
        app.logger.error(f'Error in admin dashboard: {str(e)}')
        # Check if it's a database schema issue
        if 'no such column' in str(e).lower() or 'operational' in str(e).lower():
            return render_template('error.html', 
                error='Database schema mismatch detected. The database needs to be migrated to support new photo workflow features. Please run the migration script.'), 500
        # Re-raise for general error handler
        raise

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Admin settings configuration"""
    if request.method == 'POST':
        # Update confirmation email setting
        send_confirmation = request.form.get('send_confirmation', 'false')
        AdminSettings.set_setting('SEND_CONFIRMATION_EMAIL', send_confirmation)
        
        # Update default email account selections
        confirmation_account_id = request.form.get('confirmation_account_id', '')
        photos_account_id = request.form.get('photos_account_id', '')
        test_account_id = request.form.get('test_account_id', '')
        
        AdminSettings.set_setting('DEFAULT_CONFIRMATION_ACCOUNT_ID', confirmation_account_id)
        AdminSettings.set_setting('DEFAULT_PHOTOS_ACCOUNT_ID', photos_account_id)
        AdminSettings.set_setting('DEFAULT_TEST_ACCOUNT_ID', test_account_id)
        
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    # Load current settings
    send_confirmation = AdminSettings.get_setting('SEND_CONFIRMATION_EMAIL', os.getenv('SEND_CONFIRMATION_EMAIL', 'true'))
    confirmation_account_id = AdminSettings.get_setting('DEFAULT_CONFIRMATION_ACCOUNT_ID', '')
    photos_account_id = AdminSettings.get_setting('DEFAULT_PHOTOS_ACCOUNT_ID', '')
    test_account_id = AdminSettings.get_setting('DEFAULT_TEST_ACCOUNT_ID', '')
    
    # Get all active email accounts
    email_accounts = EmailAccount.query.filter_by(is_active=True).all()
    
    return render_template('admin_settings.html', 
                         send_confirmation=send_confirmation,
                         confirmation_account_id=confirmation_account_id,
                         photos_account_id=photos_account_id,
                         test_account_id=test_account_id,
                         email_accounts=email_accounts)

@app.route('/admin/resend-confirmation/<int:registration_id>', methods=['POST'])
@login_required
def admin_resend_confirmation(registration_id):
    """Resend confirmation email to a specific registration"""
    try:
        registration = Registration.query.get_or_404(registration_id)
        
        # Get default confirmation account from settings
        confirmation_account_id = AdminSettings.get_setting('DEFAULT_CONFIRMATION_ACCOUNT_ID', '')
        if confirmation_account_id:
            account = EmailAccount.query.get(int(confirmation_account_id))
        else:
            # Fallback to system default
            account = EmailAccount.get_default()
        
        if not account:
            flash('No email account configured', 'error')
            return redirect(url_for('admin_dashboard'))
        
        success = send_confirmation_email(
            to_email=registration.email,
            first_name=registration.first_name,
            last_name=registration.last_name,
            registration_id=registration.id,
            qr_token=registration.qr_token,
            account=account
        )
        
        if success:
            registration.confirmation_sent = True
            db.session.commit()
            flash(f'Confirmation email with QR code resent to {registration.email} from "{account.name}"', 'success')
        else:
            flash(f'Failed to resend confirmation email to {registration.email}', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-photos/<int:registration_id>', methods=['POST'])
@login_required
def admin_send_photos(registration_id):
    """Send photos email to a specific registration"""
    try:
        registration = Registration.query.get_or_404(registration_id)
        photos_link = request.form.get('photos_link', '')
        
        # Get default photos account from settings
        photos_account_id = AdminSettings.get_setting('DEFAULT_PHOTOS_ACCOUNT_ID', '')
        if photos_account_id:
            account = EmailAccount.query.get(int(photos_account_id))
        else:
            # Fallback to system default
            account = EmailAccount.get_default()
        
        if not account:
            flash('No email account configured. Please set up in Settings.', 'error')
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
    sent_count = 0
    failed_count = 0
    
    # Get default photos account from settings
    photos_account_id = AdminSettings.get_setting('DEFAULT_PHOTOS_ACCOUNT_ID', '')
    if photos_account_id:
        account = EmailAccount.query.get(int(photos_account_id))
    else:
        # Fallback to system default
        account = EmailAccount.get_default()
    
    if not account:
        flash('No email account configured. Please set up in Settings.', 'error')
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

@app.route('/admin/delete-registration/<int:registration_id>', methods=['POST'])
@login_required
def admin_delete_registration(registration_id):
    """Delete a single registration"""
    try:
        registration = Registration.query.get_or_404(registration_id)
        name = f"{registration.first_name} {registration.last_name}"
        db.session.delete(registration)
        db.session.commit()
        flash(f'Registration for {name} has been deleted', 'success')
    except Exception as e:
        app.logger.error(f'Failed to delete registration: {str(e)}')
        flash(f'Error deleting registration: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-all-registrations', methods=['POST'])
@login_required
def admin_delete_all_registrations():
    """Delete all registrations with confirmation"""
    confirm = request.form.get('confirm', '')
    
    if confirm != 'DELETE ALL':
        flash('Deletion cancelled: confirmation text did not match', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        count = Registration.query.count()
        Registration.query.delete()
        db.session.commit()
        flash(f'Successfully deleted all {count} registrations', 'success')
    except Exception as e:
        app.logger.error(f'Failed to delete all registrations: {str(e)}')
        flash(f'Error deleting registrations: {str(e)}', 'error')
    
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

# ============================================
# Photo Upload Routes
# ============================================

@app.route('/admin/photos/upload')
@login_required
def admin_photo_upload():
    """Display photo upload page"""
    return render_template('admin_photo_upload.html')

@app.route('/admin/photos/create-batch', methods=['POST'])
@login_required
def create_photo_batch():
    """Create a new photo batch for uploading"""
    try:
        data = request.get_json()
        batch_name = data.get('batch_name', f'Batch_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        total_photos = data.get('total_photos', 0)
        total_size_mb = data.get('total_size_mb', 0)
        
        # Validate batch name
        if not batch_name or len(batch_name) > 200:
            return jsonify({'success': False, 'error': 'Invalid batch name'}), 400
        
        # Create batch record
        batch = PhotoBatch(
            batch_name=batch_name,
            upload_time=datetime.now(),
            total_photos=total_photos,
            total_size_mb=total_size_mb,
            processed_photos=0,
            status='uploading',
            current_action='Waiting for files...'
        )
        
        db.session.add(batch)
        db.session.commit()
        
        # Create batch directory
        batch_dir = os.path.join('uploads', 'batches', str(batch.id))
        os.makedirs(batch_dir, exist_ok=True)
        
        # Log batch creation
        log = ProcessingLog(
            batch_id=batch.id,
            action='batch_created',
            message=f'Batch "{batch_name}" created with expected {total_photos} photos ({total_size_mb:.2f} MB)',
            level='info'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'batch_id': batch.id,
            'batch_name': batch.batch_name
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error creating batch: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/photos/upload-file', methods=['POST'])
@login_required
def upload_photo_file():
    """Upload a single photo file to a batch"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        batch_id = request.form.get('batch_id')
        
        if not batch_id:
            return jsonify({'success': False, 'error': 'No batch ID provided'}), 400
        
        batch = PhotoBatch.query.get(batch_id)
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type (check magic bytes, not just extension)
        file_header = file.read(12)
        file.seek(0)
        
        # JPEG magic bytes: FF D8 FF
        is_jpeg = file_header[:3] == b'\xff\xd8\xff'
        
        if not is_jpeg:
            return jsonify({'success': False, 'error': 'File is not a valid JPEG image'}), 400
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return jsonify({'success': False, 'error': 'File size exceeds 50MB limit'}), 400
        
        # Preserve original filename for sorting (important for photo order!)
        original_filename = secure_filename(file.filename)
        if not original_filename:
            original_filename = f'photo_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.jpg'
        
        # Save file with original name, handle duplicates by adding counter to disk filename
        batch_dir = os.path.join('uploads', 'batches', str(batch_id))
        os.makedirs(batch_dir, exist_ok=True)
        
        disk_filename = original_filename
        file_path = os.path.join(batch_dir, disk_filename)
        
        # Handle duplicate filenames on disk (only affects storage, not sorting)
        counter = 1
        base_name, ext = os.path.splitext(original_filename)
        while os.path.exists(file_path):
            disk_filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(batch_dir, disk_filename)
            counter += 1
        
        file.save(file_path)
        
        # Create photo record - filename stores ORIGINAL name for proper sorting
        photo = Photo(
            batch_id=batch_id,
            filename=original_filename,  # IMPORTANT: Original name for sorting by camera order
            original_path=file_path,     # Actual disk path (may have counter suffix)
            file_size=file_size,
            upload_time=datetime.now(),
            is_qr_code=False,
            processed=False,
            uploaded_to_drive=False
        )
        
        db.session.add(photo)
        
        # Update batch progress
        batch.processed_photos = Photo.query.filter_by(batch_id=batch_id).count()
        batch.current_action = f'Uploading: {original_filename}'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'filename': original_filename,
            'file_size': file_size
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error uploading file: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/photos/batch-uploaded/<int:batch_id>', methods=['POST'])
@login_required
def mark_batch_uploaded(batch_id):
    """Mark a batch as fully uploaded"""
    try:
        batch = PhotoBatch.query.get_or_404(batch_id)
        
        # Update batch status
        batch.status = 'uploaded'
        batch.current_action = 'Upload complete. Ready to process.'
        
        # Update actual photo count
        actual_count = Photo.query.filter_by(batch_id=batch_id).count()
        batch.total_photos = actual_count
        
        # Log completion
        log = ProcessingLog(
            batch_id=batch_id,
            action='upload_completed',
            message=f'Upload completed: {actual_count} photos uploaded',
            level='info'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error marking batch as uploaded: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/photos/process/<int:batch_id>')
@login_required
def process_photo_batch(batch_id):
    """Display processing page for a batch (Phase 6)"""
    # This will be implemented in Phase 6
    batch = PhotoBatch.query.get_or_404(batch_id)
    flash('Photo processing will be implemented in Phase 6', 'info')
    return redirect(url_for('admin_dashboard'))

# Initialize database
# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        # Ensure the database directory exists and is writable
        db_path = database_uri.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_path)
        
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Created database directory: {db_dir}")
        
        # Check if database file exists and is writable
        if os.path.exists(db_path):
            if not os.access(db_path, os.W_OK):
                print(f"⚠️  Warning: Database file is not writable: {db_path}")
                print(f"   Please check file permissions.")
        
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
