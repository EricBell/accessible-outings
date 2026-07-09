# Accessible Outings Finder — Overview

> A Flask web app that helps people who use wheelchairs (and their caregivers) find wheelchair-accessible indoor venues and events near a given ZIP code.

## Purpose

The app lets users search by ZIP code and radius for accessible venues (museums, aquariums, botanical gardens, shopping centers, etc.) and events happening at those venues. Every venue carries explicit accessibility attributes (ramp access, accessible restrooms, elevator access, etc.), and users can save favorites and leave accessibility-focused reviews. Venue data is sourced from the Google Places API; an Eventbrite integration exists in the codebase but is currently disabled (see Notes & Gotchas).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask 2.3 |
| ORM | Flask-SQLAlchemy 3 / SQLAlchemy 2 |
| Auth | Flask-Login + Werkzeug/bcrypt password hashing |
| Forms | Flask-WTF / WTForms (CSRF currently disabled, see Gotchas) |
| Database | PostgreSQL (production) or SQLite (dev/Docker) |
| Frontend | Server-rendered Jinja2 templates, Bootstrap 5, vanilla JS |
| External APIs | Google Places API, Google Geocoding API, Eventbrite API (disabled) |
| Containerization | Docker (python:3.12-alpine3.21) |
| Deployment | `just deploy` — rsync to a VPS over SSH + remote restart script |
| Testing | pytest, pytest-flask |

## Directory Structure

```
.
├── config/myapp.toml       # Deploy target: ssh host, remote path, restart cmd
├── justfile                 # `just deploy <target>` — rsyncs repo to VPS and restarts
├── restart.sh / debug_deploy.sh
└── apps/myapp/               # The actual Flask application (repo root for the app)
    ├── app.py                # App factory (create_app), blueprint registration, sample-data init
    ├── config.py              # Config classes (Development/Production/Testing), env var loading
    ├── models/                # SQLAlchemy models
    │   ├── user.py            # User (Flask-Login UserMixin, bcrypt password hashing)
    │   ├── venue.py            # Venue, VenueCategory
    │   ├── event.py            # Event, EventFavorite, EventReview
    │   └── review.py           # UserReview, UserFavorite, SearchHistory, ApiCache
    ├── routes/                # Flask blueprints
    │   ├── main.py             # Page routes: /, /search, venue/event detail pages
    │   ├── api.py               # JSON REST API: /api/search, /api/venue/<id>, /api/favorites, etc.
    │   └── auth.py               # /auth/login, /auth/logout (supports BYPASS_AUTH dev mode)
    ├── utils/                 # Business logic / integrations
    │   ├── google_places.py    # GooglePlacesAPI client + VenueSearchService (with ApiCache caching)
    │   ├── geocoding.py         # GeocodingService, LocationService (ZIP → lat/lon)
    │   ├── accessibility.py     # AccessibilityFilter (scoring), AccessibilityRecommendations
    │   ├── database.py           # DatabaseCompatArray/JSON — SQLite/Postgres compatible column types
    │   ├── event_aggregator.py   # Syncs external event sources into the Event table
    │   ├── event_generator.py
    │   ├── experience_tagger.py
    │   └── event_integrations/  # base_event_provider.py, eventbrite_provider.py (disabled)
    ├── templates/               # Jinja2 templates (base.html, index, search_results, venue_detail, event_detail, auth/, errors/)
    ├── static/css, static/js
    ├── database/
    │   ├── schema.sql            # PostgreSQL schema
    │   └── schema_sqlite.sql      # SQLite schema
    ├── admin-tools/              # One-off ops scripts: db_migration.py, create_admin_user.py, fix_categories.py, etc.
    ├── debug-tools/               # Ad hoc debugging/auth-diagnosis scripts (not part of the app runtime)
    └── tests/                    # test_app.py, test_geocode.py
```

## Architecture

- **App factory pattern**: `app.py:create_app()` builds the Flask app, loads config via `config.get_config()` (driven by `FLASK_ENV`), initializes `db` and `login_manager`, registers three blueprints (`auth`, `main`, `api`), and attaches service objects (`app.google_api`, `app.venue_search_service`, `app.location_service`) directly to the Flask app instance for use in route handlers via `current_app`.
- **First-run bootstrapping**: on startup, if `VenueCategory` table is empty, `_initialize_database()` seeds 12 hardcoded venue categories (Botanical Gardens, Museums, Aquariums, etc.) and, in SQLite+BYPASS_AUTH mode, creates a default `testuser`.
- **Dev auth bypass**: `BYPASS_AUTH=True` + `DEFAULT_USER_ID` skips real login — `auth.py`'s login route auto-logs-in the default user, and both `routes/main.py` and `routes/api.py` define a local `get_current_user()` helper that falls back to the default user when bypass is enabled. This pattern is duplicated in each blueprint rather than centralized.
- **Database portability layer**: `utils/database.py` defines `DatabaseCompatArray`/`DatabaseCompatJSON` SQLAlchemy `TypeDecorator`s so the same model code works against Postgres (`ARRAY`/`JSONB`) and SQLite (JSON-serialized `Text`). `config.py` auto-detects DB type from `DATABASE_URL` and sets `DATABASE_TYPE`.
- **External API caching**: `GooglePlacesAPI._make_request()` checks/writes `ApiCache` (in `models/review.py`) before/after hitting Google, keyed by a cache key with a configurable TTL (`CACHE_TIMEOUT_HOURS`).
- **Accessibility scoring**: `utils/accessibility.py`'s `AccessibilityFilter` computes a 0–1 accessibility score per venue from its boolean accessibility columns; exposed to templates via a custom Jinja filter (`accessibility_score`) registered in `app.py`.
- **Events vs. venues**: Venues are places (from Google Places); Events are scheduled happenings tied to a venue (`Event.venue_id`), categorized as Fun/Interesting/Off-beat (`is_fun`, `is_interesting`, `is_off_beat` booleans) with fun/learning/uniqueness scores. `EventAggregator` (`utils/event_aggregator.py`) is meant to sync events from external providers into the DB but currently only uses local data — see Gotchas.

