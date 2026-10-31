from database.db import get_db
from datetime import datetime

def get_user_profile(user_id):
    """
    Fetches name, email, and created_at for the given user_id.
    Returns a dictionary with name, email, member_since, and initials.
    """
    db = get_db()
    user = db.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if not user:
        return None

    # Format created_at as "Month YYYY"
    try:
        dt = datetime.strptime(user['created_at'], '%Y-%m-%d %H:%M:%S')
        member_since = dt.strftime('%B %Y')
    except (ValueError, TypeError):
        member_since = "Unknown"

    # Generate initials
    name_parts = user['name'].split()
    if not name_parts:
        initials = "?"
    elif len(name_parts) == 1:
        initials = name_parts[0][0].upper()
    else:
        initials = (name_parts[0][0] + name_parts[-1][0]).upper()

    return {
        "name": user['name'],
        "email": user['email'],
        "member_since": member_since,
        "initials": initials
    }

def get_user_stats(user_id):
    """
    Calculates total_spent, transaction_count, and top_category for the given user_id.
    """
    db = get_db()

    # Total spent and transaction count
    stats = db.execute(
        "SELECT SUM(amount) as total, COUNT(id) as count FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    total_spent_val = stats['total'] if stats['total'] is not None else 0.0
    transaction_count = stats['count'] if stats['count'] is not None else 0

    # Top category
    top_cat_row = db.execute(
        """
        SELECT category FROM expenses
        WHERE user_id = ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    top_category = top_cat_row['category'] if top_cat_row else "—"

    return {
        "total_spent": f"₹{total_spent_val:,.2f}",
        "transaction_count": transaction_count,
        "top_category": top_category
    }


def get_recent_transactions(user_id, limit=5):
    """Fetches the most recent transactions."""
    db = get_db()
    query = """
        SELECT date, description, category, amount
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        LIMIT ?
    """
    rows = db.execute(query, (user_id, limit)).fetchall()

    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": f"₹{row['amount']:.2f}"
        }
        for row in rows
    ]

def get_category_breakdown(user_id):
    """Calculates total spent and percentage per category."""
    db = get_db()

    # 1. Calculate total spend for the user
    total_row = db.execute(
        "SELECT SUM(amount) as total FROM expenses WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    total_spend = total_row['total'] if total_row and total_row['total'] else 0

    if total_spend == 0:
        return []

    # 2. Group expenditures by category and sum the amounts
    rows = db.execute(
        "SELECT category, SUM(amount) as amount FROM expenses WHERE user_id = ? GROUP BY category ORDER BY amount DESC",
        (user_id,)
    ).fetchall()

    breakdown = []
    sum_percentages = 0

    # 3. Calculate percentages
    for row in rows:
        amount = row['amount']
        percentage = round((amount / total_spend) * 100)
        breakdown.append({
            'category': row['category'],
            'amount': amount,
            'percentage': percentage
        })
        sum_percentages += percentage

    # 4. Rounding Rule: Adjust the highest spend category to absorb the remainder
    remainder = 100 - sum_percentages
    if remainder != 0 and breakdown:
        # breakdown is already ordered by amount DESC
        breakdown[0]['percentage'] += remainder

    # 5. Final formatting
    formatted_breakdown = []
    for item in breakdown:
        formatted_breakdown.append({
            'category': item['category'],
            'amount': f"₹{item['amount']:,.2f}",
            'percentage': item['percentage']
        })

    return formatted_breakdown
