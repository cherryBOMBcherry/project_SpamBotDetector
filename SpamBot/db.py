import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "spam_bot.db")

def init_db():
    """Вызывается один раз при старте бота в main()"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missed_spam (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            added_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_missed_spam(user_id: int, text: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO missed_spam (user_id, text, added_at) VALUES (?, ?, ?)",
        (user_id, text, current_time)
    )
    
    conn.commit()
    conn.close()