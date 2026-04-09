from flask import Flask, render_template, request, redirect, session, jsonify
import json
from database import connect_db

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
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

    cart = session.get("cart", [])

    # check if item exists
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
        "qty": 1
    })

    session["cart"] = cart

    return redirect("/cart")


# ---------------- CART PAGE ----------------
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