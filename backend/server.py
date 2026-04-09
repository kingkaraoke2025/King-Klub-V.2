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
JWT_SECRET = os.environ['JWT_SECRET']
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
    {"name": "Peasant", "name_female": "Peasant", "min_points": 0, "icon": "shield"},
    {"name": "Squire", "name_female": "Lady", "min_points": 500, "icon": "sword"},
    {"name": "Knight", "name_female": "Dame", "min_points": 1000, "icon": "swords"},
    {"name": "Count", "name_female": "Countess", "min_points": 1500, "icon": "crown"},
    {"name": "Duke", "name_female": "Duchess", "min_points": 2000, "icon": "gem"},
    {"name": "Prince", "name_female": "Princess", "min_points": 2500, "icon": "sparkles"},
]

# ==================== RANK PERKS ====================
# Queue position perks based on rank
RANK_PERKS = {
    "Peasant": None,  # No perk
    "Squire": {"type": "jump_ahead", "value": 3, "description": "Jump ahead 3 spots in queue"},
    "Lady": {"type": "jump_ahead", "value": 3, "description": "Jump ahead 3 spots in queue"},
    "Knight": {"type": "jump_ahead", "value": 5, "description": "Jump ahead 5 spots in queue"},
    "Dame": {"type": "jump_ahead", "value": 5, "description": "Jump ahead 5 spots in queue"},
    "Count": {"type": "jump_to", "value": 5, "description": "Jump to 5th spot in queue"},
    "Countess": {"type": "jump_to", "value": 5, "description": "Jump to 5th spot in queue"},
    "Duke": {"type": "jump_to", "value": 2, "description": "Jump to 2nd spot in queue"},
    "Duchess": {"type": "jump_to", "value": 2, "description": "Jump to 2nd spot in queue"},
    "Prince": {"type": "jump_to", "value": 1, "description": "Jump to 1st spot in queue"},
    "Princess": {"type": "jump_to", "value": 1, "description": "Jump to 1st spot in queue"},
}

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
    title_preference: Optional[str] = "male"  # "male" or "female" for rank titles
    referred_by: Optional[str] = None  # User ID of the person who referred them

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
    title_preference: Optional[str] = "male"

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
    message_to_admin: Optional[str] = None  # Message to admin (max 250 chars)
    status: str  # pending, current, completed, cancelled
    position: int
    estimated_wait: int
    created_at: str

class AddSongRequest(BaseModel):
    song_title: str
    artist: str
    message_to_admin: Optional[str] = None  # Message to admin (max 250 chars)

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
    "tip_bartender": {"name": "Tip the Bartender", "points": 10, "description": "Show appreciation to the bartender"},
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
    "royal_recruiter": {"name": "Royal Recruiter", "description": "Bring 1 friend to King Karaoke", "icon": "user-plus", "points_reward": 10, "category": "social"},
    "social_butterfly": {"name": "Social Butterfly", "description": "Bring 3 friends to King Karaoke", "icon": "users-round", "points_reward": 30, "category": "social"},
    "kk_ambassador": {"name": "King Karaoke Ambassador", "description": "Bring 5 friends to King Karaoke", "icon": "megaphone", "points_reward": 50, "category": "social"},
    "influencer": {"name": "Influencer", "description": "Posted to TikTok", "icon": "video", "points_reward": 200, "category": "social"},
    "super_fan": {"name": "Super Fan", "description": "Followed on TikTok & Facebook", "icon": "thumbs-up", "points_reward": 20, "category": "social"},
    
    # Loyalty badges - Consecutive visits
    "night_owl": {"name": "Night Owl", "description": "Visited 3 consecutive nights", "icon": "moon", "points_reward": 25, "category": "loyalty"},
    "dedicated_fan": {"name": "Dedicated Fan", "description": "Visited 5 consecutive nights", "icon": "flame", "points_reward": 50, "category": "loyalty"},
    "loyal_patron": {"name": "Loyal Patron", "description": "Visited 10 consecutive nights", "icon": "award", "points_reward": 100, "category": "loyalty"},
    # Loyalty badges - Total nights attended
    "loyal_subject": {"name": "Loyal Subject", "description": "Attend 3 different karaoke nights", "icon": "calendar", "points_reward": 10, "category": "loyalty"},
    "court_regular": {"name": "Court Regular", "description": "Attend 5 different karaoke nights", "icon": "crown", "points_reward": 25, "category": "loyalty"},
    
    # Generosity - KJ tips
    "generous_tipper": {"name": "Generous Tipper", "description": "Tipped the KJ", "icon": "coins", "points_reward": 10, "category": "generosity"},
    "big_tipper": {"name": "Big Tipper", "description": "Tipped the KJ 5 times", "icon": "banknote", "points_reward": 50, "category": "generosity"},
    # Generosity - Bartender tips
    "benevolent_tipper": {"name": "Benevolent Tipper", "description": "Tipped the bartender", "icon": "beer", "points_reward": 10, "category": "generosity"},
    "huge_tipper": {"name": "Huge Tipper", "description": "Tipped the bartender 5 times", "icon": "gift", "points_reward": 50, "category": "generosity"},
    
    # Battle badges
    "first_battle": {"name": "First Blood", "description": "Participated in your first battle", "icon": "swords", "points_reward": 25, "category": "battle"},
    "battle_winner": {"name": "Battle Victor", "description": "Won your first battle", "icon": "trophy", "points_reward": 50, "category": "battle"},
    "duel_master": {"name": "Duel Master", "description": "Won 5 battles", "icon": "crown", "points_reward": 100, "category": "battle"},
    "crowd_champion": {"name": "Crowd Champion", "description": "Won a battle with 10+ votes", "icon": "users", "points_reward": 75, "category": "battle"},
    
    # Nightly champion
    "nightly_champion": {"name": "Nightly Champion", "description": "Finished #1 on tonight's leaderboard", "icon": "moon-star", "points_reward": 25, "category": "performance"},
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
async def check_referral_badges(referrer_id: str):
    """Check and award referral badges to the referrer"""
    # Count how many users this person has referred
    referral_count = await db.users.count_documents({"referred_by": referrer_id})
    
    referrer = await db.users.find_one({"id": referrer_id}, {"_id": 0})
    if not referrer:
        return
    
    badges = list(referrer.get("badges", []))
    badges_earned = []
    bonus_points = 0
    
    # 1 friend badge
    if referral_count >= 1 and "royal_recruiter" not in badges:
        badges.append("royal_recruiter")
        badges_earned.append("royal_recruiter")
        bonus_points += BADGES["royal_recruiter"]["points_reward"]
    
    # 3 friends badge
    if referral_count >= 3 and "social_butterfly" not in badges:
        badges.append("social_butterfly")
        badges_earned.append("social_butterfly")
        bonus_points += BADGES["social_butterfly"]["points_reward"]
    
    # 5 friends badge
    if referral_count >= 5 and "kk_ambassador" not in badges:
        badges.append("kk_ambassador")
        badges_earned.append("kk_ambassador")
        bonus_points += BADGES["kk_ambassador"]["points_reward"]
    
    if badges_earned:
        active_night = await is_active_night()
        badge_update = {"$set": {"badges": badges}, "$inc": {"points": bonus_points}}
        if active_night:
            badge_update["$inc"]["nightly_points"] = bonus_points
        await db.users.update_one({"id": referrer_id}, badge_update)
        for badge_id in badges_earned:
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": referrer_id,
                "badge_id": badge_id,
                "badge_name": BADGES[badge_id]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })

