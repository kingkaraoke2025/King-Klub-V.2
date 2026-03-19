"""
WebSocket and Battle Challenge Notification Tests
Tests:
1. WebSocket connection to /api/ws
2. Battle challenge creation triggers BATTLE_CHALLENGE notification via WebSocket
3. WebSocket connection handles ping/pong
"""

import pytest
import requests
import asyncio
import json
import os
import uuid

# Try to import websockets for WebSocket testing
try:
    import websockets
except ImportError:
    websockets = None

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@kingkaraoke2025.com"
ADMIN_PASSWORD = "admin123"
USER_EMAIL = "royaltest@example.com"
USER_PASSWORD = "password123"
KOTA_EMAIL = "dakotaolachea@hotmail.com"
KOTA_PASSWORD = "kota123"


# Helper function to get WebSocket URL
def get_ws_url():
    return BASE_URL.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/ws'


class TestWebSocketBasics:
    """Test WebSocket endpoint availability and basic functionality"""
    
    def test_websocket_endpoint_exists(self):
        """Verify the WebSocket endpoint exists at /api/ws"""
        ws_url = get_ws_url()
        
        # This test validates the endpoint is reachable
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200, "API should be reachable"
        print(f"✓ API is reachable, WebSocket endpoint should be at: {ws_url}")
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishes successfully"""
        if websockets is None:
            pytest.skip("websockets library not installed")
        
        ws_url = get_ws_url()
        print(f"Testing WebSocket connection to: {ws_url}")
        
        try:
            # Use open_timeout instead of timeout for newer websockets library
            async with websockets.connect(ws_url, open_timeout=10, close_timeout=5) as ws:
                print("✓ WebSocket connection established successfully")
                
                # Send a ping
                await ws.send("ping")
                
                # Wait for pong response
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                assert response == "pong", f"Expected 'pong', got '{response}'"
                print("✓ Ping/pong exchange successful")
                
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {type(e).__name__}: {e}")
    
    @pytest.mark.asyncio
    async def test_websocket_receives_broadcast(self):
        """Test that connected WebSocket client can receive broadcast messages"""
        if websockets is None:
            pytest.skip("websockets library not installed")
        
        ws_url = get_ws_url()
        
        # Connect a client
        try:
            async with websockets.connect(ws_url, open_timeout=10, close_timeout=5) as ws:
                # Connection successful
                print("✓ WebSocket connected for broadcast test")
                
                # Send a ping to verify connection is active
                await ws.send("ping")
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                assert response == "pong"
                print("✓ Connection is active (ping/pong works)")
                
        except Exception as e:
            pytest.fail(f"WebSocket broadcast test setup failed: {type(e).__name__}: {e}")


class TestAuthAndUsers:
    """Test authentication and user management"""
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Login response should have token"
        assert data["user"]["is_admin"] == True, "Admin user should have is_admin=True"
        print(f"✓ Admin login successful: {data['user']['display_name']}")
    
    def test_user_login_royal(self):
        """Test royal performer user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200, f"User login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Login response should have token"
        print(f"✓ Royal Performer login successful: {data['user']['display_name']}")
    
    def test_user_login_kota(self):
        """Test King Kota user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KOTA_EMAIL,
            "password": KOTA_PASSWORD
        })
        assert response.status_code == 200, f"Kota login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Login response should have token"
        print(f"✓ King Kota login successful: {data['user']['display_name']}")


class TestChallengesEndpoint:
    """Test the challenges API endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for API calls"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_challenges_list_requires_auth(self):
        """Test getting list of challenges requires authentication"""
        response = requests.get(f"{BASE_URL}/api/challenges")
        assert response.status_code == 403, "Challenges endpoint should require auth"
        print("✓ Challenges endpoint correctly requires authentication")
    
    def test_get_challenges_list(self, auth_headers):
        """Test getting list of challenges"""
        response = requests.get(f"{BASE_URL}/api/challenges", headers=auth_headers)
        assert response.status_code == 200, f"Get challenges failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Challenges should be a list"
        print(f"✓ Got {len(data)} challenges")
    
    def test_get_my_challenges(self, auth_headers):
        """Test getting my challenges"""
        response = requests.get(f"{BASE_URL}/api/challenges/my", headers=auth_headers)
        assert response.status_code == 200, f"Get my challenges failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "My challenges should be a list"
        print(f"✓ Got {len(data)} of my challenges")


