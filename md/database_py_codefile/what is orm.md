## **ORM = Object-Relational Mapping**

## **Full Name & Concept:**
**Object-Relational Mapping** is a **programming technique** that lets you work with database data using **objects** in your code, instead of writing raw SQL queries.

## **Analogy: Translator**
Think of ORM as a **translator** between:
- **Your Python objects** (classes, instances)
- **Database tables** (rows, columns)

Without ORM: You speak SQL, database speaks SQL
With ORM: You speak Python, ORM translates to SQL

## **How It Works:**

### **Without ORM (Raw SQL):**
```python
# Direct SQL - Manual mapping
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Create table with SQL
cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT
    )
""")

# Insert with SQL
cursor.execute("""
    INSERT INTO users (name, email) 
    VALUES (?, ?)
""", ("John Doe", "john@email.com"))

# Query with SQL
cursor.execute("SELECT * FROM users WHERE id = ?", (1,))
row = cursor.fetchone()

# Manual mapping to object
class User:
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

user = User(row[0], row[1], row[2])  # Manual mapping
```

### **With ORM (SQLAlchemy):**
```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

# Define as Python class
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    
    # Python methods
    def greet(self):
        return f"Hello, I'm {self.name}"

# Create table automatically
Base.metadata.create_all(engine)

# Work with objects
session = Session(engine)

# Insert (no SQL!)
user = User(name="John Doe", email="john@email.com")
session.add(user)  # ORM generates SQL: INSERT INTO users...
session.commit()

# Query (no SQL!)
user = session.query(User).filter_by(id=1).first()
print(user.greet())  # "Hello, I'm John Doe"
print(user.email)    # "john@email.com"
```

## **The "Mapping" Part:**

| **Object (Python)** | **Relational (Database)** | **Mapping** |
|-------------------|-------------------------|------------|
| `class User` | `CREATE TABLE users` | Class ↔ Table |
| `user = User()` | Row in `users` table | Instance ↔ Row |
| `user.name = "John"` | `name` column | Attribute ↔ Column |
| `user.save()` | `INSERT/UPDATE` | Method ↔ SQL Operation |
| `session.query(User)` | `SELECT * FROM users` | Query ↔ SQL Query |

## **Key Benefits of ORM:**

### **1. Productivity**
```python
# ORM: Simple and readable
new_user = User(name="Alice", age=25, city="NYC")
db.session.add(new_user)
db.session.commit()

# vs Raw SQL: More verbose, error-prone
cursor.execute("""
    INSERT INTO users (name, age, city) 
    VALUES (%s, %s, %s)
""", ("Alice", 25, "NYC"))
```

### **2. Database Agnostic**
```python
# Same code works with different databases
# SQLAlchemy handles the differences:
# - PostgreSQL
# - MySQL
# - SQLite
# - Oracle
# - SQL Server

# ORM generates appropriate SQL for each database
```

### **3. Type Safety**
```python
# Compile-time checking
user = User(name="John", email="john@email.com")
# email is String type - database expects TEXT/VARCHAR

# VS raw SQL where you might do:
cursor.execute("INSERT INTO users (name, email) VALUES (?, ?)", 
               ("John", 12345))  # Oops! Email is number
```

### **4. Relationships Made Easy**
```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    posts = relationship("Post", back_populates="user")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="posts")

# Easy navigation
user = session.query(User).first()
for post in user.posts:  # ORM handles the JOIN
    print(post.title)
```

## **How SQLAlchemy ORM Works Internally:**

### **1. Metadata Layer**
```python
# SQLAlchemy tracks everything
Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

# Behind the scenes:
print(Base.metadata.tables)  # Shows all tables
print(Product.__table__)     # Table definition
print(Product.id.property)   # Column properties
```

### **2. Unit of Work Pattern**
```python
# Tracks changes automatically
user = User(name="Bob")
session.add(user)  # Marked as "new"

user.name = "Robert"  # Marked as "dirty"

# On commit:
# 1. INSERT for new objects
# 2. UPDATE for changed objects  
# 3. DELETE for removed objects
# All in optimal order, in transaction
session.commit()
```

### **3. Identity Map**
```python
# Ensures each database row = one Python object
user1 = session.query(User).get(1)
user2 = session.query(User).get(1)

print(user1 is user2)  # True - Same object!
# Prevents duplicate objects in memory
```

## **Common ORM Operations:**

### **CRUD Operations:**
```python
# CREATE
user = User(name="Alice", email="alice@email.com")
session.add(user)

# READ
user = session.query(User).filter_by(name="Alice").first()
users = session.query(User).filter(User.age > 18).all()

# UPDATE
user.email = "new_email@example.com"
# Auto-detects change

# DELETE
session.delete(user)
```

### **Relationships:**
```python
# One-to-Many
class Author(Base):
    books = relationship("Book", back_populates="author")

class Book(Base):
    author_id = Column(Integer, ForeignKey('authors.id'))
    author = relationship("Author", back_populates="books")

# Many-to-Many
association_table = Table('association', Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id')),
    Column('course_id', Integer, ForeignKey('courses.id'))
)

class Student(Base):
    courses = relationship("Course", secondary=association_table, back_populates="students")

class Course(Base):
    students = relationship("Student", secondary=association_table, back_populates="courses")
```

## **When NOT to Use ORM:**

### **1. Complex Analytics Queries**
```python
# ORM can be cumbersome for complex reports
# Raw SQL might be cleaner:

# ORM version (complex):
session.query(
    func.count(Order.id),
    func.extract('month', Order.created_at),
    User.country
).join(User).group_by(
    func.extract('month', Order.created_at),
    User.country
).all()

# Raw SQL version (clearer):
"""
SELECT 
    COUNT(o.id),
    EXTRACT(MONTH FROM o.created_at) as month,
    u.country
FROM orders o
JOIN users u ON o.user_id = u.id
GROUP BY EXTRACT(MONTH FROM o.created_at), u.country
"""
```

### **2. Bulk Operations**
```python
# ORM: Slow for 10,000 rows
for i in range(10000):
    user = User(name=f"user_{i}")
    session.add(user)  # 10,000 individual INSERTs
session.commit()

# Better: Bulk SQL
session.execute(
    User.__table__.insert(),
    [{"name": f"user_{i}"} for i in range(10000)]
)
```

## **Popular ORMs:**

1. **SQLAlchemy** (Python) - Most powerful, flexible
2. **Django ORM** (Python) - Simpler, Django-integrated
3. **Hibernate** (Java) - Enterprise Java ORM
4. **Entity Framework** (C#) - .NET ORM
5. **Sequelize** (JavaScript) - Node.js ORM
6. **Active Record** (Ruby) - Ruby on Rails ORM

## **SQLAlchemy's Hybrid Approach:**
```python
# SQLAlchemy lets you choose:
# 1. Pure ORM (High-level)
user = session.query(User).filter(User.name == "John").first()

# 2. Core SQL (Mid-level)
stmt = select(User).where(User.name == "John")
result = session.execute(stmt)

# 3. Raw SQL (Low-level)  
session.execute("SELECT * FROM users WHERE name = :name", {"name": "John"})

# Mix and match as needed!
```

## **Summary:**
**Object-Relational Mapping (ORM)** is like having a **personal translator** between your object-oriented code and your relational database. It lets you:

- Work with **Python objects** instead of SQL
- **Auto-generate** SQL queries
- Handle **database differences** automatically
- Maintain **clean, reusable** code
- Focus on **business logic** not database syntax

**SQLAlchemy ORM** is particularly powerful because it doesn't hide SQL from you - it empowers you to use objects when convenient and drop down to SQL when needed.