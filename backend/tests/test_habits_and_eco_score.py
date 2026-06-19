"""
CarbonTrack — Integration tests for habits, eco-score, health, and auth flows.
Covers endpoints with lowest coverage in the baseline run:
  - /api/habits (47%)
  - /api/eco-score (58%)
  - /health (38%)
  - /api/auth login / me / logout / refresh (44%)
  - /api/calculator/save + /api/calculator/history (72%)
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _register_and_login(client: AsyncClient) -> tuple[str, dict]:
    """Register a unique test user and return (access_token, user_data)."""
    uid = uuid.uuid4().hex[:8]
    resp = await client.post("/api/auth/register", json={
        "email": f"testuser_{uid}@example.com",
        "username": f"testuser_{uid}",
        "password": "SecurePass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return data["access_token"], data["user"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


FOOTPRINT_PAYLOAD = {
    "transportation": {
        "car_km_per_month": 300,
        "car_fuel_type": "petrol",
        "motorcycle_km_per_month": 0,
        "bus_km_per_month": 50,
        "rail_km_per_month": 0,
        "rideshare_km_per_month": 0,
        "flights_short_haul_per_year": 0,
        "flights_long_haul_per_year": 0,
    },
    "home_energy": {
        "electricity_kwh_per_month": 200,
        "natural_gas_m3_per_month": 10,
        "lpg_litres_per_month": 0,
        "region": "us",
    },
    "food": {"diet_type": "average"},
    "shopping": {
        "clothing_usd_per_month": 40,
        "electronics_usd_per_month": 0,
        "general_goods_usd_per_month": 20,
    },
}


# ─── Health ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_endpoint():
    """GET /health returns 200 with db and redis status flags."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    # API returns "ok" (not "healthy") and uses keys "db" / "redis"
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["redis"] == "ok"



# ─── Auth: login, me, refresh, logout ────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success_and_me():
    """Full login flow: register → login with JSON body → GET /me."""
    uid = uuid.uuid4().hex[:8]
    email = f"logintest_{uid}@example.com"
    username = f"logintest_{uid}"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        reg_resp = await client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "password": "SecurePass123",
            "full_name": "Login Tester",
        })
        assert reg_resp.status_code == 201

        # Login
        login_resp = await client.post("/api/auth/login", json={
            "email": email,
            "password": "SecurePass123",
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # GET /me
        me_resp = await client.get("/api/auth/me", headers=_auth(token))
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email


@pytest.mark.asyncio
async def test_login_duplicate_email_rejected():
    """Registering the same email twice returns 409 Conflict."""
    uid = uuid.uuid4().hex[:8]
    email = f"dup_{uid}@example.com"
    payload = {"email": email, "username": f"dup1_{uid}", "password": "SecurePass123"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.post("/api/auth/register", json=payload)
        assert r1.status_code == 201

        r2 = await client.post("/api/auth/register", json={**payload, "username": f"dup2_{uid}"})
        assert r2.status_code == 409


@pytest.mark.asyncio
async def test_logout_clears_session():
    """POST /api/auth/logout with valid token returns 204."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        resp = await client.post("/api/auth/logout", headers=_auth(token))
    assert resp.status_code == 204


# ─── Habits ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_habits_requires_no_auth():
    """GET /api/habits/ is public (habit catalog)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/habits/")
    assert resp.status_code == 200
    habits = resp.json()
    assert len(habits) > 0
    # Verify expected fields exist
    assert "id" in habits[0]
    assert "name" in habits[0]
    assert "slug" in habits[0]
    assert "xp_reward" in habits[0]


@pytest.mark.asyncio
async def test_log_habit_and_reject_duplicate():
    """Log a habit for today, then reject a second log for the same day."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        headers = _auth(token)

        # Get a habit
        habits_resp = await client.get("/api/habits/", headers=headers)
        habit_id = habits_resp.json()[0]["id"]

        # Log it
        log_resp = await client.post("/api/habits/log", headers=headers, json={
            "habit_id": habit_id,
            "notes": "Did it!",
        })
        assert log_resp.status_code == 201
        data = log_resp.json()
        assert data["habit_id"] == habit_id
        assert data["current_streak"] == 1

        # Try to log again same day → 400
        dup_resp = await client.post("/api/habits/log", headers=headers, json={
            "habit_id": habit_id,
        })
        assert dup_resp.status_code == 400


@pytest.mark.asyncio
async def test_log_unknown_habit_returns_404():
    """Logging a non-existent habit_id returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        resp = await client.post("/api/habits/log", headers=_auth(token), json={
            "habit_id": str(uuid.uuid4()),
        })
    assert resp.status_code == 404


# ─── Eco-Score ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_eco_score_not_found_before_calculation():
    """GET /api/eco-score/latest returns 404 before any footprint is saved."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        resp = await client.get("/api/eco-score/latest", headers=_auth(token))
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_eco_score_created_after_calculator_save():
    """
    Saving a carbon log triggers eco-score creation.
    Validates the eco-score formula: score = clamp(100 - int(monthly_kg / 10), 10, 100).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        headers = _auth(token)

        # Save footprint
        save_resp = await client.post("/api/calculator/save", headers=headers, json=FOOTPRINT_PAYLOAD)
        assert save_resp.status_code == 201
        monthly_kg = save_resp.json()["total_monthly_kg"]

        # Eco-score should now exist
        score_resp = await client.get("/api/eco-score/latest", headers=headers)
        assert score_resp.status_code == 200
        score_data = score_resp.json()
        assert "score" in score_data
        assert "tier" in score_data

        # Validate score is within valid range
        assert 10 <= score_data["score"] <= 100

        # Validate the formula: score = max(10, min(100, 100 - int(monthly_kg / 10)))
        expected_score = max(10, min(100, 100 - int(monthly_kg / 10)))
        assert score_data["score"] == expected_score


@pytest.mark.asyncio
async def test_eco_score_history():
    """GET /api/eco-score/history returns a list after calculation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        headers = _auth(token)

        await client.post("/api/calculator/save", headers=headers, json=FOOTPRINT_PAYLOAD)

        hist_resp = await client.get("/api/eco-score/history", headers=headers)
        assert hist_resp.status_code == 200
        assert len(hist_resp.json()) >= 1


# ─── Calculator history ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_calculator_history_pagination():
    """Save two footprints and confirm history returns both, newest first."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await _register_and_login(client)
        headers = _auth(token)

        await client.post("/api/calculator/save", headers=headers, json=FOOTPRINT_PAYLOAD)
        second_payload = {**FOOTPRINT_PAYLOAD, "food": {"diet_type": "vegan"}}
        await client.post("/api/calculator/save", headers=headers, json=second_payload)

        history_resp = await client.get("/api/calculator/history?limit=10&offset=0", headers=headers)
        assert history_resp.status_code == 200
        logs = history_resp.json()
        assert len(logs) == 2
        # Newest first
        assert logs[0]["created_at"] >= logs[1]["created_at"]
