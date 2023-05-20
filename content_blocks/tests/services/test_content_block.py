import pytest
from faker import Faker

from content_blocks.conf import settings
from content_blocks.services.content_block import CacheServices, RenderServices, cache

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

    @pytest.mark.django_db
    def test_get_cache(self, text_content_block):
        """
        Should return the cached html for the given ContentBlock.
        """
        cache_key = CacheServices.cache_key(content_block=text_content_block)

        html = cache.get(cache_key)
        assert html is None

        RenderServices.render_content_block(text_content_block)
        html = cache.get(cache_key)
        html2 = CacheServices.get_cache(text_content_block)

        assert html is not None
        assert html == html2

    @pytest.mark.django_db
    def test_get_cache_site(self, text_content_block, site, rf):
        """
        Should return the cached html for the given ContentBlock.
        """
        request = rf.get("/")
        request.site = site
        context = {"request": request}
        cache_key = CacheServices.cache_key(text_content_block, site=site)

        html = cache.get(cache_key)
        assert html is None

        RenderServices.render_content_block(text_content_block, context=context)
        html = cache.get(cache_key)
        html2 = CacheServices.get_cache(text_content_block, site=site)

        assert html is not None
        assert html == html2

    @pytest.mark.django_db
    def test_set_cache(self, text_content_block):
        """
        Should set the provided html in the cache under the key for the ContentBlock.
        """
        cache_key = CacheServices.cache_key(text_content_block)
        html = faker.text()

        cached_html = cache.get(cache_key)
        assert cached_html is None

        CacheServices.set_cache(text_content_block, html)

        cached_html = cache.get(cache_key)

        assert cached_html is not None
        assert cached_html == html

    @pytest.mark.django_db
    def test_set_cache_site(self, text_content_block, site):
        """
        Should set the provided html in the cache under the key for the ContentBlock and Site.
        """
        cache_key = CacheServices.cache_key(text_content_block, site=site)
        html = faker.text()

        cached_html = cache.get(cache_key)
        assert cached_html is None

        CacheServices.set_cache(text_content_block, html, site=site)

        cached_html = cache.get(cache_key)

        assert cached_html is not None
        assert cached_html == html


class TestRenderServices:
    @pytest.mark.django_db
    @pytest.mark.parametrize("no_cache", [False, True])
    @pytest.mark.parametrize("context", [None, {"extra_context": faker.text()}])
    def test_render_content_block(
        self,
        no_cache,
        context,
        content_block_factory,
        content_block_field_factory,
        content_block_template_factory,
        text_context_template,
    ):
        """
        Should render the content block and set it in the cache if possible.
        Test covers cases where:
        * The ContentBlock can and cannot be cached.
        * Context is/isn't supplied.
        """
        content_block_template = content_block_template_factory.create(
            template_filename=text_context_template.name, no_cache=no_cache
        )
        content_block = content_block_factory.create(
            content_block_template=content_block_template
        )
        text = faker.text(256)
        extra_context_text = "" if context is None else context["extra_context"]
        content_block_field_factory.create(text=text, content_block=content_block)
        cache_key = CacheServices.cache_key(content_block)

        cached_html = cache.get(cache_key)
        assert cached_html is None

        html = RenderServices.render_content_block(content_block, context=context)
        assert html == f"{text}_{extra_context_text}"

        cached_html = cache.get(cache_key)
        assert cached_html == f"{text}_{extra_context_text}" or no_cache
        assert cached_html is None or not no_cache

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

    @pytest.mark.django_db
    def test_site(self, rf, site):
        """
        Should return the site from the given context containing Request with site attribute.
        """
        request = rf.get("/")
        request.site = site

        context_site = RenderServices.site({"request": request})
        assert context_site == site

    @pytest.mark.django_db
    def test_site_dummyrequest(self, site):
        """
        Should return the site from the given context containing DummyRequest with site attribute.
        """
        request = RenderServices.DummyRequest(site)

        context_site = RenderServices.site({"request": request})
        assert context_site == site

    @pytest.mark.django_db
    def test_site_none(self, rf):
        """
        Should return None when:
        * There is no request key in context.
        * The request doesn't have a site attribute.
        * The request site attribute is None.
        """
        context = {}

        context_site = RenderServices.site(context)
        assert context_site is None

        context["request"] = rf.get("/")
        context_site = RenderServices.site(context)
        assert context_site is None

        context["request"].site = None
        context_site = RenderServices.site(context)
        assert context_site is None

        context["request"] = RenderServices.DummyRequest(None)
        context_site = RenderServices.site(context)
        assert context_site is None
