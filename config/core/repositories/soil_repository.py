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

    def get_soil_by_id_for_farmer(self, farmer_id, soil_id):
        """Ownership-scoped read: a soil reading is only visible inside the
        farm that owns it."""
        statement = select(Soil).where(
            Soil.farmer_id == farmer_id,
            Soil.soil_id == soil_id,
        )
        return self.session.scalar(statement)

    def get_soils_by_farmer(self, farmer_id):
        """Admin-scoped helper: soils belonging to a farmer record."""
        statement = (
            select(Soil)
            .where(Soil.farmer_id == farmer_id)
            .order_by(Soil.soil_id)
        )
        return list(self.session.scalars(statement))

    def count_by_farmer(self, farmer_id):
        """Admin-scoped helper: soil count for a farmer record."""
        statement = (
            select(func.count(Soil.soil_id))
            .where(Soil.farmer_id == farmer_id)
        )
        return self.session.scalar(statement) or 0

    def delete_all_by_farmer(self, farmer_id):
        """Admin-scoped helper: remove every soil owned by a farmer
        (used during confirmed farmer-record deletion)."""
        soils = self.get_soils_by_farmer(farmer_id)
        for soil in soils:
            self.session.delete(soil)
        if soils:
            self._commit()

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
