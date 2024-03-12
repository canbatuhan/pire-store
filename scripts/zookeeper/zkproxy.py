import json

from flask import Flask, request, Response

from kazoo.client import KazooClient
from kazoo.retry import KazooRetry
from kazoo.exceptions import NodeExistsError

proxy = Flask(__name__)

class ZooKeeperProxy:
    def __init__(self) -> None:
        self.__zk = KazooClient(hosts="127.0.0.1:2181", read_only=False)

    def start(self):
        self.__zk.start()
        self.__zk.ensure_path("/store")
        self.__zk.stop()

    def set(self, key, value):
        try:
            self.__zk.start()
            self.__zk.create("/store/{}".format(key), value.encode())
        except NodeExistsError:
            self.__zk.set("/store/{}".format(key), value.encode())
        self.__zk.stop()

    def get(self, key):
        self.__zk.start()
        value, stat = self.__zk.get("/store/{}".format(key))
        self.__zk.stop()
        return value.decode(), stat.version
        
    def rem(self, key):
        self.__zk.start()
        self.__zk.delete("/store/{}".format(key))
        self.__zk.stop()

ZK_PROXY = ZooKeeperProxy()
try:
    ZK_PROXY.start()
except Exception as e:
    print(e.with_traceback(None))

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