from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
 
# Load environment variables from .env file
load_dotenv()
 
# Initialize Flask application
app = Flask(__name__)
 
# ===== Configuration =====
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///app.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
# ===== Security Configuration =====
# Enable these in production (requires HTTPS)
ENVIRONMENT = os.getenv('FLASK_ENV', 'development')
if ENVIRONMENT == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
else:
    # Development settings
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
 
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
 
# ===== Database Initialization =====
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)
 
# ===== CORS Configuration =====
# Enable Cross-Origin Resource Sharing for frontend integration
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
CORS(app, 
     resources={
         r"/*": {
             "origins": cors_origins,
             "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type"],
             "supports_credentials": True,
             "max_age": 3600
         }
     })
 
# ===== Rate Limiting Configuration =====
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv('REDIS_URL', None)  # Use Redis for distributed rate limiting
)
 
# ===== Logging Configuration =====
def setup_logging():
    """Configure application logging to file and console."""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Set logging level
    log_level = logging.INFO if ENVIRONMENT == 'production' else logging.DEBUG
    
    # Add handlers to app logger
    if not app.logger.hasHandlers():
        app.logger.setLevel(log_level)
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
    
    return app.logger
 
logger = setup_logging()
 
# ===== Security Headers Middleware =====
@app.after_request
def set_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
 
# ===== Error Handlers =====
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded: {e.description}")
    return {
        'errors': ['Too many requests. Please try again later.']
    }, 429
 
@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(e)}")
    db.session.rollback()
    return {
        'errors': ['Internal server error. Please try again later.']
    }, 500
 
@app.errorhandler(404)
def not_found(e):
    """Handle not found errors."""
    return {
        'errors': ['Resource not found.']
    }, 404
 
if __name__ == '__main__':
    logger.info(f"Starting application in {ENVIRONMENT} mode")
 






