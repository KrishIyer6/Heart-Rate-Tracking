"""
Utility functions
"""

import re

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

def validate_bp_reading(systolic, diastolic, pulse):
    """Validate blood pressure reading values"""
    from models import BloodPressureReading
    return BloodPressureReading.validate_values(systolic, diastolic, pulse)

def format_error_response(error_type, message, details=None, status_code=400):
    """Format standardized error response"""
    response = {
        'error': error_type,
        'message': message
    }
    if details:
        response['details'] = details
    
    return response, status_code

def format_success_response(message, data=None, status_code=200):
    """Format standardized success response"""
    response = {
        'message': message
    }
    if data:
        response.update(data)
    
    return response, status_code