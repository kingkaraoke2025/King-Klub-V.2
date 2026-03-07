#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime
import uuid

class KingKlubAPITester:
    def __init__(self, base_url="https://karaoke-kingdom.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        self.test_user_name = f"TestUser{datetime.now().strftime('%H%M%S')}"
        self.test_password = "TestPass123!"
        
    def log_test(self, name, success, message=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {message}")
        else:
            print(f"❌ {name}: FAILED {message}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return False, {"error": "Unsupported method"}
                
            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                print(f"   Status: {response.status_code}, Expected: {expected_status}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                    return False, error_data
                except:
                    print(f"   Error: {response.text}")
                    return False, {"error": response.text}
                    
        except Exception as e:
            print(f"   Exception: {str(e)}")
            return False, {"error": str(e)}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, data = self.make_request('GET', '/')
        return self.log_test("Root Endpoint", success, 
                           f"- {data.get('message', '')}" if success else f"- {data.get('error', '')}")

    def test_user_registration(self):
        """Test user registration"""
        reg_data = {
            "email": self.test_user_email,
            "password": self.test_password,
            "display_name": self.test_user_name
        }
        
        success, data = self.make_request('POST', '/auth/register', reg_data)
        
        if success and 'token' in data and 'user' in data:
            self.token = data['token']
            self.user_id = data['user']['id']
            return self.log_test("User Registration", True, 
                               f"- User ID: {self.user_id}, Rank: {data['user']['rank']['name']}")
        else:
            return self.log_test("User Registration", False, f"- {data.get('error', data)}")

    def test_user_login(self):
        """Test user login"""
        login_data = {
            "email": self.test_user_email,
            "password": self.test_password
        }
        
        success, data = self.make_request('POST', '/auth/login', login_data)
        
        if success and 'token' in data and 'user' in data:
            self.token = data['token']  # Update token from login
            return self.log_test("User Login", True, 
                               f"- Points: {data['user']['points']}, Rank: {data['user']['rank']['name']}")
        else:
            return self.log_test("User Login", False, f"- {data.get('error', data)}")

    def test_get_user_info(self):
        """Test getting current user info"""
        success, data = self.make_request('GET', '/auth/me')
        
        if success and 'id' in data:
            return self.log_test("Get User Info", True, 
                               f"- {data['display_name']} ({data['rank']['name']})")
        else:
            return self.log_test("Get User Info", False, f"- {data.get('error', data)}")

    def test_get_queue(self):
        """Test getting song queue"""
        success, data = self.make_request('GET', '/queue')
        
        if success and isinstance(data, list):
            return self.log_test("Get Queue", True, f"- {len(data)} items in queue")
        else:
            return self.log_test("Get Queue", False, f"- {data.get('error', data)}")

    def test_add_to_queue(self):
        """Test adding song to queue"""
        song_data = {
            "song_title": "Bohemian Rhapsody",
            "artist": "Queen"
        }
        
        success, data = self.make_request('POST', '/queue', song_data)
        
        if success and 'id' in data:
            self.queue_item_id = data['id']
            return self.log_test("Add to Queue", True, 
                               f"- Position: {data['position']}, Wait: {data['estimated_wait']} min")
        else:
            return self.log_test("Add to Queue", False, f"- {data.get('error', data)}")

    def test_add_duplicate_queue(self):
        """Test adding duplicate song (should fail)"""
        song_data = {
            "song_title": "Another Song",
            "artist": "Another Artist"
        }
        
        success, data = self.make_request('POST', '/queue', song_data, expected_status=400)
        
        if not success:  # Expected to fail
            return self.log_test("Add Duplicate Queue", True, "- Correctly prevented duplicate")
        else:
            return self.log_test("Add Duplicate Queue", False, "- Should have prevented duplicate")

    def test_remove_from_queue(self):
        """Test removing song from queue"""
        if hasattr(self, 'queue_item_id'):
            success, data = self.make_request('DELETE', f'/queue/{self.queue_item_id}')
            
            if success:
                return self.log_test("Remove from Queue", True, "- Successfully removed")
            else:
                return self.log_test("Remove from Queue", False, f"- {data.get('error', data)}")
        else:
            return self.log_test("Remove from Queue", False, "- No queue item to remove")

    def test_get_leaderboard(self):
        """Test getting leaderboard"""
        success, data = self.make_request('GET', '/leaderboard')
        
        if success and isinstance(data, list):
            return self.log_test("Get Leaderboard", True, f"- {len(data)} users on leaderboard")
        else:
            return self.log_test("Get Leaderboard", False, f"- {data.get('error', data)}")

    def test_get_badges(self):
        """Test getting all badges"""
        success, data = self.make_request('GET', '/badges')
        
        if success and isinstance(data, list):
            badge_names = [badge.get('name', 'Unknown') for badge in data[:3]]
            return self.log_test("Get Badges", True, f"- {len(data)} badges available: {', '.join(badge_names)}...")
        else:
            return self.log_test("Get Badges", False, f"- {data.get('error', data)}")

    def test_get_accomplishments(self):
        """Test getting user accomplishments"""
        success, data = self.make_request('GET', '/accomplishments')
        
        if success and isinstance(data, list):
            return self.log_test("Get Accomplishments", True, f"- {len(data)} accomplishments earned")
        else:
            return self.log_test("Get Accomplishments", False, f"- {data.get('error', data)}")

    def test_get_stats(self):
        """Test getting global stats"""
        success, data = self.make_request('GET', '/stats')
        
        if success and 'total_users' in data:
            return self.log_test("Get Stats", True, 
                               f"- Users: {data['total_users']}, Songs: {data['total_songs_performed']}, Queue: {data['current_queue_length']}")
        else:
            return self.log_test("Get Stats", False, f"- {data.get('error', data)}")

    def test_get_ranks(self):
        """Test getting ranks info"""
        success, data = self.make_request('GET', '/ranks')
        
        if success and isinstance(data, list):
            rank_names = [rank.get('name', 'Unknown') for rank in data[:3]]
            return self.log_test("Get Ranks", True, f"- {len(data)} ranks: {', '.join(rank_names)}...")
        else:
            return self.log_test("Get Ranks", False, f"- {data.get('error', data)}")

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "invalid@example.com",
            "password": "wrongpassword"
        }
        
        success, data = self.make_request('POST', '/auth/login', login_data, expected_status=401)
        
        if not success and 'detail' in data:  # Expected to fail with 401
            return self.log_test("Invalid Login", True, f"- Correctly rejected: {data['detail']}")
        else:
            return self.log_test("Invalid Login", False, "- Should have rejected invalid credentials")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🎤 Starting King Klub API Testing...")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity
        self.test_root_endpoint()
        
        # Authentication flow
        self.test_user_registration()
        self.test_user_login()
        self.test_get_user_info()
        self.test_invalid_login()
        
        # Queue management
        self.test_get_queue()
        self.test_add_to_queue()
        self.test_add_duplicate_queue()
        self.test_remove_from_queue()
        
        # Data retrieval
        self.test_get_leaderboard()
        self.test_get_badges()
        self.test_get_accomplishments()
        self.test_get_stats()
        self.test_get_ranks()
        
        # Results
        print("=" * 60)
        print(f"🏆 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("✅ All tests passed! King Klub API is working perfectly!")
            return 0
        else:
            print("❌ Some tests failed. Please check the API implementation.")
            return 1


def main():
    """Main test execution"""
    tester = KingKlubAPITester()
    return tester.run_all_tests()


if __name__ == "__main__":
    sys.exit(main())