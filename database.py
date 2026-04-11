import psycopg2, os

def connect_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode="require")

def create_tables():
    conn=connect_db()
    cur=conn.cursor()

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
        image TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id SERIAL PRIMARY KEY,
        user_email TEXT,
        items TEXT,
        status TEXT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()