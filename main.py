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
from sqlalchemy.orm import Session as DBSession
import os
import shutil
import uuid
import hashlib
import secrets

# Import database models and utilities
from database import (
    engine,
    SessionLocal,
    Base,
    User as DBUser,
    Session as DBSessionModel,
    Post as DBPost,
    PostLike as DBPostLike,
    Sentence as DBSentence,
    PracticeRecord as DBPracticeRecord,
    DailyStreak as DBDailyStreak,
    Payment as DBPayment,
    SubscriptionTier,
    PaymentStatus,
    SUBSCRIPTION_LIMITS,
    get_db,
    create_tables,
    init_demo_data,
)
from datetime import date
from dateutil.relativedelta import relativedelta

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
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))


# ============== Startup Event ==============
@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting up...")
    create_tables()
    # Initialize demo data
    db = SessionLocal()
    try:
        init_demo_data(db)
    finally:
        db.close()
    print("✅ Database ready!")


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


# ============== In-Memory Database (for items only - not auth) ==============
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

item_id_counter = 3
user_id_counter = 2


# ============== Auth Helper Functions ==============
def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == password_hash


def create_session(db: DBSession, user_id: int, username: str) -> str:
    """Create a new session in database and return the session token"""
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=7)

    db_session = DBSessionModel(
        token=session_token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_session)
    db.commit()

    return session_token


def get_session(db: DBSession, session_token: str) -> Optional[DBSessionModel]:
    """Get session data from token"""
    if not session_token:
        return None

    session = (
        db.query(DBSessionModel).filter(DBSessionModel.token == session_token).first()
    )

    if session and session.expires_at > datetime.now():
        return session
    elif session:
        # Session expired, remove it
        db.delete(session)
        db.commit()

    return None


def get_current_user(request: Request, db: DBSession) -> Optional[DBUser]:
    """Get current user from session cookie"""
    session_token = request.cookies.get("session_token")
    if not session_token:
        return None

    session = get_session(db, session_token)
    if not session:
        return None

    return db.query(DBUser).filter(DBUser.id == session.user_id).first()


def delete_session(db: DBSession, session_token: str):
    """Delete a session from database"""
    session = (
        db.query(DBSessionModel).filter(DBSessionModel.token == session_token).first()
    )
    if session:
        db.delete(session)
        db.commit()


# ============== Auth Page Endpoints ==============
@app.get("/login", response_class=HTMLResponse, tags=["Auth Pages"])
async def login_page(
    request: Request,
    error: Optional[str] = None,
    message: Optional[str] = None,
    db: DBSession = Depends(get_db),
):
    """Login page"""
    user = get_current_user(request, db)
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
async def signup_page(
    request: Request,
    error: Optional[str] = None,
    db: DBSession = Depends(get_db),
):
    """Signup page"""
    user = get_current_user(request, db)
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
    db: DBSession = Depends(get_db),
):
    """Process login form"""
    # Find user in database
    user = db.query(DBUser).filter(DBUser.username == username).first()

    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(
            url="/login?error=Invalid username or password",
            status_code=302,
        )

    if not user.is_active:
        return RedirectResponse(
            url="/login?error=Account is disabled",
            status_code=302,
        )

    # Create session in database
    session_token = create_session(db, user.id, username)

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
    db: DBSession = Depends(get_db),
):
    """Process signup form"""
    # Check if username exists
    existing_user = db.query(DBUser).filter(DBUser.username == username).first()
    if existing_user:
        return RedirectResponse(
            url="/signup?error=Username already exists",
            status_code=302,
        )

    # Check if email exists
    existing_email = db.query(DBUser).filter(DBUser.email == email).first()
    if existing_email:
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

    # Create new user in database
    new_user = DBUser(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name or username,
        is_active=True,
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(
        url="/login?message=Account created successfully! Please login.",
        status_code=302,
    )


@app.get("/logout", tags=["Auth"])
async def logout(request: Request, db: DBSession = Depends(get_db)):
    """Logout and clear session"""
    session_token = request.cookies.get("session_token")
    if session_token:
        delete_session(db, session_token)

    response = RedirectResponse(
        url="/login?message=Logged out successfully", status_code=302
    )
    response.delete_cookie("session_token")
    return response


@app.get("/profile", response_class=HTMLResponse, tags=["Auth Pages"])
async def profile_page(request: Request, db: DBSession = Depends(get_db)):
    """User profile page"""
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Convert SQLAlchemy model to dict for template
    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
    }

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "title": "Profile",
            "user": user_dict,
        },
    )


