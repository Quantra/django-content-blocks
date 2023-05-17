from django.db import models
from django.urls import reverse

from content_blocks.models import ContentBlockParentModel


class PageModel(models.Model):
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.slug or "Home"

    def get_absolute_url(self):
        if self.slug:
            return reverse("page_detail", args=[self.slug])
        return reverse("home")

    @property
    def preview_url(self):
        if self.slug:
            return reverse("page_detail_preview", args=[self.slug])
        return reverse("home_preview")


class Page(PageModel, ContentBlockParentModel):
    pass


class PageSites(PageModel, ContentBlockParentModel):
    """
    Model for testing when parent has M2M to Site.
    """

    sites = models.ManyToManyField("sites.Site", blank=True)

    @property
    def content_blocks_sites_field(self):
        return self.sites


class PageSite(PageModel, ContentBlockParentModel):
    """
    Model for testing when parent has FK to Site.
    """

    site = models.ForeignKey(
        "sites.Site", blank=True, null=True, on_delete=models.CASCADE
    )

    @property
    def content_blocks_sites_field(self):
        return self.site
