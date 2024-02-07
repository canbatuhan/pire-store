import argparse
import yaml

from pire.http.server import PireStoreHttpServer
from pire.rpc.server  import PireStoreRpcServer

parser = argparse.ArgumentParser()
parser.add_argument("-config", default="./docs/node-00.yaml", type=str)
args = vars(parser.parse_args())

CONFIG_FILE = yaml.safe_load(open(args["config"], "r"))

class Runner:
    def __init__(self, config:dict) -> None:
        self.__config = config

    def run(self) -> None:
        PireStoreRpcServer(self.__config).start()
        PireStoreHttpServer(self.__config).start()
        
if __name__ == "__main__":
    Runner(CONFIG_FILE).run()