# ============== HTML Page Endpoints ==============
@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home_page(request: Request, db: DBSession = Depends(get_db)):
    """Home page with HTML template"""
    user = get_current_user(request, db)
    user_dict = None
    if user:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "English Speaking Practice",
            "user": user_dict,
        },
    )


@app.get("/items-page", response_class=HTMLResponse, tags=["Pages"])
async def items_page(
    request: Request,
    category: Optional[str] = None,
    db: DBSession = Depends(get_db),
):
    """Items listing page with optional category filter"""
    user = get_current_user(request, db)
    user_dict = None
    if user:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        }

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
            "user": user_dict,
        },
    )


@app.get("/practice", response_class=HTMLResponse, tags=["Pages"])
async def practice_page(request: Request, db: DBSession = Depends(get_db)):
    """English speaking practice page"""
    user = get_current_user(request, db)
    user_dict = None
    if user:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        }

    # Get sentences from database
    sentences = db.query(DBSentence).order_by(DBSentence.id).all()
    sentences_list = [
        {"id": s.id, "chinese": s.chinese, "hint": s.hint} for s in sentences
    ]

    return templates.TemplateResponse(
        "practice.html",
        {
            "request": request,
            "title": "English Speaking Practice",
            "sentences": sentences_list,
            "user": user_dict,
        },
    )


@app.get("/community", response_class=HTMLResponse, tags=["Pages"])
async def community_page(request: Request, db: DBSession = Depends(get_db)):
    """Community posts page"""
    user = get_current_user(request, db)
    user_dict = None
    if user:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
        }

    # Get posts from database with author info
    posts = db.query(DBPost).order_by(DBPost.created_at.desc()).all()
    posts_list = []
    for post in posts:
        # Get likes for this post by current user
        liked_by_current_user = False
        if user:
            like = (
                db.query(DBPostLike)
                .filter(DBPostLike.post_id == post.id, DBPostLike.user_id == user.id)
                .first()
            )
            liked_by_current_user = like is not None

        posts_list.append(
            {
                "id": post.id,
                "author": post.author_user.username,
                "author_name": post.author_user.full_name or post.author_user.username,
                "content": post.content,
                "created_at": post.created_at,
                "likes": post.likes,
                "liked_by_current_user": liked_by_current_user,
            }
        )

    return templates.TemplateResponse(
        "community.html",
        {
            "request": request,
            "title": "Community",
            "posts": posts_list,
            "user": user_dict,
        },
    )


# ============== Community API Endpoints ==============
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


@app.get("/api/posts", tags=["API - Community"])
async def get_posts(db: DBSession = Depends(get_db)):
    """Get all community posts"""
    posts = db.query(DBPost).order_by(DBPost.created_at.desc()).all()
    return [
        {
            "id": post.id,
            "author": post.author_user.username,
            "author_name": post.author_user.full_name or post.author_user.username,
            "content": post.content,
            "created_at": post.created_at,
            "likes": post.likes,
        }
        for post in posts
    ]


