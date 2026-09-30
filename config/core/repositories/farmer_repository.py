"""
KisanAI OS
Farmer Repository
Version: 4.0.0
"""

from sqlalchemy import func, or_, select

from config.core.database import SessionLocal
from config.core.models.farmer import Farmer


class FarmerRepository:
    """Farmer Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def insert_farmer(self, farmer: Farmer):
        self.session.merge(farmer)
        self._commit()

    def get_farmer_by_id(self, farmer_id):
        return self.session.get(Farmer, farmer_id)

    def get_farmer_by_mobile(self, mobile):
        statement = select(Farmer).where(Farmer.mobile == mobile)
        return self.session.scalar(statement)

    def get_farmer_by_user_id(self, user_id):
        statement = select(Farmer).where(Farmer.user_id == user_id)
        return self.session.scalar(statement)

    def get_all_farmers(self):
        statement = select(Farmer).order_by(Farmer.farmer_id)
        return self.session.scalars(statement).all()

    def update_farmer(self, farmer: Farmer):
        self.session.merge(farmer)
        self._commit()

    def delete_farmer(self, farmer_id):
        farmer = self.session.get(Farmer, farmer_id)
        if farmer is not None:
            self.session.delete(farmer)
            self._commit()

    def count_farmers(self):
        statement = select(func.count(Farmer.farmer_id))
        return self.session.scalar(statement) or 0

    # ==========================================================
    # Admin-scoped search helpers (Admin Control & Farmer Support
    # module). Purely additive; the legacy APIs above are unchanged.
    # ==========================================================

    def _search_clauses(self, state=None, district=None, block=None,
                        query=None):
        clauses = []
        if state:
            clauses.append(Farmer.state == state)
        if district:
            clauses.append(Farmer.district == district)
        if block:
            clauses.append(Farmer.block == block)
        if query:
            like = f"%{query.strip()}%"
            clauses.append(
                or_(
                    Farmer.name.ilike(like),
                    Farmer.mobile.ilike(like),
                    Farmer.village.ilike(like),
                )
            )
        return clauses

    def search_farmers(self, state=None, district=None, block=None,
                       query=None, page=1, size=20):
        statement = select(Farmer).where(
            *self._search_clauses(state, district, block, query)
        )
        statement = (
            statement.order_by(Farmer.farmer_id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(self.session.scalars(statement))

    def count_search_farmers(self, state=None, district=None, block=None,
                             query=None):
        statement = select(func.count(Farmer.farmer_id)).where(
            *self._search_clauses(state, district, block, query)
        )
        return self.session.scalar(statement) or 0

    def close(self):
        self.session.close()
