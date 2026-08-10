"""
KisanAI OS
Crop Model
Version: 3.0.0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Crop(Base):
    """Crop Model"""

    __tablename__ = "crops"
    __table_args__ = (
        UniqueConstraint("crop_name", name="uq_crops_crop_name"),
    )

    crop_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="SET NULL"),
        nullable=True,
    )
    crop_name: Mapped[str] = mapped_column(String(100))
    season: Mapped[str] = mapped_column(String(20))
    duration_days: Mapped[int]
    water_requirement: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    farmer: Mapped[Farmer | None] = relationship(back_populates="crops")

    diseases: Mapped[list[Disease]] = relationship(
        back_populates="crop",
        passive_deletes=True,
    )

    def to_dict(self):
        return {
            "crop_id": self.crop_id,
            "farmer_id": self.farmer_id,
            "crop_name": self.crop_name,
            "season": self.season,
            "duration_days": self.duration_days,
            "water_requirement": self.water_requirement,
            "created_at": self.created_at,
        }
