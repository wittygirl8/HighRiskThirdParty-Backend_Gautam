from utils.Token import get_access_token
from api.Service.Data import Data
from utils.Utils import *


class DataController:

    @staticmethod
    def test(data):
        _obj = Data()
        return _obj.link_payment_hco_2_external(data)
