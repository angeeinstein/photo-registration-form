from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import os
import json
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

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload size

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
            'level': self.level
        }

# DriveOAuthToken Model - Stores OAuth 2.0 tokens for Google Drive access
class DriveOAuthToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_identifier = db.Column(db.String(100), unique=True, nullable=False)  # 'admin' or user ID
    access_token = db.Column(db.Text, nullable=False)  # OAuth access token
    refresh_token = db.Column(db.Text, nullable=False)  # OAuth refresh token (for long-term access)
    token_expiry = db.Column(db.DateTime, nullable=False)  # When access token expires
    scope = db.Column(db.Text, nullable=True)  # OAuth scopes granted
    email = db.Column(db.String(200), nullable=True)  # Google account email
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DriveOAuthToken {self.user_identifier} - {self.email}>'
    
    def is_expired(self):
        """Check if access token is expired"""
        return datetime.utcnow() >= self.token_expiry
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_identifier': self.user_identifier,
            'email': self.email,
            'scope': self.scope,
            'token_expiry': self.token_expiry.isoformat(),
            'is_expired': self.is_expired(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
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
    # Updated CSP to allow Google Identity Services for OAuth
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://accounts.google.com https://apis.google.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://accounts.google.com https://oauth2.googleapis.com; "
        "frame-src 'self' https://accounts.google.com;"
    )
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
@login_required  # Add authentication requirement
def list_registrations():
    """List all registrations (admin view - requires authentication)"""
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
        
        # Get photo batches (most recent first)
        photo_batches = PhotoBatch.query.order_by(PhotoBatch.upload_time.desc()).limit(10).all()
        
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
                             default_account=default_account,
                             photo_batches=photo_batches)
    except Exception as e:
        app.logger.error(f'Error in admin dashboard: {str(e)}')
        # Check if it's a database schema issue
        if 'no such column' in str(e).lower() or 'operational' in str(e).lower():
            return render_template('error.html', 
                error='Database schema mismatch detected. The database needs to be migrated to support new photo workflow features. Please run the migration script.'), 500
        # Re-raise for general error handler
        raise

@app.route('/admin/export/registrations.csv')
@login_required
def export_registrations_csv():
    """Export all registrations as CSV"""
    import csv
    from io import StringIO
    from flask import make_response
    
    try:
        registrations = Registration.query.order_by(Registration.registered_at.desc()).all()
        
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        
        # Write header
        writer.writerow([
            'ID',
            'First Name',
            'Last Name',
            'Email',
            'Registered At',
            'Confirmation Sent',
            'Photos Sent',
            'Photo Count',
            'Drive Share Link',
            'QR Token'
        ])
        
        # Write data rows
        for reg in registrations:
            writer.writerow([
                reg.id,
                reg.first_name,
                reg.last_name,
                reg.email,
                reg.registered_at.strftime('%Y-%m-%d %H:%M:%S') if reg.registered_at else '',
                'Yes' if reg.confirmation_sent else 'No',
                'Yes' if reg.photos_sent else 'No',
                reg.photo_count or 0,
                reg.drive_share_link or '',
                reg.qr_token or ''
            ])
        
        # Create response
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=registrations.csv"
        output.headers["Content-type"] = "text/csv"
        
        return output
        
    except Exception as e:
        app.logger.error(f'Error exporting CSV: {str(e)}')
        return "Error exporting CSV", 500

