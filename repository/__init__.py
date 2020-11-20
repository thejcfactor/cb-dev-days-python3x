import os
import datetime
import uuid
import traceback

from configuration.config import get_db_config



class Repository(object):
    __instance = None
    host = ''
    bucket_name = ''
    username = ''
    password = ''

    __cluster = None
    __bucket = None

    # Singleton pattern - only 1 CB instance / bucket
    def __new__(cls):
        if Repository.__instance is None:

            Repository.__instance = object.__new__(cls)
            db_config = get_db_config()
            Repository.__instance.host = db_config['host']
            Repository.__instance.bucket_name = db_config['bucket']
            Repository.__instance.username = db_config['username']
            Repository.__instance.password = db_config['password']
            Repository.__instance.connect()
        return Repository.__instance