from io import StringIO
from unittest.mock import MagicMock

import pytest
from django.core import serializers
from django.core.management import call_command
from django.db import connection
from faker import Faker

from content_blocks.models import (
    ContentBlock,
    ContentBlockField,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)
from content_blocks.services.content_block_template import post_import

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

    @pytest.mark.django_db
    def test_import_content_block_templates_signal_sent(
        self, cbt_import_export_json_file
    ):
        handler = MagicMock()
        post_import.connect(handler, sender=ContentBlockTemplate)

        call_command("import_content_block_templates", cbt_import_export_json_file)

        handler.assert_called_once()


class TestDjangoManagementCommands:
    """
    Tests to confirm some Django management commands work.
    """

    @pytest.mark.django_db
    def test_dumpdata_loaddata(
        self, text_content_block, content_block_collection, tmp_path_factory
    ):
        """
        dumpdata is tested here because use of natural keys + select_related in the model manager causes it to fail.
        loaddata is tested here because of the polymorphism used on ContentBlockField. When dumped and loaded the
        sequence for ID will not be reset if our model polymorphs to a proxy model.
        """
        json_path = tmp_path_factory.getbasetemp() / "testdata.json"
        json_path.touch(exist_ok=True)

        content_block_collection.content_blocks.add(text_content_block)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT nextval(%s);", ["content_blocks_contentblockfield_id_seq"]
            )
            sequence = cursor.fetchone()[0]

        assert sequence > 0

        # dumpdata json to temporary file so we can load with loaddata later
        with json_path.open("w") as f:
            call_command(
                "dumpdata",
                natural_foreign=True,
                natural_primary=True,
                indent=2,
                stdout=f,
            )

        # Delete our objects
        content_block_collection.delete()
        text_content_block.delete()

        # Reset sequences manually
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(%s, 1);", ["content_blocks_contentblockfield_id_seq"]
            )
            cursor.execute(
                "SELECT nextval(%s);", ["content_blocks_contentblockfield_id_seq"]
            )
            sequence = cursor.fetchone()[0]
        assert sequence == 2

        # loaddata
        call_command("loaddata", str(json_path))

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT nextval(%s);", ["content_blocks_contentblockfield_id_seq"]
            )
            sequence = cursor.fetchone()[0]

        assert sequence >= 3
