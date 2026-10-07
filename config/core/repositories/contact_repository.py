"""
KisanAI OS
Contact Record Repository
Version: 1.0.0

Admin Control & Farmer Support module.
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.contact_record import ContactRecord


class ContactRepository:
    """Contact Record Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, contact: ContactRecord):
        self.session.add(contact)
        self._commit()
        return contact

    def get_by_id(self, contact_id):
        return self.session.get(ContactRecord, contact_id)

    def list_by_farmer(self, farmer_id):
        statement = (
            select(ContactRecord)
            .where(ContactRecord.farmer_id == farmer_id)
            .order_by(ContactRecord.contact_id.desc())
        )
        return list(self.session.scalars(statement))

    def count_by_farmer(self, farmer_id):
        statement = (
            select(func.count(ContactRecord.contact_id))
            .where(ContactRecord.farmer_id == farmer_id)
        )
        return self.session.scalar(statement) or 0

    def delete_all_by_farmer(self, farmer_id):
        contacts = self.list_by_farmer(farmer_id)
        for contact in contacts:
            self.session.delete(contact)
        if contacts:
            self._commit()

    def close(self):
        self.session.close()