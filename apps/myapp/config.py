import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Default to SQLite if no DATABASE_URL provided
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///accessible_outings.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configure engine options based on database type
    if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_timeout': 20,
            'pool_recycle': -1,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
        }
    
    # Database type detection
    DATABASE_TYPE = 'sqlite' if SQLALCHEMY_DATABASE_URI.startswith('sqlite') else 'postgresql'
    
    # API Keys
    GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY')
    YELP_API_KEY = os.environ.get('YELP_API_KEY')
    
    # Application settings
    APP_NAME = os.environ.get('APP_NAME', 'Accessible Outings Finder')
    DEFAULT_SEARCH_RADIUS_MILES = int(os.environ.get('DEFAULT_SEARCH_RADIUS_MILES', 30))
    MAX_SEARCH_RADIUS_MILES = int(os.environ.get('MAX_SEARCH_RADIUS_MILES', 60))
    CACHE_TIMEOUT_HOURS = int(os.environ.get('CACHE_TIMEOUT_HOURS', 24))
    
    # Development settings
    BYPASS_AUTH = os.environ.get('BYPASS_AUTH', 'False').lower() == 'true'
    DEFAULT_USER_ID = int(os.environ.get('DEFAULT_USER_ID', 1))
    
    # Geocoding settings
    DEFAULT_LATITUDE = float(os.environ.get('DEFAULT_LATITUDE', 43.2081))
    DEFAULT_LONGITUDE = float(os.environ.get('DEFAULT_LONGITUDE', -71.5376))
    
    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'app.log')
    
    # WTF Forms settings
    WTF_CSRF_ENABLED = False  # Disabled for development
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    @staticmethod
    def validate_config():
        """Validate required configuration settings."""
        errors = []
        
        if not Config.DATABASE_URL:
            errors.append("DATABASE_URL is required")
            
        if not Config.GOOGLE_PLACES_API_KEY:
            errors.append("GOOGLE_PLACES_API_KEY is required for venue search")
            
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY should be changed from default value")
            
        return errors

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    @staticmethod
    def validate_config():
        """Additional validation for production."""
        errors = Config.validate_config()
        
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY must be changed for production")
            
        if not Config.DATABASE_URL or 'sqlite' in Config.DATABASE_URL:
            errors.append("Production requires PostgreSQL database")
            
        return errors

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    BYPASS_AUTH = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
