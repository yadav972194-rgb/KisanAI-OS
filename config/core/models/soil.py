"""
KisanAI OS
Soil Model
Version: 2.0.0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Soil(Base):
    """Soil Model"""

    __tablename__ = "soils"

    soil_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="SET NULL"),
        nullable=True,
    )
    soil_type: Mapped[str] = mapped_column(String(50))
    ph: Mapped[float] = mapped_column(Float)
    moisture: Mapped[float] = mapped_column(Float)
    nitrogen: Mapped[int] = mapped_column(Integer)
    phosphorus: Mapped[int] = mapped_column(Integer)
    potassium: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    farmer: Mapped[Farmer | None] = relationship(back_populates="soils")

    def to_dict(self):
        return {
            "soil_id": self.soil_id,
            "farmer_id": self.farmer_id,
            "soil_type": self.soil_type,
            "ph": self.ph,
            "moisture": self.moisture,
            "nitrogen": self.nitrogen,
            "phosphorus": self.phosphorus,
            "potassium": self.potassium,
            "created_at": self.created_at,
        }
