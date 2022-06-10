from functools import wraps
from typing import List
from flask_jwt_extended import verify_jwt_in_request, get_jwt

""" Custom decorator that verifies JWT is present in the request, as well as insuring 
that the JWT has a claim indicating that this user has requested ROLE """
class roles():
    def role_auth(acc_type: List):
        def wrapper(fn):
            @wraps(fn)
            def decorator(*args, **kwargs):
                verify_jwt_in_request()
                claims = get_jwt()
                if claims["acc_type"] in acc_type:
                    return fn(*args, **kwargs)
                else:
                    return {"message": f"Only <{acc_type}> account type(s) are allowed to execute this API endpoint!"}, 403
            return decorator
        return wrapper