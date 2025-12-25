# FastAPI Demo Project

A complete FastAPI project demonstrating various features including CRUD operations, data validation, filtering, pagination, and more.

## Features

- 🚀 **FastAPI** - Modern, fast web framework
- 📝 **Pydantic** - Data validation using Python type hints
- 📚 **Auto-generated docs** - Swagger UI & ReDoc
- 🔍 **Search & Filter** - Query parameters for filtering data
- 📊 **Statistics endpoint** - Aggregated data insights
- 🔒 **CORS enabled** - Cross-origin resource sharing

## Quick Start

### 1. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the server

```bash
uvicorn main:app --reload
```

Or run directly:

```bash
python main.py
```

### 4. Open the API docs

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## API Endpoints

### Root
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |

### Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/items` | Get all items (with filtering & pagination) |
| GET | `/items/{id}` | Get item by ID |
| POST | `/items` | Create new item |
| PUT | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Delete item |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | Get all users |
| GET | `/users/{id}` | Get user by ID |
| POST | `/users` | Create new user |
| DELETE | `/users/{id}` | Delete user |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/search?q=query` | Search items |
| GET | `/stats` | Get statistics |

## Example Requests

### Create an Item

```bash
curl -X POST "http://127.0.0.1:8000/items" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "description": "Ergonomic wireless mouse",
    "price": 29.99,
    "category": "electronics"
  }'
```

### Get Items with Filtering

```bash
# Get electronics items
curl "http://127.0.0.1:8000/items?category=electronics"

# Get items in stock with pagination
curl "http://127.0.0.1:8000/items?in_stock=true&skip=0&limit=5"
```

### Search Items

```bash
curl "http://127.0.0.1:8000/search?q=laptop"
```

## Project Structure

```
learnFastApi/
├── main.py           # Main application file
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── md/               # Documentation files
```

## Item Categories

- `electronics`
- `clothing`
- `food`
- `books`

## License

MIT License

