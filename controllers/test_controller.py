from flask import Blueprint, jsonify, request, g
from flask import json
import yaml
from flasgger import Swagger
from flasgger.utils import swag_from
import attr
import traceback
#from functools import wraps

from library.response import Response
from repository.repository import Repository
#from library.verify_token import verify_token

#from configuration.config import get_secret
from service.user_service import login as user_login

test_api = Blueprint('test', __name__, url_prefix='/test')
repository = Repository()


@test_api.route('/ping', methods=['GET'])
@swag_from('./swagger_ui/ping.yml', methods=['GET'])
def ping():
    response = Response()
    try:
        ping_resp = repository.ping()

        if ping_resp['error']:
            response.message = 'Error trying to ping database.'
            response.error = ping_resp['error']
            return jsonify(attr.asdict(response)), 500

        if ping_resp == 'NOP':
            return jsonify(attr.asdict(response)), 200

        response.data = ping_resp['result']
        response.message = 'Successfully pinged database.'
        return jsonify(attr.asdict(response)), 200
    except Exception as ex:
        response.message = 'Error attempting to ping database.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        return jsonify(attr.asdict(response)), 500


@test_api.route('/login', methods=['GET'])
@swag_from('./swagger_ui/test_login.yml', methods=['GET'])
def login():
    request_args = request.args
    response = Response()

    try:
        if 'username' not in request_args or 'password' not in request_args:
            response.message = 'No username and/or password provided.'
            return jsonify(attr.asdict(response)), 500

        print(request_args.get('password'))
        req = {
            'username': request_args.get('username'),
            'pw': request_args.get('password')
        }

        response = user_login(req)
        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error attempting to login user.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        return jsonify(attr.asdict(response)), 500