@api_router.post("/auth/register")
async def register(data: UserCreate):
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate referrer if provided
    referrer_id = None
    if data.referred_by:
        referrer = await db.users.find_one({"id": data.referred_by})
        if referrer:
            referrer_id = data.referred_by
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email,
        "password": hash_password(data.password),
        "display_name": data.display_name,
        "title_preference": data.title_preference or "male",
        "referred_by": referrer_id,
        "points": 0,
        "songs_performed": 0,
        "consecutive_visits": 0,
        "badges": [],
        "is_admin": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_visit": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    # Check referral badges for the inviter
    if referrer_id:
        await check_referral_badges(referrer_id)
    
    token = create_token(user_id)
    rank = get_rank(0)
    next_rank = get_next_rank(0)
    
    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": data.email,
            "display_name": data.display_name,
            "title_preference": user["title_preference"],
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
            "title_preference": user.get("title_preference", "male"),
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
        "title_preference": user.get("title_preference", "male"),
        "points": user["points"],
        "songs_performed": user["songs_performed"],
        "consecutive_visits": user["consecutive_visits"],
        "rank": rank,
        "next_rank": next_rank,
        "badges": user["badges"],
        "is_admin": user.get("is_admin", False),
        "created_at": user["created_at"]
    }


@api_router.get("/auth/referral-stats")
async def get_referral_stats(user: dict = Depends(get_current_user)):
    """Get user's referral statistics and link"""
    referral_count = await db.users.count_documents({"referred_by": user["id"]})
    
    # Get list of referred users
    referred_users = await db.users.find(
        {"referred_by": user["id"]},
        {"_id": 0, "display_name": 1, "created_at": 1}
    ).to_list(50)
    
    return {
        "referral_code": user["id"],
        "total_referrals": referral_count,
        "referred_users": referred_users,
        "next_badge": (
            "Royal Recruiter" if referral_count < 1 else
            "Social Butterfly" if referral_count < 3 else
            "King Karaoke Ambassador" if referral_count < 5 else
            None
        ),
        "referrals_to_next": (
            1 - referral_count if referral_count < 1 else
            3 - referral_count if referral_count < 3 else
            5 - referral_count if referral_count < 5 else
            0
        )
    }



class UpdateTitlePreferenceRequest(BaseModel):
    title_preference: str  # "male" or "female"

@api_router.put("/auth/title-preference")
async def update_title_preference(data: UpdateTitlePreferenceRequest, user: dict = Depends(get_current_user)):
    if data.title_preference not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Invalid title preference. Use 'male' or 'female'")
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"title_preference": data.title_preference}}
    )
    
    return {"message": "Title preference updated", "title_preference": data.title_preference}


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
    # Admins are exempt from QR check-in and song limits
    is_admin = user.get("is_admin", False)
    
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(VENUE_TIMEZONE)
    now = datetime.now(tz)
    
    # Use same date logic as QR code (4 AM cutoff)
    if now.hour < QR_CODE_CUTOFF_HOUR:
        effective_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        effective_date = now.strftime("%Y-%m-%d")
    
    songs_this_window = 0
    minutes_until_reset = 30
    
    # Only check for QR check-in and song limits if NOT admin
    if not is_admin:
        checkin_today = await db.checkins.find_one({
            "user_id": user["id"],
            "date": effective_date
        })
        
        if not checkin_today:
            raise HTTPException(status_code=400, detail="Please check in with the QR code first to add songs to the queue")
        
        # Calculate current 30-minute window since check-in
        checkin_time = datetime.fromisoformat(checkin_today["timestamp"].replace('Z', '+00:00'))
        time_since_checkin = datetime.now(timezone.utc) - checkin_time
        minutes_since_checkin = int(time_since_checkin.total_seconds() / 60)
        current_window = minutes_since_checkin // 30  # Which 30-min window we're in (0, 1, 2, etc.)
        
        # Calculate window start and end times
        window_start = checkin_time + timedelta(minutes=current_window * 30)
        window_end = window_start + timedelta(minutes=30)
        
        # Count songs added in the current 30-minute window
        songs_this_window = await db.queue.count_documents({
            "user_id": user["id"],
            "created_at": {
                "$gte": window_start.isoformat(),
                "$lt": window_end.isoformat()
            }
        })
        
        if songs_this_window >= 5:
            minutes_until_reset = 30 - (minutes_since_checkin % 30)
            raise HTTPException(
                status_code=400, 
                detail=f"You've added 5 songs this window. Limit resets in {minutes_until_reset} minutes!"
            )
        
        minutes_until_reset = 30 - (minutes_since_checkin % 30)
    
    # Validate message length
    message = data.message_to_admin
    if message and len(message) > 250:
        message = message[:250]  # Truncate to 250 chars
    
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
        "message_to_admin": message,
        "status": "pending",
        "position": position,
        "estimated_wait": (position - 1) * 4,  # ~4 minutes per song
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.queue.insert_one(queue_item)
    
    # Return without _id
    if "_id" in queue_item:
        del queue_item["_id"]
    
    # Broadcast queue update to all connected clients
    await manager.broadcast({
        "type": "QUEUE_UPDATED",
        "action": "song_added",
        "item": queue_item
    })
    
    # For admins, return unlimited values
    if is_admin:
        return {
            **queue_item,
            "songs_this_window": 0,
            "songs_remaining": 999,
            "window_resets_in": 0,
            "is_admin": True
        }
    
    return {
        **queue_item,
        "songs_this_window": songs_this_window + 1,
        "songs_remaining": 5 - (songs_this_window + 1),
        "window_resets_in": minutes_until_reset
    }

