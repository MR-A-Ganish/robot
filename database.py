import psycopg2, os

def connect_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")


def create_tables():
    conn = connect_db()
    cur = conn.cursor()

    # CREATE TABLE (FULL STRUCTURE)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT,
        price INTEGER,
        image TEXT,
        aisle TEXT DEFAULT 'A',
        shelf TEXT DEFAULT '1',
        position INTEGER DEFAULT 1,
        fragile BOOLEAN DEFAULT FALSE,
        weight INTEGER DEFAULT 100
    )
    """)

    # 🔥 FORCE ADD COLUMNS (THIS IS THE REAL FIX)
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS aisle TEXT DEFAULT 'A';")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS shelf TEXT DEFAULT '1';")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 1;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS fragile BOOLEAN DEFAULT FALSE;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS weight INTEGER DEFAULT 100;")

    # 🔥 FORCE UPDATE OLD DATA
    cur.execute("""
    UPDATE products SET
        aisle = COALESCE(aisle, 'A'),
        shelf = COALESCE(shelf, '1'),
        position = COALESCE(position, 1),
        fragile = COALESCE(fragile, FALSE),
        weight = COALESCE(weight, 100)
    """)

    conn.commit()
    cur.close()
    conn.close()