@app.post("/api/posts", tags=["API - Community"])
async def create_post(
    request: Request,
    post: PostCreate,
    db: DBSession = Depends(get_db),
):
    """Create a new community post"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in to post")

    new_post = DBPost(
        author_id=user.id,
        content=post.content,
        likes=0,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {
        "id": new_post.id,
        "author": user.username,
        "author_name": user.full_name or user.username,
        "content": new_post.content,
        "created_at": new_post.created_at,
        "likes": new_post.likes,
    }


@app.post("/api/posts/{post_id}/like", tags=["API - Community"])
async def like_post(
    request: Request,
    post_id: int,
    db: DBSession = Depends(get_db),
):
    """Like or unlike a post"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=401, detail="You must be logged in to like posts"
        )

    post = db.query(DBPost).filter(DBPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if user already liked this post
    existing_like = (
        db.query(DBPostLike)
        .filter(DBPostLike.post_id == post_id, DBPostLike.user_id == user.id)
        .first()
    )

    if existing_like:
        # Unlike
        db.delete(existing_like)
        post.likes = max(0, post.likes - 1)
        db.commit()
        return {"liked": False, "likes": post.likes}
    else:
        # Like
        new_like = DBPostLike(post_id=post_id, user_id=user.id)
        db.add(new_like)
        post.likes += 1
        db.commit()
        return {"liked": True, "likes": post.likes}


@app.delete("/api/posts/{post_id}", tags=["API - Community"])
async def delete_post(
    request: Request,
    post_id: int,
    db: DBSession = Depends(get_db),
):
    """Delete a post (only author can delete)"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in")

    post = db.query(DBPost).filter(DBPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.author_id != user.id:
        raise HTTPException(
            status_code=403, detail="You can only delete your own posts"
        )

    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}


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
async def get_current_user_api(request: Request, db: DBSession = Depends(get_db)):
    """Get current logged in user"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
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
async def get_sentences(db: DBSession = Depends(get_db)):
    """Get all practice sentences"""
    sentences = db.query(DBSentence).order_by(DBSentence.id).all()
    return [{"id": s.id, "chinese": s.chinese, "hint": s.hint} for s in sentences]


@app.post("/api/sentences", tags=["API - Sentences"])
async def create_sentence(sentence: SentenceCreate, db: DBSession = Depends(get_db)):
    """Add a new practice sentence"""
    # Check for duplicate ID
    existing = db.query(DBSentence).filter(DBSentence.id == sentence.id).first()
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Sentence with id {sentence.id} already exists"
        )

    new_sentence = DBSentence(
        id=sentence.id,
        chinese=sentence.chinese,
        hint=sentence.hint,
    )
    db.add(new_sentence)
    db.commit()
    db.refresh(new_sentence)

    return {
        "id": new_sentence.id,
        "chinese": new_sentence.chinese,
        "hint": new_sentence.hint,
    }


@app.delete("/api/sentences/{sentence_id}", tags=["API - Sentences"])
async def delete_sentence(sentence_id: int, db: DBSession = Depends(get_db)):
    """Delete a practice sentence"""
    sentence = db.query(DBSentence).filter(DBSentence.id == sentence_id).first()
    if not sentence:
        raise HTTPException(
            status_code=404, detail=f"Sentence with id {sentence_id} not found"
        )

    db.delete(sentence)
    db.commit()
    return {"message": f"Sentence {sentence_id} deleted successfully"}


# ============== Practice Statistics API Endpoints ==============
class PracticeRecordCreate(BaseModel):
    sentence_id: int


