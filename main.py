from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Path,
    File,
    UploadFile,
    Request,
    Depends,
    Response,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import os
import shutil
import uuid
import hashlib
import secrets

# Initialize FastAPI app with metadata
app = FastAPI(
    title="English Speaking Practice",
    description="A complete FastAPI project demonstrating various features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Create directories for static files and uploads
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Secret Key for Sessions ==============
SECRET_KEY = secrets.token_hex(32)


# ============== Enums ==============
class ItemCategory(str, Enum):
    electronics = "electronics"
    clothing = "clothing"
    food = "food"
    books = "books"


# ============== Pydantic Models ==============
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(
        None, max_length=500, description="Item description"
    )
    price: float = Field(..., gt=0, description="Item price (must be greater than 0)")
    category: ItemCategory = Field(..., description="Item category")
    in_stock: bool = Field(default=True, description="Whether item is in stock")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[ItemCategory] = None
    in_stock: Optional[bool] = None


class Item(ItemBase):
    id: int
    created_at: datetime
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserModel(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class Message(BaseModel):
    message: str


class ImageUploadResponse(BaseModel):
    filename: str
    url: str
    size: int


# ============== Auth Models ==============
class UserSignup(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime


# ============== In-Memory Database ==============
items_db: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Laptop",
        "description": "High-performance laptop for developers",
        "price": 1299.99,
        "category": "electronics",
        "in_stock": True,
        "created_at": datetime.now(),
        "image_url": None,
    },
    2: {
        "id": 2,
        "name": "Python Cookbook",
        "description": "Advanced Python recipes and techniques",
        "price": 49.99,
        "category": "books",
        "in_stock": True,
        "created_at": datetime.now(),
        "image_url": None,
    },
}

users_db: dict[int, dict] = {
    1: {
        "id": 1,
        "username": "johndoe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "is_active": True,
    }
}

# Auth users database (with passwords)
auth_users_db: dict[str, dict] = {
    "demo": {
        "id": 1,
        "username": "demo",
        "email": "demo@example.com",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "full_name": "Demo User",
        "is_active": True,
        "created_at": datetime.now(),
    }
}

# Session storage (in production, use Redis or database)
sessions_db: dict[str, dict] = {}

item_id_counter = 3
user_id_counter = 2
auth_user_id_counter = 2
post_id_counter = 4

# ============== Community Posts Database ==============
posts_db: list[dict] = [
    {
        "id": 1,
        "author": "demo",
        "author_name": "Demo User",
        "content": "Welcome to the English Speaking Practice community! 🎉 Feel free to share your learning progress, ask questions, or help others.",
        "created_at": datetime.now() - timedelta(hours=5),
        "likes": 12,
        "liked_by": ["demo"],
    },
    {
        "id": 2,
        "author": "demo",
        "author_name": "Demo User",
        "content": "今天学了一个新句子：The weather in southwest China is very special. 西南部的天气真的很特别！",
        "created_at": datetime.now() - timedelta(hours=2),
        "likes": 5,
        "liked_by": [],
    },
    {
        "id": 3,
        "author": "demo",
        "author_name": "Demo User",
        "content": "Does anyone have tips for remembering vocabulary? I keep forgetting new words after a few days. 😅",
        "created_at": datetime.now() - timedelta(minutes=30),
        "likes": 3,
        "liked_by": [],
    },
]

# ============== Practice Sentences Database ==============
sentences_db: list[dict] = [
    {
        "id": 141,
        "chinese": "中国西南部的天气很特别。",
        "hint": "The weather in... is very special/unique.",
    },
    {
        "id": 142,
        "chinese": "春天和秋天是最好的季节。",
        "hint": "Spring and autumn are...",
    },
    {
        "id": 143,
        "chinese": "中国中部和东部的天气大不相同。",
        "hint": "The weather in... is very different from...",
    },
    {
        "id": 144,
        "chinese": "暑假里我想和朋友们去旅行。",
        "hint": "During summer vacation, I want to... with my friends.",
    },
    {
        "id": 145,
        "chinese": "在秋天野餐是令人愉快的。",
        "hint": "Having a picnic in autumn is...",
    },
    {
        "id": 146,
        "chinese": "人们在这个季节喜欢参加什么活动?",
        "hint": "What activities do people like to... in this season?",
    },
    {
        "id": 147,
        "chinese": "在六月，这儿经常下大雨。",
        "hint": "In June, it often... here.",
    },
    {
        "id": 148,
        "chinese": "在这么热的天气里去游泳很凉爽。",
        "hint": "It's refreshing/cool to... in such hot weather.",
    },
]


# ============== Auth Helper Functions ==============
def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == password_hash


def create_session(user_id: int, username: str) -> str:
    """Create a new session and return the session token"""
    session_token = secrets.token_urlsafe(32)
    sessions_db[session_token] = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(days=7),
    }
    return session_token


