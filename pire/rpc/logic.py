import copy
import random
from typing import Dict, List, Tuple

import grpc

from pire.rpc.service       import pirestore_pb2
from pire.rpc.service       import pirestore_pb2_grpc
from pire.util.statemachine import ReplicatedStateMachine, Event
from pire.util.database     import LocalDatabase
from pire.util.protocols    import PireStoreProtocols
from pire.util.logger       import PireStoreLogger

class PireStoreServiceLogics:
    LOGGER:PireStoreLogger = PireStoreLogger("RPC-Server-Logician")
    
    def __init__(self, config:dict) -> None:
        # Identity
        self.__ALIAS = config.get("alias")

        # RPC Server Configurations
        rpc_cfg:Dict = config.get("servers").get("rpc")
        self.__RPC_SERVER_HOST = rpc_cfg.get("host")
        self.__RPC_SERVER_PORT = rpc_cfg.get("port")

        # Neighbour Configurations
        neighbours_cfg:List[Dict] = rpc_cfg.get("neighbours")
        self.__neighbours:List[Tuple[str,int]] = list()
        for each in neighbours_cfg:
            addr = each.get("host"), each.get("port")
            self.__neighbours.append(addr)

        # Owner map stores which neighbours stores the variables in this node
        self.__stub_map:Dict[str, pirestore_pb2_grpc.PireStoreStub] = dict()
        self.__owner_map:Dict[str, List[str]] = dict()

        # Protocol Configurations
        protocol_cfg:Dict = config.get("protocol")
        self.__REPLICAS = protocol_cfg.get("replicas")

        # Database Configurations
        db_cfg:Dict = protocol_cfg.get("database")
        database = LocalDatabase(db_cfg.get("path"))

        # State Machine Configurations
        statemachine_cfg:Dict = protocol_cfg.get("statemachine")
        self.__sample_statemachine = ReplicatedStateMachine(
            statemachine_cfg.get("min_poll_time"),
            statemachine_cfg.get("max_poll_time"))
        self.__statemachine_map:Dict[str, ReplicatedStateMachine] = dict()
        
        # Protocol instance
        self.__PROTOCOLS = PireStoreProtocols(database, self.__REPLICAS)

    def __get_statemachine(self, key:str) -> ReplicatedStateMachine:
        statemachine = self.__statemachine_map.get(key)
        if statemachine == None: # Create if not exists
            statemachine = copy.deepcopy(self.__sample_statemachine)
            statemachine.start()
            self.__statemachine_map.update({key: statemachine})
        return statemachine

    def __get_random_stub(self, neighbours:List[str], visited:List[str]) -> Tuple[str, int]:
        random.shuffle(list(neighbours))
        for alias in neighbours:
            if alias not in visited:
                return alias, self.__stub_map.get(alias)
        return None, None
    
    def __set_owner(self, key:str, owner:str) -> None:
        owners = self.__owner_map.get(key)
        if owners == None: # First owner of the variable
            self.__owner_map.update({key : [owner]})
        else: # Owner already exists
            owners.append(owner)

    def __remove_owner(self, key:str, owner:str) -> None:
        owners = self.__owner_map.get(key)
        if owners != None:
            try:
                owners.remove(owner)
                if len(owners) == 0:
                    self.__owner_map.pop(key)
                    return True # is the last one
            except Exception as e:
                pass

    def start(self):
        for host, port in self.__neighbours:
            try: # Send greetings
                stub  = pirestore_pb2_grpc.PireStoreStub(
                    grpc.insecure_channel("{}:{}".format(host, port)))
                request = pirestore_pb2.GreetMsg(
                    sender=pirestore_pb2.Address(
                        host=self.__RPC_SERVER_HOST,
                        port=self.__RPC_SERVER_PORT),
                    alias=self.__ALIAS)
                response = stub.Greet(request)
                self.__stub_map.update({response.alias : stub})

            except Exception as e:
                self.LOGGER.log(e.with_traceback(None))
        

    def Greet_ServiceLogic(self, request:pirestore_pb2.GreetMsg) -> pirestore_pb2.GreetAck:
        stub  = pirestore_pb2_grpc.PireStoreStub(
            grpc.insecure_channel("{}:{}".format(
                request.sender.host, request.sender.port)))
        self.__stub_map.update({request.alias : stub})
        return pirestore_pb2.GreetAck(alias=self.__ALIAS)

    def ISet_ServiceLogic(self, request:pirestore_pb2.SetReq) -> pirestore_pb2.SetAck:
        request.visited.extend([self.__ALIAS])

        try: # Set the state as `WRITING`
            machine = self.__get_statemachine(request.key)
            machine.poll_and_trigger(Event.WRITE)

            if request.sender != "": # Remember the owner (sending neighbour)
                self.__set_owner(request.key, request.sender)
            
            # Initializations before the protocol
            request.origin = False
            request.sender = self.__ALIAS
            local_work = True

            while request.replica < self.__REPLICAS: # Run until the criteria is met
                alias, stub = self.__get_random_stub(self.__stub_map.keys(), request.visited)
                if not local_work and stub == None:
                    break # No neighbours to visit nor a local work to do
                
                # Initiate protocol
                replica  = request.replica
                response = self.__PROTOCOLS.iset_protocol(local_work, request, stub)
                
                if local_work and alias != None:
                    if response.replica == replica: # Local work failed!
                        break # If local work fails, no need to envoke neighbours
                    elif response.replica > replica+1: # Remember the owner (receiving neighbour)
                        self.__set_owner(request.key, alias)

                elif alias != None: # No local work to do, but neighbours to visit
                    if response.replica > replica: # Remember the owner (receiving neighbour)
                        self.__set_owner(request.key, alias)
                
                if local_work == True: # For the first iteration
                    machine.trigger(Event.DONE) # After local work, turn back to 'IDLE'
                    local_work = False # No need to do local work after the first iteration
                request    = response # Re-arrange the request

        except Exception as e:
            self.LOGGER.log(e.with_traceback(None))

        # Set the state as 'IDLE', just in case
        machine.trigger(Event.DONE)
        return pirestore_pb2.SetAck(
            ack     = request.replica,
            visited = request.visited)

    def Set_ServiceLogic(self, request:pirestore_pb2.SetReq) -> pirestore_pb2.SetAck:
        request.visited.extend([self.__ALIAS])

        try: # Set the state as `WRITING`
            machine = self.__get_statemachine(request.key)
            machine.poll_and_trigger(Event.WRITE)

            if request.sender != "": # Remember the owner (sending neighbour)
                self.__set_owner(request.key, request.sender)
            
            # Initializations before the protocol
            request.origin = False
            request.sender = self.__ALIAS

            def set_service_loop(local_work, request, neighbours):
                while request.replica < self.__REPLICAS: # Run until the criteria is met
                    alias, stub = self.__get_random_stub(neighbours, request.visited)
                    if not local_work and alias == None:
                        break # No neighbours to visit nor a local work to do

                    # Initiate protocol
                    request = self.__PROTOCOLS.set_protocol(local_work, request, stub)
                    if local_work == True: # For the first iteration
                        machine.trigger(Event.DONE) # After local work, turn back to 'IDLE'
                        local_work = False # No need to do local work after the first iteration
                return request
            
            # Check owners
            owners = self.__owner_map.get(request.key)
            if owners != None: # Owners exist
                request = set_service_loop(True, request, owners)
            else: # No owners exist, no need for any local work
                request = set_service_loop(False, request, self.__stub_map.keys())

        except Exception as e:
            self.LOGGER.log(e.with_traceback(None))

        # Set the state as 'IDLE'
        machine.trigger(Event.DONE)
        return pirestore_pb2.SetAck(
            ack     = request.replica,
            visited = request.visited)

    def Get_ServiceLogic(self, request:pirestore_pb2.GetReq) -> pirestore_pb2.GetAck:
        request.visited.extend([self.__ALIAS])

        try: # Set the state as `READING`
            machine = self.__get_statemachine(request.key)
            machine.poll_and_trigger(Event.READ)

            def get_service_loop(local_work, request, neighbours):
                response = pirestore_pb2.GetAck(
                    success = False,
                    value   = "",
                    visited = request.visited)
                
                while not response.success: # Run until the criteria is met
                    address, stub = self.__get_random_stub(neighbours, request.visited)
                    if not local_work and address == None:
                        break # No neighbours to visit nor a local work to do

                     # Initiate protocol
                    request, response = self.__PROTOCOLS.get_protocol(local_work, request, stub)
                    if local_work == True: # For the first iteration
                        machine.trigger(Event.DONE) # After local work, turn back to 'IDLE'
                        local_work = False # No need to do local work after the first iteration
                return request, response

            # Check owners
            owners = self.__owner_map.get(request.key)
            if owners != None: # Owners exist
                _, response = get_service_loop(True, request, owners)
            else: # No owners exist, no need for any local work
                _, response = get_service_loop(False, request, self.__stub_map.keys())

            # Set the state as 'IDLE', just in case
            machine.trigger(Event.DONE)
            return pirestore_pb2.GetAck(
                success = response.success,
                value   = response.value,
                visited = response.visited)

        except Exception as e:
            self.LOGGER.log(e.with_traceback(None))
            # Set the state as 'IDLE'
            machine.trigger(Event.DONE)
            return pirestore_pb2.GetAck(
                success = False,
                value   = "",
                visited = request.visited)

    def Val_ServiceLogic(self, request:pirestore_pb2.ValReq) -> pirestore_pb2.ValAck:
        try: # Set the state as `WRITING`
            machine = self.__get_statemachine(request.key)
            machine.poll_and_trigger(Event.WRITE)

            # Directly envoke 'Validate' service
            request = self.__PROTOCOLS.val_protocol(request)

        except Exception as e:
            self.LOGGER.log(e.with_traceback(None))

        # Set the state as 'IDLE'
        machine.trigger(Event.DONE)
        return pirestore_pb2.ValAck(
            value   = request.value,
            version = request.version)

    def Rem_ServiceLogic(self, request:pirestore_pb2.RemReq) -> pirestore_pb2.RemAck:
        request.visited.extend([self.__ALIAS])
        
        try: # Set the state as `WRITING`
            machine = self.__get_statemachine(request.key)
            machine.poll_and_trigger(Event.WRITE)

            if request.sender != "": # Forget the owner (sending neighbour)
                is_last_one = self.__remove_owner(request.key, request.sender)
            
            # Initializations before the protocol
            request.sender = self.__ALIAS

            def rem_service_loop(local_work, request, neighbours):
                while request.replica < self.__REPLICAS: # Run until the criteria is met
                    alias, stub = self.__get_random_stub(neighbours, request.visited)
                    if not local_work and alias == None:
                        break # No neighbours to visit nor a local work to do
                    
                    # Initiate protocol
                    replica  = request.replica
                    response = self.__PROTOCOLS.rem_protocol(local_work, request, stub) 

                    if local_work and alias != None:
                        if response.replica == replica: # Local work failed!
                            break # If local work fails, no need to envoke neighbours
                        elif response.replica > replica+1: # Remember the owner (receiving neighbour)
                            self.__remove_owner(request.key, alias)

                    elif alias != None: # No local work to do, but neighbours to visit
                        if response.replica > replica: # Remember the owner (receiving neighbour)
                            self.__remove_owner(request.key, alias)    

                    if local_work == True: # For the first iteration
                        machine.trigger(Event.DONE) # After local work, turn back to 'IDLE'
                        local_work = False # No need to do local work after the first iteration
                    request    = response # Re-arrange the message

                return request

            # Check owners
            owners = self.__owner_map.get(request.key)
            if owners != None: # Owners exist
                request = rem_service_loop(True, request, owners)
            elif is_last_one: # No owners exist, but may be the last owner
                request = rem_service_loop(True, request, [])
            else: # No owners exist, nor the the last owner
                request = rem_service_loop(False, request, self.__stub_map.keys())

        except Exception as e:
            self.LOGGER.log(e.with_traceback(None))

        # Set the state as 'IDLE', just in case
        machine.trigger(Event.DONE)
        return pirestore_pb2.RemAck(
            ack     = request.replica,
            visited = request.visited)
