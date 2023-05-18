"""
Content blocks test_signals.py
"""
from pathlib import Path

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.db.models.signals import post_delete, post_save
from faker import Faker

from content_blocks.models import ContentBlockCollection, ContentBlockFields
from content_blocks.services.content_block import CacheServices, cache
from content_blocks.tests.factories import (
    PopulatedFileContentBlockFieldFactory,
    PopulatedImageContentBlockFieldFactory,
    PopulatedVideoContentBlockFieldFactory,
)

faker = Faker()


class TestModelChoiceSignals:
    @pytest.fixture
    def content_block_field(
        self, request, content_block_field_factory, content_block_template_field_factory
    ):
        field_type = request.param.get("field_type", ContentBlockFields.choices[0][0])
        return content_block_field_factory(
            template_field=content_block_template_field_factory(
                field_type=field_type, key=field_type.lower()
            ),
            field_type=field_type,
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": ContentBlockFields.MODEL_CHOICE_FIELD}],
        indirect=True,
    )
    def test_cache_updated_model_choice(
        self,
        content_block_field,
        content_block_collection_factory,
        model_choice_template,
        content_block_template_field_factory,
        settings,
    ):
        if settings.CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE:
            pytest.skip(
                "Skipping because CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE = True"
            )

        content_block = content_block_field.content_block
        content_block_template = content_block.content_block_template

        content_block_template.template_filename = model_choice_template.name
        content_block_template.model_choice_content_type = (
            ContentType.objects.get_for_model(ContentBlockCollection)
        )
        content_block_template.save()

        content_block_template_field = content_block_template_field_factory.create(
            field_type=ContentBlockFields.MODEL_CHOICE_FIELD,
            model_choice_content_type=ContentType.objects.get_for_model(
                ContentBlockCollection
            ),
            content_block_template=content_block_template,
            key="modelchoicefield",
        )

        related_content_block_collection = content_block_collection_factory.create()
        parent_content_block_collection = content_block_collection_factory.create()

        content_block_field.template_field = content_block_template_field
        content_block_field.model_choice_content_type = (
            content_block_template_field.model_choice_content_type
        )
        content_block_field.model_choice_object_id = related_content_block_collection.id
        content_block_field.save()

        parent_content_block_collection.content_blocks.add(content_block)

        cache_key = CacheServices.cache_key(content_block)

        html_1 = content_block.render()
        assert cache.get(cache_key) == html_1

        related_content_block_collection.slug = faker.slug()
        related_content_block_collection.save()

        html_2 = cache.get(cache_key)
        assert html_2 is not None
        assert html_2 != html_1

        related_content_block_collection.delete()
        content_block_field.refresh_from_db()
        assert content_block_field.model_choice is None

        html_3 = cache.get(cache_key)
        assert html_3 is not None
        assert html_3 != html_2

    @pytest.mark.django_db
    def test_model_choice_cache_signal_disabled(self, text_content_block, settings):
        if not settings.CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE:
            pytest.skip(
                "Skipping because CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE = False. "
                "Use --ds config.settings.test_disable_update_cache_model_choice to test."
            )

        # The signal should not be connected
        post_save_signals = [r[0][0] for r in post_save.receivers]
        assert "update_cache_model_choice_save" not in post_save_signals

        post_delete_signals = [r[0][0] for r in post_delete.receivers]
        assert "update_cache_model_choice_delete" not in post_delete_signals

    @pytest.mark.django_db
    def test_ready_model_choice_cache_signal_connected(
        self, text_content_block, settings
    ):
        if settings.CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE:
            pytest.skip(
                "Skipping because CONTENT_BLOCKS_DISABLE_UPDATE_CACHE_MODEL_CHOICE = True"
            )

        # The signal should be connected
        post_save_signals = [r[0][0] for r in post_save.receivers]
        assert "update_cache_model_choice_save" in post_save_signals

        post_delete_signals = [r[0][0] for r in post_delete.receivers]
        assert "update_cache_model_choice_delete" in post_delete_signals


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
