#!/usr/bin/env python3
"""
Test Flask authentication by simulating a POST request.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_flask_request():
    """Test authentication by simulating a Flask POST request."""
    try:
        from app import create_app
        from models import db
        from models.user import User
        
        app = create_app()
        
        with app.test_client() as client:
            with app.app_context():
                print("🧪 TESTING FLASK LOGIN REQUEST")
                print("=" * 50)
                
                # Test 1: GET the login page
                print("\n1. GET /auth/login")
                response = client.get('/auth/login')
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.content_type}")
                
                if response.status_code != 200:
                    print("   ❌ Login page not accessible")
                    return
                
                # Test 2: POST login data
                print("\n2. POST /auth/login with admin credentials")
                login_data = {
                    'username_or_email': 'admin',
                    'password': 'password',
                    'remember_me': False
                }
                
                response = client.post('/auth/login', data=login_data, follow_redirects=False)
                print(f"   Status: {response.status_code}")
                print(f"   Location: {response.headers.get('Location', 'None')}")
                
                if response.status_code == 302:
                    print("   ✅ Redirect - login likely successful")
                    
                    # Check where it's redirecting
                    location = response.headers.get('Location', '')
                    if 'login' in location:
                        print("   ⚠️ Redirecting back to login - authentication failed")
                    else:
                        print("   🎉 Redirecting away from login - authentication successful!")
                        
                elif response.status_code == 200:
                    print("   ⚠️ Staying on login page - check for errors")
                    
                    # Check response content for error messages
                    response_text = response.get_data(as_text=True)
                    if 'Invalid username' in response_text:
                        print("   ❌ Found 'Invalid username' error in response")
                    if 'error' in response_text.lower():
                        print("   ❌ Found error message in response")
                else:
                    print(f"   ❌ Unexpected status code: {response.status_code}")
                
                # Test 3: Check session
                print("\n3. Check session after login attempt")
                with client.session_transaction() as sess:
                    print(f"   Session data: {dict(sess)}")
                    if '_user_id' in sess:
                        print(f"   ✅ User ID in session: {sess['_user_id']}")
                    else:
                        print("   ❌ No user ID in session")
                
                # Test 4: Try accessing admin page
                print("\n4. Test admin page access")
                response = client.get('/admin', follow_redirects=False)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Admin page accessible")
                elif response.status_code == 302:
                    print("   ⚠️ Redirected - likely not authenticated")
                elif response.status_code == 403:
                    print("   ❌ Forbidden - authentication or authorization failed")
                
                print("\n🎯 RECOMMENDATION:")
                print("If the simulated request works but browser doesn't:")
                print("1. Clear all browser cookies and cache")
                print("2. Try incognito/private mode")
                print("3. Check browser developer tools for JavaScript errors")
                print("4. Verify the form is actually submitting to /auth/login")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Flask environment not available")
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_flask_request()