import hashlib
import os
import uuid
import random
import string
import traceback
import logging, logging.config, yaml
import zipfile
from io import BytesIO
from urllib.parse import urlsplit
import requests

from flask import request
from datetime import datetime, timedelta
from flask import current_app as app, make_response, jsonify, json
from flask_jwt_extended import get_jwt_identity, get_jwt

from utils.Return_codes import RetCodes


class Utils:
    a = 1

    @staticmethod
    def get_request_data(req):
        data = {}
        if req.method == "GET":
            data = req.args.to_dict()
            print(data, "in utils")
        elif req.method == "POST":
            if req.is_json:
                _ret = json.loads(req.data)
                data = _ret

        try:
            data["user"] = get_jwt_identity()
            claims = get_jwt()
            additional_claims = {k: v for k, v in claims.items() if
                                 k not in ['exp', 'iat', 'jti', 'fresh', 'type', 'sub']}
            data["claims"] = additional_claims
        except:
            pass
        return data

    @staticmethod
    def gen_guid():
        return uuid.uuid4().hex.replace("-", "")

    @staticmethod
    def gen_short_guid():
        random_data = os.urandom(128)
        return hashlib.md5(random_data).hexdigest()[:16]

    @staticmethod
    def get_client_ip():
        if request.environ.get("HTTP_X_FORWARDED_FOR") is None:
            return request.environ['REMOTE_ADDR']
        else:
            return request.environ["HTTP_X_FORWARDED_FOR"]

    @staticmethod
    def compute_md5_hash(str_val):
        m = hashlib.md5()
        m.update(str_val.encode('utf-8'))
        return m.hexdigest()

    @staticmethod
    def generate_new_password(password_length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(password_length))

    @staticmethod
    def get_current_dt():
        now = datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return dt_string

    @staticmethod
    def create_response(message, code=RetCodes.SUCCESS, data=None, headers=None):
        try:
            if headers is None:
                headers = {}
            if data is None:
                data = {}
            resp = {"message": message, "data": data}
            try:
                resp_json = jsonify(resp)
                print(resp_json)
            except Exception as E:
                print(E)
            resp = make_response(resp_json, code)
            for key, value in headers.items():
                resp.headers[key] = value
            print(resp)
            return resp
        except Exception as E:
            print(E)

    @staticmethod
    def error_log(self, method_name, error):
        class_name = self.__class__.__name__
        err = f"Error in {class_name}.{method_name}(): {repr(error)}."
        print(err)
        print(traceback.format_exc())
        return err

    @staticmethod
    def currency_format(num):
        num = float('{:.3g}'.format(num))
        magnitude = 0
        while abs(num) >= 1000:
            magnitude += 1
            num /= 1000.0
        return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

    @staticmethod
    def get_current_user(token_data):
        user = token_data["sub"]
        return user['user_id']

    @staticmethod
    def logging_init():
        log_file = 'ey_protect.log'
        log_format = '%(name)s - %(asctime)s -- %(levelname)s - %(message)s'
        logging.basicConfig(filename=log_file, filemode='w', format=log_format)
