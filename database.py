import psycopg2, os

def connect_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")


def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    # CREATE TABLE (if not exists)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
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

    # 🔥 ADD MISSING COLUMNS (THIS FIXES YOUR ERROR)
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS aisle TEXT;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS shelf TEXT;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS position INTEGER;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS fragile BOOLEAN;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS weight INTEGER;")

    conn.commit()
    cur.close()
    conn.close()