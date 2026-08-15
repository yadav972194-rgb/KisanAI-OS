"""
KisanAI OS
Farmer Model
Version: 3.0.0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Farmer(Base):
    """Farmer Model"""

    __tablename__ = "farmers"

    farmer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[str] = mapped_column(String(15), unique=True)
    village: Mapped[str] = mapped_column(String(100))
    block: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(
        String(100), default="India", server_default="India"
    )
    farm_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    user: Mapped["User | None"] = relationship(
        back_populates="farms",
    )

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
            "user_id": self.user_id,
            "name": self.name,
            "mobile": self.mobile,
            "village": self.village,
            "block": self.block,
            "district": self.district,
            "state": self.state,
            "country": self.country,
            "farm_size": self.farm_size,
            "created_at": self.created_at,
            "crops": [crop.to_dict() for crop in self.crops],
        }
