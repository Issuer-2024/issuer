import base64
import json
import pickle
import zlib
from typing import Any


class RedisUtil:
    @staticmethod
    def compress_data(data: Any) -> str:
        json_data = json.dumps(data)
        compressed_data = zlib.compress(json_data.encode('utf-8'))
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        return base64_data

    @staticmethod
    def decompress_data(base64_data: str) -> Any:
        compressed_data = base64.b64decode(base64_data)
        decompressed_data = zlib.decompress(compressed_data).decode('utf-8')
        return json.loads(decompressed_data)

    @staticmethod
    def pickle_serialize(data: Any) -> bytes:
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def pickle_deserialize(data: bytes) -> Any:
        return pickle.loads(data)
