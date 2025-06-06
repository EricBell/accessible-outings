from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from models import db
from models.venue import Venue, VenueCategory
from models.review import UserFavorite, UserReview, SearchHistory
from utils.accessibility import AccessibilityFilter, AccessibilityRecommendations

main_bp = Blueprint('main', __name__)

def get_current_user():
    """Get current user, handling bypass auth mode."""
    if current_app.config.get('BYPASS_AUTH') and not current_user.is_authenticated:
        from models.user import User
        return User.query.get(current_app.config.get('DEFAULT_USER_ID', 1))
    return current_user if current_user.is_authenticated else None

@main_bp.route('/')
def index():
    """Home page with search form."""
    categories = VenueCategory.query.all()
    
    # Get user's home ZIP code if available
    user = get_current_user()
    default_zip = user.home_zip_code if user else None
    
    # Get recent searches for suggestions
    recent_searches = []
    if user:
        recent_searches = user.get_recent_searches(5)
    
    return render_template('index.html', 
                         categories=categories, 
                         default_zip=default_zip,
                         recent_searches=recent_searches)

@main_bp.route('/search')
def search():
    """Search for venues."""
    zip_code = request.args.get('zip_code')
    category_id = request.args.get('category_id', type=int)
    radius = request.args.get('radius', 30, type=int)
    accessible_only = request.args.get('accessible_only', False, type=bool)
    
    if not zip_code:
        flash('Please provide a ZIP code to search.', 'error')
        return redirect(url_for('main.index'))
    
    # Validate and get coordinates
    coordinates = current_app.location_service.get_search_coordinates(
        zip_code=zip_code,
        default_lat=current_app.config.get('DEFAULT_LATITUDE'),
        default_lon=current_app.config.get('DEFAULT_LONGITUDE')
    )
    
    if not coordinates:
        flash('Invalid ZIP code or unable to find location.', 'error')
        return redirect(url_for('main.index'))
    
    latitude, longitude = coordinates
    
    # Search for venues
    try:
        venues = current_app.venue_search_service.search_venues(
            latitude=latitude,
            longitude=longitude,
            radius_miles=radius,
            category_id=category_id,
            wheelchair_accessible_only=accessible_only
        )
        
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
        
        # Get category info
        category = VenueCategory.query.get(category_id) if category_id else None
        
        # Get location display name
        location_name = current_app.location_service.get_location_display_name(latitude, longitude)
        
        return render_template('search_results.html',
                             venues=venues,
                             search_params={
                                 'zip_code': zip_code,
                                 'category_id': category_id,
                                 'radius': radius,
                                 'accessible_only': accessible_only,
                                 'latitude': latitude,
                                 'longitude': longitude
                             },
                             category=category,
                             location_name=location_name,
                             total_results=len(venues))
        
    except Exception as e:
        current_app.logger.error(f"Search error: {e}")
        flash('Search failed. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/venue/<int:venue_id>')
def venue_detail(venue_id):
    """Venue detail page."""
    venue = current_app.venue_search_service.get_venue_details(venue_id)
    if not venue:
        flash('Venue not found.', 'error')
        return redirect(url_for('main.index'))
    
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
        user_review = user.get_venue_review(venue_id)
    
    # Get recent reviews
    recent_reviews = UserReview.get_venue_reviews(venue_id, 5)
    
    return render_template('venue_detail.html',
                         venue=venue,
                         accessibility_summary=accessibility_summary,
                         recommendations=recommendations,
                         similar_venues=similar_venues,
                         is_favorited=is_favorited,
                         user_review=user_review,
                         recent_reviews=recent_reviews)

@main_bp.route('/favorites')
@login_required
def favorites():
    """User favorites page."""
    user = get_current_user()
    if not user:
        flash('Please log in to view favorites.', 'error')
        return redirect(url_for('auth.login'))
    
    favorites = UserFavorite.query.filter_by(user_id=user.id)\
                                 .order_by(UserFavorite.created_at.desc()).all()
    
    return render_template('favorites.html', favorites=favorites)

@main_bp.route('/add-favorite', methods=['POST'])
@login_required
def add_favorite():
    """Add venue to favorites."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Please log in to add favorites.'})
    
    venue_id = request.json.get('venue_id')
    notes = request.json.get('notes', '')
    rating = request.json.get('rating')
    
    if not venue_id:
        return jsonify({'success': False, 'message': 'Venue ID is required.'})
    
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({'success': False, 'message': 'Venue not found.'})
    
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
            'favorite_id': favorite.id
        })
        
    except Exception as e:
        current_app.logger.error(f"Add favorite error: {e}")
        return jsonify({'success': False, 'message': 'Failed to add favorite.'})

@main_bp.route('/remove-favorite', methods=['POST'])
@login_required
def remove_favorite():
    """Remove venue from favorites."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'message': 'Please log in to remove favorites.'})
    
    venue_id = request.json.get('venue_id')
    
    if not venue_id:
        return jsonify({'success': False, 'message': 'Venue ID is required.'})
    
    try:
        success = UserFavorite.remove_favorite(user.id, venue_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Removed from favorites!'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Favorite not found.'
            })
            
    except Exception as e:
        current_app.logger.error(f"Remove favorite error: {e}")
        return jsonify({'success': False, 'message': 'Failed to remove favorite.'})