## Integrations

- **Google Places API** (`utils/google_places.py`, `GOOGLE_PLACES_API_KEY`) — venue search and details.
- **Google Geocoding API** (`utils/geocoding.py`, same key) — ZIP code → lat/lon for search.
- **Eventbrite API** (`utils/event_integrations/eventbrite_provider.py`, `EVENTBRITE_API_KEY`) — implemented but **disabled** in `EventAggregator._initialize_providers()` because Eventbrite's v3 API no longer allows public search; code is commented out with a TODO to explore scraping or alternate sources.

## Database & Data Layer

- Flask-SQLAlchemy models in `models/`: `User`, `Venue`, `VenueCategory`, `Event`, `EventFavorite`, `EventReview`, `UserReview`, `UserFavorite`, `SearchHistory`, `ApiCache`.
- Dual schema files: `database/schema.sql` (Postgres) and `database/schema_sqlite.sql` (SQLite), plus `db.create_all()` at startup for dev convenience.
- `SQLALCHEMY_DATABASE_URI` comes from `DATABASE_URL` (Postgres, with `postgres://` → `postgresql://` normalization) or defaults to `sqlite:///accessible_outings.db`.
- Production requires Postgres — `ProductionConfig.validate_config()` errors if `DATABASE_URL` is unset or still SQLite.
- Ad hoc schema migrations are handled by one-off scripts in `admin-tools/` (`db_migration.py`, `update_events_schema.py`, `add_experience_columns.py`) rather than a migration framework like Alembic.

## Connectivity & Configuration

Key environment variables (loaded via `python-dotenv` in `config.py`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string (omit for SQLite dev mode) |
| `GOOGLE_PLACES_API_KEY` | Required — venue search & geocoding |
| `EVENTBRITE_API_KEY` | Present but unused (integration disabled) |
| `SECRET_KEY` | Flask session secret — must be changed for production |
| `FLASK_ENV` | `development` / `production` / `testing` — selects config class |
| `BYPASS_AUTH`, `DEFAULT_USER_ID` | Dev-only auto-login |
| `DEFAULT_SEARCH_RADIUS_MILES`, `MAX_SEARCH_RADIUS_MILES` | Search defaults (30 / 60) |
| `CACHE_TIMEOUT_HOURS` | Google API response cache TTL |
| `DEFAULT_LATITUDE`, `DEFAULT_LONGITUDE` | Fallback coordinates (defaults to Concord, NH) |
| `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE` | Cookie security flags |

Runs on port `5000` by default (`PORT` env var overrides). Deployment target and SSH details live in `config/myapp.toml`, driven by `justfile`'s `just deploy <target>` (rsyncs to `accessibleoutings@50.116.57.169:/home/accessibleoutings/public_html/flaskapp/` and runs `restart.sh` remotely).

## Key Entry Points

- `apps/myapp/app.py` — application factory and bootstrap; start here.
- `apps/myapp/config.py` — all environment-driven configuration.
- `apps/myapp/routes/main.py` — primary user-facing page flow (search, venue/event detail).
- `apps/myapp/routes/api.py` — JSON API surface (`/api/search`, `/api/venue/<id>`, `/api/favorites`, `/api/reviews`, `/api/geocode`, `/api/health`).
- `apps/myapp/models/__init__.py` — where `db`/`login_manager` are created and all models are wired together.
- `apps/myapp/utils/google_places.py` — external venue data fetching and caching.

## Notes & Gotchas

- **CSRF is disabled** in `config.py` (`WTF_CSRF_ENABLED = False`) with a comment "Disabled for development" — this applies to all configs including `ProductionConfig`, which does not override it.
- **Eventbrite integration is fully implemented but dormant** — `EventAggregator` never actually calls out to Eventbrite; only local DB events are served. Don't assume events shown are synced from a live external source.
- **No formal migration framework** (no Alembic) — schema changes are applied via bespoke scripts in `admin-tools/` that must be run in a specific order (documented in `DEPLOYMENT.md`). Two parallel schema files (`schema.sql` / `schema_sqlite.sql`) must be kept manually in sync.
- **`BYPASS_AUTH` dev convenience is duplicated logic** — both `routes/main.py` and `routes/api.py` (and `app.py`'s context processor) independently reimplement "get current user or fall back to default user," rather than sharing one helper.
- **`debug-tools/` and `admin-tools/` are large collections of one-off scripts** (password fixes, category resets, auth debugging) accumulated during development/ops — not part of the running app, but useful for understanding past issues (e.g. several `fix_admin_password*.py` variants suggest historical login/auth troubles).
- **Deployment is rsync-based, not containerized in production** — although a `Dockerfile` exists (Alpine, Python 3.12 pinned because 3.13 broke `psycopg2` builds), the actual deploy path (`justfile`) rsyncs source directly to a VPS and restarts via `restart.sh`, bypassing Docker.
- The repo root (`/home/ericbell/workspaces/original/accessible-outings`) is a thin deployment wrapper around the real app in `apps/myapp/` — most work happens inside that subdirectory.
