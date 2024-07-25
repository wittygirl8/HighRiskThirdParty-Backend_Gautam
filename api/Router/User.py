from flask import Blueprint, request, current_app as app
from flask_cors import CORS

from api.Controller.User import UserController as Controller
from utils.Return_codes import RetCodes
from utils.Utils import Utils
from utils.Token import admin_required, jwt_required

auth = Blueprint('auth', 'auth', url_prefix='/auth')
CORS(auth)


@auth.route('/login', methods=['POST'])
def login():
    data = Utils.get_request_data(request)
    token = Controller.login(data)
    if token:
        headers = {"Content-Type": "application/json; charset=UTF-8",
                   "Access-Control-Expose-Headers": "Authorization",
                   "Authorization": f"Bearer {token}"}
        return Utils.create_response("login was successful", headers=headers)
    else:
        return Utils.create_response("Invalid Credentials", code=RetCodes.Not_Found)


user_api_v1 = Blueprint('user_api_v1', 'user_api_v1', url_prefix='/api/v1/user')
CORS(user_api_v1)


@user_api_v1.route('/create', methods=['POST'])
@admin_required()
def create():
    data = Utils.get_request_data(request)
    _ret = Controller.create(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@user_api_v1.route('/get_all', methods=['GET'])
@admin_required()
def get_all():
    data = Utils.get_request_data(request)
    _ret = Controller.get_all(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@user_api_v1.route('/update', methods=['POST'])
@admin_required()
def update():
    data = Utils.get_request_data(request)
    _ret = Controller.update(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@user_api_v1.route('/delete', methods=['POST'])
@admin_required()
def delete():
    data = Utils.get_request_data(request)
    _ret = Controller.delete(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@user_api_v1.route('/status_update', methods=['POST'])
@admin_required()
def status_update():
    data = Utils.get_request_data(request)
    _ret = Controller.status_update(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)
