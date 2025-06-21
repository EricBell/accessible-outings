import logging
from typing import List, Dict, Optional
from models.venue import Venue
from models.review import UserReview

logger = logging.getLogger(__name__)

class AccessibilityFilter:
    """Service for filtering and scoring venues based on accessibility features."""
    
    # Accessibility feature weights for scoring
    FEATURE_WEIGHTS = {
        'wheelchair_accessible': 0.25,
        'accessible_parking': 0.15,
        'accessible_restroom': 0.20,
        'elevator_access': 0.10,
        'wide_doorways': 0.10,
        'ramp_access': 0.10,
        'accessible_seating': 0.10
    }
    
    # Keywords that indicate accessibility in reviews
    ACCESSIBILITY_KEYWORDS = {
        'positive': [
            'wheelchair accessible', 'wheelchair friendly', 'accessible entrance',
            'ramp available', 'elevator access', 'wide doors', 'accessible parking',
            'accessible restroom', 'accessible bathroom', 'easy access',
            'handicap accessible', 'disability friendly', 'accessible seating',
            'smooth entrance', 'no steps', 'level entrance', 'accessible path'
        ],
        'negative': [
            'not accessible', 'no wheelchair access', 'stairs only', 'narrow doors',
            'no ramp', 'no elevator', 'inaccessible', 'difficult access',
            'steps required', 'not handicap accessible', 'narrow entrance',
            'no accessible parking', 'no accessible restroom'
        ]
    }
    
    @classmethod
    def calculate_accessibility_score(cls, venue: Venue) -> float:
        """Calculate a comprehensive accessibility score for a venue."""
        score = 0.0
        
        # Base score from venue features
        for feature, weight in cls.FEATURE_WEIGHTS.items():
            if hasattr(venue, feature) and getattr(venue, feature):
                score += weight
        
        # Bonus for verified accessibility
        if venue.verified_accessible:
            score += 0.1
        
        # Factor in user reviews
        review_score = cls._calculate_review_accessibility_score(venue)
        if review_score is not None:
            # Weight user reviews at 30% of total score
            score = (score * 0.7) + (review_score * 0.3)
        
        return min(score, 1.0)  # Cap at 1.0
    
    @classmethod
    def _calculate_review_accessibility_score(cls, venue: Venue) -> Optional[float]:
        """Calculate accessibility score based on user reviews."""
        reviews = venue.reviews.all()
        if not reviews:
            return None
        
        # Get explicit accessibility ratings
        accessibility_ratings = [
            review.accessibility_rating for review in reviews 
            if review.accessibility_rating is not None
        ]
        
        if accessibility_ratings:
            # Convert 1-5 scale to 0-1 scale
            avg_rating = sum(accessibility_ratings) / len(accessibility_ratings)
            return (avg_rating - 1) / 4  # Convert 1-5 to 0-1
        
        # Analyze review text for accessibility mentions
        positive_mentions = 0
        negative_mentions = 0
        total_reviews = 0
        
        for review in reviews:
            if not review.review_text:
                continue
            
            total_reviews += 1
            review_text = review.review_text.lower()
            
            # Count positive accessibility mentions
            for keyword in cls.ACCESSIBILITY_KEYWORDS['positive']:
                if keyword in review_text:
                    positive_mentions += 1
                    break  # Only count once per review
            
            # Count negative accessibility mentions
            for keyword in cls.ACCESSIBILITY_KEYWORDS['negative']:
                if keyword in review_text:
                    negative_mentions += 1
                    break  # Only count once per review
        
        if total_reviews == 0:
            return None
        
        # Calculate score based on mention ratio
        if positive_mentions + negative_mentions == 0:
            return None  # No accessibility mentions
        
        positive_ratio = positive_mentions / (positive_mentions + negative_mentions)
        return positive_ratio
    
    @classmethod
    def filter_accessible_venues(cls, venues: List[Venue], 
                                min_score: float = 0.3) -> List[Venue]:
        """Filter venues to only include those meeting accessibility criteria."""
        accessible_venues = []
        
        for venue in venues:
            score = cls.calculate_accessibility_score(venue)
            if score >= min_score:
                accessible_venues.append(venue)
        
        return accessible_venues
    
    @classmethod
    def sort_by_accessibility(cls, venues: List[Venue], 
                            reverse: bool = True) -> List[Venue]:
        """Sort venues by accessibility score."""
        return sorted(venues, 
                     key=lambda v: cls.calculate_accessibility_score(v), 
                     reverse=reverse)
    
    @classmethod
    def get_accessibility_summary(cls, venue: Venue) -> Dict:
        """Get a comprehensive accessibility summary for a venue."""
        score = cls.calculate_accessibility_score(venue)
        features = venue.accessibility_features_list
        
        # Get user feedback
        reviews = venue.reviews.all()
        user_ratings = [r.accessibility_rating for r in reviews if r.accessibility_rating]
        recommended_count = sum(1 for r in reviews if r.recommended_for_wheelchair)
        
        # Categorize accessibility level
        if score >= 0.8:
            level = "Excellent"
            level_class = "success"
        elif score >= 0.6:
            level = "Good"
            level_class = "info"
        elif score >= 0.4:
            level = "Fair"
            level_class = "warning"
        else:
            level = "Limited"
            level_class = "danger"
        
        return {
            'score': round(score * 100, 1),
            'level': level,
            'level_class': level_class,
            'features': features,
            'feature_count': len(features),
            'verified': venue.verified_accessible,
            'user_rating_avg': round(sum(user_ratings) / len(user_ratings), 1) if user_ratings else None,
            'user_rating_count': len(user_ratings),
            'recommended_count': recommended_count,
            'total_reviews': len(reviews),
            'notes': venue.accessibility_notes
        }