@api_router.get("/queue/my-status")
async def get_my_queue_status(user: dict = Depends(get_current_user)):
    """Get user's queue status including songs count and time remaining"""
    # Admins are exempt from QR check-in and song limits
    is_admin = user.get("is_admin", False)
    
    if is_admin:
        # Get admin's pending songs
        user_songs = await db.queue.find({
            "user_id": user["id"],
            "status": {"$in": ["pending", "current"]}
        }, {"_id": 0}).sort("position", 1).to_list(20)
        
        return {
            "checked_in": True,  # Admins are always "checked in"
            "is_admin": True,
            "can_add_songs": True,
            "songs_this_window": 0,
            "songs_remaining": 999,  # Unlimited for admins
            "max_songs_per_window": 999,
            "window_resets_in": 0,
            "total_songs_in_queue": len(user_songs),
            "my_songs": user_songs,
            "reason": None
        }
    
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(VENUE_TIMEZONE)
    now = datetime.now(tz)
    
    # Use same date logic as QR code (4 AM cutoff)
    if now.hour < QR_CODE_CUTOFF_HOUR:
        effective_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        effective_date = now.strftime("%Y-%m-%d")
    
    checkin_today = await db.checkins.find_one({
        "user_id": user["id"],
        "date": effective_date
    })
    
    if not checkin_today:
        return {
            "checked_in": False,
            "can_add_songs": False,
            "reason": "Please check in with the QR code first",
            "songs_this_window": 0,
            "max_songs_per_window": 5
        }
    
    # Calculate current 30-minute window
    checkin_time = datetime.fromisoformat(checkin_today["timestamp"].replace('Z', '+00:00'))
    time_since_checkin = datetime.now(timezone.utc) - checkin_time
    minutes_since_checkin = int(time_since_checkin.total_seconds() / 60)
    current_window = minutes_since_checkin // 30
    
    # Calculate window times
    window_start = checkin_time + timedelta(minutes=current_window * 30)
    window_end = window_start + timedelta(minutes=30)
    minutes_until_reset = 30 - (minutes_since_checkin % 30)
    
    # Count songs added in current window
    songs_this_window = await db.queue.count_documents({
        "user_id": user["id"],
        "created_at": {
            "$gte": window_start.isoformat(),
            "$lt": window_end.isoformat()
        }
    })
    
    # Get user's pending songs
    user_songs = await db.queue.find({
        "user_id": user["id"],
        "status": {"$in": ["pending", "current"]}
    }, {"_id": 0}).sort("position", 1).to_list(20)
    
    can_add = songs_this_window < 5
    
    return {
        "checked_in": True,
        "checkin_time": checkin_today["timestamp"],
        "minutes_since_checkin": minutes_since_checkin,
        "current_window": current_window + 1,  # Human-friendly (1st, 2nd, etc.)
        "window_resets_in": minutes_until_reset,
        "can_add_songs": can_add,
        "songs_this_window": songs_this_window,
        "songs_remaining": 5 - songs_this_window,
        "max_songs_per_window": 5,
        "total_songs_in_queue": len(user_songs),
        "my_songs": user_songs,
        "reason": None if can_add else f"5 song limit reached. Resets in {minutes_until_reset} min!"
    }


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
    
    # Broadcast queue update
    await manager.broadcast({
        "type": "QUEUE_UPDATED",
        "action": "song_removed",
        "item_id": item_id
    })
    
    return {"message": "Removed from queue"}


# ==================== RANK PERK SYSTEM ====================
def get_user_rank_name(user: dict) -> str:
    """Get the user's rank name based on their points and title preference"""
    rank = get_rank(user["points"])
    if user.get("title_preference") == "female" and rank.get("name_female"):
        return rank["name_female"]
    return rank["name"]

@api_router.get("/queue/perk-status")
async def get_perk_status(user: dict = Depends(get_current_user)):
    """Check if user can use their rank perk tonight"""
    rank_name = get_user_rank_name(user)
    perk = RANK_PERKS.get(rank_name)
    
    if not perk:
        return {
            "has_perk": False,
            "rank": rank_name,
            "perk": None,
            "can_use": False,
            "reason": "Peasants don't have queue perks. Earn 500 points to unlock!"
        }
    
    # Check if user has checked in today
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(VENUE_TIMEZONE)
    now = datetime.now(tz)
    
    # Use same date logic as QR code (4 AM cutoff)
    if now.hour < QR_CODE_CUTOFF_HOUR:
        effective_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        effective_date = now.strftime("%Y-%m-%d")
    
    checkin_today = await db.checkins.find_one({
        "user_id": user["id"],
        "date": effective_date
    })
    
    if not checkin_today:
        return {
            "has_perk": True,
            "rank": rank_name,
            "perk": perk,
            "can_use": False,
            "reason": "You must check in with the QR code first to use your perk tonight"
        }
    
    # Check if perk already used today
    perk_used = await db.perk_usage.find_one({
        "user_id": user["id"],
        "date": effective_date
    })
    
    if perk_used:
        return {
            "has_perk": True,
            "rank": rank_name,
            "perk": perk,
            "can_use": False,
            "reason": "You've already used your perk tonight. Come back tomorrow!"
        }
    
    # Check if user has a song in queue
    queue_item = await db.queue.find_one({
        "user_id": user["id"],
        "status": "pending"
    })
    
    if not queue_item:
        return {
            "has_perk": True,
            "rank": rank_name,
            "perk": perk,
            "can_use": False,
            "reason": "Add a song to the queue first, then use your perk!"
        }
    
    return {
        "has_perk": True,
        "rank": rank_name,
        "perk": perk,
        "can_use": True,
        "queue_position": queue_item["position"],
        "song": f"{queue_item['song_title']} - {queue_item['artist']}"
    }

