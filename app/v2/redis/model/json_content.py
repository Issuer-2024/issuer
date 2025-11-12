from redis_om import Field, JsonModel

from app.v2.model.content import Content


class JSONContent(JsonModel):
    keyword: str = Field(index=True)
    created_at: str = Field(index=True)
    data: str

    def savef(self, compress_func, *args, **kwargs):
        self.data = compress_func(self.data)
        super().save(*args, **kwargs)

    @classmethod
    def get_decompressed(cls, pk: str, deserialize_func, decompress_func):
        # 압축을 해제하여 데이터를 가져옵니다.
        instance = cls.get(pk)
        instance.data = deserialize_func(decompress_func(instance.data))

        return instance
