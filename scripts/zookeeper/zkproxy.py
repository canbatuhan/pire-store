import json

from flask import Flask, request, Response

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError, NodeExistsError

proxy = Flask(__name__)


class ZooKeeperProxy:
    def __init__(self) -> None:
        self.__zk = KazooClient(hosts="127.0.0.1:2181", read_only=False)
        self.__zk.start()
        self.__zk.ensure_path("/store")
        self.__zk.stop()

    def set(self, key, value):
        self.__zk.start()
        try:
            self.__zk.sync("/store/{}".format(key))
            self.__zk.set("/store/{}".format(key), value.encode())
            self.__zk.sync("/store/{}".format(key))
            self.__zk.stop()
        except NoNodeError:
            self.__zk.sync("/store/{}".format(key))
            self.__zk.create("/store/{}".format(key), value.encode())
            self.__zk.sync("/store/{}".format(key))
            self.__zk.stop()

    def get(self, key):
        self.__zk.start()
        try:
            self.__zk.sync("/store/{}".format(key))
            value, stat = self.__zk.get("/store/{}".format(key))
            self.__zk.sync("/store/{}".format(key))
            self.__zk.stop()
            return value.decode(), stat.version
        except NoNodeError:
            self.__zk.stop()
            return -1, -1
        
    def rem(self, key):
        self.__zk.start()
        try:
            self.__zk.sync("/store/{}".format(key))
            self.__zk.delete("/store/{}".format(key))
            self.__zk.sync("/store/{}".format(key))
            self.__zk.stop()
        except:
            self.__zk.stop()
        

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
        host = "0.0.0.0",
        port = 9000)