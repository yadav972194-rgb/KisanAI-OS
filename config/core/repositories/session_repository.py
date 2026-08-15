"""
KisanAI OS
Session Repository
Version: 1.0.0
"""

from sqlalchemy import select

from config.core.database import SessionLocal
from config.core.models.user_session import UserSession


class SessionRepository:
    """Session Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, session: UserSession):
        self.session.add(session)
        self._commit()

    def get_by_jti(self, jti):
        return self.session.scalar(
            select(UserSession).where(UserSession.jti == jti)
        )

    def revoke(self, session: UserSession, revoked_at: str):
        session.revoked = True
        session.revoked_at = revoked_at
        self._commit()

    def revoke_all_for_user(self, user_id: int):
        for session in list(
            self.session.scalars(
                select(UserSession).where(
                    UserSession.user_id == user_id,
                    UserSession.revoked.is_(False),
                )
            )
        ):
            session.revoked = True
        self._commit()

    def close(self):
        self.session.close()