@api_router.post("/queue/use-perk")
async def use_rank_perk(user: dict = Depends(get_current_user)):
    """Use the rank perk to move up in the queue"""
    rank_name = get_user_rank_name(user)
    perk = RANK_PERKS.get(rank_name)
    
    if not perk:
        raise HTTPException(status_code=400, detail="Your rank doesn't have a queue perk")
    
    # Check if user has checked in today
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(VENUE_TIMEZONE)
    now = datetime.now(tz)
    
    if now.hour < QR_CODE_CUTOFF_HOUR:
        effective_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        effective_date = now.strftime("%Y-%m-%d")
    
    checkin_today = await db.checkins.find_one({
        "user_id": user["id"],
        "date": effective_date
    })
    
    if not checkin_today:
        raise HTTPException(status_code=400, detail="You must check in with the QR code first")
    
    # Check if perk already used
    perk_used = await db.perk_usage.find_one({
        "user_id": user["id"],
        "date": effective_date
    })
    
    if perk_used:
        raise HTTPException(status_code=400, detail="You've already used your perk tonight")
    
    # Get user's queue item
    queue_item = await db.queue.find_one({
        "user_id": user["id"],
        "status": "pending"
    }, {"_id": 0})
    
    if not queue_item:
        raise HTTPException(status_code=400, detail="You don't have a song in the queue")
    
    old_position = queue_item["position"]
    
    # Calculate new position based on perk type
    if perk["type"] == "jump_ahead":
        new_position = max(1, old_position - perk["value"])
    else:  # jump_to
        new_position = perk["value"]
    
    # Don't move if already at or ahead of target
    if old_position <= new_position:
        raise HTTPException(status_code=400, detail=f"You're already at position {old_position}, no need to use perk!")
    
    # Move other items down to make room
    items_to_shift = await db.queue.find({
        "status": "pending",
        "position": {"$gte": new_position, "$lt": old_position}
    }).to_list(100)
    
    for item in items_to_shift:
        await db.queue.update_one(
            {"id": item["id"]},
            {"$set": {"position": item["position"] + 1, "estimated_wait": item["position"] * 4}}
        )
    
    # Move user's item to new position
    # Mark as perk_protected if moving into top 4 positions
    perk_protected = new_position <= 4
    await db.queue.update_one(
        {"id": queue_item["id"]},
        {"$set": {
            "position": new_position, 
            "estimated_wait": (new_position - 1) * 4,
            "perk_protected": perk_protected
        }}
    )
    
    # Record perk usage
    await db.perk_usage.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "date": effective_date,
        "rank": rank_name,
        "perk_type": perk["type"],
        "old_position": old_position,
        "new_position": new_position,
        "used_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Notify admin via WebSocket
    await manager.broadcast({
        "type": "PERK_USED",
        "user_name": user["display_name"],
        "rank": rank_name,
        "perk_description": perk["description"],
        "song": f"{queue_item['song_title']} - {queue_item['artist']}",
        "old_position": old_position,
        "new_position": new_position
    })
    
    # Also store notification for admin panel
    await db.admin_notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "perk_used",
        "message": f"{user['display_name']} ({rank_name}) used their perk: moved from #{old_position} to #{new_position}",
        "user_id": user["id"],
        "user_name": user["display_name"],
        "rank": rank_name,
        "song": f"{queue_item['song_title']} - {queue_item['artist']}",
        "old_position": old_position,
        "new_position": new_position,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False
    })
    
    return {
        "message": f"Perk activated! Moved from #{old_position} to #{new_position}",
        "old_position": old_position,
        "new_position": new_position,
        "perk_used": perk["description"]
    }


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
    
    # Broadcast queue update
    await manager.broadcast({
        "type": "QUEUE_UPDATED",
        "action": "song_now_playing",
        "item_id": item_id
    })
    
    return {"message": "Current song updated"}

@api_router.post("/admin/queue/{item_id}/move-up")
async def move_song_up(item_id: str, admin: dict = Depends(get_admin_user)):
    """Move a song up one position in the queue (admin only)"""
    item = await db.queue.find_one({"id": item_id, "status": "pending"}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found or not pending")
    
    current_position = item["position"]
    
    # Can't move up if already at position 1
    if current_position <= 1:
        raise HTTPException(status_code=400, detail="Song is already at the top of the queue")
    
    # Check if this song is perk protected
    if item.get("perk_protected"):
        raise HTTPException(status_code=400, detail="This song used a perk to get here and cannot be moved")
    
    new_position = current_position - 1
    
    # Find the song currently at the target position
    song_above = await db.queue.find_one({
        "status": "pending",
        "position": new_position
    }, {"_id": 0})
    
    # Check if the song above is perk protected (in top 4)
    if song_above and song_above.get("perk_protected") and new_position <= 4:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot move above position {new_position} - that song used a perk and is protected"
        )
    
    # Swap positions
    if song_above:
        await db.queue.update_one(
            {"id": song_above["id"]},
            {"$set": {"position": current_position, "estimated_wait": (current_position - 1) * 4}}
        )
    
    await db.queue.update_one(
        {"id": item_id},
        {"$set": {"position": new_position, "estimated_wait": (new_position - 1) * 4}}
    )
    
    # Broadcast queue update
    await manager.broadcast({
        "type": "QUEUE_UPDATED",
        "action": "queue_reordered"
    })
    
    return {
        "message": f"Moved '{item['song_title']}' from #{current_position} to #{new_position}",
        "old_position": current_position,
        "new_position": new_position
    }

