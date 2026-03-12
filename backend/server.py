from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'king-klub-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Create the main app
app = FastAPI(title="King Klub API")
api_router = APIRouter(prefix="/api")

# ==================== RANK SYSTEM ====================
RANKS = [
    {"name": "Peasant", "min_points": 0, "icon": "shield"},
    {"name": "Squire", "min_points": 100, "icon": "sword"},
    {"name": "Knight", "min_points": 300, "icon": "swords"},
    {"name": "Count", "min_points": 600, "icon": "crown"},
    {"name": "Duke", "min_points": 1000, "icon": "gem"},
    {"name": "Prince", "min_points": 2000, "icon": "sparkles"},
]

def get_rank(points: int) -> dict:
    current_rank = RANKS[0]
    for rank in RANKS:
        if points >= rank["min_points"]:
            current_rank = rank
    return current_rank

def get_next_rank(points: int) -> Optional[dict]:
    for i, rank in enumerate(RANKS):
        if points < rank["min_points"]:
            return rank
    return None

# ==================== MODELS ====================
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    display_name: str
    points: int
    songs_performed: int
    consecutive_visits: int
    rank: dict
    next_rank: Optional[dict]
    badges: List[str]
    is_admin: bool
    created_at: str

class UserPublic(BaseModel):
    id: str
    display_name: str
    points: int
    rank: dict
    songs_performed: int
    badges: List[str]

class SongQueueItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    user_name: str
    song_title: str
    artist: str
    status: str  # pending, current, completed, cancelled
    position: int
    estimated_wait: int
    created_at: str

class AddSongRequest(BaseModel):
    song_title: str
    artist: str

class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    points_reward: int

class Accomplishment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    badge_id: str
    badge_name: str
    earned_at: str

# ==================== BADGE DEFINITIONS ====================
# Point actions that can be awarded
POINT_ACTIONS = {
    "sing_song": {"name": "Sing a Song", "points": 10, "description": "Perform a song on stage"},
    "bring_friend": {"name": "Bring a Friend", "points": 10, "description": "Invite a new member"},
    "sing_blindfolded": {"name": "Blindfolded Performance", "points": 250, "description": "Sing a song blindfolded"},
    "three_nights": {"name": "3 Consecutive Nights", "points": 25, "description": "Visit 3 nights in a row"},
    "five_nights": {"name": "5 Consecutive Nights", "points": 50, "description": "Visit 5 nights in a row"},
    "random_song": {"name": "Random Song Challenge", "points": 200, "description": "Sing a randomly selected song"},
    "sing_duet": {"name": "Duet Performance", "points": 10, "description": "Perform a duet with someone"},
    "tiktok_post": {"name": "TikTok Post", "points": 200, "description": "Post performance to TikTok"},
    "follow_tiktok": {"name": "Follow on TikTok", "points": 10, "description": "Follow King Karaoke on TikTok"},
    "follow_facebook": {"name": "Follow on Facebook", "points": 10, "description": "Follow King Karaoke on Facebook"},
    "tip_kj": {"name": "Tip the KJ", "points": 10, "description": "Show appreciation to the KJ"},
    "bar_song": {"name": "King Karaoke Bar Song", "points": 100, "description": "Perform the official bar song"},
}

# Achievement badges (earned automatically based on milestones)
BADGES = {
    # Performance milestones
    "first_song": {"name": "First Timer", "description": "Performed your first song", "icon": "mic", "points_reward": 10, "category": "performance"},
    "five_songs": {"name": "Rising Star", "description": "Performed 5 songs", "icon": "star", "points_reward": 25, "category": "performance"},
    "ten_songs": {"name": "Stage Regular", "description": "Performed 10 songs", "icon": "trophy", "points_reward": 50, "category": "performance"},
    "twenty_songs": {"name": "Karaoke Royalty", "description": "Performed 20 songs", "icon": "crown", "points_reward": 100, "category": "performance"},
    
    # Special challenges
    "blindfolded_master": {"name": "Blindfolded Master", "description": "Completed a blindfolded performance", "icon": "eye-off", "points_reward": 250, "category": "challenge"},
    "random_warrior": {"name": "Random Warrior", "description": "Conquered the random song challenge", "icon": "shuffle", "points_reward": 200, "category": "challenge"},
    "bar_song_hero": {"name": "Bar Song Hero", "description": "Performed the King Karaoke bar song", "icon": "music", "points_reward": 100, "category": "challenge"},
    
    # Social badges
    "duet_singer": {"name": "Duet Partner", "description": "Performed your first duet", "icon": "users", "points_reward": 10, "category": "social"},
    "duet_master": {"name": "Duet Master", "description": "Performed 5 duets", "icon": "heart-handshake", "points_reward": 50, "category": "social"},
    "social_butterfly": {"name": "Social Butterfly", "description": "Brought 3 friends to King Karaoke", "icon": "user-plus", "points_reward": 50, "category": "social"},
    "influencer": {"name": "Influencer", "description": "Posted to TikTok", "icon": "video", "points_reward": 200, "category": "social"},
    "super_fan": {"name": "Super Fan", "description": "Followed on TikTok & Facebook", "icon": "thumbs-up", "points_reward": 20, "category": "social"},
    
    # Loyalty badges
    "night_owl": {"name": "Night Owl", "description": "Visited 3 consecutive nights", "icon": "moon", "points_reward": 25, "category": "loyalty"},
    "dedicated_fan": {"name": "Dedicated Fan", "description": "Visited 5 consecutive nights", "icon": "flame", "points_reward": 50, "category": "loyalty"},
    "loyal_patron": {"name": "Loyal Patron", "description": "Visited 10 consecutive nights", "icon": "award", "points_reward": 100, "category": "loyalty"},
    
    # Generosity
    "generous_tipper": {"name": "Generous Tipper", "description": "Tipped the KJ", "icon": "coins", "points_reward": 10, "category": "generosity"},
    "big_tipper": {"name": "Big Tipper", "description": "Tipped the KJ 5 times", "icon": "banknote", "points_reward": 50, "category": "generosity"},
    
    # Battle badges
    "first_battle": {"name": "First Blood", "description": "Participated in your first battle", "icon": "swords", "points_reward": 25, "category": "battle"},
    "battle_winner": {"name": "Battle Victor", "description": "Won your first battle", "icon": "trophy", "points_reward": 50, "category": "battle"},
    "duel_master": {"name": "Duel Master", "description": "Won 5 battles", "icon": "crown", "points_reward": 100, "category": "battle"},
    "crowd_champion": {"name": "Crowd Champion", "description": "Won a battle with 10+ votes", "icon": "users", "points_reward": 75, "category": "battle"},
}