class AccessibilityRecommendations:
    """Service for providing accessibility recommendations and insights."""
    
    @classmethod
    def get_venue_recommendations(cls, venue: Venue) -> List[str]:
        """Get accessibility recommendations for a venue."""
        recommendations = []
        
        # Check for missing basic features
        if not venue.wheelchair_accessible:
            recommendations.append("Verify wheelchair accessibility at entrance")
        
        if not venue.accessible_parking:
            recommendations.append("Check for accessible parking spaces nearby")
        
        if not venue.accessible_restroom:
            recommendations.append("Inquire about accessible restroom facilities")
        
        if not venue.ramp_access and not venue.elevator_access:
            recommendations.append("Look for ramp or elevator access if there are steps")
        
        # Check user reviews for common issues
        reviews = venue.reviews.all()
        common_issues = cls._analyze_common_accessibility_issues(reviews)
        
        for issue in common_issues:
            recommendations.append(f"Note: Previous visitors mentioned {issue}")
        
        return recommendations
    
    @classmethod
    def _analyze_common_accessibility_issues(cls, reviews: List[UserReview]) -> List[str]:
        """Analyze reviews to identify common accessibility issues."""
        issues = []
        issue_keywords = {
            'parking difficulties': ['parking', 'far', 'difficult to find'],
            'entrance challenges': ['entrance', 'door', 'heavy', 'narrow'],
            'restroom concerns': ['restroom', 'bathroom', 'not accessible'],
            'navigation issues': ['crowded', 'narrow aisles', 'difficult to navigate']
        }
        
        for review in reviews:
            if not review.accessibility_notes and not review.review_text:
                continue
            
            text = (review.accessibility_notes or '') + ' ' + (review.review_text or '')
            text = text.lower()
            
            for issue_type, keywords in issue_keywords.items():
                if any(keyword in text for keyword in keywords):
                    if issue_type not in issues:
                        issues.append(issue_type)
        
        return issues
    
    @classmethod
    def get_category_accessibility_insights(cls, category_id: int) -> Dict:
        """Get accessibility insights for a venue category."""
        from models.venue import VenueCategory, Venue
        
        category = VenueCategory.query.get(category_id)
        if not category:
            return {}
        
        venues = category.venues.all()
        if not venues:
            return {'category': category.name, 'venue_count': 0}
        
        # Calculate category statistics
        total_venues = len(venues)
        accessible_venues = len([v for v in venues if v.wheelchair_accessible])
        avg_score = sum(AccessibilityFilter.calculate_accessibility_score(v) for v in venues) / total_venues
        
        # Calculate interestingness statistics
        interestingness_scores = [float(v.interestingness_score) for v in venues if v.interestingness_score]
        avg_interestingness = sum(interestingness_scores) / len(interestingness_scores) if interestingness_scores else 0.0
        high_interest_venues = len([s for s in interestingness_scores if s >= 6.0])
        
        # Get most common features
        feature_counts = {}
        for venue in venues:
            for feature in venue.accessibility_features_list:
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
        
        common_features = sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'category': category.name,
            'venue_count': total_venues,
            'accessible_count': accessible_venues,
            'accessibility_percentage': round((accessible_venues / total_venues) * 100, 1),
            'average_score': round(avg_score * 100, 1),
            'common_features': common_features,
            'average_interestingness': round(avg_interestingness, 1),
            'high_interest_count': high_interest_venues
        }
    
    @classmethod
    def suggest_similar_accessible_venues(cls, venue: Venue, limit: int = 5) -> List[Venue]:
        """Suggest similar accessible venues based on category and location."""
        if not venue.category_id or not venue.latitude or not venue.longitude:
            return []
        
        # Find venues in same category within reasonable distance
        similar_venues = Venue.query.filter(
            Venue.category_id == venue.category_id,
            Venue.id != venue.id,
            Venue.wheelchair_accessible == True
        ).all()
        
        # Filter by distance (within 50 miles)
        nearby_venues = []
        for similar_venue in similar_venues:
            if similar_venue.latitude and similar_venue.longitude:
                distance = venue.distance_from(
                    float(similar_venue.latitude), 
                    float(similar_venue.longitude)
                )
                if distance and distance <= 50:
                    nearby_venues.append(similar_venue)
        
        # Sort by accessibility score and distance
        scored_venues = []
        for similar_venue in nearby_venues:
            score = AccessibilityFilter.calculate_accessibility_score(similar_venue)
            distance = venue.distance_from(
                float(similar_venue.latitude), 
                float(similar_venue.longitude)
            )
            # Combined score: 70% accessibility, 30% proximity (inverted)
            combined_score = (score * 0.7) + ((50 - distance) / 50 * 0.3)
            scored_venues.append((similar_venue, combined_score))
        
        # Sort by combined score and return top results
        scored_venues.sort(key=lambda x: x[1], reverse=True)
        return [venue for venue, score in scored_venues[:limit]]

