import psycopg2
import os

def connect_db():
    DATABASE_URL = os.environ.get("DATABASE_URL")

    return psycopg2.connect(DATABASE_URL)

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
        fragile BOOLEAN
    )
    """)

    # ORDERS
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

    conn.commit()
    cur.close()
    conn.close()