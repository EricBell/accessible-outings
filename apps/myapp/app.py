import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from config import get_config
from models import db, login_manager
from utils.google_places import GooglePlacesAPI, VenueSearchService
from utils.geocoding import GeocodingService, LocationService
from utils.accessibility import AccessibilityFilter

def _initialize_database(app):
    """Initialize database with sample data if needed."""
    from models.venue import VenueCategory
    from models.user import User
    from utils.database import is_sqlite
    
    # Check if we need to initialize data
    if VenueCategory.query.count() == 0:
        app.logger.info("Initializing database with sample data...")
        
        # Create venue categories
        categories = [
            ('Botanical Gardens', 'Gardens, conservatories, arboretums with indoor facilities', 'fas fa-leaf', 
             ["botanical garden", "conservatory", "arboretum", "greenhouse", "indoor garden"]),
            ('Bird Watching', 'Aviaries, bird sanctuaries, nature centers with indoor exhibits', 'fas fa-dove', 
             ["aviary", "bird sanctuary", "nature center", "wildlife center", "bird exhibit"]),
            ('Museums', 'Art, history, science, and specialty museums', 'fas fa-university', 
             ["museum", "art museum", "history museum", "science museum", "gallery"]),
            ('Aquariums', 'Aquariums and marine life centers', 'fas fa-fish', 
             ["aquarium", "marine center", "sea life center", "oceanarium"]),
            ('Shopping Centers', 'Malls, shopping centers, and retail complexes', 'fas fa-shopping-bag', 
             ["shopping mall", "shopping center", "retail center", "plaza"]),
            ('Antique Shops', 'Antique stores, vintage shops, and collectible stores', 'fas fa-gem', 
             ["antique store", "vintage shop", "collectibles", "consignment shop", "thrift store"]),
            ('Art Galleries', 'Art galleries and exhibition spaces', 'fas fa-palette', 
             ["art gallery", "exhibition space", "art center", "studio gallery"]),
            ('Libraries', 'Public libraries and cultural centers', 'fas fa-book', 
             ["library", "public library", "cultural center", "community center"]),
            ('Theaters', 'Movie theaters and performance venues', 'fas fa-theater-masks', 
             ["movie theater", "cinema", "theater", "performance venue", "playhouse"]),
            ('Craft Stores', 'Hobby and craft supply stores', 'fas fa-cut', 
             ["craft store", "hobby store", "art supply", "fabric store", "craft supplies"]),
            ('Garden Centers', 'Indoor garden centers and nurseries', 'fas fa-seedling', 
             ["garden center", "nursery", "plant store", "indoor plants"]),
            ('Conservatories', 'Glass houses and plant conservatories', 'fas fa-glass-whiskey', 
             ["conservatory", "glass house", "tropical house", "palm house"])
        ]
        
        for name, description, icon_class, search_keywords in categories:
            category = VenueCategory(
                name=name,
                description=description,
                icon_class=icon_class,
                search_keywords=search_keywords
            )
            db.session.add(category)
        
        # Create default user if using SQLite and bypass auth
        if is_sqlite() and app.config.get('BYPASS_AUTH'):
            if User.query.count() == 0:
                default_user = User.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='testpass123',
                    first_name='Test',
                    last_name='User',
                    home_zip_code='03301'
                )
                app.logger.info(f"Created default user: {default_user.username}")
        
        db.session.commit()
        app.logger.info("Database initialization completed.")

def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize services
    google_api = GooglePlacesAPI(app.config['GOOGLE_PLACES_API_KEY'])
    geocoding_service = GeocodingService(app.config['GOOGLE_PLACES_API_KEY'])
    
    # Store services in app context for access in routes
    app.google_api = google_api
    app.venue_search_service = VenueSearchService(google_api)
    app.location_service = LocationService(geocoding_service)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize database with sample data if needed
        _initialize_database(app)
        
        # Validate configuration
        config_errors = config_class.validate_config()
        if config_errors:
            for error in config_errors:
                app.logger.warning(f"Configuration warning: {error}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Template context processors
    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates."""
        return {
            'app_name': app.config.get('APP_NAME', 'Accessible Outings Finder'),
            'bypass_auth': app.config.get('BYPASS_AUTH', False)
        }
    
    @app.context_processor
    def inject_user_info():
        """Inject user information into templates."""
        if app.config.get('BYPASS_AUTH') and not current_user.is_authenticated:
            # Get default user for bypass mode
            from models.user import User
            default_user = db.session.get(User, app.config.get('DEFAULT_USER_ID', 1))
            return {'current_user': default_user}
        return {}
    
    # Template filters
    @app.template_filter('accessibility_score')
    def accessibility_score_filter(venue):
        """Template filter to get accessibility score."""
        return AccessibilityFilter.calculate_accessibility_score(venue)
    
    @app.template_filter('distance')
    def distance_filter(venue, latitude=None, longitude=None):
        """Template filter to calculate distance."""
        if latitude and longitude:
            distance = venue.distance_from(latitude, longitude)
            return f"{distance:.1f} miles" if distance else "Distance unknown"
        return ""
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