@api_router.post("/admin/queue/{item_id}/move-down")
async def move_song_down(item_id: str, admin: dict = Depends(get_admin_user)):
    """Move a song down one position in the queue (admin only)"""
    item = await db.queue.find_one({"id": item_id, "status": "pending"}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found or not pending")
    
    current_position = item["position"]
    
    # Check if this song is perk protected (in top 4)
    if item.get("perk_protected") and current_position <= 4:
        raise HTTPException(status_code=400, detail="This song used a perk to get here and cannot be moved")
    
    # Find the max position
    last_item = await db.queue.find_one(
        {"status": "pending"},
        sort=[("position", -1)]
    )
    max_position = last_item["position"] if last_item else 1
    
    # Can't move down if already at the bottom
    if current_position >= max_position:
        raise HTTPException(status_code=400, detail="Song is already at the bottom of the queue")
    
    new_position = current_position + 1
    
    # Find the song currently at the target position
    song_below = await db.queue.find_one({
        "status": "pending",
        "position": new_position
    }, {"_id": 0})
    
    # Swap positions
    if song_below:
        await db.queue.update_one(
            {"id": song_below["id"]},
            {"$set": {"position": current_position, "estimated_wait": (current_position - 1) * 4}}
        )
    
    await db.queue.update_one(
        {"id": item_id},
        {"$set": {"position": new_position, "estimated_wait": (new_position - 1) * 4}}
    )
    
    # Broadcast queue update
    await manager.broadcast({
        "type": "QUEUE_UPDATED",
        "action": "queue_reordered"
    })
    
    return {
        "message": f"Moved '{item['song_title']}' from #{current_position} to #{new_position}",
        "old_position": current_position,
        "new_position": new_position
    }

class ReorderRequest(BaseModel):
    new_position: int

@api_router.post("/admin/queue/{item_id}/reorder")
async def reorder_song(item_id: str, data: ReorderRequest, admin: dict = Depends(get_admin_user)):
    """Move a song to a specific position in the queue (admin only) - for drag and drop"""
    item = await db.queue.find_one({"id": item_id, "status": "pending"}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found or not pending")
    
    current_position = item["position"]
    new_position = data.new_position
    
    # No change needed
    if current_position == new_position:
        return {"message": "No change", "position": current_position}
    
    # Check if this song is perk protected and in top 4
    if item.get("perk_protected") and current_position <= 4:
        raise HTTPException(status_code=400, detail="This song used a perk and cannot be moved")
    
    # Get all pending songs
    all_pending = await db.queue.find({"status": "pending"}, {"_id": 0}).sort("position", 1).to_list(200)
    max_position = len(all_pending)
    
    # Validate new position
    if new_position < 1 or new_position > max_position:
        raise HTTPException(status_code=400, detail=f"Invalid position. Must be between 1 and {max_position}")
    
    # Check if we're trying to move above a perk-protected song in top 4
    if new_position < current_position:
        # Moving up - check if any song in the way is perk protected in top 4
        for song in all_pending:
            if song["position"] >= new_position and song["position"] < current_position:
                if song.get("perk_protected") and song["position"] <= 4 and new_position <= 4:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Cannot move above position {song['position']} - that song is perk protected"
                    )
    
    # Perform the reorder
    if new_position < current_position:
        # Moving up: shift songs between new and current down by 1
        await db.queue.update_many(
            {
                "status": "pending",
                "position": {"$gte": new_position, "$lt": current_position}
            },
            {"$inc": {"position": 1}}
        )
    else:
        # Moving down: shift songs between current and new up by 1
        await db.queue.update_many(
            {
                "status": "pending",
                "position": {"$gt": current_position, "$lte": new_position}
            },
            {"$inc": {"position": -1}}
        )
    
    # Move the item to new position
    await db.queue.update_one(
        {"id": item_id},
        {"$set": {"position": new_position, "estimated_wait": (new_position - 1) * 4}}
    )
    
    # Update estimated wait times for all affected songs
    updated_songs = await db.queue.find({"status": "pending"}, {"_id": 0}).sort("position", 1).to_list(200)
    for song in updated_songs:
        await db.queue.update_one(
            {"id": song["id"]},
            {"$set": {"estimated_wait": (song["position"] - 1) * 4}}
        )
    
    # Broadcast queue update
    await manager.broadcast({
        "type": "QUEUE_UPDATED",
        "action": "queue_reordered"
    })
    
    return {
        "message": f"Moved '{item['song_title']}' from #{current_position} to #{new_position}",
        "old_position": current_position,
        "new_position": new_position
    }

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
            "title_preference": user.get("title_preference", "male"),
            "points": user["points"],
            "rank": get_rank(user["points"]),
            "songs_performed": user["songs_performed"],
            "badges": user["badges"]
        })
    
    return leaderboard

@api_router.get("/leaderboard/tonight")
async def get_tonight_leaderboard():
    """Get tonight's leaderboard (points earned tonight only)"""
    # Check if there's an active QR session for today
    today = get_venue_date()
    settings = await db.settings.find_one({"key": "current_night"})
    current_night = settings.get("value") if settings else None
    
    # Only show leaderboard if there's an active session for TODAY
    # If current_night doesn't match today, return empty (session ended or not started)
    if current_night != today:
        return {
            "date": today,
            "active": False,
            "leaderboard": []
        }
    
    users = await db.users.find(
        {"nightly_points": {"$gt": 0}},
        {"_id": 0, "password": 0, "email": 0}
    ).sort("nightly_points", -1).limit(20).to_list(20)
    
    leaderboard = []
    for i, user in enumerate(users):
        leaderboard.append({
            "position": i + 1,
            "id": user["id"],
            "display_name": user["display_name"],
            "title_preference": user.get("title_preference", "male"),
            "nightly_points": user.get("nightly_points", 0),
            "rank": get_rank(user["points"]),
            "badges": user.get("badges", [])
        })
    
    return {
        "date": current_night,
        "active": True,
        "leaderboard": leaderboard
    }

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
    # Only add to nightly_points if there's an active QR session
    active_night = await is_active_night()
    update_inc = {"points": points}
    if active_night:
        update_inc["nightly_points"] = points
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$inc": update_inc}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Broadcast points/leaderboard update
    await manager.broadcast({
        "type": "POINTS_UPDATED",
        "user_id": user_id
    })
    
    return {"message": f"Added {points} points" + (" (nightly)" if active_night else " (all-time only)")}

@api_router.post("/admin/users/{user_id}/toggle-admin")
async def toggle_admin(user_id: str, admin_user: dict = Depends(get_admin_user)):
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not target.get("is_admin", False)
    await db.users.update_one({"id": user_id}, {"$set": {"is_admin": new_status}})
    return {"message": f"Admin status set to {new_status}"}


@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin_user: dict = Depends(get_admin_user)):
    """Delete a user and all their associated data (admin only)"""
    # Prevent admin from deleting themselves
    if user_id == admin_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user's associated data
    await db.queue.delete_many({"user_id": user_id})
    await db.checkins.delete_many({"user_id": user_id})
    await db.accomplishments.delete_many({"user_id": user_id})
    await db.challenges.delete_many({"$or": [{"challenger_id": user_id}, {"opponent_id": user_id}]})
    await db.votes.delete_many({"user_id": user_id})
    
    # Delete the user
    await db.users.delete_one({"id": user_id})
    
    return {
        "message": f"User '{target['display_name']}' has been deleted",
        "deleted_user_id": user_id
    }

class PasswordResetRequest(BaseModel):
    new_password: str

