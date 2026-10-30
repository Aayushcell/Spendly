from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, seed_db, create_user, get_user_by_email
import sqlite3
from werkzeug.security import check_password_hash


app = Flask(__name__)
app.secret_key = "dev-secret-key-spendly"


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validation
        if not all([name, email, password, confirm_password]):
            flash("All fields are required")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match")
            return render_template("register.html")

        try:
            create_user(name, email, password)
            flash("Account created successfully! Please sign in.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered")
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            flash("Welcome back!")
            return redirect(url_for("profile"))


        flash("Invalid email or password.")
        return render_template("login.html")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Hardcoded data for UI validation (Step 4)
    user = {
        "name": "Aayush Goel",
        "email": "aayush@example.com",
        "member_since": "October 2023",
        "initials": "AG"
    }
    stats = {
        "total_spent": "₹12,450.00",
        "transaction_count": 42,
        "top_category": "Food & Dining"
    }
    transactions = [
        {"date": "2023-10-28", "description": "Starbucks Coffee", "category": "Food & Dining", "amount": "₹350.00"},
        {"date": "2023-10-27", "description": "Uber Ride", "category": "Transport", "amount": "₹120.00"},
        {"date": "2023-10-25", "description": "Amazon Electronics", "category": "Shopping", "amount": "₹2,100.00"},
        {"date": "2023-10-20", "description": "Netflix Subscription", "category": "Entertainment", "amount": "₹499.00"},
    ]
    categories = [
        {"category": "Food & Dining", "amount": "₹4,200.00", "percentage": 34},
        {"category": "Shopping", "amount": "₹3,100.00", "percentage": 25},
        {"category": "Transport", "amount": "₹1,500.00", "percentage": 12},
        {"category": "Entertainment", "amount": "₹800.00", "percentage": 6},
    ]

    return render_template("profile.html", user=user, stats=stats, transactions=transactions, categories=categories)



@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
