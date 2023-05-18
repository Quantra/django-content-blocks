"""
Content Blocks test_cache.py
"""
import pytest
from django.core.cache import caches

from content_blocks.conf import settings
from content_blocks.services.content_block import cache


class TestCache:
    def test_cache_setting_default(self):
        if "content_blocks" in settings.CACHES.keys():
            pytest.skip("skipping because --ds config.settings.test_cache_setting used")

        assert cache == caches["default"]

    def test_cache_setting_option(self):
        if "content_blocks" not in settings.CACHES.keys():
            pytest.skip(
                "skipping because --ds config.settings.test_cache_setting not used"
            )

        assert cache == caches["content_blocks"]
