"""
Content blocks test_forms.py
"""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from faker import Faker

from content_blocks.forms import (
    ContentBlockForm,
    ImportContentBlocksForm,
    NewContentBlockForm,
    NewNestedBlockForm,
    ParentModelForm,
    PublishContentBlocksForm,
    ResetContentBlocksForm,
)
from content_blocks.models import (
    ContentBlock,
    ContentBlockCollection,
    ContentBlockFields,
    ContentBlockTemplate,
)
from content_blocks.services.content_block import CloneServices

faker = Faker()


class TestParentModelForm:
    @pytest.mark.django_db
    def test_init(self, content_block_collection):
        form = ParentModelForm(parent=content_block_collection)
        assert form.parent == content_block_collection


class TestNewContentBlockFormBase:
    @pytest.mark.django_db
    @pytest.mark.parametrize("draft", [True, False])
    def test_create_content_block(
        self, content_block_collection, content_block_template_field, draft
    ):
        content_block_template = content_block_template_field.content_block_template
        form = NewContentBlockForm(
            {"content_block_template": content_block_template},
            parent=content_block_collection,
        )
        form.is_valid()
        form.create_content_block(content_block_template, draft=draft)
        assert ContentBlock.objects.count() == 1
        assert ContentBlock.objects.first().draft == draft

    @pytest.mark.django_db
    @pytest.mark.parametrize("min_num", range(4))
    def test_create_content_block_nested_min_num(
        self,
        content_block_collection,
        content_block_template_field_factory,
        text_content_block_template,
        min_num,
    ):
        content_block_template_field = content_block_template_field_factory.create(
            field_type=ContentBlockFields.NESTED_FIELD,
            min_num=min_num,
        )
        content_block_template_field.nested_templates.add(text_content_block_template)

        content_block_template = content_block_template_field.content_block_template

        form = NewContentBlockForm(
            {"content_block_template": content_block_template},
            parent=content_block_collection,
        )

        form.is_valid()
        form.create_content_block(content_block_template, draft=True)
        assert ContentBlock.objects.count() == min_num + 1


