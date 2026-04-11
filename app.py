from flask import Flask, render_template, request, redirect, session, jsonify
import os
import json
import razorpay
from dotenv import load_dotenv
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

# ---------------- LOAD ENV ----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    form = "login"

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
            session["cart"] = []
            return redirect("/dashboard")
        else:
            error = "Invalid email or password ❌"

    return render_template("login.html", error=error, form=form)

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        return render_template("login.html", error="User already exists ❌", form="signup")

    cur.execute("INSERT INTO users (email, password) VALUES (%s,%s)", (email, password))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/")

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
            "img": p[3]
        })

    return render_template("dashboard.html", products=products)

# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if "user" not in session:
        return redirect("/")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    p = cur.fetchone()

    cur.close()
    conn.close()

    if not p:
        return "Product not found ❌"

    cart = session.get("cart", [])
    found = False

    for item in cart:
        if item["id"] == p[0]:
            item["qty"] += 1
            found = True
            break

    if not found:
        cart.append({
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "image": p[3],
            "weight": p[4] if len(p) > 4 else 0,
            "fragile": p[5] if len(p) > 5 else False,
            "qty": 1
        })

    session["cart"] = cart
    return redirect("/cart")

# ---------------- CART ----------------
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/")

    cart = session.get("cart", [])
    total = sum(item["price"] * item["qty"] for item in cart)

    return render_template("cart.html", cart=cart, total=total)

# ---------------- INCREASE ----------------
@app.route("/increase/<int:index>")
def increase(index):
    cart = session.get("cart", [])

    if 0 <= index < len(cart):
        cart[index]["qty"] += 1

    session["cart"] = cart
    return redirect("/cart")

# ---------------- DECREASE ----------------
@app.route("/decrease/<int:index>")
def decrease(index):
    cart = session.get("cart", [])

    if 0 <= index < len(cart):
        if cart[index]["qty"] > 1:
            cart[index]["qty"] -= 1
        else:
            cart.pop(index)

    session["cart"] = cart
    return redirect("/cart")

# ---------------- PAYMENT PAGE ----------------
@app.route("/payment")
def payment():
    if "user" not in session:
        return redirect("/")

    cart = session.get("cart", [])
    total = sum(item["price"] * item["qty"] for item in cart)

    return render_template("payment.html", amount=total)

# ---------------- CREATE PAYMENT ----------------
@app.route("/create_payment", methods=["POST"])
def create_payment():
    try:
        key = os.getenv("RAZORPAY_KEY_ID")
        secret = os.getenv("RAZORPAY_SECRET")

        print("KEY:", key)       # DEBUG
        print("SECRET:", secret) # DEBUG

        if not key or not secret:
            return jsonify({"error": "Razorpay keys missing ❌"})

        client = razorpay.Client(auth=(key, secret))

        amount = int(request.form["amount"]) * 100

        if amount <= 0:
            return jsonify({"error": "Invalid amount ❌"})

        order = client.order.create({
            "amount": amount,
            "currency": "INR"
        })

        return jsonify({
            "order_id": order["id"],
            "key": key,
            "amount": amount
        })

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- PAYMENT SUCCESS ----------------
@app.route("/payment_success")
def payment_success():
    if "user" not in session:
        return redirect("/")

    items = session.get("cart", [])

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_email, items, status) VALUES (%s,%s,%s) RETURNING id",
        (session["user"], json.dumps(items), "processing")
    )

    order_id = cur.fetchone()[0]

    # 🤖 Robot process
    result = process_order(items)

    cur.execute(
        "UPDATE orders SET status=%s WHERE id=%s",
        ("completed", order_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    session["cart"] = []

    return render_template("result.html", result=result)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)