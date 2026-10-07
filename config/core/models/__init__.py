"""KisanAI OS - ORM models.

Importing this package registers every model on ``Base.metadata`` so
Alembic autogenerate and metadata introspection see the full schema.
"""

from config.core.models.admin_audit_log import AdminAuditLog
from config.core.models.contact_record import ContactRecord
from config.core.models.crop import Crop
from config.core.models.disease import Disease
from config.core.models.farmer import Farmer
from config.core.models.feedback import Feedback
from config.core.models.notification import Notification
from config.core.models.soil import Soil
from config.core.models.otp import OtpCode
from config.core.models.user import User
from config.core.models.user_session import UserSession
from config.core.models.weather import Weather

__all__ = [
    "AdminAuditLog",
    "ContactRecord",
    "Crop",
    "Disease",
    "Farmer",
    "Feedback",
    "Notification",
    "OtpCode",
    "Soil",
    "User",
    "UserSession",
    "Weather",
]