class TestNewContentBlockForm:
    @pytest.mark.django_db
    def test_init(self, content_block_template, content_block_collection):
        form = NewContentBlockForm(parent=content_block_collection)
        assert list(form.get_available_templates()) == list(
            form.fields["content_block_template"].queryset
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize("make_content_block_availability", [True, False])
    def test_get_available_templates(
        self,
        content_block_template,
        content_block_availability_factory,
        content_block_collection,
        make_content_block_availability,
    ):
        if make_content_block_availability:
            content_block_availability = content_block_availability_factory.create(
                content_type=ContentType.objects.get_for_model(ContentBlockCollection)
            )
            content_block_availability.content_block_templates.add(
                content_block_template
            )

        form = NewContentBlockForm(parent=content_block_collection)

        assert list(form.get_available_templates()) == list(
            ContentBlockTemplate.objects.all()
        )

    @pytest.mark.django_db
    def test_update_parent_m2m(self, content_block_collection, content_block):
        form = NewContentBlockForm(parent=content_block_collection)
        form.update_parent_m2m(content_block)
        assert content_block_collection.content_blocks.filter(
            id=content_block.id
        ).exists()

    @pytest.mark.django_db
    def test_save(
        self,
        content_block_collection,
        content_block_template_field,
    ):
        content_block_template = content_block_template_field.content_block_template
        form = NewContentBlockForm(
            {"content_block_template": content_block_template},
            parent=content_block_collection,
        )
        form.is_valid()
        form.save()
        assert ContentBlock.objects.count() == 1


class TestNewNestedBlockForm:
    @pytest.mark.django_db
    def test_save(self, nested_content_block):
        content_block, nested_content_block = nested_content_block
        assert ContentBlock.objects.count() == 2
        form = NewNestedBlockForm(
            {
                "content_block_template": content_block.content_block_template,
                "parent": nested_content_block.parent,
                "position": 1,
            }
        )
        assert form.is_valid()
        form.save()
        assert ContentBlock.objects.count() == 3


class TestContentBlockForm:
    @pytest.mark.django_db
    def test_init(self, content_block_field):
        content_block = content_block_field.content_block
        content_block.css_class = faker.text(256)

        form = ContentBlockForm(content_block=content_block)

        assert form.content_block == content_block
        assert form.fields["css_class"].initial == content_block.css_class

    @pytest.mark.django_db
    def test_set_fields(self, content_block_field):
        content_block = content_block_field.content_block
        content_block.css_class = faker.text(256)

        form = ContentBlockForm(content_block=content_block)
        assert "textfield" in form.fields.keys()

    @pytest.mark.django_db
    def test_save(self, content_block_field):
        content_block = content_block_field.content_block
        text = faker.text(256)

        form = ContentBlockForm({"textfield": text}, content_block=content_block)
        assert form.is_valid()
        form.save()

        content_block_field.refresh_from_db()
        assert content_block_field.text == text

    @pytest.mark.django_db
    def test_save_svg(self, image_content_block_field_factory, svg_file):
        content_block_field = image_content_block_field_factory.create()
        content_block = content_block_field.content_block

        form = ContentBlockForm(
            files={"imagefield": File(svg_file.open("rb"), name=svg_file.name)},
            content_block=content_block,
        )
        assert form.is_valid()
        form.save()

        content_block_field.refresh_from_db()
        assert content_block_field.image.read() == svg_file.open("rb").read()

    @pytest.mark.django_db
    def test_save_png(self, image_content_block_field_factory, png_file):
        content_block_field = image_content_block_field_factory.create()
        content_block = content_block_field.content_block

        form = ContentBlockForm(
            files={"imagefield": File(png_file.open("rb"), name=png_file.name)},
            content_block=content_block,
        )
        assert form.is_valid()
        form.save()

        content_block_field.refresh_from_db()
        assert content_block_field.image.read() == png_file.open("rb").read()


class TestPublishContentBlocksForm:
    @pytest.mark.django_db
    def test_save(self, content_block_collection, content_block):
        content_block_collection.content_blocks.add(content_block)
        content_block_2 = CloneServices.clone_content_block(
            content_block, attrs={"draft": True}
        )
        content_block_collection.content_blocks.add(content_block_2)

        assert ContentBlock.objects.count() == 2

        form = PublishContentBlocksForm({}, parent=content_block_collection)
        assert form.is_valid()
        form.save()

        assert ContentBlock.objects.count() == 2
        assert not content_block_collection.content_blocks.filter(
            id=content_block.id
        ).exists()


class TestResetContentBlocksForm:
    @pytest.mark.django_db
    def test_save(self, content_block_collection, content_block):
        content_block_collection.content_blocks.add(content_block)
        content_block_2 = CloneServices.clone_content_block(
            content_block, attrs={"draft": True}
        )
        content_block_collection.content_blocks.add(content_block_2)

        assert ContentBlock.objects.count() == 2

        form = ResetContentBlocksForm({}, parent=content_block_collection)
        assert form.is_valid()
        form.save()

        assert ContentBlock.objects.count() == 2
        assert not content_block_collection.content_blocks.filter(
            id=content_block_2.id
        ).exists()


class TestImportContentBlocksForm:
    @pytest.fixture
    def two_content_block_collections(self, content_block_collection_factory):
        content_block_collection_factory.create_batch(2)
        return (
            ContentBlockCollection.objects.first(),
            ContentBlockCollection.objects.last(),
        )

    @pytest.mark.django_db
    def test_init(self, two_content_block_collections):
        (
            content_block_collection_1,
            content_block_collection_2,
        ) = two_content_block_collections

        form = ImportContentBlocksForm(parent=content_block_collection_2)
        assert list(form.fields["master"].queryset) == list(form.get_master_queryset())

    @pytest.mark.django_db
    def test_get_master_queryset(self, two_content_block_collections):
        (
            content_block_collection_1,
            content_block_collection_2,
        ) = two_content_block_collections

        form = ImportContentBlocksForm(parent=content_block_collection_2)
        assert list(form.get_master_queryset()) == list(
            ContentBlockCollection.objects.exclude(id=content_block_collection_2.id)
        )

    @pytest.mark.django_db
    def test_save(self, two_content_block_collections, content_block_factory):
        (
            content_block_collection_1,
            content_block_collection_2,
        ) = two_content_block_collections

        content_block = content_block_factory.create(draft=True)
        content_block_collection_1.content_blocks.add(content_block)

        assert ContentBlock.objects.count() == 1

        form = ImportContentBlocksForm(
            {"master": content_block_collection_1}, parent=content_block_collection_2
        )
        assert form.is_valid()
        form.save()

        assert content_block_collection_1.content_blocks.count() == 1
        assert content_block_collection_2.content_blocks.count() == 1
