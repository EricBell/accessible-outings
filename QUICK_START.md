# Quick Start Guide

## Starting from Ground Zero

### Option 1: Use the Reset Script (Recommended)
```bash
./reset_and_start.sh
```

### Option 2: Manual Steps
```bash
# 1. Stop any running app
pkill -f "python.*app.py"

# 2. Remove database 
rm -f instance/accessible_outings.db

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start fresh
python app.py
```

## What Happens on First Start

1. **Database Creation**: SQLite database created in `instance/accessible_outings.db`
2. **Sample Data**: Categories and default user created automatically
3. **App Ready**: Visit http://127.0.0.1:5000

## Default Credentials
- **Username**: testuser
- **Password**: testpass

## Testing the Venue Detail Issue

1. Go to http://127.0.0.1:5000
2. Enter a ZIP code (e.g., "03865") and search
3. Click "View Details" on any venue
4. **Expected**: You should see the missing template issue

## Running Tests
```bash
# Run all tests
python -m unittest unit_tests

# Run specific test
python -m unittest unit_tests.VenueDetailTestCase.test_venue_detail_template_missing_error -v
```

## Files to Know About
- `templates/venue_detail.html` - **MISSING** - This needs to be created
- `unit_tests.py` - Tests that verify the missing template issue
- `routes/main.py` - Contains the venue detail route that fails