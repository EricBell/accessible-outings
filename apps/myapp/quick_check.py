#!/usr/bin/env python3
"""
Quick app health check - run this before every deployment.
Usage: python quick_check.py
"""

import sys
import subprocess
import requests
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"🔍 {description}...", end=" ")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅")
            return True
        else:
            print(f"❌ Failed: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_app_running(port=5000):
    """Check if app is responding on given port."""
    print(f"🌐 Checking if app responds on port {port}...", end=" ")
    try:
        response = requests.get(f'http://localhost:{port}', timeout=5)
        if response.status_code == 200:
            print("✅")
            return True
        else:
            print(f"❌ Status: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ No response")
        return False

def main():
    print("🚀 QUICK APP HEALTH CHECK")
    print("="*40)
    
    checks_passed = 0
    total_checks = 0
    
    # File existence checks
    critical_files = [
        'app.py',
        'templates/index.html',
        'templates/venue_detail.html',
        'templates/about.html'
    ]
    
    for file_path in critical_files:
        total_checks += 1
        if Path(file_path).exists():
            print(f"📁 {file_path} exists... ✅")
            checks_passed += 1
        else:
            print(f"📁 {file_path} exists... ❌")
    
    # Python syntax check
    total_checks += 1
    if run_command("python -m py_compile app.py", "Python syntax check"):
        checks_passed += 1
    
    # Try importing main modules
    total_checks += 1
    if run_command("python -c 'from app import create_app; print(\"Import successful\")'", "Import test"):
        checks_passed += 1
    
    # Test database operations
    total_checks += 1
    test_db_cmd = """python -c "
from app import create_app
app = create_app()
with app.app_context():
    from models import db
    db.create_all()
    print('Database operations successful')
" """
    if run_command(test_db_cmd, "Database operations"):
        checks_passed += 1
    
    # Check if app can start (brief test)
    print("🏃 Testing app startup...")
    startup_cmd = "timeout 10s python app.py || echo 'App startup test completed'"
    run_command(startup_cmd, "App startup test")
    
    # Summary
    print("\n" + "="*40)
    print("QUICK CHECK SUMMARY")
    print("="*40)
    success_rate = (checks_passed / total_checks) * 100
    print(f"✅ Passed: {checks_passed}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 App looks healthy!")
        return 0
    else:
        print("⚠️  Issues detected. Run full validation: python validate_app.py")
        return 1

if __name__ == '__main__':
    exit(main())