# Admin Tools

This folder contains scripts needed for administrative tasks and data management.

## User Management
- `create_admin_user.py` - Create a new admin user account
- `fix_admin_password.py` - Fix admin user password issues
- `fix_admin_password_final.py` - Final admin password reset tool
- `final_admin_fix.py` - Comprehensive admin user fixes
- `clean_admin_setup.py` - Clean and reset admin setup
- `verify_admin_setup.py` - Verify admin user configuration
- `update_admin_password_direct.py` - Direct password update utility
- `simple_password_fix.py` - Simple admin password reset

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

## Usage

To run any admin tool:
```bash
cd admin-tools
python script_name.py
```

**Warning:** These scripts modify production data. Use with caution in production environments.

## Common Admin Tasks

### Reset Admin Password
```bash
python fix_admin_password_final.py
```

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