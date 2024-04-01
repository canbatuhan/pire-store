import threading
from typing import Tuple

from pire.rpc.service   import pirestore_pb2
from pire.rpc.service   import pirestore_pb2_grpc
from pire.util.database import LocalDatabase
from pire.util.logger   import PireStoreLogger

class PireStoreProtocols:
    LOGGER:PireStoreLogger = PireStoreLogger("Pire-Protocols")

    def __init__(self, database:LocalDatabase, replicas:int) -> None:
        self.__database = database
        self.__replicas = replicas
    
    def __validate_thread(self, stub, key, value, version):
        try: # Call 'Validate'
            validate_request = pirestore_pb2.ValReq(
                key=key, value=value, version=version)
            validate_response = stub.Val(validate_request)
            
            # Eventual consistency!
            if validate_response.version > version:
                self.__database.validate(validate_request.key,
                                         validate_response.value,
                                         validate_response.version)
                
        except Exception:
            pass

    def iset_protocol(
            self,
            local_work:bool,
            request:pirestore_pb2.SetReq,
            stub:pirestore_pb2_grpc.PireStoreStub
        ) -> pirestore_pb2.SetReq:

        def extend_protocol(
                request:pirestore_pb2.SetReq,
                stub:pirestore_pb2_grpc.PireStoreStub
            ) -> pirestore_pb2.SetReq:
            try: # Call 'ISet'
                response = stub.ISet(request)
                if response.ack > request.replica:
                    request.replica = response.ack
                del request.visited[:]
                request.visited.extend(response.visited)
            except Exception as e:
                self.LOGGER.log(e.with_traceback(None))
            return request
        
        if local_work: # Do local work, then extend the protocol if necessary
            success = self.__database.create(request.key, request.value)
            if success: # Variable created in the local database
                request.replica += 1 # Protocol might be extend
                if request.replica < self.__replicas and stub != None:
                    request = extend_protocol(request, stub)

        elif stub != None: # Extend the protocol (stub != None, for this case)
            request = extend_protocol(request, stub)

        # Return updated request
        return request

    def set_protocol(
            self,
            local_work:bool,
            request:pirestore_pb2.SetReq,
            stub:pirestore_pb2_grpc.PireStoreStub
        ) -> pirestore_pb2.SetReq:
        if local_work: # Do local work
            success = self.__database.update(request.key, request.value)
            if success: # Variable updated in the local database
                request.replica += 1
            
        # Extend the protocol, if necessary
        if request.replica < self.__replicas and stub != None:
            try: # Call 'Set'
                response = stub.Set(request)
                if response.ack > request.replica:
                    request.replica = response.ack
                del request.visited[:]
                request.visited.extend(response.visited)
            except Exception as e:
                self.LOGGER.log(e.with_traceback(None))

        # Return updated request
        return request

    def get_protocol(
            self,
            local_work:bool,
            request:pirestore_pb2.GetReq,
            stub:pirestore_pb2_grpc.PireStoreStub
        ) -> Tuple[pirestore_pb2.GetReq, pirestore_pb2.GetAck]:
        if local_work: # Do local work
            success, value, version = self.__database.read(request.key)
            
            if success: # Validate the pair in a thread and return

                # Validate in a thread
                threading.Thread(target=self.__validate_thread, args=(stub, request.key, value, version)).start()

                # Pair is found and sent to validation, return
                return request, pirestore_pb2.GetAck(
                    success = True,
                    value   = value,
                    visited = request.visited)
        
        # Could not find the pair locally, extend the protocol
        try: # Call 'Get'
            response = stub.Get(request)
            del request.visited[:]
            request.visited.extend(response.visited)

        except Exception as e:
            self.LOGGER.log(e.with_traceback(None))
            response = pirestore_pb2.GetAck(success=False, visited=request.visited)

        return request, response

    def val_protocol(
            self,
            request:pirestore_pb2.ValReq
        ) -> pirestore_pb2.ValReq:
        # Read value and version, check eventual consistency
        _, value, version = self.__database.read(request.key)
        if request.version > version:
            self.__database.validate(
                request.key, request.value, request.version)
            return request # Return the request as it is
        
        # Return pair info to update
        return pirestore_pb2.ValReq(
            key     = request.key,
            value   = value,
            version = version)

    def rem_protocol(
            self,
            local_work:bool,
            request:pirestore_pb2.RemReq,
            stub:pirestore_pb2_grpc.PireStoreStub
        ) -> pirestore_pb2.RemAck:
        if local_work: # Do local work
            success = self.__database.delete(request.key)
            if success: # Variable remove in the local database
                request.replica += 1
            
        # Extend the protocol, if necessary
        if request.replica < self.__replicas and stub != None:
            try: # Try to call 'Rem'
                response = stub.Rem(request)
                if response.ack > request.replica:
                    request.replica = response.ack
                del request.visited[:]
                request.visited.extend(response.visited)

            except Exception as e:
                self.LOGGER.log(e.with_traceback(None))
                
        # Return updated request
        return request
    