from datetime import datetime
from . import db

class BloodPressureReading(db.Model):
    """Blood pressure reading model for storing user health data"""
    __tablename__ = 'blood_pressure_readings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    systolic = db.Column(db.Integer, nullable=False)
    diastolic = db.Column(db.Integer, nullable=False)
    pulse = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    CATEGORY_NORMAL = 'Normal'
    CATEGORY_ELEVATED = 'Elevated'
    CATEGORY_STAGE_1 = 'Stage 1'
    CATEGORY_STAGE_2 = 'Stage 2'
    CATEGORY_CRISIS = 'Crisis'
    
    def categorize_reading(self):
        """
        Automatically categorize blood pressure reading based on AHA guidelines
        Returns the appropriate category string
        """
        if self.systolic >= 180 or self.diastolic >= 120:
            return self.CATEGORY_CRISIS
        elif self.systolic >= 140 or self.diastolic >= 90:
            return self.CATEGORY_STAGE_2
        elif self.systolic >= 130 or self.diastolic >= 80:
            return self.CATEGORY_STAGE_1
        elif self.systolic >= 120 and self.diastolic < 80:
            return self.CATEGORY_ELEVATED
        else:
            return self.CATEGORY_NORMAL
    
    def get_category_info(self):
        """
        Get detailed information about the current category
        Returns a dictionary with category details
        """
        category_info = {
            self.CATEGORY_NORMAL: {
                'name': 'Normal',
                'description': 'Less than 120/80 mmHg',
                'color': 'green',
                'recommendation': 'Maintain healthy lifestyle'
            },
            self.CATEGORY_ELEVATED: {
                'name': 'Elevated',
                'description': '120-129 systolic and less than 80 diastolic',
                'color': 'yellow',
                'recommendation': 'Focus on lifestyle changes'
            },
            self.CATEGORY_STAGE_1: {
                'name': 'High Blood Pressure Stage 1',
                'description': '130-139/80-89 mmHg',
                'color': 'orange',
                'recommendation': 'Lifestyle changes and possibly medication'
            },
            self.CATEGORY_STAGE_2: {
                'name': 'High Blood Pressure Stage 2',
                'description': '140/90 mmHg or higher',
                'color': 'red',
                'recommendation': 'Lifestyle changes and medication'
            },
            self.CATEGORY_CRISIS: {
                'name': 'Hypertensive Crisis',
                'description': 'Higher than 180/120 mmHg',
                'color': 'darkred',
                'recommendation': 'Seek immediate medical attention'
            }
        }
        return category_info.get(self.category, {})
    
    def is_high_risk(self):
        """Check if this reading indicates high risk (Stage 2 or Crisis)"""
        return self.category in [self.CATEGORY_STAGE_2, self.CATEGORY_CRISIS]
    
    def to_dict(self, include_category_info=False):
        """
        Convert reading to dictionary for JSON serialization
        Args:
            include_category_info (bool): Whether to include detailed category information
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'systolic': self.systolic,
            'diastolic': self.diastolic,
            'pulse': self.pulse,
            'category': self.category,
            'notes': self.notes,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_category_info:
            result['category_info'] = self.get_category_info()
        
        return result
    
    def update_reading(self, systolic=None, diastolic=None, pulse=None, notes=None, timestamp=None):
        """
        Update reading values and recalculate category
        """
        if systolic is not None:
            self.systolic = systolic
        if diastolic is not None:
            self.diastolic = diastolic
        if pulse is not None:
            self.pulse = pulse
        if notes is not None:
            self.notes = notes
        if timestamp is not None:
            self.timestamp = timestamp
        
        self.category = self.categorize_reading()
        self.updated_at = datetime.utcnow()
    
    @staticmethod
    def validate_reading_values(systolic, diastolic, pulse):
        """
        Validate blood pressure reading values
        Returns tuple (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(systolic, (int, float)) or not (60 <= systolic <= 300):
            errors.append("Systolic pressure must be between 60 and 300 mmHg")
        
        if not isinstance(diastolic, (int, float)) or not (30 <= diastolic <= 200):
            errors.append("Diastolic pressure must be between 30 and 200 mmHg")
        
        if not isinstance(pulse, (int, float)) or not (30 <= pulse <= 220):
            errors.append("Pulse rate must be between 30 and 220 BPM")
        
        if isinstance(systolic, (int, float)) and isinstance(diastolic, (int, float)):
            if systolic <= diastolic:
                errors.append("Systolic pressure must be higher than diastolic pressure")
        
        return len(errors) == 0, errors
    
    @classmethod
    def create_reading(cls, user_id, systolic, diastolic, pulse, notes=None, timestamp=None):
        """
        Class method to create a new reading with validation
        """
        is_valid, errors = cls.validate_reading_values(systolic, diastolic, pulse)
        if not is_valid:
            raise ValueError(f"Invalid reading values: {', '.join(errors)}")
        
        reading = cls(
            user_id=user_id,
            systolic=int(systolic),
            diastolic=int(diastolic),
            pulse=int(pulse),
            notes=notes.strip() if notes else None,
            timestamp=timestamp or datetime.utcnow()
        )
        
        reading.category = reading.categorize_reading()
        
        return reading
    
    def __repr__(self):
        return f'<BloodPressureReading {self.systolic}/{self.diastolic} ({self.category})>'