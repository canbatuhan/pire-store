import json

from flask import Flask, request, Response

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError, NodeExistsError

proxy = Flask(__name__)

TIMEOUT = 0.05 # seconds

class ZooKeeperProxy:
    def __init__(self) -> None:
        self.__zk = KazooClient(hosts="127.0.0.1:2181", read_only=False, timeout=TIMEOUT)
        self.__zk.start()
        self.__zk.ensure_path("/store")

    def set(self, key, value):
        try:
            self.__zk.start(TIMEOUT)
            self.__zk.set("/store/{}".format(key), value.encode())
            self.__zk.sync("/store/{}".format(key))
        except NoNodeError:
            self.__zk.create("/store/{}".format(key), value.encode())
            self.__zk.sync("/store/{}".format(key))

    def get(self, key):
        value, stat = self.__zk.get("/store/{}".format(key))
        self.__zk.sync("/store/{}".format(key))
        return value.decode(), stat.version
        
    def rem(self, key):
        try:
            self.__zk.delete("/store/{}".format(key))
            self.__zk.sync("/store/{}".format(key))
        except NoNodeError:
            pass

ZK_PROXY = ZooKeeperProxy()

@proxy.route("/zookeeper/store/set", methods=["POST"])
def set():
    try:
        data  = request.get_json()
        key   = str(data.get("key"))
        value = str(data.get("value"))
        ZK_PROXY.set(key, value)

    except Exception as e:
        return Response(
            json.dumps({"msg": e.with_traceback(None)}),
            status=400)
    
    return Response(
        json.dumps({
            "key": key,
            "value": value,
            "msg": "OK."}),
        status=200)

@proxy.route("/zookeeper/store/get", methods=["POST"])
def get():
    try:
        data  = request.get_json()
        key   = str(data.get("key"))
        value, version = ZK_PROXY.get(key)

    except Exception as e:
        return Response(
            json.dumps({"msg": e.with_traceback(None)}),
            status=400)
    
    return Response(
        json.dumps({
            "key": key,
            "value": value,
            "version": version,
            "msg": "OK."}),
        status=200)

@proxy.route("/zookeeper/store/rem", methods=["POST"])
def rem():
    try:
        data    = request.get_json()
        key     = str(data.get("key"))
        success = ZK_PROXY.rem(key)

    except Exception as e:
        return Response(
            json.dumps({"msg": e.with_traceback(None)}),
            status=400)
    
    return Response(
        json.dumps({
            "key": key,
            "success": success,
            "msg": "OK."}),
        status=200)

if __name__ == "__main__":
    proxy.run(
        threaded = True,
        host = "0.0.0.0",
        port = 9000)