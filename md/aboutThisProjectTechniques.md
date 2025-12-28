I’ll scan the main code, dependencies, and config to summarize the techniques and technologies this project uses.
Here’s a high-level summary of the main techniques and technologies this project uses:

1. **Web framework & API design**
   - FastAPI (`FastAPI`, path operations, query/path/form parameters)
   - Pydantic models (`BaseModel`, `Field`, `EmailStr`) for validation and serialization
   - Enum-based types for controlled values (e.g., `ItemCategory`, subscription enums)

2. **HTML rendering & static files**
   - Jinja2 templates via `Jinja2Templates` for server-side rendered pages (`login.html`, `signup.html`, `index.html`, etc.)
   - `StaticFiles` for serving static assets and user uploads (`static/uploads`)
   - HTML responses (`HTMLResponse`, `FileResponse`, `RedirectResponse`)

3. **Authentication & session handling**
   - Custom username/password auth with SHA-256 password hashing (`hash_password`, `verify_password`)
   - Cookie-based sessions:
     - Session tokens stored in the `sessions` table (`DBSessionModel`)
     - Session cookie (`session_token`) with `httponly`, `samesite` security
   - Helper functions to create, validate, and delete sessions (`create_session`, `get_session`, `get_current_user`)

4. **Database & ORM**
   - SQLAlchemy ORM models for:
     - Users, sessions
     - Community posts and likes
     - Practice sentences and practice records
     - Daily streak tracking
     - Payments / subscription info
   - PostgreSQL as the primary database (with connection pooling tuned for production)
   - Migration helper (`migrate_database`) to alter existing tables safely
   - Tier-based subscription logic (`SubscriptionTier`, `PaymentStatus`, `SUBSCRIPTION_LIMITS`, computed properties like `is_premium`, `tier_limits`)

5. **Business logic: learning + community features**
   - English speaking practice domain:
     - Sentences with difficulty levels, categories, hints
     - Practice records for spaced repetition and mastery tracking
     - Daily streaks: current streak, longest streak, total practice days
   - Community posts and likes: social aspect around practice content
   - Subscription/payments:
     - Multiple tiers (free, basic, premium, lifetime)
     - Limits per tier (daily sentences, history days, ads, etc.)
     - Payment model for storing Alipay-related info

6. **Deployment & environment**
   - Dockerfile:
     - Python 3.11 slim image
     - Installs PostgreSQL client libs (`libpq-dev`) and compilers
     - Runs app with **Gunicorn + Uvicorn worker** (`gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`)
   - docker-compose:
     - Orchestrates FastAPI app, PostgreSQL 15, and Redis 7
     - Volume mounts for Postgres data, Redis data, and uploaded files
     - Environment variables for `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `ENVIRONMENT`

7. **Caching / sessions with Redis**
   - Redis 7 is used in this project (per your memories and `docker-compose`) for:
     - Session storage
     - Caching frequently accessed data (for performance)
   - `redis` package in `requirements.txt` for connecting to Redis

8. **Async capabilities & file uploads**
   - Async route handlers (`async def`) for web endpoints
   - File uploads using `UploadFile` and `File`, saving to `static/uploads`
   - Multipart/form parsing via `python-multipart`

9. **Tooling & testing**
   - `pytest` + `pytest-asyncio` for tests
   - `httpx` for HTTP client/testing
   - `python-dotenv` for environment variable management
   - `alembic` for migrations (even though there’s also a custom migration helper)

10. **Miscellaneous techniques**
    - CORS configuration (`CORSMiddleware`) allowing cross-origin access
    - In-memory “mini DB” dictionaries for demo item and user data (`items_db`, `users_db`)
    - Use of `dateutil.relativedelta` for date arithmetic (e.g., subscription periods)

If you want, I can map specific endpoints (like practice, community, payment) to the techniques they demonstrate so you can use this project as a learning roadmap.