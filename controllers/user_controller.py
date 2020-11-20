from flask import Blueprint, jsonify, request, g
#from flask import json
#import yaml
#from flasgger import Swagger
from flasgger.utils import swag_from
import attr
import traceback
#from functools import wraps

from library.response import Response
#from repository.repository import Repository
from library.verify_token import verify_token
import service.user_service


user_api = Blueprint('user', __name__, url_prefix='/user')


@user_api.route('/register', methods=['POST'])
@swag_from('./swagger_ui/register.yml', methods=['POST'])
def register():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_content = request.get_json()

        if 'requestId' in request_content:
            req_id = int(request_content['requestId'])

        response = service.user_service.register(request_content)
        response.request_id = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200
    except Exception as ex:
        response.message = 'Error attempting to register user.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500


@user_api.route('/login', methods=['POST'])
@swag_from('./swagger_ui/login.yml', methods=['POST'])
def login():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_content = request.get_json()

        if 'requestId' in request_content:
            req_id = int(request_content['requestId'])

        if not ('username' in request_content and 'password' in request_content):
            response.message = 'No username and/or password provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        req = {
            'username': request_content['username'],
            'pw': request_content['password']
        }

        response = service.user_service.login(req)
        response.request_id = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        if response.data and response.authorized:
            return jsonify(attr.asdict(response)), 200

        return jsonify(attr.asdict(response)), 401

    except Exception as ex:
        response.message = 'Error attempting to login user.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500


@user_api.route('/verifyUserSession', methods=['GET'])
# this needs to go before the @swag_from() otherwise swagger page throws an error
@verify_token
@swag_from('./swagger_ui/verify_user_session.yml', methods=['GET'])
def verify_user_session():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_content = request.get_json()

        if request_content and 'requestId' in request_content:
            req_id = int(request_content['requestId'])

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401

            return jsonify(attr.asdict(jwt['result'])), 400

        username = jwt['result'].data['username']
        response = service.user_service.get_user_from_session(
            username, jwt['token'])
        response.request_id = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200
    except Exception as ex:
        response.message = 'Error trying to verify user session.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500


@user_api.route('/getCustomer', methods=['GET'])
@verify_token
@swag_from('./swagger_ui/get_customer.yml', methods=['GET'])
def get_customer():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_args = request.args

        if 'requestId' in request_args:
            req_id = int(request_args.get('requestId'))

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401

            return jsonify(attr.asdict(jwt['result'])), 400

        if 'customerId' not in request_args:
            response.message = 'No customerId provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        customer_id = int(request_args.get('customerId'))

        response = service.user_service.get_customer(customer_id)
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to retrieve customer.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500

@user_api.route('/getOrder', methods=['GET'])
@verify_token
@swag_from('./swagger_ui/get_order.yml', methods=['GET'])
def get_order():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_args = request.args

        if 'requestId' in request_args:
            req_id = int(request_args.get('requestId'))

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401
                
            return jsonify(attr.asdict(jwt['result'])), 400

        if 'orderId' not in request_args:
            response.message = 'No orderId provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        response = service.user_service.get_order(request_args.get('orderId'))
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to retrieve order.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500

@user_api.route('/saveOrUpdateOrder', methods=['POST'])
@verify_token
@swag_from('./swagger_ui/save_or_update_order.yml', methods=['POST'])
def save_or_update_order():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_content = request.get_json()

        if 'requestId' in request_content:
            req_id = int(request_content['requestId'])

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401
                
            return jsonify(attr.asdict(jwt['result'])), 400

        if 'order' not in request_content:
            response.message = 'No order provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        req = {
            'order': request_content['order'],
            'update': request_content['update'] if 'update' in request_content else False
        }

        response = service.user_service.save_or_update_order(req)
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to save/update order.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500

@user_api.route('/deleteOrder', methods=['DELETE'])
@verify_token
@swag_from('./swagger_ui/delete_order.yml', methods=['DELETE'])
def delete_order():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_args = request.args

        if 'requestId' in request_args:
            req_id = int(request_args.get('requestId'))

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401
                
            return jsonify(attr.asdict(jwt['result'])), 400

        if 'orderId' not in request_args:
            response.message = 'No orderId provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        response = service.user_service.delete_order(request_args.get('orderId'))
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to delete order.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500

@user_api.route('/getCustomerOrders', methods=['GET'])
@verify_token
@swag_from('./swagger_ui/get_customer_orders.yml', methods=['GET'])
def get_customer_orders():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_args = request.args

        if 'requestId' in request_args:
            req_id = int(request_args.get('requestId'))

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401
                
            return jsonify(attr.asdict(jwt['result'])), 400

        if 'customerId' not in request_args:
            response.message = 'No customerId provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        customer_id = int(request_args.get('customerId'))

        response = service.user_service.get_customer_orders(customer_id)
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to retrieve customer orders.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500

@user_api.route('/getNewOrder', methods=['GET'])
@verify_token
@swag_from('./swagger_ui/get_new_order.yml', methods=['GET'])
def get_new_order():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_args = request.args

        if 'requestId' in request_args:
            req_id = int(request_args.get('requestId'))

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401
                
            return jsonify(attr.asdict(jwt['result'])), 400

        if 'customerId' not in request_args:
            response.message = 'No customerId provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        customer_id = int(request_args.get('customerId'))

        response = service.user_service.get_new_order(customer_id)
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to retrieve customer orders.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500

@user_api.route('/saveOrUpdateAddress', methods=['POST'])
@verify_token
@swag_from('./swagger_ui/save_or_update_address.yml', methods=['POST'])
def save_or_update_address():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_content = request.get_json()

        if 'requestId' in request_content:
            req_id = int(request_content['requestId'])

        jwt = g.get('jwt', None)
        if not jwt['token']:
            if jwt['result'].authorized is not None and not jwt['result'].authorized:
                return jsonify(attr.asdict(jwt['result'])), 401
                
            return jsonify(attr.asdict(jwt['result'])), 400

        if 'customerId' not in request_content:
            response.message = 'No customerId provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        if 'address' not in request_content:
            response.message = 'No address provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        if 'path' not in request_content:
            response.message = 'No path provided.'
            response.requestId = req_id
            return jsonify(attr.asdict(response)), 400

        req = {
            'custId': request_content['customerId'],
            'address': request_content['address'],
            'path': request_content['path'],
            'update': request_content['update'] if 'update' in request_content else False
        }

        response = service.user_service.save_or_update_address(req)
        response.requestId = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200

    except Exception as ex:
        response.message = 'Error trying to save/update address.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500