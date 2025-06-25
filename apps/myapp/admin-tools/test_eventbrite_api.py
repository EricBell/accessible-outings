#!/usr/bin/env python3
"""
Test Eventbrite API - Diagnostic tool to test API key and endpoints
"""
import sys
import os
import requests
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_eventbrite_api():
    """Test Eventbrite API key and endpoints"""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get('EVENTBRITE_API_KEY')
    
    print("🔍 Eventbrite API Diagnostic Tool")
    print("=" * 40)
    
    if not api_key:
        print("❌ EVENTBRITE_API_KEY not found in environment variables")
        print("   Check your .env file")
        return False
    
    print(f"✅ API Key found: {api_key[:8]}...")
    
    # Test API endpoints
    base_url = "https://www.eventbriteapi.com/v3"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print(f"\n🔗 Testing API endpoints...")
    
    # Test 1: User info endpoint
    print(f"\n1. Testing user info endpoint...")
    try:
        response = requests.get(f"{base_url}/users/me/", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ User endpoint works")
            print(f"   User: {user_data.get('name', 'Unknown')}")
            print(f"   Email: {user_data.get('email', 'Unknown')}")
        elif response.status_code == 401:
            print(f"   ❌ Unauthorized - Invalid API key")
            print(f"   Response: {response.text}")
            return False
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network error: {e}")
        return False
    
    # Test 2: Event search endpoint
    print(f"\n2. Testing event search endpoint...")
    try:
        params = {
            'location.address': '02114',  # Boston ZIP
            'start_date.range_start': f"{date.today()}T00:00:00",
            'start_date.range_end': f"{date.today()}T23:59:59",
            'location.within': '25mi',
            'sort_by': 'date',
            'page_size': 5
        }
        
        response = requests.get(f"{base_url}/events/search/", headers=headers, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   URL: {response.url}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"   ✅ Search endpoint works")
            print(f"   Found {len(events)} events")
            
            if events:
                print(f"   Sample event: {events[0].get('name', {}).get('text', 'Unknown')}")
            else:
                print(f"   No events found for today in Boston area")
                
        elif response.status_code == 404:
            print(f"   ❌ Endpoint not found (404)")
            print(f"   This suggests the API endpoint URL has changed")
            print(f"   Response: {response.text}")
        elif response.status_code == 401:
            print(f"   ❌ Unauthorized - API key issue")
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network error: {e}")
    
    # Test 3: Try a broader date range
    print(f"\n3. Testing with broader date range...")
    try:
        from datetime import timedelta
        end_date = date.today() + timedelta(days=30)
        
        params = {
            'location.address': 'Boston, MA',  # Try city name instead of ZIP
            'start_date.range_start': f"{date.today()}T00:00:00",
            'start_date.range_end': f"{end_date}T23:59:59",
            'location.within': '50mi',
            'sort_by': 'date',
            'page_size': 10
        }
        
        response = requests.get(f"{base_url}/events/search/", headers=headers, params=params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events = data.get('events', [])
            print(f"   ✅ Broader search works")
            print(f"   Found {len(events)} events in next 30 days")
            
            if events:
                for i, event in enumerate(events[:3]):
                    name = event.get('name', {}).get('text', 'Unknown')
                    start = event.get('start', {}).get('local', 'Unknown')
                    print(f"   Event {i+1}: {name} - {start}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network error: {e}")
    
    # Test 4: Check API documentation endpoint
    print(f"\n4. Checking API status...")
    try:
        # Some APIs have a status or health endpoint
        response = requests.get("https://www.eventbriteapi.com/v3/", headers=headers, timeout=5)
        print(f"   API Base Status: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Could not reach API base: {e}")
    
    print(f"\n📋 Recommendations:")
    print(f"   1. Verify your API key is active at: https://www.eventbrite.com/platform/api-keys")
    print(f"   2. Check if you have proper permissions for event search")
    print(f"   3. Try searching on Eventbrite.com for events in your area to see if any exist")
    print(f"   4. Consider using a different location for testing (major cities like NYC, SF)")
    
    return True

def main():
    """Main function"""
    try:
        test_eventbrite_api()
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()