"""Main Flask application for VTA JEE."""

import os
import logging
from pathlib import Path
from flask import Flask, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from config import get_config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Create upload directory
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(exist_ok=True)
    
    # Register blueprints
    from api import query_bp, auth_bp, feedback_bp
    app.register_blueprint(query_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(feedback_bp, url_prefix='/api')
    
    # Root route
    @app.route('/')
    def index():
        """Render the main application page."""
        return render_template('index.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return {'status': 'healthy', 'service': 'VTA JEE'}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {error}")
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        """Handle file too large errors."""
        return {'error': 'File too large. Maximum size is 16MB'}, 413
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Create database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=7415,
        debug=app.config['DEBUG']
    )
