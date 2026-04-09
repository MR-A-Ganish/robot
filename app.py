from flask import Flask, render_template, request, redirect, session, jsonify
import json
import os
import razorpay
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Razorpay
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_SECRET = os.environ.get("RAZORPAY_SECRET")

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
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

        except Exception as e:
            print("Login Error:", e)
            return "Server error. Try again."

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
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

        except Exception as e:
            print("Signup Error:", e)
            return "Server error"

    return render_template("signup.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    try:
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

    except Exception as e:
        print("Dashboard Error:", e)
        return "Error loading products"


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

    try:
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

        return render_template("result.html", result=result)

    except Exception as e:
        print("Order Error:", e)
        return "Order failed"


# ---------------- INIT PRODUCTS ----------------
@app.route("/init_products")
def init_products():
    try:
        conn = connect_db()
        cur = conn.cursor()

        products = [
            ("Milk", 30, "https://cdn-icons-png.flaticon.com/512/1046/1046784.png", 500, False, "A", "1", 1),
            ("Eggs", 60, "https://cdn-icons-png.flaticon.com/512/1046/1046857.png", 200, True, "A", "1", 2),
            ("Rice", 100, "https://cdn-icons-png.flaticon.com/512/3075/3075977.png", 1000, False, "B", "2", 1),
            ("Bread", 40, "https://cdn-icons-png.flaticon.com/512/1046/1046751.png", 300, False, "B", "2", 2),
            ("Juice", 80, "https://cdn-icons-png.flaticon.com/512/3050/3050156.png", 400, False, "C", "3", 1)
        ]

        for p in products:
            cur.execute("""
                INSERT INTO products 
                (name, price, image, weight, fragile, aisle, shelf, position)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, p)

        conn.commit()
        cur.close()
        conn.close()

        return "Products Added ✅"

    except Exception as e:
        print("Init Error:", e)
        return "Error adding products"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- MAIN (FIXED FOR RENDER) ----------------
if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print("DB Init Error:", e)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)