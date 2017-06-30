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
from tornado.httpclient import AsyncHTTPClient
import tornado.web
import tornado.ioloop as ioloop
from tornado import websocket
import traceback
import urllib

from uyubase.base.response import success, error, UAURET

if config.LOGFILE:
    log = logger.install(config.LOGFILE)
else:
    log = logger.install('stdout')


class PushHandler(tornado.web.RequestHandler):
    key_need = {
            'push': ('msgid', 'type', 'data'),
    }

    def get(self):
        return self.post()

    def post(self):
        try:
            start = int(time.time() * 1000000)
            msg_body = self.get_argument("msg", None)
            token = self.get_argument("token", None)

            log.debug("msg_body: %s", msg_body)
            if not token or not msg_body:
                log.warn("param err")
                self.write(error(UAURET.PUSHDEVERR))
                return
            push_data = json.loads(msg_body)
            check = PushHandler.key_need['push']
            for item in check:
                if push_data.get(item, None) == None:
                    log.warn("param err lack %s", item)
                    self.write(error(UAURET.PUSHDEVERR))
                    return
            msg_id = push_data['msgid']
            
            push_to = WsHandler.clients.get(token, None) 
            if not push_to:
                log.warn("token %s offline", token)
                self.write(error(UAURET.PUSHCONNERR))
                return
            else:
                msg_q = push_to["msg_q"]
                msg_q.append(msg_id)
                WsHandler.msgs[msg_id] = {"create_time": time.time(), "push_time": None, "msg": msg_body, "push_count": 0, "succ": False}
            
            self.write(success({}))
        except:
            log.warn(traceback.format_exc())
            self.write(error(UAURET.PUSHDEVERR))

