from io import StringIO

import pytest
from django.core import serializers
from django.core.management import call_command
from faker import Faker

from content_blocks.cache import cache
from content_blocks.models import (
    ContentBlock,
    ContentBlockField,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)

faker = Faker()


def _test_imported_json(json):
    """
    :param json: string or stream
    """
    export = serializers.deserialize("json", json)

    for py_obj in export:
        fields = py_obj.object.__dict__.copy()

        try:
            fields.pop("_state")
            fields.pop("mod_date")
            fields.pop("create_date")
        except KeyError:
            pass

        model = type(py_obj.object)

        model.objects.get(**fields)


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

    @pytest.mark.django_db
    def test_export_content_block_templates(self, cbt_import_export_objects):
        """
        Attempt a get from db for each object exported with exact fields except mod_date.
        """
        buffer = StringIO()
        call_command("export_content_block_templates", stdout=buffer)
        buffer.seek(0)

        _test_imported_json(buffer)

    @pytest.mark.django_db
    def test_import_content_block_templates(
        self,
        cbt_import_export_json_file,
    ):
        call_command("import_content_block_templates", cbt_import_export_json_file)

        content_block_templates = ContentBlockTemplate.objects.all()
        assert content_block_templates.count() == 1

        content_block_template_fields = ContentBlockTemplateField.objects.all()
        assert content_block_template_fields.count() == 1

    @pytest.mark.django_db
    def test_import_content_block_templates_clean(
        self,
        cbt_import_export_json_file,
    ):
        ContentBlockTemplate.objects.all().delete()
        ContentBlockTemplateField.objects.all().delete()

        call_command("import_content_block_templates", cbt_import_export_json_file)

        content_block_templates = ContentBlockTemplate.objects.all()
        assert content_block_templates.count() == 1

        content_block_template_fields = ContentBlockTemplateField.objects.all()
        assert content_block_template_fields.count() == 1

    @pytest.mark.django_db
    def test_import_content_block_templates_add_fields(
        self,
        cbt_import_export_json_file,
    ):
        content_block_template_fields_query = ContentBlockTemplateField.objects.all()
        content_block_templates_query = ContentBlockTemplate.objects.all()

        content_block_fields_query = ContentBlockField.objects.all()

        # check we have just one template field and field in the db
        assert content_block_template_fields_query.count() == 1
        assert content_block_fields_query.count() == 1

        content_block_template_fields_query.delete()

        # template field and field should be deleted now
        assert content_block_template_fields_query.count() == 0
        assert content_block_fields_query.count() == 0

        call_command("import_content_block_templates", cbt_import_export_json_file)

        # template field and template should exist once more
        assert content_block_templates_query.count() == 1
        assert content_block_template_fields_query.count() == 1
        assert content_block_fields_query.count() == 1

    @pytest.mark.django_db
    def test_import_content_block_templates_bad_json(
        self, cbt_import_export_bad_json_file
    ):
        content_blocks_query = ContentBlock.objects.all()
        content_block_templates_query = ContentBlockTemplate.objects.all()
        content_block_template_field_query = ContentBlockTemplateField.objects.all()

        assert content_blocks_query.count() == 1
        assert content_block_templates_query.count() == 1
        assert content_block_template_field_query.count() == 0

        call_command("import_content_block_templates", cbt_import_export_bad_json_file)

        assert content_blocks_query.count() == 1
        assert content_block_templates_query.count() == 1
        assert content_block_template_field_query.count() == 0
