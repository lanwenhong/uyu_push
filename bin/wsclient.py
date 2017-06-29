#coding:utf-8
import os, sys
import json
from websocket import create_connection


def wait():
    ws = create_connection("ws://127.0.0.1:8012/v1/msg/connect")
    # dev_bind = {"dev": "98:D3:32:70:DB:75"}
    dev_bind = {"dev": "bt_v1"}
    ws.send(json.dumps(dev_bind))
    
    ret = ws.recv()
    print "bind ret ", ret
    x = json.loads(ret)
    if x["respcd"] != "0000":
        return

    while True:
        ret = ws.recv()
        print "recv msg ", ret


if __name__ == '__main__':
    wait()
