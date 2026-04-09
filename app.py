from flask import Flask, render_template, request, redirect, session
import os
from database import connect_db, create_tables
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

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

                if stored_password.startswith("pbkdf2:"):
                    if check_password_hash(stored_password, password):
                        session["user"] = email
                        return redirect("/dashboard")
                else:
                    if stored_password == password:
                        session["user"] = email
                        return redirect("/dashboard")

            error = "Invalid email or password ❌"

        except Exception as e:
            print("Login Error:", e)
            error = "Server error ❌"

    return render_template("login.html", error=error)


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = connect_db()
            cur = conn.cursor()

            is_sqlite = "sqlite3" in str(type(conn))
            query = "SELECT * FROM users WHERE email=?" if is_sqlite else "SELECT * FROM users WHERE email=%s"

            cur.execute(query, (email,))

            if cur.fetchone():
                error = "User already exists ❌"
            else:
                hashed = generate_password_hash(password)

                insert = "INSERT INTO users (email, password) VALUES (?, ?)" if is_sqlite else "INSERT INTO users (email, password) VALUES (%s, %s)"
                cur.execute(insert, (email, hashed))

                conn.commit()
                cur.close()
                conn.close()

                return redirect("/")

            cur.close()
            conn.close()

        except Exception as e:
            print("Signup Error:", e)
            error = "Something went wrong ❌"

    return render_template("signup.html", error=error)


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return f"Welcome {session['user']} 🚀"


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
        print("DB Error:", e)

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)