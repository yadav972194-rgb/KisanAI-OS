"""
KisanAI OS
Disease Model
Version: 2.0.0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Disease(Base):
    """Disease Model"""

    __tablename__ = "diseases"
    __table_args__ = (
        UniqueConstraint("crop_id", "disease_name", name="uq_diseases_crop_disease"),
    )

    disease_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    crop_id: Mapped[int | None] = mapped_column(
        ForeignKey("crops.crop_id", ondelete="SET NULL"),
        nullable=True,
    )
    crop_name: Mapped[str] = mapped_column(String(100))
    disease_name: Mapped[str] = mapped_column(String(100))
    symptoms: Mapped[str] = mapped_column(Text)
    solution: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    crop: Mapped[Crop | None] = relationship(back_populates="diseases")

    def to_dict(self):
        return {
            "disease_id": self.disease_id,
            "crop_id": self.crop_id,
            "crop_name": self.crop_name,
            "disease_name": self.disease_name,
            "symptoms": self.symptoms,
            "solution": self.solution,
            "severity": self.severity,
            "created_at": self.created_at,
        }
