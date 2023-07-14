"""
Tests for ContentBlock services.
"""

import pytest
from faker import Faker

from content_blocks.services.content_block import CloneServices, RenderServices

faker = Faker()


class TestRenderServices:
    @pytest.mark.django_db
    @pytest.mark.parametrize("context", [None, {"extra_context": faker.text()}])
    def test_render_content_block(
        self,
        context,
        content_block_factory,
        content_block_field_factory,
        content_block_template_factory,
        text_context_template,
    ):
        """
        Should render the content block to html.
        Test covers cases where:
        * Context is/isn't supplied.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_context_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        extra_context_text = "" if context is None else context["extra_context"]
        content_block_field_factory.create(text=text, content_block=content_block)

        html = RenderServices.render_content_block(content_block, context=context)
        assert html == f"{text}_{extra_context_text}"

    @pytest.mark.django_db
    def test_context(self, text_content_block):
        """
        Should return dictionary of context containing the ContentBlock.context and the ContentBlock object.
        """
        context = RenderServices.context(text_content_block)

        context_name = text_content_block.context_name

        assert context_name in context.keys()
        assert context[context_name] == text_content_block.context

        object_context_name = f"{context_name}_object"

        assert object_context_name in context.keys()
        assert context[object_context_name] == text_content_block

    @pytest.mark.django_db
    def test_context_update(self, text_content_block):
        """
        Should return dictionary of context containing the ContentBlock.context, ContentBlock object and the
        existing context supplied.
        """
        existing_context_name = "existing_context"
        existing_context = {existing_context_name: faker.text()}

        context = RenderServices.context(text_content_block, context=existing_context)

        assert existing_context_name in context.keys()
        assert context[existing_context_name] == existing_context[existing_context_name]

        context_name = text_content_block.context_name

        assert context_name in context.keys()
        assert context[context_name] == text_content_block.context

        object_context_name = f"{context_name}_object"

        assert object_context_name in context.keys()
        assert context[object_context_name] == text_content_block


class TestCloneServices:
    @pytest.mark.django_db
    def test_content_block_clone(self, nested_content_block):
        """
        The clone method should duplicate the content block and all fields.
        """
        content_block, nested_content_block = nested_content_block

        new_content_block = CloneServices.clone_content_block(content_block)

        assert new_content_block.id != content_block.id
        assert new_content_block.fields.keys() == content_block.fields.keys()

        new_content_block_nested_context = new_content_block.context.pop("nestedfield")
        content_block_nested_context = content_block.context.pop("nestedfield")
        assert (
            new_content_block_nested_context[0].content_block_template
            == content_block_nested_context[0].content_block_template
        )
        assert new_content_block.context == content_block.context
