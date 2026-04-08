from database import connect_db

conn = connect_db()
cur = conn.cursor()

products = [
    ("Milk", 30, "...", 500, False, "A", "1", 1),
    ("Eggs", 60, "...", 200, True, "A", "1", 2),
    ("Rice", 100, "...", 1000, False, "B", "2", 1),
    ("Bread", 40, "...", 300, False, "B", "2", 2),
    ("Juice", 80, "...", 400, False, "C", "3", 1)
]

cur.executemany(
    """INSERT INTO products 
    (name, price, image, weight, fragile, aisle, shelf, position)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
    products
)

conn.commit()
cur.close()
conn.close()

print("Products added ✅")