@app.route('/admin/registration/<int:registration_id>/qr-code')
@login_required
@csrf.exempt  # Exempt from CSRF for GET request
def get_registration_qr_code(registration_id):
    """Generate and return QR code image for a specific registration"""
    from io import BytesIO
    from flask import send_file
    
    try:
        # Get the registration
        registration = Registration.query.get_or_404(registration_id)
        
        # Import QR generator
        try:
            from qr_generator import generate_qr_code
        except ImportError as e:
            app.logger.error(f"QR generator module not found: {str(e)}")
            return jsonify({'error': 'QR generation not available'}), 500
        
        # Generate qr_token if not exists
        if not registration.qr_token:
            import uuid
            registration.qr_token = str(uuid.uuid4())
            db.session.commit()
            app.logger.info(f"Generated new QR token for registration {registration_id}")
        
        # Prepare person data
        person_data = {
            'first_name': registration.first_name,
            'last_name': registration.last_name,
            'email': registration.email,
            'registration_id': registration.id,
            'qr_token': registration.qr_token
        }
        
        app.logger.info(f"Generating QR code for registration {registration_id}: {registration.first_name} {registration.last_name}")
        
        # Generate QR code as PNG bytes
        qr_bytes = generate_qr_code(person_data, output_format='bytes')
        
        if not qr_bytes:
            app.logger.error(f"Failed to generate QR code for registration {registration_id}")
            return jsonify({'error': 'Failed to generate QR code'}), 500
        
        app.logger.info(f"QR code generated successfully for registration {registration_id}, size: {len(qr_bytes)} bytes")
        
        # Return as image
        return send_file(
            BytesIO(qr_bytes),
            mimetype='image/png',
            as_attachment=False,
            download_name=f'qr_code_{registration.first_name}_{registration.last_name}.png'
        )
        
    except Exception as e:
        app.logger.error(f"Error generating QR code for registration {registration_id}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to generate QR code: {str(e)}'}), 500

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

# Google Drive Settings Routes
@app.route('/admin/drive/oauth')
@login_required
def admin_drive_oauth():
    """Google Drive OAuth 2.0 connection page"""
    oauth_client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    return render_template('admin_drive_oauth.html', oauth_client_id=oauth_client_id)

@app.route('/admin/drive/settings', methods=['GET', 'POST'])
@login_required
def admin_drive_settings():
    """Google Drive API configuration"""
    from drive_credentials_manager import DriveCredentialsManager
    
    drive_manager = DriveCredentialsManager()
    
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'credentials_file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(url_for('admin_drive_settings'))
            
            file = request.files['credentials_file']
            
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('admin_drive_settings'))
            
            if not file.filename.endswith('.json'):
                flash('Invalid file type. Please upload a JSON file', 'error')
                return redirect(url_for('admin_drive_settings'))
            
            # Parse JSON content
            try:
                credentials_data = json.loads(file.read().decode('utf-8'))
            except json.JSONDecodeError:
                flash('Invalid JSON file. Please check the file format', 'error')
                return redirect(url_for('admin_drive_settings'))
            
            # Get additional settings
            parent_folder_id = request.form.get('parent_folder_id', '').strip() or None
            folder_name_format = request.form.get('folder_name_format', 'FirstName_LastName')
            
            # Save credentials
            drive_manager.save_credentials(
                credentials_data,
                parent_folder_id=parent_folder_id,
                folder_name_format=folder_name_format
            )
            
            flash('Google Drive credentials saved successfully! You can now test the connection.', 'success')
            return redirect(url_for('admin_drive_settings'))
            
        except ValueError as e:
            flash(f'Invalid credentials: {str(e)}', 'error')
            return redirect(url_for('admin_drive_settings'))
        except Exception as e:
            app.logger.error(f'Error saving Drive credentials: {str(e)}')
            flash(f'Error saving credentials: {str(e)}', 'error')
            return redirect(url_for('admin_drive_settings'))
    
    # GET request - show settings page
    drive_configured = drive_manager.is_configured()
    drive_info = drive_manager.get_config() if drive_configured else None
    
    return render_template('admin_drive_settings.html',
                         drive_configured=drive_configured,
                         drive_info=drive_info)

@app.route('/admin/drive/delete-credentials', methods=['POST'])
@login_required
def admin_drive_delete_credentials():
    """Delete Google Drive credentials"""
    from drive_credentials_manager import DriveCredentialsManager
    
    try:
        drive_manager = DriveCredentialsManager()
        drive_manager.delete_credentials()
        flash('Google Drive credentials removed successfully', 'success')
    except Exception as e:
        app.logger.error(f'Error deleting Drive credentials: {str(e)}')
        flash(f'Error removing credentials: {str(e)}', 'error')
    
    return redirect(url_for('admin_drive_settings'))

