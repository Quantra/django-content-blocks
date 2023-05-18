import pytest
from faker import Faker

from content_blocks.conf import settings
from content_blocks.services.content_block import CacheServices, RenderServices

faker = Faker()


class TestCacheServices:
    @pytest.mark.django_db
    def test_cache_key(self, content_block):
        """
        The cache key should be {cache_prefix}_{id} when no site is supplied.
        """
        cache_prefix = settings.CONTENT_BLOCKS_CACHE_PREFIX
        assert (
            CacheServices.cache_key(content_block)
            == f"{cache_prefix}_{content_block.id}"
        )

    @pytest.mark.django_db
    def test_cache_key_site(self, content_block, site):
        """
        The cache key should be {cache_prefix}_{id}_site_{site_id} when site is supplied.
        """
        cache_prefix = settings.CONTENT_BLOCKS_CACHE_PREFIX
        assert (
            CacheServices.cache_key(content_block, site)
            == f"{cache_prefix}_{content_block.id}_site_{site.id}"
        )


class TestRenderServices:
    @pytest.mark.django_db
    def test_render_html(
        self,
        content_block_factory,
        content_block_field_factory,
        content_block_template_factory,
        text_template,
    ):
        """
        Should render the template.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        content_block_field_factory.create(text=text, content_block=content_block)

        html = RenderServices.render_html(content_block)

        assert html == text

    @pytest.mark.django_db
    def test_render_html_context(
        self,
        content_block_factory,
        content_block_field_factory,
        content_block_template_factory,
        text_context_template,
    ):
        """
        Should render the template with the supplied context.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_context_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        content_block_field_factory.create(text=text, content_block=content_block)

        extra_context_text = faker.text()
        context = {"extra_context": extra_context_text}

        html = RenderServices.render_html(content_block, context=context)

        assert html == f"{text}_{extra_context_text}"

    @pytest.mark.django_db
    def test_render_html_context_site(
        self,
        content_block_factory,
        content_block_field_factory,
        content_block_template_factory,
        text_context_site_template,
        site,
    ):
        """
        Should render the template with the supplied context + site.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_context_site_template.name
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        content_block_field_factory.create(text=text, content_block=content_block)

        extra_context_text = faker.text()
        context = {"extra_context": extra_context_text}

        html = RenderServices.render_html(content_block, context=context, site=site)

        assert html == f"{text}_{extra_context_text}_{site}"

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
        existing_context = {existing_context_name: "Context which exists"}

        context = RenderServices.context(text_content_block, context=existing_context)

        assert existing_context_name in context.keys()
        assert context[existing_context_name] == existing_context[existing_context_name]

        context_name = text_content_block.context_name

        assert context_name in context.keys()
        assert context[context_name] == text_content_block.context

        object_context_name = f"{context_name}_object"

        assert object_context_name in context.keys()
        assert context[object_context_name] == text_content_block

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

        assert RenderServices.can_render(content_block) is True

    @pytest.mark.django_db
    def test_content_block_cannot_render_no_template(self, content_block):
        """
        Should return False when ContentBlockTemplate has not template file
        """
        assert RenderServices.can_render(content_block) is False

    @pytest.mark.django_db
    def test_content_block_cannot_render_bad_template(
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

        assert RenderServices.can_render(content_block) is False
