"""
Content Blocks abstract_models.py
"""

from django.db import models


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
