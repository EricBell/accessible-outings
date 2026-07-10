# Accessible Outings Finder — Overview

> A Flask web app that helps people who use wheelchairs (and their caregivers) find wheelchair-accessible indoor venues and events near a given ZIP code.

## 1. Purpose

The app lets users search by ZIP code and radius for accessible venues (museums, aquariums, botanical gardens, shopping centers, etc.) and events happening at those venues. Every venue carries explicit accessibility attributes (ramp access, accessible restrooms, elevator access, etc.), and users can save favorites and leave accessibility-focused reviews. Venue data is sourced from Google's **Places API (New)**; an Eventbrite integration exists in the codebase but is currently disabled (see Notes & Gotchas). Admins have a dedicated dashboard for user management and for growing/monitoring venue data coverage.

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, Flask 2.3 |
| Packaging | [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`) — replaces pip/venv/requirements.txt |
| ORM | Flask-SQLAlchemy 3 / SQLAlchemy 2 |
| Migrations | Flask-Migrate / Alembic (`migrations/`) |
| Auth | Flask-Login + Werkzeug password hashing |
| Forms | Flask-WTF / WTForms (CSRF currently disabled, see Gotchas) |
| Database | PostgreSQL (production and dev) or SQLite (fallback/Docker) |
| Frontend | Server-rendered Jinja2 templates, Bootstrap 5, vanilla JS |
| External APIs | Google Places API (New), Google Geocoding API, Eventbrite API (disabled) |
| Containerization | Docker (python:3.12-alpine3.21), builds via `uv sync --frozen` |
| Deployment | `just deploy` — rsync to a VPS over SSH + remote restart script (runs `uv sync` + `flask db upgrade` on restart) |
| Testing | pytest, pytest-flask |

## 3. Directory Structure

```
.
├── config/myapp.toml       # Deploy target: ssh host, remote path, restart cmd
├── justfile                 # `just deploy <target>` — rsyncs repo to VPS and restarts
├── restart.sh / debug_deploy.sh
└── apps/myapp/               # The actual Flask application (repo root for the app)
    ├── app.py                # App factory (create_app), blueprint registration, Alembic
    │                          #   upgrade-on-startup, `flask create-admin` CLI command
    ├── config.py              # Config classes (Development/Production/Testing), env var loading
    ├── pyproject.toml, uv.lock, .python-version   # uv-managed dependencies
    ├── migrations/            # Alembic env; migrations/versions/7298bca17ff7_baseline_schema.py
    ├── models/                # SQLAlchemy models
    │   ├── user.py            # User (Flask-Login UserMixin, Werkzeug password hashing, is_admin)
    │   ├── venue.py            # Venue, VenueCategory
    │   ├── event.py            # Event, EventFavorite, EventReview
    │   └── review.py           # UserReview, UserFavorite, SearchHistory, ApiCache
    ├── routes/                # Flask blueprints
    │   ├── main.py             # Page routes: /, /search, venue/event detail pages, /admin/*
    │   ├── api.py               # JSON REST API: /api/search, /api/venue/<id>, /api/favorites, etc.
    │   └── auth.py               # /auth/login, /auth/register, /auth/logout (supports BYPASS_AUTH)
    ├── utils/                 # Business logic / integrations
    │   ├── google_places.py    # GooglePlacesAPI client (Places API New) + VenueSearchService
    │   ├── geocoding.py         # GeocodingService, LocationService (ZIP → lat/lon)
    │   ├── accessibility.py     # AccessibilityFilter (scoring), AccessibilityRecommendations
    │   ├── database.py           # DatabaseCompatArray/JSON — SQLite/Postgres compatible column types
    │   ├── event_aggregator.py   # Syncs external event sources into the Event table
    │   └── event_integrations/  # base_event_provider.py, eventbrite_provider.py (disabled)
    ├── templates/               # Jinja2 templates, including templates/admin*.html (see Architecture)
    ├── static/css, static/js
    ├── database/
    │   ├── schema.sql            # SUPERSEDED — historical snapshot, Alembic is the source of truth
    │   └── schema_sqlite.sql      # SUPERSEDED — same
    ├── admin-tools/              # Ops scripts: fix_categories.py, reset_categories.py,
    │                              #   user_manager.py (CLI fallback for user mgmt), etc.
    ├── debug-tools/               # Ad hoc debugging scripts (not part of the app runtime)
    └── tests/                    # test_app.py, test_geocode.py
```

## 4. Architecture

- **App factory pattern**: `app.py:create_app()` builds the Flask app, loads config via `config.get_config()` (driven by `FLASK_ENV`), initializes `db`, `migrate` (Flask-Migrate), and `login_manager`, registers three blueprints (`auth`, `main`, `api`), and attaches service objects (`app.google_api`, `app.venue_search_service`, `app.location_service`) directly to the Flask app instance for use in route handlers via `current_app`.
- **Schema managed by Alembic**: on startup, `create_app()` runs `flask_migrate.upgrade()` against `migrations/` (guarded so `flask db init`/`migrate` can still import the app before that directory exists), then seeds 12 hardcoded venue categories if `VenueCategory` is empty. There's no more `db.create_all()` — the migration is the source of truth.
- **Admin bootstrap**: `uv run flask create-admin` (a `@app.cli.command()` in `app.py`) is the only way to create the first admin — it prompts for username/email/password and uses the real `User` model + Werkzeug hashing. Additional admins are promoted from the web UI.
- **Admin dashboard** (`routes/main.py`, gated by `admin_required`): `/admin` (stats overview), `/admin/users` (list/promote/demote/reset-password/delete), `/admin/seed` (proactively populate venue data for a ZIP/region by calling the same `VenueSearchService` the public search uses, across selected categories), `/admin/staleness` (buckets venues by `last_updated` age — Fresh/Aging/Stale/Very Stale — overall and per category, plus a "most stale" spot-check list).
- **Dev auth bypass**: `BYPASS_AUTH=True` + `DEFAULT_USER_ID` skips real login — `auth.py`'s login route auto-logs-in the default user, and both `routes/main.py` and `routes/api.py` define a local `get_current_user()` helper that falls back to the default user when bypass is enabled. This pattern is duplicated in each blueprint rather than centralized.
- **Database portability layer**: `utils/database.py` defines `DatabaseCompatArray`/`DatabaseCompatJSON` SQLAlchemy `TypeDecorator`s so the same model code works against Postgres (`ARRAY`/`JSONB`) and SQLite (JSON-serialized `Text`). `config.py` auto-detects DB type from `DATABASE_URL` and sets `DATABASE_TYPE`. The baseline Alembic migration explicitly imports `utils.database` since autogenerate doesn't add that import itself.
- **External API caching**: `GooglePlacesAPI` checks/writes `ApiCache` (`models/review.py`) before/after hitting Google, keyed by a cache key with a configurable TTL. Venues are deduped by `google_place_id` and re-fetched from Google if `last_updated` is more than 7 days old (`utils/google_places.py`).
- **Accessibility scoring**: `utils/accessibility.py`'s `AccessibilityFilter` computes a 0–1 accessibility score per venue from its boolean accessibility columns; exposed to templates via a custom Jinja filter (`accessibility_score`) registered in `app.py`.
- **Events vs. venues**: Venues are places (from Google Places); Events are scheduled happenings tied to a venue (`Event.venue_id`). `EventAggregator` (`utils/event_aggregator.py`) is meant to sync events from external providers into the DB but currently only uses local data — see Gotchas.

## 5. Integrations

- **Google Places API (New)** (`utils/google_places.py`, `GOOGLE_PLACES_API_KEY`) — venue search and details. Uses `places.googleapis.com/v1`, POST + JSON bodies, and a mandatory `X-Goog-FieldMask` header (migrated from the legacy `maps.googleapis.com/maps/api/place` GET-based API).
- **Google Geocoding API** (`utils/geocoding.py`, same key) — ZIP code → lat/lon for search, using the `postal_code` components filter (fixed after a bug where free-text ZIP lookups occasionally resolved to the wrong region, e.g. Boston's `02101` resolving to Colorado).
- **Eventbrite API** (`utils/event_integrations/eventbrite_provider.py`, `EVENTBRITE_API_KEY`) — implemented but **disabled** in `EventAggregator._initialize_providers()` because Eventbrite's v3 API no longer allows public search.

## 6. Database & Data Layer

- Flask-SQLAlchemy models in `models/`: `User` (with `is_admin`), `Venue`, `VenueCategory`, `Event`, `EventFavorite`, `EventReview`, `UserReview`, `UserFavorite`, `SearchHistory`, `ApiCache`.
- **Schema is managed by Alembic** (`migrations/`, Flask-Migrate) — `migrations/versions/7298bca17ff7_baseline_schema.py` is the baseline; `database/schema.sql` / `schema_sqlite.sql` are superseded historical snapshots, no longer executed by the app.
- `SQLALCHEMY_DATABASE_URI` comes from `DATABASE_URL` (Postgres, with `postgres://` → `postgresql://` normalization) or defaults to `sqlite:///accessible_outings.db`. `.env` is per-machine and git-ignored — local dev and the VPS each need their own `DATABASE_URL`.
- Production requires Postgres — `ProductionConfig.validate_config()` errors if `DATABASE_URL` is unset or still SQLite.
- **Postgres 15+ gotcha**: `GRANT ALL PRIVILEGES ON DATABASE` no longer implies `CREATE` on the `public` schema. A separate `GRANT ALL ON SCHEMA public TO <user>;`, run while connected to the target database (not `postgres`), is required or `flask db upgrade` fails with `permission denied for schema public`. Documented in README.md/DEPLOYMENT.md.
- Old ad hoc migration scripts in `admin-tools/` (`db_migration.py`, `update_events_schema.py`) are deprecated — they operate on a stale hardcoded SQLite path and predate Alembic adoption.

## 7. Connectivity & Configuration

Key environment variables (loaded via `python-dotenv` in `config.py`):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection string (omit for SQLite dev mode) |
| `GOOGLE_PLACES_API_KEY` | Required — venue search (Places API New) & geocoding |
| `EVENTBRITE_API_KEY` | Present but unused (integration disabled) |
| `SECRET_KEY` | Flask session secret — must be changed for production |
| `FLASK_ENV` | `development` / `production` / `testing` — selects config class |
| `BYPASS_AUTH`, `DEFAULT_USER_ID` | Dev-only auto-login |
| `DEFAULT_SEARCH_RADIUS_MILES`, `MAX_SEARCH_RADIUS_MILES` | Search defaults (30 / 60), also used by `/admin/seed` |
| `CACHE_TIMEOUT_HOURS` | Google API response cache TTL |
| `DEFAULT_LATITUDE`, `DEFAULT_LONGITUDE` | Fallback coordinates (defaults to Concord, NH) |
| `SESSION_COOKIE_SECURE/HTTPONLY/SAMESITE` | Cookie security flags |

Runs on port `5000` by default (`PORT` env var overrides). Deployment target and SSH details live in `config/myapp.toml`, driven by `justfile`'s `just deploy <target>` (rsyncs to `accessibleoutings@50.116.57.169:/home/accessibleoutings/public_html/flaskapp/` and runs `restart.sh` remotely, which now runs `uv sync --frozen --no-dev` before restarting).

## 8. Key Entry Points

- `apps/myapp/app.py` — application factory, Alembic upgrade-on-startup, `flask create-admin` CLI; start here.
- `apps/myapp/config.py` — all environment-driven configuration.
- `apps/myapp/routes/main.py` — primary user-facing page flow (search, venue/event detail) plus all `/admin/*` routes.
- `apps/myapp/routes/api.py` — JSON API surface (`/api/search`, `/api/venue/<id>`, `/api/favorites`, `/api/reviews`, `/api/geocode`, `/api/health`).
- `apps/myapp/models/__init__.py` — where `db`/`login_manager` are created and all models are wired together.
- `apps/myapp/utils/google_places.py` — external venue data fetching and caching (Places API New).
- `apps/myapp/migrations/` — Alembic migration environment; `flask db upgrade`/`flask db migrate` operate here.

## 9. Notes & Gotchas

- **CSRF is disabled** in `config.py` (`WTF_CSRF_ENABLED = False`) with a comment "Disabled for development" — this applies to all configs including `ProductionConfig`, which does not override it. Admin/auth POST forms (including the newer `/admin/users/*` and `/admin/seed` routes) rely on plain `<form>` posts with no CSRF token, matching the rest of the app.
- **Eventbrite integration is fully implemented but dormant** — `EventAggregator` never actually calls out to Eventbrite; only local DB events are served. Don't assume events shown are synced from a live external source.
- **No scheduler / background jobs** — venue data only refreshes when a user (or admin, via `/admin/seed`) triggers a search. `/admin/staleness` gives visibility into data age but doesn't auto-refresh anything.
- **`BYPASS_AUTH` dev convenience is duplicated logic** — both `routes/main.py` and `routes/api.py` (and `app.py`'s context processor) independently reimplement "get current user or fall back to default user," rather than sharing one helper.
- **`debug-tools/` and `admin-tools/` still hold one-off scripts** for data cleanup (`fix_categories.py`, `fix_venue_addresses.py`, `reset_categories.py`, etc.) — these remain shell-only; only user management (`user_manager.py`) and admin bootstrap have been migrated to proper CLI/web tooling so far.
- **Deployment is rsync-based, not containerized in production** — although a `Dockerfile` exists (Alpine, Python 3.12, builds via `uv sync --frozen --no-dev`), the actual deploy path (`justfile`) rsyncs source directly to a VPS and restarts via `restart.sh`, bypassing Docker.
- The repo root (`/home/ericbell/workspaces/original/accessible-outings`) is a thin deployment wrapper around the real app in `apps/myapp/` — most work happens inside that subdirectory.
