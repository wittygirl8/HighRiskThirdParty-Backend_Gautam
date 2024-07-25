from flask import Blueprint, request, current_app as app
from flask_cors import CORS

from api.Controller.Scorecard import ScorecardController as Controller
from utils.Return_codes import RetCodes
from utils.Utils import Utils
from utils.Token import admin_required, jwt_required

scorecard_api_v1 = Blueprint('scorecard_api_v1', 'scorecard_api_v1', url_prefix='/api/v1/scorecard')
CORS(scorecard_api_v1)


@scorecard_api_v1.route('/test', methods=['GET'])
@jwt_required()
def test():
    data = Utils.get_request_data(request)
    _ret = Controller.test(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)    


@scorecard_api_v1.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_stats(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)
    

@scorecard_api_v1.route('/dashboard/riskTable', methods=['GET'])
@jwt_required()
def dashboard_risk_table():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_risk_table(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)
    

@scorecard_api_v1.route('/dashboard/businessActivities', methods=['GET'])
@jwt_required()
def dashboard_business_activities():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_business_activities(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)
    

@scorecard_api_v1.route('/dashboard/connections', methods=['GET'])
@jwt_required()
def dashboard_connections():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_connections(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)
    

@scorecard_api_v1.route('/dashboard/globalSpend', methods=['GET'])
@jwt_required()
def dashboard_global_spend():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_global_spend(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@scorecard_api_v1.route('/dashboard/mediaCoverage', methods=['GET'])
@jwt_required()
def dashboard_media_coverage():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_media_coverage(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)


@scorecard_api_v1.route('/dashboard/connectionsTable', methods=['GET'])
@jwt_required()
def dashboard_connections_table():
    data = Utils.get_request_data(request)
    _ret = Controller.dashboard_connections_table(data)
    if _ret[0]:
        return Utils.create_response(_ret[1], data=_ret[2])
    else:
        return Utils.create_response(_ret[1], code=RetCodes.Not_Found)