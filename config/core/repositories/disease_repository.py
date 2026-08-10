"""
KisanAI OS
Disease Repository
Version: 4.1.0
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.disease import Disease


class DiseaseRepository:
    """Disease Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def insert_disease(self, disease: Disease):
        self.session.merge(disease)
        self._commit()

    def get_disease_by_id(self, disease_id):
        return self.session.get(Disease, disease_id)

    def get_disease_by_crop_and_name(self, crop_id, disease_name):
        statement = select(Disease).where(
            Disease.crop_id == crop_id,
            Disease.disease_name == disease_name,
        )
        return self.session.scalar(statement)

    def get_all_diseases(self):
        statement = select(Disease).order_by(Disease.disease_id)
        return self.session.scalars(statement).all()

    def update_disease(self, disease: Disease):
        self.session.merge(disease)
        self._commit()

    def delete_disease(self, disease_id):
        disease = self.session.get(Disease, disease_id)
        if disease is not None:
            self.session.delete(disease)
            self._commit()

    def count_diseases(self):
        statement = select(func.count(Disease.disease_id))
        return self.session.scalar(statement) or 0

    def close(self):
        self.session.close()
