# Admin Tools

This folder contains scripts needed for administrative tasks and data management.

## User Management

Creating the first admin account and day-to-day user management (promote/demote admin, reset
password, delete) are no longer done via scripts in this folder - see:
- `uv run flask create-admin` (from `apps/myapp/`) - Create an admin account. Uses the real
  `User` model and Werkzeug password hashing, and works against Postgres or SQLite.
- `/admin/users` web UI - Promote/demote admin, reset passwords, and delete users once logged
  in as an admin.

The old `create_admin_user.py`, `fix_admin_password*.py`, `final_admin_fix.py`,
`clean_admin_setup.py`, `verify_admin_setup.py`, and `update_admin_password_direct.py` scripts
have been removed - they operated on a stale hardcoded SQLite path and (except `user_manager.py`)
used a password hashing scheme incompatible with the app's real login.

- `user_manager.py` - **Interactive CLI fallback for user management (verify/change/delete
  users)**. Still uses correct Werkzeug hashing; kept for shell-access scenarios where the web
  UI isn't convenient.

## Data Management
- `create_sample_events.py` - Create sample event data for testing/demo
- `create_boston_events.py` - Create Boston area event data
- `fix_categories.py` - Fix venue category data
- `fix_cities.py` - Fix city data inconsistencies
- `fix_venue_addresses.py` - Fix venue address formatting
- `update_venue_categories.py` - Update venue categorization
- `update_venue_experiences.py` - Update venue experience tags
- `reset_categories.py` - Reset venue categories to default
- `db_migration.py` - Database migration and schema updates
- `update_events_schema.py` - Add API integration fields to events table
- `reset_database_fresh.py` - **Clean database reset - removes all fake/generated data**

## Usage

To run any admin tool:
```bash
cd admin-tools
python script_name.py
```

**Note:** All scripts automatically reference the database at `../instance/accessible_outings.db` relative to the admin-tools directory.

**Warning:** These scripts modify production data. Use with caution in production environments.

## Common Admin Tasks

### Create Sample Data
```bash
python create_sample_events.py
python create_boston_events.py
```

### Fix Data Issues
```bash
python fix_categories.py
python fix_venue_addresses.py
```

### User Management
```bash
python user_manager.py
```
**Interactive tool to verify credentials, change passwords, and delete user accounts.**

### Fresh Database Reset (Remove Fake Data)
```bash
python reset_database_fresh.py
```
**Removes all fake/auto-generated events and venues, keeping only real data with Google Place IDs. Use this to start fresh with real Eventbrite events only.**