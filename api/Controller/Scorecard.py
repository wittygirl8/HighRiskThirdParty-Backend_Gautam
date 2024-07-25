from utils.Token import get_access_token
from api.Service.Scorecard import Scorecard
from utils.Utils import *


class ScorecardController:

    @staticmethod
    def test(data):
        _obj = Scorecard()
        return _obj.link_payment_hco_2_external(data)