class WsHandler(websocket.WebSocketHandler):
    clients = {} 
    msgs = {}
    key_need = {
            'auth': {'req': ('msgid', 'type', 'data'), 'ack': ('msgid', 'type', 'result')},
            'train': {'req': ('msgid', 'type', 'data'), 'ack': ('msgid', 'type', 'result'),},
            'inspect': {'req': ('msgid', 'type', 'data'), 'ack': ('msgid', 'type', 'result'),},
    }
    
    def check_origin(self, origin):
        return True
    
    def _close_pre(self):
        loop = ioloop.IOLoop.current()
        if self.check_auth:
            loop.remove_timeout(self.check_auth)
        if self.msg_push:
            loop.remove_timeout(self.msg_push)
        if self.token:
            xtoken = WsHandler.clients.get(self.token, None)
            if xtoken:
                xtoken['conn'] = None

    def _ws_close(self):
        self._close_pre()
        self.close()

    def _check_auth(self):
        if not self.is_auth:
            log.warn("not auth close")
            self._ws_close()
    
    def _msg_push(self):
        try:
            log.debug("====push===")
            loop = ioloop.IOLoop.current()
            self.msg_push = loop.add_timeout(loop.time() + config.scan_token_msg_q_interval, self._msg_push)
            msg_q = WsHandler.clients[self.token]['msg_q'] 
            if len(msg_q) == 0:
                log.debug("token %s msg_q empty", self.token)
                return
            msg_id = msg_q.pop(0)
            log.debug("msg_id: %d", msg_id)
            msg_info =  WsHandler.msgs[msg_id]
            push_count = msg_info["push_count"]
            ctime = int(msg_info["create_time"])
            msg = msg_info["msg"]
            succ = msg_info["succ"]

            if succ:
                log.debug("push msgid %d succ!!!", msg_id)
                del WsHandler.msgs[msg_id]
                return
            if push_count == 0 or (int(time.time()) - ctime < config.msg_ttl and int(time.time()) - int(msg_info["push_time"]) >= config.msg_push_interval):
                self.write_message(msg)
                msg_info["push_count"] += 1
                msg_info["push_time"] = time.time()
                msg_q.append(msg_id)
                log.debug("qlen: %d",   len(msg_q))
                log.debug("qlen: %d",   len(WsHandler.clients[self.token]['msg_q']))
                log.info('func=push|ctime=%d|push_count=%d|push_time=%d|token=%s|msgid=%d', ctime, msg_info["push_count"], msg_info["push_time"], self.token, msg_id)
            elif int(time.time()) - ctime >= config.msg_ttl:
                log.info('func=push_expire|ctime=%d|push_count=%d|push_time=%d|token=%s|msgid=%d', ctime, msg_info["push_count"], msg_info["push_time"], self.token, msg_id)
                del WsHandler.msgs[msg_id]
            else:
                log.debug("msgid %s not target throw to q", msg_id)
                msg_q.append(msg_id)
                
        except:
            log.warning(traceback.format_exc())

    def open(self):
        self.stream.set_nodelay(True)
        self.connect_time = int(time.time()) * 1000000
        self.is_auth = False

        loop = ioloop.IOLoop.current()
        
        #链接开始，30s不发auth报文， 关闭连接
        self.check_auth = None
        #每个auth后的连接，定时器每隔1s从推送队列中取出消息进行推送
        self.msg_push = None

        self.token = None
        self.cdata = None

        self.check_auth = loop.add_timeout(loop.time() + config.auth_time, self._check_auth)
        self.httpclient = AsyncHTTPClient()

        #self.close()
        
    def _proto_check(self, cdata):
        type = cdata.get("type", None)  
        if not type:
            return False
        check = WsHandler.key_need.get(type, None)
        if not check:
            return False
        result = cdata.get("result", None)
        if result:
            need = check['ack']
            for key in need:
                if  cdata.get(key, None) == None:
                    return False
        else:
            need = check['req']
            log.debug("need: %s", need)
            for key in need:
                log.debug("key: %s", key)
                if cdata.get(key, None) == None:
                    return False
        return True
            
    def _ack_handler(self, cdata):
        result = cdata["result"]
        msgid = cdata["msgid"]
        msg_info =  WsHandler.msgs[msgid]
        ctime = msg_info["create_time"]
        if result == UAURET.OK:
            msg_id = cdata["msgid"]
            WsHandler.msgs[msg_id]['succ'] = True
        log.info("func=push_ack|token=%s|ctime=%d|push_count=%d|msgid=%d|time=%d", self.token, int(ctime),  msg_info["push_count"], msgid, int(time.time() * 1000000) - int(ctime * 1000000))
        
    def auth_ret(self, response):
        try:
            if response.code != 200:
                self._ws_close()
                return
            log.debug("body: %s", response.body)
            vdata = json.loads(response.body)
            if vdata['respcd'] == UAURET.OK:
                self.is_auth = True
            ret = {"msgid": self.cdata["msgid"], "type": self.cdata["type"], "result": vdata['respcd']}
            self.write_message(json.dumps(ret))
            log.info("func=auth|in=%s|out=%s|time=%s", self.cdata, ret, response.request_time)
            if self.is_auth:
                xtoken = WsHandler.clients.get(self.token, None)
                if xtoken:
                    oldconn = xtoken.get('conn', None)
                    if oldconn:
                        oldconn._ws_close()
                        log.debug('kick old %s', self.token)
                    xtoken['conn'] = self
                else:
                    WsHandler.clients[self.token] = {"conn": self, "msg_q": []}
                loop = ioloop.IOLoop.current()
                self.msg_push = loop.add_timeout(loop.time() + 1, self._msg_push)
            else:
                self._ws_close()
        except:
            log.warn(traceback.format_exc())
            self._ws_close()

    def on_message(self, message):
        try:
            cdata = json.loads(message)
            if not self._proto_check(cdata):
                log.warn("proto err: %s", cdata)
                #self.close()
                self._ws_close()
                return

            type = cdata.get("type") 
            #认证
            if type == 'auth':
                token = cdata['data'].get('token', None)
                if not token:
                    log.warn("auth not have token")
                    #self.close()
                    self._ws_close()
                    return
                vdata = {"token": token}
                self.token = token
                self.cdata = cdata
                log.debug("url: %s", config.token_verify_url)
                self.httpclient.fetch(config.token_verify_url, self.auth_ret, method='POST', body=urllib.urlencode(vdata), 
                    connect_timeout=config.connect_timeout, request_timeout=config.request_timeout)

            #推送inspect应答
            elif type == 'inspect':
                self._ack_handler(cdata)
            #推送train应答
            elif type == 'train':
                self._ack_handler(cdata)
        except:
            log.warning(traceback.format_exc())
            #self.close()
            self._ws_close()
        
    def on_close(self):
        # 客户端主动关闭
        #del WsHandler.clients[self.dev]
        self._close_pre()
        self.close()
        log.info("func=close|dev=%s|stay=%d", self.dev, int(time.time()) * 1000000 - self.connect_time)

    def on_pong(self, data):
        log.info("func=pong|data=%s", data)
 
if __name__ == '__main__':
    app = tornado.web.Application(
        handlers=[
            (r"/v1/msg/push", PushHandler),
            (r"/v1/msg/wait", WsHandler)
        ],
        debug = False,
    )
    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(config.port, address=config.host)
    log.info("server start")
    tornado.ioloop.IOLoop.instance().start()
