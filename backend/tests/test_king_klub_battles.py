"""
King Klub Backend Tests - Battle/Challenge System & Core Features
Tests: Auth flows, Battle creation, Voting, Leaderboard, QR Check-in
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
USER_EMAIL = "royaltest@example.com"
USER_PASSWORD = "password123"
ADMIN_EMAIL = "admin@kingkaraoke2025.com"
ADMIN_PASSWORD = "admin123"

# Test user for opponent
TEST_OPPONENT_EMAIL = "TEST_opponent@example.com"
TEST_OPPONENT_PASSWORD = "testpass123"
TEST_OPPONENT_NAME = "TEST Opponent"


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_api_root_accessible(self):
        """Test API root endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "King Klub API"
        print("SUCCESS: API root accessible")

    def test_user_login_success(self):
        """Test user login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == USER_EMAIL
        assert "rank" in data["user"]
        print(f"SUCCESS: User login - {data['user']['display_name']}, Rank: {data['user']['rank']['name']}")
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"SUCCESS: Admin login - {data['user']['display_name']}, is_admin: {data['user']['is_admin']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("SUCCESS: Invalid login correctly returns 401")

    def test_auth_me_with_valid_token(self):
        """Test /auth/me endpoint with valid token"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        
        # Then call /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == USER_EMAIL
        print(f"SUCCESS: /auth/me returns user data - {data['display_name']}")


