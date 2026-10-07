"""
KisanAI OS
Notification Repository
Version: 1.0.0

Admin Control & Farmer Support module.
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.notification import Notification


class NotificationRepository:
    """Notification Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, notification: Notification):
        self.session.add(notification)
        self._commit()
        return notification

    def get_by_id(self, notification_id):
        return self.session.get(Notification, notification_id)

    def list_by_user(self, user_id):
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.notification_id.desc())
        )
        return list(self.session.scalars(statement))

    def list_all(self, category=None, status=None, user_id=None,
                 page=1, size=20):
        statement = select(Notification)
        if category:
            statement = statement.where(Notification.category == category)
        if status:
            statement = statement.where(Notification.status == status)
        if user_id is not None:
            statement = statement.where(Notification.user_id == user_id)
        statement = (
            statement.order_by(Notification.notification_id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(self.session.scalars(statement))

    def count(self, category=None, status=None, user_id=None):
        statement = select(func.count(Notification.notification_id))
        if category:
            statement = statement.where(Notification.category == category)
        if status:
            statement = statement.where(Notification.status == status)
        if user_id is not None:
            statement = statement.where(Notification.user_id == user_id)
        return self.session.scalar(statement) or 0

    def count_by_farmer(self, farmer_id):
        statement = (
            select(func.count(Notification.notification_id))
            .where(Notification.farmer_id == farmer_id)
        )
        return self.session.scalar(statement) or 0

    def update(self, notification: Notification):
        self._commit()
        return notification

    def delete_all_by_farmer(self, farmer_id):
        statement = select(Notification).where(
            Notification.farmer_id == farmer_id
        )
        rows = list(self.session.scalars(statement))
        for row in rows:
            self.session.delete(row)
        if rows:
            self._commit()

    def close(self):
        self.session.close()