from enum import Enum

class UserRoles(Enum):
    TOURIST = "Tourist"
    TRAVEL_GUIDE = "Travel Guide"
    ADMIN = "Admin"
    DEFAULT_ROLE = TOURIST