# Challenge types
CHALLENGE_TYPES = {
    "royal_duel": {"name": "Royal Duel", "description": "Classic head-to-head battle", "points_winner": 50, "points_participant": 25},
    "blind_challenge": {"name": "Blind Challenge", "description": "Sing without seeing lyrics", "points_winner": 75, "points_participant": 35},
    "rank_battle": {"name": "Rank Battle", "description": "Battle for rank supremacy", "points_winner": 60, "points_participant": 30},
    "roulette": {"name": "Song Roulette", "description": "Random song assigned to both", "points_winner": 100, "points_participant": 50},
    "harmony_duel": {"name": "Harmony Duel", "description": "Duet-style battle", "points_winner": 75, "points_participant": 40},
}

# ==================== AUTH HELPERS ====================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, is_admin: bool = False) -> str:
    payload = {
        "user_id": user_id,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    user = await get_current_user(credentials)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ==================== AUTH ENDPOINTS ====================
@api_router.post("/auth/register")
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email,
        "password": hash_password(data.password),
        "display_name": data.display_name,
        "points": 0,
        "songs_performed": 0,
        "consecutive_visits": 0,
        "badges": [],
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_visit": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id)
    rank = get_rank(0)
    next_rank = get_next_rank(0)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email,
            "display_name": data.display_name,
            "points": 0,
            "songs_performed": 0,
            "consecutive_visits": 0,
            "rank": rank,
            "next_rank": next_rank,
            "badges": [],
            "is_admin": False,
            "created_at": user["created_at"]
        }
    }

@api_router.post("/auth/login")
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last visit and consecutive visits
    last_visit = datetime.fromisoformat(user["last_visit"].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    days_diff = (now - last_visit).days
    
    consecutive_visits = user["consecutive_visits"]
    if days_diff == 1:
        consecutive_visits += 1
    elif days_diff > 1:
        consecutive_visits = 1
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"last_visit": now.isoformat(), "consecutive_visits": consecutive_visits}}
    )
    
    token = create_token(user["id"], user.get("is_admin", False))
    rank = get_rank(user["points"])
    next_rank = get_next_rank(user["points"])
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "display_name": user["display_name"],
            "points": user["points"],
            "songs_performed": user["songs_performed"],
            "consecutive_visits": consecutive_visits,
            "rank": rank,
            "next_rank": next_rank,
            "badges": user["badges"],
            "is_admin": user.get("is_admin", False),
            "created_at": user["created_at"]
        }
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    rank = get_rank(user["points"])
    next_rank = get_next_rank(user["points"])
    return {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "points": user["points"],
        "songs_performed": user["songs_performed"],
        "consecutive_visits": user["consecutive_visits"],
        "rank": rank,
        "next_rank": next_rank,
        "badges": user["badges"],
        "is_admin": user.get("is_admin", False),
        "created_at": user["created_at"]
    }

# ==================== SONG QUEUE ENDPOINTS ====================
@api_router.get("/queue")
async def get_queue():
    queue = await db.queue.find(
        {"status": {"$in": ["pending", "current"]}},
        {"_id": 0}
    ).sort("position", 1).to_list(100)
    return queue

