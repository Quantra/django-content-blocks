from .base import *  # noqa

CACHES = CACHES.copy()  # noqa
CACHES["content_blocks"] = {
    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    "LOCATION": "content_blocks",
}
CONTENT_BLOCKS_CACHE = "content_blocks"
