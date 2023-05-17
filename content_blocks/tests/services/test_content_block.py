import pytest
from faker import Faker

from content_blocks.conf import settings
from content_blocks.services.content_block import CacheServices, RenderServices

faker = Faker()


class TestCacheServices:
    @pytest.mark.django_db
    def test_cache_key(self, content_block):
        """
        The cache key should be {cache_prefix}_{id} when no site is supplied.
        """
        cache_prefix = settings.CONTENT_BLOCKS_CACHE_PREFIX
        assert (
            CacheServices.cache_key(content_block)
            == f"{cache_prefix}_{content_block.id}"
        )

    @pytest.mark.django_db
    def test_cache_key_site(self, content_block, site):
        """
        The cache key should be {cache_prefix}_{id}_site_{site_id} when site is supplied.
        """
        cache_prefix = settings.CONTENT_BLOCKS_CACHE_PREFIX
        assert (
            CacheServices.cache_key(content_block, site)
            == f"{cache_prefix}_{content_block.id}_site_{site.id}"
        )


class TestRenderServices:
    @pytest.mark.django_db
    def test_can_render(
        self, content_block_template_factory, content_block_factory, text_template
    ):
        content_block_template = content_block_template_factory.create(
            template_filename=text_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )

        assert RenderServices.can_render(content_block) is True

    @pytest.mark.django_db
    def test_content_block_cannot_render_no_template(self, content_block):
        assert RenderServices.can_render(content_block) is False

    @pytest.mark.django_db
    def test_content_block_cannot_render_bad_template(
        self, content_block_template_factory, content_block_factory
    ):
        content_block_template = content_block_template_factory.create(
            template_filename=faker.file_name(extension=".html")
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )

        assert RenderServices.can_render(content_block) is False
