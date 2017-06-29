#coding:utf-8
import os, sys
import json
from websocket import create_connection


def wait():
    ws = create_connection("ws://127.0.0.1:8011/v1/msg/wait")
    msg = {"msgid": 11111, "type": "auth", "data": {"token": "xxxxxxx"}}
    #dev_bind = {"token": "98:D3:32:70:DB:75"}
    ws.send(json.dumps(msg))
    
    ret = ws.recv()
    print "bind ret ", ret
    x = json.loads(ret)
    if x["result"] != "0000":
        return

    while True:
        ret = ws.recv()
        print "recv msg ", ret


if __name__ == '__main__':
    wait()
