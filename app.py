from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

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
    
    def __repr__(self):
        return f'<Registration {self.first_name} {self.last_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'registered_at': self.registered_at.isoformat()
        }

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
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! You will receive your photos via email.',
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

# Initialize database
def init_db():
    """Initialize the database"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
