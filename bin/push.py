#coding: utf-8
import os, sys
import urllib, urllib2

def push():
    url = "http://127.0.0.1:8011/v1/msg/push"
    x = {"dev": "98:D3:32:70:DB:75", "msg": "rinidaye"}

    post_data = urllib.urlencode(x)
    re = urllib2.urlopen(url, post_data)
    s = re.read()
    print s

if __name__ == '__main__':
    push()
