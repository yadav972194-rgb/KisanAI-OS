"""
KisanAI OS
Project Constants
"""

# Application
APP_AUTHOR = "Pradeep Yadav"
COUNTRY = "India"
CURRENCY = "INR"

# Languages
LANG_HINDI = "hi"
LANG_ENGLISH = "en"

# User Roles
ROLE_ADMIN = "admin"
ROLE_FARMER = "farmer"
ROLE_EXPERT = "expert"
# Super admin is an additive escalation of the admin role. Admin accounts
# grant the support module's shared capabilities; the super-admin flag
# (users.super_admin) additionally unlocks delete and member-management
# actions. It is never assignable through the public register API.
ROLE_SUPER_ADMIN = "super_admin"

# Crop Status
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"

# Weather Units
TEMP_UNIT = "Celsius"
RAIN_UNIT = "mm"