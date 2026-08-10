"""
KisanAI OS
Soil Repository
Version: 4.0.0
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.soil import Soil


class SoilRepository:
    """Soil Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add_soil(self, soil: Soil):
        self.session.merge(soil)
        self._commit()

    def get_soil_by_id(self, soil_id):
        return self.session.get(Soil, soil_id)

    def get_all_soils(self):
        statement = select(Soil).order_by(Soil.soil_id)
        return self.session.scalars(statement).all()

    def update_soil(self, soil: Soil):
        self.session.merge(soil)
        self._commit()

    def delete_soil(self, soil_id):
        soil = self.session.get(Soil, soil_id)
        if soil is not None:
            self.session.delete(soil)
            self._commit()

    def count_soils(self):
        statement = select(func.count(Soil.soil_id))
        return self.session.scalar(statement) or 0

    def close(self):
        self.session.close()
