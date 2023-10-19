"""
Model tests
"""
import pytest
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import get_storage_class
from django.db import IntegrityError
from django.forms.utils import pretty_name
from faker import Faker

from content_blocks.conf import settings
from content_blocks.fields import SVGAndImageFieldFormField
from content_blocks.models import (
    ContentBlock,
    ContentBlockAvailability,
    ContentBlockCollection,
    ContentBlockField,
    ContentBlockFields,
    ContentBlockTemplate,
    ContentBlockTemplateField,
    PolymorphError,
)
from content_blocks.tests.storages import SettingsTestStorage

faker = Faker()


class TestContentBlockTemplate:
    @pytest.mark.django_db
    def test_create_content_block_template(self, content_block_template):
        assert ContentBlockTemplate.objects.count() == 1
        assert content_block_template == ContentBlockTemplate.objects.first()

    @pytest.mark.django_db
    def test_content_block_template_str(self, content_block_template):
        assert str(content_block_template) == content_block_template.name


class TestContentBlockTemplateField:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_template_field__field_type",
        [c[0] for c in ContentBlockFields.choices],
    )
    def test_create_content_block_template_field(self, content_block_template_field):
        assert ContentBlockTemplateField.objects.count() == 1
        obj_from_db = ContentBlockTemplateField.objects.first()
        assert content_block_template_field == obj_from_db
        assert content_block_template_field.field_type == obj_from_db.field_type

    @pytest.mark.django_db
    def test_content_block_template_field_unique_together(
        self, content_block_template_field_factory, content_block_template_factory
    ):
        with pytest.raises(IntegrityError):
            template = content_block_template_factory()
            content_block_template_field_factory(
                key="same_key", content_block_template=template
            )
            content_block_template_field_factory(
                key="same_key", content_block_template=template
            )

    @pytest.mark.django_db
    def test_content_block_template_field_str(self, content_block_template_field):
        assert str(content_block_template_field) == content_block_template_field.key


