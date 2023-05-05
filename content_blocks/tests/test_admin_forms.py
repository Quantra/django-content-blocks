"""
Content blocks test_admin_forms.py
"""
import json

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import model_to_dict

from content_blocks.admin_forms import (
    ContentBlockTemplateFieldAdminForm,
    ContentBlockTemplateImportForm,
    validate_choices,
)
from content_blocks.models import (
    ContentBlockCollection,
    ContentBlockField,
    ContentBlockFields,
)


class TestContentBlockTemplateFieldAdminForm:
    @pytest.mark.django_db
    @pytest.mark.parametrize("min_num", range(2, 4))
    def test_clean_nested_field(
        self,
        nested_content_block_template_field_factory,
        min_num,
        text_content_block_template,
    ):
        nested_content_block_template_field = (
            nested_content_block_template_field_factory.create()
        )

        form_data = model_to_dict(nested_content_block_template_field)
        form_data["nested_templates"] = [text_content_block_template]

        form = ContentBlockTemplateFieldAdminForm(
            form_data,
            instance=nested_content_block_template_field,
        )
        assert form.is_valid()

        form_data["min_num"] = min_num
        form_data["max_num"] = min_num + 1
        form = ContentBlockTemplateFieldAdminForm(
            form_data,
            instance=nested_content_block_template_field,
        )
        assert form.is_valid()

        form_data2 = form_data.copy()
        form_data2["nested_templates"] = None
        form = ContentBlockTemplateFieldAdminForm(
            form_data2,
            instance=nested_content_block_template_field,
        )
        assert not form.is_valid()
        assert "nested_templates" in form.errors.keys()

        form_data3 = form_data.copy()
        form_data3["max_num"] = min_num - 1
        form = ContentBlockTemplateFieldAdminForm(
            form_data3,
            instance=nested_content_block_template_field,
        )
        assert not form.is_valid()
        assert "min_num" in form.errors.keys()
        assert "max_num" in form.errors.keys()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "bad_choice",
        [None, "None", "not good choices", "['bad', 'list']", "[['bad',],]"],
    )
    def test_clean_choice_field(self, content_block_template_field_factory, bad_choice):
        content_block_template_field = content_block_template_field_factory.create(
            field_type=ContentBlockFields.CHOICE_FIELD,
            choices=json.dumps([["value1", "Option One"], ["value2", "Option Two"]]),
        )

        form_data = model_to_dict(content_block_template_field)
        form = ContentBlockTemplateFieldAdminForm(
            form_data, instance=content_block_template_field
        )
        assert form.is_valid()

        form_data["choices"] = bad_choice
        form = ContentBlockTemplateFieldAdminForm(
            form_data, instance=content_block_template_field
        )
        assert not form.is_valid()
        assert "choices" in form.errors.keys()

    @pytest.mark.django_db
    def test_clean_model_choice_fields(self, content_block_template_field_factory):
        content_block_template_field = content_block_template_field_factory.create(
            field_type=ContentBlockFields.MODEL_CHOICE_FIELD,
            model_choice_content_type=ContentType.objects.get_for_model(
                ContentBlockCollection
            ),
        )

        form_data = model_to_dict(content_block_template_field)

        form = ContentBlockTemplateFieldAdminForm(
            form_data, instance=content_block_template_field
        )

        assert form.is_valid()

        form_data["model_choice_content_type"] = None
        form = ContentBlockTemplateFieldAdminForm(
            form_data, instance=content_block_template_field
        )

        assert not form.is_valid()
        assert "model_choice_content_type" in form.errors.keys()

    @pytest.mark.django_db
    def test_clean_field_type(self, content_block_template_field):
        """
        Should not be able to change the field type.
        """
        form_data = model_to_dict(content_block_template_field)
        form = ContentBlockTemplateFieldAdminForm(
            form_data, instance=content_block_template_field
        )
        assert form.is_valid()

        form_data["field_type"] = ContentBlockFields.CONTENT_FIELD  # not TEXT_FIELD
        form = ContentBlockTemplateFieldAdminForm(
            form_data, instance=content_block_template_field
        )
        assert not form.is_valid()
        assert "field_type" in form.errors.keys()

    @pytest.mark.django_db
    def test_save(self, content_block_field_factory):
        """
        If this is a new template field a field corresponding to this field should be added to all existing content
        blocks that share the same content block template as this field.
        """
        content_block_field = content_block_field_factory.create(
            field_type=ContentBlockFields.TEXT_FIELD
        )
        content_block_template_field = content_block_field.template_field
        form_data = model_to_dict(content_block_template_field)

        content_block = content_block_field.content_block
        form_data.pop("id")
        form_data["key"] = "new_key"
        form_data["content_block_template"] = content_block.content_block_template.id

        form = ContentBlockTemplateFieldAdminForm(form_data)
        assert form.is_valid()
        form.save()
        assert ContentBlockField.objects.count() == 2

    def test_validate_choices(self):
        choices = "not even json"
        assert not validate_choices(choices)

        choices = json.dumps({"not": "a list"})
        assert not validate_choices(choices)

        choices = json.dumps([{"not": "a nested list"}])
        assert not validate_choices(choices)

        choices = json.dumps([["inner", "list", "too long"]])
        assert not validate_choices(choices)

        choices = json.dumps([["inner list too short"]])
        assert not validate_choices(choices)

        choices = json.dumps([["good", "choices"]])
        assert validate_choices(choices)


class TestContentBlockTemplateImportForm:
    @pytest.mark.django_db
    def test_clean_fixture_file(self, cbt_import_export_json_file, text_file):
        json_file = SimpleUploadedFile(
            cbt_import_export_json_file.name,
            cbt_import_export_json_file.read_bytes(),
            "application/json",
        )

        form_data = {"fixture_file": cbt_import_export_json_file.name}
        form_files = {"fixture_file": json_file}

        form = ContentBlockTemplateImportForm(form_data, form_files)

        assert form.is_valid()

        text_file = SimpleUploadedFile(text_file.name, text_file.read_bytes())

        form_data["fixture_file"] = text_file

        form = ContentBlockTemplateImportForm(form_data, form_files)

        assert not form.is_valid()
        assert "fixture_file" in form.errors.keys()
