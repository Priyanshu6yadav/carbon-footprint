"""Initial schema — all tables for CarbonTrack.

Revision ID: 0001
Revises:
Create Date: 2026-06-18

"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.Text, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("xp_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"])
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    # ── refresh_tokens ─────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text, nullable=False),
        sa.Column("is_revoked", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_hint", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_user_revoked", "refresh_tokens", ["user_id", "is_revoked"])

    # ── audit_logs ─────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_user_created", "audit_logs", ["user_id", "created_at"])
    op.create_index("ix_audit_logs_action_created", "audit_logs", ["action", "created_at"])

    # ── carbon_logs ────────────────────────────────────────────────
    op.create_table(
        "carbon_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transport_car", sa.Float, nullable=False, server_default="0"),
        sa.Column("transport_public", sa.Float, nullable=False, server_default="0"),
        sa.Column("transport_flights", sa.Float, nullable=False, server_default="0"),
        sa.Column("transport_motorcycle", sa.Float, nullable=False, server_default="0"),
        sa.Column("transport_total", sa.Float, nullable=False, server_default="0"),
        sa.Column("energy_electricity", sa.Float, nullable=False, server_default="0"),
        sa.Column("energy_natural_gas", sa.Float, nullable=False, server_default="0"),
        sa.Column("energy_lpg", sa.Float, nullable=False, server_default="0"),
        sa.Column("energy_total", sa.Float, nullable=False, server_default="0"),
        sa.Column("food_diet_type", sa.String(50), nullable=False, server_default="average"),
        sa.Column("food_total", sa.Float, nullable=False, server_default="0"),
        sa.Column("shopping_clothing", sa.Float, nullable=False, server_default="0"),
        sa.Column("shopping_electronics", sa.Float, nullable=False, server_default="0"),
        sa.Column("shopping_general", sa.Float, nullable=False, server_default="0"),
        sa.Column("shopping_total", sa.Float, nullable=False, server_default="0"),
        sa.Column("total_monthly_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("total_annual_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("raw_input", sa.Text, nullable=True),
        sa.Column("emission_factors_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_carbon_logs_user_id", "carbon_logs", ["user_id"])
    op.create_index("ix_carbon_logs_user_created", "carbon_logs", ["user_id", "created_at"])

    # ── eco_scores ─────────────────────────────────────────────────
    op.create_table(
        "eco_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("tier", sa.String(50), nullable=False),
        sa.Column("carbon_log_id", UUID(as_uuid=True), sa.ForeignKey("carbon_logs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("transport_score", sa.Float, server_default="0"),
        sa.Column("energy_score", sa.Float, server_default="0"),
        sa.Column("food_score", sa.Float, server_default="0"),
        sa.Column("shopping_score", sa.Float, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_eco_scores_user_id", "eco_scores", ["user_id"])
    op.create_index("ix_eco_scores_user_created", "eco_scores", ["user_id", "created_at"])

    # ── habits ─────────────────────────────────────────────────────
    op.create_table(
        "habits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default="10"),
        sa.Column("co2_saved_kg_per_log", sa.Float, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_habits_slug", "habits", ["slug"], unique=True)

    # ── habit_logs ─────────────────────────────────────────────────
    op.create_table(
        "habit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("habit_id", UUID(as_uuid=True), sa.ForeignKey("habits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("current_streak", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_habit_logs_user_id", "habit_logs", ["user_id"])
    op.create_index("ix_habit_logs_user_date", "habit_logs", ["user_id", "log_date"])
    op.create_index("ix_habit_logs_user_habit", "habit_logs", ["user_id", "habit_id"])

    # ── challenges ─────────────────────────────────────────────────
    op.create_table(
        "challenges",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("challenge_type", sa.String(50), nullable=False),
        sa.Column("template_slug", sa.String(100), nullable=True),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default="50"),
        sa.Column("co2_saved_estimate_kg", sa.Float, nullable=False, server_default="0"),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── challenge_completions ──────────────────────────────────────
    op.create_table(
        "challenge_completions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("challenge_id", UUID(as_uuid=True), sa.ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_at", sa.Date, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_challenge_completions_user", "challenge_completions", ["user_id", "completed_at"])

    # ── achievements ───────────────────────────────────────────────
    op.create_table(
        "achievements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default="100"),
        sa.Column("trigger_rule", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_achievements_slug", "achievements", ["slug"], unique=True)

    # ── user_achievements ──────────────────────────────────────────
    op.create_table(
        "user_achievements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("achievement_id", UUID(as_uuid=True), sa.ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_achievements_user", "user_achievements", ["user_id", "created_at"])

    # ── ai_recommendations ─────────────────────────────────────────
    op.create_table(
        "ai_recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("carbon_log_id", UUID(as_uuid=True), sa.ForeignKey("carbon_logs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recommendation_text", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("estimated_co2_saving_kg", sa.Float, nullable=True),
        sa.Column("is_ai_generated", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("is_fallback", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("user_rating", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_recommendations_user_id", "ai_recommendations", ["user_id"])
    op.create_index("ix_ai_recommendations_user_created", "ai_recommendations", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("ai_recommendations")
    op.drop_table("user_achievements")
    op.drop_table("achievements")
    op.drop_table("challenge_completions")
    op.drop_table("challenges")
    op.drop_table("habit_logs")
    op.drop_table("habits")
    op.drop_table("eco_scores")
    op.drop_table("carbon_logs")
    op.drop_table("audit_logs")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
