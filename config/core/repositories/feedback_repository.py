"""
KisanAI OS
Feedback Repository
Version: 1.0.0

Admin Control & Farmer Support module.
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.feedback import Feedback


class FeedbackRepository:
    """Feedback Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, feedback: Feedback):
        self.session.add(feedback)
        self._commit()
        return feedback

    def get_by_id(self, feedback_id):
        return self.session.get(Feedback, feedback_id)

    def list_by_farmer(self, farmer_id):
        statement = (
            select(Feedback)
            .where(Feedback.farmer_id == farmer_id)
            .order_by(Feedback.feedback_id.desc())
        )
        return list(self.session.scalars(statement))

    def list_by_user(self, user_id, page=1, size=20):
        statement = (
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .order_by(Feedback.feedback_id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(self.session.scalars(statement))

    def list_all(self, status=None, priority=None, page=1, size=20):
        statement = select(Feedback)
        if status:
            statement = statement.where(Feedback.status == status)
        if priority:
            statement = statement.where(Feedback.priority == priority)
        statement = (
            statement.order_by(Feedback.feedback_id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(self.session.scalars(statement))

    def count(self, status=None, priority=None):
        statement = select(func.count(Feedback.feedback_id))
        if status:
            statement = statement.where(Feedback.status == status)
        if priority:
            statement = statement.where(Feedback.priority == priority)
        return self.session.scalar(statement) or 0

    def count_by_farmer(self, farmer_id):
        statement = (
            select(func.count(Feedback.feedback_id))
            .where(Feedback.farmer_id == farmer_id)
        )
        return self.session.scalar(statement) or 0

    def count_by_user(self, user_id):
        statement = (
            select(func.count(Feedback.feedback_id))
            .where(Feedback.user_id == user_id)
        )
        return self.session.scalar(statement) or 0

    def update(self, feedback: Feedback):
        self._commit()
        return feedback

    def delete(self, feedback_id):
        feedback = self.session.get(Feedback, feedback_id)
        if feedback is not None:
            self.session.delete(feedback)
            self._commit()

    def delete_all_by_farmer(self, farmer_id):
        feedback_rows = self.list_by_farmer(farmer_id)
        for row in feedback_rows:
            self.session.delete(row)
        if feedback_rows:
            self._commit()

    def close(self):
        self.session.close()