"""
Production-specific configuration settings.
"""

import os
from datetime import timedelta


class ProductionConfig:
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set in production")
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        raise ValueError("DATABASE_URL environment variable must be set in production")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', 10))
    SQLALCHEMY_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', 20))
    SQLALCHEMY_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', 3600))
    SQLALCHEMY_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', 20))
    
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '')
    CORS_ORIGINS = ALLOWED_ORIGINS.split(',') if ALLOWED_ORIGINS else []
    CORS_SUPPORTS_CREDENTIALS = True
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'
    
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'true').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '1000/hour')
    
    SESSION_COOKIE_SECURE = True  
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    FORCE_HTTPS = os.environ.get('FORCE_HTTPS', 'true').lower() == 'true'
    
    HEALTH_CHECK_PATH = '/api/health'
    
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    SENTRY_ENVIRONMENT = 'production'
    
    SWAGGER_UI_DOC_EXPANSION = 'none'
    RESTX_VALIDATE = True
    RESTX_MASK_SWAGGER = True
    
    APM_SERVICE_NAME = 'heart-monitor-api'
    APM_ENVIRONMENT = 'production'
    
    @staticmethod
    def init_app(app):
        """Initialize app with production-specific settings."""
        import logging
        from logging.handlers import RotatingFileHandler, SMTPHandler
        
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
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.addHandler(file_handler)
        
        if app.config.get('LOG_TO_STDOUT'):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            app.logger.addHandler(console_handler)
        
        if app.config.get('MAIL_SERVER'):
            auth = None
            if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            
            secure = None
            if app.config.get('MAIL_USE_TLS'):
                secure = ()
            
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@example.com'),
                toaddrs=[os.environ.get('ADMIN_EMAIL', 'admin@example.com')],
                subject='Heart Monitor API Error',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
        
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        app.logger.info('Heart Monitor API startup - Production mode')
        
        if app.config.get('SENTRY_DSN'):
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                
                sentry_sdk.init(
                    dsn=app.config['SENTRY_DSN'],
                    integrations=[
                        FlaskIntegration(),
                        SqlalchemyIntegration(),
                    ],
                    traces_sample_rate=0.1,
                    environment=app.config['SENTRY_ENVIRONMENT']
                )
                app.logger.info('Sentry error tracking initialized')
            except ImportError:
                app.logger.warning('Sentry SDK not available, error tracking disabled')
        
        @app.after_request
        def add_security_headers(response):
            """Add security headers to all responses."""
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            return response
        
        if app.config.get('FORCE_HTTPS'):
            @app.before_request
            def force_https():
                if not request.is_secure and app.env != 'development':
                    return redirect(request.url.replace('http://', 'https://'))
        
        app.logger.info('Production security measures initialized')