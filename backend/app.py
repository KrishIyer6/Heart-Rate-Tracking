from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import datetime, timedelta
import os
import re
from config import config
from models import db, User, BloodPressureReading
from models.user import bcrypt as user_bcrypt

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-string-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///heart_monitor.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
user_bcrypt.init_app(app)  # Initialize the bcrypt instance in user model
CORS(app)
migrate = Migrate(app, db)

# Utility functions
def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error', 'message': 'Something went wrong'}), 500

# Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }), 200

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            email=email,
            first_name=data.get('first_name', '').strip(),
            last_name=data.get('last_name', '').strip()
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'message': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        # Check credentials
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'message': str(e)}), 500

@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile', 'message': str(e)}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update current user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update profile
        user.update_profile(
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'message': str(e)}), 500

# Blood Pressure Reading Routes
@app.route('/api/readings', methods=['GET'])
@jwt_required()
def get_readings():
    """Get all readings for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        days = request.args.get('days', type=int)
        include_category_info = request.args.get('include_category_info', 'false').lower() == 'true'
        
        # Base query
        query = BloodPressureReading.query.filter_by(user_id=current_user_id)
        
        # Filter by days if specified
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(BloodPressureReading.timestamp >= cutoff_date)
        
        # Order by timestamp (newest first) and apply pagination
        readings = query.order_by(BloodPressureReading.timestamp.desc()).offset(offset).limit(limit).all()
        
        # Get total count
        total_count = query.count()
        
        return jsonify({
            'readings': [reading.to_dict(include_category_info=include_category_info) for reading in readings],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get readings', 'message': str(e)}), 500

@app.route('/api/readings', methods=['POST'])
@jwt_required()
def create_reading():
    """Create a new blood pressure reading"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['systolic', 'diastolic', 'pulse']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse timestamp if provided
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        # Create reading using class method (includes validation)
        reading = BloodPressureReading.create_reading(
            user_id=current_user_id,
            systolic=data['systolic'],
            diastolic=data['diastolic'],
            pulse=data['pulse'],
            notes=data.get('notes', ''),
            timestamp=timestamp
        )
        
        db.session.add(reading)
        db.session.commit()
        
        return jsonify({
            'message': 'Reading created successfully',
            'reading': reading.to_dict(include_category_info=True)
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid data', 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create reading', 'message': str(e)}), 500

@app.route('/api/readings/<int:reading_id>', methods=['GET'])
@jwt_required()
def get_reading(reading_id):
    """Get a specific reading"""
    try:
        current_user_id = get_jwt_identity()
        include_category_info = request.args.get('include_category_info', 'false').lower() == 'true'
        
        reading = BloodPressureReading.query.filter_by(
            id=reading_id, 
            user_id=current_user_id
        ).first()
        
        if not reading:
            return jsonify({'error': 'Reading not found'}), 404
        
        return jsonify({
            'reading': reading.to_dict(include_category_info=include_category_info)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reading', 'message': str(e)}), 500

@app.route('/api/readings/<int:reading_id>', methods=['PUT'])
@jwt_required()
def update_reading(reading_id):
    """Update a specific reading"""
    try:
        current_user_id = get_jwt_identity()
        
        reading = BloodPressureReading.query.filter_by(
            id=reading_id, 
            user_id=current_user_id
        ).first()
        
        if not reading:
            return jsonify({'error': 'Reading not found'}), 404
        
        data = request.get_json()
        
        # Parse timestamp if provided
        timestamp = None
        if 'timestamp' in data:
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        # Update reading using model method
        reading.update_reading(
            systolic=data.get('systolic'),
            diastolic=data.get('diastolic'),
            pulse=data.get('pulse'),
            notes=data.get('notes'),
            timestamp=timestamp
        )
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reading updated successfully',
            'reading': reading.to_dict(include_category_info=True)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid data', 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update reading', 'message': str(e)}), 500

@app.route('/api/readings/<int:reading_id>', methods=['DELETE'])
@jwt_required()
def delete_reading(reading_id):
    """Delete a specific reading"""
    try:
        current_user_id = get_jwt_identity()
        
        reading = BloodPressureReading.query.filter_by(
            id=reading_id, 
            user_id=current_user_id
        ).first()
        
        if not reading:
            return jsonify({'error': 'Reading not found'}), 404
        
        db.session.delete(reading)
        db.session.commit()
        
        return jsonify({
            'message': 'Reading deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete reading', 'message': str(e)}), 500

@app.route('/api/analytics/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    """Get analytics summary for the current user"""
    try:
        current_user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        readings = BloodPressureReading.query.filter(
            BloodPressureReading.user_id == current_user_id,
            BloodPressureReading.timestamp >= cutoff_date
        ).all()
        
        if not readings:
            return jsonify({
                'summary': {
                    'total_readings': 0,
                    'period_days': days,
                    'averages': {},
                    'category_distribution': {},
                    'trends': {},
                    'high_risk_readings': 0
                }
            }), 200
        
        # Calculate averages
        avg_systolic = sum(r.systolic for r in readings) / len(readings)
        avg_diastolic = sum(r.diastolic for r in readings) / len(readings)
        avg_pulse = sum(r.pulse for r in readings) / len(readings)
        
        # Category distribution
        category_dist = {}
        high_risk_count = 0
        for reading in readings:
            category_dist[reading.category] = category_dist.get(reading.category, 0) + 1
            if reading.is_high_risk():
                high_risk_count += 1
        
        # Trends (if we have at least 2 readings)
        if len(readings) >= 2:
            first_reading = readings[-1]  # Oldest
            last_reading = readings[0]   # Newest
            
            systolic_trend = last_reading.systolic - first_reading.systolic
            diastolic_trend = last_reading.diastolic - first_reading.diastolic
            pulse_trend = last_reading.pulse - first_reading.pulse
        else:
            systolic_trend = diastolic_trend = pulse_trend = 0
        
        return jsonify({
            'summary': {
                'total_readings': len(readings),
                'period_days': days,
                'averages': {
                    'systolic': round(avg_systolic, 1),
                    'diastolic': round(avg_diastolic, 1),
                    'pulse': round(avg_pulse, 1)
                },
                'category_distribution': category_dist,
                'trends': {
                    'systolic_change': systolic_trend,
                    'diastolic_change': diastolic_trend,
                    'pulse_change': pulse_trend
                },
                'high_risk_readings': high_risk_count
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get analytics', 'message': str(e)}), 500

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

if __name__ == '__main__':
    create_tables()
    
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)