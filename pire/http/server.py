import json
import multiprocessing
from typing import Dict

import grpc
from flask import Flask, request, Response

from pire.rpc.service import pirestore_pb2, pirestore_pb2_grpc
from pire.util.logger import PireStoreLogger

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

class PireStoreHttpServer(multiprocessing.Process):
    SERVER:Flask = Flask(__name__)
    RPC_STUB:pirestore_pb2_grpc.PireStoreStub = None
    LOGGER:PireStoreLogger = PireStoreLogger("HTTP-Server")
    
    def __init__(self, config:dict) -> None:
        super().__init__()

        # HTTP Server Configurations
        http_cfg:Dict = config.get("servers").get("http")
        self.__HTTP_SERVER_HOST = http_cfg.get("host")
        self.__HTTP_SERVER_PORT = http_cfg.get("port")

        # RPC Server Configurations
        rpc_cfg:Dict = config.get("servers").get("rpc")
        self.__RPC_SERVER_HOST = rpc_cfg.get("host")
        self.__RPC_SERVER_PORT = rpc_cfg.get("port")

    @SERVER.route("/store/set", methods=["POST"])
    def set():
        try:
            data:Dict    = request.get_json()
            key          = str(data.get("key"))
            value        = str(data.get("val")) 
            rpc_request  = pirestore_pb2.SetReq(key=key, value=value, replica=0, origin=True, visited=[], sender=None)
            rpc_response = PireStoreHttpServer.RPC_STUB.Set(rpc_request)

        except Exception as e:
            exception_msg = e.with_traceback(None)
            PireStoreHttpServer.LOGGER.log(exception_msg)
            response = json.dumps({"msg": exception_msg})
            return Response(response, status=400)
        
        response = json.dumps({
            "key": key,
            "val": value,
            "rep": rpc_response.ack,
            "msg": "OK."})
        return Response(response, status=200)

    @SERVER.route("/store/get", methods=["POST"])
    def get():
        try:
            data:Dict    = request.get_json()
            key          = str(data.get("key"))
            rpc_request  = pirestore_pb2.GetReq(key=key, visited=[])
            rpc_response = PireStoreHttpServer.RPC_STUB.Get(rpc_request)

        except Exception as e:
            exception_msg = e.with_traceback(None)
            PireStoreHttpServer.LOGGER.log(exception_msg)
            response = json.dumps({"msg": exception_msg})
            return Response(response, status=400)
        
        response = json.dumps({
            "key": key,
            "val": rpc_response.value,
            "suc": rpc_response.success})
        return Response(response, status=200, mimetype="application/json")

    @SERVER.route("/store/rem", methods=["POST"])
    def remove():
        try:
            data:Dict    = request.get_json()
            key          = str(data.get("key")) 
            rpc_request  = pirestore_pb2.RemReq(key=key, replica=0, visited=[], sender=None)
            rpc_response = PireStoreHttpServer.RPC_STUB.Rem(rpc_request)

        except Exception as e:
            exception_msg = e.with_traceback(None)
            PireStoreHttpServer.LOGGER.log(exception_msg)
            response = json.dumps({"msg": exception_msg})
            return Response(response, status=400)
        
        response = json.dumps({
            "key": key,
            "rep": rpc_response.ack,
            "msg": "OK."})
        return Response(response, status=200)

    def run(self):
        # Creating an RPC stub
        PireStoreHttpServer.RPC_STUB = pirestore_pb2_grpc.PireStoreStub(
            grpc.insecure_channel("{}:{}".format(
                self.__RPC_SERVER_HOST, self.__RPC_SERVER_PORT)))
        
        self.SERVER.run(
            threaded = False,
            host = "0.0.0.0",
            port = self.__HTTP_SERVER_PORT)
