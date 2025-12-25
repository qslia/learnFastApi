"""
Database migration script to add new columns to existing tables.
Run this once to update your database schema.
"""

from database import engine
from sqlalchemy import text

def migrate():
    print("🔄 Running database migrations...")
    
    with engine.connect() as conn:
        # Add subscription columns to users table
        migrations = [
            # Users table - subscription fields
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_expires_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS lifetime_member BOOLEAN DEFAULT FALSE",
            
            # Create payments table if not exists
            """
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                order_id VARCHAR(64) UNIQUE NOT NULL,
                alipay_trade_no VARCHAR(64),
                subscription_tier VARCHAR(20) NOT NULL,
                amount FLOAT NOT NULL,
                months INTEGER DEFAULT 1,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP
            )
            """,
            
            # Create practice_records table if not exists
            """
            CREATE TABLE IF NOT EXISTS practice_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                sentence_id INTEGER NOT NULL,
                practice_date DATE DEFAULT CURRENT_DATE,
                completed BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, sentence_id, practice_date)
            )
            """,
            
            # Create daily_streaks table if not exists
            """
            CREATE TABLE IF NOT EXISTS daily_streaks (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_practice_date DATE,
                total_practice_days INTEGER DEFAULT 0,
                total_sentences_practiced INTEGER DEFAULT 0
            )
            """,
        ]
        
        for sql in migrations:
            try:
                conn.execute(text(sql))
                print(f"✅ Executed: {sql[:50]}...")
            except Exception as e:
                # Ignore errors for "already exists" type errors
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print(f"⏭️  Skipped (already exists): {sql[:50]}...")
                else:
                    print(f"⚠️  Warning: {e}")
        
        conn.commit()
    
    print("✅ Database migration completed!")

if __name__ == "__main__":
    migrate()