def get_session(session_token: str) -> Optional[dict]:
    """Get session data from token"""
    if not session_token:
        return None
    session = sessions_db.get(session_token)
    if session and session["expires_at"] > datetime.now():
        return session
    elif session:
        # Session expired, remove it
        del sessions_db[session_token]
    return None


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session cookie"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None
    session = get_session(session_token)
    if not session:
        return None
    username = session.get("username")
    return auth_users_db.get(username)


# ============== Auth Page Endpoints ==============
@app.get("/login", response_class=HTMLResponse, tags=["Auth Pages"])
async def login_page(
    request: Request, error: Optional[str] = None, message: Optional[str] = None
):
    """Login page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "Login",
            "error": error,
            "message": message,
        },
    )


@app.get("/signup", response_class=HTMLResponse, tags=["Auth Pages"])
async def signup_page(request: Request, error: Optional[str] = None):
    """Signup page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        "signup.html",
        {
            "request": request,
            "title": "Sign Up",
            "error": error,
        },
    )


@app.post("/login", tags=["Auth"])
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    """Process login form"""
    user = auth_users_db.get(username)

    if not user or not verify_password(password, user["password_hash"]):
        return RedirectResponse(
            url="/login?error=Invalid username or password",
            status_code=302,
        )

    if not user["is_active"]:
        return RedirectResponse(
            url="/login?error=Account is disabled",
            status_code=302,
        )

    # Create session
    session_token = create_session(user["id"], username)

    # Redirect to home with session cookie
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=7 * 24 * 60 * 60,  # 7 days
        samesite="lax",
    )
    return response


@app.post("/signup", tags=["Auth"])
async def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(None),
):
    """Process signup form"""
    global auth_user_id_counter

    # Check if username exists
    if username in auth_users_db:
        return RedirectResponse(
            url="/signup?error=Username already exists",
            status_code=302,
        )

    # Check if email exists
    for user in auth_users_db.values():
        if user["email"] == email:
            return RedirectResponse(
                url="/signup?error=Email already registered",
                status_code=302,
            )

    # Validate password length
    if len(password) < 6:
        return RedirectResponse(
            url="/signup?error=Password must be at least 6 characters",
            status_code=302,
        )

    # Create new user
    auth_users_db[username] = {
        "id": auth_user_id_counter,
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name or username,
        "is_active": True,
        "created_at": datetime.now(),
    }
    auth_user_id_counter += 1

    return RedirectResponse(
        url="/login?message=Account created successfully! Please login.",
        status_code=302,
    )


@app.get("/logout", tags=["Auth"])
async def logout(request: Request):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    if session_token and session_token in sessions_db:
        del sessions_db[session_token]

    response = RedirectResponse(
        url="/login?message=Logged out successfully", status_code=302
    )
    response.delete_cookie("session_token")
    return response


@app.get("/profile", response_class=HTMLResponse, tags=["Auth Pages"])
async def profile_page(request: Request):
    """User profile page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Profile",
            "user": user,
        },
    )


# ============== HTML Page Endpoints ==============
@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home_page(request: Request):
    """Home page with HTML template"""
    user = get_current_user(request)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "English Speaking Practice",
            "items": list(items_db.values()),
            "user": user,
        },
    )


@app.get("/gallery", response_class=HTMLResponse, tags=["Pages"])
async def gallery_page(request: Request):
    """Image gallery page"""
    user = get_current_user(request)
    # Get all uploaded images
    upload_dir = "static/uploads"
    images = []
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                images.append(
                    {"filename": filename, "url": f"/static/uploads/{filename}"}
                )

    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "title": "Image Gallery",
            "images": images,
            "user": user,
        },
    )


@app.get("/items-page", response_class=HTMLResponse, tags=["Pages"])
async def items_page(request: Request, category: Optional[str] = None):
    """Items listing page with optional category filter"""
    user = get_current_user(request)
    items = list(items_db.values())
    if category:
        items = [item for item in items if item["category"] == category]

    return templates.TemplateResponse(
        "items.html",
        {
            "request": request,
            "title": "Items Catalog",
            "items": items,
            "categories": [c.value for c in ItemCategory],
            "selected_category": category,
            "user": user,
        },
    )


@app.get("/practice", response_class=HTMLResponse, tags=["Pages"])
async def practice_page(request: Request):
    """English speaking practice page"""
    user = get_current_user(request)
    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "title": "English Speaking Practice",
            "sentences": sentences_db,
            "user": user,
        },
    )


@app.get("/community", response_class=HTMLResponse, tags=["Pages"])
async def community_page(request: Request):
    """Community posts page"""
    user = get_current_user(request)
    # Sort posts by created_at descending (newest first)
    sorted_posts = sorted(posts_db, key=lambda x: x["created_at"], reverse=True)
    return templates.TemplateResponse(
        "community.html",
        {
            "request": request,
            "title": "Community",
            "posts": sorted_posts,
            "user": user,
        },
    )


# ============== Community API Endpoints ==============
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


@app.get("/api/posts", tags=["API - Community"])
async def get_posts():
    """Get all community posts"""
    sorted_posts = sorted(posts_db, key=lambda x: x["created_at"], reverse=True)
    return sorted_posts


@app.post("/api/posts", tags=["API - Community"])
async def create_post(request: Request, post: PostCreate):
    """Create a new community post"""
    global post_id_counter

    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in to post")

    new_post = {
        "id": post_id_counter,
        "author": user["username"],
        "author_name": user["full_name"] or user["username"],
        "content": post.content,
        "created_at": datetime.now(),
        "likes": 0,
        "liked_by": [],
    }
    posts_db.insert(0, new_post)
    post_id_counter += 1

    return new_post


@app.post("/api/posts/{post_id}/like", tags=["API - Community"])
async def like_post(request: Request, post_id: int):
    """Like or unlike a post"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401, detail="You must be logged in to like posts"
        )

    for post in posts_db:
        if post["id"] == post_id:
            if user["username"] in post["liked_by"]:
                # Unlike
                post["liked_by"].remove(user["username"])
                post["likes"] -= 1
                return {"liked": False, "likes": post["likes"]}
            else:
                # Like
                post["liked_by"].append(user["username"])
                post["likes"] += 1
                return {"liked": True, "likes": post["likes"]}

    raise HTTPException(status_code=404, detail="Post not found")


