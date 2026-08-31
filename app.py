import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_connection
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


# =========================
# HOME PAGE
# =========================

@app.route("/")
def index():
    return render_template("index.html")


# =========================
# USER REGISTRATION
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        conn = get_connection()
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password, phone)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, password, phone)
            )

            conn.commit()

            flash("Registration successful! Please login.")

            return redirect(url_for("login"))

        except Exception:

            flash("Email already exists or an error occurred.")

        finally:

            cursor.close()
            conn.close()

    return render_template("register.html")


# =========================
# USER LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = %s AND password = %s
            """,
            (email, password)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM admins
            WHERE username = %s AND password = %s
            """,
            (username, password)
        )

        admin = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin:

            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]

            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin username or password.")

    return render_template("admin_login.html")


# =========================
# USER DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT complaints.*, categories.name AS category_name
        FROM complaints
        JOIN categories
        ON complaints.category_id = categories.id
        WHERE complaints.user_id = %s
        ORDER BY complaints.created_at DESC
        """,
        (session["user_id"],)
    )

    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        complaints=complaints,
        user_name=session["user_name"]
    )


# =========================
# SUBMIT COMPLAINT
# =========================

@app.route("/submit_complaint", methods=["GET", "POST"])
def submit_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":

        subject = request.form["subject"]
        category_id = request.form["category_id"]
        description = request.form["description"]
        priority = request.form["priority"]

        cursor.execute(
            """
            INSERT INTO complaints
            (user_id, category_id, subject, description, priority)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],
                category_id,
                subject,
                description,
                priority
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Complaint submitted successfully!")

        return redirect(url_for("dashboard"))

    cursor.execute(
        "SELECT * FROM categories ORDER BY name"
    )

    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "submit_complaint.html",
        categories=categories
    )


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            complaints.*,
            users.name AS user_name,
            users.email AS user_email,
            categories.name AS category_name
        FROM complaints
        JOIN users
            ON complaints.user_id = users.id
        JOIN categories
            ON complaints.category_id = categories.id
        ORDER BY complaints.created_at DESC
        """
    )

    complaints = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        complaints=complaints
    )


# =========================
# ADMIN UPDATE COMPLAINT
# =========================

@app.route("/admin/update/<int:complaint_id>", methods=["POST"])
def update_complaint(complaint_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    status = request.form["status"]
    admin_reply = request.form["admin_reply"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE complaints
        SET status = %s,
            admin_reply = %s
        WHERE id = %s
        """,
        (status, admin_reply, complaint_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Complaint updated successfully!")

    return redirect(url_for("admin_dashboard"))


# =========================
# USER LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# =========================
# ADMIN LOGOUT
# =========================

@app.route("/admin/logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect(url_for("index"))


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(debug=True)