@app.post("/api/practice/record", tags=["API - Practice Stats"])
async def record_practice(
    record: PracticeRecordCreate,
    request: Request,
    db: DBSession = Depends(get_db),
):
    """Record that a user practiced a sentence today"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in to track practice")

    today = date.today()
    
    # Check daily limit for free users
    tier = user.current_tier
    limits = SUBSCRIPTION_LIMITS[tier]
    daily_limit = limits["daily_sentences"]
    
    if daily_limit > 0:  # -1 means unlimited
        today_count = db.query(DBPracticeRecord).filter(
            DBPracticeRecord.user_id == user.id,
            DBPracticeRecord.practice_date == today,
        ).count()
        
        if today_count >= daily_limit:
            raise HTTPException(
                status_code=403, 
                detail={
                    "message": f"已达到今日练习上限 ({daily_limit}句)，升级会员解锁更多！",
                    "limit_reached": True,
                    "daily_limit": daily_limit,
                    "upgrade_url": "/pricing",
                }
            )
    
    # Check if already recorded today
    existing = db.query(DBPracticeRecord).filter(
        DBPracticeRecord.user_id == user.id,
        DBPracticeRecord.sentence_id == record.sentence_id,
        DBPracticeRecord.practice_date == today,
    ).first()
    
    if not existing:
        # Create new practice record
        new_record = DBPracticeRecord(
            user_id=user.id,
            sentence_id=record.sentence_id,
            practice_date=today,
            completed=True,
        )
        db.add(new_record)
        
        # Update or create streak
        streak = db.query(DBDailyStreak).filter(DBDailyStreak.user_id == user.id).first()
        if not streak:
            streak = DBDailyStreak(user_id=user.id)
            db.add(streak)
        
        # Update streak statistics
        streak.total_sentences_practiced += 1
        
        # Check if this is a new day of practice
        if streak.last_practice_date != today:
            streak.total_practice_days += 1
            
            # Update streak
            if streak.last_practice_date:
                days_diff = (today - streak.last_practice_date).days
                if days_diff == 1:
                    # Consecutive day
                    streak.current_streak += 1
                elif days_diff > 1:
                    # Streak broken
                    streak.current_streak = 1
            else:
                streak.current_streak = 1
            
            # Update longest streak
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
            
            streak.last_practice_date = today
        
        db.commit()
    
    return {"message": "Practice recorded", "date": str(today)}


@app.get("/api/practice/stats", tags=["API - Practice Stats"])
async def get_practice_stats(
    request: Request,
    db: DBSession = Depends(get_db),
):
    """Get user's practice statistics"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in to view stats")

    today = date.today()
    
    # Get streak info
    streak = db.query(DBDailyStreak).filter(DBDailyStreak.user_id == user.id).first()
    
    # Get today's practice count
    today_count = db.query(DBPracticeRecord).filter(
        DBPracticeRecord.user_id == user.id,
        DBPracticeRecord.practice_date == today,
    ).count()
    
    # Get practiced sentence IDs for today
    today_practiced = db.query(DBPracticeRecord.sentence_id).filter(
        DBPracticeRecord.user_id == user.id,
        DBPracticeRecord.practice_date == today,
    ).all()
    today_sentence_ids = [r[0] for r in today_practiced]
    
    # Get total sentences
    total_sentences = db.query(DBSentence).count()
    
    # Get practice history for last 7 days
    from datetime import timedelta
    history = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = db.query(DBPracticeRecord).filter(
            DBPracticeRecord.user_id == user.id,
            DBPracticeRecord.practice_date == day,
        ).count()
        history.append({
            "date": str(day),
            "day_name": day.strftime("%a"),
            "count": count,
        })
    
    return {
        "today_date": str(today),
        "today_practiced": today_count,
        "today_sentence_ids": today_sentence_ids,
        "total_sentences": total_sentences,
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "total_practice_days": streak.total_practice_days if streak else 0,
        "total_sentences_practiced": streak.total_sentences_practiced if streak else 0,
        "last_7_days": history,
    }


