#!/usr/bin/env python3
"""
App validation script - checks for common issues and verifies functionality.
Run this regularly to catch problems early.
"""

import os
import sys
import importlib.util
import subprocess
import json
from pathlib import Path


class AppValidator:
    """Validates app structure, dependencies, and basic functionality."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def check(self, description, condition, error_msg=None, warning_msg=None):
        """Helper method to run a check and track results."""
        self.total_checks += 1
        print(f"Checking: {description}...", end=" ")
        
        if condition:
            print("✅ PASS")
            self.success_count += 1
        else:
            if error_msg:
                print(f"❌ FAIL: {error_msg}")
                self.errors.append(f"{description}: {error_msg}")
            elif warning_msg:
                print(f"⚠️  WARN: {warning_msg}")
                self.warnings.append(f"{description}: {warning_msg}")
            else:
                print("❌ FAIL")
                self.errors.append(description)

    def validate_file_structure(self):
        """Check that required files exist."""
        print("\n🗂️  VALIDATING FILE STRUCTURE")
        print("-" * 40)
        
        required_files = [
            'app.py',
            'config.py',
            'requirements.txt',
            'models/__init__.py',
            'models/venue.py',
            'models/user.py',
            'routes/main.py',
            'templates/base.html',
            'templates/index.html',
            'templates/search_results.html',
            'templates/venue_detail.html',
            'templates/about.html',
            'static/css/style.css',
            'static/js/app.js'
        ]
        
        for file_path in required_files:
            self.check(
                f"File exists: {file_path}",
                os.path.exists(file_path),
                f"Missing required file: {file_path}"
            )

    def validate_python_syntax(self):
        """Check Python files for syntax errors."""
        print("\n🐍 VALIDATING PYTHON SYNTAX")
        print("-" * 40)
        
        python_files = []
        for root, dirs, files in os.walk('.'):
            # Skip virtual environment and cache directories
            dirs[:] = [d for d in dirs if d not in ['.venv', '__pycache__', '.git']]
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
                self.check(f"Syntax: {py_file}", True)
            except SyntaxError as e:
                self.check(
                    f"Syntax: {py_file}", 
                    False, 
                    f"Syntax error: {e}"
                )
            except Exception as e:
                self.check(
                    f"Syntax: {py_file}", 
                    False, 
                    f"Error reading file: {e}"
                )

    def validate_imports(self):
        """Check that key imports work."""
        print("\n📦 VALIDATING IMPORTS")
        print("-" * 40)
        
        key_imports = [
            ('flask', 'Flask web framework'),
            ('flask_sqlalchemy', 'Database ORM'),
            ('flask_login', 'User authentication'),
            ('requests', 'HTTP requests'),
            ('bcrypt', 'Password hashing'),
        ]
        
        for module, description in key_imports:
            try:
                __import__(module)
                self.check(f"Import: {module} ({description})", True)
            except ImportError:
                self.check(
                    f"Import: {module} ({description})", 
                    False, 
                    f"Missing dependency: {module}"
                )

    def validate_templates(self):
        """Check template files for basic structure."""
        print("\n🎨 VALIDATING TEMPLATES")
        print("-" * 40)
        
        templates = {
            'templates/base.html': ['<!DOCTYPE html>', '<html', '<head>', '<body>'],
            'templates/index.html': ['{% extends "base.html" %}', '{% block content %}'],
            'templates/venue_detail.html': ['{% extends "base.html" %}', '{% block content %}'],
            'templates/search_results.html': ['{% extends "base.html" %}', '{% block content %}'],
            'templates/about.html': ['{% extends "base.html" %}', '{% block content %}']
        }
        
        for template, required_elements in templates.items():
            if os.path.exists(template):
                try:
                    with open(template, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    for element in required_elements:
                        self.check(
                            f"Template {template} contains '{element}'",
                            element in content,
                            f"Missing required element: {element}"
                        )
                except Exception as e:
                    self.check(
                        f"Read template: {template}",
                        False,
                        f"Error reading template: {e}"
                    )

    def validate_database_models(self):
        """Check database model definitions."""
        print("\n🗄️  VALIDATING DATABASE MODELS")
        print("-" * 40)
        
        try:
            # Try to import the models
            from models.venue import Venue, VenueCategory
            from models.user import User
            
            # Check that models have required attributes
            venue_attrs = ['name', 'address', 'latitude', 'longitude', 'accessibility_features']
            for attr in venue_attrs:
                self.check(
                    f"Venue model has {attr}",
                    hasattr(Venue, attr),
                    f"Venue model missing attribute: {attr}"
                )
            
            user_attrs = ['username', 'email', 'password_hash']
            for attr in user_attrs:
                self.check(
                    f"User model has {attr}",
                    hasattr(User, attr),
                    f"User model missing attribute: {attr}"
                )
                
        except ImportError as e:
            self.check(
                "Import database models",
                False,
                f"Cannot import models: {e}"
            )

    def validate_configuration(self):
        """Check configuration setup."""
        print("\n⚙️  VALIDATING CONFIGURATION")
        print("-" * 40)
        
        try:
            from config import get_config
            config = get_config()
            
            required_config = [
                'SECRET_KEY',
                'SQLALCHEMY_DATABASE_URI',
                'GOOGLE_PLACES_API_KEY'
            ]
            
            for setting in required_config:
                self.check(
                    f"Config has {setting}",
                    hasattr(config, setting),
                    f"Missing configuration: {setting}"
                )
                
        except Exception as e:
            self.check(
                "Load configuration",
                False,
                f"Configuration error: {e}"
            )

    def validate_static_assets(self):
        """Check static files exist and are accessible."""
        print("\n📁 VALIDATING STATIC ASSETS")
        print("-" * 40)
        
        static_files = [
            'static/css/style.css',
            'static/js/app.js'
        ]
        
        for asset in static_files:
            self.check(
                f"Static asset: {asset}",
                os.path.exists(asset) and os.path.getsize(asset) > 0,
                f"Missing or empty asset: {asset}"
            )

    def run_basic_app_test(self):
        """Try to create app instance and test basic functionality."""
        print("\n🚀 TESTING BASIC APP FUNCTIONALITY")
        print("-" * 40)
        
        try:
            # Try to import and create app
            from app import create_app
            app = create_app()
            
            self.check("App creation", app is not None)
            
            # Test with app context
            with app.app_context():
                # Try to access some routes
                client = app.test_client()
                
                # Test home page
                response = client.get('/')
                self.check(
                    "Home page accessible",
                    response.status_code == 200,
                    f"Home page returned status {response.status_code}"
                )
                
                # Test about page
                response = client.get('/about')
                self.check(
                    "About page accessible",
                    response.status_code == 200,
                    f"About page returned status {response.status_code}"
                )
                
        except Exception as e:
            self.check(
                "Basic app functionality",
                False,
                f"App test failed: {e}"
            )

    def check_for_common_issues(self):
        """Check for common development issues."""
        print("\n🔍 CHECKING FOR COMMON ISSUES")
        print("-" * 40)
        
        # Check for hardcoded secrets
        try:
            with open('app.py', 'r') as f:
                content = f.read()
                self.check(
                    "No hardcoded API keys in app.py",
                    'sk-' not in content and 'AIza' not in content,
                    warning_msg="Possible hardcoded API key detected"
                )
        except:
            pass
        
        # Check for debug mode in production files
        try:
            with open('app.py', 'r') as f:
                content = f.read()
                self.check(
                    "Debug mode handled properly",
                    'debug=True' not in content.replace('debug=debug', ''),
                    warning_msg="Hardcoded debug=True found"
                )
        except:
            pass

    def run_all_validations(self):
        """Run all validation checks."""
        print("🔍 STARTING APP VALIDATION")
        print("=" * 60)
        
        self.validate_file_structure()
        self.validate_python_syntax()
        self.validate_imports()
        self.validate_templates()
        self.validate_database_models()
        self.validate_configuration()
        self.validate_static_assets()
        self.run_basic_app_test()
        self.check_for_common_issues()
        
        self.print_summary()

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        success_rate = (self.success_count / self.total_checks) * 100 if self.total_checks > 0 else 0
        
        print(f"✅ Passed: {self.success_count}/{self.total_checks} ({success_rate:.1f}%)")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ ERRORS TO FIX:")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS TO REVIEW:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n🎉 ALL VALIDATIONS PASSED! Your app looks good!")
        elif not self.errors:
            print("\n✅ No critical errors found. Review warnings above.")
        else:
            print("\n🛠️  Please fix the errors above before deploying.")
        
        return len(self.errors) == 0


def main():
    """Main validation entry point."""
    validator = AppValidator()
    success = validator.run_all_validations()
    
    print(f"\n{'='*60}")
    print("NEXT STEPS:")
    print("="*60)
    print("1. Fix any errors listed above")
    print("2. Run comprehensive tests: python test_comprehensive.py")
    print("3. Test manually in browser")
    print("4. Deploy when all tests pass")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())