"""
KisanAI OS
Crop Repository
Version: 4.1.0
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.crop import Crop


class CropRepository:
    """Crop Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add_crop(self, crop: Crop):
        self.session.merge(crop)
        self._commit()

    def get_crop_by_id(self, crop_id):
        return self.session.get(Crop, crop_id)

    def get_crop_by_name(self, crop_name):
        statement = select(Crop).where(Crop.crop_name == crop_name)
        return self.session.scalar(statement)

    def get_all_crops(self):
        statement = select(Crop).order_by(Crop.crop_id)
        return self.session.scalars(statement).all()

    def get_crops_by_farmer(self, farmer_id):
        statement = (
            select(Crop)
            .where(Crop.farmer_id == farmer_id)
            .order_by(Crop.crop_id)
        )
        return self.session.scalars(statement).all()

    def update_crop(self, crop: Crop):
        self.session.merge(crop)
        self._commit()

    def delete_crop(self, crop_id):
        crop = self.session.get(Crop, crop_id)
        if crop is not None:
            self.session.delete(crop)
            self._commit()

    def count_crops(self):
        statement = select(func.count(Crop.crop_id))
        return self.session.scalar(statement) or 0

    def close(self):
        self.session.close()
