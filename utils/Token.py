from flask import current_app
import datetime
from flask_jwt_extended import (
    jwt_required,
    get_jwt,
    verify_jwt_in_request, create_access_token, get_jwt_identity
)
from functools import wraps

"""
blacklist.py
This file just contains the blacklist of the JWT tokens–it will be imported by
app and the logout resource so that tokens can be added to the blacklist when the
user logs out.
"""
BLACKLIST = set()


def get_access_token(user, additional_claims):
    x =  create_access_token(identity=user,
                               additional_claims=additional_claims,
                               expires_delta=datetime.timedelta(hours=10),  # minutes=15),
                               fresh=True)
    print(x)
    return x

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user = get_jwt_identity()
            print(user)
            if user["type"].strip() == "admin":
                claims = get_jwt()
                return fn(*args, **kwargs)
            return 'Admin privilege required.', 401

        return decorator

    return wrapper
