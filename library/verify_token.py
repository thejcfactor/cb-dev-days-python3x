from flask import request, g
from functools import wraps
import traceback

from service.user_service import extend_session
from library.response import Response


def verify_token(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        bearer_header = request.headers.get('Authorization', None)
        response = Response()
        if not bearer_header:
            response.message = 'No authorization token provided.'
            response.authorized = False
            g.jwt = {
                'token': None,
                'result': response
            }
            return f(*args, **kwargs)

        try:
            token = bearer_header.replace('Bearer ', '')
            ext_session_res = extend_session(token)
            g.jwt = {
                'token': None if ext_session_res.error else token,
                'result': ext_session_res
            }
        except Exception as ex:
            response.error = {
                'message': repr(ex),
                'stackTrace': traceback.format_exc()
            }
            response.message
            g.jwt = {
                'token': None,
                'result': response
            }

        return f(*args, **kwargs)

    return decorated
