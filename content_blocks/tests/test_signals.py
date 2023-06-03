"""
Content blocks test_signals.py
"""
from pathlib import Path

import pytest
from django.core.management import call_command
from faker import Faker

from content_blocks.services.content_block import CacheServices, cache
from content_blocks.tests.factories import (
    PopulatedFileContentBlockFieldFactory,
    PopulatedImageContentBlockFieldFactory,
    PopulatedVideoContentBlockFieldFactory,
)

faker = Faker()


class TestCleanupMediaSignals:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "sender",
        [
            {"factory": PopulatedImageContentBlockFieldFactory, "field": "image"},
            {"factory": PopulatedVideoContentBlockFieldFactory, "field": "video"},
            {"factory": PopulatedFileContentBlockFieldFactory, "field": "file"},
        ],
    )
    def test_cleanup_media_delete(self, sender):
        factory = sender["factory"]
        field = sender["field"]

        file_field = factory.create()
        file_field_2 = factory.create(**{field: getattr(file_field, field)})
        file_path = Path(getattr(file_field, field).path)

        # The file should exist
        assert file_path.is_file()

        # The file should exist as a content block field is still using it
        file_field.delete()
        assert file_path.is_file()

        # The file should be deleted now
        file_field_2.delete()
        assert not file_path.is_file()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "sender",
        [
            {
                "factory": PopulatedImageContentBlockFieldFactory,
                "field": "image",
                "extension": "jpg",
            },
            {
                "factory": PopulatedVideoContentBlockFieldFactory,
                "field": "video",
                "extension": "mp4",
            },
            {
                "factory": PopulatedFileContentBlockFieldFactory,
                "field": "file",
                "extension": "pdf",
            },
        ],
    )
    def test_cleanup_media_save(self, sender):
        factory = sender["factory"]
        field = sender["field"]
        extension = sender["extension"]

        file_field = factory.create()
        file_field_2 = factory.create(**{field: getattr(file_field, field)})
        file_path = Path(getattr(file_field, field).path)

        assert file_path.is_file()

        file_field.save_value(faker.file_name(extension=extension))
        assert file_path.is_file()

        file_field_2.save_value(faker.file_name(extension=extension))
        assert not file_path.is_file()


class TestDBTemplatesSignals:
    @pytest.mark.django_db
    def test_update_cache_template(
        self, text_content_block, template_factory, settings, content_block_collection
    ):
        if "dbtemplates" not in settings.INSTALLED_APPS:
            pytest.skip("skipping tests that require dbtemplates")

        content_block_collection.content_blocks.add(text_content_block)

        cache_key = CacheServices.cache_key(text_content_block)

        html = text_content_block.render()
        assert cache.get(cache_key) == html

        db_template = template_factory.create(
            name=text_content_block.template,
            content="db_template {{ content_block.textfield }}",
        )

        new_html = cache.get(cache_key)
        assert new_html is not None
        assert new_html != html

        db_template.delete()
        new_html = cache.get(cache_key)
        assert new_html is not None
        assert new_html == html


class TestSignals:
    @pytest.mark.django_db
    def test_loaddata(
        self,
        populated_image_content_block_field_factory,
        populated_video_content_block_field_factory,
        populated_file_content_block_field_factory,
        tmp_path_factory,
        template_factory,
        settings,
    ):
        """
        Test we can loaddata without any errors.
        None of our signals should run or cause errors.
        """
        populated_image_content_block_field_factory.create()
        populated_video_content_block_field_factory.create()
        populated_file_content_block_field_factory.create()

        call_command_args = ["dumpdata", "content_blocks"]
        if "dbtemplates" in settings.INSTALLED_APPS:
            template_factory.create()
            call_command_args.append("dbtemplates")

        path = tmp_path_factory.getbasetemp() / "test_dump.json"

        path.touch(exist_ok=True)
        call_command(*call_command_args, stdout=path.open("w"))

        call_command("loaddata", path)
