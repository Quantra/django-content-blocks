import pytest

from content_blocks.models import ContentBlockCollection, ContentBlockParentModel
from content_blocks.services.content_block_parent import ParentServices
from example.pages.models import Page, PageSite, PageSites


class TestParentServices:
    @pytest.mark.django_db
    def test_parent_models(self):
        """
        Should return a list of all parent models.
        """
        parent_models = [ContentBlockCollection, Page, PageSites, PageSite]

        parent_models_from_service = ParentServices.parent_models(
            ContentBlockParentModel
        )

        assert parent_models_from_service == parent_models

    @pytest.mark.django_db
    def test_parent_sites_m2m(self, page_sites, site_factory):
        """
        Should return .all() of the sites m2m.
        """
        for j in range(4):
            site = site_factory.create()
            page_sites.sites.add(site)

        sites = ParentServices.parent_sites(page_sites)

        assert list(sites) == list(page_sites.sites.all())

    @pytest.mark.django_db
    def test_parent_sites_fk(self, page_site_factory, site):
        """
        Should return a list containing the FK object.
        """
        page_site = page_site_factory.create(site=site)

        sites = ParentServices.parent_sites(page_site)

        assert sites == [site]

    @pytest.mark.django_db
    def test_parent_sites_none(self, page):
        """
        Should return [None]
        """
        sites = ParentServices.parent_sites(page)

        assert sites == [None]
