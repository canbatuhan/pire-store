import json
import argparse

from flask import Flask, request, Response

from kazoo.client import KazooClient
from kazoo.retry import KazooRetry
from kazoo.exceptions import NodeExistsError

parser = argparse.ArgumentParser()
parser.add_argument("-host", required=True, type=str)
parser.add_argument("-port", required=True, type=int)
args = vars(parser.parse_args())

HOST = args["host"]
PORT = args["port"]

proxy = Flask(__name__)

class ZooKeeperProxy:
    def __init__(self) -> None:
        self.__zk = KazooClient("127.0.0.1:2181", read_only=False)
        self.__retry = KazooRetry(max_tries=5, ignore_expire=False)

    def start(self):
        self.__zk.start()
        self.__zk.ensure_path("/kv/store")

    def set(self, key, value):
        try:
            self.__retry(self.__zk.create, "/kv/store/{}".format(key), value.encode())
        except NodeExistsError:
            self.__retry(self.__zk.set, "/kv/store/{}".format(key), value.encode())
        except Exception:
            pass

    def get(self, key):
        try:
            value, stat = self.__retry(self.__zk.get, "/kv/store/{}".format(key))
            return value.decode(), stat.version
        except Exception:
            return None, None
        
    def rem(self, key):
        try:
            self.__retry(self.__zk.delete, "/kv/store/{}".format(key))
            return True
        except Exception:
            return False

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
        host = HOST,
        port = PORT)