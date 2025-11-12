import json
import base64
import pickle
import zlib

import brotli
import zstandard as zstd


class RedisUtil:
    # ---------- 공통 유틸 ----------
    @staticmethod
    def _ensure_bytes(data: any) -> bytes:
        """bytes | str | (dict/list 등 JSON 직렬화 대상) → bytes"""
        if isinstance(data, (bytes, bytearray, memoryview)):
            return bytes(data)
        if isinstance(data, str):
            return data.encode("utf-8")
        # dict/list 등은 JSON 문자열로 변환
        return json.dumps(data, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _text_or_bytes(raw_bytes: bytes):
        """
        UTF-8로 디코드 후 JSON 여부만 확인하고,
        JSON이면 문자열(str), 아니면 bytes를 반환(기존 zlib 구현과 동일 정책).
        """
        try:
            text = raw_bytes.decode("utf-8")
            # JSON 여부만 확인 (파싱 결과는 버리고 문자열을 반환)
            json.loads(text)
            return text
        except (UnicodeDecodeError, json.JSONDecodeError):
            return raw_bytes

    # ---------- zlib (기존) ----------
    @staticmethod
    def compress_zlib(data: any) -> str:
        raw = RedisUtil._ensure_bytes(data)
        compressed = zlib.compress(raw)
        return base64.b64encode(compressed).decode("utf-8")

    @staticmethod
    def decompress_zlib(encoded: str):
        compressed = base64.b64decode(encoded)
        raw = zlib.decompress(compressed)
        return RedisUtil._text_or_bytes(raw)

    # ---------- zstd ----------
    @staticmethod
    def compress_zstd(data: any, level: int = 3) -> str:
        raw = RedisUtil._ensure_bytes(data)
        cctx = zstd.ZstdCompressor(level=level)
        compressed = cctx.compress(raw)
        return base64.b64encode(compressed).decode("utf-8")

    @staticmethod
    def decompress_zstd(encoded: str):
        compressed = base64.b64decode(encoded)
        dctx = zstd.ZstdDecompressor()
        raw = dctx.decompress(compressed)
        return RedisUtil._text_or_bytes(raw)

    # ---------- brotli ----------
    @staticmethod
    def compress_brotli(data: any, quality: int = 5, mode: str = "text") -> str:
        raw = RedisUtil._ensure_bytes(data)
        # mode: "text" | "font" | "generic"
        mode_map = {"text": brotli.MODE_TEXT, "font": brotli.MODE_FONT, "generic": brotli.MODE_GENERIC}
        compressed = brotli.compress(raw, quality=quality, mode=mode_map.get(mode, brotli.MODE_TEXT))
        return base64.b64encode(compressed).decode("utf-8")

    @staticmethod
    def decompress_brotli(encoded: str):
        compressed = base64.b64decode(encoded)
        raw = brotli.decompress(compressed)
        return RedisUtil._text_or_bytes(raw)

    # # ---------- snappy ----------
    # @staticmethod
    # def compress_snappy(data: any) -> str:
    #     raw = RedisUtil._ensure_bytes(data)
    #     compressed = snappy.compress(raw)
    #     return base64.b64encode(compressed).decode("utf-8")
    #
    # @staticmethod
    # def decompress_snappy(encoded: str):
    #     compressed = base64.b64decode(encoded)
    #     raw = snappy.uncompress(compressed)
    #     return RedisUtil._text_or_bytes(raw)

    # ---------- JSON / Pickle ----------
    @staticmethod
    def json_serialize(data: any) -> str:
        # 객체 → dict 변환 시도
        if hasattr(data, "model_dump"):      # pydantic v2
            data = data.model_dump()
        elif hasattr(data, "dict"):          # pydantic v1
            data = data.dict()
        elif not isinstance(data, (dict, list)):
            data = vars(data)  # 또는 data.__dict__
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def json_deserialize(data: str) -> any:
        return json.loads(data)

    @staticmethod
    def pickle_serialize(data: any) -> bytes:
        return pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def pickle_deserialize(data: bytes) -> any:
        return pickle.loads(data)