import jwt
import bcrypt
import traceback

from library.response import Response
from repository.repository import Repository
from configuration.config import get_secret, get_ttl

repository = Repository()

def register(req):
    req['password'] = bcrypt.hashpw(str.encode(
        req['password']), bcrypt.gensalt()).decode()
    response = Response()
    result = repository.create_account(req)
    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error registering customer/user.'
    else:
        if result == 'NOP':
            return response
        response.data = result['acct']
        response.message = 'Successfully registered customer/user.'

    return response


def login(req):
    valid_user = verify_user(req['username'], str.encode(req['pw']))
    if valid_user.error or 'Operation not' in valid_user.message:
        return valid_user

    response = Response()

    if not valid_user.data:
        response.message = 'Invalid user.  Check username and password.'
        response.authorized = False
        return response

    key = 'customer_{0}'.format(valid_user.data['custId'])
    customer_info = repository.get_object_by_key(key)

    session_res = create_session(req['username'])

    if session_res.error:
        return session_res

    secret = get_secret()
    encoded_jwt = jwt.encode({'id': session_res.data},
                             secret, algorithm='HS256')
    response.data = {
        'userInfo': {
            'userId': valid_user.data['userId'],
            'username': valid_user.data['username'],
            'token': encoded_jwt.decode()
        },
        'customerInfo': customer_info['result']
    }
    response.message = 'Successfully logged in (session created).'
    response.authorized = True

    return response


def verify_user(username, pw, jwt=None):
    result = repository.get_user_info(username)

    response = Response()
    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Could not find user.'
        return response

    if result == 'NOP':
        return response

    # no password when using JWT, if user is found, consider valid
    if jwt:
        response.data = result['user_info']
        response.message = 'JWT - no password verification needed.'
        return response

    if bcrypt.checkpw(pw, str.encode(result['user_info']['password'])):
        response.data = result['user_info']
        response.message = 'Password verified.'

    return response


def create_session(username):
    response = Response()

    expiry = int(get_ttl())
    session = repository.create_session(username, expiry)

    if 'error' in session and session['error']:
        response.message = 'Error creating session.'
        response.error = session['error']
        return response

    if 'session_id' in session and session['session_id']:
        response.data = session['session_id']
        response.message = 'Session created.'

    return response


def extend_session(token):
    secret = get_secret()
    response = Response()
    #decoded = None
    try:
        decoded_jwt = jwt.decode(token, secret, algorithms=['HS256'])
    except Exception as ex:
        print(ex)
        response.message = 'Error extending session.  Invalid token.'
        response.error = ex
        return response

    expiry = int(get_ttl())
    session = repository.extend_session(decoded_jwt['id'], expiry)
    if 'error' in session and session['error']:
        if session['error']['message'] == 'Document not found.':
            response.message = 'Unauthorizeed.  Session expired'
            response.authorized = False
        else:
            response.message = "Error trying to verify session."

        response.error = {
            'message': repr(session['error']),
            'stackTrace': traceback.format_exc()
        }
        return response

    if session == 'NOP':
        return response

    response.data = session['session']
    response.message = 'Successfully extended session.'
    response.authorized = True
    return response


def get_user_from_session(username, token):
    valid_user = verify_user(username, None, True)

    if valid_user.error or 'Operation not' in valid_user.message:
        return valid_user

    response = Response()

    if not valid_user.data:
        response.message = 'Invalid user.  Check username and password.'
        response.authorized = False
        return response

    key = 'customer_{}'.format(valid_user.data['custId'])
    customer_info = repository.get_object_by_key(key)
    if ('error' in customer_info and customer_info['error']) or ('result' in customer_info and not customer_info['result']):
        response.message = ''
        response.authorized = False
        response.error = customer_info['error']
        return response

    response.data = {
        'userInfo': {
            'userId': valid_user.data['userId'],
            'username': valid_user.data['username'],
            'token': token
        },
        'customerInfo': customer_info['result']
    }
    response.message = 'Successfully verified and extended session.'
    response.authorized = True

    return response


def get_customer(id):
    response = Response()
    customer_id = 'customer_{}'.format(id)
    result = repository.get_customer(customer_id)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error retrieving customer.'
        return response

    if result == 'NOP':
        return response

    response.data = result['customer']
    response.message = 'Successfully retrieved customer.'
    return response

def get_order(order_id):
    response = Response()
    result = repository.get_order(order_id)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error retrieving order.'
        return response

    if result == 'NOP':
        return response

    response.data = result['order']
    response.message = 'Successfully retrieved order.'
    return response

def save_or_update_order(req):
    return update_order(req['order']) if req['update'] else save_order(req['order'])

def update_order(order):
    response = Response()
    result = repository.replace_order(order)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error updating order.'
        return response

    if result == 'NOP':
        return response

    response.data = result['success']
    response.message = 'Successfully updated order.'
    return response

def save_order(order):
    response = Response()
    result = repository.save_order(order)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error saving order.'
        return response

    if result == 'NOP':
        return response

    response.data = result['order']
    response.message = 'Successfully saved order.'
    return response

def delete_order(order_id):
    response = Response()
    result = repository.delete_order(order_id)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error retrieving order.'
        return response

    if result == 'NOP':
        return response

    response.data = result['success']
    response.message = 'Successfully deleted order.'
    return response

def get_customer_orders(id):
    response = Response()
    result = repository.get_orders(id)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error retrieving customer orders.'
        return response

    if result == 'NOP':
        return response

    response.data = result['orders']
    response.message = 'Successfully retrieved customer orders.'
    return response

def get_new_order(id):
    response = Response()
    result = repository.get_new_order(id)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error retrieving customer new/pending order.'
        return response

    if result == 'NOP':
        return response

    response.data = result['order']
    response.message = 'Successfully retrieved customer new/pending order.'
    return response

def save_or_update_address(req):
    return update_address(req) if req['update'] else save_address(req)

def update_address(req):
    response = Response()
    result = repository.udpate_address(req['custId'], req['path'], req['address'])

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error updating address.'
        return response

    if result == 'NOP':
        return response

    response.data = result['success']
    response.message = 'Successfully updated address.'
    return response

def save_address(req):
    response = Response()
    result = repository.save_address(req['custId'], req['path'], req['address'])

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error saving address.'
        return response

    if result == 'NOP':
        return response

    response.data = result['success']
    response.message = 'Successfully saved address.'
    return response
