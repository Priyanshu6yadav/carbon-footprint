"""
CarbonTrack — Analytics & Reporting Integration Tests.
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_analytics_flow():
    uid = uuid.uuid4().hex[:8]
    email = f"analytics_tester_{uid}@example.com"
    username = f"analytester_{uid}"
    password = "SecurePass123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register test user
        reg_resp = await client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Analytics Tester",
        })
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get active habits
        habits_resp = await client.get("/api/habits/", headers=headers)
        assert habits_resp.status_code == 200
        habits = habits_resp.json()
        assert len(habits) > 0
        habit_id = habits[0]["id"]

        # 3. Get active challenges (generate them first to ensure some exist)
        gen_resp = await client.post("/api/challenges/generate", headers=headers)
        assert gen_resp.status_code == 201

        challenges_resp = await client.get("/api/challenges/", headers=headers)
        assert challenges_resp.status_code == 200
        challenges = challenges_resp.json()
        assert len(challenges) > 0
        challenge_id = challenges[0]["id"]

        # 4. Save carbon footprint calculation
        calc_resp = await client.post(
            "/api/calculator/save",
            headers=headers,
            json={
                "transportation": {
                    "car_km_per_month": 500,
                    "car_fuel_type": "petrol",
                    "motorcycle_km_per_month": 0,
                    "bus_km_per_month": 100,
                    "rail_km_per_month": 0,
                    "rideshare_km_per_month": 0,
                    "flights_short_haul_per_year": 0,
                    "flights_long_haul_per_year": 0
                },
                "home_energy": {
                    "electricity_kwh_per_month": 150,
                    "natural_gas_m3_per_month": 20,
                    "lpg_litres_per_month": 0,
                    "region": "us"
                },
                "food": {
                    "diet_type": "average"
                },
                "shopping": {
                    "clothing_usd_per_month": 50,
                    "electronics_usd_per_month": 0,
                    "general_goods_usd_per_month": 50
                }
            }
        )
        assert calc_resp.status_code == 201

        # 5. Log habit completion
        habit_log_resp = await client.post(
            "/api/habits/log",
            headers=headers,
            json={
                "habit_id": habit_id,
                "notes": "Did this today!"
            }
        )
        assert habit_log_resp.status_code == 201

        # 6. Complete challenge
        challenge_comp_resp = await client.post(
            f"/api/challenges/{challenge_id}/complete",
            headers=headers,
            json={
                "challenge_id": challenge_id,
                "notes": "Finished!"
            }
        )
        assert challenge_comp_resp.status_code == 201

        # 7. Test Carbon Trend endpoint
        trend_resp = await client.get("/api/analytics/carbon-trend?range=month", headers=headers)
        assert trend_resp.status_code == 200
        trend_data = trend_resp.json()
        assert len(trend_data) > 0
        assert trend_data[0]["total"] > 0

        # 8. Test Category Breakdown endpoint
        breakdown_resp = await client.get("/api/analytics/category-breakdown?range=month", headers=headers)
        assert breakdown_resp.status_code == 200
        breakdown_data = breakdown_resp.json()
        assert breakdown_data["transport"] > 0
        assert breakdown_data["energy"] > 0
        assert breakdown_data["food"] > 0

        # 9. Test Habit Completion rates endpoint
        habit_rates_resp = await client.get("/api/analytics/habit-completion?range=month", headers=headers)
        assert habit_rates_resp.status_code == 200
        habit_rates_data = habit_rates_resp.json()
        assert len(habit_rates_data) > 0
        # Check that the logged habit has a non-zero completion rate
        logged_habit = next(h for h in habit_rates_data if h["id"] == habit_id)
        assert logged_habit["logged_days"] == 1
        assert logged_habit["completion_rate"] > 0

        # 10. Test Eco-Score Trend endpoint
        eco_trend_resp = await client.get("/api/analytics/eco-score-trend?range=month", headers=headers)
        assert eco_trend_resp.status_code == 200
        eco_trend_data = eco_trend_resp.json()
        assert len(eco_trend_data) > 0
        assert eco_trend_data[0]["score"] > 0

        # 11. Test PDF Sustainability Report endpoint
        pdf_resp = await client.get("/api/analytics/report/pdf?range=month", headers=headers)
        assert pdf_resp.status_code == 200
        assert pdf_resp.headers["content-type"] == "application/pdf"
        assert len(pdf_resp.content) > 1000  # valid PDF should be multi-KB
