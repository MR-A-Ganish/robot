from flask import Flask, render_template, request, redirect, session
from database import connect_db

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s",
                    (email, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/dashboard")
        else:
            return "❌ Invalid credentials"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["email"]
    password = request.form["password"]

    conn = connect_db()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO users (email, password) VALUES (%s, %s)",
                    (email, password))
        conn.commit()
    except:
        return "User already exists ❌"

    cur.close()
    conn.close()

    return redirect("/login")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")

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

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    p = cur.fetchone()

    cur.close()
    conn.close()

    if not p:
        return "Product not found"

    cart = session.get("cart", [])

    # if exists → increase qty
    for item in cart:
        if item["id"] == p[0]:
            item["qty"] += 1
            session["cart"] = cart
            return redirect("/cart")

    # new item
    cart.append({
        "id": p[0],
        "name": p[1],
        "price": p[2],
        "image": p[3],
        "qty": 1,
        "fragile": p[5]
    })

    session["cart"] = cart

    return redirect("/cart")


# ---------------- CART ----------------
@app.route("/cart")
def cart():
    cart = session.get("cart", [])

    total = sum(item["price"] * item["qty"] for item in cart)
    count = sum(item["qty"] for item in cart)

    return render_template("cart.html", cart=cart, total=total, count=count)


# ---------------- INCREASE ----------------
@app.route("/increase/<int:index>")
def increase(index):
    cart = session.get("cart", [])
    cart[index]["qty"] += 1
    session["cart"] = cart
    return redirect("/cart")


# ---------------- DECREASE ----------------
@app.route("/decrease/<int:index>")
def decrease(index):
    cart = session.get("cart", [])

    if cart[index]["qty"] > 1:
        cart[index]["qty"] -= 1
    else:
        cart.pop(index)

    session["cart"] = cart
    return redirect("/cart")


# ---------------- PAYMENT ----------------
@app.route("/payment", methods=["GET", "POST"])
def payment():
    if "cart" not in session or len(session["cart"]) == 0:
        return redirect("/dashboard")

    if request.method == "POST":
        return redirect("/result")

    return render_template("payment.html")


# ---------------- RESULT (ROBOT OUTPUT) ----------------
@app.route("/result")
def result():
    cart = session.get("cart", [])

    if not cart:
        return redirect("/dashboard")

    # 🤖 ROBOT LOGIC
    output = []
    output.append("🤖 Robot Activated...\n")

    for item in cart:
        output.append(f"➡️ Moving to {item['name']} location")
        output.append(f"🛒 Picking item: {item['name']}")

        if item["fragile"]:
            output.append("🤏 Using SOFT grip (fragile)")
        else:
            output.append("💪 Using STRONG grip")

        output.append("✅ Item picked\n")

    output.append("📦 Packing items...")
    output.append("🚚 Moving to delivery zone")
    output.append("✅ Order ready!")

    session.pop("cart", None)

    return render_template("result.html", output=output)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)