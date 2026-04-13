from flask import Flask, render_template, request, redirect, session
import os, json
from database import connect_db, create_tables
from robot.main import process_order
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret"

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
    cur.close(); conn.close()

    products = []
    for p in data:
        products.append({
            "id":p[0],
            "name":p[1],
            "price":p[2],
            "img":p[3]
        })

    return render_template("dashboard.html", products=products)

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
            request.form["price"],
            request.form["image"],
            request.form["aisle"],
            request.form["shelf"],
            request.form["position"],
            request.form.get("fragile") == "on",
            request.form["weight"]
        ))

        conn.commit()
        cur.close(); conn.close()

        return redirect("/dashboard")

    return render_template("add_product.html")

# ---------------- CART ----------------
@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id=%s",(id,))
    p = cur.fetchone()
    cur.close(); conn.close()

    cart = session.get("cart", [])

    found = False
    for item in cart:
        if item["id"] == id:
            item["qty"] += 1
            found = True

    if not found:
        cart.append({
            "id":id,
            "name":p[1],
            "price":p[2],
            "image":p[3],
            "fragile":p[7],
            "qty":1
        })

    session["cart"] = cart
    return redirect("/cart")

@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(i["price"]*i["qty"] for i in cart)
    return render_template("cart.html", cart=cart, total=total)

# ---------------- CHECKOUT ----------------
@app.route("/checkout")
def checkout():
    cart = session["cart"]
    total = sum(i["price"]*i["qty"] for i in cart)
    wallet = session["wallet"]

    return render_template("checkout.html", total=total, wallet=wallet)

# ---------------- PLACE ORDER ----------------
@app.route("/place_order")
def place_order():

    cart = session["cart"]
    total = sum(i["price"]*i["qty"] for i in cart)

    if session["wallet"] < total:
        return "❌ Not enough balance"

    session["wallet"] -= total

    result = process_order(cart)

    session["cart"] = []

    return render_template("result.html", result=result)

# ---------------- RUN ----------------
if __name__ == "__main__":
    create_tables()
    app.run(debug=True)