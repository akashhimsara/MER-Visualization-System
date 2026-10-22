"""
Utility script to reset demo integration users back to cold start baseline.
Safe for viva demonstrations: Clears only demo integration test records without touching other data.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from components.personalization.persistence.database import get_session_factory
from components.personalization.persistence.models import (
    PersonalizationInteractionModel,
    PersonalizationLinUCBStateModel,
    PersonalizationPresetStatsModel,
    PersonalizationProcessedFeedbackModel,
    PersonalizationUserStateModel,
)

TARGET_USERS = ["demo-integration-user-a", "demo-integration-user-b"]


def reset_demo_users(user_ids=None):
    users = user_ids or TARGET_USERS
    Session = get_session_factory()
    with Session() as session:
        with session.begin():
            for uid in users:
                session.query(PersonalizationPresetStatsModel).filter_by(user_id=uid).delete()
                session.query(PersonalizationLinUCBStateModel).filter_by(user_id=uid).delete()
                session.query(PersonalizationInteractionModel).filter_by(user_id=uid).delete()
                session.query(PersonalizationProcessedFeedbackModel).filter_by(user_id=uid).delete()
                session.query(PersonalizationUserStateModel).filter_by(user_id=uid).delete()
    print(f"[SUCCESS] Successfully cleared database records for: {users}")
    print("Demo users are now reset to clean baseline (0 learning updates, Cold Start active).")


if __name__ == "__main__":
    reset_demo_users()