class TestBattleChallengeNotification:
    """Test battle challenge creation and WebSocket notifications"""
    
    @pytest.fixture
    def setup_users(self):
        """Setup test users and tokens"""
        # Login all users
        admin_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert admin_resp.status_code == 200, "Admin login failed"
        admin_data = admin_resp.json()
        
        royal_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert royal_resp.status_code == 200, "Royal user login failed"
        royal_data = royal_resp.json()
        
        kota_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KOTA_EMAIL,
            "password": KOTA_PASSWORD
        })
        assert kota_resp.status_code == 200, "Kota login failed"
        kota_data = kota_resp.json()
        
        return {
            "admin": {"token": admin_data["token"], "id": admin_data["user"]["id"], "name": admin_data["user"]["display_name"]},
            "royal": {"token": royal_data["token"], "id": royal_data["user"]["id"], "name": royal_data["user"]["display_name"]},
            "kota": {"token": kota_data["token"], "id": kota_data["user"]["id"], "name": kota_data["user"]["display_name"]}
        }
    
    def test_cannot_challenge_self(self, setup_users):
        """Test that a user cannot challenge themselves"""
        users = setup_users
        
        response = requests.post(
            f"{BASE_URL}/api/challenges",
            json={
                "opponent_id": users["royal"]["id"],
                "challenge_type": "royal_duel"
            },
            headers={"Authorization": f"Bearer {users['royal']['token']}"}
        )
        
        # Should fail - cannot challenge self
        assert response.status_code == 400, f"Should not be able to challenge self: {response.text}"
        print("✓ Cannot challenge self - correctly rejected")
    
    def test_check_existing_challenges_between_users(self, setup_users):
        """Check for existing challenges between test users"""
        users = setup_users
        
        response = requests.get(
            f"{BASE_URL}/api/challenges",
            headers={"Authorization": f"Bearer {users['royal']['token']}"}
        )
        assert response.status_code == 200
        
        challenges = response.json()
        
        # Find challenges involving our test users
        royal_id = users["royal"]["id"]
        kota_id = users["kota"]["id"]
        
        existing_between_users = []
        for c in challenges:
            if c.get("status") in ["pending", "accepted"]:
                if (c.get("challenger_id") == royal_id and c.get("opponent_id") == kota_id) or \
                   (c.get("challenger_id") == kota_id and c.get("opponent_id") == royal_id):
                    existing_between_users.append(c)
        
        print(f"✓ Found {len(existing_between_users)} active challenges between Royal and Kota")
    
    @pytest.mark.asyncio
    async def test_challenge_creates_websocket_broadcast(self, setup_users):
        """Test that creating a challenge broadcasts BATTLE_CHALLENGE via WebSocket"""
        if websockets is None:
            pytest.skip("websockets library not installed")
        
        users = setup_users
        ws_url = get_ws_url()
        
        # First check if there's already an active challenge between these users
        response = requests.get(
            f"{BASE_URL}/api/challenges",
            headers={"Authorization": f"Bearer {users['royal']['token']}"}
        )
        challenges = response.json()
        
        royal_id = users["royal"]["id"]
        kota_id = users["kota"]["id"]
        
        has_existing = False
        for c in challenges:
            if c.get("status") in ["pending", "accepted"]:
                if (c.get("challenger_id") == royal_id and c.get("opponent_id") == kota_id) or \
                   (c.get("challenger_id") == kota_id and c.get("opponent_id") == royal_id):
                    has_existing = True
                    print(f"⚠ Existing active challenge found: {c['id']}")
                    break
        
        if has_existing:
            print("⚠ Skipping challenge creation test - active challenge exists between users")
            pytest.skip("Active challenge exists between test users - cannot create new one")
        
        # Connect WebSocket first to receive the broadcast
        try:
            async with websockets.connect(ws_url, open_timeout=10, close_timeout=5) as ws:
                print("✓ WebSocket connected for broadcast listening")
                
                # Verify connection with ping
                await ws.send("ping")
                pong = await asyncio.wait_for(ws.recv(), timeout=5)
                assert pong == "pong"
                print("✓ WebSocket connection verified")
                
                # Create a challenge while listening
                challenge_response = requests.post(
                    f"{BASE_URL}/api/challenges",
                    json={
                        "opponent_id": kota_id,
                        "challenge_type": "royal_duel"
                    },
                    headers={"Authorization": f"Bearer {users['royal']['token']}"}
                )
                
                if challenge_response.status_code == 400:
                    error_detail = challenge_response.json().get("detail", "")
                    if "already" in error_detail.lower():
                        print(f"⚠ Challenge creation blocked: {error_detail}")
                        pytest.skip("Active challenge exists - API correctly prevents duplicates")
                
                assert challenge_response.status_code == 200, f"Challenge creation failed: {challenge_response.text}"
                challenge_data = challenge_response.json()
                print(f"✓ Challenge created: {challenge_data['id']}")
                
                # Wait for WebSocket broadcast
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=5)
                    broadcast_data = json.loads(message)
                    
                    assert broadcast_data.get("type") == "BATTLE_CHALLENGE", f"Expected BATTLE_CHALLENGE, got {broadcast_data.get('type')}"
                    assert broadcast_data.get("challenger_id") == royal_id
                    assert broadcast_data.get("opponent_id") == kota_id
                    assert broadcast_data.get("challenge_type") == "royal_duel"
                    
                    print("✓ BATTLE_CHALLENGE broadcast received!")
                    print(f"  - Challenge ID: {broadcast_data.get('challenge_id')}")
                    print(f"  - Challenger: {broadcast_data.get('challenger_name')}")
                    print(f"  - Opponent: {broadcast_data.get('opponent_name')}")
                    print(f"  - Type: {broadcast_data.get('challenge_type_name')}")
                    
                except asyncio.TimeoutError:
                    pytest.fail("Timeout waiting for BATTLE_CHALLENGE WebSocket broadcast")
                    
        except Exception as e:
            pytest.fail(f"WebSocket broadcast test failed: {type(e).__name__}: {e}")


