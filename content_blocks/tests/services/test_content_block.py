import pytest
from faker import Faker
from pytest_lazyfixture import lazy_fixture

from content_blocks.conf import settings as content_blocks_settings
from content_blocks.models import ContentBlock
from content_blocks.services.content_block import CacheServices, RenderServices, cache
from example.pages.models import Page, PageSite, PageSites

faker = Faker()


class TestCacheServices:
    @pytest.mark.django_db
    def test_cache_key(self, content_block):
        """
        The cache key should be {cache_prefix}_{id} when no site is supplied.
        """
        cache_prefix = content_blocks_settings.CONTENT_BLOCKS_CACHE_PREFIX
        assert (
            CacheServices.cache_key(content_block)
            == f"{cache_prefix}_{content_block.id}"
        )

    @pytest.mark.django_db
    def test_cache_key_site(self, content_block, site):
        """
        The cache key should be {cache_prefix}_{id}_site_{site_id} when site is supplied.
        """
        cache_prefix = content_blocks_settings.CONTENT_BLOCKS_CACHE_PREFIX
        assert (
            CacheServices.cache_key(content_block, site)
            == f"{cache_prefix}_{content_block.id}_site_{site.id}"
        )

    @pytest.mark.django_db
    @pytest.mark.parametrize("site_p", [None, lazy_fixture("site")])
    def test_get_cache(self, text_content_block, site_p):
        """
        Should return the cached html for the given ContentBlock.
        """
        cache_key = CacheServices.cache_key(text_content_block, site=site_p)

        cached_html = cache.get(cache_key)
        assert cached_html is None

        html = faker.text()
        cache.set(cache_key, html)

        cached_html = CacheServices.get_cache(text_content_block, site=site_p)

        assert cached_html is not None
        assert cached_html == html

    @pytest.mark.django_db
    @pytest.mark.parametrize("site_p", [None, lazy_fixture("site")])
    def test_set_cache(self, text_content_block, site_p):
        """
        Should set the provided html in the cache under the key for the ContentBlock and Site if provided.
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
    @pytest.mark.parametrize("site_p", [None, lazy_fixture("site")])
    def test_delete_cache(self, text_content_block, site_p):
        """
        Should delete the provided html in the cache under the key for the ContentBlock and Site if provided.
        """
        cache_key = CacheServices.cache_key(text_content_block, site=site_p)
        html = faker.text()

        cached_html = cache.get(cache_key)
        assert cached_html is None

        cache.set(cache_key, html)

        cached_html = cache.get(cache_key)
        assert cached_html == html

        CacheServices.delete_cache(text_content_block, site=site_p)

        cached_html = cache.get(cache_key)
        assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize("site_p", [None, lazy_fixture("site")])
    @pytest.mark.parametrize(
        "context_p",
        [None, faker.pydict(), {"request": lazy_fixture("request_with_site")}],
    )
    def test_get_or_set_cache(self, text_content_block, site_p, context_p):
        """
        Should set the cache the first time it's called and get from cache on the next call.
        """
        cache_key = CacheServices.cache_key(text_content_block, site=site_p)

        # Check cache is empty
        cached_html = cache.get(cache_key)
        assert cached_html is None

        # Get or set and assert the returned html is in the cache
        html = CacheServices.get_or_set_cache(
            text_content_block, context=context_p, site=site_p
        )
        cached_html = cache.get(cache_key)
        assert cached_html is not None
        assert cached_html == html

        # Change the cached html in the cache directly and assert we get this back
        cached_html = faker.text()
        cache.set(cache_key, cached_html)
        html = CacheServices.get_or_set_cache(
            text_content_block, context=context_p, site=site_p
        )
        assert html == cached_html

    @pytest.mark.django_db
    @pytest.mark.parametrize("num_sites", [1, 9])
    def test_get_or_set_cache_per_site(
        self, text_content_block, site_factory, num_sites
    ):
        """
        Should set the cache the first time it's called only.
        The cache should be set for each site.
        """
        sites = site_factory.create_batch(num_sites)

        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)

            # Check cache is empty
            cached_html = cache.get(cache_key)
            assert cached_html is None

        CacheServices.get_or_set_cache_per_site(text_content_block, sites)

        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            # Assert the cached html matches what would be rendered
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == RenderServices.render_html(
                text_content_block, site=site
            )

        # Change the html in the cache directly
        html = faker.text()
        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            cache.set(cache_key, html)

        CacheServices.get_or_set_cache_per_site(text_content_block, sites)

        # Confirm the cache wasn't updated this time
        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            cached_html = cache.get(cache_key)
            assert cached_html == html

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    @pytest.mark.parametrize("num_sites", [1, 9])
    def test_get_or_set_cache_parent_model_sites(
        self, text_content_blocks, page_sites, site_factory, num_sites
    ):
        """
        Should set the cache on first call only.
        Should cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has a M2M to Site.
        """
        sites = site_factory.create_batch(num_sites)
        # Set up a Page/PageSites model with several sites.
        for site in sites:
            page_sites.sites.add(site)

        # Set up several text_content_block and add them to the PageSites.
        for content_block in text_content_blocks:
            page_sites.content_blocks.add(content_block)

            # Confirm the cache is empty
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                cached_html = cache.get(cache_key)
                assert cached_html is None

        CacheServices.get_or_set_cache_parent_model(PageSites)

        # Confirm the cache is not empty and is what is expected
        htmls = {}
        for content_block in text_content_blocks:
            site_htmls = {}
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                cached_html = cache.get(cache_key)
                assert cached_html is not None
                assert cached_html == RenderServices.render_html(
                    content_block, site=site
                )

                # Update the cache directly (for the next assertions)
                html = faker.text()
                cache.set(cache_key, html)
                site_htmls[site] = html

            htmls[content_block] = site_htmls

        CacheServices.get_or_set_cache_parent_model(PageSites)

        # Confirm the cache was not updated and is not empty
        for content_block in text_content_blocks:
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                cached_html = cache.get(cache_key)
                assert cached_html is not None
                assert cached_html == htmls[content_block][site]

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    def test_get_or_set_cache_parent_model_site(
        self, text_content_blocks, page_site_factory, site
    ):
        """
        Should set the cache on first call only.
        Should cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has a FK to Site.
        """
        # Set up a PageSite model with several sites.
        page_site = page_site_factory.create(site=site)

        # Set up several text_content_block and add them to the PageSites.
        for content_block in text_content_blocks:
            page_site.content_blocks.add(content_block)

            # Confirm the cache is empty
            cache_key = CacheServices.cache_key(content_block, site)
            cached_html = cache.get(cache_key)
            assert cached_html is None

        CacheServices.get_or_set_cache_parent_model(PageSite)

        # Confirm the cache is not empty and is what is expected
        htmls = {}
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block, site)
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == RenderServices.render_html(content_block, site=site)

            # Update the cache directly (for the next assertions)
            html = faker.text()
            cache.set(cache_key, html)
            htmls[content_block] = html

        CacheServices.get_or_set_cache_parent_model(PageSite)

        # Confirm the cache was not updated and is not empty
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block, site)
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == htmls[content_block]

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    def test_get_or_set_cache_parent_model(self, text_content_blocks, page):
        """
        Should set the cache on first call only.
        Should cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has no relation to Site.
        """
        # Set up several text_content_block and add them to the PageSites.
        for content_block in text_content_blocks:
            page.content_blocks.add(content_block)

            # Confirm the cache is empty
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            assert cached_html is None

        CacheServices.get_or_set_cache_parent_model(Page)

        # Confirm the cache is not empty and is what is expected
        htmls = {}
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == RenderServices.render_html(content_block)

            # Update the cache directly (for the next assertions)
            html = faker.text()
            cache.set(cache_key, html)
            htmls[content_block] = html

        CacheServices.get_or_set_cache_parent_model(PageSite)

        # Confirm the cache was not updated and is not empty
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == htmls[content_block]

    @pytest.mark.django_db
    @pytest.mark.parametrize("disable_cache", [False, True])
    @pytest.mark.parametrize("text_content_blocks", [1, 2, 24], indirect=True)
    def test_get_or_set_cache_all(
        self,
        settings,
        disable_cache,
        text_content_blocks,
        page,
        content_block_collection,
    ):
        """
        Should set the cache for all ContentBlock on first call and get from cache on next call.
        """
        settings.CONTENT_BLOCKS_DISABLE_CACHE = disable_cache
        # Setup several text content block and assert cache is empty

        def assert_cache_empty(cb):
            cache_key = CacheServices.cache_key(cb)
            cached_html = cache.get(cache_key)
            assert cached_html is None

        for content_block in text_content_blocks[::2]:
            page.content_blocks.add(content_block)
            assert_cache_empty(content_block)

        for content_block in text_content_blocks[1::2]:
            content_block_collection.content_blocks.add(content_block)
            assert_cache_empty(content_block)

        CacheServices.get_or_set_cache_all()

        # Assert the cache is correctly populated
        htmls = {}
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            rendered_html = RenderServices.render_html(content_block)
            if not disable_cache:
                assert cached_html is not None
                assert cached_html == rendered_html
            else:
                assert cached_html is None

            # Update the cache directly (for the next assertions)
            html = faker.text()
            cache.set(cache_key, html)
            htmls[content_block] = html

        CacheServices.get_or_set_cache_all()

        # Assert the cache was not updated
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == htmls[content_block]

    @pytest.mark.django_db
    @pytest.mark.parametrize("site_p", [None, lazy_fixture("site")])
    def test_set_cache_content_block(self, site_p, text_content_block):
        """
        Should render the html for the given ContentBlock and set it in the cache.
        """
        cache_key = CacheServices.cache_key(text_content_block, site=site_p)
        cached_html = cache.get(cache_key)
        assert cached_html is None

        html = RenderServices.render_html(text_content_block, site=site_p)

        CacheServices.set_cache_content_block(text_content_block, site=site_p)

        cached_html = cache.get(cache_key)
        assert cached_html is not None
        assert cached_html == html

    @pytest.mark.django_db
    @pytest.mark.parametrize("num_sites", [1, 9])
    def test_set_cache_per_site(self, text_content_block, site_factory, num_sites):
        """
        Should set the cache.
        The cache should be set for each site.
        """
        sites = site_factory.create_batch(num_sites)

        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)

            # Check cache is empty
            cached_html = cache.get(cache_key)
            assert cached_html is None

        CacheServices.set_cache_per_site(text_content_block, sites)

        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            # Assert the cached html matches what would be rendered
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == RenderServices.render_html(
                text_content_block, site=site
            )

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    @pytest.mark.parametrize("num_sites", [1, 9])
    @pytest.mark.parametrize("queryset", [None, True])
    def test_set_cache_parent_model_sites(
        self, text_content_blocks, page_sites, site_factory, num_sites, queryset
    ):
        """
        Should set the cache on first call only.
        Should cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has a M2M to Site.
        """
        sites = site_factory.create_batch(num_sites)
        # Set up a Page/PageSites model with several sites.
        for site in sites:
            page_sites.sites.add(site)

        # Set up several text_content_block and add them to the PageSites.
        for content_block in text_content_blocks:
            page_sites.content_blocks.add(content_block)

            # Confirm the cache is empty
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                cached_html = cache.get(cache_key)
                assert cached_html is None

        # Setup queryset
        if queryset is not None:
            queryset = ContentBlock.objects.filter(
                id__in=[cb.id for cb in text_content_blocks[::2]]
            )

        CacheServices.set_cache_parent_model(PageSites, queryset=queryset)

        # Confirm the cache is not empty and is what is expected
        for content_block in text_content_blocks:
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                cached_html = cache.get(cache_key)

                if queryset is None or queryset.filter(id=content_block.id).exists():
                    assert cached_html is not None
                    assert cached_html == RenderServices.render_html(
                        content_block, site=site
                    )
                else:
                    assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    @pytest.mark.parametrize("queryset", [None, True])
    @pytest.mark.parametrize(
        "parent,site_p",
        [
            [lazy_fixture("content_block_collection"), None],
            [lazy_fixture("page_site"), lazy_fixture("site")],
            [lazy_fixture("page_site"), None],
        ],
    )
    def test_set_cache_parent_model_site(
        self, text_content_blocks, site_p, queryset, parent
    ):
        """
        Should set the cache.
        Should cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has a FK to Site.
        """
        try:
            parent.site = site_p
            parent.save()
        except AttributeError:
            pass

        # Set up several text_content_block and add them to the PageSites.
        for content_block in text_content_blocks:
            parent.content_blocks.add(content_block)

            # Confirm the cache is empty
            cache_key = CacheServices.cache_key(content_block, site_p)
            cached_html = cache.get(cache_key)
            assert cached_html is None

        # Setup queryset
        if queryset is not None:
            queryset = ContentBlock.objects.filter(
                id__in=[cb.id for cb in text_content_blocks[::2]]
            )

        CacheServices.set_cache_parent_model(type(parent), queryset=queryset)

        # Confirm the cache is not empty and is what is expected
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block, site_p)
            cached_html = cache.get(cache_key)

            if queryset is None or queryset.filter(id=content_block.id).exists():
                assert cached_html is not None
                assert cached_html == RenderServices.render_html(
                    content_block, site=site_p
                )
            else:
                assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize("disable_cache", [False, True])
    @pytest.mark.parametrize("queryset", [None, True])
    @pytest.mark.parametrize("text_content_blocks", [1, 2, 24], indirect=True)
    def test_set_cache_all(
        self,
        settings,
        disable_cache,
        text_content_blocks,
        page,
        content_block_collection,
        queryset,
    ):
        """
        Should set the cache for all ContentBlock.
        """
        settings.CONTENT_BLOCKS_DISABLE_CACHE = disable_cache
        # Setup several text content block and assert cache is empty

        def assert_cache_empty(cb):
            cache_key = CacheServices.cache_key(cb)
            cached_html = cache.get(cache_key)
            assert cached_html is None

        for content_block in text_content_blocks[::2]:
            page.content_blocks.add(content_block)
            assert_cache_empty(content_block)

        for content_block in text_content_blocks[1::2]:
            content_block_collection.content_blocks.add(content_block)
            assert_cache_empty(content_block)

        # Setup queryset
        if queryset is not None:
            queryset = ContentBlock.objects.filter(
                id__in=[cb.id for cb in text_content_blocks[::2]]
            )

        CacheServices.set_cache_all(queryset=queryset)

        # Assert the cache is correctly populated
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            rendered_html = RenderServices.render_html(content_block)
            if not disable_cache and (
                queryset is None or queryset.filter(id=content_block.id).exists()
            ):
                assert cached_html is not None
                assert cached_html == rendered_html
            else:
                assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "parent,site_p",
        [
            [lazy_fixture("content_block_collection"), None],
            [lazy_fixture("page_site"), lazy_fixture("site")],
            [lazy_fixture("page_site"), None],
        ],
    )
    def test_set_cache_content_block_parent(self, text_content_block, parent, site_p):
        """
        Should set the cache for the given content block across all sites based on the parent.
        Tests the case of a parent with single site or none.
        """
        try:
            parent.site = site_p
        except AttributeError:
            pass

        parent.content_blocks.add(text_content_block)

        html = RenderServices.render_html(text_content_block, site=site_p)

        cache_key = CacheServices.cache_key(text_content_block, site=site_p)
        cached_html = cache.get(cache_key)
        assert cached_html is None

        CacheServices.set_cache_content_block_parent(text_content_block, parent)

        cached_html = cache.get(cache_key)
        assert cached_html is not None
        assert cached_html == html

    @pytest.mark.django_db
    @pytest.mark.parametrize("num_sites", [1, 9])
    def test_set_cache_content_block_parent_sites(
        self, text_content_block, site_factory, num_sites, page_sites
    ):
        """
        Should set the cache for the given content block across all sites based on the parent.
        Tests the case of a parent with multiple sites.
        """
        page_sites.content_blocks.add(text_content_block)

        sites = site_factory.create_batch(num_sites)
        for site in sites:
            page_sites.sites.add(site)
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            cached_html = cache.get(cache_key)
            assert cached_html is None

        CacheServices.set_cache_content_block_parent(text_content_block, page_sites)

        for site in sites:
            html = RenderServices.render_html(text_content_block, site=site)
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == html

    @pytest.mark.django_db
    @pytest.mark.parametrize("num_sites", [1, 9])
    def test_delete_cache_per_site(self, text_content_block, site_factory, num_sites):
        """
        Should delete the cache.
        The cache should be deleted for each site.
        """
        sites = site_factory.create_batch(num_sites)

        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)

            html = faker.text()
            cache.set(cache_key, html)

            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == html

        CacheServices.delete_cache_per_site(text_content_block, sites)

        for site in sites:
            cache_key = CacheServices.cache_key(text_content_block, site=site)
            cached_html = cache.get(cache_key)
            assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    @pytest.mark.parametrize(
        "parent,site_p",
        [
            [lazy_fixture("content_block_collection"), None],
            [lazy_fixture("page_site"), lazy_fixture("site")],
            [lazy_fixture("page_site"), None],
        ],
    )
    def test_delete_cache_parent_model_site(self, text_content_blocks, site_p, parent):
        """
        Should delete the cache.
        Should delete cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has a FK to Site.
        """
        try:
            parent.site = site_p
            parent.save()
        except AttributeError:
            pass

        # Set up several text_content_block and add them to the PageSite.
        for content_block in text_content_blocks:
            parent.content_blocks.add(content_block)

            # Set the cache
            cache_key = CacheServices.cache_key(content_block, site_p)
            html = faker.text()
            cache.set(cache_key, html)

            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == html

        CacheServices.delete_cache_parent_model(type(parent))

        # Confirm the cache is now empty
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block, site_p)
            cached_html = cache.get(cache_key)
            assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 9], indirect=True)
    @pytest.mark.parametrize("num_sites", [1, 9])
    def test_delete_cache_parent_model_sites(
        self, text_content_blocks, page_sites, site_factory, num_sites
    ):
        """
        Should delete the cache.
        Should delete cache per site if the parent has a sites_field attribute.
        Tests the case where the parent model has a M2M to Site.
        """
        sites = site_factory.create_batch(num_sites)
        # Set up a Page/PageSites model with several sites.
        for site in sites:
            page_sites.sites.add(site)

        # Set up several text_content_block and add them to the PageSites.
        for content_block in text_content_blocks:
            page_sites.content_blocks.add(content_block)

            # Set the cache
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                html = RenderServices.render_html(content_block, site=site)
                cache.set(cache_key, html)

                cached_html = cache.get(cache_key)
                assert cached_html is not None
                assert cached_html == html

        CacheServices.delete_cache_parent_model(PageSites)

        # Confirm the cache is not empty and is what is expected
        for content_block in text_content_blocks:
            for site in sites:
                cache_key = CacheServices.cache_key(content_block, site)
                cached_html = cache.get(cache_key)

                assert cached_html is None

    @pytest.mark.django_db
    @pytest.mark.parametrize("text_content_blocks", [1, 2, 24], indirect=True)
    def test_delete_cache_all(
        self,
        text_content_blocks,
        page,
        content_block_collection,
    ):
        """
        Should delete the cache for all ContentBlock.
        """

        def set_cache(cb):
            cache_key = CacheServices.cache_key(cb)
            html = faker.text()
            cache.set(cache_key, html)

            cached_html = cache.get(cache_key)
            assert cached_html is not None
            assert cached_html == html

        for content_block in text_content_blocks[::2]:
            page.content_blocks.add(content_block)
            set_cache(content_block)

        for content_block in text_content_blocks[1::2]:
            content_block_collection.content_blocks.add(content_block)
            set_cache(content_block)

        CacheServices.delete_cache_all()

        # Assert the cache is correctly populated
        for content_block in text_content_blocks:
            cache_key = CacheServices.cache_key(content_block)
            cached_html = cache.get(cache_key)
            assert cached_html is None


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
