import pytest

import content_blocks
from content_blocks.apps import ContentBlocksConfig
from content_blocks.cache import cache


class TestContentBlocksConfig:
    @pytest.fixture
    def content_blocks_config(self):
        return ContentBlocksConfig("content_blocks", content_blocks)

    @pytest.mark.django_db
    def test_ready(self, text_content_block, content_blocks_config):
        # Content blocks should be cached on start
        assert cache.get(text_content_block.cache_key) is None

        content_blocks_config.ready()

        assert cache.get(text_content_block.cache_key) is not None

    @pytest.mark.django_db
    def test_ready_cache_disabled(
        self, text_content_block, content_blocks_config, settings
    ):
        settings.CONTENT_BLOCKS_DISABLE_CACHE = True

        assert cache.get(text_content_block.cache_key) is None

        content_blocks_config.ready()

        assert cache.get(text_content_block.cache_key) is None

    @pytest.mark.django_db
    def test_ready_cache_on_start_disabled(
        self, text_content_block, content_blocks_config, settings
    ):
        settings.CONTENT_BLOCKS_DISABLE_CACHE_ON_START = True

        assert cache.get(text_content_block.cache_key) is None

        content_blocks_config.ready()

        assert cache.get(text_content_block.cache_key) is None
