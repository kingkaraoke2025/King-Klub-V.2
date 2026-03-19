"""
King Klub Backend Tests - Badge Awarding System
Tests: Badge award logic via /api/admin/award-points endpoint
Categories: Performance, Challenge, Social, Loyalty, Generosity
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
ADMIN_EMAIL = "admin@kingkaraoke2025.com"
ADMIN_PASSWORD = "admin123"

# Test user for badge testing (fresh user each test run)
TEST_BADGE_USER_EMAIL = f"TEST_badge_user_{uuid.uuid4().hex[:8]}@example.com"
TEST_BADGE_USER_PASSWORD = "badgetest123"
TEST_BADGE_USER_NAME = f"TEST Badge User {uuid.uuid4().hex[:4]}"


class TestBadgeAwardingSetup:
    """Setup tests - verify API access and create test user"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        return {"token": data["token"], "user_id": data["user"]["id"]}
    
    def test_api_accessible(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print(f"SUCCESS: API accessible at {BASE_URL}")
    
    def test_admin_login(self, admin_auth):
        """Verify admin can login"""
        assert admin_auth["token"] is not None
        print(f"SUCCESS: Admin logged in")
    
    def test_point_actions_endpoint(self):
        """Verify point actions endpoint returns all actions"""
        response = requests.get(f"{BASE_URL}/api/point-actions")
        assert response.status_code == 200
        data = response.json()
        
        expected_actions = [
            "sing_song", "bring_friend", "sing_blindfolded", "three_nights", 
            "five_nights", "random_song", "sing_duet", "tiktok_post",
            "follow_tiktok", "follow_facebook", "tip_kj", "tip_bartender", "bar_song"
        ]
        
        action_ids = [a["id"] for a in data]
        for action in expected_actions:
            assert action in action_ids, f"Missing action: {action}"
        
        print(f"SUCCESS: All {len(expected_actions)} point actions available")


class TestBadgeAwarding:
    """Core badge awarding tests via /api/admin/award-points"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        return {"token": data["token"], "user_id": data["user"]["id"]}
    
    @pytest.fixture(scope="class")
    def test_user(self, admin_auth):
        """Create a fresh test user for badge testing"""
        email = f"TEST_badge_{uuid.uuid4().hex[:8]}@example.com"
        password = "badgetest123"
        name = f"TEST BadgeTester {uuid.uuid4().hex[:4]}"
        
        # Register new user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": password,
            "display_name": name
        })
        
        assert response.status_code == 200, f"Failed to create test user: {response.text}"
        data = response.json()
        
        print(f"SUCCESS: Created test user '{name}' (ID: {data['user']['id']})")
        
        return {
            "id": data["user"]["id"],
            "email": email,
            "name": name,
            "token": data["token"]
        }
    
    # ==================== PERFORMANCE BADGES ====================
    
    def test_first_song_badge_after_1_song(self, admin_auth, test_user):
        """Test: sing_song action awards 'first_song' badge after 1 song"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "sing_song",
                "notes": "Test first song"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        # Verify first_song badge was awarded
        assert "first_song" in data["badges_earned"], f"first_song badge not awarded. Badges earned: {data['badges_earned']}"
        assert data["points_awarded"] == 10  # Base points for sing_song
        
        # Verify badge bonus points included
        assert data["bonus_points"] >= 10  # first_song badge reward is 10 points
        
        print(f"SUCCESS: first_song badge awarded. Points: {data['points_awarded']}, Bonus: {data['bonus_points']}")
    
    def test_five_songs_badge_after_5_songs(self, admin_auth, test_user):
        """Test: sing_song action awards 'five_songs' badge after 5 total songs"""
        # Award 4 more songs (already have 1 from previous test)
        for i in range(4):
            response = requests.post(
                f"{BASE_URL}/api/admin/award-points",
                json={
                    "user_id": test_user["id"],
                    "action_id": "sing_song",
                    "notes": f"Test song {i+2}"
                },
                headers={"Authorization": f"Bearer {admin_auth['token']}"}
            )
            assert response.status_code == 200, f"Award points failed on song {i+2}: {response.text}"
        
        # Get user data to verify
        user_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert user_response.status_code == 200
        user_data = user_response.json()
        
        assert "five_songs" in user_data["badges"], f"five_songs badge not in user badges: {user_data['badges']}"
        assert user_data["songs_performed"] >= 5, f"Songs performed: {user_data['songs_performed']}"
        
        print(f"SUCCESS: five_songs badge awarded. Total songs: {user_data['songs_performed']}")
    
    # ==================== CHALLENGE BADGES ====================
    
    def test_blindfolded_master_badge(self, admin_auth, test_user):
        """Test: sing_blindfolded action awards 'blindfolded_master' badge"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "sing_blindfolded",
                "notes": "Test blindfolded performance"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "blindfolded_master" in data["badges_earned"], f"blindfolded_master badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 250  # sing_blindfolded points
        
        print(f"SUCCESS: blindfolded_master badge awarded. Points: {data['points_awarded']}")
    
    def test_random_warrior_badge(self, admin_auth, test_user):
        """Test: random_song action awards 'random_warrior' badge"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "random_song",
                "notes": "Test random song challenge"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "random_warrior" in data["badges_earned"], f"random_warrior badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 200  # random_song points
        
        print(f"SUCCESS: random_warrior badge awarded. Points: {data['points_awarded']}")
    
    def test_bar_song_hero_badge(self, admin_auth, test_user):
        """Test: bar_song action awards 'bar_song_hero' badge"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "bar_song",
                "notes": "Test bar song performance"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "bar_song_hero" in data["badges_earned"], f"bar_song_hero badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 100  # bar_song points
        
        print(f"SUCCESS: bar_song_hero badge awarded. Points: {data['points_awarded']}")
    
    # ==================== SOCIAL BADGES ====================
    
    def test_duet_singer_badge_after_1_duet(self, admin_auth, test_user):
        """Test: sing_duet action awards 'duet_singer' badge after 1 duet"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "sing_duet",
                "notes": "Test duet performance"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "duet_singer" in data["badges_earned"], f"duet_singer badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 10  # sing_duet points
        
        print(f"SUCCESS: duet_singer badge awarded. Points: {data['points_awarded']}")
    
    def test_influencer_badge(self, admin_auth, test_user):
        """Test: tiktok_post action awards 'influencer' badge"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "tiktok_post",
                "notes": "Test TikTok post"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "influencer" in data["badges_earned"], f"influencer badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 200  # tiktok_post points
        
        print(f"SUCCESS: influencer badge awarded. Points: {data['points_awarded']}")
    
    def test_super_fan_badge_after_following_both(self, admin_auth, test_user):
        """Test: follow_tiktok + follow_facebook awards 'super_fan' badge"""
        # First follow TikTok
        response1 = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "follow_tiktok",
                "notes": "Test follow TikTok"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert response1.status_code == 200, f"Follow TikTok failed: {response1.text}"
        
        # Then follow Facebook - should trigger super_fan badge
        response2 = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "follow_facebook",
                "notes": "Test follow Facebook"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert response2.status_code == 200, f"Follow Facebook failed: {response2.text}"
        data = response2.json()
        
        assert "super_fan" in data["badges_earned"], f"super_fan badge not awarded: {data['badges_earned']}"
        
        print(f"SUCCESS: super_fan badge awarded after following both TikTok and Facebook")
    
    # ==================== GENEROSITY BADGES ====================
    
    def test_generous_tipper_badge_after_1_tip(self, admin_auth, test_user):
        """Test: tip_kj action awards 'generous_tipper' badge after 1 tip"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "tip_kj",
                "notes": "Test KJ tip"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "generous_tipper" in data["badges_earned"], f"generous_tipper badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 10  # tip_kj points
        
        print(f"SUCCESS: generous_tipper badge awarded. Points: {data['points_awarded']}")
    
    def test_benevolent_tipper_badge_after_1_bartender_tip(self, admin_auth, test_user):
        """Test: tip_bartender action awards 'benevolent_tipper' badge after 1 tip"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "tip_bartender",
                "notes": "Test bartender tip"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "benevolent_tipper" in data["badges_earned"], f"benevolent_tipper badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 10  # tip_bartender points
        
        print(f"SUCCESS: benevolent_tipper badge awarded. Points: {data['points_awarded']}")
    
    # ==================== LOYALTY BADGES ====================
    
    def test_night_owl_badge_after_three_nights(self, admin_auth, test_user):
        """Test: three_nights action awards 'night_owl' badge (3 consecutive visits)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={
                "user_id": test_user["id"],
                "action_id": "three_nights",
                "notes": "Test 3 consecutive nights"
            },
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 200, f"Award points failed: {response.text}"
        data = response.json()
        
        assert "night_owl" in data["badges_earned"], f"night_owl badge not awarded: {data['badges_earned']}"
        assert data["points_awarded"] == 25  # three_nights points
        
        # Verify consecutive_visits was set
        user_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["consecutive_visits"] >= 3, f"consecutive_visits not updated: {user_data['consecutive_visits']}"
        
        print(f"SUCCESS: night_owl badge awarded. Consecutive visits: {user_data['consecutive_visits']}")


class TestBadgeVerification:
    """Verify badges appear on user profile and accomplishments"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return {"token": response.json()["token"], "user_id": response.json()["user"]["id"]}
    
    @pytest.fixture(scope="class")
    def badged_user(self, admin_auth):
        """Create a user and award them badges"""
        email = f"TEST_badged_{uuid.uuid4().hex[:8]}@example.com"
        
        # Register new user
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "badgetest123",
            "display_name": f"TEST BadgedUser {uuid.uuid4().hex[:4]}"
        })
        assert response.status_code == 200
        user_data = response.json()
        user_id = user_data["user"]["id"]
        user_token = user_data["token"]
        
        # Award several badges
        badges_to_award = ["sing_song", "sing_blindfolded", "tip_kj"]
        for action in badges_to_award:
            requests.post(
                f"{BASE_URL}/api/admin/award-points",
                json={"user_id": user_id, "action_id": action},
                headers={"Authorization": f"Bearer {admin_auth['token']}"}
            )
        
        return {"id": user_id, "token": user_token}
    
    def test_badges_appear_on_user_profile(self, badged_user):
        """Verify badges appear on user's profile via /auth/me"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {badged_user['token']}"}
        )
        
        assert response.status_code == 200
        user_data = response.json()
        
        # Should have at least first_song, blindfolded_master, and generous_tipper badges
        expected_badges = ["first_song", "blindfolded_master", "generous_tipper"]
        for badge in expected_badges:
            assert badge in user_data["badges"], f"Badge '{badge}' not in user profile: {user_data['badges']}"
        
        print(f"SUCCESS: All expected badges found on user profile: {user_data['badges']}")
    
    def test_accomplishments_recorded_in_database(self, badged_user):
        """Verify accomplishments are recorded when badges are earned"""
        response = requests.get(
            f"{BASE_URL}/api/accomplishments",
            headers={"Authorization": f"Bearer {badged_user['token']}"}
        )
        
        assert response.status_code == 200
        accomplishments = response.json()
        
        # Should have accomplishment records for earned badges
        assert len(accomplishments) >= 3, f"Expected at least 3 accomplishments, got {len(accomplishments)}"
        
        # Verify accomplishment structure
        for acc in accomplishments:
            assert "badge_id" in acc, "Accomplishment missing badge_id"
            assert "badge_name" in acc, "Accomplishment missing badge_name"
            assert "earned_at" in acc, "Accomplishment missing earned_at"
            assert "user_id" in acc, "Accomplishment missing user_id"
        
        badge_ids = [acc["badge_id"] for acc in accomplishments]
        print(f"SUCCESS: Found {len(accomplishments)} accomplishments: {badge_ids}")


