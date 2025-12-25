"""
Database configuration for production deployment.
Uses SQLAlchemy with support for PostgreSQL (production) or SQLite (development).
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Date,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date
import os

# Database URL - PostgreSQL for production
# IMPORTANT: Using psycopg3 driver (postgresql+psycopg) to fix Windows Unicode issues
#
# Connection string format:
#   postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE
#
# ⚠️  CHANGE THE PASSWORD BELOW to match your PostgreSQL installation password!
#
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:a123@localhost:5432/english_practice",
    #                             ^^^^^^^^^^^^^^^^^
    #                             Replace with your actual PostgreSQL password!
)

# Fix for cloud providers and ensure psycopg3 driver is used
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

print(f"🐘 Connecting to PostgreSQL: {DATABASE_URL.split('@')[-1]}")

# Create engine with connection pooling for production scale
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Number of persistent connections
    max_overflow=30,  # Extra connections when needed
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ============== Database Models ==============


class User(Base):
    """User account model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship(
        "Post", back_populates="author_user", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    """User session model for authentication"""

    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")


class Post(Base):
    """Community post model"""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    likes = Column(Integer, default=0)

    # Relationships
    author_user = relationship("User", back_populates="posts")
    post_likes = relationship(
        "PostLike", back_populates="post", cascade="all, delete-orphan"
    )


class PostLike(Base):
    """Track which users liked which posts"""

    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="post_likes")


class Sentence(Base):
    """Practice sentence model"""

    __tablename__ = "sentences"

    id = Column(Integer, primary_key=True, index=True)
    chinese = Column(Text, nullable=False)
    hint = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PracticeRecord(Base):
    """Track user practice statistics by date"""

    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sentence_id = Column(Integer, ForeignKey("sentences.id"), nullable=False)
    practice_date = Column(Date, default=date.today, index=True)
    completed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint: one record per user per sentence per day
    __table_args__ = (
        UniqueConstraint('user_id', 'sentence_id', 'practice_date', name='unique_daily_practice'),
    )

    # Relationships
    user = relationship("User", backref="practice_records")


class DailyStreak(Base):
    """Track user's daily practice streak"""

    __tablename__ = "daily_streaks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_practice_date = Column(Date, nullable=True)
    total_practice_days = Column(Integer, default=0)
    total_sentences_practiced = Column(Integer, default=0)

    # Relationships
    user = relationship("User", backref="streak")


# ============== Database Utilities ==============


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency to get database session.
    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_demo_data(db):
    """Initialize database with demo data if empty"""
    # Check if demo user exists
    demo_user = db.query(User).filter(User.username == "demo").first()
    if not demo_user:
        import hashlib

        # Create demo user
        demo_user = User(
            username="demo",
            email="demo@example.com",
            password_hash=hashlib.sha256("demo123".encode()).hexdigest(),
            full_name="Demo User",
            is_active=True,
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

        # Create demo posts
        posts = [
            Post(
                author_id=demo_user.id,
                content="Welcome to the English Speaking Practice community! 🎉 Feel free to share your learning progress, ask questions, or help others.",
                likes=12,
            ),
            Post(
                author_id=demo_user.id,
                content="今天学了一个新句子：The weather in southwest China is very special. 西南部的天气真的很特别！",
                likes=5,
            ),
            Post(
                author_id=demo_user.id,
                content="Does anyone have tips for remembering vocabulary? I keep forgetting new words after a few days. 😅",
                likes=3,
            ),
        ]
        db.add_all(posts)

        # Create demo sentences
        sentences = [
            Sentence(
                id=141,
                chinese="中国西南部的天气很特别。",
                hint="The weather in... is very special/unique.",
            ),
            Sentence(
                id=142,
                chinese="春天和秋天是最好的季节。",
                hint="Spring and autumn are...",
            ),
            Sentence(
                id=143,
                chinese="中国中部和东部的天气大不相同。",
                hint="The weather in... is very different from...",
            ),
            Sentence(
                id=144,
                chinese="暑假里我想和朋友们去旅行。",
                hint="During summer vacation, I want to... with my friends.",
            ),
            Sentence(
                id=145,
                chinese="在秋天野餐是令人愉快的。",
                hint="Having a picnic in autumn is...",
            ),
            Sentence(
                id=146,
                chinese="人们在这个季节喜欢参加什么活动?",
                hint="What activities do people like to... in this season?",
            ),
            Sentence(
                id=147,
                chinese="在六月，这儿经常下大雨。",
                hint="In June, it often... here.",
            ),
            Sentence(
                id=148,
                chinese="在这么热的天气里去游泳很凉爽。",
                hint="It's refreshing/cool to... in such hot weather.",
            ),
        ]
        db.add_all(sentences)
        db.commit()

        print("✅ Demo data initialized!")


if __name__ == "__main__":
    # Run this file directly to create tables
    print("Creating database tables...")
    create_tables()
    print("✅ Tables created!")

    # Initialize demo data
    db = SessionLocal()
    init_demo_data(db)
    db.close()
