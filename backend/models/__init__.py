from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .reading import BloodPressureReading

__all__ = ['db', 'User', 'BloodPressureReading']