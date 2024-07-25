from utils.Token import get_access_token
from api.Service.Deepdive import Deepdive
from utils.Utils import *


class DeepdiveController:


    @staticmethod
    def get_country(data):
        _obj = Deepdive()
        return _obj.get_countries(data)

    @staticmethod
    def data_by_country(data):
        _obj = Deepdive()
        return _obj.data_by_country(data)

    @staticmethod
    def data_by_node(data):
        _obj = Deepdive()
        return _obj.data_by_node(data)

    @staticmethod
    def timeline(data):
        _obj = Deepdive()
        return _obj.timeline(data)

    @staticmethod
    def ext_events(data):
        _obj = Deepdive()
        return _obj.ext_events(data)

    @staticmethod
    def overview(data):
        _obj = Deepdive()
        return _obj.overview(data)