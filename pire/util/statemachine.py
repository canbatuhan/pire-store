from enum import Enum
import time
from smpai.fsm import FiniteStateMachine

SM_CONFIG_PATH = "./resource/statemachine.json"

class Event(Enum):
    START = "START"
    END   = "END"
    READ  = "READ"
    WRITE = "WRITE"
    DONE  = "DONE"

class PollingTimeout(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class ReplicatedStateMachine:
    def __init__(self, min_poll_time:float, max_poll_time:float) -> None:
        self.__machine     = FiniteStateMachine(SM_CONFIG_PATH)
        self.__MIN_POLL_TIME = min_poll_time
        self.__MAX_POLL_TIME = max_poll_time

    def start(self) -> None:
        self.__machine.start() # Start machine -> INIT
        self.trigger(Event.START) # INIT -> IDLE

    def __check(self, event:Event) -> bool:
        return self.__machine.check_event(event.value)

    def poll(self, event:Event) -> None:
        wait_time = self.__MIN_POLL_TIME
        while not self.__check(event):
            time.sleep(wait_time)
            wait_time *= 2
            if wait_time >= self.__MAX_POLL_TIME:
                raise PollingTimeout("Polling timeout occured for Event : {}.".format(event.value))

    def trigger(self, event:Event) -> bool:
        self.__machine.send_event(event.value)
        return True
    
    def poll_and_trigger(self, event:Event) -> bool:
        self.poll(event)
        return self.trigger(event)

    def end(self) -> None:
        self.trigger(Event.END) # IDLE -> S_FINAL