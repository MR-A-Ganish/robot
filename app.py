from flask import Flask, render_template, request, redirect, session, jsonify
import os
import json
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = connect_db()
            cur = conn.cursor()

            is_sqlite = "sqlite3" in str(type(conn))

            query = "SELECT * FROM users WHERE email=?" if is_sqlite else "SELECT * FROM users WHERE email=%s"
            cur.execute(query, (email,))

            user = cur.fetchone()

            cur.close()
            conn.close()

            if user:
                stored_password = user[2]

                # ✅ Handle both hashed + plain (for safety)
                if stored_password.startswith("pbkdf2:"):
                    if check_password_hash(stored_password, password):
                        session["user"] = email
                        return redirect("/dashboard")
                else:
                    if stored_password == password:
                        session["user"] = email
                        return redirect("/dashboard")

            return "Invalid email or password ❌"

        except Exception as e:
            print("🔥 Login Error:", e)
            return f"Server error: {e}"

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

            is_sqlite = "sqlite3" in str(type(conn))

            check_query = "SELECT * FROM users WHERE email=?" if is_sqlite else "SELECT * FROM users WHERE email=%s"
            cur.execute(check_query, (email,))

            if cur.fetchone():
                return "User already exists ❌"

            hashed = generate_password_hash(password)

            insert_query = "INSERT INTO users (email, password) VALUES (?, ?)" if is_sqlite else "INSERT INTO users (email, password) VALUES (%s, %s)"
            cur.execute(insert_query, (email, hashed))

            conn.commit()
            cur.close()
            conn.close()

            return redirect("/")

        except Exception as e:
            print("🔥 Signup Error:", e)
            return f"Server error: {e}"

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
        print("🔥 Dashboard Error:", e)
        return f"Error: {e}"


# ---------------- ADD SAMPLE PRODUCTS ----------------
@app.route("/init_products")
def init_products():
    try:
        conn = connect_db()
        cur = conn.cursor()

        is_sqlite = "sqlite3" in str(type(conn))

        products = [
            ("Milk", 30, "https://cdn-icons-png.flaticon.com/512/1046/1046784.png", 500, False, "A", "1", 1),
            ("Eggs", 60, "https://cdn-icons-png.flaticon.com/512/1046/1046857.png", 200, True, "A", "1", 2),
            ("Rice", 100, "https://cdn-icons-png.flaticon.com/512/3075/3075977.png", 1000, False, "B", "2", 1)
        ]

        for p in products:
            query = """
            INSERT INTO products (name, price, image, weight, fragile, aisle, shelf, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """ if is_sqlite else """
            INSERT INTO products (name, price, image, weight, fragile, aisle, shelf, position)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cur.execute(query, p)

        conn.commit()
        cur.close()
        conn.close()

        return "Products added ✅"

    except Exception as e:
        print("🔥 Init Error:", e)
        return f"Error: {e}"


# ---------------- PLACE ORDER ----------------
@app.route("/place_order", methods=["POST"])
def place_order():
    try:
        items = request.form["items"]

        conn = connect_db()
        cur = conn.cursor()

        is_sqlite = "sqlite3" in str(type(conn))

        query = "INSERT INTO orders (user_email, items, status) VALUES (?, ?, ?)" if is_sqlite else "INSERT INTO orders (user_email, items, status) VALUES (%s, %s, %s)"
        cur.execute(query, (session["user"], items, "pending"))

        conn.commit()

        result = process_order(json.loads(items))

        cur.close()
        conn.close()

        return render_template("result.html", result=result)

    except Exception as e:
        print("🔥 Order Error:", e)
        return f"Order failed: {e}"


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print("🔥 DB Error:", e)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)