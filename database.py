import psycopg2
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


# ---------------- CONNECT DB ----------------
def connect_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # ✅ Production (Render)
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, sslmode='require')

    # ✅ Local (SQLite)
    return sqlite3.connect("app.db")


# ---------------- CREATE TABLES ----------------
def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    is_sqlite = "sqlite3" in str(type(conn))

    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"

    # USERS
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS users (
        id {id_type},
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # PRODUCTS
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS products (
        id {id_type},
        name TEXT,
        price INTEGER,
        image TEXT,
        weight INTEGER,
        fragile BOOLEAN,
        aisle TEXT,
        shelf TEXT,
        position INTEGER
    )
    """)

    # ORDERS
    cur.execute(f"""
    CREATE TABLE IF NOT EXISTS orders (
        id {id_type},
        user_email TEXT,
        items TEXT,
        status TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()