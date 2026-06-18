"""seed_habit_catalog

Revision ID: 7cd2f28508a9
Revises: ce7e2e7b4542
Create Date: 2026-06-18 10:03:41.155476

"""
from typing import Sequence, Union

import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cd2f28508a9'
down_revision: Union[str, None] = 'ce7e2e7b4542'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get metadata from the habits table
    habits_table = sa.table(
        'habits',
        sa.column('id', sa.UUID),
        sa.column('slug', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
        sa.column('icon', sa.String),
        sa.column('co2_saved_kg_per_log', sa.Float),
        sa.column('xp_reward', sa.Integer),
        sa.column('is_active', sa.Boolean),
    )

    op.bulk_insert(
        habits_table,
        [
            {
                "id": str(uuid.uuid4()),
                "slug": "public-transit",
                "name": "Ride Public Transit",
                "description": "Take the bus, metro, or train instead of driving.",
                "icon": "bus",
                "co2_saved_kg_per_log": 5.0,
                "xp_reward": 15,
                "is_active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "slug": "meatless-meals",
                "name": "Meat-Free Day",
                "description": "Eat vegetarian or vegan meals all day.",
                "icon": "utensils",
                "co2_saved_kg_per_log": 3.5,
                "xp_reward": 10,
                "is_active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "slug": "unplug-standby",
                "name": "Unplug Idle Devices",
                "description": "Turn off standby power on electronics.",
                "icon": "power",
                "co2_saved_kg_per_log": 1.2,
                "xp_reward": 5,
                "is_active": True,
            },
            {
                "id": str(uuid.uuid4()),
                "slug": "cold-wash",
                "name": "Cold Water Laundry",
                "description": "Wash clothes at 30°C or cold water.",
                "icon": "droplet",
                "co2_saved_kg_per_log": 0.8,
                "xp_reward": 8,
                "is_active": True,
            },
        ]
    )


def downgrade() -> None:
    op.execute("DELETE FROM habits WHERE slug IN ('public-transit', 'meatless-meals', 'unplug-standby', 'cold-wash')")
