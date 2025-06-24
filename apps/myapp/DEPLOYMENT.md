# Deployment Guide for VPS

This guide covers the essential scripts and steps needed to deploy the Accessible Outings app to a VPS.

## Prerequisites

1. **Python 3.8+** installed on VPS
2. **PostgreSQL** database setup (recommended for production)
3. **Environment variables** configured
4. **API Keys** obtained and configured

## Deployment Steps

### 1. Environment Setup

First, configure your environment variables in `.env`:

```bash
# Copy and modify the environment file
cp .env.example .env
```

**Required Environment Variables:**
```bash
# Database (Use PostgreSQL for production)
DATABASE_URL=postgresql://username:password@localhost:5432/accessible_outings

# API Keys (REQUIRED)
GOOGLE_PLACES_API_KEY=your_google_places_api_key
EVENTBRITE_API_KEY=your_eventbrite_api_key

# Flask Configuration
SECRET_KEY=your_very_secure_secret_key_here
FLASK_ENV=production
FLASK_DEBUG=False

# Security Settings (for HTTPS)
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True

# Disable auth bypass for production
BYPASS_AUTH=False
```

### 2. Database Migration Scripts (Run in Order)

Run these scripts from the `admin-tools/` directory:

```bash
cd admin-tools

# 1. Initial database setup and schema creation
python db_migration.py

# 2. Add API integration fields to events table
python update_events_schema.py

# 3. Create admin user account
python create_admin_user.py

# 4. Verify admin setup is working
python verify_admin_setup.py
```

### 3. Category Setup

```bash
# If you need to set up venue categories from scratch
python reset_categories.py
python fix_categories.py
```

### 4. Optional: Sample Data (for testing)

```bash
# Only run if you want sample data for testing
# python create_sample_events.py
# python create_boston_events.py
```

### 5. Production Database Validation

```bash
# Check database schema and integrity
cd ../debug-tools
python check_schema.py
```

## Essential Scripts Summary

### Must Run (in order):
1. `admin-tools/db_migration.py` - Creates all database tables and schema
2. `admin-tools/update_events_schema.py` - Adds Eventbrite API fields
3. `admin-tools/create_admin_user.py` - Creates admin account
4. `admin-tools/verify_admin_setup.py` - Verifies admin login works

### Optional:
- `admin-tools/reset_categories.py` - Reset venue categories to defaults
- `admin-tools/fix_categories.py` - Fix/update venue categorization
- `admin-tools/reset_database_fresh.py` - Clean slate (removes fake data)

## Environment-Specific Considerations

### PostgreSQL Setup
```sql
-- Create database
CREATE DATABASE accessible_outings;
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE accessible_outings TO app_user;
```

### File Permissions
```bash
# Make scripts executable
chmod +x admin-tools/*.py
chmod +x debug-tools/*.py
```

### Application Startup
```bash
# Production startup (use gunicorn or similar)
gunicorn --bind 0.0.0.0:8000 app:app

# Or for development testing
python app.py
```

## Verification Checklist

After running deployment scripts, verify:

- [ ] Database tables created successfully
- [ ] Admin user can login at `/auth/login`
- [ ] Venue categories are populated
- [ ] Google Places API integration works (search for venues)
- [ ] Eventbrite API integration works (event search)
- [ ] All templates render without errors
- [ ] SSL/HTTPS configured (if applicable)

## API Key Validation

Test your API keys:
```bash
# Check Google Places API
curl "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=42.3601,-71.0589&radius=1000&key=YOUR_API_KEY"

# Eventbrite API validation is done automatically during first search
```

## Troubleshooting

### Database Issues
```bash
# Check database connection
python -c "from app import app; app.app_context().push(); from models import db; print('DB Connected:', db.engine.url)"
```

### Missing Admin User
```bash
cd admin-tools
python clean_admin_setup.py
python create_admin_user.py
```

### Schema Problems
```bash
cd admin-tools
python db_migration.py --force-recreate
```

## Production Security

1. **Change default admin password** after first login
2. **Use strong SECRET_KEY** (not the default)
3. **Enable HTTPS** and set `SESSION_COOKIE_SECURE=True`
4. **Restrict API keys** to your domain
5. **Set up database backups**
6. **Monitor API usage** to avoid rate limits

## Monitoring

- Check application logs for errors
- Monitor API rate limits (Google Places, Eventbrite)
- Set up database backup schedule
- Monitor disk space for SQLite logs and cache

---

**Quick Start Command Sequence:**
```bash
cd admin-tools
python db_migration.py
python update_events_schema.py  
python create_admin_user.py
python verify_admin_setup.py
cd ..
python app.py
```

Your app should now be ready for production use!