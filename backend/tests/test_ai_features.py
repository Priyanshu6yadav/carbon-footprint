"""
CarbonTrack — AI Features integration tests.
Tests the challenge generator daily limit and chatbot boundaries.
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_challenges_generation_and_limit():
    uid = uuid.uuid4().hex[:8]
    email = f"ai_tester_{uid}@example.com"
    username = f"aitester_{uid}"
    password = "SecurePass123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Register test user
        reg_resp = await client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "AI Tester",
        })
        assert reg_resp.status_code == 201
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. First challenges generation — should succeed (returns 201)
        gen_resp = await client.post("/api/challenges/generate", headers=headers)
        assert gen_resp.status_code == 201
        challenges = gen_resp.json()
        assert len(challenges) >= 1
        assert len(challenges) <= 3
        
        # Verify fields
        challenge = challenges[0]
        assert "id" in challenge
        assert "xp_reward" in challenge
        assert "co2_saved_estimate_kg" in challenge
        assert "template_slug" in challenge
        assert challenge["template_slug"] is not None

        # 3. Second challenges generation on the same day — should block with 429
        gen_resp_2 = await client.post("/api/challenges/generate", headers=headers)
        assert gen_resp_2.status_code == 429
        assert "already generated" in gen_resp_2.json()["detail"].lower()

        # 4. Complete a challenge and verify XP rewards match deterministic rule
        challenge_id = challenge["id"]
        expected_xp = challenge["xp_reward"]
        
        # Check initial user details
        me_resp = await client.get("/api/auth/me", headers=headers)
        initial_xp = me_resp.json()["xp_total"]

        comp_resp = await client.post(
            f"/api/challenges/{challenge_id}/complete",
            headers=headers,
            json={
                "challenge_id": challenge_id,
                "notes": "Finished E2E test challenge"
            }
        )
        assert comp_resp.status_code == 201
        
        # Check updated user details
        me_resp_updated = await client.get("/api/auth/me", headers=headers)
        updated_xp = me_resp_updated.json()["xp_total"]
        assert updated_xp == initial_xp + expected_xp


@pytest.mark.asyncio
async def test_sustainability_chatbot_boundaries():
    uid = uuid.uuid4().hex[:8]
    email = f"chat_tester_{uid}@example.com"
    username = f"chattester_{uid}"
    password = "SecurePass123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register test user
        reg_resp = await client.post("/api/auth/register", json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Chat Tester",
        })
        token = reg_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Ask a valid sustainability question
        chat_resp = await client.post(
            "/api/chat/sustainability",
            headers=headers,
            json={
                "message": "What is a carbon footprint and why does it matter?"
            }
        )
        assert chat_resp.status_code == 200
        reply = chat_resp.json()["reply"]
        assert len(reply) > 10

        # 2. Ask an off-topic legal/financial advice query (should refuse and redirect)
        chat_resp_offtopic = await client.post(
            "/api/chat/sustainability",
            headers=headers,
            json={
                "message": "Can you give me legal advice on how to start a business?"
            }
        )
        assert chat_resp_offtopic.status_code == 200
        reply_offtopic = chat_resp_offtopic.json()["reply"]
        
        # Verify refusal/redirect keywords
        refusal_keywords = {"refuse", "cannot", "only", "legal", "professional", "sustainability"}
        assert any(kw in reply_offtopic.lower() for kw in refusal_keywords)