@app.route('/admin/drive/test-connection', methods=['POST'])
@login_required
def admin_drive_test_connection():
    """Test Google Drive API connection"""
    from drive_credentials_manager import DriveCredentialsManager
    
    try:
        drive_manager = DriveCredentialsManager()
        
        if not drive_manager.is_configured():
            return jsonify({
                'success': False,
                'error': 'Google Drive is not configured'
            }), 400
        
        # Get credentials path
        creds_path = drive_manager.get_credentials_path()
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            # Create credentials with full Drive scope
            credentials = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            
            # Build Drive service
            service = build('drive', 'v3', credentials=credentials)
            
            # Test by getting user info
            about = service.about().get(fields='user').execute()
            user_email = about.get('user', {}).get('emailAddress', 'Unknown')
            
            # Log for debugging
            app.logger.info(f"Service account authenticated: {user_email}")
            
            # Test parent folder access if configured
            config = drive_manager.get_config()
            parent_folder_id = config.get('parent_folder_id')
            
            if parent_folder_id:
                try:
                    # First, list what the service account can see
                    app.logger.info(f"Attempting to access folder ID: {parent_folder_id}")
                    
                    # Try to list files to see if we can query at all
                    try:
                        list_result = service.files().list(
                            pageSize=1,
                            fields='files(id, name)',
                            supportsAllDrives=True,
                            includeItemsFromAllDrives=True
                        ).execute()
                        app.logger.info(f"Service account can list files: {len(list_result.get('files', []))} files found")
                    except Exception as list_error:
                        app.logger.error(f"Cannot list files: {str(list_error)}")
                    
                    # First, try to get folder metadata
                    folder = service.files().get(
                        fileId=parent_folder_id,
                        fields='id, name, mimeType, capabilities, owners, shared, ownedByMe, permissions',
                        supportsAllDrives=True
                    ).execute()
                    
                    app.logger.info(f"Folder found: {folder.get('name')}")
                    app.logger.info(f"Owned by service account: {folder.get('ownedByMe')}")
                    app.logger.info(f"Shared: {folder.get('shared')}")
                    
                    # Check permissions
                    try:
                        permissions = service.permissions().list(
                            fileId=parent_folder_id,
                            fields='permissions(id, type, role, emailAddress)',
                            supportsAllDrives=True
                        ).execute()
                        
                        app.logger.info(f"Folder permissions: {permissions.get('permissions', [])}")
                        
                        # Check if service account has permission
                        has_permission = False
                        for perm in permissions.get('permissions', []):
                            if perm.get('emailAddress') == user_email:
                                has_permission = True
                                app.logger.info(f"Service account permission found: {perm.get('role')}")
                        
                        if not has_permission:
                            app.logger.warning("Service account email not found in folder permissions!")
                            
                    except Exception as perm_error:
                        app.logger.error(f"Cannot list permissions: {str(perm_error)}")
                    
                    # Verify it's actually a folder
                    if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                        return jsonify({
                            'success': False,
                            'error': f'❌ The provided ID is not a folder. It\'s a {folder.get("mimeType")}.\n\nPlease provide a folder ID, not a file ID.'
                        }), 400
                    
                    # Check if we can create files in this folder
                    capabilities = folder.get('capabilities', {})
                    can_add_children = capabilities.get('canAddChildren', False)
                    
                    if not can_add_children:
                        config = drive_manager.get_config()
                        service_email = config.get('service_account_email', 'unknown')
                        
                        return jsonify({
                            'success': False,
                            'error': f'❌ Service account cannot create files in this folder.\n\n📧 Service Account: {service_email}\n\n✅ To fix this:\n1. Open Google Drive in your browser\n2. Find the folder: {folder.get("name")}\n3. Right-click → Share\n4. Add the service account email above\n5. Set permission to "Editor" (not Viewer!)\n6. Uncheck "Notify people"\n7. Click Share\n8. Wait 30 seconds for permissions to propagate\n9. Try testing again'
                        }), 400
                    
                    folder_message = f"✅ Parent folder access verified: '{folder.get('name')}' (can create files)"
                    
                except Exception as folder_error:
                    error_msg = str(folder_error)
                    
                    # Get service account email for better error message
                    config = drive_manager.get_config()
                    service_email = config.get('service_account_email', 'unknown')
                    
                    # Provide helpful error message based on error type
                    if 'File not found' in error_msg or 'notFound' in error_msg or '404' in error_msg:
                        return jsonify({
                            'success': False,
                            'error': f'❌ Cannot access folder with ID: {parent_folder_id}\n\n📧 Service Account: {service_email}\n\n🔍 Possible causes:\n1. The folder ID is incorrect\n2. The folder hasn\'t been shared with the service account\n3. The folder was deleted\n\n✅ To fix:\n1. Verify the folder ID is correct (copy from Drive URL)\n2. Open the folder in Google Drive\n3. Click Share button\n4. Add the service account email above\n5. Set permission to "Editor"\n6. Click Share\n7. Try again'
                        }), 400
                    elif 'insufficientPermissions' in error_msg or 'Permission denied' in error_msg:
                        return jsonify({
                            'success': False,
                            'error': f'❌ Permission denied to access folder.\n\n📧 Service Account: {service_email}\n\nThe service account needs "Editor" permissions on this folder.\n\n✅ To fix:\n1. Open the folder in Google Drive\n2. Click Share button\n3. Add the service account email: {service_email}\n4. Change permission to "Editor" (not "Viewer"!)\n5. Click Share\n6. Try again'
                        }), 400
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'Cannot access parent folder: {error_msg}\n\n📧 Service Account: {service_email}\n\nMake sure:\n1. The folder ID is correct\n2. The folder is shared with the service account with "Editor" permissions\n3. You waited 30 seconds after sharing'
                        }), 400
            else:
                folder_message = "Using root folder (My Drive)"
            
            return jsonify({
                'success': True,
                'message': f'Connection successful! Service account: {user_email}. {folder_message}'
            })
            
        finally:
            # Cleanup temporary credentials
            drive_manager.cleanup_temp_credentials()
            
    except Exception as e:
        app.logger.error(f'Drive connection test failed: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Connection failed: {str(e)}'
        }), 500

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
# OAuth 2.0 Routes for Google Drive
# ============================================

