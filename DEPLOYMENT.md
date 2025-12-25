# 🚀 Deployment Guide

This guide covers deploying your FastAPI application to production with thousands of users.

## 📋 Pre-Deployment Checklist

- [ ] Set up PostgreSQL database
- [ ] Configure environment variables
- [ ] Set a secure SECRET_KEY
- [ ] Test locally with production settings
- [ ] Set up monitoring/logging

---

## 🌐 Option 1: Railway (Recommended for Beginners)

Railway offers easy deployment with free PostgreSQL.

### Steps:

1. **Create account** at [railway.app](https://railway.app)

2. **Connect GitHub repo**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

3. **Add PostgreSQL**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway auto-sets `DATABASE_URL`

4. **Set environment variables**
   ```
   SECRET_KEY=<generate-secure-key>
   ENVIRONMENT=production
   ```

5. **Deploy!** Railway auto-deploys on git push.

### Cost: Free tier includes 500 hours/month

---

## 🎨 Option 2: Render

### Steps:

1. **Create account** at [render.com](https://render.com)

2. **Create PostgreSQL database**
   - Dashboard → New → PostgreSQL
   - Copy the "External Database URL"

3. **Create Web Service**
   - New → Web Service → Connect repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT`

4. **Set environment variables**
   ```
   DATABASE_URL=<your-postgres-url>
   SECRET_KEY=<generate-secure-key>
   ```

### Cost: Free tier available (spins down after inactivity)

---

## 🐳 Option 3: Docker + VPS (DigitalOcean, AWS, etc.)

For more control and better performance.

### Steps:

1. **Create VPS** ($5-10/month)
   - DigitalOcean Droplet
   - AWS EC2
   - Linode

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt install docker-compose
   ```

3. **Clone and deploy**
   ```bash
   git clone <your-repo>
   cd <your-repo>
   
   # Create .env file
   cp .env.example .env
   nano .env  # Edit with your values
   
   # Start services
   docker-compose up -d
   ```

4. **Set up Nginx** (optional, for SSL)
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx
   ```

---

## 🔧 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | Session encryption key | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `REDIS_URL` | Redis connection (optional) | `redis://localhost:6379` |
| `ENVIRONMENT` | `development` or `production` | `production` |

---

## 📊 Scaling for Thousands of Users

### Database Optimization
```python
# Add indexes in database.py
class User(Base):
    __tablename__ = "users"
    username = Column(String(50), unique=True, index=True)  # ✅ Indexed
    email = Column(String(255), unique=True, index=True)    # ✅ Indexed
```

### Connection Pooling
```python
# In database.py, use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # Number of connections to keep
    max_overflow=30,        # Extra connections when needed
    pool_pre_ping=True,     # Verify connections
)
```

### Caching with Redis
```python
import redis
r = redis.from_url(os.getenv("REDIS_URL"))

# Cache frequently accessed data
def get_posts_cached():
    cached = r.get("posts")
    if cached:
        return json.loads(cached)
    posts = db.query(Post).all()
    r.setex("posts", 60, json.dumps(posts))  # Cache for 60 seconds
    return posts
```

### Load Balancing
```
                    ┌─────────────┐
                    │   Nginx     │
                    │ Load Balancer│
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ FastAPI  │    │ FastAPI  │    │ FastAPI  │
    │ Instance │    │ Instance │    │ Instance │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    ┌──────────┐
                    │PostgreSQL│
                    └──────────┘
```

---

## 🔒 Security Checklist

- [ ] Use HTTPS (Let's Encrypt with Certbot)
- [ ] Set secure SECRET_KEY
- [ ] Enable CORS only for your domain
- [ ] Use parameterized queries (SQLAlchemy does this)
- [ ] Rate limit API endpoints
- [ ] Hash passwords with bcrypt (upgrade from SHA-256)
- [ ] Set secure cookie flags

### Upgrade to bcrypt (recommended)
```bash
pip install bcrypt
```

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

---

## 📈 Monitoring

### Option 1: Sentry (Error Tracking)
```bash
pip install sentry-sdk[fastapi]
```

```python
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Option 2: Prometheus + Grafana
For detailed metrics and dashboards.

---

## 💰 Cost Estimates

| Users | Platform | Estimated Cost |
|-------|----------|----------------|
| 0-1,000 | Railway/Render Free | $0/month |
| 1,000-10,000 | Railway/Render Paid | $10-25/month |
| 10,000-100,000 | VPS + Managed DB | $50-200/month |
| 100,000+ | Cloud (AWS/GCP) | $200+/month |

---

## 🚀 Quick Deploy Commands

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render
Just connect your GitHub repo and Render auto-deploys!

### Docker
```bash
docker-compose up -d
```

---

## Need Help?

- FastAPI Docs: https://fastapi.tiangolo.com/deployment/
- Railway Docs: https://docs.railway.app/
- Render Docs: https://render.com/docs

