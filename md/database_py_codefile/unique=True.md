## **`unique=True` - Database Unique Constraint**

The **`unique=True`** constraint ensures that **no two rows can have the same value** in that column. It's like saying "this value must be one-of-a-kind in this table."

## **What It Does:**

1. **Prevents duplicates** in the column
2. **Creates a unique index** in the database
3. **Enforces data integrity**

## **In Your Code:**
```python
username = Column(String(50), unique=True, index=True, nullable=False)
# ↑ No two users can have the same username
```

## **Example Table: Users**

| id | username (UNIQUE) | email |
|----|-------------------|-------|
| 1 | **alice123** | alice@email.com |
| 2 | **bob_smith** | bob@email.com |
| 3 | **charlie99** | charlie@email.com |

✅ **Allowed:**
- `alice123`, `bob_smith`, `charlie99` (all different)

❌ **Blocked:**
- Trying to add another `alice123` → **ERROR!**
- Trying to add another `bob_smith` → **ERROR!**

## **Why Use Unique Constraints:**

### **1. Prevent Duplicate Data**
```python
# Without unique:
db.add(User(username="john"))
db.add(User(username="john"))  # Oops! Two Johns
# Both get saved - confusing!

# With unique=True:
db.add(User(username="john"))
db.add(User(username="john"))  # ← Database ERROR!
# "Duplicate entry 'john' for key 'username'"
```

### **2. Business Rules Enforcement**
```python
# Email must be unique (one account per email)
email = Column(String, unique=True, nullable=False)

# Social Security Number must be unique
ssn = Column(String(11), unique=True)

# Product SKU must be unique
sku = Column(String, unique=True)

# Phone number must be unique
phone = Column(String, unique=True)
```

### **3. Fast Lookups**
```python
# Database creates special index for unique columns
username = Column(String, unique=True, index=True)
# Finding by username is VERY fast (O(log n))
```

## **How It Works in SQL:**

```sql
-- SQL equivalent
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,  -- ← UNIQUE constraint
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Allowed:
INSERT INTO users (username, email) VALUES ('john', 'john@email.com');

-- ERROR (duplicate username):
INSERT INTO users (username, email) VALUES ('john', 'different@email.com');

-- ERROR (duplicate email):
INSERT INTO users (username, email) VALUES ('different', 'john@email.com');
```

## **SQLAlchemy Examples:**

### **1. Basic Unique Column**
```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)  # ← Must be unique
    email = Column(String(100), unique=True)    # ← Also unique
    
# Usage:
try:
    user1 = User(username="alice", email="alice@email.com")
    db.add(user1)
    db.commit()
    
    # This will fail:
    user2 = User(username="alice", email="bob@email.com")  # Same username!
    db.add(user2)
    db.commit()  # Raises IntegrityError
except IntegrityError:
    db.rollback()
    print("Username already exists!")
```

### **2. Multiple Unique Columns**
```python
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True)      # Unique SKU
    upc = Column(String, unique=True)      # Unique UPC code
    name = Column(String)                  # Not unique (multiple products can have same name)
```

### **3. Unique Composite Constraint (Multiple Columns Together)**
```python
class Enrollment(Base):
    __tablename__ = 'enrollments'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    course_id = Column(Integer)
    semester = Column(String)
    
    # Unique across student_id + course_id + semester
    # A student can't enroll in same course same semester twice
    __table_args__ = (
        UniqueConstraint('student_id', 'course_id', 'semester', name='uix_student_course_semester'),
    )

# This is allowed:
# Student 1, Course 101, Semester "Fall 2024"
# Student 1, Course 101, Semester "Spring 2025"

# This is BLOCKED (duplicate):
# Student 1, Course 101, Semester "Fall 2024"
# Student 1, Course 101, Semester "Fall 2024" ← ERROR!
```

## **Unique vs Primary Key:**

| Feature | **Primary Key** | **Unique Constraint** |
|---------|----------------|----------------------|
| **Uniqueness** | Must be unique | Must be unique |
| **Null values** | Cannot be NULL | Can be NULL (usually) |
| **Quantity** | One per table | Multiple per table |
| **Purpose** | Identify rows | Prevent duplicates |
| **Relationships** | Used for foreign keys | Not used for foreign keys |
| **Index** | Always indexed | Usually indexed |

## **Important Nuances:**

### **1. NULL Values in Unique Columns**
```python
# By default, unique columns can have multiple NULLs
email = Column(String, unique=True)
# Allowed: NULL, NULL, NULL (multiple empty emails)
# Allowed: "a@b.com", NULL, NULL
# Blocked: "a@b.com", "a@b.com"

# To prevent multiple NULLs:
email = Column(String, unique=True, nullable=False)
# Or use database-specific syntax
```

### **2. Case Sensitivity**
```python
# Database default: Usually CASE SENSITIVE
username = Column(String, unique=True)
# "John" and "JOHN" are DIFFERENT (allowed)

# Case insensitive unique (database-specific):
# PostgreSQL:
username = Column(String, unique=True)
# Plus in table_args:
__table_args__ = (
    Index('ix_users_username_lower', func.lower(username), unique=True),
)
```

## **Real-World Examples:**

### **E-commerce Site:**
```python
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    sku = Column(String(20), unique=True)          # Unique stock code
    upc_code = Column(String(12), unique=True)     # Unique barcode
    serial_number = Column(String, unique=True)    # Unique for each item
    name = Column(String)                          # Not unique
```

### **Social Media App:**
```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(30), unique=True)     # @handle must be unique
    email = Column(String, unique=True)            # One account per email
    phone = Column(String, unique=True, nullable=True)  # Optional but unique
```

### **Banking System:**
```python
class Account(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    account_number = Column(String(20), unique=True)  # Must be unique
    customer_id = Column(Integer)
    # A customer can have multiple accounts, but each number is unique
```

## **Error Handling:**
```python
from sqlalchemy.exc import IntegrityError

def create_user(username, email):
    try:
        user = User(username=username, email=email)
        db.add(user)
        db.commit()
        return user
    except IntegrityError as e:
        db.rollback()
        
        # Check which constraint failed
        if "username" in str(e):
            return {"error": "Username already taken"}
        elif "email" in str(e):
            return {"error": "Email already registered"}
        else:
            return {"error": "Database error"}
```

## **Best Practices:**

1. **Use `unique=True`** for any field that should be unique (email, username, SSN, etc.)
2. **Combine with `nullable=False`** if the field is required
3. **Add `index=True`** for better performance (often automatic with unique)
4. **Handle `IntegrityError`** in your code
5. **Use composite unique constraints** for multi-field uniqueness

**Unique constraint** is your database's **duplicate checker** - it ensures that critical values remain one-of-a-kind, maintaining data integrity and preventing conflicts.