class TestContentBlock:
    @pytest.mark.django_db
    def test_create_content_block(self, content_block):
        assert ContentBlock.objects.count() == 1
        assert content_block == ContentBlock.objects.first()

    @pytest.mark.django_db
    def test_content_block_template(
        self, content_block_factory, content_block_template_factory
    ):
        template = faker.file_name(extension="html")
        content_block_template = content_block_template_factory.create(
            template_filename=template
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        assert (
            content_block.template
            == f"content_blocks/content_blocks/{content_block.content_block_template.template_filename}"
        )

    @pytest.mark.django_db
    def test_content_block_fields(self, content_block, content_block_field_factory):
        """
        The fields property should return a dictionary of content block field key and field object.
        We also test the value is cached on the object.
        """
        content_block_field = content_block_field_factory.create(
            content_block=content_block, text=faker.text(256)
        )
        assert content_block.fields == {content_block_field.key: content_block_field}

    @pytest.mark.django_db
    def test_content_block_nested_fields(
        self, content_block, nested_content_block_field_factory
    ):
        """
        The nested fields property should return a dictionary of content block field key and field object.
        We also test the value is cached on the object.
        """
        nested_content_block_field = nested_content_block_field_factory.create(
            content_block=content_block
        )

        assert content_block.nested_fields == {
            nested_content_block_field.key: nested_content_block_field
        }

    @pytest.mark.django_db
    def test_content_block_context(
        self, content_block_factory, content_block_field_factory
    ):
        """
        The context property should return a dictionary of content block field key and field object context plus the
        css_class context.
        We also test the value is cached on the object.
        """
        content_block = content_block_factory.create(css_class=faker.text(64))
        content_block_field = content_block_field_factory.create(
            content_block=content_block, text=faker.text(256)
        )
        assert content_block.context == {
            content_block_field.key: content_block_field.context_value,
            "css_class": content_block.css_class,
        }

    @pytest.mark.django_db
    def test_can_render(
        self, content_block_template_factory, content_block_factory, text_template
    ):
        """
        Should return True when the ContentBlockTemplate has a template file and it exists.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )

        assert content_block.can_render is True

    @pytest.mark.django_db
    def test_cannot_render_no_template(self, content_block):
        """
        Should return False when ContentBlockTemplate has not template file
        """
        assert content_block.can_render is False

    @pytest.mark.django_db
    def test_cannot_render_bad_template(
        self, content_block_template_factory, content_block_factory
    ):
        """
        Should return False when the template file does not exist.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=faker.file_name(extension=".html")
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )

        assert content_block.can_render is False

    @pytest.mark.django_db
    def test_content_block_render(
        self,
        content_block_template_factory,
        content_block_factory,
        content_block_field_factory,
        text_template,
    ):
        content_block_template = content_block_template_factory.create(
            template_filename=text_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        content_block_field_factory.create(text=text, content_block=content_block)

        assert content_block.render() == text


class TestContentBlockField:
    @pytest.fixture
    def content_block_field(
        self, request, content_block_field_factory, content_block_template_field_factory
    ):
        field_type = request.param.get("field_type", ContentBlockFields.choices[0][0])
        kwargs = {}
        if field_type == ContentBlockFields.MODEL_CHOICE_FIELD:
            kwargs["model_choice_content_type"] = ContentType.objects.get_for_model(
                ContentBlockCollection
            )
        return content_block_field_factory(
            template_field=content_block_template_field_factory(field_type=field_type),
            field_type=field_type,
            **kwargs,
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_create_content_block_field(self, content_block_field):
        assert ContentBlockField.objects.count() == 1
        obj_from_db = ContentBlockField.objects.first()
        assert content_block_field == obj_from_db
        assert content_block_field.field_type == obj_from_db.field_type
        assert (
            content_block_field.template_field.field_type
            == content_block_field.field_type
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_content_block_field_polymorphism(self, content_block_field):
        """
        Test polymorphism. The object class should match it's field_type choice.
        """
        content_block_field.polymorph()
        assert content_block_field.__class__.__name__ == content_block_field.field_type

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_content_block_field_polymorphism_fails(self, content_block_field):
        """
        Test polymorphism fails when there is no subclass to polymorph to.
        """
        content_block_field.field_type = faker.text(32)

        with pytest.raises(PolymorphError):
            content_block_field.polymorph()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_content_block_field_template_name(self, content_block_field):
        """
        The template name should be default for everything except checkboxes.
        """
        template_names = {
            ContentBlockFields.CHECKBOX_FIELD: "content_blocks/partials/fields/checkbox.html"
        }
        template_name = template_names.get(
            content_block_field.field_type,
            "content_blocks/partials/fields/default.html",
        )
        assert content_block_field.template_name == template_name

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_content_block_field_preview_template_name(self, content_block_field):
        """
        The template name should be None except for Image, Video and Embedded Video fields
        """
        preview_template_names = {
            ContentBlockFields.IMAGE_FIELD: "content_blocks/partials/fields/previews/image.html",
            ContentBlockFields.VIDEO_FIELD: "content_blocks/partials/fields/previews/video.html",
            ContentBlockFields.EMBEDDED_VIDEO_FIELD: "content_blocks/partials/fields/previews/embedded_video.html",
            ContentBlockFields.IFRAME_FIELD: "content_blocks/partials/fields/previews/iframe.html",
        }
        preview_template_name = preview_template_names.get(
            content_block_field.field_type
        )
        assert content_block_field.preview_template_name == preview_template_name

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_content_block_field_form_field_class(self, content_block_field):
        """
        Should return the appropriate form field for the field type.
        """
        form_fields = {
            ContentBlockFields.TEXT_FIELD: forms.CharField,
            ContentBlockFields.CONTENT_FIELD: forms.CharField,
            ContentBlockFields.IMAGE_FIELD: SVGAndImageFieldFormField,
            ContentBlockFields.NESTED_FIELD: None.__class__,
            ContentBlockFields.CHECKBOX_FIELD: forms.BooleanField,
            ContentBlockFields.CHOICE_FIELD: forms.CharField,
            ContentBlockFields.MODEL_CHOICE_FIELD: forms.ModelChoiceField,
            ContentBlockFields.FILE_FIELD: forms.FileField,
            ContentBlockFields.VIDEO_FIELD: forms.FileField,
            ContentBlockFields.EMBEDDED_VIDEO_FIELD: forms.CharField,
            ContentBlockFields.IFRAME_FIELD: forms.CharField,
        }
        form_field = form_fields.get(content_block_field.field_type)
        assert content_block_field.form_field.__class__ == form_field

    @pytest.fixture
    def field_types(self):
        return {
            ContentBlockFields.TEXT_FIELD: {"value": faker.text(256), "field": "text"},
            ContentBlockFields.CONTENT_FIELD: {
                "value": faker.paragraph(),
                "field": "content",
            },
            ContentBlockFields.IMAGE_FIELD: {
                "value": faker.file_name(extension="png"),
                "field": "image",
            },
            ContentBlockFields.CHECKBOX_FIELD: {"value": True, "field": "checkbox"},
            ContentBlockFields.CHOICE_FIELD: {"value": "choice_2", "field": "choice"},
            ContentBlockFields.FILE_FIELD: {
                "value": faker.file_name(extension="pdf"),
                "field": "file",
            },
            ContentBlockFields.VIDEO_FIELD: {
                "value": faker.file_name(extension="mp4"),
                "field": "video",
            },
            ContentBlockFields.EMBEDDED_VIDEO_FIELD: {
                "value": faker.uri(),
                "field": "embedded_video",
            },
            ContentBlockFields.MODEL_CHOICE_FIELD: {
                "value": "1",
                "field": "model_choice",
            },
            ContentBlockFields.IFRAME_FIELD: {
                "value": faker.uri(),
                "field": "iframe",
            },
        }

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [
            {"field_type": c[0]}
            for c in ContentBlockFields.choices
            if c[0]
            not in [
                ContentBlockFields.NESTED_FIELD,
                ContentBlockFields.MODEL_CHOICE_FIELD,
            ]
        ],
        indirect=True,
    )
    def test_content_block_field_save_value(self, content_block_field, field_types):
        """
        Test the appropriate field is saved with the value given based on field type.
        Tests all field_types except nested, model choice and model multiple choice.
        """
        field_type = field_types.get(content_block_field.field_type)

        save_value = content_block_field.save_value(field_type["value"])
        assert (
            getattr(content_block_field, field_type["field"])
            == field_type["value"]
            == save_value
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": ContentBlockFields.NESTED_FIELD}],
        indirect=True,
    )
    def test_content_block_nested_field_save_value(self, content_block_field):
        save_value = content_block_field.save_value(None)
        assert save_value is None

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": ContentBlockFields.MODEL_CHOICE_FIELD}],
        indirect=True,
    )
    def test_content_block_model_choice_field_save_value(
        self, content_block_field, content_block_collection
    ):
        content_block_field.model_choice_content_type = (
            ContentType.objects.get_for_model(ContentBlockCollection)
        )
        save_value = content_block_field.save_value(content_block_collection)
        assert (
            content_block_field.model_choice == content_block_collection == save_value
        )

        save_value = content_block_field.save_value(None)
        assert save_value is None

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [
            {"field_type": c[0]}
            for c in ContentBlockFields.choices
            if c[0]
            not in [
                ContentBlockFields.NESTED_FIELD,
                ContentBlockFields.MODEL_CHOICE_FIELD,
            ]
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("content_blocks_mark_safe", [False, True])
    def test_content_block_field_context_value(
        self, content_block_field, field_types, settings, content_blocks_mark_safe
    ):
        settings.CONTENT_BLOCKS_MARK_SAFE = content_blocks_mark_safe
        field_type = field_types.get(content_block_field.field_type)
        field, value = field_type["field"], field_type["value"]
        setattr(content_block_field, field, value)
        assert content_block_field.context_value == value

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": c[0]} for c in ContentBlockFields.choices],
        indirect=True,
    )
    def test_content_block_context_value_none(self, content_block_field):
        """
        Context value should be None or None like unless a value is set.
        :param content_block_field:
        :return:
        """
        assert not content_block_field.context_value

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": ContentBlockFields.MODEL_CHOICE_FIELD}],
        indirect=True,
    )
    def test_content_block_model_choice_field_context_value(
        self, content_block_field, content_block_collection
    ):
        content_block_field.model_choice = content_block_collection
        content_block_field.save()
        assert content_block_field.context_value == content_block_collection

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "content_block_field",
        [{"field_type": ContentBlockFields.NESTED_FIELD}],
        indirect=True,
    )
    def test_content_block_nested_field_context_value(
        self, content_block_field, content_block_field_factory, content_block_factory
    ):
        """
        Nested field context value should be list of context of child content blocks.
        """
        nested_block_1 = content_block_factory.create(
            parent=content_block_field, saved=True
        )
        nested_block_2 = content_block_factory.create(
            parent=content_block_field, saved=True
        )

        content_block_field_factory.create(
            content_block=nested_block_1, text=faker.text(256)
        )
        content_block_field_factory.create(
            content_block=nested_block_2, text=faker.text(256)
        )

        assert list(content_block_field.context_value) == [
            nested_block_1,
            nested_block_2,
        ]

    @pytest.mark.django_db
    def test_content_block_nested_field_label(self, content_block_field_factory):
        content_block_field = content_block_field_factory.create(
            field_type=ContentBlockFields.NESTED_FIELD
        )

        label = pretty_name(content_block_field.template_field.key)

        assert content_block_field.label == label


