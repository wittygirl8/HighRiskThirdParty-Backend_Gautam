import logging
import logging.config
import os
import yaml
import pyodbc

from flask import Flask, render_template, request, jsonify, g
from flask_jwt_extended import JWTManager, jwt_required
from flask_cors import CORS
from utils.db import MSSQLConnection
from utils.Token import BLACKLIST

from api.Router.User import auth, user_api_v1
from api.Router.Scorecard import scorecard_api_v1
from api.Router.Deepdive import deepdive_api_v1

def create_app(config_object='settings'):
    app = Flask(__name__)
    app.config.from_object(config_object)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    try:
        logging.config.dictConfig(yaml.full_load(open("logging.conf")))
        app.logger = logging.getLogger('file')
    except Exception as e:
        app.logger.info("No logging config file found, using default logger: {}".format(e))

    jwt = JWTManager(app)

    app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB
    db = MSSQLConnection()
    db.init_app(app)

    @app.route("/check", methods=["GET"])
    def check_app():
        kwargs = {"name": request.args.get('name')}
        return render_template("index.html", **kwargs)

    @app.route("/gauth", methods=["GET"])
    @jwt_required()
    def gauth():
        kwargs = {"name": request.args.get('name')}
        return render_template("index.html", **kwargs)

    # This method will check if a token is blacklisted, and will be called automatically when blacklist is enabled
    @jwt.token_in_blocklist_loader
    def check_if_token_is_revoked(jwt_header, jwt_payload):
        return jwt_payload['jti'] in BLACKLIST

    # The following callbacks are used for customizing jwt response/error messages.
    # The original ones may not be in a very pretty format (opinionated)
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'message': 'The token has expired.',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'message': "Use a new token",
            'error': error
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "message": "Request does not contain an access token.",
            'error': error
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_loader(jwt_header, jwt_payload):
        return jsonify({
            "message": "The token has been revoked.",
            'error': 'token_revoked'
        }), 401

    @app.after_request
    def after_request_func(response):
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response

    cors = CORS(app)

    app.register_blueprint(auth)
    app.register_blueprint(user_api_v1)
    app.register_blueprint(scorecard_api_v1)
    app.register_blueprint(deepdive_api_v1)

    return app

