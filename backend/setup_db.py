import sqlite3
import hashlib
import os

# === Define path to DB ===
db_path = os.path.join(os.path.dirname(__file__), 'users.db')

# === Connect and create cursor ===
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# === Create users table ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# === Create actions table ===
cursor.execute('''
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    customer TEXT NOT NULL,
    action TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# === Add default admin user ===
username = 'admin'
password = 'password'
hashed = hashlib.sha256(password.encode()).hexdigest()

cursor.execute(
    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
    (username, hashed)
)

# === Finalize ===
conn.commit()
conn.close()

print("✅ users.db initialized with default admin account and actions table.")
