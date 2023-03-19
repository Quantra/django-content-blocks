from django.contrib import admin

from content_blocks.admin import ContentBlockModelAdmin

from .models import Page


@admin.register(Page)
class PageAdmin(ContentBlockModelAdmin):
    list_display = ["__str__", "content_blocks_link"]

    fieldsets = (
        (
            "Page",
            {"fields": ["slug", "content_blocks_button"]},
        ),
    )