class TestContentBlockManager:
    @pytest.mark.django_db
    def test_content_block_manager_visible(self, content_block, content_block_factory):
        content_block_factory.create(draft=False, visible=False)

        assert ContentBlock.objects.count() == 2
        assert ContentBlock.objects.visible().count() == 1

    @pytest.mark.django_db
    def test_content_block_manager_previews(self, content_block, content_block_factory):
        content_block_factory.create(draft=True, visible=True, saved=True)

        assert ContentBlock.objects.count() == 2
        assert ContentBlock.objects.previews().count() == 1

    @pytest.mark.django_db
    def test_content_block_manager_drafts(self, content_block, content_block_factory):
        content_block_factory.create(draft=True, visible=False)

        assert ContentBlock.objects.count() == 2
        assert ContentBlock.objects.drafts().count() == 1

    @pytest.mark.django_db
    def test_content_block_manager_published(
        self, content_block, content_block_factory
    ):
        content_block_factory.create(draft=True, visible=False)

        assert ContentBlock.objects.count() == 2
        assert ContentBlock.objects.published().count() == 1


class TestContentBlockAvailability:
    @pytest.mark.django_db
    def test_create_content_block_availability(self, content_block_availability):
        assert ContentBlockAvailability.objects.count() == 1
        assert content_block_availability == ContentBlockAvailability.objects.first()

    @pytest.mark.django_db
    def test_content_block_availability_str(self, content_block_availability):
        assert str(content_block_availability) == str(
            content_block_availability.content_type
        )