@app.route('/admin/drive/oauth/status')
@login_required
def admin_drive_oauth_status():
    """Get OAuth connection status"""
    try:
        token = DriveOAuthToken.query.filter_by(user_identifier='admin').first()
        
        if token:
            return jsonify({
                'connected': True,
                'email': token.email,
                'expires_at': token.token_expiry.isoformat(),
                'is_expired': token.is_expired()
            })
        else:
            return jsonify({'connected': False})
    except Exception as e:
        app.logger.error(f'Error checking OAuth status: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/admin/drive/oauth/exchange', methods=['POST'])
@login_required
def admin_drive_oauth_exchange():
    """Exchange authorization code for OAuth tokens"""
    import requests
    from datetime import timedelta
    
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400
        
        # Get OAuth client credentials from environment
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        redirect_uri = os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'postmessage')  # For popup flow
        
        if not client_id or not client_secret:
            return jsonify({'error': 'OAuth credentials not configured in environment'}), 500
        
        # Exchange code for tokens
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        app.logger.info(f'Exchanging OAuth code for tokens...')
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            app.logger.error(f'Token exchange failed: {response.text}')
            return jsonify({'error': 'Failed to exchange authorization code', 'details': response.text}), 400
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')
        expires_in = token_response.get('expires_in', 3600)  # Default 1 hour
        scope = token_response.get('scope', '')
        
        if not access_token or not refresh_token:
            return jsonify({'error': 'No tokens received from Google'}), 400
        
        # Get user info from Google
        userinfo_url = 'https://www.googleapis.com/oauth2/v2/userinfo'
        headers = {'Authorization': f'Bearer {access_token}'}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        
        email = None
        if userinfo_response.status_code == 200:
            userinfo = userinfo_response.json()
            email = userinfo.get('email')
        
        # Calculate expiry time
        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Save or update token in database
        token = DriveOAuthToken.query.filter_by(user_identifier='admin').first()
        
        if token:
            # Update existing token
            token.access_token = access_token
            token.refresh_token = refresh_token
            token.token_expiry = token_expiry
            token.scope = scope
            token.email = email
            token.updated_at = datetime.utcnow()
        else:
            # Create new token
            token = DriveOAuthToken(
                user_identifier='admin',
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
                scope=scope,
                email=email
            )
            db.session.add(token)
        
        db.session.commit()
        
        app.logger.info(f'OAuth tokens saved successfully for {email}')
        
        return jsonify({
            'success': True,
            'email': email,
            'expires_at': token_expiry.isoformat()
        })
        
    except Exception as e:
        app.logger.error(f'Error exchanging OAuth code: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/drive/oauth/disconnect', methods=['POST'])
