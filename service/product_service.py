import traceback

from library.response import Response
from repository.repository import Repository

repository = Repository()

def search_products(product, fuzziness):
    response = Response()
    result = repository.search_products(product, fuzziness)

    if 'error' in result and result['error']:
        response.error = result['error']
        response.message = 'Error searching for products.'
    else:
        if result == 'NOP':
            return response
        response.data = result['products']
        response.message = 'Successfully searched for products.'

    return response