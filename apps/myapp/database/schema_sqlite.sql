-- Wheelchair-Friendly Outing Finder Database Schema
-- SQLite Database Schema for Accessible Outings Application

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS search_history;
DROP TABLE IF EXISTS api_cache;
DROP TABLE IF EXISTS user_reviews;
DROP TABLE IF EXISTS user_favorites;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS venue_categories;
DROP TABLE IF EXISTS users;

-- Users table for authentication and preferences
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    home_zip_code VARCHAR(10),
    max_travel_minutes INTEGER DEFAULT 60,
    accessibility_needs TEXT,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Venue categories tailored to user interests
CREATE TABLE venue_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_class VARCHAR(50), -- CSS class for icons
    search_keywords TEXT -- JSON array of keywords for API searches
);

-- Main venues table with comprehensive accessibility information
CREATE TABLE venues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_place_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    website VARCHAR(500),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    category_id INTEGER REFERENCES venue_categories(id),
    google_rating DECIMAL(2,1),
    price_level INTEGER, -- 0-4 scale from Google
    -- Accessibility features
    wheelchair_accessible BOOLEAN DEFAULT 0,
    accessible_parking BOOLEAN DEFAULT 0,
    accessible_restroom BOOLEAN DEFAULT 0,
    elevator_access BOOLEAN DEFAULT 0,
    wide_doorways BOOLEAN DEFAULT 0,
    ramp_access BOOLEAN DEFAULT 0,
    accessible_seating BOOLEAN DEFAULT 0,
    accessibility_notes TEXT,
    -- Operating hours
    hours_monday VARCHAR(50),
    hours_tuesday VARCHAR(50),
    hours_wednesday VARCHAR(50),
    hours_thursday VARCHAR(50),
    hours_friday VARCHAR(50),
    hours_saturday VARCHAR(50),
    hours_sunday VARCHAR(50),
    seasonal_hours TEXT,
    -- Experience and Interest Scoring
    experience_tags TEXT, -- JSON array of experience tags
    interestingness_score DECIMAL(3,2) DEFAULT 0.0, -- 0.0-10.0 scale
    event_frequency_score INTEGER DEFAULT 0, -- How often events happen (0-5)
    -- Metadata
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_accessible BOOLEAN DEFAULT 0, -- User-verified accessibility
    photo_urls TEXT -- JSON array of photo URLs
);

-- User favorites with personal notes
CREATE TABLE user_favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    venue_id INTEGER REFERENCES venues(id) ON DELETE CASCADE,
    notes TEXT,
    personal_accessibility_rating INTEGER CHECK (personal_accessibility_rating >= 1 AND personal_accessibility_rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, venue_id)
);

-- User reviews and visit logs
CREATE TABLE user_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    venue_id INTEGER REFERENCES venues(id) ON DELETE CASCADE,
    visit_date DATE,
    overall_rating INTEGER CHECK (overall_rating >= 1 AND overall_rating <= 5),
    accessibility_rating INTEGER CHECK (accessibility_rating >= 1 AND accessibility_rating <= 5),
    review_text TEXT,
    accessibility_notes TEXT,
    would_return BOOLEAN,
    recommended_for_wheelchair BOOLEAN,
    photos TEXT, -- JSON array of photo URLs/paths
    weather_conditions VARCHAR(100),
    visit_duration_hours DECIMAL(3,1),
    companion_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API cache for performance optimization
CREATE TABLE api_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    cache_data TEXT NOT NULL, -- JSON data
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history for improving recommendations
CREATE TABLE search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    search_zip VARCHAR(10),
    search_radius INTEGER,
    category_filter INTEGER REFERENCES venue_categories(id),
    results_count INTEGER,
    accessibility_filter BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_venues_location ON venues(latitude, longitude);
CREATE INDEX idx_venues_category ON venues(category_id);
CREATE INDEX idx_venues_accessibility ON venues(wheelchair_accessible);
CREATE INDEX idx_venues_google_place_id ON venues(google_place_id);
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_reviews_user_id ON user_reviews(user_id);
CREATE INDEX idx_user_reviews_venue_id ON user_reviews(venue_id);
CREATE INDEX idx_api_cache_expires ON api_cache(expires_at);
CREATE INDEX idx_search_history_user_id ON search_history(user_id);

-- Insert initial venue categories based on user interests
INSERT INTO venue_categories (name, description, icon_class, search_keywords) VALUES
('Botanical Gardens', 'Gardens, conservatories, arboretums with indoor facilities', 'fas fa-leaf', 
 '["botanical garden", "conservatory", "arboretum", "greenhouse", "indoor garden"]'),
 
('Bird Watching', 'Aviaries, bird sanctuaries, nature centers with indoor exhibits', 'fas fa-dove', 
 '["aviary", "bird sanctuary", "nature center", "wildlife center", "bird exhibit"]'),
 
('Museums', 'Art, history, science, and specialty museums', 'fas fa-university', 
 '["museum", "art museum", "history museum", "science museum", "gallery"]'),
 
('Aquariums', 'Aquariums and marine life centers', 'fas fa-fish', 
 '["aquarium", "marine center", "sea life center", "oceanarium"]'),
 
('Shopping Centers', 'Malls, shopping centers, and retail complexes', 'fas fa-shopping-bag', 
 '["shopping mall", "shopping center", "retail center", "plaza"]'),
 
('Antique Shops', 'Antique stores, vintage shops, and collectible stores', 'fas fa-gem', 
 '["antique store", "vintage shop", "collectibles", "consignment shop", "thrift store"]'),
 
('Art Galleries', 'Art galleries and exhibition spaces', 'fas fa-palette', 
 '["art gallery", "exhibition space", "art center", "studio gallery"]'),
 
('Libraries', 'Public libraries and cultural centers', 'fas fa-book', 
 '["library", "public library", "cultural center", "community center"]'),
 
('Theaters', 'Movie theaters and performance venues', 'fas fa-theater-masks', 
 '["movie theater", "cinema", "theater", "performance venue", "playhouse"]'),
 
('Craft Stores', 'Hobby and craft supply stores', 'fas fa-cut', 
 '["craft store", "hobby store", "art supply", "fabric store", "craft supplies"]'),
 
('Garden Centers', 'Indoor garden centers and nurseries', 'fas fa-seedling', 
 '["garden center", "nursery", "plant store", "indoor plants"]'),
 
('Conservatories', 'Glass houses and plant conservatories', 'fas fa-glass-whiskey', 
 '["conservatory", "glass house", "tropical house", "palm house"]');

-- Sample data for testing (optional - can be removed in production)
-- Insert a test user (password is 'testpass123' hashed with bcrypt)
INSERT INTO users (username, email, password_hash, first_name, last_name, home_zip_code) VALUES
('testuser', 'test@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq/3Haa', 'Test', 'User', '03301');

-- Trigger to update updated_at timestamp (SQLite version)
CREATE TRIGGER update_users_updated_at 
    AFTER UPDATE ON users
    FOR EACH ROW
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;
