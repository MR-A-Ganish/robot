from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
import razorpay
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ✅ SESSION FIX
app.config["SESSION_PERMANENT"] = False


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
            session["cart"] = []   # ✅ initialize cart
            return redirect("/dashboard")
        else:
            error = "Invalid email or password ❌"

    return render_template("login.html", error=error, form=form)


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["email"]
    password = request.form["password"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cur.fetchone():
        return render_template("login.html", error="User already exists ❌", form="signup")

    hashed = generate_password_hash(password)

    cur.execute("INSERT INTO users (email, password) VALUES (%s,%s)", (email, hashed))

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

    item = {
        "id": p[0],
        "name": p[1],
        "price": p[2],
        "image": p[3],
        "fragile": p[5]
    }

    cart = session.get("cart", [])
    cart.append(item)

    session["cart"] = cart

    print("✅ Cart:", cart)  # DEBUG

    return redirect("/cart")   # ✅ direct to cart


# ---------------- CART ----------------
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/")

    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)

    return render_template("cart.html", cart=cart, total=total)


# ---------------- REMOVE ----------------
@app.route("/remove_from_cart/<int:index>")
def remove_from_cart(index):
    cart = session.get("cart", [])

    if 0 <= index < len(cart):
        cart.pop(index)

    session["cart"] = cart

    return redirect("/cart")


# ---------------- PAYMENT ----------------
@app.route("/payment")
def payment():
    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)

    return render_template("payment.html", amount=total)


# ---------------- CREATE PAYMENT ----------------
@app.route("/create_payment", methods=["POST"])
def create_payment():
    key = os.environ.get("RAZORPAY_KEY_ID")
    secret = os.environ.get("RAZORPAY_SECRET")

    client = razorpay.Client(auth=(key, secret))

    amount = int(request.form["amount"]) * 100

    order = client.order.create({
        "amount": amount,
        "currency": "INR"
    })

    return jsonify({
        "order_id": order["id"],
        "key": key,
        "amount": amount
    })


# ---------------- PAYMENT SUCCESS ----------------
@app.route("/payment_success")
def payment_success():

    items = session.get("cart", [])

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_email, items, status) VALUES (%s,%s,%s)",
        (session["user"], json.dumps(items), "processing")
    )

    conn.commit()

    # 🤖 ROBOT EXECUTION
    result = process_order(items)

    cur.execute(
        "UPDATE orders SET status=%s WHERE user_email=%s",
        ("completed", session["user"])
    )

    conn.commit()

    cur.close()
    conn.close()

    session["cart"] = []   # clear cart

    return render_template("result.html", result=result)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=10000)