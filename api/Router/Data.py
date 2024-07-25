from flask import Blueprint, request, current_app as app
from flask_cors import CORS

from api.Controller.Data import DataController as Controller
from utils.Return_codes import RetCodes
from utils.Utils import Utils
from utils.Token import admin_required, jwt_required

data_api_v1 = Blueprint('data_api_v1', 'data_api_v1', url_prefix='/api/v1/data')
CORS(data_api_v1)


@data_api_v1.route('/test', methods=['GET'])
def test():
    data = Utils.get_request_data(request)
    _ret = Controller.test(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)
