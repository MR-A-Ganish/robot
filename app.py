from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
import razorpay
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Razorpay config
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))

create_tables()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = email
            return redirect("/dashboard")
        else:
            return "Invalid email or password ❌"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            return "User already exists ❌"

        hashed = generate_password_hash(password)

        cur.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/")

    return render_template("signup.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products")
    data = cur.fetchall()

    cur.close()
    conn.close()

    products = []
    for p in data:
        products.append({
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "img": p[3],
            "weight": p[4],
            "fragile": p[5]
        })

    return render_template("dashboard.html", products=products)


# ---------------- CART ----------------
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/")
    return render_template("cart.html")


# ---------------- PAYMENT ----------------
@app.route("/create_payment", methods=["POST"])
def create_payment():
    amount = int(request.form["amount"]) * 100

    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify({
        "order_id": order["id"],
        "key": RAZORPAY_KEY_ID,
        "amount": amount
    })


# ---------------- PLACE ORDER ----------------
@app.route("/place_order", methods=["POST"])
def place_order():
    if "user" not in session:
        return redirect("/")

    items = request.form["items"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_email, items, status) VALUES (%s, %s, %s)",
        (session["user"], items, "pending")
    )

    conn.commit()

    # 🤖 Robot processing
    result = process_order(json.loads(items))

    cur.execute(
        "UPDATE orders SET status=%s WHERE user_email=%s",
        ("processed", session["user"])
    )

    conn.commit()
    cur.close()
    conn.close()

    # 🔥 SHOW RESULT PAGE
    return render_template("result.html", result=result)


# ---------------- INIT PRODUCTS ----------------
@app.route("/init_products")
def init_products():
    conn = connect_db()
    cur = conn.cursor()

    products = [
        ("Milk", 30, "https://cdn-icons-png.flaticon.com/512/1046/1046784.png", 500, False),
        ("Eggs", 60, "https://cdn-icons-png.flaticon.com/512/1046/1046857.png", 200, True),
        ("Rice", 100, "https://cdn-icons-png.flaticon.com/512/3075/3075977.png", 1000, False),
        ("Bread", 40, "https://cdn-icons-png.flaticon.com/512/1046/1046751.png", 300, False),
        ("Juice", 80, "https://cdn-icons-png.flaticon.com/512/3050/3050156.png", 400, False)
    ]

    for p in products:
        cur.execute(
            "INSERT INTO products (name, price, image, weight, fragile) VALUES (%s, %s, %s, %s, %s)",
            p
        )

    conn.commit()
    cur.close()
    conn.close()

    return "Products Added ✅"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)