@login_required
def admin_drive_oauth_disconnect():
    """Disconnect OAuth and revoke tokens"""
    import requests
    
    try:
        token = DriveOAuthToken.query.filter_by(user_identifier='admin').first()
        
        if token:
            # Revoke the refresh token with Google
            try:
                revoke_url = f'https://oauth2.googleapis.com/revoke?token={token.refresh_token}'
                requests.post(revoke_url)
                app.logger.info('OAuth token revoked with Google')
            except Exception as revoke_error:
                app.logger.warning(f'Failed to revoke token with Google: {str(revoke_error)}')
            
            # Delete from database
            db.session.delete(token)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Disconnected successfully'})
        else:
            return jsonify({'success': False, 'message': 'No connection to disconnect'})
            
    except Exception as e:
        app.logger.error(f'Error disconnecting OAuth: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/drive/oauth/refresh', methods=['POST'])
@login_required
def admin_drive_oauth_refresh():
    """Manually refresh OAuth access token"""
    import requests
    from datetime import timedelta
    
    try:
        token = DriveOAuthToken.query.filter_by(user_identifier='admin').first()
        
        if not token:
            return jsonify({'error': 'No OAuth connection found'}), 404
        
        # Get OAuth client credentials
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            return jsonify({'error': 'OAuth credentials not configured'}), 500
        
        # Refresh the access token
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': token.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(token_url, data=token_data)
        
        if response.status_code != 200:
            app.logger.error(f'Token refresh failed: {response.text}')
            return jsonify({'error': 'Failed to refresh token', 'details': response.text}), 400
        
        token_response = response.json()
        access_token = token_response.get('access_token')
        expires_in = token_response.get('expires_in', 3600)
        
        # Update token in database
        token.access_token = access_token
        token.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        token.updated_at = datetime.utcnow()
        db.session.commit()
        
        app.logger.info('OAuth token refreshed successfully')
        
        return jsonify({
            'success': True,
            'expires_at': token.token_expiry.isoformat()
        })
        
    except Exception as e:
        app.logger.error(f'Error refreshing OAuth token: {str(e)}')
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/drive/folder-config', methods=['GET', 'POST'])
@login_required
def admin_drive_folder_config():
    """Get or set the parent folder ID for Drive uploads"""
    try:
        if request.method == 'GET':
            # Return current folder configuration
            folder_id = os.environ.get('GOOGLE_DRIVE_PARENT_FOLDER_ID', '')
            return jsonify({
                'folder_id': folder_id if folder_id else None
            })
        
        elif request.method == 'POST':
            # Update folder configuration
            data = request.get_json()
            folder_id = data.get('folder_id', '').strip()
            
            # Path to .env file
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            
            # Read existing .env file
            env_lines = []
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()
            
            # Update or add GOOGLE_DRIVE_PARENT_FOLDER_ID
            found = False
            for i, line in enumerate(env_lines):
                if line.strip().startswith('GOOGLE_DRIVE_PARENT_FOLDER_ID='):
                    if folder_id:
                        env_lines[i] = f'GOOGLE_DRIVE_PARENT_FOLDER_ID={folder_id}\n'
                    else:
                        env_lines[i] = '#GOOGLE_DRIVE_PARENT_FOLDER_ID=\n'
                    found = True
                    break
            
            if not found:
                # Add new line
                if folder_id:
                    env_lines.append(f'\nGOOGLE_DRIVE_PARENT_FOLDER_ID={folder_id}\n')
                else:
                    env_lines.append(f'\n#GOOGLE_DRIVE_PARENT_FOLDER_ID=\n')
            
            # Write back to .env file
            with open(env_path, 'w') as f:
                f.writelines(env_lines)
            
            # Update current environment
            if folder_id:
                os.environ['GOOGLE_DRIVE_PARENT_FOLDER_ID'] = folder_id
            else:
                os.environ.pop('GOOGLE_DRIVE_PARENT_FOLDER_ID', None)
            
            app.logger.info(f'Drive parent folder updated: {folder_id if folder_id else "None (using Drive root)"}')
            
            return jsonify({
                'success': True,
                'message': 'Folder configuration saved successfully',
                'folder_id': folder_id if folder_id else None
            })
    
    except Exception as e:
        app.logger.error(f'Error managing folder config: {str(e)}')
        return jsonify({'error': str(e)}), 500

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
def process_photo_batch_page(batch_id):
    """Display processing page with real-time metrics"""
    batch = PhotoBatch.query.get_or_404(batch_id)
    
    # Allow viewing progress during processing, or starting new processing
    if batch.status not in ['uploaded', 'error', 'processing', 'completed']:
        flash(f'Batch cannot be processed in current status: {batch.status}', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_photo_process.html', batch=batch)

@app.route('/admin/photos/process/<int:batch_id>/start', methods=['POST'])
@login_required
def start_batch_processing(batch_id):
    """Start processing a batch (API endpoint) - runs in background thread"""
    import threading
    
    try:
        from photo_processor import PhotoProcessor
        
        batch = PhotoBatch.query.get_or_404(batch_id)
        
        # Verify batch status
        if batch.status not in ['uploaded', 'error']:
            return jsonify({
                'success': False,
                'error': f'Batch cannot be processed in current status: {batch.status}'
            }), 400
        
        # Start processing in background thread
        def process_in_background():
            """Background processing function"""
            try:
                with app.app_context():
                    processor = PhotoProcessor(batch_id)
                    metrics = processor.process_batch()
                    app.logger.info(f'Batch {batch_id} processing completed: {metrics}')
            except Exception as e:
                app.logger.error(f'Background processing error for batch {batch_id}: {str(e)}')
                import traceback
                app.logger.error(traceback.format_exc())
        
        # Start background thread
        thread = threading.Thread(target=process_in_background, daemon=True)
        thread.start()
        
        # Return immediately
        return jsonify({
            'success': True,
            'message': 'Processing started in background',
            'batch_id': batch_id
        })
        
    except Exception as e:
        app.logger.error(f'Error starting batch processing: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/photos/process/<int:batch_id>/status')
@login_required
def get_processing_status(batch_id):
    """Get current processing status (for real-time updates)"""
    try:
        batch = PhotoBatch.query.get_or_404(batch_id)
        
        # Get processing metrics
        total_photos = batch.total_photos or 0
        processed_photos = batch.processed_photos or 0
        progress_pct = int((processed_photos / total_photos * 100)) if total_photos > 0 else 0
        
        # Count people found (registrations with photos)
        people_found = db.session.query(Registration).join(Photo).filter(
            Photo.batch_id == batch_id,
            Photo.registration_id.isnot(None)
        ).distinct().count()
        
        # Count unmatched photos
        unmatched_count = Photo.query.filter_by(
            batch_id=batch_id,
            registration_id=None
        ).count()
        
        return jsonify({
            'success': True,
            'status': batch.status,
            'current_action': batch.current_action or '',
            'processed_photos': processed_photos,
            'total_photos': total_photos,
            'progress_percentage': progress_pct,
            'people_found': people_found,
            'unmatched_photos': unmatched_count
        })
        
    except Exception as e:
        app.logger.error(f'Error getting processing status: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/photos/batch/<int:batch_id>/delete', methods=['POST'])
@login_required
def delete_photo_batch(batch_id):
    """Delete a photo batch and all associated data"""
    try:
        batch = PhotoBatch.query.get_or_404(batch_id)
        batch_name = batch.batch_name
        
        # Delete all photos in this batch
        photos = Photo.query.filter_by(batch_id=batch_id).all()
        photo_count = len(photos)
        for photo in photos:
            db.session.delete(photo)
        
        # Delete all processing logs
        logs = ProcessingLog.query.filter_by(batch_id=batch_id).all()
        log_count = len(logs)
        for log in logs:
            db.session.delete(log)
        
        # Delete the batch itself
        db.session.delete(batch)
        db.session.commit()
        
        # Delete physical files
        import shutil
        batch_dir = Path(f"uploads/batches/{batch_id}")
        if batch_dir.exists():
            shutil.rmtree(batch_dir)
            app.logger.info(f"Deleted batch directory: {batch_dir}")
        
        flash(f'Batch "{batch_name}" deleted successfully ({photo_count} photos, {log_count} logs)', 'success')
        app.logger.info(f"Deleted batch {batch_id}: {batch_name}")
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error deleting batch {batch_id}: {str(e)}')
        flash(f'Error deleting batch: {str(e)}', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/photos/batch-results/<int:batch_id>')
@login_required
def batch_results_page(batch_id):
    """Display batch results with email sending interface"""
    batch = PhotoBatch.query.get_or_404(batch_id)
    
    # Get all people found in this batch (registrations with photos)
    people = db.session.query(Registration).join(Photo).filter(
        Photo.batch_id == batch_id,
        Photo.registration_id.isnot(None)
    ).distinct().all()
    
    # Count emails sent
    emails_sent_count = sum(1 for p in people if p.photos_email_sent)
    
    return render_template('admin_batch_results.html',
                          batch=batch,
                          people=people,
                          people_count=len(people),
                          emails_sent_count=emails_sent_count)

@app.route('/admin/photos/send-email/<int:registration_id>', methods=['POST'])
@login_required
def send_individual_photo_email(registration_id):
    """Send photo delivery email to a single person"""
    try:
        from send_email import send_photo_delivery_email, create_email_sender_from_account
        
        person = Registration.query.get_or_404(registration_id)
        
        # Check if person has Drive link
        if not person.drive_share_link:
            return jsonify({
                'success': False,
                'error': 'No Google Drive link available for this person'
            }), 400
        
        # Check if email already sent
        if person.photos_email_sent:
            return jsonify({
                'success': False,
                'error': 'Email already sent to this person'
            }), 400
        
        # Get default email account
        email_account = EmailAccount.query.filter_by(is_default=True, is_active=True).first()
        
        # Get event name from settings or use default
        event_name = os.getenv('EVENT_NAME', 'our event')
        organization_name = os.getenv('ORGANIZATION_NAME', 'Photo Registration Team')
        retention_days = int(os.getenv('PHOTO_RETENTION_DAYS', '30'))
        
        # Send email
        success = send_photo_delivery_email(
            to_email=person.email,
            first_name=person.first_name,
            drive_link=person.drive_share_link,
            photo_count=person.photo_count,
            event_name=event_name,
            retention_days=retention_days,
            organization_name=organization_name,
            account=email_account
        )
        
        if success:
            # Update tracking
            person.photos_email_sent = True
            person.photos_email_sent_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'person_name': f'{person.first_name} {person.last_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send email'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error sending photo email: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/photos/send-all/<int:batch_id>', methods=['POST'])
@login_required
def send_all_photo_emails(batch_id):
    """Send photo delivery emails to all unsent people in a batch"""
    try:
        from send_email import send_photo_delivery_email
        
        batch = PhotoBatch.query.get_or_404(batch_id)
        
        # Get all people who haven't received emails yet
        people = db.session.query(Registration).join(Photo).filter(
            Photo.batch_id == batch_id,
            Photo.registration_id.isnot(None),
            Registration.photos_email_sent == False,
            Registration.drive_share_link.isnot(None)
        ).distinct().all()
        
        if not people:
            return jsonify({
                'success': False,
                'error': 'No people to send emails to'
            }), 400
        
        # Get default email account
        email_account = EmailAccount.query.filter_by(is_default=True, is_active=True).first()
        
        # Get event settings
        event_name = os.getenv('EVENT_NAME', 'our event')
        organization_name = os.getenv('ORGANIZATION_NAME', 'Photo Registration Team')
        retention_days = int(os.getenv('PHOTO_RETENTION_DAYS', '30'))
        
        # Send emails
        sent_count = 0
        failed = []
        
        for person in people:
            try:
                success = send_photo_delivery_email(
                    to_email=person.email,
                    first_name=person.first_name,
                    drive_link=person.drive_share_link,
                    photo_count=person.photo_count,
                    event_name=event_name,
                    retention_days=retention_days,
                    organization_name=organization_name,
                    account=email_account
                )
                
                if success:
                    person.photos_email_sent = True
                    person.photos_email_sent_at = datetime.utcnow()
                    sent_count += 1
                else:
                    failed.append(person.email)
                    
            except Exception as e:
                app.logger.error(f'Failed to send email to {person.email}: {str(e)}')
                failed.append(person.email)
        
        # Commit all updates
        db.session.commit()
        
        result = {
            'success': True,
            'emails_sent': sent_count,
            'total_attempted': len(people)
        }
        
        if failed:
            result['failed'] = failed
            result['message'] = f'Sent {sent_count}/{len(people)} emails. {len(failed)} failed.'
        
        return jsonify(result)
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error sending batch emails: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