class TestContentBlockCollection:
    @pytest.mark.django_db
    def test_create_content_block_collection(self, content_block_collection):
        assert ContentBlockCollection.objects.count() == 1
        assert content_block_collection == ContentBlockCollection.objects.first()

    @pytest.mark.django_db
    def test_content_block_collection_str(self, content_block_collection):
        assert str(content_block_collection) == content_block_collection.slug

    @pytest.mark.django_db
    def test_content_block_collection_content_blocks_deleted(
        self, content_block, content_block_collection
    ):
        """
        When a content block collection is deleted the content blocks in it should also be deleted.
        :return:
        """
        assert ContentBlock.objects.count() == 1
        content_block_collection.content_blocks.add(content_block)
        content_block_collection.delete()
        assert ContentBlock.objects.count() == 0


class TestStorageSettings:
    @pytest.mark.django_db
    def test_content_blocks_storage_setting(self, content_block_field):
        if settings.CONTENT_BLOCKS_STORAGE == settings.DEFAULT_FILE_STORAGE:
            pytest.skip(
                "Skipping because --ds config.settings.test_storage_setting not used"
            )

        assert (
            content_block_field.file.storage.__class__
            == content_block_field.video.storage.__class__
            == SettingsTestStorage
        )
        assert content_block_field.image.storage.__class__ == get_storage_class(
            "django.core.files.storage.FileSystemStorage"
        )

    @pytest.mark.django_db
    def test_content_blocks_storage_setting_default(self, content_block_field):
        if settings.CONTENT_BLOCKS_STORAGE != settings.DEFAULT_FILE_STORAGE:
            pytest.skip(
                "Skipping because --ds config.settings.test_storage_setting used"
            )
        assert (
            content_block_field.image.storage.__class__
            == content_block_field.file.storage.__class__
            == content_block_field.video.storage.__class__
            == get_storage_class(settings.DEFAULT_FILE_STORAGE)
        )
