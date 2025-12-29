## **`primary_key=True` - Database Primary Key**

A **primary key** is a **unique identifier** for each record in a database table. It's the most fundamental concept in relational databases.

## **What a Primary Key Is:**

1. **Unique Identifier** → Like a social security number for database rows
2. **Mandatory** → Every table should have one (good practice)
3. **Non-null** → Can never be empty/NULL
4. **Immutable** → Shouldn't change once assigned

## **In Your Code:**
```python
id = Column(Integer, primary_key=True, index=True)
# This column is THE unique identifier for each row
```

## **Example Table: Users**

| **id** (Primary Key) | name | email |
|---------------------|------|-------|
| **1** | Alice | alice@email.com |
| **2** | Bob | bob@email.com |
| **3** | Charlie | charlie@email.com |

- `id=1` **uniquely identifies** Alice's record
- No other row can have `id=1`
- `id` cannot be NULL

## **Why Primary Keys Are Essential:**

### **1. Uniquely Identify Records**
```sql
-- Without primary key: Which John Smith?
SELECT * FROM users WHERE name = 'John Smith';

-- With primary key: Exact record
SELECT * FROM users WHERE id = 42;
```

### **2. Enable Relationships (Foreign Keys)**
```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)  # ← Primary key
    
class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # ← References users.id
    # "Which user wrote this post? Look at users.id"
```

### **3. Fast Lookups**
- Databases create special indexes for primary keys
- Finding by primary key is **extremely fast**

## **Types of Primary Keys:**

### **1. Natural Key** (Using existing data)
```python
# BAD PRACTICE usually
email = Column(String, primary_key=True)  # Email as primary key
# Problem: What if email changes?
```

### **2. Surrogate Key** (Artificial, like your `id`)
```python
# GOOD PRACTICE
id = Column(Integer, primary_key=True)  # Artificial ID
# Doesn't change, simple, efficient
```

### **3. Composite Primary Key** (Multiple columns)
```python
class Enrollment(Base):
    __tablename__ = 'enrollments'
    student_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, primary_key=True)
    # Both together are unique
    # Student 1 + Course 101 = unique combination
```

## **SQLAlchemy Behavior:**

### **Auto-increment (Default)**
```python
id = Column(Integer, primary_key=True)
# Automatically increments: 1, 2, 3, 4...
# You don't need to set it manually
```

### **Manual Primary Key**
```python
class Product(Base):
    __tablename__ = 'products'
    sku = Column(String, primary_key=True)  # Stock Keeping Unit
    # You must provide SKU for each product
```

### **UUID Primary Key**
```python
import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Generates: '123e4567-e89b-12d3-a456-426614174000'
```

## **Complete Example:**
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

class Author(Base):
    __tablename__ = 'authors'
    # PRIMARY KEY
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    
    # Related books
    books = relationship("Book", back_populates="author")

class Book(Base):
    __tablename__ = 'books'
    # PRIMARY KEY
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    
    # FOREIGN KEY references Author's primary key
    author_id = Column(Integer, ForeignKey('authors.id'))
    
    # Relationship
    author = relationship("Author", back_populates="books")

# Usage:
db = SessionLocal()

# Create author (id automatically assigned)
author = Author(name="J.K. Rowling")
db.add(author)
db.commit()
# author.id is now 1 (or next available number)

# Create book referencing author's primary key
book = Book(title="Harry Potter", author_id=author.id)
db.add(book)
db.commit()
```

## **Database SQL Equivalent:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,  -- ← Primary key in SQL
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);

-- INSERT (database auto-generates id)
INSERT INTO users (name, email) VALUES ('Alice', 'alice@email.com');
-- id becomes 1 automatically
```

## **Common Mistakes:**

### **1. Forgetting Primary Key**
```python
# BAD: No primary key
class LogEntry(Base):
    __tablename__ = 'logs'
    message = Column(String)
    timestamp = Column(DateTime)
    # Which log entry is which? Hard to reference!
```

### **2. Changing Primary Key Value**
```python
# DANGEROUS!
user = db.query(User).first()
user.id = 999  # Never do this! Breaks relationships.
```

### **3. Non-Unique "Primary Key"**
```python
# WON'T WORK as expected
age = Column(Integer, primary_key=True)
# Multiple people can have same age!
```

## **Best Practices:**

1. **Always use `primary_key=True`** on one column per table
2. **Use surrogate keys** (`id`) for most tables
3. **Let database auto-generate** (autoincrement)
4. **Never modify** primary key values
5. **Keep it simple** - integers are usually best

## **Index=True Bonus:**
```python
id = Column(Integer, primary_key=True, index=True)
# 'index=True' is redundant here!
# Primary keys are automatically indexed by databases
```

**Primary key** is your database's **social security system** - every record gets a unique, permanent ID that never changes and uniquely identifies it among all other records.