"""
KisanAI OS
User Repository
Version: 1.0.0
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.user import User


class UserRepository:
    """User Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, user: User):
        self.session.add(user)
        self._commit()

    def get_by_username(self, username):
        return self.session.scalar(
            select(User).where(User.username == username)
        )

    def get_by_mobile(self, mobile):
        if not mobile:
            return None
        return self.session.scalar(
            select(User).where(User.mobile == mobile)
        )

    def get_by_id(self, user_id):
        return self.session.get(User, user_id)

    def get_all_users(self):
        statement = select(User).order_by(User.id)
        return list(self.session.scalars(statement))

    def update(self, user: User):
        self._commit()

    def delete(self, user_id):
        """Delete a user account (admin module, confirmation required)."""
        user = self.session.get(User, user_id)
        if user is not None:
            self.session.delete(user)
            self._commit()

    def count_active_super_admins(self):
        """Number of active accounts with the super-admin flag."""
        statement = (
            select(func.count(User.id))
            .where(User.super_admin.is_(True), User.is_active.is_(True))
        )
        return self.session.scalar(statement) or 0

    def count_users(self):
        statement = select(func.count(User.id))
        return self.session.scalar(statement) or 0

    def close(self):
        self.session.close()
