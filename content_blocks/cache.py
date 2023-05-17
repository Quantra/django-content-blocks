"""
Content Blocks cache.py
"""
from django.core.cache import caches

from content_blocks.conf import settings

cache = caches[settings.CONTENT_BLOCKS_CACHE]
# todo refactor this into services
