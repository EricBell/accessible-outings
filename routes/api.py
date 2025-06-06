from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db
from models.venue import Venue, VenueCategory
from models.review import UserFavorite, UserReview, SearchHistory, ApiCache
from utils.accessibility import AccessibilityFilter, AccessibilityRecommendations

api_bp = Blueprint('api', __name__)

def get_current_user():
    """Get current user, handling bypass auth mode."""
    if current_app.config.get('BYPASS_AUTH') and not current_user.is_authenticated:
        from models.user import User
        return User.query.get(current_app.config.get('DEFAULT_USER_ID', 1))
    return current_user if current_user.is_authenticated else None

@api_bp.route('/search')
def api_search():
    """API endpoint for venue search."""
    zip_code = request.args.get('zip_code')
    category_id = request.args.get('category_id', type=int)
    radius = request.args.get('radius', 30, type=int)
    accessible_only = request.args.get('accessible_only', False, type=bool)
    limit = request.args.get('limit', 50, type=int)
    
    if not zip_code:
        return jsonify({'error': 'ZIP code is required'}), 400
    
    # Validate and get coordinates
    coordinates = current_app.location_service.get_search_coordinates(
        zip_code=zip_code,
        default_lat=current_app.config.get('DEFAULT_LATITUDE'),
        default_lon=current_app.config.get('DEFAULT_LONGITUDE')
    )
    
    if not coordinates:
        return jsonify({'error': 'Invalid ZIP code or unable to find location'}), 400
    
    latitude, longitude = coordinates
    
    try:
        # Search for venues
        venues = current_app.venue_search_service.search_venues(
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius,
            category_id=category_id,
            wheelchair_accessible_only=accessible_only
        )
        
        # Limit results
        venues = venues[:limit]
        
        # Convert to JSON
        venues_data = []
        for venue in venues:
            venue_data = venue.to_dict(latitude, longitude)
            venue_data['accessibility_score'] = AccessibilityFilter.calculate_accessibility_score(venue)
            venues_data.append(venue_data)
        
        # Log search for analytics
        user = get_current_user()
        if user:
            SearchHistory.log_search(
                user_id=user.id,
                search_zip=zip_code,
                search_radius=radius,
                category_filter=category_id,
                results_count=len(venues),
                accessibility_filter=accessible_only
            )
        
        return jsonify({
            'success': True,
            'venues': venues_data,
            'total_results': len(venues_data),
            'search_params': {
                'zip_code': zip_code,
                'category_id': category_id,
                'radius': radius,
                'accessible_only': accessible_only,
                'latitude': latitude,
                'longitude': longitude
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"API search error: {e}")
        return jsonify({'error': 'Search failed'}), 500

@api_bp.route('/venue/<int:venue_id>')
def api_venue_detail(venue_id):
    """API endpoint for venue details."""
    venue = current_app.venue_search_service.get_venue_details(venue_id)
    if not venue:
        return jsonify({'error': 'Venue not found'}), 404
    
    # Get accessibility summary
    accessibility_summary = AccessibilityFilter.get_accessibility_summary(venue)
    
    # Get recommendations
    recommendations = AccessibilityRecommendations.get_venue_recommendations(venue)
    
    # Get similar venues
    similar_venues = AccessibilityRecommendations.suggest_similar_accessible_venues(venue, 3)
    
    # Check if user has favorited this venue
    user = get_current_user()
    is_favorited = False
    user_review = None
    
    if user:
        is_favorited = user.is_venue_favorited(venue_id)
        user_review_obj = user.get_venue_review(venue_id)
        user_review = user_review_obj.to_dict() if user_review_obj else None
    
    # Get recent reviews
    recent_reviews = UserReview.get_venue_reviews(venue_id, 5)
    
    venue_data = venue.to_dict()
    venue_data.update({
        'accessibility_summary': accessibility_summary,
        'recommendations': recommendations,
        'similar_venues': [v.to_dict() for v in similar_venues],
        'is_favorited': is_favorited,
        'user_review': user_review,
        'recent_reviews': [r.to_dict() for r in recent_reviews]
    })
    
    return jsonify({
        'success': True,
        'venue': venue_data
    })

@api_bp.route('/categories')
def api_categories():
    """API endpoint for venue categories."""
    categories = VenueCategory.query.all()
    
    categories_data = []
    for category in categories:
        category_data = category.to_dict()
        insights = AccessibilityRecommendations.get_category_accessibility_insights(category.id)
        category_data['insights'] = insights
        categories_data.append(category_data)
    
    return jsonify({
        'success': True,
        'categories': categories_data
    })

@api_bp.route('/favorites', methods=['GET'])
@login_required
def api_favorites():
    """API endpoint for user favorites."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    favorites = UserFavorite.query.filter_by(user_id=user.id)\
                                 .order_by(UserFavorite.created_at.desc()).all()
    
    favorites_data = [favorite.to_dict() for favorite in favorites]
    
    return jsonify({
        'success': True,
        'favorites': favorites_data
    })

@api_bp.route('/favorites', methods=['POST'])
@login_required
def api_add_favorite():
    """API endpoint to add venue to favorites."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    venue_id = data.get('venue_id')
    notes = data.get('notes', '')
    rating = data.get('rating')
    
    if not venue_id:
        return jsonify({'error': 'Venue ID is required'}), 400
    
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({'error': 'Venue not found'}), 404
    
    try:
        favorite = UserFavorite.add_favorite(
            user_id=user.id,
            venue_id=venue_id,
            notes=notes,
            personal_accessibility_rating=rating
        )
        
        return jsonify({
            'success': True,
            'message': f'{venue.name} added to favorites!',
            'favorite': favorite.to_dict()
        })
        
    except Exception as e:
        current_app.logger.error(f"API add favorite error: {e}")
        return jsonify({'error': 'Failed to add favorite'}), 500

@api_bp.route('/favorites/<int:venue_id>', methods=['DELETE'])
@login_required
def api_remove_favorite(venue_id):
    """API endpoint to remove venue from favorites."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    try:
        success = UserFavorite.remove_favorite(user.id, venue_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Removed from favorites!'
            })
        else:
            return jsonify({'error': 'Favorite not found'}), 404
            
    except Exception as e:
        current_app.logger.error(f"API remove favorite error: {e}")
        return jsonify({'error': 'Failed to remove favorite'}), 500

@api_bp.route('/reviews', methods=['GET'])
@login_required
def api_reviews():
    """API endpoint for user reviews."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    reviews = UserReview.get_user_reviews(user.id)
    reviews_data = [review.to_dict() for review in reviews]
    
    return jsonify({
        'success': True,
        'reviews': reviews_data
    })

@api_bp.route('/reviews', methods=['POST'])
@login_required
def api_add_review():
    """API endpoint to add venue review."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    venue_id = data.get('venue_id')
    
    if not venue_id:
        return jsonify({'error': 'Venue ID is required'}), 400
    
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({'error': 'Venue not found'}), 404
    
    # Check for existing review
    existing_review = UserReview.query.filter_by(user_id=user.id, venue_id=venue_id).first()
    
    try:
        if existing_review:
            # Update existing review
            for key, value in data.items():
                if hasattr(existing_review, key) and key != 'venue_id':
                    setattr(existing_review, key, value)
            
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Review updated successfully!',
                'review': existing_review.to_dict()
            })
        else:
            # Create new review
            review = UserReview(user_id=user.id, venue_id=venue_id, **data)
            db.session.add(review)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Review added successfully!',
                'review': review.to_dict()
            })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API review error: {e}")
        return jsonify({'error': 'Failed to save review'}), 500

@api_bp.route('/geocode')
def api_geocode():
    """API endpoint for geocoding ZIP codes."""
    zip_code = request.args.get('zip_code')
    
    if not zip_code:
        return jsonify({'error': 'ZIP code is required'}), 400
    
    try:
        coordinates = current_app.location_service.get_search_coordinates(zip_code=zip_code)
        
        if coordinates:
            latitude, longitude = coordinates
            location_name = current_app.location_service.get_location_display_name(latitude, longitude)
            
            return jsonify({
                'success': True,
                'zip_code': zip_code,
                'latitude': latitude,
                'longitude': longitude,
                'location_name': location_name
            })
        else:
            return jsonify({'error': 'Invalid ZIP code or location not found'}), 400
            
    except Exception as e:
        current_app.logger.error(f"API geocode error: {e}")
        return jsonify({'error': 'Geocoding failed'}), 500

@api_bp.route('/accessibility-score/<int:venue_id>')
def api_accessibility_score(venue_id):
    """API endpoint for venue accessibility score."""
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({'error': 'Venue not found'}), 404
    
    accessibility_summary = AccessibilityFilter.get_accessibility_summary(venue)
    
    return jsonify({
        'success': True,
        'venue_id': venue_id,
        'accessibility_summary': accessibility_summary
    })

@api_bp.route('/search-history')
@login_required
def api_search_history():
    """API endpoint for user search history."""
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Authentication required'}), 401
    
    searches = user.get_recent_searches(20)
    searches_data = [search.to_dict() for search in searches]
    
    return jsonify({
        'success': True,
        'search_history': searches_data
    })

@api_bp.route('/popular-searches')
def api_popular_searches():
    """API endpoint for popular searches."""
    try:
        popular_searches = SearchHistory.get_popular_searches(days=30, limit=10)
        
        searches_data = []
        for search_zip, category_filter, search_count in popular_searches:
            category_name = None
            if category_filter:
                category = VenueCategory.query.get(category_filter)
                category_name = category.name if category else None
            
            searches_data.append({
                'zip_code': search_zip,
                'category_id': category_filter,
                'category_name': category_name,
                'search_count': search_count
            })
        
        return jsonify({
            'success': True,
            'popular_searches': searches_data
        })
        
    except Exception as e:
        current_app.logger.error(f"API popular searches error: {e}")
        return jsonify({'error': 'Failed to get popular searches'}), 500

@api_bp.route('/cache/clear', methods=['POST'])
def api_clear_cache():
    """API endpoint to clear API cache (admin only)."""
    # This would typically require admin authentication
    # For now, we'll allow it for development
    
    try:
        pattern = request.json.get('pattern', '') if request.json else ''
        
        if pattern:
            cleared_count = ApiCache.clear_cache_by_pattern(pattern)
            message = f'Cleared {cleared_count} cache entries matching pattern "{pattern}"'
        else:
            cleared_count = ApiCache.clean_expired_cache()
            message = f'Cleared {cleared_count} expired cache entries'
        
        return jsonify({
            'success': True,
            'message': message,
            'cleared_count': cleared_count
        })
        
    except Exception as e:
        current_app.logger.error(f"API cache clear error: {e}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@api_bp.route('/health')
def api_health():
    """API health check endpoint."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Test Google API key
        google_api_configured = bool(current_app.config.get('GOOGLE_PLACES_API_KEY'))
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'google_api': 'configured' if google_api_configured else 'not configured',
            'app_name': current_app.config.get('APP_NAME', 'Accessible Outings Finder')
        })
        
    except Exception as e:
        current_app.logger.error(f"Health check error: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500
