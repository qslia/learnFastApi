from fastapi import FastAPI, HTTPException, Query, Path, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum
import os
import shutil
import uuid

# Initialize FastAPI app with metadata
app = FastAPI(
    title="FastAPI Demo Project",
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


class User(BaseModel):
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

item_id_counter = 3
user_id_counter = 2


# ============== HTML Page Endpoints ==============
@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home_page(request: Request):
    """Home page with HTML template"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "FastAPI Demo",
            "items": list(items_db.values()),
        },
    )


@app.get("/gallery", response_class=HTMLResponse, tags=["Pages"])
async def gallery_page(request: Request):
    """Image gallery page"""
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
        },
    )


@app.get("/items-page", response_class=HTMLResponse, tags=["Pages"])
async def items_page(request: Request, category: Optional[str] = None):
    """Items listing page with optional category filter"""
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
        },
    )


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
@app.get("/api/users", response_model=list[User], tags=["API - Users"])
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


@app.get("/api/users/{user_id}", response_model=User, tags=["API - Users"])
async def get_user(
    user_id: int = Path(..., gt=0, description="The ID of the user to retrieve")
):
    """Get a specific user by ID"""
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return users_db[user_id]


@app.post("/api/users", response_model=User, status_code=201, tags=["API - Users"])
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
