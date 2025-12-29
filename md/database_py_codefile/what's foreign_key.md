## **Foreign Key - Database Relationship Link**

A **foreign key** is a **column (or set of columns)** in one table that references the **primary key** of another table. It creates a **link/relationship** between two tables.

## **Simple Analogy:**
- **Primary Key** = Your social security number (unique to you)
- **Foreign Key** = Your spouse's social security number in your family record (references another person)

## **Visual Example:**

### **Table 1: Users (Parent Table)**
| **id** (PK) | name     |
|-------------|----------|
| **1**       | Alice    |
| **2**       | Bob      |
| **3**       | Charlie  |

### **Table 2: Orders (Child Table)**
| order_id (PK) | **user_id** (FK) | product  |
|---------------|------------------|----------|
| 101           | **1**            | Laptop   | ← Alice's order
| 102           | **2**            | Phone    | ← Bob's order  
| 103           | **1**            | Mouse    | ← Another of Alice's orders
| 104           | **3**            | Keyboard | ← Charlie's order

**Foreign Key:** `user_id` in Orders table **references** `id` in Users table

## **In SQLAlchemy Code:**
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)          # ← Primary Key
    name = Column(String)
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    product = Column(String)
    
    # FOREIGN KEY: Links to User.id
    user_id = Column(Integer, ForeignKey('users.id'))  # ← Foreign Key
    
    user = relationship("User", back_populates="orders")
```

## **What Foreign Keys Enforce:**

### **1. Referential Integrity**
```python
# CAN'T create an order for non-existent user
order = Order(product="Laptop", user_id=999)  # ❌ ERROR if no user 999
# Database says: "User 999 doesn't exist!"

# MUST reference valid user
order = Order(product="Laptop", user_id=1)    # ✅ OK if user 1 exists
```

### **2. Cascade Rules** (What happens when parent is deleted?)
```python
# Different behaviors:
user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
# Options:
# - CASCADE: Delete child when parent deleted
# - SET NULL: Set child's FK to NULL  
# - RESTRICT: Prevent parent deletion if children exist
# - NO ACTION: Similar to RESTRICT
# - SET DEFAULT: Set to default value
```

## **SQL Equivalent:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),  -- ← Foreign Key
    product VARCHAR(100)
    
    -- Alternative syntax:
    -- FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Valid:
INSERT INTO orders (user_id, product) VALUES (1, 'Laptop');  -- ✅ User 1 exists

-- Invalid:
INSERT INTO orders (user_id, product) VALUES (999, 'Laptop'); -- ❌ User 999 doesn't exist
```

## **Types of Relationships with Foreign Keys:**

### **1. One-to-Many (Most Common)**
```python
# One user can have many orders
class User(Base):
    id = Column(Integer, primary_key=True)
    orders = relationship("Order", back_populates="user")  # ← "Many" side

class Order(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # ← Foreign Key
    user = relationship("User", back_populates="orders")  # ← "One" side

# Usage:
user = session.query(User).first()
print(f"{user.name}'s orders:")
for order in user.orders:  # Access all orders of this user
    print(f"  - {order.product}")
```

### **2. One-to-One**
```python
# One user has one profile
class User(Base):
    id = Column(Integer, primary_key=True)
    profile = relationship("Profile", back_populates="user", uselist=False)

class Profile(Base):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)  # ← UNIQUE!
    user = relationship("User", back_populates="profile")

# Each user_id appears only once in Profile table
```

### **3. Many-to-Many** (Uses junction table)
```python
# Association/Junction table with TWO foreign keys
association_table = Table('user_courses', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),      # ← FK to users
    Column('course_id', Integer, ForeignKey('courses.id'))   # ← FK to courses
)

class User(Base):
    id = Column(Integer, primary_key=True)
    courses = relationship("Course", secondary=association_table, back_populates="users")

class Course(Base):
    id = Column(Integer, primary_key=True)
    users = relationship("User", secondary=association_table, back_populates="courses")

# Many users can take many courses
```

## **Real-World Examples:**

### **Example 1: Blog System**
```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    
    # Foreign key to author
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")
    
    # Foreign key to category
    category_id = Column(Integer, ForeignKey('categories.id'))
    category