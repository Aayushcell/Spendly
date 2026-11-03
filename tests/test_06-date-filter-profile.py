import pytest
from app import app as flask_app
from database.db import init_db
from datetime import datetime, timedelta
import sqlite3

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': ':memory:',  # Isolated in-memory DB per test
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        init_db()
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """A test client that is already logged in."""
    client.post('/register', data={'name': 'Test User', 'email': 'test@example.com', 'password': 'testpass', 'confirm_password': 'testpass'})
    client.post('/login', data={'email': 'test@example.com', 'password': 'testpass'})
    return client

@pytest.fixture
def seeded_data(app, auth_client):
    """Seeds the in-memory DB with specific expenses for date testing."""
    with app.app_context():
        from database.db import get_db
        db = get_db()
        # Get the logged in user ID
        user = db.execute("SELECT id FROM users WHERE email = ?", ('test@example.com',)).fetchone()
        uid = user['id']

        # Expenses for different periods
        # Using fixed dates to ensure deterministic tests
        expenses = [
            (uid, 100.0, 'Food', '2026-10-01', 'Old Expense'),
            (uid, 200.0, 'Transport', '2026-11-01', 'Start of Month'),
            (uid, 300.0, 'Bills', '2026-11-03', 'Recent Expense'),
        ]
        db.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        db.commit()

class TestDateFilterProfile:

    def test_profile_auth_guard(self, client):
        """Ensure unauthenticated users are redirected to login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_profile_unfiltered_view(self, auth_client, seeded_data):
        """Visiting /profile without params shows all data."""
        response = auth_client.get('/profile')
        assert response.status_code == 200
        # Total should be 100 + 200 + 300 = 600
        assert b'600' in response.data
        assert b'Old Expense' in response.data
        assert b'Recent Expense' in response.data

    def test_profile_valid_date_range(self, auth_client, seeded_data):
        """Filtering with valid date_from and date_to."""
        # Filter for November only
        response = auth_client.get('/profile?date_from=2026-11-01&date_to=2026-11-03')
        assert response.status_code == 200
        # Total should be 200 + 300 = 500
        assert b'500' in response.data
        assert b'Old Expense' not in response.data
        assert b'Recent Expense' in response.data

    def test_profile_range_no_expenses(self, auth_client, seeded_data):
        """A date range with no expenses should show 0 totals."""
        response = auth_client.get('/profile?date_from=2020-01-01&date_to=2020-01-02')
        assert response.status_code == 200
        # Expect ₹0.00 or similar
        assert b'0' in response.data
        # Should not contain any of the seeded descriptions
        assert b'Old Expense' not in response.data

    def test_profile_range_single_expense(self, auth_client, seeded_data):
        """A date range capturing exactly one record."""
        response = auth_client.get('/profile?date_from=2026-10-01&date_to=2026-10-01')
        assert response.status_code == 200
        assert b'100' in response.data
        assert b'Old Expense' in response.data
        assert b'Recent Expense' not in response.data

    @pytest.mark.parametrize("date_from, date_to", [
        ("2026-11-03", "2026-11-01"), # from > to
    ])
    def test_profile_inverted_date_range(self, auth_client, seeded_data, date_from, date_to):
        """date_from > date_to should flash error and fall back to unfiltered."""
        response = auth_client.get(f'/profile?date_from={date_from}&date_to={date_to}')
        assert response.status_code == 200
        assert b'Start date must be before end date.' in response.data
        # Should fall back to unfiltered view (Total 600)
        assert b'600' in response.data

    @pytest.mark.parametrize("date_from, date_to", [
        ("not-a-date", "2026-11-03"),
        ("2026-11-01", "malformed"),
        ("not-a-date", "not-a-date"),
    ])
    def test_profile_malformed_dates(self, auth_client, seeded_data, date_from, date_to):
        """Malformed date strings should silently fall back to unfiltered."""
        response = auth_client.get(f'/profile?date_from={date_from}&date_to={date_to}')
        assert response.status_code == 200
        # Should fall back to unfiltered view (Total 600)
        assert b'600' in response.data

    @pytest.mark.parametrize("date_from, date_to", [
        ("2026-11-01", None),
        (None, "2026-11-03"),
    ])
    def test_profile_missing_one_date_param(self, auth_client, seeded_data, date_from, date_to):
        """Missing one of the two date parameters should fall back to unfiltered."""
        url = '/profile'
        params = {}
        if date_from: params['date_from'] = date_from
        if date_to: params['date_to'] = date_to

        response = auth_client.get(url, query_string=params)
        assert response.status_code == 200
        # Should fall back to unfiltered view (Total 600)
        assert b'600' in response.data

    def test_profile_presets_logic(self, auth_client, seeded_data):
        """Verify that presets render correct URLs and results."""
        response = auth_client.get('/profile')
        assert response.status_code == 200

        # Check if preset labels are present in the HTML
        assert b'This Month' in response.data
        assert b'Last 3 Months' in response.data
        assert b'Last 6 Months' in response.data
        assert b'All Time' in response.data

    def test_profile_all_time_preset(self, auth_client, seeded_data):
        """The 'All Time' preset should pass no query params and show all data."""
        # Simulate clicking "All Time" (which redirects to /profile with no params)
        response = auth_client.get('/profile')
        assert response.status_code == 200
        assert b'600' in response.data
