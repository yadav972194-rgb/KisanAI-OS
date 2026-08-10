"""
KisanAI OS
Farmer Model
Version: 3.0.0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Farmer(Base):
    """Farmer Model"""

    __tablename__ = "farmers"

    farmer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), unique=True)
    village: Mapped[str] = mapped_column(String(100))
    district: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    soils: Mapped[list[Soil]] = relationship(
        back_populates="farmer",
        cascade="all, delete-orphan",
    )

    crops: Mapped[list[Crop]] = relationship(
        back_populates="farmer",
        passive_deletes=True,
    )

    def to_dict(self):
        return {
            "farmer_id": self.farmer_id,
            "name": self.name,
            "mobile": self.mobile,
            "village": self.village,
            "district": self.district,
            "state": self.state,
            "created_at": self.created_at,
            "crops": [crop.to_dict() for crop in self.crops],
        }
