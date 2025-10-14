from pathlib import Path
import json
import pytest
from redis_om import Migrator

from app.v2.model.content import Content
from app.v2.redis import RedisUtil
from app.v2.redis.model import PickleContent, JSONContent

compress = RedisUtil.compress_brotli
decompress = RedisUtil.decompress_brotli

@pytest.fixture
def mock_content():
    data_path = Path(__file__).parent / "../mock_content.json"
    assert data_path.exists(), f"테스트 데이터가 없습니다: {data_path}"
    with data_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Content(**data)


@pytest.fixture
def before_compress(mock_content) -> json:
    """직렬화 결과(json)"""
    return RedisUtil.json_serialize(mock_content)


@pytest.fixture
def before_save(mock_content):
    """
    Redis에 저장하기 직전의 모델 인스턴스.
    """
    jsoned: json = RedisUtil.json_serialize(mock_content)
    b64: str = compress(jsoned)

    model = JSONContent(
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
    instance = JSONContent.get(saved_pk)
    assert instance is not None
    return instance.data


@pytest.fixture
def before_deserialize(before_decompress) -> str:
    raw_json = decompress(before_decompress)
    return raw_json


def test_압축(before_compress):
    s = compress(before_compress)
    assert isinstance(s, str) and len(s) > 0


def test_저장(before_save):
    """저장 후 TTL 설정"""
    before_save.save()
    before_save.expire(10)
    assert before_save.pk is not None


def test_불러오기(mock_content, saved_pk):
    """키워드로 조회 + pk로 단일 조회"""
    # 키워드 검색 (인덱스 필요)
    rows = JSONContent.find(PickleContent.keyword == mock_content.keyword).all()
    assert len(rows) >= 1

    # pk로 가져오기
    inst = JSONContent.get(saved_pk)
    assert inst is not None
    assert isinstance(inst.data, str)  # base64 str


def test_압축_해제(before_decompress):
    raw = decompress(before_decompress)
    assert isinstance(raw, str)
