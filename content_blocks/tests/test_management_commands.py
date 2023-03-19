import pytest
from django.core.management import call_command
from faker import Faker

from content_blocks.cache import cache

faker = Faker()


class TestManagementCommands:
    @pytest.mark.django_db
    def test_clear_cache_management_command(
        self,
        content_block_template_factory,
        content_block_factory,
        content_block_field_factory,
        text_template,
    ):
        """
        Test clear cache management command.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        content_block_field_factory.create(text=text, content_block=content_block)

        content_block.render()

        assert cache.get(content_block.cache_key) == text

        call_command("clear_content_blocks_cache", verbosity=0)

        assert cache.get(content_block.cache_key) is None

    @pytest.mark.django_db
    def test_update_cache_management_command(
        self,
        content_block_template_factory,
        content_block_factory,
        content_block_field_factory,
        text_template,
    ):
        """
        Test update cache management command.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        content_block_field = content_block_field_factory.create(
            text=text, content_block=content_block
        )

        content_block.render()

        assert cache.get(content_block.cache_key) == text

        new_text = faker.text(256)
        content_block_field.save_value(new_text)

        assert cache.get(content_block.cache_key) == text

        call_command("update_content_blocks_cache", verbosity=0)

        assert cache.get(content_block.cache_key) == new_text
