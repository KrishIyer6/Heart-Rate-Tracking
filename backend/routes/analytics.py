"""
Analytics routes
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, desc, asc
from models import BloodPressureReading, db

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/summary', methods=['GET'])
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
        ).order_by(BloodPressureReading.timestamp.asc()).all()
        
        if not readings:
            return jsonify({
                'summary': {
                    'total_readings': 0,
                    'period_days': days,
                    'averages': {},
                    'category_distribution': {},
                    'trends': {},
                    'ranges': {}
                }
            }), 200
        
        avg_systolic = sum(r.systolic for r in readings) / len(readings)
        avg_diastolic = sum(r.diastolic for r in readings) / len(readings)
        avg_pulse = sum(r.pulse for r in readings) / len(readings)
        
        systolic_values = [r.systolic for r in readings]
        diastolic_values = [r.diastolic for r in readings]
        pulse_values = [r.pulse for r in readings]
        
        ranges = {
            'systolic': {'min': min(systolic_values), 'max': max(systolic_values)},
            'diastolic': {'min': min(diastolic_values), 'max': max(diastolic_values)},
            'pulse': {'min': min(pulse_values), 'max': max(pulse_values)}
        }
        
        category_dist = {}
        for reading in readings:
            category_dist[reading.category] = category_dist.get(reading.category, 0) + 1
        
        trends = {}
        if len(readings) >= 4:
            mid_point = len(readings) // 2
            first_half = readings[:mid_point]
            second_half = readings[mid_point:]
            
            first_avg_sys = sum(r.systolic for r in first_half) / len(first_half)
            second_avg_sys = sum(r.systolic for r in second_half) / len(second_half)
            
            first_avg_dia = sum(r.diastolic for r in first_half) / len(first_half)
            second_avg_dia = sum(r.diastolic for r in second_half) / len(second_half)
            
            first_avg_pulse = sum(r.pulse for r in first_half) / len(first_half)
            second_avg_pulse = sum(r.pulse for r in second_half) / len(second_half)
            
            trends = {
                'systolic_change': round(second_avg_sys - first_avg_sys, 1),
                'diastolic_change': round(second_avg_dia - first_avg_dia, 1),
                'pulse_change': round(second_avg_pulse - first_avg_pulse, 1)
            }
        else:
            trends = {
                'systolic_change': 0,
                'diastolic_change': 0,
                'pulse_change': 0
            }
        
        return jsonify({
            'summary': {
                'total_readings': len(readings),
                'period_days': days,
                'averages': {
                    'systolic': round(avg_systolic, 1),
                    'diastolic': round(avg_diastolic, 1),
                    'pulse': round(avg_pulse, 1)
                },
                'ranges': ranges,
                'category_distribution': category_dist,
                'trends': trends
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get analytics', 'message': str(e)}), 500

@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """Get detailed trend data for charts"""
    try:
        current_user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        group_by = request.args.get('group_by', 'day')  # day, week, month
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        readings = BloodPressureReading.query.filter(
            BloodPressureReading.user_id == current_user_id,
            BloodPressureReading.timestamp >= cutoff_date
        ).order_by(BloodPressureReading.timestamp.asc()).all()
        
        if not readings:
            return jsonify({
                'trends': [],
                'group_by': group_by,
                'period_days': days
            }), 200
        
        grouped_data = {}
        
        for reading in readings:
            if group_by == 'day':
                key = reading.timestamp.strftime('%Y-%m-%d')
            elif group_by == 'week':
                monday = reading.timestamp - timedelta(days=reading.timestamp.weekday())
                key = monday.strftime('%Y-%m-%d')
            elif group_by == 'month':
                key = reading.timestamp.strftime('%Y-%m')
            else:
                key = reading.timestamp.strftime('%Y-%m-%d')
            
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(reading)
        
        trend_data = []
        for period, period_readings in sorted(grouped_data.items()):
            avg_systolic = sum(r.systolic for r in period_readings) / len(period_readings)
            avg_diastolic = sum(r.diastolic for r in period_readings) / len(period_readings)
            avg_pulse = sum(r.pulse for r in period_readings) / len(period_readings)
            
            trend_data.append({
                'period': period,
                'count': len(period_readings),
                'averages': {
                    'systolic': round(avg_systolic, 1),
                    'diastolic': round(avg_diastolic, 1),
                    'pulse': round(avg_pulse, 1)
                }
            })
        
        return jsonify({
            'trends': trend_data,
            'group_by': group_by,
            'period_days': days
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get trends', 'message': str(e)}), 500

@analytics_bp.route('/patterns', methods=['GET'])
@jwt_required()
def get_patterns():
    """Analyze patterns in blood pressure readings"""
    try:
        current_user_id = get_jwt_identity()
        days = request.args.get('days', 90, type=int)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        readings = BloodPressureReading.query.filter(
            BloodPressureReading.user_id == current_user_id,
            BloodPressureReading.timestamp >= cutoff_date
        ).order_by(BloodPressureReading.timestamp.asc()).all()
        
        if len(readings) < 7:  
            return jsonify({
                'patterns': {
                    'insufficient_data': True,
                    'message': 'Need at least 7 readings for pattern analysis'
                }
            }), 200
        
        day_patterns = {}
        for reading in readings:
            day_name = reading.timestamp.strftime('%A')
            if day_name not in day_patterns:
                day_patterns[day_name] = []
            day_patterns[day_name].append(reading)
        
        day_averages = {}
        for day, day_readings in day_patterns.items():
            if day_readings:
                day_averages[day] = {
                    'systolic': round(sum(r.systolic for r in day_readings) / len(day_readings), 1),
                    'diastolic': round(sum(r.diastolic for r in day_readings) / len(day_readings), 1),
                    'pulse': round(sum(r.pulse for r in day_readings) / len(day_readings), 1),
                    'count': len(day_readings)
                }
        
        time_patterns = {}
        for reading in readings:
            hour = reading.timestamp.hour
            time_period = 'Morning' if 5 <= hour < 12 else 'Afternoon' if 12 <= hour < 17 else 'Evening' if 17 <= hour < 22 else 'Night'
            
            if time_period not in time_patterns:
                time_patterns[time_period] = []
            time_patterns[time_period].append(reading)
        
        time_averages = {}
        for time_period, time_readings in time_patterns.items():
            if time_readings:
                time_averages[time_period] = {
                    'systolic': round(sum(r.systolic for r in time_readings) / len(time_readings), 1),
                    'diastolic': round(sum(r.diastolic for r in time_readings) / len(time_readings), 1),
                    'pulse': round(sum(r.pulse for r in time_readings) / len(time_readings), 1),
                    'count': len(time_readings)
                }
        
        insights = []
        
        if day_averages:
            best_day = min(day_averages.keys(), key=lambda x: day_averages[x]['systolic'])
            worst_day = max(day_averages.keys(), key=lambda x: day_averages[x]['systolic'])
            
            insights.append({
                'type': 'day_of_week',
                'message': f'Lowest average systolic on {best_day} ({day_averages[best_day]["systolic"]} mmHg), highest on {worst_day} ({day_averages[worst_day]["systolic"]} mmHg)'
            })
        
        if time_averages:
            best_time = min(time_averages.keys(), key=lambda x: time_averages[x]['systolic'])
            worst_time = max(time_averages.keys(), key=lambda x: time_averages[x]['systolic'])
            
            insights.append({
                'type': 'time_of_day',
                'message': f'Lowest average systolic in {best_time} ({time_averages[best_time]["systolic"]} mmHg), highest in {worst_time} ({time_averages[worst_time]["systolic"]} mmHg)'
            })
        
        return jsonify({
            'patterns': {
                'day_of_week': day_averages,
                'time_of_day': time_averages,
                'insights': insights,
                'analysis_period_days': days,
                'total_readings_analyzed': len(readings)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get patterns', 'message': str(e)}), 500

@analytics_bp.route('/goals', methods=['GET'])
@jwt_required()
def get_goal_progress():
    """Get progress towards blood pressure goals"""
    try:
        current_user_id = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        target_systolic = request.args.get('target_systolic', 120, type=int)
        target_diastolic = request.args.get('target_diastolic', 80, type=int)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        readings = BloodPressureReading.query.filter(
            BloodPressureReading.user_id == current_user_id,
            BloodPressureReading.timestamp >= cutoff_date
        ).order_by(BloodPressureReading.timestamp.asc()).all()
        
        if not readings:
            return jsonify({
                'goal_progress': {
                    'no_data': True,
                    'message': 'No readings found for the specified period'
                }
            }), 200
        
        current_avg_systolic = sum(r.systolic for r in readings) / len(readings)
        current_avg_diastolic = sum(r.diastolic for r in readings) / len(readings)
        
        within_target = sum(1 for r in readings if r.systolic <= target_systolic and r.diastolic <= target_diastolic)
        percentage_within_target = (within_target / len(readings)) * 100
        
        systolic_improvement_needed = max(0, current_avg_systolic - target_systolic)
        diastolic_improvement_needed = max(0, current_avg_diastolic - target_diastolic)
        
        progress_trend = 'stable'
        if len(readings) >= 14:
            first_week_readings = [r for r in readings if r.timestamp <= readings[0].timestamp + timedelta(days=7)]
            last_week_readings = readings[-min(7, len(readings)):]
            
            first_week_avg = sum(r.systolic for r in first_week_readings) / len(first_week_readings)
            last_week_avg = sum(r.systolic for r in last_week_readings) / len(last_week_readings)
            
            if last_week_avg < first_week_avg - 2:
                progress_trend = 'improving'
            elif last_week_avg > first_week_avg + 2:
                progress_trend = 'worsening'
        
        return jsonify({
            'goal_progress': {
                'targets': {
                    'systolic': target_systolic,
                    'diastolic': target_diastolic
                },
                'current_averages': {
                    'systolic': round(current_avg_systolic, 1),
                    'diastolic': round(current_avg_diastolic, 1)
                },
                'improvement_needed': {
                    'systolic': round(systolic_improvement_needed, 1),
                    'diastolic': round(diastolic_improvement_needed, 1)
                },
                'within_target_percentage': round(percentage_within_target, 1),
                'readings_within_target': within_target,
                'total_readings': len(readings),
                'progress_trend': progress_trend,
                'period_days': days
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get goal progress', 'message': str(e)}), 500

@analytics_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_detailed_statistics():
    """Get detailed statistical analysis"""
    try:
        current_user_id = get_jwt_identity()
        days = request.args.get('days', 90, type=int)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        readings = BloodPressureReading.query.filter(
            BloodPressureReading.user_id == current_user_id,
            BloodPressureReading.timestamp >= cutoff_date
        ).order_by(BloodPressureReading.timestamp.asc()).all()
        
        if not readings:
            return jsonify({
                'statistics': {
                    'no_data': True,
                    'message': 'No readings found for the specified period'
                }
            }), 200
        
        systolic_values = [r.systolic for r in readings]
        diastolic_values = [r.diastolic for r in readings]
        pulse_values = [r.pulse for r in readings]
        
        def calculate_stats(values):
            """Calculate comprehensive statistics for a list of values"""
            values_sorted = sorted(values)
            n = len(values)
            mean = sum(values) / n
            
            def percentile(data, p):
                index = (p / 100) * (len(data) - 1)
                if index.is_integer():
                    return data[int(index)]
                else:
                    lower = data[int(index)]
                    upper = data[int(index) + 1]
                    return lower + (upper - lower) * (index - int(index))
            
            variance = sum((x - mean) ** 2 for x in values) / n
            std_dev = variance ** 0.5
            
            return {
                'mean': round(mean, 1),
                'median': round(percentile(values_sorted, 50), 1),
                'min': min(values),
                'max': max(values),
                'std_dev': round(std_dev, 1),
                'percentiles': {
                    '25th': round(percentile(values_sorted, 25), 1),
                    '75th': round(percentile(values_sorted, 75), 1),
                    '90th': round(percentile(values_sorted, 90), 1),
                    '95th': round(percentile(values_sorted, 95), 1)
                }
            }
        
        def calculate_correlation(x_values, y_values):
            """Calculate Pearson correlation coefficient"""
            n = len(x_values)
            if n < 2:
                return 0
            
            mean_x = sum(x_values) / n
            mean_y = sum(y_values) / n
            
            numerator = sum((x_values[i] - mean_x) * (y_values[i] - mean_y) for i in range(n))
            sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
            sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
            
            denominator = (sum_sq_x * sum_sq_y) ** 0.5
            
            if denominator == 0:
                return 0
            
            return numerator / denominator
        
        correlation_sys_dia = calculate_correlation(systolic_values, diastolic_values)
        
        return jsonify({
            'statistics': {
                'systolic': calculate_stats(systolic_values),
                'diastolic': calculate_stats(diastolic_values),
                'pulse': calculate_stats(pulse_values),
                'correlations': {
                    'systolic_diastolic': round(correlation_sys_dia, 3)
                },
                'total_readings': len(readings),
                'period_days': days,
                'reading_frequency': {
                    'readings_per_day': round(len(readings) / days, 1),
                    'days_with_readings': len(set(r.timestamp.date() for r in readings))
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get statistics', 'message': str(e)}), 500