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

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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
                email_sent = send_confirmation_email(
                    registration.email,
                    registration.first_name,
                    registration.last_name
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
    
    # Get email settings
    email_configured = create_email_sender_from_env() is not None
    send_confirmation = os.getenv('SEND_CONFIRMATION_EMAIL', 'true').lower() == 'true'
    
    stats = {
        'total_registrations': len(registrations),
        'confirmation_sent': sum(1 for r in registrations if r.confirmation_sent),
        'photos_sent': sum(1 for r in registrations if r.photos_sent),
        'email_configured': email_configured,
        'auto_confirmation': send_confirmation
    }
    
    return render_template('admin_dashboard.html', registrations=registrations, stats=stats)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Admin email settings configuration"""
    if request.method == 'POST':
        # Update email settings
        settings = {
            'SMTP_SERVER': request.form.get('smtp_server'),
            'SMTP_PORT': request.form.get('smtp_port'),
            'SMTP_USERNAME': request.form.get('smtp_username'),
            'SMTP_PASSWORD': request.form.get('smtp_password'),
            'SMTP_USE_TLS': request.form.get('smtp_use_tls', 'false'),
            'SMTP_FROM_EMAIL': request.form.get('smtp_from_email'),
            'SMTP_FROM_NAME': request.form.get('smtp_from_name'),
            'SEND_CONFIRMATION_EMAIL': request.form.get('send_confirmation', 'false'),
            'CONFIRMATION_EMAIL_SUBJECT': request.form.get('confirmation_subject'),
            'PHOTOS_EMAIL_SUBJECT': request.form.get('photos_subject'),
        }
        
        # Save to database (for runtime changes)
        for key, value in settings.items():
            AdminSettings.set_setting(key, value)
        
        # Note: For permanent changes, update .env file
        flash('Settings saved! Note: Restart the service to apply changes from .env file.', 'success')
        return redirect(url_for('admin_settings'))
    
    # Load current settings
    current_settings = {
        'smtp_server': AdminSettings.get_setting('SMTP_SERVER', os.getenv('SMTP_SERVER', '')),
        'smtp_port': AdminSettings.get_setting('SMTP_PORT', os.getenv('SMTP_PORT', '587')),
        'smtp_username': AdminSettings.get_setting('SMTP_USERNAME', os.getenv('SMTP_USERNAME', '')),
        'smtp_from_email': AdminSettings.get_setting('SMTP_FROM_EMAIL', os.getenv('SMTP_FROM_EMAIL', '')),
        'smtp_from_name': AdminSettings.get_setting('SMTP_FROM_NAME', os.getenv('SMTP_FROM_NAME', 'Photo Registration')),
        'smtp_use_tls': AdminSettings.get_setting('SMTP_USE_TLS', os.getenv('SMTP_USE_TLS', 'true')),
        'send_confirmation': AdminSettings.get_setting('SEND_CONFIRMATION_EMAIL', os.getenv('SEND_CONFIRMATION_EMAIL', 'true')),
        'confirmation_subject': AdminSettings.get_setting('CONFIRMATION_EMAIL_SUBJECT', os.getenv('CONFIRMATION_EMAIL_SUBJECT', 'Registration Confirmation')),
        'photos_subject': AdminSettings.get_setting('PHOTOS_EMAIL_SUBJECT', os.getenv('PHOTOS_EMAIL_SUBJECT', 'Your Event Photos')),
    }
    
    # Get available templates
    templates_dir = os.path.join(os.path.dirname(__file__), 'email_templates')
    templates = []
    if os.path.exists(templates_dir):
        templates = [f for f in os.listdir(templates_dir) if f.endswith('.html')]
    
    return render_template('admin_settings.html', settings=current_settings, templates=templates)

@app.route('/admin/test-email', methods=['POST'])
@login_required
def admin_test_email():
    """Test email configuration"""
    try:
        success = test_email_configuration()
        if success:
            flash('Test email sent successfully! Check your inbox.', 'success')
        else:
            flash('Failed to send test email. Check your SMTP configuration.', 'error')
    except Exception as e:
        flash(f'Error sending test email: {str(e)}', 'error')
    
    return redirect(url_for('admin_settings'))

@app.route('/admin/send-photos/<int:registration_id>', methods=['POST'])
@login_required
def admin_send_photos(registration_id):
    """Send photos email to a specific registration"""
    try:
        registration = Registration.query.get_or_404(registration_id)
        photos_link = request.form.get('photos_link', '')
        
        success = send_photos_email(
            registration.email,
            registration.first_name,
            photos_link=photos_link if photos_link else None
        )
        
        if success:
            registration.photos_sent = True
            db.session.commit()
            flash(f'Photos email sent to {registration.email}', 'success')
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
    
    registrations = Registration.query.filter_by(photos_sent=False).all()
    
    for registration in registrations:
        try:
            success = send_photos_email(
                registration.email,
                registration.first_name,
                photos_link=photos_link if photos_link else None
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
    
    flash(f'Bulk send complete: {sent_count} sent, {failed_count} failed', 'success')
    return redirect(url_for('admin_dashboard'))

# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