class TestLeaderboard:
    """Leaderboard endpoint tests"""
    
    def test_leaderboard_accessible(self):
        """Test leaderboard endpoint returns user rankings"""
        response = requests.get(f"{BASE_URL}/api/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "position" in data[0]
            assert "display_name" in data[0]
            assert "points" in data[0]
            assert "rank" in data[0]
        print(f"SUCCESS: Leaderboard returns {len(data)} users")


class TestChallengeTypes:
    """Challenge types endpoint tests"""
    
    def test_challenge_types_accessible(self):
        """Test challenge types endpoint"""
        response = requests.get(f"{BASE_URL}/api/challenges/types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5  # Should have 5 challenge types
        
        # Verify expected types exist
        type_ids = [t["id"] for t in data]
        expected_types = ["royal_duel", "blind_challenge", "rank_battle", "roulette", "harmony_duel"]
        for expected in expected_types:
            assert expected in type_ids, f"Missing challenge type: {expected}"
        print(f"SUCCESS: {len(data)} challenge types available")


class TestBattleChallengeSystem:
    """Battle/Challenge system tests"""
    
    @pytest.fixture
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"], response.json()["user"]["id"]
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"], response.json()["user"]["id"]
    
    @pytest.fixture
    def opponent_token(self):
        """Create or login test opponent user"""
        # Try login first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_OPPONENT_EMAIL,
            "password": TEST_OPPONENT_PASSWORD
        })
        
        if login_resp.status_code == 200:
            return login_resp.json()["token"], login_resp.json()["user"]["id"]
        
        # If login fails, try to register
        register_resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_OPPONENT_EMAIL,
            "password": TEST_OPPONENT_PASSWORD,
            "display_name": TEST_OPPONENT_NAME
        })
        
        if register_resp.status_code == 200:
            return register_resp.json()["token"], register_resp.json()["user"]["id"]
        
        # If both fail, skip test
        pytest.skip(f"Cannot create opponent user: {register_resp.text}")
    
    def test_get_active_challenges(self, user_token):
        """Test getting active challenges"""
        token, user_id = user_token
        response = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Got {len(data)} active challenges")
    
    def test_get_my_challenges(self, user_token):
        """Test getting user's own challenges"""
        token, user_id = user_token
        response = requests.get(f"{BASE_URL}/api/challenges/my", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Got {len(data)} challenges for user")
    
    def test_create_challenge(self, user_token, opponent_token):
        """Test creating a new challenge"""
        token, user_id = user_token
        opponent_tok, opponent_id = opponent_token
        
        response = requests.post(f"{BASE_URL}/api/challenges", json={
            "opponent_id": opponent_id,
            "challenge_type": "royal_duel"
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        # Could be 200 or 400 if challenge already exists
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "message" in data
            print(f"SUCCESS: Challenge created - {data['message']}")
            return data["id"]
        elif response.status_code == 400:
            # Already have an active challenge
            print(f"INFO: Challenge creation skipped - {response.json().get('detail', 'active challenge exists')}")
            return None
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")
    
    def test_accept_challenge(self, user_token, opponent_token):
        """Test accepting a pending challenge"""
        user_tok, user_id = user_token
        opponent_tok, opponent_id = opponent_token
        
        # First, create a challenge from user to opponent
        create_resp = requests.post(f"{BASE_URL}/api/challenges", json={
            "opponent_id": opponent_id,
            "challenge_type": "royal_duel"
        }, headers={
            "Authorization": f"Bearer {user_tok}"
        })
        
        if create_resp.status_code != 200:
            # Get existing challenges for opponent
            my_challenges = requests.get(f"{BASE_URL}/api/challenges/my", headers={
                "Authorization": f"Bearer {opponent_tok}"
            })
            pending = [c for c in my_challenges.json() if c["status"] == "pending" and c["opponent_id"] == opponent_id]
            
            if len(pending) == 0:
                print("INFO: No pending challenges to accept")
                return
            
            challenge_id = pending[0]["id"]
        else:
            challenge_id = create_resp.json()["id"]
        
        # Accept the challenge as opponent
        accept_resp = requests.post(f"{BASE_URL}/api/challenges/{challenge_id}/accept", headers={
            "Authorization": f"Bearer {opponent_tok}"
        })
        
        if accept_resp.status_code == 200:
            print("SUCCESS: Challenge accepted")
        elif accept_resp.status_code == 400:
            print(f"INFO: Challenge state issue - {accept_resp.json().get('detail', 'unknown')}")
        else:
            print(f"INFO: Accept response - {accept_resp.status_code}: {accept_resp.text}")


class TestVotingSystem:
    """Voting system tests"""
    
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
    def user_token(self):
        """Get user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"], response.json()["user"]["id"]
    
    def test_get_voting_open_status(self):
        """Test checking if voting is open"""
        response = requests.get(f"{BASE_URL}/api/challenges/voting-open")
        assert response.status_code == 200
        data = response.json()
        assert "voting_open" in data
        print(f"SUCCESS: Voting status check - voting_open: {data['voting_open']}")
    
    def test_open_voting_admin(self, admin_token):
        """Test opening voting (admin only) on an accepted challenge"""
        # First get active challenges
        challenges_resp = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert challenges_resp.status_code == 200
        
        accepted_challenges = [c for c in challenges_resp.json() if c["status"] == "accepted"]
        
        if len(accepted_challenges) == 0:
            print("INFO: No accepted challenges to open voting on")
            return
        
        challenge_id = accepted_challenges[0]["id"]
        
        # Open voting
        response = requests.post(f"{BASE_URL}/api/challenges/{challenge_id}/open-voting", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        if response.status_code == 200:
            print("SUCCESS: Voting opened for challenge")
        else:
            print(f"INFO: Open voting response - {response.status_code}: {response.text}")
    
    def test_close_voting_admin(self, admin_token):
        """Test closing voting (admin only)"""
        # Check if any voting is open
        voting_status = requests.get(f"{BASE_URL}/api/challenges/voting-open")
        if not voting_status.json().get("voting_open"):
            print("INFO: No voting is currently open to close")
            return
        
        challenge_id = voting_status.json()["challenge"]["id"]
        
        response = requests.post(f"{BASE_URL}/api/challenges/{challenge_id}/close-voting", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200
        print("SUCCESS: Voting closed")
    
    def test_vote_endpoint(self, user_token, admin_token):
        """Test voting for a performer in a battle"""
        token, user_id = user_token
        
        # Get active challenges
        challenges_resp = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {token}"
        })
        accepted = [c for c in challenges_resp.json() if c["status"] == "accepted"]
        
        if len(accepted) == 0:
            print("INFO: No accepted challenges to vote on")
            return
        
        challenge = accepted[0]
        
        # Skip if user is participant
        if user_id in [challenge["challenger_id"], challenge["opponent_id"]]:
            print("INFO: User is participant, cannot vote")
            return
        
        # Try to vote
        response = requests.post(f"{BASE_URL}/api/challenges/{challenge['id']}/vote", json={
            "vote_for": challenge["challenger_id"]
        }, headers={
            "Authorization": f"Bearer {token}"
        })
        
        if response.status_code == 200:
            print(f"SUCCESS: Vote recorded - {response.json().get('message')}")
        elif response.status_code == 400:
            print(f"INFO: Vote status - {response.json().get('detail')}")
        else:
            print(f"INFO: Vote response - {response.status_code}: {response.text}")


class TestQRCheckin:
    """QR Check-in system tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_qr_data_admin(self, admin_token):
        """Test getting QR code data (admin only)"""
        response = requests.get(f"{BASE_URL}/api/venue/qr-data", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "venue_code" in data
        assert "date" in data
        assert "checkin_url" in data
        print(f"SUCCESS: QR data retrieved - code: {data['venue_code'][:6]}..., date: {data['date']}")
    
    def test_qr_data_requires_admin(self):
        """Test that QR data endpoint requires admin"""
        # Login as regular user
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Try to get QR data
        response = requests.get(f"{BASE_URL}/api/venue/qr-data", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 403
        print("SUCCESS: QR data correctly requires admin access")


class TestFinalizeChallenge:
    """Challenge finalization tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_finalize_challenge_admin(self, admin_token):
        """Test finalizing a challenge (admin only)"""
        # Get accepted challenges
        challenges_resp = requests.get(f"{BASE_URL}/api/challenges", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        accepted = [c for c in challenges_resp.json() if c["status"] == "accepted" and c.get("vote_count", 0) > 0]
        
        if len(accepted) == 0:
            print("INFO: No accepted challenges with votes to finalize")
            return
        
        challenge_id = accepted[0]["id"]
        
        response = requests.post(f"{BASE_URL}/api/challenges/{challenge_id}/finalize", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Challenge finalized - Winner: {data.get('winner_name')}")
        elif response.status_code == 400:
            print(f"INFO: Cannot finalize - {response.json().get('detail')}")
        else:
            print(f"INFO: Finalize response - {response.status_code}: {response.text}")


class TestWebSocketEndpoint:
    """WebSocket endpoint tests"""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is configured (via HTTP OPTIONS)"""
        # Can't directly test WebSocket in pytest, but verify the upgrade path exists
        # The server.py has @app.websocket("/ws") defined
        # We'll just verify the endpoint doesn't 404 on regular HTTP
        
        response = requests.get(f"{BASE_URL}/ws")
        # WebSocket endpoints typically return 426 (Upgrade Required) for HTTP
        # or 400 Bad Request, not 404
        assert response.status_code != 404, "WebSocket endpoint not found"
        print(f"SUCCESS: WebSocket endpoint exists at /ws (HTTP response: {response.status_code})")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
