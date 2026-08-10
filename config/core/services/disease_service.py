"""
KisanAI OS
Disease Service
Version: 5.4.0
"""

from config.core.models.disease import Disease
from config.core.repositories.crop_repository import CropRepository
from config.core.repositories.disease_repository import DiseaseRepository


class DiseaseService:
    """Disease Service"""

    def __init__(self, session=None):
        self.repo = DiseaseRepository(session)
        self.crop_repo = CropRepository(session)

    def _resolve_crop_name(self, crop_id, crop_name):
        """Derive crop_name from the linked crop when crop_id is given."""
        if crop_id is None:
            return crop_name, None

        crop = self.crop_repo.get_crop_by_id(crop_id)

        if crop is None:
            return None, "Crop Not Found"

        return crop.crop_name, None

    def _duplicate_exists(self, crop_id, disease_name, exclude_disease_id=None):
        """Linked (crop_id, disease_name) duplicates are rejected.

        Diseases without a crop (crop_id NULL) are not subject to the
        uniqueness rule, matching the database unique constraint where
        NULLs are treated as distinct.
        """
        if crop_id is None:
            return False

        owner = self.repo.get_disease_by_crop_and_name(crop_id, disease_name)

        if owner is None:
            return False

        if exclude_disease_id is not None and owner.disease_id == exclude_disease_id:
            return False

        return True

    def create_disease(self, disease_data):

        crop_id = disease_data.get("crop_id")

        crop_name, error = self._resolve_crop_name(
            crop_id,
            disease_data["crop_name"],
        )

        if error is not None:
            return {
                "success": False,
                "message": error,
            }

        disease_name = disease_data["disease_name"]

        if self._duplicate_exists(crop_id, disease_name):
            return {
                "success": False,
                "message": "Disease already exists",
            }

        disease = Disease(
            disease_id=disease_data.get("disease_id"),
            crop_id=crop_id,
            crop_name=crop_name,
            disease_name=disease_name,
            symptoms=disease_data["symptoms"],
            solution=disease_data["solution"],
            severity=disease_data["severity"],
        )

        self.repo.insert_disease(disease)

        return {
            "success": True,
            "message": "Disease Added Successfully",
        }

    def get_disease(self, disease_id):

        disease = self.repo.get_disease_by_id(disease_id)

        if disease is None:
            return {
                "success": False,
                "message": "Disease Not Found",
            }

        return disease.to_dict()

    def get_all_diseases(self):
        return [
            disease.to_dict()
            for disease in self.repo.get_all_diseases()
        ]

    def update_disease(self, disease_id, disease_data):

        existing = self.repo.get_disease_by_id(disease_id)

        if existing is None:
            return {
                "success": False,
                "message": "Disease Not Found",
            }

        crop_id = disease_data.get("crop_id")

        if crop_id is None:
            crop_id = existing.crop_id

        crop_name, error = self._resolve_crop_name(
            crop_id,
            disease_data["crop_name"],
        )

        if error is not None:
            return {
                "success": False,
                "message": error,
            }

        disease_name = disease_data["disease_name"]

        if self._duplicate_exists(crop_id, disease_name, exclude_disease_id=disease_id):
            return {
                "success": False,
                "message": "Disease already exists",
            }

        disease = Disease(
            disease_id=disease_id,
            crop_id=crop_id,
            crop_name=crop_name,
            disease_name=disease_name,
            symptoms=disease_data["symptoms"],
            solution=disease_data["solution"],
            severity=disease_data["severity"],
        )

        self.repo.update_disease(disease)

        return {
            "success": True,
            "message": "Disease Updated Successfully",
        }

    def delete_disease(self, disease_id):

        existing = self.repo.get_disease_by_id(disease_id)

        if existing is None:
            return {
                "success": False,
                "message": "Disease Not Found",
            }

        self.repo.delete_disease(disease_id)

        return {
            "success": True,
            "message": "Disease Deleted Successfully",
        }

    def count_diseases(self):
        return self.repo.count_diseases()

    def close(self):
        self.repo.close()
        self.crop_repo.close()
