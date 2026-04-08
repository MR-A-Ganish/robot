from database import connect_db

conn = connect_db()
cur = conn.cursor()

products = [
    ("Milk", 30, "https://cdn-icons-png.flaticon.com/512/1046/1046784.png", 500, 0),
    ("Eggs", 60, "https://cdn-icons-png.flaticon.com/512/1046/1046857.png", 200, 1),
    ("Rice", 100, "https://cdn-icons-png.flaticon.com/512/3075/3075977.png", 1000, 0),
    ("Bread", 40, "https://cdn-icons-png.flaticon.com/512/1046/1046751.png", 300, 0),
    ("Juice", 80, "https://cdn-icons-png.flaticon.com/512/3050/3050156.png", 400, 0)
]

cur.executemany(
    "INSERT INTO products (name, price, image, weight, fragile) VALUES (?, ?, ?, ?, ?)",
    products
)

conn.commit()
conn.close()

print("Products added ✅")