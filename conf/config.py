#coding: utf-8
import os, sys
HOME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bin')

port = 8011
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


#单条消息推送间隔，单位s
msg_push_interval = 10
#建立连接后，auth完成时间, 单位s
auth_time = 30
#扫描token的消息队列时间间隔，单位s
scan_token_msg_q_interval = 1
#消息过期时间, 单位s
msg_ttl = 30

