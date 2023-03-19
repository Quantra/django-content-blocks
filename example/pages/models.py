from django.db import models
from django.urls import reverse

from content_blocks.models import ContentBlockParentModel


class Page(ContentBlockParentModel):
    slug = models.SlugField(unique=True, blank=True)

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
