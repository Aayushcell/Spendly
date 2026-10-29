import sqlite3
from flask import g
from werkzeug.security import generate_password_hash

DATABASE = "spendly.db"

def get_db():
    """
    Returns the database connection for the current request context.
    Ensures foreign key constraints are enabled.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Enable foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")
        # Return rows as dictionaries
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database by creating all necessary tables."""
    # Using a separate connection for initialization to avoid g context issues
    with sqlite3.connect(DATABASE) as conn:
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON;")

        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Expenses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
    print("Database initialized successfully.")

def seed_db():
    """Seeds the database with initial sample data."""
    # Using a separate connection for seeding
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row

        # 1. Check if data already exists to prevent duplicates
        cursor = conn.execute("SELECT 1 FROM users LIMIT 1")
        if cursor.fetchone():
            print("Database already seeded. Skipping.")
            return

        # 2. Insert Demo User
        hashed_pw = generate_password_hash("demo123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", hashed_pw)
        )
        user_id = cursor.lastrowid

        # 3. Insert 8 sample expenses across all fixed categories
        # Categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other
        expenses = [
            (user_id, 12.50, 'Food', '2026-10-01', 'Lunch at Cafe'),
            (user_id, 45.00, 'Transport', '2026-10-05', 'Gas refill'),
            (user_id, 120.00, 'Bills', '2026-10-10', 'Internet bill'),
            (user_id, 30.00, 'Health', '2026-10-12', 'Pharmacy'),
            (user_id, 15.00, 'Entertainment', '2026-10-15', 'Cinema ticket'),
            (user_id, 65.20, 'Shopping', '2026-10-18', 'Grocery shopping'),
            (user_id, 10.00, 'Other', '2026-10-20', 'Misc'),
            (user_id, 25.00, 'Food', '2026-10-25', 'Dinner'),
        ]

        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )

    print("Database seeded successfully.")

def create_user(name, email, password):
    """
    Creates a new user in the database.
    Returns the new user's ID on success.
    Raises sqlite3.IntegrityError if email is already taken.
    """
    db = get_db()
    hashed_password = generate_password_hash(password)
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, hashed_password)
    )
    db.commit()
    return cursor.lastrowid
