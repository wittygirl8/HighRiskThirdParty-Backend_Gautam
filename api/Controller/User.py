from utils.Token import get_access_token
from api.Service.User import User
from utils.Utils import *


class UserController:

    @staticmethod
    def login(data):
        user = User().login(data)
        claims = User.get_claims(user)
        access_token = None
        if user:
            access_token = get_access_token(user, claims)
        return access_token

    @staticmethod
    def create(data):
        _obj = User()
        return _obj.create(data)

    @staticmethod
    def get_all(data):
        _obj = User()
        return _obj.get_all(data)

    @staticmethod
    def update(data):
        _obj = User()
        return _obj.update(data)

    @staticmethod
    def delete(data):
        _obj = User()
        return _obj.delete(data)

    @staticmethod
    def status_update(data):
        _obj = User()
        return _obj.status_update(data)
