"""
CarbonTrack — models package init.
Import all models here so Alembic can discover them.
"""
from app.models.achievement import Achievement, UserAchievement
from app.models.ai_recommendation import AIRecommendation
from app.models.audit_log import AuditLog
from app.models.carbon_log import CarbonLog
from app.models.challenge import Challenge, ChallengeCompletion
from app.models.eco_score import EcoScore
from app.models.habit import Habit, HabitLog
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = [
    "User",
    "CarbonLog",
    "EcoScore",
    "Habit",
    "HabitLog",
    "Challenge",
    "ChallengeCompletion",
    "Achievement",
    "UserAchievement",
    "AIRecommendation",
    "AuditLog",
    "RefreshToken",
]
