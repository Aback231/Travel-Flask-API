from constants.http_status_codes import HTTP_403_FORBIDDEN
from functools import wraps
from typing import List
from flask_jwt_extended import verify_jwt_in_request, get_jwt

from libs.strings import get_text


""" Custom decorator that verifies JWT is present in the request, as well as insuring 
that the JWT has a claim indicating that this user has requested ROLE """


class roles():
    def role_auth(acc_type: List):
        def wrapper(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                verify_jwt_in_request()
                claims = get_jwt()
                # Verify acc_type in JWT belongs to one of acc_types requested to execute endpoint
                if claims["acc_type"] in acc_type:
                    return fn(*args, **kwargs)
                return {"message": get_text("DECORATOR_ROLES_ERROR").format(acc_type)}, HTTP_403_FORBIDDEN
            return decorator
        return wrapper