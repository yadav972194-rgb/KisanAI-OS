"""
KisanAI OS
Admin Farmer Service
Version: 1.0.0

Admin Control & Farmer Support module. Farmer directory search, profile
view, farm/crop/soil corrections (recorded as changed fields in the audit
log) and confirmed farmer-record deletion with an affected-count preview.
"""

from config.core.models.farmer import Farmer
from config.core.repositories.contact_repository import ContactRepository
from config.core.repositories.crop_repository import CropRepository
from config.core.repositories.farmer_repository import FarmerRepository
from config.core.repositories.feedback_repository import FeedbackRepository
from config.core.repositories.notification_repository import (
    NotificationRepository,
)
from config.core.repositories.soil_repository import SoilRepository
from config.core.services.audit_service import AuditService


def _clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


class AdminFarmerService:
    """Admin Farmer Service"""

    def __init__(self, session=None):
        self.farmer_repo = FarmerRepository(session)
        self.crop_repo = CropRepository(session)
        self.soil_repo = SoilRepository(session)
        self.feedback_repo = FeedbackRepository(session)
        self.contact_repo = ContactRepository(session)
        self.notice_repo = NotificationRepository(session)
        self.audit = AuditService(session)

    # ==========================================================
    # Directory & profile
    # ==========================================================

    def search_farmers(self, filters):
        page = max(1, int(filters.get("page") or 1))
        size = max(1, min(100, int(filters.get("size") or 20)))

        rows = self.farmer_repo.search_farmers(
            state=filters.get("state") or None,
            district=filters.get("district") or None,
            block=filters.get("block") or None,
            query=filters.get("q") or None,
            page=page,
            size=size,
        )
        total = self.farmer_repo.count_search_farmers(
            state=filters.get("state") or None,
            district=filters.get("district") or None,
            block=filters.get("block") or None,
            query=filters.get("q") or None,
        )
        return {
            "success": True,
            "items": [row.to_dict() for row in rows],
            "total": total,
            "page": page,
            "size": size,
        }

    def get_farmer_profile(self, farmer_id):
        farmer = self.farmer_repo.get_farmer_by_id(farmer_id)
        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        return {
            "success": True,
            "farmer": farmer.to_dict(),
            "soils": [soil.to_dict() for soil in self.soil_repo.get_soils_by_farmer(farmer_id)],
            "contacts": [
                contact.to_dict()
                for contact in self.contact_repo.list_by_farmer(farmer_id)
            ],
            "feedback": [
                row.to_dict()
                for row in self.feedback_repo.list_by_farmer(farmer_id)
            ],
        }

    # ==========================================================
    # Corrections (audited)
    # ==========================================================

    def update_farmer(self, actor_user_id, farmer_id, data):
        farmer = self.farmer_repo.get_farmer_by_id(farmer_id)
        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        mobile = _clean_text(data.get("mobile"))
        if not mobile:
            return {
                "success": False,
                "message": "Mobile number is required",
            }

        mobile_owner = self.farmer_repo.get_farmer_by_mobile(mobile)
        if mobile_owner is not None and mobile_owner.farmer_id != farmer.farmer_id:
            return {
                "success": False,
                "message": "Mobile number already exists",
            }

        changes = {}
        fields = {
            "name": _clean_text(data.get("name")),
            "mobile": mobile,
            "village": _clean_text(data.get("village")),
            "district": _clean_text(data.get("district")),
            "state": _clean_text(data.get("state")),
            "country": _clean_text(data.get("country")) or "India",
        }
        for key, value in fields.items():
            if not value:
                return {
                    "success": False,
                    "message": f"{key} is required",
                }
            old = getattr(farmer, key)
            if old != value:
                changes[key] = [old, value]
                setattr(farmer, key, value)

        block = _clean_text(data.get("block"))
        if farmer.block != block:
            changes["block"] = [farmer.block, block or None]
            farmer.block = block or None

        farm_size = data.get("farm_size")
        if "farm_size" in data and (data["farm_size"] is None or farmer.farm_size != farm_size):
            changes["farm_size"] = [farmer.farm_size, farm_size]
            farmer.farm_size = farm_size

        if changes:
            self.farmer_repo.update_farmer(farmer)
            self.audit.record(
                actor_user_id,
                "farmer.update",
                "farmer",
                farmer.farmer_id,
                details={"name": farmer.name, "changes": changes},
            )

        return {
            "success": True,
            "message": "Farmer profile updated successfully",
            "changed_fields": list(changes.keys()),
        }

    def update_crop(self, actor_user_id, farmer_id, crop_id, data):
        farmer = self.farmer_repo.get_farmer_by_id(farmer_id)
        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        crop = self.crop_repo.get_crop_by_id(crop_id)
        # Ownership scoping: an admin edit may only touch crops that
        # belong to the requested farmer record.
        if crop is None or crop.farmer_id != farmer.farmer_id:
            return {
                "success": False,
                "message": "Crop Not Found",
            }

        crop_name = _clean_text(data.get("crop_name"))
        season = _clean_text(data.get("season"))
        water_requirement = _clean_text(data.get("water_requirement"))
        duration_days = data.get("duration_days")

        if not crop_name or not season or not water_requirement:
            return {
                "success": False,
                "message": "All crop fields are required",
            }

        name_owner = self.crop_repo.get_crop_by_farmer_and_name(
            farmer.farmer_id, crop_name
        )
        if name_owner is not None and name_owner.crop_id != crop_id:
            return {
                "success": False,
                "message": "Crop already added to this farm",
            }

        changes = {}
        if crop.crop_name != crop_name:
            changes["crop_name"] = [crop.crop_name, crop_name]
            crop.crop_name = crop_name
        if crop.season != season:
            changes["season"] = [crop.season, season]
            crop.season = season
        if crop.water_requirement != water_requirement:
            changes["water_requirement"] = [crop.water_requirement, water_requirement]
            crop.water_requirement = water_requirement
        if int(crop.duration_days) != int(duration_days):
            changes["duration_days"] = [crop.duration_days, duration_days]
            crop.duration_days = int(duration_days)

        if changes:
            self.crop_repo.update_crop(crop)
            self.audit.record(
                actor_user_id,
                "crop.update",
                "crop",
                crop.crop_id,
                details={"farmer_id": farmer.farmer_id, "changes": changes},
            )

        return {
            "success": True,
            "message": "Crop updated successfully",
            "changed_fields": list(changes.keys()),
        }

    def update_soil(self, actor_user_id, farmer_id, soil_id, data):
        farmer = self.farmer_repo.get_farmer_by_id(farmer_id)
        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        soil = self.soil_repo.get_soil_by_id(soil_id)
        if soil is None or soil.farmer_id != farmer.farmer_id:
            return {
                "success": False,
                "message": "Soil Not Found",
            }

        changes = {}
        if soil.soil_type != _clean_text(data.get("soil_type")):
            changes["soil_type"] = [soil.soil_type, _clean_text(data.get("soil_type"))]
            soil.soil_type = _clean_text(data.get("soil_type"))
        for field in ("ph", "moisture", "nitrogen", "phosphorus", "potassium"):
            if field in data:
                current = getattr(soil, field)
                if current != data[field]:
                    changes[field] = [current, data[field]]
                    setattr(soil, field, data[field])

        if changes:
            self.soil_repo.update_soil(soil)
            self.audit.record(
                actor_user_id,
                "soil.update",
                "soil",
                soil.soil_id,
                details={"farmer_id": farmer.farmer_id, "changes": changes},
            )

        return {
            "success": True,
            "message": "Soil updated successfully",
            "changed_fields": list(changes.keys()),
        }

    # ==========================================================
    # Delete (super-admin only at the API layer)
    # ==========================================================

    def _affected_counts(self, farmer_id):
        return {
            "crops": self.crop_repo.count_by_farmer(farmer_id),
            "soils": self.soil_repo.count_by_farmer(farmer_id),
            "feedback": self.feedback_repo.count_by_farmer(farmer_id),
            "contacts": self.contact_repo.count_by_farmer(farmer_id),
            "notifications": self.notice_repo.count_by_farmer(farmer_id),
        }

    def delete_preview(self, farmer_id):
        farmer = self.farmer_repo.get_farmer_by_id(farmer_id)
        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        counts = self._affected_counts(farmer_id)
        return {
            "success": True,
            "farmer_id": farmer.farmer_id,
            "name": farmer.name,
            **counts,
        }

    def delete_farmer(self, actor_user_id, farmer_id, confirm=False):
        """Confirmed deletion of a farmer record and its dependent rows."""
        if not confirm:
            return {
                "success": False,
                "message": "Deletion requires confirmation",
            }

        farmer = self.farmer_repo.get_farmer_by_id(farmer_id)
        if farmer is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        counts = self._affected_counts(farmer_id)

        self.crop_repo.delete_all_by_farmer(farmer_id)
        self.soil_repo.delete_all_by_farmer(farmer_id)
        self.feedback_repo.delete_all_by_farmer(farmer_id)
        self.contact_repo.delete_all_by_farmer(farmer_id)
        self.notice_repo.delete_all_by_farmer(farmer_id)
        self.farmer_repo.delete_farmer(farmer_id)

        self.audit.record(
            actor_user_id,
            "farmer.delete",
            "farmer",
            farmer_id,
            details={"name": farmer.name, "affected": counts},
        )

        return {
            "success": True,
            "message": "Farmer record deleted successfully",
            "affected": counts,
        }

    def close(self):
        self.farmer_repo.close()
        self.crop_repo.close()
        self.soil_repo.close()
        self.feedback_repo.close()
        self.contact_repo.close()
        self.notice_repo.close()
        self.audit.close()