from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response


def api_cache(timeout=None):
    if timeout is None:
        timeout = 60*5
        settings_cache = settings.CACHES.get('default')
        if settings_cache:
            timeout = settings_cache.get('TIMEOUT')

    def dec(func):
        def wrapper(*args, **kwargs):
            path = args[1].path
            user = args[1].user.id
            cache_data = cache.get(f'{path}-user-{user}')

            if cache_data:
                return Response(cache_data)
            else:
                res = func(*args, **kwargs)
                cache.set(f'{path}-user-{user}', res.data, timeout)
                return Response(res.data)
        return wrapper
    return dec
