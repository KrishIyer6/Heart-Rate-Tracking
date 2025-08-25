"""
Development-specific configuration settings.
"""

import os
from datetime import timedelta


class DevelopmentConfig:
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-development-only'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-secret-key-change-me'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///heart_monitor_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  
    SQLALCHEMY_RECORD_QUERIES = True
    
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:3001',
        'http://127.0.0.1:3001',
        'http://localhost:8080',
        'http://127.0.0.1:8080'
    ]
    CORS_SUPPORTS_CREDENTIALS = True
    
    LOG_LEVEL = 'DEBUG'
    LOG_TO_STDOUT = True
    
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    DEFAULT_PAGE_SIZE = 20  # Smaller for easier testing
    MAX_PAGE_SIZE = 50
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@heartmonitor.dev')
    
    CACHE_TYPE = 'simple'  # Use 'redis' if Redis is available
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    
    FLASK_PROFILER_ENABLED = os.environ.get('FLASK_PROFILER', 'false').lower() == 'true'
    SQLALCHEMY_ECHO_POOL = False
    SQLALCHEMY_POOL_RECYCLE = 300
    
    SWAGGER_UI_DOC_EXPANSION = 'full'
    RESTX_VALIDATE = True
    RESTX_MASK_SWAGGER = False
    
    @staticmethod
    def init_app(app):
        """Initialize app with development-specific settings."""
        import logging
        
        if not app.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            )
            console_handler.setFormatter(formatter)
            app.logger.addHandler(console_handler)
            app.logger.setLevel(logging.DEBUG)
        
        app.logger.info('Starting Heart Monitor API in DEVELOPMENT mode')
        app.logger.info(f'Database URI: {app.config["SQLALCHEMY_DATABASE_URI"]}')
        app.logger.info(f'Debug mode: {app.config["DEBUG"]}')
        
        if app.config.get('SQLALCHEMY_ECHO'):
            logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        
        try:
            if app.config.get('FLASK_PROFILER_ENABLED'):
                from flask_profiler import Profiler
                app.config['flask_profiler'] = {
                    'enabled': True,
                    'storage': {
                        'engine': 'sqlite'
                    },
                    'basicAuth': {
                        'enabled': True,
                        'username': 'admin',
                        'password': 'admin'
                    },
                    'ignore': ['^/static/.*']
                }
                Profiler(app)
                app.logger.info('Flask Profiler enabled at /_profiler')
        except ImportError:
            app.logger.warning('Flask Profiler not available')