import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if not DATABASE_URL:
        raise Exception("❌ DATABASE_URL not found")

    return psycopg2.connect(DATABASE_URL, sslmode="require")


def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # PRODUCTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
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
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_email TEXT,
        items TEXT,
        status TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()