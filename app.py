from flask import Flask, render_template, request, redirect, session
from dotenv import load_dotenv
from database import connect_db, create_tables
from robot.main import process_order

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- INIT DB SAFELY ----------------
def init_db_safe():
    conn = connect_db()
    cur = conn.cursor()

    # Ensure table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT,
        price INTEGER,
        image TEXT
    )
    """)

    # Add missing columns safely
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS aisle TEXT DEFAULT 'A';")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS shelf TEXT DEFAULT '1';")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 1;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS fragile BOOLEAN DEFAULT FALSE;")
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS weight INTEGER DEFAULT 100;")

    # Fix existing rows
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


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form.get("email", "guest")
        session["cart"] = []
        session["wallet"] = 1000
        return redirect("/dashboard")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    cur.close()
    conn.close()

    cart = session.get("cart", [])

    products = []
    for p in data:
        qty = 0
        for item in cart:
            if item["id"] == p[0]:
                qty = item["qty"]

        products.append({
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "img": p[3] if len(p) > 3 else "",
            "qty": qty
        })

    return render_template("dashboard.html", products=products)


# ---------------- UPDATE CART ----------------
@app.route("/update_cart/<int:product_id>/<action>")
def update_cart(product_id, action):

    cart = session.get("cart", [])
    found = False

    for item in cart:
        if item["id"] == product_id:
            found = True

            if action == "increase":
                item["qty"] += 1
            elif action == "decrease":
                if item["qty"] > 1:
                    item["qty"] -= 1
                else:
                    cart.remove(item)
            break

    if not found and action == "increase":
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
        p = cur.fetchone()
        cur.close()
        conn.close()

        if not p:
            return "❌ Product not found"

        cart.append({
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "image": p[3] if len(p) > 3 else "",
            "fragile": False,
            "weight": 100,
            "qty": 1
        })

    session["cart"] = cart
    return redirect("/dashboard")


# ---------------- CART ----------------
@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] * item["qty"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)


# ---------------- CHECKOUT ----------------
@app.route("/checkout")
def checkout():
    cart = session.get("cart", [])
    total = sum(item["price"] * item["qty"] for item in cart)
    wallet = session.get("wallet", 0)
    return render_template("checkout.html", total=total, wallet=wallet)


# ---------------- PLACE ORDER ----------------
@app.route("/place_order")
def place_order():

    cart = session.get("cart", [])

    if not cart:
        return "❌ Cart is empty"

    total = sum(item["price"] * item["qty"] for item in cart)
    wallet = session.get("wallet", 0)

    if wallet < total:
        return "❌ Not enough balance"

    session["wallet"] = wallet - total

    try:
        result = process_order(cart)
    except Exception as e:
        return f"❌ Robot Error: {str(e)}"

    session["cart"] = []

    return render_template("result.html", result=result)


# ---------------- ADD PRODUCT ----------------
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        try:
            conn = connect_db()
            cur = conn.cursor()

            cur.execute("""
            INSERT INTO products (name,price,image,aisle,shelf,position,fragile,weight)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                request.form.get("name"),
                int(request.form.get("price", 0)),
                request.form.get("image", ""),
                request.form.get("aisle", "A"),
                request.form.get("shelf", "1"),
                int(request.form.get("position", 1)),
                request.form.get("fragile") == "on",
                int(request.form.get("weight", 100))
            ))

            conn.commit()
            cur.close()
            conn.close()

            return redirect("/dashboard")

        except Exception as e:
            return f"❌ Error: {str(e)}"

    return render_template("add_product.html")


# ---------------- RESET DB (LAST RESORT) ----------------
@app.route("/reset_db")
def reset_db():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS products")
    conn.commit()
    cur.close()
    conn.close()
    return "✅ DB Reset Done"


# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    init_db_safe()   # 🔥 THIS FIXES YOUR ERROR AUTOMATICALLY
    app.run(debug=True)