@app.delete("/api/posts/{post_id}", tags=["API - Community"])
async def delete_post(request: Request, post_id: int):
    """Delete a post (only author can delete)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in")

    for i, post in enumerate(posts_db):
        if post["id"] == post_id:
            if post["author"] != user["username"]:
                raise HTTPException(
                    status_code=403, detail="You can only delete your own posts"
                )
            posts_db.pop(i)
            return {"message": "Post deleted successfully"}

    raise HTTPException(status_code=404, detail="Post not found")


# ============== Image Upload Endpoints ==============
@app.post("/upload/image", response_model=ImageUploadResponse, tags=["Images"])
async def upload_image(file: UploadFile = File(...)):
    """Upload an image file"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
        )

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = f"static/uploads/{unique_filename}"

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    file_size = os.path.getsize(file_path)

    return ImageUploadResponse(
        filename=unique_filename,
        url=f"/static/uploads/{unique_filename}",
        size=file_size,
    )


@app.post("/items/{item_id}/image", tags=["Images"])
async def upload_item_image(
    item_id: int = Path(..., gt=0), file: UploadFile = File(...)
):
    """Upload an image for a specific item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
        )

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"item_{item_id}_{uuid.uuid4()}{file_ext}"
    file_path = f"static/uploads/{unique_filename}"

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update item with image URL
    items_db[item_id]["image_url"] = f"/static/uploads/{unique_filename}"

    return {
        "message": "Image uploaded successfully",
        "image_url": items_db[item_id]["image_url"],
    }


@app.get("/images/{filename}", tags=["Images"])
async def get_image(filename: str):
    """Get an uploaded image by filename"""
    file_path = f"static/uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


@app.delete("/images/{filename}", response_model=Message, tags=["Images"])
async def delete_image(filename: str):
    """Delete an uploaded image"""
    file_path = f"static/uploads/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    os.remove(file_path)
    return {"message": f"Image {filename} deleted successfully"}


# ============== API Health Check ==============
@app.get("/api/health", response_model=Message, tags=["API"])
async def health_check():
    """Health check endpoint"""
    return {"message": "OK"}


# ============== Auth API Endpoints ==============
@app.get("/api/auth/me", tags=["API - Auth"])
async def get_current_user_api(request: Request):
    """Get current logged in user"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
    }


