"""
Blood pressure readings routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from models import BloodPressureReading, db
from utils import validate_bp_reading

readings_bp = Blueprint('readings', __name__)

@readings_bp.route('', methods=['GET'])
@jwt_required()
def get_readings():
    """Get all readings for the current user"""
    try:
        current_user_id = get_jwt_identity()
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        days = request.args.get('days', type=int)
        category = request.args.get('category', type=str)
        
        query = BloodPressureReading.query.filter_by(user_id=current_user_id)
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(BloodPressureReading.timestamp >= cutoff_date)
        
        if category:
            query = query.filter(BloodPressureReading.category == category)
        
        readings = query.order_by(BloodPressureReading.timestamp.desc()).offset(offset).limit(limit).all()
        
        total_count = query.count()
        
        return jsonify({
            'readings': [reading.to_dict() for reading in readings],
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': total_count > (offset + limit)
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get readings', 'message': str(e)}), 500

@readings_bp.route('', methods=['POST'])
@jwt_required()
def create_reading():
    """Create a new blood pressure reading"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['systolic', 'diastolic', 'pulse']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        systolic = int(data['systolic'])
        diastolic = int(data['diastolic'])
        pulse = int(data['pulse'])
        
        is_valid, errors = validate_bp_reading(systolic, diastolic, pulse)
        if not is_valid:
            return jsonify({'error': 'Invalid reading values', 'details': errors}), 400
        
        reading = BloodPressureReading(
            user_id=current_user_id,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            notes=data.get('notes', '').strip(),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.utcnow()
        )
        
        reading.category = reading.categorize_reading()
        
        db.session.add(reading)
        db.session.commit()
        
        return jsonify({
            'message': 'Reading created successfully',
            'reading': reading.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid data type', 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create reading', 'message': str(e)}), 500

@readings_bp.route('/<int:reading_id>', methods=['GET'])
@jwt_required()
def get_reading(reading_id):
    """Get a specific reading"""
    try:
        current_user_id = get_jwt_identity()
        
        reading = BloodPressureReading.query.filter_by(
            id=reading_id, 
            user_id=current_user_id
        ).first()
        
        if not reading:
            return jsonify({'error': 'Reading not found'}), 404
        
        return jsonify({
            'reading': reading.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get reading', 'message': str(e)}), 500

@readings_bp.route('/<int:reading_id>', methods=['PUT'])
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
        
        if 'systolic' in data:
            reading.systolic = int(data['systolic'])
        if 'diastolic' in data:
            reading.diastolic = int(data['diastolic'])
        if 'pulse' in data:
            reading.pulse = int(data['pulse'])
        if 'notes' in data:
            reading.notes = data['notes'].strip()
        if 'timestamp' in data:
            reading.timestamp = datetime.fromisoformat(data['timestamp'])
        
        is_valid, errors = validate_bp_reading(reading.systolic, reading.diastolic, reading.pulse)
        if not is_valid:
            return jsonify({'error': 'Invalid reading values', 'details': errors}), 400
        
        reading.category = reading.categorize_reading()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Reading updated successfully',
            'reading': reading.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': 'Invalid data type', 'message': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update reading', 'message': str(e)}), 500

@readings_bp.route('/<int:reading_id>', methods=['DELETE'])
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

@readings_bp.route('/bulk', methods=['POST'])
@jwt_required()
def create_bulk_readings():
    """Create multiple readings at once"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'readings' not in data or not isinstance(data['readings'], list):
            return jsonify({'error': 'readings field must be a list'}), 400
        
        if len(data['readings']) == 0:
            return jsonify({'error': 'At least one reading is required'}), 400
        
        if len(data['readings']) > 100:  
            return jsonify({'error': 'Maximum 100 readings per bulk operation'}), 400
        
        created_readings = []
        errors = []
        
        for i, reading_data in enumerate(data['readings']):
            try:
                required_fields = ['systolic', 'diastolic', 'pulse']
                for field in required_fields:
                    if field not in reading_data:
                        errors.append(f'Reading {i+1}: {field} is required')
                        continue
                
                systolic = int(reading_data['systolic'])
                diastolic = int(reading_data['diastolic'])
                pulse = int(reading_data['pulse'])
                
                is_valid, validation_errors = validate_bp_reading(systolic, diastolic, pulse)
                if not is_valid:
                    errors.extend([f'Reading {i+1}: {error}' for error in validation_errors])
                    continue
                
                reading = BloodPressureReading(
                    user_id=current_user_id,
                    systolic=systolic,
                    diastolic=diastolic,
                    pulse=pulse,
                    notes=reading_data.get('notes', '').strip(),
                    timestamp=datetime.fromisoformat(reading_data['timestamp']) if reading_data.get('timestamp') else datetime.utcnow()
                )
                reading.category = reading.categorize_reading()
                
                db.session.add(reading)
                created_readings.append(reading)
                
            except (ValueError, TypeError) as e:
                errors.append(f'Reading {i+1}: Invalid data type - {str(e)}')
        
        if errors and not created_readings:
            db.session.rollback()
            return jsonify({'error': 'All readings failed validation', 'details': errors}), 400
        
        db.session.commit()
        
        response = {
            'message': f'Successfully created {len(created_readings)} readings',
            'created_count': len(created_readings),
            'readings': [reading.to_dict() for reading in created_readings]
        }
        
        if errors:
            response['warnings'] = errors
            response['failed_count'] = len(errors)
        
        return jsonify(response), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create bulk readings', 'message': str(e)}), 500

@readings_bp.route('/export', methods=['GET'])
@jwt_required()
def export_readings():
    """Export readings as CSV"""
    try:
        current_user_id = get_jwt_identity()
        
        days = request.args.get('days', type=int)
        format_type = request.args.get('format', 'json').lower()
        
        query = BloodPressureReading.query.filter_by(user_id=current_user_id)
        
        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(BloodPressureReading.timestamp >= cutoff_date)
        
        readings = query.order_by(BloodPressureReading.timestamp.desc()).all()
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            writer.writerow(['Date', 'Time', 'Systolic', 'Diastolic', 'Pulse', 'Category', 'Notes'])
            
            for reading in readings:
                writer.writerow([
                    reading.timestamp.strftime('%Y-%m-%d'),
                    reading.timestamp.strftime('%H:%M:%S'),
                    reading.systolic,
                    reading.diastolic,
                    reading.pulse,
                    reading.category,
                    reading.notes or ''
                ])
            
            csv_data = output.getvalue()
            output.close()
            
            return jsonify({
                'format': 'csv',
                'data': csv_data,
                'filename': f'blood_pressure_readings_{datetime.now().strftime("%Y%m%d")}.csv'
            }), 200
        else:
            return jsonify({
                'format': 'json',
                'data': [reading.to_dict() for reading in readings],
                'total_count': len(readings)
            }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to export readings', 'message': str(e)}), 500