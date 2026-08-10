"""
KisanAI OS
Farmer Repository
Version: 4.0.0
"""

from sqlalchemy import func, select

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

    def close(self):
        self.session.close()
