#coding: utf-8
import os, sys
import logging
HOME = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HOME), 'conf'))

from zbase.base import logger
import config
import json
import time
import tornado.httpserver
import tornado.web
import tornado.ioloop
from tornado import websocket

from uyubase.base.response import success, error, UAURET

if config.LOGFILE:
    log = logger.install(config.LOGFILE)
else:
    log = logger.install('stdout')


class PushHandler(tornado.web.RequestHandler):
    def get(self):
        return self.post()

    def post(self):
        dev = self.get_argument("dev", None)
        msg = self.get_argument("msg", None)
        if not dev or not msg:
            log.warn("param err")
            log.info("func=push|dev=%s|msg=%s|status=fail|ret=%s", dev, msg, error(UAURET.PUSHDEVERR))
            self.write(error(UAURET.PUSHDEVERR))
        client = WsHandler.clients.get(dev, None)
        if not client:
            log.warn("dev %s offline", dev)
            self.write(error(UAURET.PUSHCONNERR))
            log.info("func=push|dev=%s|msg=%s|status=fail|ret=%s", dev, msg, error(UAURET.PUSHCONNERR))
            return

        start = int(time.time()) * 1000000
        client.write_message(msg)
        self.write(success({}))
        end = int(time.time()) * 1000000 
        log.info("func=push|dev=%s|msg=%s|status=succ|ret=%s", dev, msg, success({}))

class WsHandler(websocket.WebSocketHandler):
    clients = {} 
    
    def check_origin(self, origin):
        return True

    def open(self):
        self.stream.set_nodelay(True)
        self.connect_time = int(time.time()) * 1000000
        
    def on_message(self, message):
        cdata = json.loads(message)
        log.debug("cdata: %s", cdata)
        dev = cdata.get("dev", None)
        log.debug("dev: %s", dev)
        if not dev:
            self.write_message(error(UAURET.PUSHDEVERR))
            self.close()
            log.info("func=bind|dev=%s|status=err", dev)
            return
        client = WsHandler.clients.get(dev, None)
        if not client:
            WsHandler.clients[dev] = self

        else:
            client.close()
            WsHandler.clients[dev] = self
        self.dev = dev
        self.write_message(success({}))
        log.info("func=bind|dev=%s|status=succ", dev)

    def on_close(self):
        # 客户端主动关闭
        del WsHandler.clients[self.dev]
        log.info("func=close|dev=%s|stay=%d", self.dev, int(time.time()) * 1000000 - self.connect_time)

    def on_pong(self, data):
        log.info("func=pong|data=%s", data)
 
if __name__ == '__main__':
    app = tornado.web.Application(
        handlers=[
            (r"/v1/msg/push", PushHandler),
            (r"/v1/msg/connect", WsHandler)
        ],
        debug = False,
    )
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(config.port, address=config.host)
    log.info("server start")
    tornado.ioloop.IOLoop.instance().start()