# ============== Item API Endpoints ==============
@app.get("/api/items", response_model=list[Item], tags=["API - Items"])
async def get_items(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of items to return"),
    category: Optional[ItemCategory] = Query(None, description="Filter by category"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock status"),
):
    """Get all items with optional filtering and pagination"""
    items = list(items_db.values())

    # Apply filters
    if category:
        items = [item for item in items if item["category"] == category.value]
    if in_stock is not None:
        items = [item for item in items if item["in_stock"] == in_stock]

    # Apply pagination
    return items[skip : skip + limit]


@app.get("/api/items/{item_id}", response_model=Item, tags=["API - Items"])
async def get_item(
    item_id: int = Path(..., gt=0, description="The ID of the item to retrieve")
):
    """Get a specific item by ID"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")
    return items_db[item_id]


@app.post("/api/items", response_model=Item, status_code=201, tags=["API - Items"])
async def create_item(item: ItemCreate):
    """Create a new item"""
    global item_id_counter

    new_item = {
        "id": item_id_counter,
        **item.model_dump(),
        "category": item.category.value,
        "created_at": datetime.now(),
        "image_url": None,
    }
    items_db[item_id_counter] = new_item
    item_id_counter += 1

    return new_item


@app.put("/api/items/{item_id}", response_model=Item, tags=["API - Items"])
async def update_item(item_id: int = Path(..., gt=0), item_update: ItemUpdate = None):
    """Update an existing item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")

    stored_item = items_db[item_id]
    update_data = item_update.model_dump(exclude_unset=True)

    # Convert category enum to string if present
    if "category" in update_data and update_data["category"]:
        update_data["category"] = update_data["category"].value

    stored_item.update(update_data)
    return stored_item


@app.delete("/api/items/{item_id}", response_model=Message, tags=["API - Items"])
async def delete_item(item_id: int = Path(..., gt=0)):
    """Delete an item"""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")

    del items_db[item_id]
    return {"message": f"Item {item_id} deleted successfully"}


# ============== User API Endpoints ==============
@app.get("/api/users", response_model=list[UserModel], tags=["API - Users"])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(False, description="Return only active users"),
):
    """Get all users with optional filtering"""
    users = list(users_db.values())

    if active_only:
        users = [user for user in users if user["is_active"]]

    return users[skip : skip + limit]


@app.get("/api/users/{user_id}", response_model=UserModel, tags=["API - Users"])
async def get_user(
    user_id: int = Path(..., gt=0, description="The ID of the user to retrieve")
):
    """Get a specific user by ID"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return users_db[user_id]


@app.post("/api/users", response_model=UserModel, status_code=201, tags=["API - Users"])
async def create_user(user: UserCreate):
    """Create a new user"""
    global user_id_counter

    # Check for duplicate email
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")

    new_user = {"id": user_id_counter, **user.model_dump(), "is_active": True}
    users_db[user_id_counter] = new_user
    user_id_counter += 1

    return new_user


@app.delete("/api/users/{user_id}", response_model=Message, tags=["API - Users"])
async def delete_user(user_id: int = Path(..., gt=0)):
    """Delete a user"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")

    del users_db[user_id]
    return {"message": f"User {user_id} deleted successfully"}


# ============== Search Endpoint ==============
@app.get("/api/search", tags=["API - Search"])
async def search_items(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[ItemCategory] = None,
):
    """Search items by name or description"""
    results = []
    query_lower = q.lower()

    for item in items_db.values():
        if category and item["category"] != category.value:
            continue
        if query_lower in item["name"].lower() or (
            item["description"] and query_lower in item["description"].lower()
        ):
            results.append(item)

    return {"query": q, "count": len(results), "results": results}


# ============== Sentence API Endpoints ==============
class SentenceCreate(BaseModel):
    id: int
    chinese: str = Field(..., min_length=1)
    hint: Optional[str] = None


@app.get("/api/sentences", tags=["API - Sentences"])
async def get_sentences():
    """Get all practice sentences"""
    return sentences_db


@app.post("/api/sentences", tags=["API - Sentences"])
async def create_sentence(sentence: SentenceCreate):
    """Add a new practice sentence"""
    # Check for duplicate ID
    for s in sentences_db:
        if s["id"] == sentence.id:
            raise HTTPException(
                status_code=400, detail=f"Sentence with id {sentence.id} already exists"
            )

    new_sentence = {
        "id": sentence.id,
        "chinese": sentence.chinese,
        "hint": sentence.hint,
    }
    sentences_db.insert(0, new_sentence)  # Add to beginning
    return new_sentence


@app.delete("/api/sentences/{sentence_id}", tags=["API - Sentences"])
async def delete_sentence(sentence_id: int):
    """Delete a practice sentence"""
    for i, s in enumerate(sentences_db):
        if s["id"] == sentence_id:
            sentences_db.pop(i)
            return {"message": f"Sentence {sentence_id} deleted successfully"}
    raise HTTPException(
        status_code=404, detail=f"Sentence with id {sentence_id} not found"
    )


# ============== Stats Endpoint ==============
@app.get("/api/stats", tags=["API - Statistics"])
async def get_stats():
    """Get statistics about the data"""
    items = list(items_db.values())

    category_counts = {}
    for item in items:
        cat = item["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    in_stock_count = sum(1 for item in items if item["in_stock"])

    return {
        "total_items": len(items),
        "total_users": len(users_db),
        "items_in_stock": in_stock_count,
        "items_out_of_stock": len(items) - in_stock_count,
        "items_by_category": category_counts,
        "average_price": (
            round(sum(item["price"] for item in items) / len(items), 2) if items else 0
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