@main_bp.route('/add-review/<int:venue_id>', methods=['GET', 'POST'])
@login_required
def add_review(venue_id):
    """Add or edit venue review."""
    user = get_current_user()
    if not user:
        flash('Please log in to add reviews.', 'error')
        return redirect(url_for('auth.login'))
    
    venue = Venue.query.get(venue_id)
    if not venue:
        flash('Venue not found.', 'error')
        return redirect(url_for('main.index'))
    
    # Check for existing review
    existing_review = UserReview.query.filter_by(user_id=user.id, venue_id=venue_id).first()
    
    if request.method == 'POST':
        visit_date = request.form.get('visit_date')
        overall_rating = request.form.get('overall_rating', type=int)
        accessibility_rating = request.form.get('accessibility_rating', type=int)
        review_text = request.form.get('review_text')
        accessibility_notes = request.form.get('accessibility_notes')
        would_return = request.form.get('would_return') == 'on'
        recommended_for_wheelchair = request.form.get('recommended_for_wheelchair') == 'on'
        weather_conditions = request.form.get('weather_conditions')
        visit_duration_hours = request.form.get('visit_duration_hours', type=float)
        companion_count = request.form.get('companion_count', type=int)
        
        try:
            if existing_review:
                # Update existing review
                existing_review.visit_date = visit_date
                existing_review.overall_rating = overall_rating
                existing_review.accessibility_rating = accessibility_rating
                existing_review.review_text = review_text
                existing_review.accessibility_notes = accessibility_notes
                existing_review.would_return = would_return
                existing_review.recommended_for_wheelchair = recommended_for_wheelchair
                existing_review.weather_conditions = weather_conditions
                existing_review.visit_duration_hours = visit_duration_hours
                existing_review.companion_count = companion_count
                
                db.session.commit()
                flash('Review updated successfully!', 'success')
            else:
                # Create new review
                review = UserReview(
                    user_id=user.id,
                    venue_id=venue_id,
                    visit_date=visit_date,
                    overall_rating=overall_rating,
                    accessibility_rating=accessibility_rating,
                    review_text=review_text,
                    accessibility_notes=accessibility_notes,
                    would_return=would_return,
                    recommended_for_wheelchair=recommended_for_wheelchair,
                    weather_conditions=weather_conditions,
                    visit_duration_hours=visit_duration_hours,
                    companion_count=companion_count
                )
                
                db.session.add(review)
                db.session.commit()
                flash('Review added successfully!', 'success')
            
            return redirect(url_for('main.venue_detail', venue_id=venue_id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Review error: {e}")
            flash('Failed to save review. Please try again.', 'error')
    
    return render_template('add_review.html', venue=venue, existing_review=existing_review)

@main_bp.route('/reviews')
@login_required
def my_reviews():
    """User's reviews page."""
    user = get_current_user()
    if not user:
        flash('Please log in to view reviews.', 'error')
        return redirect(url_for('auth.login'))
    
    reviews = UserReview.get_user_reviews(user.id)
    
    return render_template('my_reviews.html', reviews=reviews)

@main_bp.route('/categories')
def categories():
    """Browse venues by category."""
    categories = VenueCategory.query.all()
    
    # Get category insights
    category_insights = {}
    for category in categories:
        insights = AccessibilityRecommendations.get_category_accessibility_insights(category.id)
        category_insights[category.id] = insights
    
    return render_template('categories.html', 
                         categories=categories,
                         category_insights=category_insights)

@main_bp.route('/category/<int:category_id>')
def category_venues(category_id):
    """View venues in a specific category."""
    category = VenueCategory.query.get(category_id)
    if not category:
        flash('Category not found.', 'error')
        return redirect(url_for('main.categories'))
    
    # Get venues in this category
    venues = category.venues.all()
    
    # Sort by accessibility score
    venues = AccessibilityFilter.sort_by_accessibility(venues)
    
    # Get category insights
    insights = AccessibilityRecommendations.get_category_accessibility_insights(category_id)
    
    return render_template('category_venues.html',
                         category=category,
                         venues=venues,
                         insights=insights)

@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@main_bp.route('/accessibility-guide')
def accessibility_guide():
    """Accessibility guide page."""
    return render_template('accessibility_guide.html')