@app.get("/api/practice/history", tags=["API - Practice Stats"])
async def get_practice_history(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    db: DBSession = Depends(get_db),
):
    """Get user's practice history for specified number of days"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="You must be logged in to view history")

    today = date.today()
    from datetime import timedelta
    start_date = today - timedelta(days=days-1)
    
    # Get all practice records in date range
    records = db.query(DBPracticeRecord).filter(
        DBPracticeRecord.user_id == user.id,
        DBPracticeRecord.practice_date >= start_date,
    ).all()
    
    # Group by date
    history = {}
    for record in records:
        date_str = str(record.practice_date)
        if date_str not in history:
            history[date_str] = {"date": date_str, "count": 0, "sentence_ids": []}
        history[date_str]["count"] += 1
        history[date_str]["sentence_ids"].append(record.sentence_id)
    
    return {
        "start_date": str(start_date),
        "end_date": str(today),
        "history": list(history.values()),
    }


# ============== Stats Endpoint ==============
@app.get("/api/stats", tags=["API - Statistics"])
async def get_stats(db: DBSession = Depends(get_db)):
    """Get statistics about the data"""
    items = list(items_db.values())

    category_counts = {}
    for item in items:
        cat = item["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    in_stock_count = sum(1 for item in items if item["in_stock"])

    # Get user count from database
    user_count = db.query(DBUser).count()
    post_count = db.query(DBPost).count()

    return {
        "total_items": len(items),
        "total_users": user_count,
        "total_posts": post_count,
        "items_in_stock": in_stock_count,
        "items_out_of_stock": len(items) - in_stock_count,
        "items_by_category": category_counts,
        "average_price": (
            round(sum(item["price"] for item in items) / len(items), 2) if items else 0
        ),
    }


# ============== Subscription & Payment Endpoints ==============

# Alipay Configuration (set these in environment variables for production)
ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID", "your_app_id")
ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY", "")
ALIPAY_PUBLIC_KEY = os.getenv("ALIPAY_PUBLIC_KEY", "")
ALIPAY_NOTIFY_URL = os.getenv("ALIPAY_NOTIFY_URL", "http://localhost:8000/api/payment/notify")
ALIPAY_RETURN_URL = os.getenv("ALIPAY_RETURN_URL", "http://localhost:8000/payment/success")

# Pricing configuration
PRICING = {
    "basic_monthly": {"tier": SubscriptionTier.BASIC, "months": 1, "price": 9.9, "name": "基础版月度"},
    "basic_yearly": {"tier": SubscriptionTier.BASIC, "months": 12, "price": 99, "name": "基础版年度"},
    "premium_monthly": {"tier": SubscriptionTier.PREMIUM, "months": 1, "price": 29.9, "name": "高级版月度"},
    "premium_yearly": {"tier": SubscriptionTier.PREMIUM, "months": 12, "price": 299, "name": "高级版年度"},
    "lifetime": {"tier": SubscriptionTier.LIFETIME, "months": 0, "price": 199, "name": "终身会员"},
}


@app.get("/api/subscription/status", tags=["API - Subscription"])
async def get_subscription_status(request: Request, db: DBSession = Depends(get_db)):
    """Get current user's subscription status"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get today's practice count for limit check
    today = date.today()
    today_count = db.query(DBPracticeRecord).filter(
        DBPracticeRecord.user_id == user.id,
        DBPracticeRecord.practice_date == today,
    ).count()
    
    tier = user.current_tier
    limits = SUBSCRIPTION_LIMITS[tier]
    daily_limit = limits["daily_sentences"]
    
    return {
        "tier": tier.value,
        "tier_name": {
            "free": "免费版",
            "basic": "基础版",
            "premium": "高级版",
            "lifetime": "终身会员",
        }.get(tier.value, tier.value),
        "is_premium": user.is_premium,
        "lifetime_member": user.lifetime_member,
        "expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
        "limits": {
            "daily_sentences": daily_limit,
            "today_practiced": today_count,
            "remaining_today": max(0, daily_limit - today_count) if daily_limit > 0 else -1,
            "can_practice": daily_limit == -1 or today_count < daily_limit,
            "history_days": limits["history_days"],
            "can_add_sentences": limits["can_add_sentences"],
            "show_ads": limits["show_ads"],
        },
    }


