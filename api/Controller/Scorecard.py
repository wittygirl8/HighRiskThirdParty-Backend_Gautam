from utils.Token import get_access_token
from api.Service.Scorecard import Scorecard
from utils.Utils import *


class ScorecardController:

    @staticmethod
    def test(data):
        _obj = Scorecard()
        return _obj.link_payment_hco_2_external(data)    
    
    @staticmethod
    def dashboard_stats(data):
        _obj = Scorecard()
        return _obj.dashboard_stats(data)
    
    @staticmethod
    def dashboard_risk_table(data):
        _obj = Scorecard()
        return _obj.dashboard_risk_table(data)
    
    @staticmethod
    def dashboard_business_activities(data):
        _obj = Scorecard()
        return _obj.dashboard_business_activities(data)
    
    @staticmethod
    def dashboard_connections(data):
        _obj = Scorecard()
        return _obj.dashboard_connections(data)
    
    @staticmethod
    def dashboard_global_spend(data):
        _obj = Scorecard()
        return _obj.dashboard_global_spend(data)
    
    @staticmethod
    def dashboard_media_coverage(data):
        _obj = Scorecard()
        return _obj.dashboard_media_coverage(data)
    
    @staticmethod
    def dashboard_connections_table(data):
        _obj = Scorecard()
        return _obj.dashboard_connections_table(data)
    