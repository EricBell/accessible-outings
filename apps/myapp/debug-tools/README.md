# Debug Tools

This folder contains scripts for debugging, testing, and development purposes.

## Authentication Debug Tools
- `debug_auth.py` - Debug authentication system
- `debug_auth_info.py` - Display detailed auth information
- `debug_flask_auth.py` - Debug Flask authentication flow
- `debug_login_flow.py` - Comprehensive login flow debugging
- `add_debug_auth.py` - Add debug authentication features
- `enable_flask_debugging.py` - Enable Flask debugging mode

## Authentication Testing
- `test_exact_auth.py` - Test exact authentication logic
- `test_flask_auth.py` - Test Flask authentication
- `test_flask_context.py` - Test Flask application context
- `test_flask_request.py` - Test Flask request handling
- `test_werkzeug_compat.py` - Test Werkzeug compatibility

## General Testing
- `simple_unit_tests.py` - Simple unit tests
- `unit_tests.py` - Comprehensive unit tests
- `test_comprehensive.py` - Comprehensive system tests
- `ultimate_tests.py` - Ultimate test suite

## Validation and Audit Tools
- `check_schema.py` - Check database schema integrity
- `quick_check.py` - Quick system health check
- `audit_data_sources.py` - Audit data source integrity
- `validate_app.py` - Validate application configuration
- `validate_data_sources.py` - Validate data source connections

## Other Debug Tools
- `debug_venues.py` - Debug venue data and functionality

## Usage

To run any debug tool:
```bash
cd debug-tools
python script_name.py
```

## Common Debug Tasks

### Debug Login Issues
```bash
python debug_login_flow.py
python debug_auth_info.py
```

### Test Authentication
```bash
python test_flask_auth.py
python test_exact_auth.py
```

### Run Test Suite
```bash
python test_comprehensive.py
python ultimate_tests.py
```

### Enable Debug Mode
```bash
python enable_flask_debugging.py
```

**Note:** These scripts are for development and debugging only. Do not run in production environments.