@app.get("/api/subscription/pricing", tags=["API - Subscription"])
async def get_pricing():
    """Get subscription pricing options"""
    return {
        "plans": [
            {
                "id": "basic_monthly",
                "name": "基础版",
                "period": "月度",
                "price": 9.9,
                "price_display": "¥9.9/月",
                "features": ["每日50句练习", "30天历史记录", "添加自定义句子", "无广告"],
            },
            {
                "id": "basic_yearly",
                "name": "基础版",
                "period": "年度",
                "price": 99,
                "price_display": "¥99/年",
                "original_price": 118.8,
                "discount": "省¥19.8",
                "features": ["每日50句练习", "30天历史记录", "添加自定义句子", "无广告"],
            },
            {
                "id": "premium_monthly",
                "name": "高级版",
                "period": "月度",
                "price": 29.9,
                "price_display": "¥29.9/月",
                "features": ["无限练习", "完整历史记录", "添加自定义句子", "无广告", "优先支持"],
                "recommended": True,
            },
            {
                "id": "premium_yearly",
                "name": "高级版",
                "period": "年度",
                "price": 299,
                "price_display": "¥299/年",
                "original_price": 358.8,
                "discount": "省¥59.8",
                "features": ["无限练习", "完整历史记录", "添加自定义句子", "无广告", "优先支持"],
            },
            {
                "id": "lifetime",
                "name": "终身会员",
                "period": "一次性",
                "price": 199,
                "price_display": "¥199",
                "features": ["永久无限练习", "永久完整记录", "添加自定义句子", "永久无广告", "优先支持"],
                "best_value": True,
            },
        ],
        "free_limits": {
            "daily_sentences": 10,
            "history_days": 7,
        },
    }


@app.post("/api/payment/create", tags=["API - Payment"])
async def create_payment(
    request: Request,
    plan_id: str = Query(..., description="Plan ID from pricing"),
    db: DBSession = Depends(get_db),
):
    """Create a payment order for subscription"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if plan_id not in PRICING:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    plan = PRICING[plan_id]
    
    # Generate unique order ID
    order_id = f"ESP{datetime.now().strftime('%Y%m%d%H%M%S')}{user.id}{secrets.token_hex(4).upper()}"
    
    # Create payment record
    payment = DBPayment(
        user_id=user.id,
        order_id=order_id,
        subscription_tier=plan["tier"].value,
        amount=plan["price"],
        months=plan["months"],
        status=PaymentStatus.PENDING.value,
    )
    db.add(payment)
    db.commit()
    
    # Generate Alipay payment URL
    # In production, use actual Alipay SDK
    # For now, return order info for frontend to handle
    
    return {
        "order_id": order_id,
        "amount": plan["price"],
        "plan_name": plan["name"],
        "message": "订单创建成功",
        # In production, include actual Alipay payment URL:
        # "payment_url": alipay.create_page_pay(...)
        "payment_info": {
            "subject": f"英语口语练习 - {plan['name']}",
            "out_trade_no": order_id,
            "total_amount": str(plan["price"]),
            "product_code": "FAST_INSTANT_TRADE_PAY",
        },
    }


@app.post("/api/payment/notify", tags=["API - Payment"])
async def payment_notify(request: Request, db: DBSession = Depends(get_db)):
    """Alipay async notification callback"""
    # Get form data from Alipay
    form_data = await request.form()
    data = dict(form_data)
    
    # In production, verify signature with Alipay SDK
    # alipay.verify(data, signature)
    
    order_id = data.get("out_trade_no")
    trade_status = data.get("trade_status")
    alipay_trade_no = data.get("trade_no")
    
    if not order_id:
        return "fail"
    
    # Find payment record
    payment = db.query(DBPayment).filter(DBPayment.order_id == order_id).first()
    if not payment:
        return "fail"
    
    # Update payment status
    if trade_status in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
        payment.status = PaymentStatus.COMPLETED.value
        payment.alipay_trade_no = alipay_trade_no
        payment.paid_at = datetime.utcnow()
        
        # Update user subscription
        user = db.query(DBUser).filter(DBUser.id == payment.user_id).first()
        if user:
            if payment.months == 0:  # Lifetime
                user.lifetime_member = True
                user.subscription_tier = SubscriptionTier.LIFETIME.value
            else:
                user.subscription_tier = payment.subscription_tier
                # Extend or set expiration
                if user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow():
                    # Extend existing subscription
                    user.subscription_expires_at = user.subscription_expires_at + relativedelta(months=payment.months)
                else:
                    # New subscription
                    user.subscription_expires_at = datetime.utcnow() + relativedelta(months=payment.months)
        
        db.commit()
        return "success"
    
    return "fail"


@app.get("/api/payment/check/{order_id}", tags=["API - Payment"])
async def check_payment(
    order_id: str,
    request: Request,
    db: DBSession = Depends(get_db),
):
    """Check payment status"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payment = db.query(DBPayment).filter(
        DBPayment.order_id == order_id,
        DBPayment.user_id == user.id,
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "order_id": payment.order_id,
        "status": payment.status,
        "amount": payment.amount,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