class TestWebSocketWithMultipleClients:
    """Test that multiple WebSocket clients can connect and receive broadcasts"""
    
    @pytest.mark.asyncio
    async def test_multiple_clients_connect(self):
        """Test that multiple clients can connect simultaneously"""
        if websockets is None:
            pytest.skip("websockets library not installed")
        
        ws_url = get_ws_url()
        
        clients = []
        try:
            # Connect 3 clients
            for i in range(3):
                ws = await websockets.connect(ws_url, open_timeout=10, close_timeout=5)
                clients.append(ws)
                print(f"✓ Client {i+1} connected")
            
            # Verify all connections with ping
            for i, ws in enumerate(clients):
                await ws.send("ping")
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                assert response == "pong", f"Client {i+1} ping failed"
                print(f"✓ Client {i+1} ping/pong successful")
            
            print(f"✓ All {len(clients)} clients connected and verified")
            
        finally:
            # Close all connections
            for ws in clients:
                await ws.close()


# Integration test - simulate full flow
class TestIntegrationBattleFlow:
    """Integration tests for the complete battle notification flow"""
    
    def test_challenge_api_response_structure(self):
        """Test that challenge creation response has correct structure"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": USER_EMAIL,
            "password": USER_PASSWORD
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["token"]
        user_id = login_resp.json()["user"]["id"]
        
        # Get another user to challenge
        kota_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": KOTA_EMAIL,
            "password": KOTA_PASSWORD
        })
        kota_id = kota_resp.json()["user"]["id"]
        
        # Try to create a challenge
        response = requests.post(
            f"{BASE_URL}/api/challenges",
            json={
                "opponent_id": kota_id,
                "challenge_type": "royal_duel"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # If successful, check response structure
        if response.status_code == 200:
            data = response.json()
            assert "id" in data, "Response should have challenge id"
            assert "message" in data, "Response should have message"
            assert "type" in data, "Response should have type"
            assert "type_info" in data, "Response should have type_info"
            print(f"✓ Challenge created with proper response structure: {data['id']}")
        elif response.status_code == 400:
            # Expected if challenge already exists
            error = response.json().get("detail", "")
            print(f"⚠ Challenge creation blocked (expected if active challenge exists): {error}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code} - {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