class AccessibilityValidator:
    """Service for validating and improving accessibility data."""
    
    @classmethod
    def validate_venue_accessibility(cls, venue: Venue) -> Dict:
        """Validate accessibility information for a venue."""
        validation = {
            'valid': True,
            'warnings': [],
            'suggestions': [],
            'completeness_score': 0.0
        }
        
        # Check for basic accessibility information
        required_fields = [
            'wheelchair_accessible', 'accessible_parking', 'accessible_restroom'
        ]
        
        completed_fields = 0
        total_fields = len(AccessibilityFilter.FEATURE_WEIGHTS)
        
        for field in AccessibilityFilter.FEATURE_WEIGHTS.keys():
            if hasattr(venue, field) and getattr(venue, field) is not None:
                completed_fields += 1
        
        validation['completeness_score'] = completed_fields / total_fields
        
        # Check for inconsistencies
        if venue.wheelchair_accessible and not venue.accessible_parking:
            validation['warnings'].append(
                "Venue is wheelchair accessible but no accessible parking information"
            )
        
        if venue.wheelchair_accessible and not venue.accessible_restroom:
            validation['warnings'].append(
                "Venue is wheelchair accessible but no accessible restroom information"
            )
        
        # Suggest improvements
        if validation['completeness_score'] < 0.5:
            validation['suggestions'].append(
                "Consider adding more detailed accessibility information"
            )
        
        if not venue.accessibility_notes:
            validation['suggestions'].append(
                "Add accessibility notes for more detailed information"
            )
        
        if not venue.verified_accessible and venue.wheelchair_accessible:
            validation['suggestions'].append(
                "Consider verifying accessibility information through site visit"
            )
        
        return validation
    
    @classmethod
    def suggest_accessibility_updates(cls, venue: Venue) -> List[str]:
        """Suggest updates to improve accessibility information."""
        suggestions = []
        
        # Check user reviews for accessibility information
        reviews = venue.reviews.all()
        accessibility_mentions = []
        
        for review in reviews:
            text = (review.review_text or '') + ' ' + (review.accessibility_notes or '')
            text = text.lower()
            
            for keyword in AccessibilityFilter.ACCESSIBILITY_KEYWORDS['positive']:
                if keyword in text:
                    accessibility_mentions.append(keyword)
        
        # Suggest updates based on review mentions
        if 'ramp' in ' '.join(accessibility_mentions) and not venue.ramp_access:
            suggestions.append("Consider updating ramp access information based on user reviews")
        
        if 'elevator' in ' '.join(accessibility_mentions) and not venue.elevator_access:
            suggestions.append("Consider updating elevator access information based on user reviews")
        
        if 'parking' in ' '.join(accessibility_mentions) and not venue.accessible_parking:
            suggestions.append("Consider updating accessible parking information based on user reviews")
        
        return suggestions
