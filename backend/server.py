from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
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
BADGES = {
    "first_song": {"name": "First Timer", "description": "Performed your first song", "icon": "mic", "points_reward": 25},
    "five_songs": {"name": "Rising Star", "description": "Performed 5 songs", "icon": "star", "points_reward": 50},
    "ten_songs": {"name": "Stage Regular", "description": "Performed 10 songs", "icon": "trophy", "points_reward": 100},
    "twenty_songs": {"name": "Karaoke King", "description": "Performed 20 songs", "icon": "crown", "points_reward": 200},
    "rock_star": {"name": "Rock Star", "description": "Performed 3 rock songs", "icon": "guitar", "points_reward": 50},
    "pop_icon": {"name": "Pop Icon", "description": "Performed 3 pop songs", "icon": "music", "points_reward": 50},
    "duet_master": {"name": "Duet Master", "description": "Performed 3 duets", "icon": "users", "points_reward": 75},
    "night_owl": {"name": "Night Owl", "description": "Visited 5 consecutive times", "icon": "moon", "points_reward": 100},
    "loyal_patron": {"name": "Loyal Patron", "description": "Visited 10 consecutive times", "icon": "heart", "points_reward": 150},
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

# ==================== RANKS INFO ====================
@api_router.get("/ranks")
async def get_ranks():
    return RANKS

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
