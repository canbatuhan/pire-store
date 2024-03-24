import pickledb
import struct
from typing import Tuple

MODE = "<8sH" # Little endian (8-byte string | 2-byte uint)

class LocalDatabase:
    def __init__(self, path:str) -> None:
        self.__db   = pickledb.load(path, False)
        self.__size = len(self.__db.getall())

    def start(self) -> None:
        pass

    def get_size(self) -> int:
        return self.__size

    def create(self, key:str, value:str) -> bool:
        entry = struct.pack(MODE, value.encode(), 0)
        self.__db.set(key, entry.decode())
        self.__size += 1
        return True

    def read(self, key:str) -> Tuple[bool,str,int]:
        entry = self.__db.get(key)
        if not entry: # Key does not exist
            return False, "", -1
        entry = entry.encode()
        value, version = struct.unpack(MODE, entry)
        value = value.decode().rstrip("\x00")
        return True, value, version

    def validate(self, key:str, value:str, version:int) -> bool:
        entry = struct.pack(MODE, value.encode(), version)
        self.__db.set(key, entry.decode())
        return True

    def update(self, key:str, value:str) -> bool:
        entry = entry.encode()
        _, version = struct.unpack(MODE, entry)
        new_entry  = struct.pack(MODE, value.encode(), version+1)
        self.__db.set(key, new_entry.decode())
        return True

    def delete(self, key:str) -> bool:
        self.__db.rem(key)
        self.__size -= 1
        return True