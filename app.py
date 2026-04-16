from flask import Flask, render_template, request, redirect, session
import os
from dotenv import load_dotenv
from database import connect_db, create_tables
from robot.main import process_order

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["email"]
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
            "img": p[3],
            "qty": qty
        })

    return render_template("dashboard.html", products=products)


# ---------------- UPDATE CART (MAIN FEATURE) ----------------
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

    # if not found → add new
    if not found and action == "increase":

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id=%s",(product_id,))
        p = cur.fetchone()
        cur.close()
        conn.close()

        if p:
            cart.append({
                "id": p[0],
                "name": p[1],
                "price": p[2],
                "image": p[3],
                "fragile": p[7],
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

    session["wallet"] -= total

    result = process_order(cart)

    session["cart"] = []

    return render_template("result.html", result=result)


# ---------------- ADD PRODUCT ----------------
@app.route("/add_product", methods=["GET","POST"])
def add_product():
    if request.method == "POST":
        conn = connect_db()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO products (name,price,image,aisle,shelf,position,fragile,weight)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """,(
            request.form["name"],
            int(request.form["price"]),
            request.form["image"],
            request.form["aisle"],
            request.form["shelf"],
            int(request.form["position"]),
            request.form.get("fragile") == "on",
            int(request.form["weight"])
        ))

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_product.html")


# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)