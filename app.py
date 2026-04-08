from flask import Flask, render_template, request, redirect, session
import json
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = "supersecretkey"

create_tables()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()

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

        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        if cur.fetchone():
            return "User already exists ❌"

        hashed = generate_password_hash(password)

        cur.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, hashed)
        )
        conn.commit()

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

    products = []
    for p in data:
        products.append({
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "img": p[3],
            "weight": p[4],
            "fragile": bool(p[5])
        })

    return render_template("dashboard.html", products=products)

# ---------------- CART PAGE ----------------
@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect("/")
    return render_template("cart.html")

# ---------------- PLACE ORDER ----------------
@app.route("/place_order", methods=["POST"])
def place_order():
    items = request.form["items"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user, items, status) VALUES (?, ?, ?)",
        (session["user"], items, "pending")
    )
    order_id = cur.lastrowid
    conn.commit()

    result = process_order(json.loads(items))

    cur.execute(
        "UPDATE orders SET status=? WHERE id=?",
        ("processed", order_id)
    )
    conn.commit()

    return f"✅ Order Placed Successfully!\n\n{result}"

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)