from flask import Flask, render_template, request, redirect, session, jsonify
import os
import json
import razorpay
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Razorpay keys
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))


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

    cur.execute(
        "INSERT INTO users (email, password) VALUES (%s, %s)",
        (email, hashed)
    )

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


# ---------------- CART ----------------
@app.route("/cart", methods=["POST"])
def cart():
    items = request.form["items"]
    session["cart"] = items
    return redirect("/payment")


# ---------------- PAYMENT PAGE ----------------
@app.route("/payment")
def payment():
    if "user" not in session:
        return redirect("/")

    items = json.loads(session.get("cart", "[]"))

    total = sum(item["price"] for item in items)

    return render_template("payment.html", amount=total)


# ---------------- CREATE PAYMENT ----------------
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


# ---------------- PAYMENT SUCCESS ----------------
@app.route("/payment_success")
def payment_success():
    if "user" not in session:
        return redirect("/")

    items = json.loads(session.get("cart", "[]"))

    conn = connect_db()
    cur = conn.cursor()

    # Store order
    cur.execute(
        "INSERT INTO orders (user_email, items, status) VALUES (%s, %s, %s)",
        (session["user"], json.dumps(items), "processing")
    )

    conn.commit()

    # 🤖 ROBOT PROCESS
    result = process_order(items)

    # Update status
    cur.execute(
        "UPDATE orders SET status=%s WHERE user_email=%s",
        ("completed", session["user"])
    )

    conn.commit()
    cur.close()
    conn.close()

    return render_template("result.html", result=result)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    app.run(host="0.0.0.0", port=10000)