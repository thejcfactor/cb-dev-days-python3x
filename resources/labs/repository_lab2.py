import os
import datetime
import uuid
import traceback

from couchbase.collection import DeltaValue
from couchbase.options import SignedInt64
from couchbase.subdocument import upsert

from configuration.config import get_db_config
from library.utilities import output_message

from couchbase.cluster import Cluster, ClusterOptions, QueryOptions
from couchbase.collection import CounterOptions
from couchbase_core.cluster import PasswordAuthenticator
import couchbase.subdocument as SD
from couchbase.exceptions import CouchbaseException, DocumentNotFoundException
from couchbase.search import TermQuery, SearchOptions


class Repository(object):
    __instance = None
    host = ''
    bucket_name = ''
    username = ''
    password = ''

    counter_ids = {
        'customer': 'cbdd-customer-counter',
        'user': 'cbdd-user-counter',
        'order': 'cbdd-order-counter',
    }

    __cluster = None
    __bucket = None
    __collection = None

    # Singleton pattern - only 1 CB instance / bucket
    def __new__(cls):
        if Repository.__instance is None:

            Repository.__instance = object.__new__(cls)
            Repository.__instance.connect()
        return Repository.__instance

    def connect(self):
        db_config = get_db_config()
        self.host = db_config['host']
        self.bucket_name = db_config['bucket']
        self.username = db_config['username']
        self.password = db_config['password']
        connection_str = 'couchbase://{0}'.format(self.host)
        if db_config['secure'] == 'true':
            connection_str = 'couchbases://{0}?ssl=no_verify'.format(self.host)

        print(connection_str)
        secure = db_config['secure']
        print(secure)
        try:
            options = ClusterOptions(
                PasswordAuthenticator(self.username, self.password))
            self.__cluster = Cluster(connection_str, options)
            self.__bucket = self.__cluster.bucket(self.bucket_name)
            self.__collection = self.__bucket.default_collection()
            output_message('repository')
            if len(self.__bucket.name) > 0:
                output_message(self.__bucket.name,
                               'repository.py:connect() - connected to bucket:')
            else:
                output_message(
                    'repository.py:connect() - error connecting to bucket.')
        except Exception as ex:
            output_message(
                ex, 'repository.py:connect() - error connecting to bucket.')
            raise

    def ping(self):
        try:
            result = self.get_object_by_key('customer_0')
            return {
                'result': 'Connected to Couchbase server.' if result['result'] else None,
                'error': result['error']
            }
        except Exception as ex:
            output_message(
                ex, 'repository.py:ping() - error:')
            return {
                'result': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }
            }

    def get_user_info(self, username):
        try:
            n1ql = """
            SELECT c.custId, u.userId, u.username, u.`password`
            FROM `{0}` u
            JOIN `{0}` c ON c.username = u.username AND c.doc.type = 'customer'
            WHERE u.docType ='user' AND u.username = $1
            ORDER BY u.userId DESC
            LIMIT 1;
            """.format(self.bucket_name)

            params = [username]
            opts = QueryOptions(positional_parameters=params)

            result = self.__cluster.query(n1ql, opts)

            user = next((u for u in result.rows() if u is not None), None)

            return {'user_info': user, 'error': None}

        except Exception as ex:
            output_message(
                ex, 'repository.py:get_user_info() - error:')
            return {
                'user_info': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def create_session(self, username, expiry):
        try:
            session = {
                'sessionId': str(uuid.uuid4()),
                'username': username,
                'docType': 'SESSION'
            }

            key = 'session::{0}'.format(session['sessionId'])
            result = self.__collection.insert(key, session, ttl=expiry)
            return {'session_id': session['sessionId'] if result else None, 'error': None}
        except Exception as ex:
            output_message(
                ex, 'repository.py:create_session() - error:')
            return {
                'session_id': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def extend_session(self, sessionId, expiry):
        try:
            key = 'session::{0}'.format(sessionId)
            result = self.__collection.get(key, ttl=expiry)
            return {
                'session': result.content if result else None,
                'error': None
            }
        except DocumentNotFoundException as ex:
            output_message(
                ex, 'repository.py:extend_session() - error:')
            return {
                'session': None,
                'error': {
                    'message': 'Document not found.',
                    'stackTrace': traceback.format_exc()
                }}

    def create_account(self, user_info):
        try:
            customer_doc = self.get_new_customer_document(user_info)
            saved_customer = self.__collection.insert(
                customer_doc['_id'], customer_doc)
            if not saved_customer:
                return {
                    'acct': None,
                    'error': {
                        'message': 'Unable to save customer document.',
                        'stackTrace': None
                    }}

            user_doc = self.get_new_user_document(user_info)
            saved_user = self.__collection.insert(user_doc['_id'], user_doc)
            if not saved_user:
                return {
                    'acct': None,
                    'error': {
                        'message': 'Unable to save user document.',
                        'stackTrace': None
                    }}

            user_doc['password'] = None

            return {
                'acct': {
                    'customerInfo': customer_doc,
                    'userInfo': user_doc
                },
                'error': None
            }

        except Exception as ex:
            output_message(
                ex, 'repository.py:create_account() - error:')
            return {
                'acct': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def get_customer(self, id):
        """
            Lab 1:  K/V operation - Get
                1.  Get customer:  bucket.get(key)
        """
        try:
            result = self.__collection.get(id)
            return {
                'customer': result.content,
                'error': None
            }
        except Exception as ex:
            output_message(
                ex, 'repository.py:get_customer() - error:')
            return {
                'customer': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def search_products(self, product, fuzziness):
        """
        Lab 2:  Search operation (FTS)
          1.  FTS:
            term query w/ fuzziness
            use "basic-search" as index name for searchQuery
          2.  K/V getMulti() using FTS results
        """
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:search_products() - error:')
            return {
                'products': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def get_order(self, order_id):
        '''
            Lab 3:  K/V operation(s):
              1.  get order:  cluster.get(key)
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:get_order() - error:')
            return {
                'order': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def save_order(self, order):
        '''
            Lab 3:  K/V operation(s):
              1.  generate key:  order_<orderId>
              2.  insert order:  collection.insert(key, document)
              3.  IF successful insert, GET order
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:save_order() - error:')
            return {
                'order': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def replace_order(self, order):
        '''
            Lab 3:  K/V operation(s):
              1.  generate key:  order_<orderId>
              2.  replace order:  collection.insert(key, document)
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:replace_order() - error:')
            return {
                'success': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def delete_order(self, order_id):
        '''
            Lab 3:  K/V operation(s):
              1.  delete order:  cluster.remove(key)
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:delete_order() - error:')
            return {
                'success': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def get_orders(self, customer_id):
        '''
            Lab 4:  N1QL operations
              1. Get orders for customerId
                - WHERE order.orderStatus != 'created'
                - Document properties needed (more can be provided):
                    id,
                    orderStatus,
                    shippingInfo.name aliased as shippedTo,
                    grandTotal,
                    lineItems,
                    orderDate (hint use MILLIS_TO_STR())
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:get_orders() - error:')
            return {
                'order': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def get_new_order(self, customer_id):
        '''
            Lab 4:  N1QL operations
              1. Get latest order for customerId
                - WHERE order.orderStatus = 'created'
                - Document properties needed (more can be provided):
                    doc, custId, orderStatus,
                    billingInfo, shippingInfo, shippingTotal,
                    tax, lineItems, grandTotal, orderId, _id

        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:get_new_order() - error:')
            return {
                'order': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def save_address(self, cust_id, path, address):
        '''
            Lab 5:  K/V sub-document operation(s):
              1.  generate key:  customer_<custId>
              2.  get customer addresses
              3.  create business logic to add new address
              4.  update customer address path
              5.  update customer modified date and modifiedBy

            When updating, think about pros/cons to UPSERT v. REPLACE
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:save_address() - error:')
            return {
                'success': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    def udpate_address(self, cust_id, path, address):
        '''
            Lab 5:  K/V sub-document operation(s):
              1.  generate key:  customer_<custId>
              2.  update customer document address path
              3.  update customer document modified date and modifiedBy

            When updating, think about pros/cons to UPSERT v. REPLACE
        '''
        try:
            return 'NOP'
        except Exception as ex:
            output_message(
                ex, 'repository.py:udpate_address() - error:')
            return {
                'success': False,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }}

    '''
    Helper methods
    '''

    def get_object_by_key(self, key):
        try:
            result = self.__collection.get(key)
            return {
                'result': result.content,
                'error': None
            }
        except Exception as ex:
            output_message(
                ex, 'repository.py:get_object_by_key() - error retreiving document: {}'.format(key))
            return {
                'result': None,
                'error': {
                    'message': repr(ex),
                    'stackTrace': traceback.format_exc()
                }
            }

    def get_new_customer_document(self, user_info):
        cust_id = self.get_next_customer_id()
        key = 'customer_{0}'.format(cust_id + 1)
        now = datetime.datetime.now()
        timestamp = int(now.timestamp())
        return {
            'doc': {
                'type': 'customer',
                'schema': '1.0.0.0',
                'created': timestamp,
                'createdBy': 1234
            },
            '_id': key,
            'custId': cust_id + 1,
            'custName': {
                'firstName': user_info['firstName'],
                'lastName': user_info['lastName'],
            },
            'username': user_info['username'],
            'email': user_info['email'],
            'createdOn': '{0:%Y-%m-%d}'.format(now),
            'address': {
                'home': {
                    'address': '1234 Main St',
                    'city': 'Some City',
                    'state': 'TX',
                    'zipCode': '12345',
                    'country': 'US',
                },
                'work': {
                    'address': '1234 Main St',
                    'city': 'Some City',
                    'state': 'TX',
                    'zipCode': '12345',
                    'country': 'US',
                }
            },
            'mainPhone': {
                'phone_number': '1234567891',
                'extension': '1234'
            },
            'additionalPhones': {
                'type': 'work',
                'phone_number': '1234567891',
                'extension': '1234'
            }
        }

    def get_new_user_document(self, user_info):
        user_id = self.get_next_user_id()
        key = 'user_{0}'.format(user_id + 1)

        return {
            'docType': 'user',
            '_id': key,
            'userId': user_id + 1,
            'username': user_info['username'],
            'password': user_info['password']
        }

    def get_next_customer_id(self):
        result = self.__collection.binary().increment(
            self.counter_ids['customer'], CounterOptions(delta=DeltaValue(1), initial=SignedInt64(1000)))
        if '_original' in result.__dict__:
            return result.__dict__['_original'].value
        return None

    def get_next_user_id(self):
        result = self.__collection.binary().increment(
            self.counter_ids['user'], CounterOptions(delta=DeltaValue(1), initial=SignedInt64(1000)))
        if '_original' in result.__dict__:
            return result.__dict__['_original'].value
        return None

    def get_next_order_id(self):
        result = self.__collection.binary().increment(
            self.counter_ids['order'], CounterOptions(delta=DeltaValue(1), initial=SignedInt64(1000)))
        if '_original' in result.__dict__:
            return result.__dict__['_original'].value
        return None