@api_router.post("/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, data: PasswordResetRequest, admin_user: dict = Depends(get_admin_user)):
    """Admin reset a user's password"""
    # Find the target user
    target = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cannot reset admin passwords through this endpoint
    if target.get("is_admin"):
        raise HTTPException(status_code=403, detail="Cannot reset admin passwords through this endpoint")
    
    # Validate password length
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Hash and update the password
    hashed_password = hash_password(data.new_password)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password": hashed_password}}
    )
    
    return {
        "message": f"Password reset successful for '{target['display_name']}'",
        "user_id": user_id
    }


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
    
    # Tipper badges (KJ)
    if tips >= 1 and "generous_tipper" not in badges:
        badges.append("generous_tipper")
        new_badges.append("generous_tipper")
        bonus_points += BADGES["generous_tipper"]["points_reward"]
    
    if tips >= 5 and "big_tipper" not in badges:
        badges.append("big_tipper")
        new_badges.append("big_tipper")
        bonus_points += BADGES["big_tipper"]["points_reward"]
    
    # Tipper badges (Bartender)
    bartender_tips = stats.get("bartender_tips", 0)
    if bartender_tips >= 1 and "benevolent_tipper" not in badges:
        badges.append("benevolent_tipper")
        new_badges.append("benevolent_tipper")
        bonus_points += BADGES["benevolent_tipper"]["points_reward"]
    
    if bartender_tips >= 5 and "huge_tipper" not in badges:
        badges.append("huge_tipper")
        new_badges.append("huge_tipper")
        bonus_points += BADGES["huge_tipper"]["points_reward"]
    
    # Update user badges and add bonus points (only nightly_points if active session)
    if new_badges:
        active_night = await is_active_night()
        badge_update = {"$set": {"badges": badges}, "$inc": {"points": bonus_points}}
        if active_night:
            badge_update["$inc"]["nightly_points"] = bonus_points
        await db.users.update_one({"id": user_id}, badge_update)
        
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
    
    # Check if there's an active QR session for nightly points
    active_night = await is_active_night()
    
    # Prepare update - only include nightly_points if active QR session
    update_ops = {"$inc": {"points": points}}
    if active_night:
        update_ops["$inc"]["nightly_points"] = points
    
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
    elif data.action_id == "tip_bartender":
        update_ops["$inc"]["action_stats.bartender_tips"] = 1
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
        badge_update = {"$set": {"badges": badges}, "$inc": {"points": bonus_points}}
        if active_night:
            badge_update["$inc"]["nightly_points"] = bonus_points
        await db.users.update_one({"id": data.user_id}, badge_update)
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
    
    # Collect all user IDs and fetch in one query (avoid N+1)
    user_ids = set()
    for c in challenges:
        user_ids.add(c["challenger_id"])
        user_ids.add(c["opponent_id"])
    
    users = await db.users.find(
        {"id": {"$in": list(user_ids)}},
        {"_id": 0, "id": 1, "display_name": 1, "rank": 1, "points": 1}
    ).to_list(100)
    user_map = {u["id"]: u for u in users}
    
    # Add user data to challenges
    for c in challenges:
        c["challenger"] = user_map.get(c["challenger_id"])
        c["opponent"] = user_map.get(c["opponent_id"])
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
    
    # Collect all user IDs and fetch in one query (avoid N+1)
    user_ids = set()
    for c in challenges:
        user_ids.add(c["challenger_id"])
        user_ids.add(c["opponent_id"])
    
    users = await db.users.find(
        {"id": {"$in": list(user_ids)}},
        {"_id": 0, "id": 1, "display_name": 1}
    ).to_list(100)
    user_map = {u["id"]: u for u in users}
    
    for c in challenges:
        c["challenger"] = user_map.get(c["challenger_id"])
        c["opponent"] = user_map.get(c["opponent_id"])
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
    
    # Broadcast notification to opponent that they've been challenged
    await manager.broadcast({
        "type": "BATTLE_CHALLENGE",
        "challenge_id": challenge["id"],
        "challenger_id": user["id"],
        "challenger_name": user["display_name"],
        "opponent_id": data.opponent_id,
        "opponent_name": opponent["display_name"],
        "challenge_type": data.challenge_type,
        "challenge_type_name": CHALLENGE_TYPES[data.challenge_type]["name"]
    })
    
    # Award first battle badge if needed
    user_badges = list(user.get("badges", []))
    if "first_battle" not in user_badges:
        user_badges.append("first_battle")
        active_night = await is_active_night()
        badge_update = {"$set": {"badges": user_badges}, "$inc": {"points": BADGES["first_battle"]["points_reward"]}}
        if active_night:
            badge_update["$inc"]["nightly_points"] = BADGES["first_battle"]["points_reward"]
        await db.users.update_one({"id": user["id"]}, badge_update)
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
    
    # Get challenger info for notification
    challenger = await db.users.find_one({"id": challenge["challenger_id"]}, {"_id": 0, "display_name": 1})
    
    # Broadcast challenge accepted notification
    await manager.broadcast({
        "type": "CHALLENGE_ACCEPTED",
        "challenge_id": challenge_id,
        "challenger_id": challenge["challenger_id"],
        "challenger_name": challenger["display_name"] if challenger else "Unknown",
        "opponent_id": user["id"],
        "opponent_name": user["display_name"],
        "challenge_type": challenge["type"],
        "challenge_type_name": CHALLENGE_TYPES.get(challenge["type"], {}).get("name", "Battle")
    })
    
    # Award first battle badge to opponent if needed
    user_badges = list(user.get("badges", []))
    if "first_battle" not in user_badges:
        user_badges.append("first_battle")
        active_night = await is_active_night()
        badge_update = {"$set": {"badges": user_badges}, "$inc": {"points": BADGES["first_battle"]["points_reward"]}}
        if active_night:
            badge_update["$inc"]["nightly_points"] = BADGES["first_battle"]["points_reward"]
        await db.users.update_one({"id": user["id"]}, badge_update)
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
    
    # Check if active QR session for nightly points
    active_night = await is_active_night()
    winner_total = type_info["points_winner"] + winner_bonus
    winner_update = {"$inc": {"points": winner_total}, "$set": {"badges": winner_badges, "battle_wins": battle_wins}}
    if active_night:
        winner_update["$inc"]["nightly_points"] = winner_total
    await db.users.update_one({"id": winner_id}, winner_update)
    
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
    loser_update = {"$inc": {"points": type_info["points_participant"]}}
    if active_night:
        loser_update["$inc"]["nightly_points"] = type_info["points_participant"]
    await db.users.update_one({"id": loser_id}, loser_update)
    
    winner_user = await db.users.find_one({"id": winner_id}, {"_id": 0, "display_name": 1})
    loser_user = await db.users.find_one({"id": loser_id}, {"_id": 0, "display_name": 1})
    
    # Broadcast battle ended notification
    await manager.broadcast({
        "type": "BATTLE_ENDED",
        "challenge_id": challenge_id,
        "winner_id": winner_id,
        "winner_name": winner_user["display_name"],
        "loser_id": loser_id,
        "loser_name": loser_user["display_name"],
        "winner_votes": vote_count[winner_id],
        "loser_votes": vote_count.get(loser_id, 0),
        "challenge_type": challenge["type"],
        "challenge_type_name": CHALLENGE_TYPES.get(challenge["type"], {}).get("name", "Battle")
    })
    
    return {
        "message": f"{winner_user['display_name']} wins the battle!",
        "winner_id": winner_id,
        "winner_name": winner_user["display_name"],
        "winner_votes": vote_count[winner_id],
        "loser_votes": vote_count.get(loser_id, 0),
        "points_awarded": type_info["points_winner"],
        "badges_earned": new_badges
    }


