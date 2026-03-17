"""
King Klub Backend Tests - Queue Song Limit (5 songs per 30-minute window)
Tests: Check-in flow, Queue status, Song limit enforcement, Window reset info
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
ADMIN_EMAIL = "admin@kingkaraoke2025.com"
ADMIN_PASSWORD = "admin123"

# Unique test user for this test run
TEST_USER_EMAIL = f"TEST_queue_limit_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "testpass123"
TEST_USER_NAME = "TEST Queue Limit User"


class TestCheckinRequired:
    """Tests that check-in is required before adding songs"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def new_test_user(self):
        """Create a fresh test user for testing queue limit"""
        # Generate unique email each time
        unique_email = f"TEST_queue_{uuid.uuid4().hex[:8]}@example.com"
        
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "display_name": f"TEST Queue User {uuid.uuid4().hex[:4]}"
        })
        
        if register_resp.status_code == 200:
            data = register_resp.json()
            return data["token"], data["user"]["id"], unique_email
        
        pytest.skip(f"Cannot create test user: {register_resp.text}")
    
    def test_queue_status_without_checkin(self, new_test_user):
        """Test that new user without check-in shows proper status"""
        token, user_id, email = new_test_user
        
        response = requests.get(f"{BASE_URL}/api/queue/my-status", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # User should NOT be checked in
        assert data["checked_in"] == False
        assert data["can_add_songs"] == False
        assert data["reason"] == "Please check in with the QR code first"
        assert data["songs_this_window"] == 0
        assert data["max_songs_per_window"] == 5
        
        print(f"SUCCESS: Queue status shows not checked in - {data['reason']}")
    
    def test_add_song_without_checkin_fails(self, new_test_user):
        """Test that adding song without check-in returns proper error"""
        token, user_id, email = new_test_user
        
        response = requests.post(f"{BASE_URL}/api/queue", json={
            "song_title": "Test Song",
            "artist": "Test Artist"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "check in" in data["detail"].lower() or "qr code" in data["detail"].lower()
        
        print(f"SUCCESS: Add song without check-in blocked - {data['detail']}")


class TestCheckinFlow:
    """Tests for check-in functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def venue_code(self, admin_token):
        """Get today's venue code for check-in"""
        response = requests.get(f"{BASE_URL}/api/venue/qr-data", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        return response.json()["venue_code"]
    
    @pytest.fixture
    def new_test_user(self):
        """Create a fresh test user"""
        unique_email = f"TEST_checkin_{uuid.uuid4().hex[:8]}@example.com"
        
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "display_name": f"TEST Checkin User {uuid.uuid4().hex[:4]}"
        })
        
        if register_resp.status_code == 200:
            data = register_resp.json()
            return data["token"], data["user"]["id"], unique_email
        
        pytest.skip(f"Cannot create test user: {register_resp.text}")
    
    def test_valid_checkin(self, new_test_user, venue_code):
        """Test that valid check-in works correctly"""
        token, user_id, email = new_test_user
        
        response = requests.post(f"{BASE_URL}/api/checkin/{venue_code}", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # First check-in should succeed
        if data.get("already_checked_in"):
            print(f"INFO: User already checked in today")
        else:
            assert "points_awarded" in data
            print(f"SUCCESS: Check-in successful - Points awarded: {data.get('points_awarded', 0)}")
    
    def test_duplicate_checkin_blocked(self, new_test_user, venue_code):
        """Test that duplicate check-in is properly handled"""
        token, user_id, email = new_test_user
        
        # First check-in
        first_response = requests.post(f"{BASE_URL}/api/checkin/{venue_code}", headers={
            "Authorization": f"Bearer {token}"
        })
        assert first_response.status_code == 200
        
        # Second check-in attempt
        second_response = requests.post(f"{BASE_URL}/api/checkin/{venue_code}", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert second_response.status_code == 200
        data = second_response.json()
        assert data.get("already_checked_in") == True
        assert data.get("points_awarded") == 0
        
        print(f"SUCCESS: Duplicate check-in blocked - {data.get('message')}")
    
    def test_invalid_venue_code_rejected(self, new_test_user):
        """Test that invalid venue code is rejected"""
        token, user_id, email = new_test_user
        
        response = requests.post(f"{BASE_URL}/api/checkin/invalid_code_123", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower() or "expired" in data["detail"].lower()
        
        print(f"SUCCESS: Invalid venue code rejected - {data['detail']}")


class TestSongLimitEnforcement:
    """Tests for the 5-song per 30-minute window limit"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def venue_code(self, admin_token):
        """Get today's venue code"""
        response = requests.get(f"{BASE_URL}/api/venue/qr-data", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        return response.json()["venue_code"]
    
    @pytest.fixture
    def checked_in_user(self, venue_code):
        """Create a fresh test user and check them in"""
        # Create unique user
        unique_email = f"TEST_songlimit_{uuid.uuid4().hex[:8]}@example.com"
        display_name = f"TEST Song Limit User {uuid.uuid4().hex[:4]}"
        
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "display_name": display_name
        })
        
        if register_resp.status_code != 200:
            pytest.skip(f"Cannot create test user: {register_resp.text}")
        
        token = register_resp.json()["token"]
        user_id = register_resp.json()["user"]["id"]
        
        # Check in the user
        checkin_resp = requests.post(f"{BASE_URL}/api/checkin/{venue_code}", headers={
            "Authorization": f"Bearer {token}"
        })
        assert checkin_resp.status_code == 200
        
        return token, user_id, unique_email, display_name
    
    def test_add_first_song_success(self, checked_in_user):
        """Test that first song can be added after check-in"""
        token, user_id, email, name = checked_in_user
        
        response = requests.post(f"{BASE_URL}/api/queue", json={
            "song_title": "First Test Song",
            "artist": "Test Artist 1"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert data["song_title"] == "First Test Song"
        assert data["artist"] == "Test Artist 1"
        assert data["songs_this_window"] == 1
        assert data["songs_remaining"] == 4
        assert "window_resets_in" in data
        
        print(f"SUCCESS: First song added - {data['songs_remaining']} songs remaining, window resets in {data['window_resets_in']} min")
    
    def test_add_five_songs_exhausts_limit(self, checked_in_user):
        """Test that user can add exactly 5 songs"""
        token, user_id, email, name = checked_in_user
        
        songs = [
            ("Song One", "Artist 1"),
            ("Song Two", "Artist 2"),
            ("Song Three", "Artist 3"),
            ("Song Four", "Artist 4"),
            ("Song Five", "Artist 5"),
        ]
        
        for i, (title, artist) in enumerate(songs):
            response = requests.post(f"{BASE_URL}/api/queue", json={
                "song_title": title,
                "artist": artist
            }, headers={
                "Authorization": f"Bearer {token}"
            })
            
            assert response.status_code == 200, f"Song {i+1} should be added successfully"
            data = response.json()
            
            assert data["songs_this_window"] == i + 1
            assert data["songs_remaining"] == 4 - i
            
            print(f"  Song {i+1}: {title} - songs_this_window={data['songs_this_window']}, remaining={data['songs_remaining']}")
        
        # Final verification
        status_resp = requests.get(f"{BASE_URL}/api/queue/my-status", headers={
            "Authorization": f"Bearer {token}"
        })
        assert status_resp.status_code == 200
        status = status_resp.json()
        
        assert status["songs_this_window"] == 5
        assert status["songs_remaining"] == 0
        assert status["can_add_songs"] == False
        
        print(f"SUCCESS: All 5 songs added, limit reached - can_add_songs={status['can_add_songs']}")
    
    def test_sixth_song_blocked(self, checked_in_user):
        """Test that 6th song is blocked after adding 5"""
        token, user_id, email, name = checked_in_user
        
        # Add 5 songs first
        for i in range(5):
            requests.post(f"{BASE_URL}/api/queue", json={
                "song_title": f"Song {i+1}",
                "artist": f"Artist {i+1}"
            }, headers={
                "Authorization": f"Bearer {token}"
            })
        
        # Try to add 6th song
        response = requests.post(f"{BASE_URL}/api/queue", json={
            "song_title": "Sixth Song",
            "artist": "Blocked Artist"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 400
        data = response.json()
        
        assert "5 songs" in data["detail"].lower() or "limit" in data["detail"].lower()
        assert "resets" in data["detail"].lower()
        
        print(f"SUCCESS: 6th song blocked correctly - {data['detail']}")


class TestQueueStatusEndpoint:
    """Tests for GET /api/queue/my-status endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def venue_code(self, admin_token):
        """Get today's venue code"""
        response = requests.get(f"{BASE_URL}/api/venue/qr-data", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        return response.json()["venue_code"]
    
    @pytest.fixture
    def checked_in_user(self, venue_code):
        """Create and check in a test user"""
        unique_email = f"TEST_status_{uuid.uuid4().hex[:8]}@example.com"
        
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "display_name": f"TEST Status User {uuid.uuid4().hex[:4]}"
        })
        
        if register_resp.status_code != 200:
            pytest.skip(f"Cannot create test user: {register_resp.text}")
        
        token = register_resp.json()["token"]
        user_id = register_resp.json()["user"]["id"]
        
        # Check in
        requests.post(f"{BASE_URL}/api/checkin/{venue_code}", headers={
            "Authorization": f"Bearer {token}"
        })
        
        return token, user_id, unique_email
    
    def test_queue_status_after_checkin(self, checked_in_user):
        """Test queue status endpoint returns correct data after check-in"""
        token, user_id, email = checked_in_user
        
        response = requests.get(f"{BASE_URL}/api/queue/my-status", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert data["checked_in"] == True
        assert "checkin_time" in data
        assert "minutes_since_checkin" in data
        assert data["current_window"] >= 1
        assert "window_resets_in" in data
        assert data["can_add_songs"] == True
        assert data["songs_this_window"] == 0
        assert data["songs_remaining"] == 5
        assert data["max_songs_per_window"] == 5
        assert "my_songs" in data
        
        print(f"SUCCESS: Queue status verified - current_window={data['current_window']}, resets_in={data['window_resets_in']}min")
    
    def test_queue_status_after_adding_songs(self, checked_in_user):
        """Test queue status updates correctly after adding songs"""
        token, user_id, email = checked_in_user
        
        # Add 3 songs
        for i in range(3):
            requests.post(f"{BASE_URL}/api/queue", json={
                "song_title": f"Status Test Song {i+1}",
                "artist": f"Artist {i+1}"
            }, headers={
                "Authorization": f"Bearer {token}"
            })
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/queue/my-status", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["songs_this_window"] == 3
        assert data["songs_remaining"] == 2
        assert data["can_add_songs"] == True
        assert len(data["my_songs"]) == 3
        
        print(f"SUCCESS: Queue status shows 3 songs added, {data['songs_remaining']} remaining")
    
    def test_queue_status_shows_limit_reason(self, checked_in_user):
        """Test that status shows proper reason when limit reached"""
        token, user_id, email = checked_in_user
        
        # Add 5 songs
        for i in range(5):
            requests.post(f"{BASE_URL}/api/queue", json={
                "song_title": f"Limit Test Song {i+1}",
                "artist": f"Artist {i+1}"
            }, headers={
                "Authorization": f"Bearer {token}"
            })
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/queue/my-status", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["can_add_songs"] == False
        assert data["songs_remaining"] == 0
        assert data["reason"] is not None
        assert "5 song limit" in data["reason"] or "resets" in data["reason"].lower()
        
        print(f"SUCCESS: Queue status shows limit reached - reason: {data['reason']}")


class TestMessageToAdmin:
    """Tests for message_to_admin field"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def venue_code(self, admin_token):
        """Get venue code"""
        response = requests.get(f"{BASE_URL}/api/venue/qr-data", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        return response.json()["venue_code"]
    
    @pytest.fixture
    def checked_in_user(self, venue_code):
        """Create and check in a test user"""
        unique_email = f"TEST_msg_{uuid.uuid4().hex[:8]}@example.com"
        
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": TEST_USER_PASSWORD,
            "display_name": f"TEST Msg User {uuid.uuid4().hex[:4]}"
        })
        
        if register_resp.status_code != 200:
            pytest.skip(f"Cannot create test user: {register_resp.text}")
        
        token = register_resp.json()["token"]
        user_id = register_resp.json()["user"]["id"]
        
        requests.post(f"{BASE_URL}/api/checkin/{venue_code}", headers={
            "Authorization": f"Bearer {token}"
        })
        
        return token, user_id
    
    def test_add_song_with_message(self, checked_in_user):
        """Test adding song with message to admin"""
        token, user_id = checked_in_user
        
        response = requests.post(f"{BASE_URL}/api/queue", json={
            "song_title": "Birthday Song",
            "artist": "Happy Artist",
            "message_to_admin": "It's my friend's birthday!"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message_to_admin"] == "It's my friend's birthday!"
        
        print(f"SUCCESS: Song added with message to admin")
    
    def test_message_truncated_at_250_chars(self, checked_in_user):
        """Test that message is truncated at 250 characters"""
        token, user_id = checked_in_user
        
        long_message = "A" * 300  # 300 characters
        
        response = requests.post(f"{BASE_URL}/api/queue", json={
            "song_title": "Long Message Song",
            "artist": "Test Artist",
            "message_to_admin": long_message
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Message should be truncated to 250 chars
        assert len(data["message_to_admin"]) == 250
        
        print(f"SUCCESS: Long message truncated to 250 characters")


class TestExistingUserWithCheckin:
    """Tests using existing user that may already be checked in"""
    
    def test_existing_user_royaltest_status(self):
        """Test queue status for existing royaltest user"""
        # Login as existing user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "royaltest@example.com",
            "password": "password123"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        
        # Check queue status
        response = requests.get(f"{BASE_URL}/api/queue/my-status", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\n=== Existing User Queue Status ===")
        print(f"  checked_in: {data.get('checked_in')}")
        print(f"  can_add_songs: {data.get('can_add_songs')}")
        print(f"  songs_this_window: {data.get('songs_this_window')}")
        print(f"  songs_remaining: {data.get('songs_remaining')}")
        print(f"  current_window: {data.get('current_window')}")
        print(f"  window_resets_in: {data.get('window_resets_in')} min")
        print(f"  reason: {data.get('reason')}")
        print(f"  total_songs_in_queue: {data.get('total_songs_in_queue')}")
        
        # Assert expected structure
        assert "checked_in" in data
        assert "can_add_songs" in data
        assert "songs_this_window" in data
        assert "max_songs_per_window" in data
        assert data["max_songs_per_window"] == 5
        
        print(f"\nSUCCESS: Queue status endpoint returns valid data")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
