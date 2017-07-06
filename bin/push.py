#coding: utf-8
import os, sys
import urllib, urllib2
import json

def push():
    url = "http://127.0.0.1:8091/v1/msg/push"
    #x = {"dev": "98:D3:32:70:DB:75", "msg": "rinidaye"}
   
    for i in xrange (1, 11):
        msg = {'msgid': i, 'type': 'train', 'data': {'id': 111}}
        x = {"token": '72197bc3-474f-46e3-8019-64b5df4b9994', 'msg': json.dumps(msg)}

        post_data = urllib.urlencode(x)
        re = urllib2.urlopen(url, post_data)
        s = re.read()
        print s

if __name__ == '__main__':
    push()
