from importlib import import_module


def __getattr__(name):
    modules = {
        "RedisManager": (".redis_manager", "RedisManager"),
        "RedisUtil": (".redis_util", "RedisUtil"),
        "redis_connection": (".redis_connection", None),
    }
    try:
        module_name, attribute_name = modules[name]
    except KeyError as error:
        raise AttributeError(name) from error
    module = import_module(module_name, __name__)
    return module if attribute_name is None else getattr(module, attribute_name)


__all__ = ["RedisManager", "RedisUtil", "redis_connection"]
