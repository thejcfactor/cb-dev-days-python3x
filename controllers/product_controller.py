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
#from library.verify_token import verify_token
import service.product_service

product_api = Blueprint('product', __name__, url_prefix='/product')

@product_api.route('/searchProducts', methods=['GET'])
@swag_from('./swagger_ui/search_products.yml', methods=['GET'])
def search():
    # only used for req/response logging in UI
    req_id = None
    response = Response()
    try:
        request_args = request.args

        if 'requestId' in request_args:
            req_id = int(request_args.get('requestId'))

        if 'product' not in request_args or request_args.get('product') == '':
            response.message = 'No search term provided.'
            return jsonify(attr.asdict(response)), 200

        fuzziness = None
        if 'fuzziness' in request_args:
            fuzziness = int(request_args.get('fuzziness'))

        product = request_args.get('product')
        response = service.product_service.search_products(product, fuzziness)
        response.request_id = req_id

        if response.error:
            return jsonify(attr.asdict(response)), 500

        return jsonify(attr.asdict(response)), 200
    except Exception as ex:
        response.message = 'Error attempting to search for products.'
        response.error = {
            'message': repr(ex),
            'stackTrace': traceback.format_exc()
        }
        response.requestId = req_id
        return jsonify(attr.asdict(response)), 500