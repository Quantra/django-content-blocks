import pytest

import content_blocks
from content_blocks.apps import ContentBlocksConfig
from content_blocks.cache import cache
from content_blocks.services.content_block import CacheServices


class TestContentBlocksConfig:
    @pytest.fixture
    def content_blocks_config(self):
        return ContentBlocksConfig("content_blocks", content_blocks)

    @pytest.mark.django_db
    def test_ready(
        self, text_content_block, content_blocks_config, content_block_collection
    ):
        # Content blocks should be cached on start
        cache_key = CacheServices.cache_key(text_content_block)

        content_block_collection.content_blocks.add(text_content_block)

        assert cache.get(cache_key) is None

        content_blocks_config.ready()

        assert cache.get(cache_key) is not None

    @pytest.mark.django_db
    def test_ready_cache_disabled(
        self,
        text_content_block,
        content_blocks_config,
        settings,
        content_block_collection,
    ):
        settings.CONTENT_BLOCKS_DISABLE_CACHE = True

        cache_key = CacheServices.cache_key(text_content_block)

        content_block_collection.content_blocks.add(text_content_block)

        assert cache.get(cache_key) is None

        content_blocks_config.ready()

        assert cache.get(cache_key) is None

    @pytest.mark.django_db
    def test_ready_cache_on_start_disabled(
        self,
        text_content_block,
        content_blocks_config,
        settings,
        content_block_collection,
    ):
        settings.CONTENT_BLOCKS_DISABLE_CACHE_ON_START = True

        cache_key = CacheServices.cache_key(text_content_block)

        content_block_collection.content_blocks.add(text_content_block)

        assert cache.get(cache_key) is None

        content_blocks_config.ready()

        assert cache.get(cache_key) is None