# Demo endpoint to simulate successful payment (remove in production!)
@app.post("/api/payment/demo-complete/{order_id}", tags=["API - Payment"])
async def demo_complete_payment(
    order_id: str,
    request: Request,
    db: DBSession = Depends(get_db),
):
    """[DEMO ONLY] Simulate successful payment - REMOVE IN PRODUCTION"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payment = db.query(DBPayment).filter(
        DBPayment.order_id == order_id,
        DBPayment.user_id == user.id,
    ).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status == PaymentStatus.COMPLETED.value:
        return {"message": "Payment already completed"}
    
    # Complete payment
    payment.status = PaymentStatus.COMPLETED.value
    payment.alipay_trade_no = f"DEMO_{secrets.token_hex(8)}"
    payment.paid_at = datetime.utcnow()
    
    # Update user subscription
    if payment.months == 0:  # Lifetime
        user.lifetime_member = True
        user.subscription_tier = SubscriptionTier.LIFETIME.value
    else:
        user.subscription_tier = payment.subscription_tier
        if user.subscription_expires_at and user.subscription_expires_at > datetime.utcnow():
            user.subscription_expires_at = user.subscription_expires_at + relativedelta(months=payment.months)
        else:
            user.subscription_expires_at = datetime.utcnow() + relativedelta(months=payment.months)
    
    db.commit()
    
    return {
        "message": "Payment completed successfully (DEMO)",
        "subscription_tier": user.subscription_tier,
        "expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else "Lifetime",
    }


# ============== Pricing Page ==============
@app.get("/pricing", response_class=HTMLResponse, tags=["Pages"])
async def pricing_page(request: Request, db: DBSession = Depends(get_db)):
    """Pricing page"""
    user = get_current_user(request, db)
    user_dict = None
    subscription_info = None
    
    if user:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_premium": user.is_premium,
            "tier": user.current_tier.value,
        }
        subscription_info = {
            "tier": user.current_tier.value,
            "expires_at": user.subscription_expires_at,
            "lifetime": user.lifetime_member,
        }
    
    return templates.TemplateResponse(
        "pricing.html",
        {
            "request": request,
            "title": "升级会员 - Upgrade",
            "user": user_dict,
            "subscription": subscription_info,
        },
    )


@app.get("/payment/success", response_class=HTMLResponse, tags=["Pages"])
async def payment_success_page(
    request: Request,
    out_trade_no: str = Query(None),
    db: DBSession = Depends(get_db),
):
    """Payment success page"""
    user = get_current_user(request, db)
    user_dict = None
    payment_info = None
    
    if user:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "is_premium": user.is_premium,
            "tier": user.current_tier.value,
        }
        
        if out_trade_no:
            payment = db.query(DBPayment).filter(
                DBPayment.order_id == out_trade_no,
                DBPayment.user_id == user.id,
            ).first()
            if payment:
                payment_info = {
                    "order_id": payment.order_id,
                    "status": payment.status,
                    "amount": payment.amount,
                }
    
    return templates.TemplateResponse(
        "payment_success.html",
        {
            "request": request,
            "title": "支付结果",
            "user": user_dict,
            "payment": payment_info,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
