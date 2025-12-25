# 🐘 PostgreSQL Setup Guide for Windows

## Step 1: Install PostgreSQL

### Option A: Download Installer (Recommended)
1. Go to https://www.postgresql.org/download/windows/
2. Download the installer (EDB installer)
3. Run the installer and follow the wizard:
   - Choose installation directory (default is fine)
   - Select components: PostgreSQL Server, pgAdmin 4, Command Line Tools
   - Set password for `postgres` user: **`postgres`** (or your choice)
   - Port: **5432** (default)
   - Locale: Default
4. Complete the installation

### Option B: Using Chocolatey
```powershell
choco install postgresql
```

### Option C: Using Docker (if you have Docker installed)
```powershell
docker run --name postgres-local -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
```

---

## Step 2: Create the Database

### Using pgAdmin 4 (GUI)
1. Open pgAdmin 4 (installed with PostgreSQL)
2. Connect to local server (password: `postgres`)
3. Right-click "Databases" → "Create" → "Database"
4. Name: `english_practice`
5. Click "Save"

### Using Command Line (psql)
```powershell
# Open PowerShell and run:
psql -U postgres

# Enter password when prompted: postgres

# Create database:
CREATE DATABASE english_practice;

# Exit:
\q
```

---

## Step 3: Verify Connection

Test that your database is accessible:

```powershell
# In your project directory
python -c "from database import engine; print('✅ Connected to PostgreSQL!')"
```

---

## Step 4: Initialize Tables and Demo Data

```powershell
# Run the database setup script
python database.py
```

This will:
- Create all tables (users, sessions, posts, sentences, etc.)
- Add demo user (username: `demo`, password: `demo123`)
- Add sample posts and sentences

---

## Step 5: Run the Application

```powershell
# Install dependencies first
pip install -r requirements.txt

# Run the server
python main.py
```

Visit http://localhost:8000 and login with:
- **Username:** `demo`
- **Password:** `demo123`

---

## Troubleshooting

### "Connection refused" error
- Make sure PostgreSQL service is running:
  ```powershell
  # Check service status
  Get-Service -Name "postgresql*"
  
  # Start if stopped
  Start-Service -Name "postgresql-x64-15"  # Version may vary
  ```

### "Database does not exist" error
- Create the database manually (see Step 2)

### "Authentication failed" error
- Check your password in `database.py`:
  ```python
  DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/english_practice"
  ```

### Using a different password?
Update `database.py`:
```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:YOUR_PASSWORD@localhost:5432/english_practice"
)
```

Or set environment variable:
```powershell
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/english_practice"
python main.py
```

---

## Database Connection String Format

```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

| Part | Default Value |
|------|---------------|
| USERNAME | `postgres` |
| PASSWORD | `postgres` |
| HOST | `localhost` |
| PORT | `5432` |
| DATABASE_NAME | `english_practice` |

---

## Quick Docker Setup (Alternative)

If you prefer Docker, run this single command:

```powershell
docker-compose up -d db
```

This starts PostgreSQL with all settings pre-configured!