class TestBadgeEdgeCases:
    """Edge case tests for badge awarding"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return {"token": response.json()["token"]}
    
    def test_badge_not_awarded_twice(self, admin_auth):
        """Test: Same badge is not awarded multiple times"""
        # Create fresh user
        email = f"TEST_double_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "test123",
            "display_name": f"TEST DoubleBadge {uuid.uuid4().hex[:4]}"
        })
        assert response.status_code == 200
        user_id = response.json()["user"]["id"]
        user_token = response.json()["token"]
        
        # Award blindfolded performance twice
        resp1 = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={"user_id": user_id, "action_id": "sing_blindfolded"},
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert "blindfolded_master" in data1["badges_earned"]
        
        resp2 = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={"user_id": user_id, "action_id": "sing_blindfolded"},
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert "blindfolded_master" not in data2["badges_earned"], "Badge awarded twice!"
        
        # Verify user only has one instance of the badge
        user_resp = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        user_data = user_resp.json()
        badge_count = user_data["badges"].count("blindfolded_master")
        assert badge_count == 1, f"Badge appears {badge_count} times in user badges"
        
        print("SUCCESS: Badge not awarded multiple times")
    
    def test_invalid_action_id_rejected(self, admin_auth):
        """Test: Invalid action_id returns error"""
        # Get any user ID
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert response.status_code == 200
        users = response.json()
        if len(users) == 0:
            pytest.skip("No users available")
        
        user_id = users[0]["id"]
        
        # Try invalid action
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={"user_id": user_id, "action_id": "invalid_action_xyz"},
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Invalid action ID" in response.json().get("detail", "")
        
        print("SUCCESS: Invalid action_id correctly rejected")
    
    def test_nonexistent_user_rejected(self, admin_auth):
        """Test: Awarding points to non-existent user returns error"""
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={"user_id": "nonexistent-user-id-123", "action_id": "sing_song"},
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        assert "User not found" in response.json().get("detail", "")
        
        print("SUCCESS: Non-existent user correctly rejected")
    
    def test_requires_admin_auth(self):
        """Test: award-points endpoint requires admin authentication"""
        # Login as regular user
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "royaltest@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        user_token = response.json()["token"]
        user_id = response.json()["user"]["id"]
        
        # Try to award points as regular user
        response = requests.post(
            f"{BASE_URL}/api/admin/award-points",
            json={"user_id": user_id, "action_id": "sing_song"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        
        print("SUCCESS: Admin authentication correctly required")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_auth(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return {"token": response.json()["token"]}
    
    def test_cleanup_test_users(self, admin_auth):
        """Cleanup TEST_ prefixed users created during testing"""
        # Get all users
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_auth['token']}"}
        )
        assert response.status_code == 200
        users = response.json()
        
        deleted_count = 0
        for user in users:
            if user.get("email", "").startswith("TEST_") or user.get("display_name", "").startswith("TEST"):
                delete_resp = requests.delete(
                    f"{BASE_URL}/api/admin/users/{user['id']}",
                    headers={"Authorization": f"Bearer {admin_auth['token']}"}
                )
                if delete_resp.status_code == 200:
                    deleted_count += 1
        
        print(f"SUCCESS: Cleaned up {deleted_count} test users")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
