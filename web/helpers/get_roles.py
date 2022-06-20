from constants.user_roles import UserRoles

def get_roles_list():
    roles = (UserRoles.ADMIN.value, UserRoles.TOURIST.value, UserRoles.TRAVEL_GUIDE.value)
    return roles