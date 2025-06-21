"""
Experience Tagging System for Venue Interestingness
==================================================

This module provides automated experience tagging based on venue characteristics,
Google Places data, and venue names to identify interesting, offbeat, and engaging experiences.
"""

from typing import List, Dict, Set
import re
from models.venue import Venue

class ExperienceTagger:
    """Automated experience tagging for venues based on various signals."""
    
    # Core experience tag categories
    EXPERIENCE_TAGS = {
        # Activity Type Tags
        'hands-on': 'Interactive activities where visitors participate',
        'interactive': 'Engaging exhibits or experiences requiring participation', 
        'educational': 'Learning-focused experiences with educational value',
        'guided-tours': 'Expert-led tours with insider knowledge',
        'self-guided': 'Explore-at-your-own-pace experiences',
        'workshops': 'Skill-building or creative workshops',
        'demonstrations': 'Live demonstrations of crafts, skills, or processes',
        'behind-the-scenes': 'Access to normally restricted areas or processes',
        
        # Vibe and Character Tags
        'quirky': 'Unusual, offbeat, or unconventional experiences',
        'unique': 'One-of-a-kind or rare experiences',
        'historic': 'Rich historical significance or preserved heritage',
        'artistic': 'Creative or artistically focused experiences',
        'immersive': 'Fully engaging environments that transport visitors',
        'peaceful': 'Calm, relaxing, contemplative experiences',
        'adventurous': 'Exciting or physically engaging experiences',
        
        # Experience Quality Tags  
        'high-quality': 'Exceptional execution or presentation',
        'authentic': 'Genuine, non-commercialized experiences',
        'seasonal': 'Experience varies significantly by season',
        'photogenic': 'Highly visual or Instagram-worthy',
        'sensory': 'Rich sensory experiences (sounds, smells, textures)',
        
        # Social and Accessibility Tags
        'family-friendly': 'Great experiences for children and families',
        'date-worthy': 'Romantic or special occasion appropriate',
        'group-friendly': 'Good for groups or social gatherings',
        'solo-friendly': 'Enjoyable for individual visitors',
        'accessibility-champion': 'Exceptional accessibility accommodations'
    }
    
    # Venue name patterns that suggest interesting experiences
    INTERESTING_NAME_PATTERNS = {
        'quirky': [
            r'\b(odditorium|peculiar|bizarre|weird|strange|unusual)\b',
            r'\b(mystery|secret|hidden|forgotten)\b',
            r'\b(world.*largest|smallest.*world)\b',
        ],
        'hands-on': [
            r'\b(hands.?on|interactive|touch|make|create|build)\b',
            r'\b(workshop|studio|maker|craft|pottery|glass.*blow)\b',
            r'\b(demonstration|demo|live.*show)\b',
        ],
        'historic': [
            r'\b(historic|heritage|colonial|victorian|antique)\b',
            r'\b(old|vintage|traditional|preserved|restored)\b',
            r'\b(museum|house|mansion|homestead)\b',
        ],
        'unique': [
            r'\b(only|first|last|original|authentic)\b',
            r'\b(collection|exhibit|display.*rare)\b',
            r'\b(specialty|specialized|unique)\b',
        ],
        'artistic': [
            r'\b(art|artist|gallery|studio|creative)\b',
            r'\b(sculpture|painting|craft|handmade)\b',
            r'\b(design|contemporary|modern.*art)\b',
        ]
    }
    
    # Google Places types that suggest specific experiences
    GOOGLE_TYPE_EXPERIENCE_MAPPING = {
        'amusement_park': ['adventurous', 'family-friendly', 'high-quality'],
        'aquarium': ['educational', 'immersive', 'family-friendly', 'sensory'],
        'art_gallery': ['artistic', 'peaceful', 'photogenic', 'solo-friendly'],
        'museum': ['educational', 'historic', 'self-guided', 'photogenic'],
        'zoo': ['educational', 'family-friendly', 'hands-on', 'seasonal'],
        'botanical_garden': ['peaceful', 'photogenic', 'seasonal', 'sensory'],
        'library': ['educational', 'peaceful', 'solo-friendly'],
        'park': ['peaceful', 'family-friendly', 'seasonal', 'photogenic'],
        'tourist_attraction': ['photogenic', 'unique'],
        'establishment': [],  # Too generic
    }
    
    # Category-based experience assignments
    CATEGORY_EXPERIENCE_MAPPING = {
        1: ['peaceful', 'photogenic', 'seasonal', 'educational', 'sensory'],  # Botanical Gardens
        2: ['peaceful', 'educational', 'unique', 'seasonal', 'solo-friendly'],  # Bird Watching  
        3: ['educational', 'historic', 'self-guided', 'photogenic'],  # Museums
        4: ['immersive', 'educational', 'family-friendly', 'sensory'],  # Aquariums
        5: [],  # Shopping Centers - generally not interesting
        6: ['quirky', 'unique', 'historic', 'hands-on'],  # Antique Shops
        7: ['artistic', 'peaceful', 'photogenic', 'solo-friendly'],  # Art Galleries
        8: ['educational', 'peaceful', 'solo-friendly'],  # Libraries
        9: ['immersive', 'date-worthy', 'group-friendly'],  # Theaters
        10: ['hands-on', 'workshops', 'family-friendly', 'creative'],  # Craft Stores
        11: ['hands-on', 'seasonal', 'educational', 'peaceful'],  # Garden Centers
        12: ['immersive', 'unique', 'photogenic', 'sensory'],  # Conservatories
    }
    
    @classmethod
    def analyze_venue_experience(cls, venue: Venue, place_data: Dict = None) -> List[str]:
        """Analyze a venue and return appropriate experience tags."""
        tags = set()
        
        # Add category-based tags
        if venue.category_id in cls.CATEGORY_EXPERIENCE_MAPPING:
            tags.update(cls.CATEGORY_EXPERIENCE_MAPPING[venue.category_id])
        
        # Add name-based tags
        name_tags = cls._analyze_venue_name(venue.name)
        tags.update(name_tags)
        
        # Add Google Places type-based tags
        if place_data and 'types' in place_data:
            type_tags = cls._analyze_google_types(place_data['types'])
            tags.update(type_tags)
        
        # Add accessibility-based tags
        accessibility_tags = cls._analyze_accessibility_quality(venue)
        tags.update(accessibility_tags)
        
        # Add rating-based quality tags
        quality_tags = cls._analyze_quality_signals(venue)
        tags.update(quality_tags)
        
        return list(tags)
    
    @classmethod 
    def _analyze_venue_name(cls, name: str) -> Set[str]:
        """Extract experience tags from venue name patterns."""
        tags = set()
        name_lower = name.lower()
        
        for tag, patterns in cls.INTERESTING_NAME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    tags.add(tag)
                    break
        
        return tags
    
    @classmethod
    def _analyze_google_types(cls, types: List[str]) -> Set[str]:
        """Extract experience tags from Google Places types."""
        tags = set()
        
        for place_type in types:
            if place_type in cls.GOOGLE_TYPE_EXPERIENCE_MAPPING:
                tags.update(cls.GOOGLE_TYPE_EXPERIENCE_MAPPING[place_type])
        
        return tags
    
    @classmethod
    def _analyze_accessibility_quality(cls, venue: Venue) -> Set[str]:
        """Determine accessibility-related experience tags."""
        tags = set()
        
        # Count accessibility features
        features = [
            venue.wheelchair_accessible,
            venue.accessible_parking, 
            venue.accessible_restroom,
            venue.ramp_access,
            venue.elevator_access,
            venue.wide_doorways,
            venue.accessible_seating
        ]
        
        accessibility_score = sum(features) / len(features)
        
        # Exceptional accessibility gets a tag
        if accessibility_score >= 0.8:
            tags.add('accessibility-champion')
        
        return tags
    
    @classmethod 
    def _analyze_quality_signals(cls, venue: Venue) -> Set[str]:
        """Determine quality-based experience tags."""
        tags = set()
        
        # High Google rating suggests high quality
        if venue.google_rating and float(venue.google_rating) >= 4.5:
            tags.add('high-quality')
        
        # Multiple reviews suggest authenticity
        review_count = venue.reviews.count() if venue.reviews else 0
        if review_count >= 5:
            tags.add('authentic')
        
        return tags
    
    @classmethod
    def get_tag_description(cls, tag: str) -> str:
        """Get human-readable description for a tag."""
        return cls.EXPERIENCE_TAGS.get(tag, tag.replace('-', ' ').title())
    
    @classmethod
    def get_interesting_tags(cls) -> List[str]:
        """Get tags that indicate particularly interesting experiences."""
        return [
            'quirky', 'unique', 'hands-on', 'interactive', 'immersive',
            'behind-the-scenes', 'workshops', 'demonstrations', 'artistic',
            'historic', 'high-quality', 'authentic'
        ]
    
    @classmethod
    def calculate_experience_interestingness(cls, tags: List[str]) -> float:
        """Calculate how interesting a venue is based on its experience tags."""
        if not tags:
            return 0.0
        
        interesting_tags = cls.get_interesting_tags()
        interesting_count = sum(1 for tag in tags if tag in interesting_tags)
        
        # Base score from interesting tag ratio
        base_score = (interesting_count / len(interesting_tags)) * 5.0
        
        # Bonus for multiple interesting tags
        if interesting_count >= 3:
            base_score += 1.0
        
        return min(base_score, 5.0)  # Cap at 5.0 for this component