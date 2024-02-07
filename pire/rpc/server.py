from concurrent import futures
import multiprocessing
from typing import Dict

import grpc

from pire.rpc.service       import pirestore_pb2
from pire.rpc.service       import pirestore_pb2_grpc
from pire.rpc.logic         import PireStoreServiceLogics
from pire.util.logger       import PireStoreLogger

class PireStoreRpcServer(multiprocessing.Process, pirestore_pb2_grpc.PireStoreServicer):
    LOGGER:PireStoreLogger = PireStoreLogger("RPC-Server-Logician")

    def __init__(self, config:dict) -> None:
        multiprocessing.Process.__init__(self)
        self.__logician = PireStoreServiceLogics(config)

        # RPC Server Configurations
        rpc_cfg:Dict = config.get("servers").get("rpc")
        self.__RPC_SERVER_HOST = rpc_cfg.get("host")
        self.__RPC_SERVER_PORT = rpc_cfg.get("port")
        self.__MAX_WORKERS     = rpc_cfg.get("workers")
    
    """ RPC Service Implementations """

    def Greet(self, request, context) -> pirestore_pb2.GreetAck:
        return self.__logician.Greet_ServiceLogic(request)

    def ISet(self, request, context) -> pirestore_pb2.SetAck:
        return self.__logician.ISet_ServiceLogic(request) 

    def Set(self, request, context) -> pirestore_pb2.SetAck:
        is_origin = request.origin
        response  = self.__logician.Set_ServiceLogic(request)
        if is_origin and response.ack == request.replica:
            request.sender = ""
            del request.visited[:]
            response = self.__logician.ISet_ServiceLogic(request)
        return response

    def Get(self, request, context) -> pirestore_pb2.GetAck:
        return self.__logician.Get_ServiceLogic(request)

    def Val(self, request, context) -> pirestore_pb2.ValAck:
        return self.__logician.Val_ServiceLogic(request)

    def Rem(self, request, context) -> pirestore_pb2.RemAck:
        return self.__logician.Rem_ServiceLogic(request)
    

    """ Runners """

    def run(self):
        # RPC Server Declarations
        self.__rpc_server = grpc.server(thread_pool=futures.ThreadPoolExecutor(max_workers=self.__MAX_WORKERS))
        pirestore_pb2_grpc.add_PireStoreServicer_to_server(self, self.__rpc_server)
        self.__rpc_server.add_insecure_port("127.0.0.1:{}".format(self.__RPC_SERVER_PORT))
        
        # Running the server
        self.__rpc_server.start()
        self.__logician.start()
        
        # Infinite loop
        self.__rpc_server.wait_for_termination()