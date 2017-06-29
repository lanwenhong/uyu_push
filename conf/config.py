#coding: utf-8
import os, sys
HOME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin')

port = 8012
host = '127.0.0.1'

LOGFILE = { 
    'root': {
        'filename': {
            'DEBUG': os.path.join(HOME, '../log/uyu_push.log'),
            'WARN': os.path.join(HOME, '../log/uyu_push.error.log'),
        }   
    }   
}
LOGFILE = None
REDIS_CONFIG = {
    'host': '127.0.0.1',
    'port': 4600,
    'selected_db': 0
}
