"""
Content Blocks abstract_models.py
"""

from django.db import models
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string

from content_blocks.cache import cache


class VisibleManager(models.Manager):
    def visible(self):
        return self.get_queryset().filter(visible=True)


class VisibleModel(models.Model):
    visible = models.BooleanField(default=True, help_text="Uncheck to hide this.")

    class Meta:
        abstract = True


class AutoDateModel(models.Model):
    create_date = models.DateTimeField("Creation Date", auto_now_add=True)
    mod_date = models.DateTimeField("Last Modified", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-create_date"]


class PositionModel(models.Model):
    position = models.PositiveIntegerField(
        default=0, help_text="Set a custom ordering. Lower numbers appear first."
    )

    class Meta:
        abstract = True
        ordering = ["position"]


class CachedHtmlModel(models.Model):
    """
    Provides methods for cacheing objects html output and managing the cache.
    """

    _can_render = None
    context_name = "object"
    cache_prefix = None

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.clear_cache()
        return super().delete(using=using, keep_parents=keep_parents)

    @property
    def template(self):
        """
        Must be overridden and return full path to template
        :return:
        """
        raise NotImplementedError  # pragma: no cover

    @property
    def context(self):
        """
        Provided to be overridden with custom context for the object
        :return:
        """
        return self  # pragma: no cover

    @property
    def cache_key(self):
        """
        Set the cache prefix to something unique
        :return:
        """
        if not self.cache_prefix:
            raise NotImplementedError  # pragma: no cover

        return f"{self.cache_prefix}_{self.id}"

    @property
    def can_render(self):
        """
        Does the template exist
        :return:
        """
        if not self.template:
            return False
        try:
            get_template(self.template)
            return True
        except TemplateDoesNotExist:
            return False

    def render(self):  # pragma: no cover
        """
        Render html for this object and cache
        """
        if not self.can_render:
            return ""

        html = cache.get(self.cache_key)
        if not html:
            html = render_to_string(self.template, {self.context_name: self.context})
            cache.set(self.cache_key, html)
        return html

    def clear_cache(self):
        """
        Clear the cache for this object
        """
        cache.delete(self.cache_key)

    def update_cache(self):
        """
        Update the cache for this object
        :return:
        """
        cache.delete(self.cache_key)
        self.render()
