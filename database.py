import psycopg2, os

def connect_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products(
        id SERIAL PRIMARY KEY,
        name TEXT,
        price INTEGER,
        image TEXT,
        aisle TEXT,
        shelf TEXT,
        position INTEGER,
        fragile BOOLEAN,
        weight INTEGER
    )
    """)

    conn.commit()
    cur.close()
    conn.close()