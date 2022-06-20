from enum import Enum
import config

class UserRoles(Enum):
    TOURIST = config.TOURIST
    TRAVEL_GUIDE = config.TRAVEL_GUIDE
    ADMIN = config.ADMIN
    DEFAULT_ROLE = TOURIST

    @classmethod
    def get_roles_touple(cls):
        roles = ()
        for role in cls:
            roles = (*roles, role.value)
        return roles