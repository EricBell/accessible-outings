# Deployment Guide for VPS

This guide covers the essential scripts and steps needed to deploy the Accessible Outings app to a VPS.

## Prerequisites

1. **[uv](https://docs.astral.sh/uv/)** installed on VPS (manages the Python version and virtual environment)
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

### 2. Database Schema (Alembic)

Schema creation and changes are managed by Alembic (`apps/myapp/migrations/`), not by the
old `admin-tools/db_migration.py` / `update_events_schema.py` scripts (those are deprecated
and kept only for historical reference - they operate on a stale hardcoded SQLite path and
won't touch Postgres).

**Brand-new database** (nothing created yet): the app applies pending migrations
automatically on startup, so you can skip straight to running the app. To apply them
manually first instead:

```bash
uv run flask db upgrade
```

**Existing database** (already has tables from a previous `schema.sql`/admin-tools setup):
tell Alembic it's already at the baseline instead of trying to recreate the tables:

```bash
uv run flask db stamp 7298bca17ff7
```

From then on, `uv run flask db upgrade` (or just starting the app) applies any future
migrations on top of that baseline.

Then create the admin account:

```bash
uv run flask create-admin
```

This prompts for username/email/password and creates a user with `is_admin=True` using the
app's real `User` model and Werkzeug password hashing. Additional admins can be created the
same way, or promoted from the web UI at `/admin/users` (see "User Management" below) once one
admin account exists.

### 3. Category Setup

```bash
# If you need to set up venue categories from scratch
uv run python reset_categories.py
uv run python fix_categories.py
```

### 4. Optional: Sample Data (for testing)

```bash
# Only run if you want sample data for testing
# uv run python create_sample_events.py
# uv run python create_boston_events.py
```

### 5. Production Database Validation

```bash
# Check database schema and integrity
cd ../debug-tools
uv run python check_schema.py
```

## Essential Scripts Summary

### Must Run (in order):
1. `uv run flask db upgrade` (or `flask db stamp 7298bca17ff7` for an existing database) - Creates/aligns all database tables and schema
2. `uv run flask create-admin` - Creates admin account (prompts for username/email/password)

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

On Postgres 15+, the grant above does not include permission to create tables - you also
need a schema-level grant, run while connected *to* `accessible_outings` specifically
(schema privileges are per-database):

```sql
\c accessible_outings
GRANT ALL ON SCHEMA public TO app_user;
```

Without this, `flask db upgrade` (see "Database Schema (Alembic)" above) fails with
`permission denied for schema public`.

### File Permissions
```bash
# Make scripts executable
chmod +x admin-tools/*.py
chmod +x debug-tools/*.py
```

### Application Startup
```bash
# Production startup (use gunicorn or similar)
uv run gunicorn --bind 0.0.0.0:8000 app:app

# Or for development testing
uv run python app.py
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
uv run python -c "from app import app; app.app_context().push(); from models import db; print('DB Connected:', db.engine.url)"
```

### Missing Admin User
```bash
uv run flask create-admin
```

To manage existing users (promote/demote admin, reset password, delete), use the web UI at
`/admin/users` once logged in as an admin.

### Schema Problems
```bash
# Check the current migration state
uv run flask db current

# See what would change
uv run flask db upgrade --sql

# Apply pending migrations
uv run flask db upgrade
```

## Production Security

1. **Use strong, unique passwords** for all admin accounts created via `flask create-admin`
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
uv run flask db upgrade  # or: flask db stamp 7298bca17ff7 for an existing database
uv run flask create-admin
uv run python app.py
```

Your app should now be ready for production use!