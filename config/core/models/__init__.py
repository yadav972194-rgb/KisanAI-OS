"""KisanAI OS - ORM models.

Importing this package registers every model on ``Base.metadata`` so
Alembic autogenerate and metadata introspection see the full schema.
"""

from config.core.models.crop import Crop
from config.core.models.disease import Disease
from config.core.models.farmer import Farmer
from config.core.models.soil import Soil
from config.core.models.user import User
from config.core.models.weather import Weather

__all__ = [
    "Crop",
    "Disease",
    "Farmer",
    "Soil",
    "User",
    "Weather",
]
