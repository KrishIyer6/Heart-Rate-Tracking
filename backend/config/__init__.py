"""
Configuration module for the Heart Monitor Flask application.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class with common settings."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    APP_NAME = 'Heart Monitor API'
    APP_VERSION = '1.0.0'
    
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    
    @staticmethod
    def init_app(app):
        """Initialize app with configuration-specific settings."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///heart_monitor_dev.db'
    
    LOG_LEVEL = 'DEBUG'
    
    CORS_ORIGINS = ['*']
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        import logging
        logging.basicConfig(level=logging.DEBUG)


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        'sqlite:///heart_monitor_prod.db'
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # Shorter token expiry
    
    LOG_LEVEL = 'INFO'
    
    CORS_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',') if os.environ.get('ALLOWED_ORIGINS') else []
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug and not app.testing:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            
            file_handler = RotatingFileHandler(
                'logs/heart_monitor.log', 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Heart Monitor API startup')


class TestingConfig(Config):
    """Testing configuration."""
    
    DEBUG = True
    TESTING = True
    
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    WTF_CSRF_ENABLED = False
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}