@api_router.post("/challenges/{challenge_id}/cancel")
async def admin_decide_winner(challenge_id: str, winner_id: str = None, admin: dict = Depends(get_admin_user)):
    """Admin decides the winner manually - for when no one votes (admin only)"""
    challenge = await db.challenges.find_one({"id": challenge_id}, {"_id": 0})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge["status"] == "completed":
        raise HTTPException(status_code=400, detail="Challenge already completed")
    
    if challenge["status"] != "accepted":
        raise HTTPException(status_code=400, detail="Challenge must be accepted first")
    
    if not winner_id:
        raise HTTPException(status_code=400, detail="Must specify a winner_id")
    
    # Validate winner is one of the participants
    if winner_id not in [challenge["challenger_id"], challenge["opponent_id"]]:
        raise HTTPException(status_code=400, detail="Winner must be one of the participants")
    
    loser_id = challenge["challenger_id"] if winner_id == challenge["opponent_id"] else challenge["opponent_id"]
    
    # Close voting if open
    if challenge.get("voting_open"):
        await manager.broadcast({"type": "CLOSE_VOTING", "challenge_id": challenge_id})
    
    # Update challenge status
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {
            "status": "completed", 
            "voting_open": False, 
            "winner_id": winner_id,
            "admin_decided": True,
            "decided_at": datetime.now(timezone.utc).isoformat()
        }}
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
    
    # Check if active QR session for nightly points
    active_night = await is_active_night()
    winner_total = type_info["points_winner"] + winner_bonus
    winner_update = {"$inc": {"points": winner_total}, "$set": {"badges": winner_badges, "battle_wins": battle_wins}}
    if active_night:
        winner_update["$inc"]["nightly_points"] = winner_total
    await db.users.update_one({"id": winner_id}, winner_update)
    
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
    loser_update = {"$inc": {"points": type_info["points_participant"]}}
    if active_night:
        loser_update["$inc"]["nightly_points"] = type_info["points_participant"]
    await db.users.update_one({"id": loser_id}, loser_update)
    
    winner_user = await db.users.find_one({"id": winner_id}, {"_id": 0, "display_name": 1})
    loser_user = await db.users.find_one({"id": loser_id}, {"_id": 0, "display_name": 1})
    
    # Broadcast battle ended notification (admin decision)
    await manager.broadcast({
        "type": "BATTLE_ENDED",
        "challenge_id": challenge_id,
        "winner_id": winner_id,
        "winner_name": winner_user["display_name"],
        "loser_id": loser_id,
        "loser_name": loser_user["display_name"],
        "winner_votes": 0,
        "loser_votes": 0,
        "admin_decided": True,
        "challenge_type": challenge["type"],
        "challenge_type_name": CHALLENGE_TYPES.get(challenge["type"], {}).get("name", "Battle")
    })
    
    return {
        "message": f"{winner_user['display_name']} wins! (Admin decision)",
        "winner_id": winner_id,
        "winner_name": winner_user["display_name"],
        "points_awarded": type_info["points_winner"],
        "badges_earned": new_badges,
        "admin_decided": True
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
    
    # Check if voting has expired
    voting_ends_at = challenge.get("voting_ends_at")
    if voting_ends_at:
        end_time = datetime.fromisoformat(voting_ends_at.replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > end_time:
            # Voting has expired, close it
            await db.challenges.update_one(
                {"id": challenge["id"]},
                {"$set": {"voting_open": False}}
            )
            return {"voting_open": False, "challenge": None}
    
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
            "votingStartedAt": challenge.get("voting_started_at"),
            "votingEndsAt": challenge.get("voting_ends_at")
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
# WebSocket endpoint for /ws path (fallback)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
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
    
    # Calculate voting end time (3 minutes from now)
    voting_duration_seconds = 180  # 3 minutes
    voting_started_at = datetime.now(timezone.utc)
    voting_ends_at = voting_started_at + timedelta(seconds=voting_duration_seconds)
    
    # Mark voting as open with end time
    await db.challenges.update_one(
        {"id": challenge_id},
        {"$set": {
            "voting_open": True, 
            "voting_started_at": voting_started_at.isoformat(),
            "voting_ends_at": voting_ends_at.isoformat()
        }}
    )
    
    # Broadcast to all connected clients with the server end time
    await manager.broadcast({
        "type": "OPEN_VOTING",
        "challenge": {
            "id": challenge_id,
            "challengerId": challenge["challenger_id"],
            "opponentId": challenge["opponent_id"],
            "challengerName": challenger["display_name"] if challenger else "Unknown",
            "opponentName": opponent["display_name"] if opponent else "Unknown",
            "challengeType": challenge["type"],
            "typeName": CHALLENGE_TYPES.get(challenge["type"], {}).get("name", "Battle"),
            "votingEndsAt": voting_ends_at.isoformat(),
            "votingDuration": voting_duration_seconds
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
from zoneinfo import ZoneInfo

VENUE_SECRET = os.environ['VENUE_SECRET']
VENUE_TIMEZONE = os.environ.get('VENUE_TIMEZONE', 'America/Chicago')  # Central Time for King Karaoke
CHECKIN_POINTS = 10
QR_CODE_CUTOFF_HOUR = 4  # QR code expires at 4 AM the next day

async def is_active_night():
    """Check if there's an active QR code session for tonight.
    Returns True only if the current venue date matches the stored current_night.
    This ensures nightly points are only awarded during active QR sessions."""
    today = get_venue_date()
    settings = await db.settings.find_one({"key": "current_night"})
    if not settings:
        return False
    return settings.get("value") == today

def get_venue_date():
    """Get current date in venue's local timezone, accounting for 4 AM cutoff.
    
    QR codes are valid from 4 AM until 4 AM the next day.
    - If it's 8 PM Monday, use Monday's date (valid until 4 AM Tuesday)
    - If it's 2 AM Tuesday, still use Monday's date (same QR code)
    - If it's 5 AM Tuesday, use Tuesday's date (new QR code)
    """
    tz = ZoneInfo(VENUE_TIMEZONE)
    now = datetime.now(tz)
    
    # If it's before 4 AM, use yesterday's date (same QR code as previous night)
    if now.hour < QR_CODE_CUTOFF_HOUR:
        effective_date = now - timedelta(days=1)
    else:
        effective_date = now
    
    return effective_date.strftime("%Y-%m-%d")

@api_router.get("/venue/qr-data")
async def get_venue_qr_data(admin: dict = Depends(get_admin_user)):
    """Get QR code data for venue check-in (admin only)"""
    today = get_venue_date()
    daily_code = hashlib.sha256(f"{VENUE_SECRET}-{today}".encode()).hexdigest()[:12]
    
    # Check if this is a new night (different from last stored night)
    settings = await db.settings.find_one({"key": "current_night"})
    last_night = settings.get("value") if settings else None
    nightly_reset = False
    
    if last_night != today:
        # Before resetting, award "Nightly Champion" badge to #1 on tonight's leaderboard
        nightly_champion = await db.users.find_one(
            {"nightly_points": {"$gt": 0}},
            {"_id": 0, "id": 1, "display_name": 1, "badges": 1, "nightly_points": 1},
            sort=[("nightly_points", -1)]
        )
        
        champion_awarded = None
        if nightly_champion and nightly_champion.get("nightly_points", 0) > 0:
            champion_id = nightly_champion["id"]
            champion_badges = list(nightly_champion.get("badges", []))
            
            # Award the badge (can earn multiple times, but only once per night)
            if "nightly_champion" not in champion_badges:
                champion_badges.append("nightly_champion")
            
            # Add badge points to their total (not nightly since we're resetting)
            await db.users.update_one(
                {"id": champion_id},
                {
                    "$set": {"badges": champion_badges},
                    "$inc": {"points": BADGES["nightly_champion"]["points_reward"]}
                }
            )
            
            # Record the accomplishment
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": champion_id,
                "badge_id": "nightly_champion",
                "badge_name": BADGES["nightly_champion"]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat(),
                "night_date": last_night,
                "nightly_points": nightly_champion.get("nightly_points", 0)
            })
            
            champion_awarded = {
                "user_id": champion_id,
                "display_name": nightly_champion["display_name"],
                "nightly_points": nightly_champion.get("nightly_points", 0)
            }
        
        # New night! Reset all users' nightly_points to 0
        await db.users.update_many({}, {"$set": {"nightly_points": 0}})
        # Store the new night date
        await db.settings.update_one(
            {"key": "current_night"},
            {"$set": {"value": today, "reset_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True
        )
        nightly_reset = True
        # Broadcast leaderboard update to all clients
        await manager.broadcast({
            "type": "LEADERBOARD_RESET", 
            "date": today,
            "champion": champion_awarded
        })
    
    # Calculate when this code expires (4 AM next day in venue timezone)
    tz = ZoneInfo(VENUE_TIMEZONE)
    now = datetime.now(tz)
    
    if now.hour < QR_CODE_CUTOFF_HOUR:
        # Already past midnight, expires at 4 AM today
        expires_at = now.replace(hour=QR_CODE_CUTOFF_HOUR, minute=0, second=0, microsecond=0)
    else:
        # Expires at 4 AM tomorrow
        tomorrow = now + timedelta(days=1)
        expires_at = tomorrow.replace(hour=QR_CODE_CUTOFF_HOUR, minute=0, second=0, microsecond=0)
    
    return {
        "venue_code": daily_code,
        "date": today,
        "timezone": VENUE_TIMEZONE,
        "expires_at": expires_at.isoformat(),
        "checkin_url": f"/checkin/{daily_code}",
        "nightly_reset": nightly_reset
    }

@api_router.post("/checkin/{venue_code}")
async def perform_checkin(venue_code: str, user: dict = Depends(get_current_user)):
    """Perform a venue check-in via QR code"""
    today = get_venue_date()
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
    
    # Calculate yesterday in venue timezone
    tz = ZoneInfo(VENUE_TIMEZONE)
    yesterday = (datetime.now(tz) - timedelta(days=1)).strftime("%Y-%m-%d")
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
            "$inc": {"points": CHECKIN_POINTS, "nightly_points": CHECKIN_POINTS, "total_checkins": 1},
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
    
    # Count total unique nights attended for Loyal Subject and Court Regular badges
    total_nights = await db.checkins.count_documents({"user_id": user["id"]})
    
    if total_nights >= 3 and "loyal_subject" not in user_badges:
        user_badges.append("loyal_subject")
        badges_earned.append("loyal_subject")
        bonus_points += BADGES["loyal_subject"]["points_reward"]
    
    if total_nights >= 5 and "court_regular" not in user_badges:
        user_badges.append("court_regular")
        badges_earned.append("court_regular")
        bonus_points += BADGES["court_regular"]["points_reward"]
    
    if badges_earned:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"badges": user_badges}, "$inc": {"points": bonus_points, "nightly_points": bonus_points}}
        )
        for badge_id in badges_earned:
            await db.accomplishments.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "badge_id": badge_id,
                "badge_name": BADGES[badge_id]["name"],
                "earned_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Broadcast points/leaderboard update after check-in
    await manager.broadcast({
        "type": "POINTS_UPDATED",
        "user_id": user["id"]
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
    today = get_venue_date()  # Use venue date with 4AM cutoff
    checkins = await db.checkins.find(
        {"date": today},
        {"_id": 0}
    ).to_list(500)
    
    # Collect all user IDs and fetch in one query (avoid N+1)
    user_ids = list(set([c["user_id"] for c in checkins]))
    users = await db.users.find(
        {"id": {"$in": user_ids}},
        {"_id": 0, "id": 1, "display_name": 1}
    ).to_list(500)
    user_map = {u["id"]: u["display_name"] for u in users}
    
    for checkin in checkins:
        checkin["user_name"] = user_map.get(checkin["user_id"], "Unknown")
    
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

# WebSocket endpoint - must be after router is included
@app.websocket("/api/ws")
async def websocket_endpoint_api(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