@api_router.post("/queue")
async def add_to_queue(data: AddSongRequest, user: dict = Depends(get_current_user)):
    # Check if user already has a pending song
    existing = await db.queue.find_one({
        "user_id": user["id"],
        "status": {"$in": ["pending", "current"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="You already have a song in queue")
    
    # Get current max position
    last_item = await db.queue.find_one(
        {"status": {"$in": ["pending", "current"]}},
        sort=[("position", -1)]
    )
    position = (last_item["position"] + 1) if last_item else 1
    
    queue_item = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_name": user["display_name"],
        "song_title": data.song_title,
        "artist": data.artist,
        "status": "pending",
        "position": position,
        "estimated_wait": (position - 1) * 4,  # ~4 minutes per song
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.queue.insert_one(queue_item)
    
    # Return without _id
    if "_id" in queue_item:
        del queue_item["_id"]
    return queue_item

@api_router.delete("/queue/{item_id}")
async def remove_from_queue(item_id: str, user: dict = Depends(get_current_user)):
    item = await db.queue.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    if item["user_id"] != user["id"] and not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.queue.update_one({"id": item_id}, {"$set": {"status": "cancelled"}})
    
    # Recalculate positions
    remaining = await db.queue.find(
        {"status": {"$in": ["pending", "current"]}, "position": {"$gt": item["position"]}}
    ).to_list(100)
    
    for q_item in remaining:
        await db.queue.update_one(
            {"id": q_item["id"]},
            {"$set": {"position": q_item["position"] - 1, "estimated_wait": (q_item["position"] - 2) * 4}}
        )
    
    return {"message": "Removed from queue"}

# ==================== ADMIN QUEUE MANAGEMENT ====================
@api_router.post("/admin/queue/{item_id}/complete")
async def complete_song(item_id: str, user: dict = Depends(get_admin_user)):
    item = await db.queue.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    # Mark as completed
    await db.queue.update_one({"id": item_id}, {"$set": {"status": "completed"}})
    
    # Award points to the performer
    performer = await db.users.find_one({"id": item["user_id"]}, {"_id": 0})
    if performer:
        new_points = performer["points"] + 10
        new_songs = performer["songs_performed"] + 1
        badges = list(performer["badges"])
        
        # Check for new badges
        if new_songs == 1 and "first_song" not in badges:
            badges.append("first_song")
            new_points += BADGES["first_song"]["points_reward"]
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": performer["id"],
                "badge_id": "first_song",
                "badge_name": BADGES["first_song"]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
        
        if new_songs == 5 and "five_songs" not in badges:
            badges.append("five_songs")
            new_points += BADGES["five_songs"]["points_reward"]
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": performer["id"],
                "badge_id": "five_songs",
                "badge_name": BADGES["five_songs"]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
        
        if new_songs == 10 and "ten_songs" not in badges:
            badges.append("ten_songs")
            new_points += BADGES["ten_songs"]["points_reward"]
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": performer["id"],
                "badge_id": "ten_songs",
                "badge_name": BADGES["ten_songs"]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
        
        if new_songs == 20 and "twenty_songs" not in badges:
            badges.append("twenty_songs")
            new_points += BADGES["twenty_songs"]["points_reward"]
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": performer["id"],
                "badge_id": "twenty_songs",
                "badge_name": BADGES["twenty_songs"]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
        
        await db.users.update_one(
            {"id": performer["id"]},
            {"$set": {"points": new_points, "songs_performed": new_songs, "badges": badges}}
        )
    
    # Set next song as current
    next_song = await db.queue.find_one(
        {"status": "pending"},
        sort=[("position", 1)]
    )
    if next_song:
        await db.queue.update_one({"id": next_song["id"]}, {"$set": {"status": "current"}})
    
    # Recalculate positions
    remaining = await db.queue.find(
        {"status": {"$in": ["pending", "current"]}}
    ).sort("position", 1).to_list(100)
    
    for i, q_item in enumerate(remaining):
        await db.queue.update_one(
            {"id": q_item["id"]},
            {"$set": {"position": i + 1, "estimated_wait": i * 4}}
        )
    
    return {"message": "Song completed", "points_awarded": 10}

@api_router.post("/admin/queue/{item_id}/set-current")
async def set_current_song(item_id: str, user: dict = Depends(get_admin_user)):
    # Set all current songs to pending
    await db.queue.update_many({"status": "current"}, {"$set": {"status": "pending"}})
    
    # Set this one as current
    result = await db.queue.update_one({"id": item_id}, {"$set": {"status": "current"}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    return {"message": "Current song updated"}

# ==================== LEADERBOARD ====================
@api_router.get("/leaderboard")
async def get_leaderboard():
    users = await db.users.find(
        {},
        {"_id": 0, "password": 0, "email": 0}
    ).sort("points", -1).limit(20).to_list(20)
    
    leaderboard = []
    for i, user in enumerate(users):
        leaderboard.append({
            "position": i + 1,
            "id": user["id"],
            "display_name": user["display_name"],
            "points": user["points"],
            "rank": get_rank(user["points"]),
            "songs_performed": user["songs_performed"],
            "badges": user["badges"]
        })
    
    return leaderboard

# ==================== ACCOMPLISHMENTS ====================
@api_router.get("/accomplishments")
async def get_user_accomplishments(user: dict = Depends(get_current_user)):
    accomplishments = await db.accomplishments.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("earned_at", -1).to_list(100)
    return accomplishments

@api_router.get("/badges")
async def get_all_badges():
    return [{"id": k, **v} for k, v in BADGES.items()]

# ==================== ADMIN USERS ====================
@api_router.get("/admin/users")
async def get_all_users(user: dict = Depends(get_admin_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    for u in users:
        u["rank"] = get_rank(u["points"])
    return users

@api_router.post("/admin/users/{user_id}/points")
async def adjust_points(user_id: str, points: int, user: dict = Depends(get_admin_user)):
    result = await db.users.update_one(
        {"id": user_id},
        {"$inc": {"points": points}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"Added {points} points"}

@api_router.post("/admin/users/{user_id}/toggle-admin")
async def toggle_admin(user_id: str, admin_user: dict = Depends(get_admin_user)):
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not target.get("is_admin", False)
    await db.users.update_one({"id": user_id}, {"$set": {"is_admin": new_status}})
    return {"message": f"Admin status set to {new_status}"}

# ==================== STATS ====================
@api_router.get("/stats")
async def get_stats():
    total_users = await db.users.count_documents({})
    total_songs = await db.queue.count_documents({"status": "completed"})
    queue_length = await db.queue.count_documents({"status": {"$in": ["pending", "current"]}})
    
    return {
        "total_users": total_users,
        "total_songs_performed": total_songs,
        "current_queue_length": queue_length
    }

# ==================== POINT ACTIONS ====================
@api_router.get("/point-actions")
async def get_point_actions():
    """Get all available point-earning actions"""
    return [{"id": k, **v} for k, v in POINT_ACTIONS.items()]

class AwardPointsRequest(BaseModel):
    user_id: str
    action_id: str
    notes: Optional[str] = None

async def check_and_award_badges(user_id: str, user_data: dict):
    """Check if user qualifies for any new badges and award them"""
    badges = list(user_data.get("badges", []))
    new_badges = []
    bonus_points = 0
    
    # Get user stats
    stats = user_data.get("action_stats", {})
    songs = user_data.get("songs_performed", 0)
    duets = stats.get("duets", 0)
    friends_brought = stats.get("friends_brought", 0)
    tips = stats.get("tips", 0)
    consecutive = user_data.get("consecutive_visits", 0)
    
    # Performance badges
    if songs >= 1 and "first_song" not in badges:
        badges.append("first_song")
        new_badges.append("first_song")
        bonus_points += BADGES["first_song"]["points_reward"]
    
    if songs >= 5 and "five_songs" not in badges:
        badges.append("five_songs")
        new_badges.append("five_songs")
        bonus_points += BADGES["five_songs"]["points_reward"]
    
    if songs >= 10 and "ten_songs" not in badges:
        badges.append("ten_songs")
        new_badges.append("ten_songs")
        bonus_points += BADGES["ten_songs"]["points_reward"]
    
    if songs >= 20 and "twenty_songs" not in badges:
        badges.append("twenty_songs")
        new_badges.append("twenty_songs")
        bonus_points += BADGES["twenty_songs"]["points_reward"]
    
    # Duet badges
    if duets >= 1 and "duet_singer" not in badges:
        badges.append("duet_singer")
        new_badges.append("duet_singer")
        bonus_points += BADGES["duet_singer"]["points_reward"]
    
    if duets >= 5 and "duet_master" not in badges:
        badges.append("duet_master")
        new_badges.append("duet_master")
        bonus_points += BADGES["duet_master"]["points_reward"]
    
    # Social badges
    if friends_brought >= 3 and "social_butterfly" not in badges:
        badges.append("social_butterfly")
        new_badges.append("social_butterfly")
        bonus_points += BADGES["social_butterfly"]["points_reward"]
    
    # Loyalty badges
    if consecutive >= 3 and "night_owl" not in badges:
        badges.append("night_owl")
        new_badges.append("night_owl")
        bonus_points += BADGES["night_owl"]["points_reward"]
    
    if consecutive >= 5 and "dedicated_fan" not in badges:
        badges.append("dedicated_fan")
        new_badges.append("dedicated_fan")
        bonus_points += BADGES["dedicated_fan"]["points_reward"]
    
    if consecutive >= 10 and "loyal_patron" not in badges:
        badges.append("loyal_patron")
        new_badges.append("loyal_patron")
        bonus_points += BADGES["loyal_patron"]["points_reward"]
    
    # Tipper badges
    if tips >= 1 and "generous_tipper" not in badges:
        badges.append("generous_tipper")
        new_badges.append("generous_tipper")
        bonus_points += BADGES["generous_tipper"]["points_reward"]
    
    if tips >= 5 and "big_tipper" not in badges:
        badges.append("big_tipper")
        new_badges.append("big_tipper")
        bonus_points += BADGES["big_tipper"]["points_reward"]
    
    # Update user badges and add bonus points
    if new_badges:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"badges": badges}, "$inc": {"points": bonus_points}}
        )
        
        # Record accomplishments
        for badge_id in new_badges:
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "badge_id": badge_id,
                "badge_name": BADGES[badge_id]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
    
    return new_badges, bonus_points

@api_router.post("/admin/award-points")
async def award_points_action(data: AwardPointsRequest, admin: dict = Depends(get_admin_user)):
    """Award points for a specific action (admin only)"""
    if data.action_id not in POINT_ACTIONS:
        raise HTTPException(status_code=400, detail="Invalid action ID")
    
    action = POINT_ACTIONS[data.action_id]
    points = action["points"]
    
    # Get user
    user = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update
    update_ops = {"$inc": {"points": points}}
    
    # Track specific stats based on action
    if data.action_id == "sing_song":
        update_ops["$inc"]["songs_performed"] = 1
    elif data.action_id == "sing_duet":
        update_ops["$inc"]["songs_performed"] = 1
        update_ops["$inc"]["action_stats.duets"] = 1
    elif data.action_id == "bring_friend":
        update_ops["$inc"]["action_stats.friends_brought"] = 1
    elif data.action_id == "tip_kj":
        update_ops["$inc"]["action_stats.tips"] = 1
    elif data.action_id in ["three_nights", "five_nights"]:
        update_ops["$set"] = {"consecutive_visits": 3 if data.action_id == "three_nights" else 5}
    elif data.action_id == "follow_tiktok":
        update_ops["$set"] = update_ops.get("$set", {})
        update_ops["$set"]["action_stats.followed_tiktok"] = True
    elif data.action_id == "follow_facebook":
        update_ops["$set"] = update_ops.get("$set", {})
        update_ops["$set"]["action_stats.followed_facebook"] = True
    
    # Apply update
    await db.users.update_one({"id": data.user_id}, update_ops)
    
    # Check for special action badges
    badges_awarded = []
    bonus_points = 0
    
    user_updated = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    badges = list(user_updated.get("badges", []))
    
    # Special challenge badges (awarded immediately)
    if data.action_id == "sing_blindfolded" and "blindfolded_master" not in badges:
        badges.append("blindfolded_master")
        badges_awarded.append("blindfolded_master")
        bonus_points += BADGES["blindfolded_master"]["points_reward"]
    
    if data.action_id == "random_song" and "random_warrior" not in badges:
        badges.append("random_warrior")
        badges_awarded.append("random_warrior")
        bonus_points += BADGES["random_warrior"]["points_reward"]
    
    if data.action_id == "bar_song" and "bar_song_hero" not in badges:
        badges.append("bar_song_hero")
        badges_awarded.append("bar_song_hero")
        bonus_points += BADGES["bar_song_hero"]["points_reward"]
    
    if data.action_id == "tiktok_post" and "influencer" not in badges:
        badges.append("influencer")
        badges_awarded.append("influencer")
        bonus_points += BADGES["influencer"]["points_reward"]
    
    # Check for super fan badge (followed both)
    stats = user_updated.get("action_stats", {})
    if stats.get("followed_tiktok") and stats.get("followed_facebook") and "super_fan" not in badges:
        badges.append("super_fan")
        badges_awarded.append("super_fan")
        bonus_points += BADGES["super_fan"]["points_reward"]
    
    # Update badges if any awarded
    if badges_awarded:
        await db.users.update_one(
            {"id": data.user_id},
            {"$set": {"badges": badges}, "$inc": {"points": bonus_points}}
        )
        for badge_id in badges_awarded:
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": data.user_id,
                "badge_id": badge_id,
                "badge_name": BADGES[badge_id]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Check milestone badges
    user_final = await db.users.find_one({"id": data.user_id}, {"_id": 0})
    milestone_badges, milestone_bonus = await check_and_award_badges(data.user_id, user_final)
    badges_awarded.extend(milestone_badges)
    bonus_points += milestone_bonus
    
    # Record action in history
    await db.point_history.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": data.user_id,
        "action_id": data.action_id,
        "action_name": action["name"],
        "points": points,
        "notes": data.notes,
        "awarded_by": admin["id"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": f"Awarded {points} points for {action['name']}",
        "points_awarded": points,
        "bonus_points": bonus_points,
        "total_points": points + bonus_points,
        "badges_earned": badges_awarded
    }

@api_router.get("/admin/point-history/{user_id}")
async def get_user_point_history(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get point history for a user"""
    history = await db.point_history.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(100)
    return history

# ==================== BATTLE/CHALLENGE SYSTEM ====================
class ChallengeCreate(BaseModel):
    opponent_id: str
    challenge_type: str  # royal_duel, blind_challenge, rank_battle, roulette, harmony_duel

class VoteRequest(BaseModel):
    vote_for: str  # user_id of performer to vote for

@api_router.get("/challenges")
async def get_active_challenges(user: dict = Depends(get_current_user)):
    """Get all active challenges (pending or accepted)"""
    challenges = await db.challenges.find(
        {"status": {"$in": ["pending", "accepted"]}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Add user names
    for c in challenges:
        challenger = await db.users.find_one({"id": c["challenger_id"]}, {"_id": 0, "display_name": 1, "rank": 1, "points": 1})
        opponent = await db.users.find_one({"id": c["opponent_id"]}, {"_id": 0, "display_name": 1, "rank": 1, "points": 1})
        c["challenger"] = challenger
        c["opponent"] = opponent
        c["vote_count"] = len(c.get("votes", []))
        c["type_info"] = CHALLENGE_TYPES.get(c["type"], {})
    
    return challenges

@api_router.get("/challenges/my")
async def get_my_challenges(user: dict = Depends(get_current_user)):
    """Get challenges involving the current user"""
    challenges = await db.challenges.find(
        {"$or": [{"challenger_id": user["id"]}, {"opponent_id": user["id"]}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    for c in challenges:
        challenger = await db.users.find_one({"id": c["challenger_id"]}, {"_id": 0, "display_name": 1})
        opponent = await db.users.find_one({"id": c["opponent_id"]}, {"_id": 0, "display_name": 1})
        c["challenger"] = challenger
        c["opponent"] = opponent
        c["type_info"] = CHALLENGE_TYPES.get(c["type"], {})
    
    return challenges

@api_router.post("/challenges")
async def create_challenge(data: ChallengeCreate, user: dict = Depends(get_current_user)):
    """Issue a challenge to another user"""
    if data.challenge_type not in CHALLENGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid challenge type")
    
    if data.opponent_id == user["id"]:
        raise HTTPException(status_code=400, detail="Cannot challenge yourself")
    
    # Check opponent exists
    opponent = await db.users.find_one({"id": data.opponent_id})
    if not opponent:
        raise HTTPException(status_code=404, detail="Opponent not found")
    
    # Check for existing active challenge between these users
    existing = await db.challenges.find_one({
        "$or": [
            {"challenger_id": user["id"], "opponent_id": data.opponent_id},
            {"challenger_id": data.opponent_id, "opponent_id": user["id"]}
        ],
        "status": {"$in": ["pending", "accepted"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Active challenge already exists between these users")
    
    challenge = {
        "id": str(uuid.uuid4()),
        "challenger_id": user["id"],
        "opponent_id": data.opponent_id,
        "type": data.challenge_type,
        "status": "pending",
        "votes": [],
        "winner_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.challenges.insert_one(challenge)
    
    # Award first battle badge if needed
    user_badges = list(user.get("badges", []))
    if "first_battle" not in user_badges:
        user_badges.append("first_battle")
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"badges": user_badges}, "$inc": {"points": BADGES["first_battle"]["points_reward"]}}
        )
        await db.accomplishments.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "badge_id": "first_battle",
            "badge_name": BADGES["first_battle"]["name"],
            "earned_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "id": challenge["id"],
        "message": f"Challenge issued to {opponent['display_name']}!",
        "type": data.challenge_type,
        "type_info": CHALLENGE_TYPES[data.challenge_type]
    }

@api_router.post("/challenges/{challenge_id}/accept")
async def accept_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Accept a pending challenge"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["opponent_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the challenged user can accept")
    
    if challenge["status"] != "pending":
        raise HTTPException(status_code=400, detail="Challenge is not pending")
    
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {"status": "accepted"}}
    )
    
    # Award first battle badge to opponent if needed
    user_badges = list(user.get("badges", []))
    if "first_battle" not in user_badges:
        user_badges.append("first_battle")
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"badges": user_badges}, "$inc": {"points": BADGES["first_battle"]["points_reward"]}}
        )
        await db.accomplishments.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "badge_id": "first_battle",
            "badge_name": BADGES["first_battle"]["name"],
            "earned_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {"message": "Challenge accepted! Let the battle begin!"}

@api_router.post("/challenges/{challenge_id}/decline")
async def decline_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Decline a pending challenge"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["opponent_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Only the challenged user can decline")
    
    if challenge["status"] != "pending":
        raise HTTPException(status_code=400, detail="Challenge is not pending")
    
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {"status": "declined"}}
    )
    
    return {"message": "Challenge declined"}

@api_router.post("/challenges/{challenge_id}/vote")
async def vote_for_performer(challenge_id: str, data: VoteRequest, user: dict = Depends(get_current_user)):
    """Vote for a performer in a battle"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["status"] != "accepted":
        raise HTTPException(status_code=400, detail="Challenge is not active")
    
    # Cannot vote for yourself if you're a participant
    if user["id"] in [challenge["challenger_id"], challenge["opponent_id"]]:
        raise HTTPException(status_code=400, detail="Participants cannot vote in their own battle")
    
    # Check vote target is valid
    if data.vote_for not in [challenge["challenger_id"], challenge["opponent_id"]]:
        raise HTTPException(status_code=400, detail="Invalid vote target")
    
    # Check if already voted
    votes = challenge.get("votes", [])
    if any(v["voter_id"] == user["id"] for v in votes):
        raise HTTPException(status_code=400, detail="You have already voted")
    
    # Add vote
    votes.append({
        "voter_id": user["id"],
        "vote_for": data.vote_for
    })
    
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {"votes": votes}}
    )
    
    return {"message": "Vote recorded!", "total_votes": len(votes)}

@api_router.post("/challenges/{challenge_id}/finalize")
async def finalize_challenge(challenge_id: str, admin: dict = Depends(get_admin_user)):
    """Finalize a challenge and determine the winner (admin only)"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["status"] != "accepted":
        raise HTTPException(status_code=400, detail="Challenge must be accepted to finalize")
    
    votes = challenge.get("votes", [])
    if len(votes) == 0:
        raise HTTPException(status_code=400, detail="No votes yet")
    
    # Count votes
    vote_count = {}
    for v in votes:
        vote_count[v["vote_for"]] = vote_count.get(v["vote_for"], 0) + 1
    
    # Determine winner
    winner_id = max(vote_count.keys(), key=lambda k: vote_count[k])
    loser_id = challenge["challenger_id"] if winner_id == challenge["opponent_id"] else challenge["opponent_id"]
    
    # Update challenge
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {"status": "completed", "winner_id": winner_id}}
    )
    
    # Get challenge type info
    type_info = CHALLENGE_TYPES.get(challenge["type"], {"points_winner": 50, "points_participant": 25})
    
    # Award points to winner
    winner = await db.users.find_one({"id": winner_id}, {"_id": 0})
    winner_badges = list(winner.get("badges", []))
    winner_bonus = 0
    new_badges = []
    
    # Battle winner badge
    if "battle_winner" not in winner_badges:
        winner_badges.append("battle_winner")
        new_badges.append("battle_winner")
        winner_bonus += BADGES["battle_winner"]["points_reward"]
    
    # Track wins
    battle_wins = winner.get("battle_wins", 0) + 1
    
    # Duel master badge (5 wins)
    if battle_wins >= 5 and "duel_master" not in winner_badges:
        winner_badges.append("duel_master")
        new_badges.append("duel_master")
        winner_bonus += BADGES["duel_master"]["points_reward"]
    
    # Crowd champion badge (10+ votes)
    if vote_count[winner_id] >= 10 and "crowd_champion" not in winner_badges:
        winner_badges.append("crowd_champion")
        new_badges.append("crowd_champion")
        winner_bonus += BADGES["crowd_champion"]["points_reward"]
    
    await db.users.update_one(
        {"id": winner_id},
        {
            "$inc": {"points": type_info["points_winner"] + winner_bonus},
            "$set": {"badges": winner_badges, "battle_wins": battle_wins}
        }
    )
    
    # Record badges
    for badge_id in new_badges:
        await db.accomplishments.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": winner_id,
            "badge_id": badge_id,
            "badge_name": BADGES[badge_id]["name"],
            "earned_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Award participation points to loser
    await db.users.update_one(
        {"id": loser_id},
        {"$inc": {"points": type_info["points_participant"]}}
    )
    
    winner_user = await db.users.find_one({"id": winner_id}, {"_id": 0, "display_name": 1})
    
    return {
        "message": f"{winner_user['display_name']} wins the battle!",
        "winner_id": winner_id,
        "winner_name": winner_user["display_name"],
        "winner_votes": vote_count[winner_id],
        "loser_votes": vote_count.get(loser_id, 0),
        "points_awarded": type_info["points_winner"],
        "badges_earned": new_badges
    }

@api_router.get("/challenges/types")
async def get_challenge_types():
    """Get all available challenge types"""
    return [{"id": k, **v} for k, v in CHALLENGE_TYPES.items()]

@api_router.get("/challenges/voting-open")
async def get_open_voting_challenge():
    """Get currently open voting challenge (if any) - PUBLIC endpoint"""
    challenge = await db.challenges.find_one(
        {"voting_open": True, "status": "accepted"},
        {"_id": 0}
    )
    
    if not challenge:
        return {"voting_open": False, "challenge": None}
    
    challenger = await db.users.find_one({"id": challenge["challenger_id"]}, {"_id": 0, "display_name": 1})
    opponent = await db.users.find_one({"id": challenge["opponent_id"]}, {"_id": 0, "display_name": 1})
    
    return {
        "voting_open": True,
        "challenge": {
            "id": challenge["id"],
            "challengerId": challenge["challenger_id"],
            "opponentId": challenge["opponent_id"],
            "challengerName": challenger["display_name"] if challenger else "Unknown",
            "opponentName": opponent["display_name"] if opponent else "Unknown",
            "challengeType": challenge["type"],
            "typeName": CHALLENGE_TYPES.get(challenge["type"], {}).get("name", "Battle"),
            "votes": len(challenge.get("votes", [])),
            "voting_started_at": challenge.get("voting_started_at")
        }
    }

@api_router.get("/challenges/{challenge_id}")
async def get_challenge(challenge_id: str, user: dict = Depends(get_current_user)):
    """Get a specific challenge"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    challenger = await db.users.find_one({"id": challenge["challenger_id"]}, {"_id": 0, "display_name": 1, "rank": 1, "points": 1})
    opponent = await db.users.find_one({"id": challenge["opponent_id"]}, {"_id": 0, "display_name": 1, "rank": 1, "points": 1})
    
    # Count votes per person
    votes = challenge.get("votes", [])
    vote_count = {}
    for v in votes:
        vote_count[v["vote_for"]] = vote_count.get(v["vote_for"], 0) + 1
    
    # Check if current user voted
    user_voted = any(v["voter_id"] == user["id"] for v in votes)
    
    challenge["challenger"] = challenger
    challenge["opponent"] = opponent
    challenge["type_info"] = CHALLENGE_TYPES.get(challenge["type"], {})
    challenge["vote_count"] = len(votes)
    challenge["challenger_votes"] = vote_count.get(challenge["challenger_id"], 0)
    challenge["opponent_votes"] = vote_count.get(challenge["opponent_id"], 0)
    challenge["user_voted"] = user_voted
    
    return challenge

# ==================== RANKS INFO ====================
@api_router.get("/ranks")
async def get_ranks():
    return RANKS

# ==================== WEBSOCKET & LIVE VOTING ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for messages
            data = await websocket.receive_text()
            # Echo back or handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@api_router.post("/challenges/{challenge_id}/open-voting")
async def open_voting(challenge_id: str, admin: dict = Depends(get_admin_user)):
    """Open voting for a challenge - broadcasts to all connected clients"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["status"] != "accepted":
        raise HTTPException(status_code=400, detail="Challenge must be accepted to open voting")
    
    # Get user names
    challenger = await db.users.find_one({"id": challenge["challenger_id"]}, {"_id": 0, "display_name": 1})
    opponent = await db.users.find_one({"id": challenge["opponent_id"]}, {"_id": 0, "display_name": 1})
    
    # Mark voting as open
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {"voting_open": True, "voting_started_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Broadcast to all connected clients
    await manager.broadcast({
        "type": "OPEN_VOTING",
        "challenge": {
            "id": challenge_id,
            "challengerId": challenge["challenger_id"],
            "opponentId": challenge["opponent_id"],
            "challengerName": challenger["display_name"] if challenger else "Unknown",
            "opponentName": opponent["display_name"] if opponent else "Unknown",
            "challengeType": challenge["type"],
            "typeName": CHALLENGE_TYPES.get(challenge["type"], {}).get("name", "Battle")
        }
    })
    
    return {"message": "Voting opened! All users notified.", "challenge_id": challenge_id}

@api_router.post("/challenges/{challenge_id}/close-voting")
async def close_voting(challenge_id: str, admin: dict = Depends(get_admin_user)):
    """Close voting and finalize the challenge"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Broadcast voting closed
    await manager.broadcast({
        "type": "CLOSE_VOTING",
        "challengeId": challenge_id
    })
    
    # Update challenge
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {"voting_open": False}}
    )
    
    return {"message": "Voting closed"}

# ==================== QR CODE CHECK-IN ====================
import hashlib
VENUE_SECRET = os.environ.get('VENUE_SECRET', 'king-karaoke-2024')
CHECKIN_POINTS = 50

@api_router.get("/venue/qr-data")
async def get_venue_qr_data(admin: dict = Depends(get_admin_user)):
    """Get QR code data for venue check-in (admin only)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_code = hashlib.sha256(f"{VENUE_SECRET}-{today}".encode()).hexdigest()[:12]
    
    return {
        "venue_code": daily_code,
        "date": today,
        "checkin_url": f"/checkin/{daily_code}"
    }

@api_router.post("/checkin/{venue_code}")
async def perform_checkin(venue_code: str, user: dict = Depends(get_current_user)):
    """Perform a venue check-in via QR code"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    expected_code = hashlib.sha256(f"{VENUE_SECRET}-{today}".encode()).hexdigest()[:12]
    
    if venue_code != expected_code:
        raise HTTPException(status_code=400, detail="Invalid or expired QR code")
    
    existing_checkin = await db.checkins.find_one({
        "user_id": user["id"],
        "date": today
    })
    
    if existing_checkin:
        return {
            "success": False,
            "message": "You've already checked in today!",
            "already_checked_in": True,
            "points_awarded": 0
        }
    
    checkin = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "date": today,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "venue_code": venue_code
    }
    await db.checkins.insert_one(checkin)
    
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_checkin = await db.checkins.find_one({
        "user_id": user["id"],
        "date": yesterday
    })
    
    current_consecutive = user.get("consecutive_visits", 0)
    if yesterday_checkin:
        new_consecutive = current_consecutive + 1
    else:
        new_consecutive = 1
    
    await db.users.update_one(
        {"id": user["id"]},
        {
            "$inc": {"points": CHECKIN_POINTS, "total_checkins": 1},
            "$set": {"consecutive_visits": new_consecutive, "last_checkin": today}
        }
    )
    
    badges_earned = []
    bonus_points = 0
    user_badges = list(user.get("badges", []))
    
    if new_consecutive >= 3 and "night_owl" not in user_badges:
        user_badges.append("night_owl")
        badges_earned.append("night_owl")
        bonus_points += BADGES["night_owl"]["points_reward"]
    
    if new_consecutive >= 5 and "dedicated_fan" not in user_badges:
        user_badges.append("dedicated_fan")
        badges_earned.append("dedicated_fan")
        bonus_points += BADGES["dedicated_fan"]["points_reward"]
    
    if new_consecutive >= 10 and "loyal_patron" not in user_badges:
        user_badges.append("loyal_patron")
        badges_earned.append("loyal_patron")
        bonus_points += BADGES["loyal_patron"]["points_reward"]
    
    if badges_earned:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"badges": user_badges}, "$inc": {"points": bonus_points}}
        )
        for badge_id in badges_earned:
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "badge_id": badge_id,
                "badge_name": BADGES[badge_id]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
    
    return {
        "success": True,
        "message": f"Welcome to King Karaoke! +{CHECKIN_POINTS} points",
        "points_awarded": CHECKIN_POINTS,
        "bonus_points": bonus_points,
        "consecutive_visits": new_consecutive,
        "badges_earned": [BADGES[b]["name"] for b in badges_earned],
        "already_checked_in": False
    }

@api_router.get("/checkin/status/today")
async def get_today_checkin_status(user: dict = Depends(get_current_user)):
    """Check if user has checked in today"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = await db.checkins.find_one({
        "user_id": user["id"],
        "date": today
    })
    
    return {
        "checked_in_today": existing is not None,
        "consecutive_visits": user.get("consecutive_visits", 0),
        "total_checkins": user.get("total_checkins", 0)
    }

@api_router.get("/admin/checkins/today")
async def get_today_checkins(admin: dict = Depends(get_admin_user)):
    """Get all check-ins for today (admin only)"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    checkins = await db.checkins.find(
        {"date": today},
        {"_id": 0}
    ).to_list(500)
    
    for checkin in checkins:
        u = await db.users.find_one({"id": checkin["user_id"]}, {"_id": 0, "display_name": 1})
        checkin["user_name"] = u["display_name"] if u else "Unknown"
    
    return {
        "date": today,
        "total_checkins": len(checkins),
        "checkins": checkins
    }

# ==================== ROOT ====================
@api_router.get("/")
async def root():
    return {"message": "King Klub API", "version": "1.0.0"}

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
