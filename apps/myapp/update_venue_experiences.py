#!/usr/bin/env python3
"""
Script to update existing venues with experience tags and interestingness scores.
This implements the hybrid approach for making venues more engaging and discovery-focused.
"""

import sqlite3
import os
import json
import re

def get_experience_tags(venue_name, category_id):
    """Determine experience tags for a venue based on name and category."""
    tags = []
    name_lower = venue_name.lower()
    
    # Category-based tags
    category_tags = {
        1: ['peaceful', 'photogenic', 'seasonal', 'educational', 'sensory'],  # Botanical Gardens
        2: ['peaceful', 'educational', 'unique', 'seasonal', 'solo-friendly'],  # Bird Watching  
        3: ['educational', 'historic', 'self-guided', 'photogenic'],  # Museums
        4: ['immersive', 'educational', 'family-friendly', 'sensory'],  # Aquariums
        5: [],  # Shopping Centers - generally not interesting
        6: ['quirky', 'unique', 'historic', 'hands-on'],  # Antique Shops
        7: ['artistic', 'peaceful', 'photogenic', 'solo-friendly'],  # Art Galleries
        8: ['educational', 'peaceful', 'solo-friendly'],  # Libraries
        9: ['immersive', 'date-worthy', 'group-friendly'],  # Theaters
        10: ['hands-on', 'workshops', 'family-friendly'],  # Craft Stores
        11: ['hands-on', 'seasonal', 'educational', 'peaceful'],  # Garden Centers
        12: ['immersive', 'unique', 'photogenic', 'sensory'],  # Conservatories
    }
    
    if category_id in category_tags:
        tags.extend(category_tags[category_id])
    
    # Name-based tags
    name_patterns = {
        'quirky': [r'\b(museum|amc)\b'],  # AMC theaters can be quirky experiences
        'hands-on': [r'\b(craft|workshop|studio|make|create|build)\b'],
        'historic': [r'\b(historic|heritage|colonial|victorian|antique|old)\b'],
        'unique': [r'\b(only|first|last|original|authentic|specialty)\b'],
        'artistic': [r'\b(art|artist|gallery|studio|creative|design)\b'],
        'high-quality': [r'\b(amc)\b'],  # AMC theaters are generally high quality
        'family-friendly': [r'\b(amc|target|walmart)\b'],  # These venues cater to families
    }
    
    for tag, patterns in name_patterns.items():
        for pattern in patterns:
            if re.search(pattern, name_lower, re.IGNORECASE):
                if tag not in tags:
                    tags.append(tag)
                break
    
    return tags

def calculate_interestingness_score(venue_name, category_id, experience_tags, google_rating, wheelchair_accessible):
    """Calculate interestingness score for a venue."""
    score = 0.0
    
    # Base score from category
    category_scores = {
        1: 7.0,   # Botanical Gardens
        2: 8.0,   # Bird Watching
        3: 6.5,   # Museums
        4: 8.5,   # Aquariums
        5: 2.0,   # Shopping Centers
        6: 7.5,   # Antique Shops
        7: 7.0,   # Art Galleries
        8: 5.0,   # Libraries
        9: 4.0,   # Theaters
        10: 6.0,  # Craft Stores
        11: 6.5,  # Garden Centers
        12: 8.0   # Conservatories
    }
    
    if category_id:
        score += category_scores.get(category_id, 5.0)
    
    # Experience tags boost
    interesting_tags = [
        'hands-on', 'interactive', 'quirky', 'unique', 'educational',
        'guided-tours', 'live-performances', 'workshops', 'demonstrations',
        'seasonal-events', 'family-friendly', 'behind-the-scenes'
    ]
    
    if experience_tags:
        tag_boost = sum(1.0 for tag in experience_tags if tag in interesting_tags)
        score += min(tag_boost * 0.5, 2.0)
    
    # Accessibility boost
    if wheelchair_accessible:
        score += 0.5
    
    # Rating boost
    if google_rating:
        rating_boost = (google_rating - 3.0) * 0.5
        score += rating_boost
    
    return min(score, 10.0)

def calculate_event_frequency_score(category_id, experience_tags):
    """Calculate event frequency score (0-5)."""
    category_scores = {
        1: 3, 2: 2, 3: 4, 4: 3, 5: 1, 6: 2,
        7: 4, 8: 3, 9: 5, 10: 3, 11: 2, 12: 3
    }
    
    score = category_scores.get(category_id, 1)
    
    # Boost for event-related tags
    event_tags = ['workshops', 'demonstrations', 'guided-tours', 'live-performances']
    if any(tag in experience_tags for tag in event_tags):
        score = min(score + 1, 5)
    
    return score

def update_venue_experiences():
    """Update all venues with experience data."""
    db_path = 'instance/accessible_outings.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all venues
    cursor.execute("""
        SELECT id, name, category_id, google_rating, wheelchair_accessible 
        FROM venues
    """)
    venues = cursor.fetchall()
    
    print(f"Updating {len(venues)} venues with experience data...")
    
    updated_count = 0
    for venue_id, name, category_id, google_rating, wheelchair_accessible in venues:
        try:
            # Get experience tags
            experience_tags = get_experience_tags(name, category_id)
            
            # Calculate scores
            interestingness_score = calculate_interestingness_score(
                name, category_id, experience_tags, google_rating, wheelchair_accessible
            )
            event_frequency_score = calculate_event_frequency_score(category_id, experience_tags)
            
            # Update venue
            cursor.execute("""
                UPDATE venues 
                SET experience_tags = ?, 
                    interestingness_score = ?, 
                    event_frequency_score = ?
                WHERE id = ?
            """, (json.dumps(experience_tags), interestingness_score, event_frequency_score, venue_id))
            
            updated_count += 1
            print(f"Updated {name}: score={interestingness_score:.1f}, tags={experience_tags}")
            
        except Exception as e:
            print(f"Error updating {name}: {e}")
            continue
    
    conn.commit()
    print(f"\nSuccessfully updated {updated_count} venues")
    
    # Show interesting venues
    print("\nTop 10 most interesting venues:")
    cursor.execute("""
        SELECT name, interestingness_score, experience_tags
        FROM venues 
        WHERE category_id IS NOT NULL
        ORDER BY interestingness_score DESC 
        LIMIT 10
    """)
    
    for i, (name, score, tags_json) in enumerate(cursor.fetchall(), 1):
        tags = json.loads(tags_json) if tags_json else []
        print(f"{i}. {name} (score: {score:.1f}) - {', '.join(tags[:3])}")
    
    conn.close()

if __name__ == '__main__':
    update_venue_experiences()