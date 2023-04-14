"""
Content blocks test_templatetags.py
"""
import pytest
from django.template import Context
from faker import Faker

from content_blocks.forms import ContentBlockForm, NewNestedBlockForm
from content_blocks.templatetags.content_block_admin import (
    app_model_label,
    content_block_form,
    new_nested_block_form,
)
from content_blocks.templatetags.content_blocks import (
    content_block_collection as content_block_collection_tag,
)
from content_blocks.templatetags.content_blocks import (
    render_content_block as render_content_block_tag,
)

faker = Faker()


class TestContentBlockAdmin:
    @pytest.mark.django_db
    def test_content_block_form(self, content_block):
        assert str(content_block_form(content_block)) == str(
            ContentBlockForm(content_block=content_block)
        )

    @pytest.mark.django_db
    def test_new_nested_block_form(self, nested_content_block):
        content_block, nested_content_block = nested_content_block

        parent = nested_content_block.parent

        assert str(new_nested_block_form(parent)) == str(
            NewNestedBlockForm(
                initial={
                    "parent": parent,
                }
            )
        )

    @pytest.mark.django_db
    def test_app_model_label(self, content_block):
        assert (
            app_model_label(content_block)
            == f"{content_block._meta.app_label}.{content_block._meta.model.__name__}"
        )


class TestContentBlocks:
    @pytest.mark.django_db
    def test_content_block_collection(
        self, content_block_collection, text_content_block
    ):
        content_block_collection.content_blocks.add(text_content_block)
        context = content_block_collection_tag({}, content_block_collection.slug)
        assert context["slug"] == content_block_collection.slug
        assert context["content_block_collection"] == content_block_collection

    @pytest.mark.django_db
    def test_content_block_collection_fails_silently(self):
        slug = "non-existent-slug"
        context = content_block_collection_tag({}, slug)
        assert context["slug"] == slug
        assert "content_block_collection" not in context.keys()

    @pytest.mark.django_db
    def test_render_content_block(self, text_content_block):
        rendered = render_content_block_tag(Context(), text_content_block)
        assert rendered == text_content_block.render()
