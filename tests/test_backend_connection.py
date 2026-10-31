import pytest
from app import app as flask_app
from database.db import init_db, seed_db, get_db
from database.queries import (
    get_user_profile,
    get_user_stats,
    get_recent_transactions,
    get_category_breakdown
)
import sqlite3
import os

@pytest.fixture
def app():
    return flask_app

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Initialize and seed database for tests
    with flask_app.app_context():
        init_db()
        seed_db()
    yield

def test_get_user_profile_valid():
    with flask_app.app_context():
        user = get_user_profile(1)
        assert user is not None
        assert user["name"] == "Demo User"
        assert "2026" in user["member_since"]
        assert user["initials"] == "DU"

def test_get_user_profile_invalid():
    with flask_app.app_context():
        assert get_user_profile(999) is None

def test_get_user_stats_seed():
    with flask_app.app_context():
        stats = get_user_stats(1)
        assert stats["transaction_count"] == 8
        assert stats["top_category"] == "Bills"

def test_get_user_stats_empty():
    with flask_app.app_context():
        db = get_db()
        cursor = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                           ("Empty User", "empty@test.com", "hash"))
        db.commit()
        empty_id = cursor.lastrowid
        stats = get_user_stats(empty_id)
        assert stats["total_spent"] == "₹0.00"
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "—"

def test_get_recent_transactions_seed():
    with flask_app.app_context():
        txs = get_recent_transactions(1)
        assert len(txs) > 0
        assert "₹" in txs[0]["amount"]
        assert txs[0]["date"] == "2026-10-25"

def test_get_category_breakdown_sum():
    with flask_app.app_context():
        breakdown = get_category_breakdown(1)
        total_pct = sum(item["percentage"] for item in breakdown)
        assert total_pct == 100
        assert breakdown[0]["category"] == "Bills"

def test_get_category_breakdown_empty():
    with flask_app.app_context():
        db = get_db()
        cursor = db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                           ("Empty User 2", "empty2@test.com", "hash"))
        db.commit()
        empty_id = cursor.lastrowid
        assert get_category_breakdown(empty_id) == []

def test_profile_route_auth_guard(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.location

def test_profile_route_authenticated(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Demo User" in response.data
    assert response.data.decode('utf-8').count('₹') > 0
