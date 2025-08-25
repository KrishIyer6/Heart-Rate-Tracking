"""
Routes package initialization
"""

from .auth import auth_bp
from .readings import readings_bp
from .analytics import analytics_bp

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(readings_bp, url_prefix='/api/readings')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')