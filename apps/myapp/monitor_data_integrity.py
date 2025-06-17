#!/usr/bin/env python3
"""
Live Data Integrity Monitor - Runs checks against live app to verify data authenticity.
Can be run as a cron job or scheduled task.
"""

import requests
import json
import re
import sys
from datetime import datetime
from urllib.parse import urljoin


class LiveDataMonitor:
    """Monitors live app to ensure data displayed is authentic and not static/fake."""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.issues_found = []
        self.validations_passed = []
        
    def log_issue(self, check, message, severity='ERROR'):
        """Log a data integrity issue."""
        issue = f"[{severity}] {check}: {message}"
        self.issues_found.append(issue)
        print(f"{'❌' if severity == 'ERROR' else '⚠️'} {issue}")
        
    def log_success(self, check):
        """Log a successful validation."""
        self.validations_passed.append(check)
        print(f"✅ {check}")

    def check_page_loads(self):
        """Verify critical pages load and contain expected content."""
        print("\n🌐 CHECKING PAGE LOADS AND CONTENT")
        print("-" * 40)
        
        pages = {
            '/': ['Search for accessible venues', 'venue categories'],
            '/about': ['Making the World More Accessible', 'accessibility'],
            '/search?zip_code=10001&radius=10': ['Search Results', 'venues']
        }
        
        for path, expected_content in pages.items():
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                
                if response.status_code != 200:
                    self.log_issue(f"Page {path}", f"Status code {response.status_code}")
                    continue
                
                content = response.text.lower()
                missing_content = [item for item in expected_content if item.lower() not in content]
                
                if missing_content:
                    self.log_issue(f"Page {path}", f"Missing expected content: {missing_content}")
                else:
                    self.log_success(f"Page {path} loads with expected content")
                    
            except requests.RequestException as e:
                self.log_issue(f"Page {path}", f"Request failed: {e}")

    def check_search_results_dynamic(self):
        """Verify search results change based on different parameters."""
        print("\n🔍 CHECKING SEARCH RESULTS ARE DYNAMIC")
        print("-" * 40)
        
        # Test different search parameters to ensure results are dynamic
        searches = [
            {'zip_code': '10001', 'radius': '5'},
            {'zip_code': '10001', 'radius': '25'},
            {'zip_code': '90210', 'radius': '10'},
        ]
        
        results = []
        for search_params in searches:
            try:
                url = urljoin(self.base_url, '/search')
                response = self.session.get(url, params=search_params, timeout=10)
                
                if response.status_code == 200:
                    # Extract venue count from "Found X venues"
                    content = response.text
                    venue_count_match = re.search(r'Found\s+<strong>(\d+)</strong>\s+venues', content)
                    if venue_count_match:
                        count = int(venue_count_match.group(1))
                        results.append(count)
                        self.log_success(f"Search {search_params} returned {count} venues")
                    else:
                        self.log_issue("Search results", f"No venue count found for {search_params}", "WARNING")
                else:
                    self.log_issue("Search request", f"Failed for {search_params}: {response.status_code}")
                    
            except Exception as e:
                self.log_issue("Search request", f"Exception for {search_params}: {e}")
        
        # Check if results vary (indicating dynamic behavior)
        if len(set(results)) > 1:
            self.log_success("Search results vary by location/radius (dynamic behavior confirmed)")
        elif results:
            self.log_issue("Search behavior", "All searches return same count (possibly static data)", "WARNING")

    def check_venue_detail_authenticity(self):
        """Check that venue detail pages show real, varying data."""
        print("\n🏢 CHECKING VENUE DETAIL AUTHENTICITY")
        print("-" * 40)
        
        # First get some venue IDs from search
        try:
            search_url = urljoin(self.base_url, '/search')
            response = self.session.get(search_url, params={'zip_code': '10001', 'radius': '10'}, timeout=10)
            
            if response.status_code == 200:
                # Extract venue IDs from "View Details" links
                venue_links = re.findall(r'/venue/(\d+)', response.text)
                unique_venues = list(set(venue_links))[:3]  # Check first 3 unique venues
                
                venue_data = []
                for venue_id in unique_venues:
                    venue_url = urljoin(self.base_url, f'/venue/{venue_id}')
                    venue_response = self.session.get(venue_url, timeout=10)
                    
                    if venue_response.status_code == 200:
                        content = venue_response.text
                        
                        # Check for suspicious test data patterns
                        suspicious_patterns = [
                            ('test', 'Contains "test"'),
                            ('example', 'Contains "example"'),
                            ('lorem ipsum', 'Contains lorem ipsum'),
                            ('123 main st', 'Generic test address'),
                            ('sample', 'Contains "sample"')
                        ]
                        
                        venue_suspicious = False
                        content_lower = content.lower()
                        for pattern, description in suspicious_patterns:
                            if pattern in content_lower:
                                self.log_issue(f"Venue {venue_id}", f"Suspicious content: {description}", "WARNING")
                                venue_suspicious = True
                        
                        # Extract venue name from page title or h1
                        name_match = re.search(r'<h1[^>]*>([^<]+)</h1>', content)
                        if name_match:
                            venue_name = name_match.group(1).strip()
                            venue_data.append({
                                'id': venue_id,
                                'name': venue_name,
                                'suspicious': venue_suspicious
                            })
                        
                        if not venue_suspicious:
                            self.log_success(f"Venue {venue_id} appears authentic")
                    else:
                        self.log_issue(f"Venue {venue_id}", f"Failed to load: {venue_response.status_code}")
                
                # Check if venue names are unique (not copy-pasted test data)
                venue_names = [v['name'] for v in venue_data]
                if len(venue_names) != len(set(venue_names)):
                    self.log_issue("Venue data", "Duplicate venue names found (possible test data)", "WARNING")
                else:
                    self.log_success("Venue names are unique (good sign of real data)")
                    
            else:
                self.log_issue("Venue ID extraction", f"Search failed: {response.status_code}")
                
        except Exception as e:
            self.log_issue("Venue detail check", f"Exception: {e}")

    def check_accessibility_scores_vary(self):
        """Verify accessibility scores vary and aren't hardcoded."""
        print("\n♿ CHECKING ACCESSIBILITY SCORE VARIATION")
        print("-" * 40)
        
        try:
            # Get search results and extract accessibility scores
            search_url = urljoin(self.base_url, '/search')
            response = self.session.get(search_url, params={'zip_code': '10001', 'radius': '25'}, timeout=10)
            
            if response.status_code == 200:
                # Extract accessibility scores from search results
                score_pattern = r'accessibility-(?:excellent|good|fair|limited)[^>]*>.*?(\d+)%'
                scores = re.findall(score_pattern, response.text, re.DOTALL)
                
                if scores:
                    score_values = [int(score) for score in scores]
                    unique_scores = set(score_values)
                    
                    if len(unique_scores) > 1:
                        self.log_success(f"Accessibility scores vary: {sorted(unique_scores)} (authentic calculation)")
                    else:
                        self.log_issue("Accessibility scores", 
                                     f"All scores identical: {list(unique_scores)} (possibly hardcoded)", 
                                     "WARNING")
                    
                    # Check for realistic score distribution
                    if max(score_values) == min(score_values):
                        self.log_issue("Score distribution", "No score variation (suspicious)", "WARNING")
                    elif 0 <= min(score_values) and max(score_values) <= 100:
                        self.log_success("Accessibility scores in valid range (0-100%)")
                    else:
                        self.log_issue("Score range", f"Scores outside valid range: {min(score_values)}-{max(score_values)}")
                else:
                    self.log_issue("Accessibility scores", "No scores found in search results", "WARNING")
            else:
                self.log_issue("Accessibility score check", f"Search failed: {response.status_code}")
                
        except Exception as e:
            self.log_issue("Accessibility score check", f"Exception: {e}")

    def check_api_data_freshness(self):
        """Check if data appears fresh and not stale/cached indefinitely."""
        print("\n🕒 CHECKING DATA FRESHNESS")
        print("-" * 40)
        
        try:
            # Check if server includes date headers
            response = self.session.head(self.base_url, timeout=5)
            
            if 'Date' in response.headers:
                server_date = response.headers['Date']
                self.log_success(f"Server includes date header: {server_date}")
            else:
                self.log_issue("Data freshness", "No date header from server", "WARNING")
            
            # Check for cache control headers
            if 'Cache-Control' in response.headers:
                cache_control = response.headers['Cache-Control']
                if 'no-cache' in cache_control or 'max-age' in cache_control:
                    self.log_success(f"Appropriate cache control: {cache_control}")
                else:
                    self.log_issue("Cache control", f"Unusual cache control: {cache_control}", "WARNING")
            
        except Exception as e:
            self.log_issue("Data freshness check", f"Exception: {e}")

    def check_for_placeholder_content(self):
        """Check for obvious placeholder or template content."""
        print("\n📝 CHECKING FOR PLACEHOLDER CONTENT")
        print("-" * 40)
        
        placeholder_patterns = [
            ('lorem ipsum', 'Lorem ipsum placeholder text'),
            ('placeholder', 'Placeholder text'),
            ('todo', 'TODO comments'),
            ('fixme', 'FIXME comments'),
            ('coming soon', 'Coming soon placeholders'),
            ('under construction', 'Under construction messages'),
            ('[venue name]', 'Template placeholders'),
            ('{{', 'Unprocessed template variables')
        ]
        
        try:
            # Check main pages for placeholder content
            pages_to_check = ['/', '/about']
            
            for page in pages_to_check:
                url = urljoin(self.base_url, page)
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    content = response.text.lower()
                    found_placeholders = []
                    
                    for pattern, description in placeholder_patterns:
                        if pattern in content:
                            found_placeholders.append(description)
                    
                    if found_placeholders:
                        self.log_issue(f"Placeholder content in {page}", 
                                     f"Found: {', '.join(found_placeholders)}", 
                                     "WARNING")
                    else:
                        self.log_success(f"No placeholder content in {page}")
                        
        except Exception as e:
            self.log_issue("Placeholder content check", f"Exception: {e}")

    def run_all_checks(self):
        """Run all live data integrity checks."""
        print("🔍 LIVE DATA INTEGRITY MONITORING")
        print("=" * 60)
        print(f"Target: {self.base_url}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.check_page_loads()
        self.check_search_results_dynamic()
        self.check_venue_detail_authenticity()
        self.check_accessibility_scores_vary()
        self.check_api_data_freshness()
        self.check_for_placeholder_content()
        
        self.print_summary()

    def print_summary(self):
        """Print monitoring summary."""
        print("\n" + "=" * 60)
        print("LIVE DATA INTEGRITY SUMMARY")
        print("=" * 60)
        
        total_checks = len(self.validations_passed) + len(self.issues_found)
        success_rate = (len(self.validations_passed) / total_checks * 100) if total_checks > 0 else 0
        
        print(f"✅ Checks Passed: {len(self.validations_passed)}")
        print(f"⚠️  Issues Found: {len(self.issues_found)}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.issues_found:
            print("\n🔍 ISSUES DETECTED:")
            for issue in self.issues_found:
                print(f"   {issue}")
        
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! Your live data appears authentic and properly sourced.")
        elif success_rate >= 75:
            print("\n✅ GOOD! Minor issues detected but data appears mostly authentic.")
        else:
            print("\n⚠️  CONCERNS! Multiple issues suggest possible static/fake data.")
        
        return success_rate >= 75


def main():
    """Run live data monitoring."""
    import argparse
    parser = argparse.ArgumentParser(description='Monitor live app data integrity')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL of the app to monitor')
    parser.add_argument('--output', help='Save results to file')
    
    args = parser.parse_args()
    
    monitor = LiveDataMonitor(args.url)
    success = monitor.run_all_checks()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"Data integrity check: {datetime.now()}\n")
            f.write(f"Target: {args.url}\n")
            f.write(f"Success: {success}\n")
            f.write(f"Issues: {len(monitor.issues_found)}\n")
            for issue in monitor.issues_found:
                f.write(f"  {issue}\n")
    
    print(f"\n{'='*60}")
    print("USAGE RECOMMENDATIONS:")
    print("="*60)
    print("1. Run this hourly/daily as a cron job")
    print("2. Alert on success rate < 75%")
    print("3. Monitor for new placeholder patterns")
    print("4. Verify data changes over time")
    print("5. Check against production URL before deployment")
    
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())