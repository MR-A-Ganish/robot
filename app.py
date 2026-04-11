from flask import Flask, render_template, request, redirect, session, jsonify
import json, os, razorpay
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
from robot.main import process_order

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback")

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    error=None
    form="login"

    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]

        conn=connect_db()
        cur=conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=%s",(email,))
        user=cur.fetchone()

        cur.close(); conn.close()

        if user and check_password_hash(user[2],password):
            session["user"]=email
            session["cart"]=[]
            return redirect("/dashboard")
        else:
            error="Invalid login ❌"

    return render_template("login.html",error=error,form=form)

# ---------------- SIGNUP ----------------
@app.route("/signup",methods=["POST"])
def signup():
    email=request.form["email"]
    password=generate_password_hash(request.form["password"])

    conn=connect_db()
    cur=conn.cursor()

    cur.execute("INSERT INTO users (email,password) VALUES (%s,%s)",(email,password))
    conn.commit()

    cur.close(); conn.close()
    return redirect("/")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn=connect_db()
    cur=conn.cursor()
    cur.execute("SELECT * FROM products")
    data=cur.fetchall()
    cur.close(); conn.close()

    products=[]
    for p in data:
        products.append({
            "id":p[0],
            "name":p[1],
            "price":p[2],
            "img":p[3]
        })

    return render_template("dashboard.html",products=products)

# ---------------- ADD TO CART ----------------
@app.route("/add_to_cart/<int:id>")
def add_to_cart(id):
    conn=connect_db()
    cur=conn.cursor()

    cur.execute("SELECT * FROM products WHERE id=%s",(id,))
    p=cur.fetchone()

    cart=session.get("cart",[])
    found=False

    for item in cart:
        if item["id"]==p[0]:
            item["qty"]+=1
            found=True

    if not found:
        cart.append({
            "id":p[0],
            "name":p[1],
            "price":p[2],
            "image":p[3],
            "qty":1
        })

    session["cart"]=cart
    return redirect("/cart")

# ---------------- CART ----------------
@app.route("/cart")
def cart():
    cart=session.get("cart",[])
    total=sum(i["price"]*i["qty"] for i in cart)
    return render_template("cart.html",cart=cart,total=total)

# ---------------- INCREASE / DECREASE ----------------
@app.route("/increase/<int:i>")
def inc(i):
    cart=session["cart"]
    cart[i]["qty"]+=1
    session["cart"]=cart
    return redirect("/cart")

@app.route("/decrease/<int:i>")
def dec(i):
    cart=session["cart"]
    if cart[i]["qty"]>1:
        cart[i]["qty"]-=1
    else:
        cart.pop(i)
    session["cart"]=cart
    return redirect("/cart")

# ---------------- PAYMENT ----------------
@app.route("/payment")
def payment():
    total=sum(i["price"]*i["qty"] for i in session["cart"])
    return render_template("payment.html",amount=total)

# ---------------- PAYMENT SUCCESS ----------------
@app.route("/payment_success")
def success():
    items=session["cart"]

    conn=connect_db()
    cur=conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_email,items,status) VALUES (%s,%s,%s) RETURNING id",
        (session["user"],json.dumps(items),"processing")
    )

    order_id=cur.fetchone()[0]

    result=process_order(items)

    cur.execute("UPDATE orders SET status=%s WHERE id=%s",("completed",order_id))
    conn.commit()

    cur.close(); conn.close()

    session["cart"]=[]

    return render_template("result.html",result=result)

# ---------------- ORDER HISTORY ----------------
@app.route("/orders")
def orders():
    conn=connect_db()
    cur=conn.cursor()

    cur.execute("SELECT * FROM orders WHERE user_email=%s",(session["user"],))
    data=cur.fetchall()

    cur.close(); conn.close()

    return render_template("orders.html",orders=data)

# ---------------- ADMIN ----------------
@app.route("/admin",methods=["GET","POST"])
def admin():
    if request.method=="POST":
        name=request.form["name"]
        price=request.form["price"]
        img=request.form["img"]

        conn=connect_db()
        cur=conn.cursor()

        cur.execute(
            "INSERT INTO products (name,price,image) VALUES (%s,%s,%s)",
            (name,price,img)
        )
        conn.commit()
        cur.close(); conn.close()

    return render_template("admin.html")

# ---------------- RUN ----------------
if __name__=="__main__":
    create_tables()
    app.run(debug=True)