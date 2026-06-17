"""
CarbonTrack — Database Seeding Script.
Populates a test user, historical carbon logs, eco-scores, habits, and challenge completions.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone
import random
import uuid

from sqlalchemy import delete, select
from app.database import AsyncSessionLocal
from app.models import (
    User,
    CarbonLog,
    EcoScore,
    Habit,
    HabitLog,
    Challenge,
    ChallengeCompletion,
)
from app.services.auth_service import hash_password


async def seed_db():
    print("Starting database seeding...")
    async with AsyncSessionLocal() as db:
        # 1. Clean up existing test data for the test user to make it re-runnable
        test_email = "dashboard_tester@example.com"
        user_result = await db.execute(select(User).where(User.email == test_email))
        existing_user = user_result.scalar_one_or_none()

        if existing_user:
            print(f"Found existing test user {test_email}. Re-seeding details...")
            # Cascade deletes will handle related logs/scores/etc.
            await db.delete(existing_user)
            await db.commit()

        # Delete any orphan challenges/habits to avoid duplicate key conflicts
        await db.execute(delete(Challenge))
        await db.execute(delete(Habit))
        await db.commit()

        # 2. Create the test user
        hashed_pwd = hash_password("SecurePass123")
        test_user = User(
            email=test_email,
            username="dashboard_tester",
            hashed_password=hashed_pwd,
            full_name="Dashboard Tester",
            xp_total=1450,
            level=6,
            is_active=True,
            is_verified=True,
        )
        db.add(test_user)
        await db.flush()
        user_id = test_user.id
        print(f"Created test user with ID: {user_id}")

        # 3. Create standard habits
        habits_list = [
            Habit(
                slug="public-transit",
                name="Ride Public Transit",
                description="Take the bus, metro, or train instead of driving.",
                icon="bus",
                co2_saved_kg_per_log=5.0,
                xp_reward=15,
                is_active=True,
            ),
            Habit(
                slug="meatless-meals",
                name="Meat-Free Day",
                description="Eat vegetarian or vegan meals all day.",
                icon="utensils",
                co2_saved_kg_per_log=3.5,
                xp_reward=10,
                is_active=True,
            ),
            Habit(
                slug="unplug-standby",
                name="Unplug Idle Devices",
                description="Turn off standby power on electronics.",
                icon="power",
                co2_saved_kg_per_log=1.2,
                xp_reward=5,
                is_active=True,
            ),
            Habit(
                slug="cold-wash",
                name="Cold Water Laundry",
                description="Wash clothes at 30°C or cold water.",
                icon="droplet",
                co2_saved_kg_per_log=0.8,
                xp_reward=8,
                is_active=True,
            ),
        ]
        db.add_all(habits_list)
        await db.flush()
        print("Created standard habits.")

        # 4. Create challenges
        challenges_list = [
            Challenge(
                title="No-Car Week",
                description="Commute without driving a car for 7 days.",
                challenge_type="weekly",
                xp_reward=100,
                co2_saved_estimate_kg=35.0,
                difficulty="hard",
                is_active=True,
            ),
            Challenge(
                title="Plant-Powered Weekend",
                description="Eat vegan for an entire weekend.",
                challenge_type="weekly",
                xp_reward=60,
                co2_saved_estimate_kg=12.0,
                difficulty="medium",
                is_active=True,
            ),
            Challenge(
                title="Eco-Friendly Office",
                description="Reduce office paper and energy usage for a month.",
                challenge_type="monthly",
                xp_reward=150,
                co2_saved_estimate_kg=50.0,
                difficulty="medium",
                is_active=True,
            ),
        ]
        db.add_all(challenges_list)
        await db.flush()
        print("Created active challenges.")

        # 5. Populate Carbon Logs & Eco-Scores over the last 1 year (52 weeks)
        now_dt = datetime.now(timezone.utc)
        print("Generating historical carbon logs and eco-scores...")

        # We generate a log every 7 days
        for i in range(52):
            log_date = now_dt - timedelta(days=7 * i)
            # Create a seasonal/random fluctuation in carbon footprint
            # Winters/summers might use slightly more electricity/heating
            month = log_date.month
            season_mult = 1.2 if month in [12, 1, 2, 6, 7, 8] else 0.9

            car_km = random.uniform(100, 300)
            public_km = random.uniform(20, 100)
            flight_co2 = 250.0 if (i % 12 == 0) else 0.0  # occasional flights

            transport_car = car_km * 0.18  # ~0.18kg CO2 per km
            transport_public = public_km * 0.05
            transport_total = transport_car + transport_public + flight_co2

            electricity_kwh = random.uniform(100, 250) * season_mult
            gas_therms = random.uniform(10, 40) * season_mult
            energy_electricity = electricity_kwh * 0.4
            energy_gas = gas_therms * 5.3
            energy_total = energy_electricity + energy_gas

            diet_type = random.choice(["meat-heavy", "average", "vegetarian", "vegan"])
            food_total = {
                "meat-heavy": 230.0,
                "average": 140.0,
                "vegetarian": 75.0,
                "vegan": 45.0
            }[diet_type]

            shopping_clothing = random.uniform(10, 80)
            shopping_electronics = random.uniform(0, 150) if i % 4 == 0 else 0.0
            shopping_general = random.uniform(20, 70)
            shopping_total = (shopping_clothing + shopping_electronics + shopping_general) * 0.1

            total_monthly_kg = transport_total + energy_total + food_total + shopping_total
            total_annual_kg = total_monthly_kg * 12

            carbon_log = CarbonLog(
                user_id=user_id,
                transport_car=transport_car,
                transport_public=transport_public,
                transport_flights=flight_co2,
                transport_motorcycle=0.0,
                transport_total=transport_total,
                energy_electricity=energy_electricity,
                energy_natural_gas=energy_gas,
                energy_lpg=0.0,
                energy_total=energy_total,
                food_diet_type=diet_type,
                food_total=food_total,
                shopping_clothing=shopping_clothing,
                shopping_electronics=shopping_electronics,
                shopping_general=shopping_general,
                shopping_total=shopping_total,
                total_monthly_kg=total_monthly_kg,
                total_annual_kg=total_annual_kg,
                emission_factors_version="1.0",
                created_at=log_date,
                updated_at=log_date,
            )
            db.add(carbon_log)
            await db.flush()

            # Generate corresponding Eco Score
            # Perfect score (100) minus penalties based on high carbon logs
            base_score = 100
            penalty = int(total_monthly_kg / 10)  # e.g., 500kg -> -50
            score_val = max(10, min(100, base_score - penalty))

            tier = "Footprint Saver"
            if score_val >= 85:
                tier = "Climate Champion"
            elif score_val >= 70:
                tier = "Eco Conscious"

            eco_score = EcoScore(
                user_id=user_id,
                score=score_val,
                tier=tier,
                carbon_log_id=carbon_log.id,
                transport_score=max(10, 100 - int(transport_total / 5)),
                energy_score=max(10, 100 - int(energy_total / 5)),
                food_score=max(10, 100 - int(food_total / 3)),
                shopping_score=max(10, 100 - int(shopping_total / 2)),
                created_at=log_date,
                updated_at=log_date,
            )
            db.add(eco_score)

        # 6. Populate Habit Logs
        print("Generating historical habit logs...")
        # Populate random logs for the last 30 days
        for h in habits_list:
            for day_offset in range(30):
                # 60% chance to log a habit daily
                if random.random() < 0.6:
                    log_date_val = (now_dt - timedelta(days=day_offset)).date()
                    habit_log = HabitLog(
                        user_id=user_id,
                        habit_id=h.id,
                        log_date=log_date_val,
                        notes="Completed as part of seed data",
                        current_streak=random.randint(1, 10),
                        created_at=now_dt - timedelta(days=day_offset),
                        updated_at=now_dt - timedelta(days=day_offset),
                    )
                    db.add(habit_log)

        # 7. Populate Challenge Completions
        print("Generating challenge completions...")
        for c in challenges_list:
            # 70% chance to have completed a challenge in the past
            if random.random() < 0.7:
                comp_offset = random.randint(5, 60)
                comp_date = (now_dt - timedelta(days=comp_offset)).date()
                completion = ChallengeCompletion(
                    user_id=user_id,
                    challenge_id=c.id,
                    completed_at=comp_date,
                    notes="Completed challenge during seed window",
                    created_at=now_dt - timedelta(days=comp_offset),
                    updated_at=now_dt - timedelta(days=comp_offset),
                )
                db.add(completion)

        await db.commit()
        print("Database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed_db())
