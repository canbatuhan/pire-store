import numpy as np
import pandas as pd
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-store", type=str, required=True)
parser.add_argument("-read", type=float, required=True)
args = vars(parser.parse_args())

STORE = args["store"]
READ = args["read"]

NUM_OF_REQUESTS = 10000

HOSTS = [
    "192.168.1.120",
    "192.168.1.121",
    "192.168.1.122",
    "192.168.1.123",
    "192.168.1.124",
]

URLS = {
    "etcd": {
        "set": "/v3/kv/put",
        "get": "/v3/kv/range",
        "rem": "/v3/kv/deleterange"
    },
    "zk": {
        "set": "/zookeeper/store/set",
        "get": "/zookeeper/store/get",
        "rem": "/zookeeper/store/rem"
    },
    "pire": {
        "set": "store/set",
        "get": "store/get",
        "rem": "store/rem"
    }
}

PORTS = {
    "etcd": 2379,
    "zk": 9000,
    "pire": 9000
}

NUM_OF_SET = int(NUM_OF_REQUESTS * (2/3) * (1-READ))
NUM_OF_GET = int(NUM_OF_REQUESTS * READ)
NUM_OF_REM = NUM_OF_REQUESTS - NUM_OF_SET - NUM_OF_GET

print(NUM_OF_SET, NUM_OF_GET, NUM_OF_REM)

set_data = np.array([
    [random.choice(HOSTS),
     PORTS.get(STORE),
     URLS.get(STORE).get("set"),
     np.random.randint(1000, NUM_OF_REQUESTS),
     np.random.randint(1000, NUM_OF_REQUESTS)
     ] for _ in range(NUM_OF_SET)
])

get_data = np.array([
    [random.choice(HOSTS),
     PORTS.get(STORE),
     URLS.get(STORE).get("get"),
     np.random.randint(1000, NUM_OF_REQUESTS),
     np.random.randint(1000, NUM_OF_REQUESTS)
     ] for _ in range(NUM_OF_GET)
])

rem_data = np.array([
    [random.choice(HOSTS),
     PORTS.get(STORE),
     URLS.get(STORE).get("rem"),
     np.random.randint(1000, NUM_OF_REQUESTS),
     np.random.randint(1000, NUM_OF_REQUESTS)
     ] for _ in range(NUM_OF_REM)
])

data = np.concatenate((set_data, get_data, rem_data), axis=0)
np.random.shuffle(data)

data_frame = pd.DataFrame(data)
data_frame.to_csv(
    "{}_{}_read_case.csv".format(STORE, str(int(READ*100))),
    header=["host", "port", "url", "key", "value"],
    sep=",", index=False)