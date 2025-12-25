You're right! The current code uses in-memory storage which loses data when the server restarts. Let me update `main.py` to use the PostgreSQL database with SQLAlchemy so your accounts persist.

[1 tool called]

Now I'll rewrite `main.py` to use PostgreSQL with SQLAlchemy for persistent storage. First, let me also check the database.py file:

[1 tool called]

Now let me rewrite `main.py` to use PostgreSQL with SQLAlchemy:

[2 tools called]

Now let me update the `database.py` to default to PostgreSQL instead of SQLite:

[2 tools called]

Now let me create a setup script to help you install PostgreSQL and set up the database:

[2 tools called]

These are just IDE warnings because the packages aren't installed yet. Let me check if you need to install the dependencies:

[1 tool called]

I see you've already installed dependencies. Now you need to set up PostgreSQL. Here's a summary of what's been done and what you need to do:

## ✅ Changes Made

### 1. `main.py` - Now uses PostgreSQL database
- All auth (login, signup, sessions) now saved to PostgreSQL
- Posts and sentences also saved to database
- Data persists across server restarts!

### 2. `database.py` - Configured for PostgreSQL
- Default connection: `postgresql://postgres:postgres@localhost:5432/english_practice`
- Connection pooling enabled for better performance

### 3. `setup_postgres.md` - Setup guide created

---

## 🚀 What You Need to Do

### Step 1: Install PostgreSQL on Windows

**Easiest way - Download installer:**
1. Go to https://www.postgresql.org/download/windows/
2. Download and run the EDB installer
3. Set password to `postgres` during installation
4. Keep port as `5432`

**Or use Docker:**
```powershell
docker-compose up -d db
```

### Step 2: Create the database

Open **pgAdmin 4** (installed with PostgreSQL) or run in PowerShell:

```powershell
# Connect to PostgreSQL
psql -U postgres

# Create database (in psql prompt)
CREATE DATABASE english_practice;
\q
```

### Step 3: Run the app

[1 tool called]

No problem! Here's the complete guide:

---

## 📋 Complete Setup Steps

### 1️⃣ Install PostgreSQL
Download from: https://www.postgresql.org/download/windows/

During installation:
- Password: `postgres`
- Port: `5432`

### 2️⃣ Create Database
Open **pgAdmin 4** or **SQL Shell (psql)** and run:
```sql
CREATE DATABASE english_practice;
```

### 3️⃣ Run the App
```powershell
python main.py
```

The app will automatically:
- ✅ Create all database tables
- ✅ Add demo user (`demo` / `demo123`)
- ✅ Add sample posts and sentences

### 4️⃣ Test It!
1. Visit http://localhost:8000
2. Sign up with a new account
3. Stop the server (Ctrl+C)
4. Restart the server
5. **Login with your account - it's saved!** 🎉

---

## 🔧 If Using Different Password

If you set a different PostgreSQL password during installation, update `database.py`:

```python
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/english_practice"
```

Or set environment variable:
```powershell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/english_practice"
```