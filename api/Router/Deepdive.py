from flask import Blueprint, request, current_app as app
from flask_cors import CORS

from api.Controller.Deepdive import DeepdiveController as Controller
from utils.Return_codes import RetCodes
from utils.Utils import Utils
from utils.Token import admin_required, jwt_required

deepdive_api_v1 = Blueprint('deepdive_api_v1', 'deepdive_api_v1', url_prefix='/api/v1/deepdive')
CORS(deepdive_api_v1)


@deepdive_api_v1.route('/graph/user', methods=['GET'])
@jwt_required()
def data_by_user():
    data = Utils.get_request_data(request)
    print(data)
    _ret = Controller.get_country(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@deepdive_api_v1.route('/graph/country', methods=['GET'])
@jwt_required()
def graph_by_country():
    data = Utils.get_request_data(request)
    print(data, "--------------------------------------------------------")
    _ret = Controller.graph_by_country(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@deepdive_api_v1.route('/graph/node', methods=['GET'])
@jwt_required()
def graph_by_node():
    data = Utils.get_request_data(request)
    _ret = Controller.graph_by_node(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@deepdive_api_v1.route('/timeline', methods=['GET'])
@jwt_required()
def timeline():
    data = Utils.get_request_data(request)
    _ret = Controller.timeline(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@deepdive_api_v1.route('/ext_events', methods=['GET'])
@jwt_required()
def ext_events():
    data = Utils.get_request_data(request)
    _ret = Controller.ext_events(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@deepdive_api_v1.route('/overview', methods=['GET'])
@jwt_required()
def overview():
    data = Utils.get_request_data(request)
    _ret = Controller.overview(data)
    print(_ret)
    print('IN ROUTER')
    if _ret[0]:
        print("in if")
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


