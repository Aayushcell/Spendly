from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, seed_db, create_user, get_user_by_email
from database.queries import get_user_profile, get_user_stats, get_recent_transactions, get_category_breakdown
import sqlite3
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta



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
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # 1. Extract and validate date filters
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    def is_valid_date(date_str):
        if not date_str:
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # Validation logic
    valid_from = is_valid_date(date_from)
    valid_to = is_valid_date(date_to)

    if valid_from and valid_to:
        if date_from > date_to:
            flash("Start date must be before end date.")
            date_from = date_to = None
    elif valid_from or valid_to:
        # If only one is provided, we still treat as unfiltered per spec
        # "When both are provided, add BETWEEN".
        # However, for a better UX we usually need both for a range.
        # Spec says: "If either parameter is absent or malformed, the route falls back to 'All Time'"
        date_from = date_to = None

    # 2. Calculate presets for the UI
    today = datetime.now().date()

    # This Month: 1st of current month to today
    this_month_start = today.replace(day=1).strftime("%Y-%m-%d")
    this_month_end = today.strftime("%Y-%m-%d")

    # Last 3 Months: 90 days ago to today
    three_months_start = (today - timedelta(days=90)).strftime("%Y-%m-%d")
    three_months_end = today.strftime("%Y-%m-%d")

    # Last 6 Months: 180 days ago to today
    six_months_start = (today - timedelta(days=180)).strftime("%Y-%m-%d")
    six_months_end = today.strftime("%Y-%m-%d")

    presets = [
        {"label": "This Month", "from": this_month_start, "to": this_month_end},
        {"label": "Last 3 Months", "from": three_months_start, "to": three_months_end},
        {"label": "Last 6 Months", "from": six_months_start, "to": six_months_end},
        {"label": "All Time", "from": None, "to": None},
    ]

    # 3. Fetch data using filters
    user = get_user_profile(user_id)
    stats = get_user_stats(user_id, date_from, date_to)
    transactions = get_recent_transactions(user_id, date_from=date_from, date_to=date_to)
    categories = get_category_breakdown(user_id, date_from, date_to)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        date_from=date_from,
        date_to=date_to,
        presets=presets
    )



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
