def cached_property(func):
    cached_name = "_cached_{}".format(func)
    sentinel = object()

    def inner(instance):
        cache = getattr(instance, cached_name, sentinel)
        if cache is not sentinel:
            return cache
        result = func(instance)
        setattr(instance, cached_name, result)
        return result

    return property(inner)
