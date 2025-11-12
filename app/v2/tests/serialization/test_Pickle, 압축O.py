# tests/test_pickle_pipeline.py
from pathlib import Path
import json
import pytest

from app.v2.model.content import Content
from app.v2.redis import RedisUtil
from app.v2.redis.model import PickleContent

@pytest.fixture
def mock_content():
    data_path = Path(__file__).parent / "../mock_content.json"
    assert data_path.exists(), f"테스트 데이터가 없습니다: {data_path}"
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Content(**data)


@pytest.fixture
def before_compress(mock_content) -> bytes:
    """직렬화 결과(bytes)"""
    return RedisUtil.pickle_serialize(mock_content)


@pytest.fixture
def before_save(mock_content):
    """
    Redis에 저장하기 직전의 모델 인스턴스.
    data에는 base64 문자열(압축 후)로 들어갑니다.
    """
    pickled: bytes = RedisUtil.pickle_serialize(mock_content)
    b64: str = RedisUtil.compress_zlib(pickled)  # bytes → (zlib) → base64 str

    model = PickleContent(
        keyword=mock_content.keyword,
        created_at=getattr(mock_content, "created_at", "NA"),
        data=b64,
    )
    return model


@pytest.fixture
def saved_pk(before_save) -> str:
    """실제 저장하고 pk 반환"""
    before_save.save()
    before_save.expire(10)
    return before_save.pk


@pytest.fixture
def before_decompress(saved_pk) -> str:
    """
    압축 해제 직전의 데이터(= base64 문자열).
    """
    instance = PickleContent.get(saved_pk)
    assert instance is not None
    return instance.data  # base64 str


@pytest.fixture
def before_deserialize(before_decompress) -> bytes:
    """
    압축을 해제한 bytes (pickle.loads 직전).
    """
    raw_bytes = RedisUtil.decompress_zlib(before_decompress)  # → bytes
    assert isinstance(raw_bytes, (bytes, bytearray))
    return raw_bytes


def test_직렬화(mock_content):
    """pickle 직렬화는 bytes를 반환해야 함"""
    b = RedisUtil.pickle_serialize(mock_content)
    assert isinstance(b, (bytes, bytearray))


def test_압축(before_compress):
    """압축은 base64 문자열을 반환해야 함(우리 구현 기준)"""
    s = RedisUtil.compress_zlib(before_compress)  # ❌ vars(...) 금지
    assert isinstance(s, str) and len(s) > 0


def test_저장(before_save):
    """저장 후 TTL 설정"""
    before_save.save()
    before_save.expire(10)
    assert before_save.pk is not None


def test_불러오기(mock_content, saved_pk):
    """키워드로 조회 + pk로 단일 조회"""
    # 키워드 검색 (인덱스 필요)
    rows = PickleContent.find(PickleContent.keyword == mock_content.keyword).all()
    assert len(rows) >= 1

    # pk로 가져오기
    inst = PickleContent.get(saved_pk)
    assert inst is not None
    assert isinstance(inst.data, bytes)  # base64 str


def test_압축_해제(before_decompress):
    """base64(str) → zlib 해제 → bytes"""
    raw = RedisUtil.decompress_zlib(before_decompress)
    assert isinstance(raw, (bytes, bytearray))


def test_역직렬화(before_deserialize):
    """bytes → pickle.loads → 객체"""
    obj = RedisUtil.pickle_deserialize(before_deserialize)
    # 최소 필드 체크 (예: title 존재)
    assert hasattr(obj, "content") or isinstance(obj, Content)