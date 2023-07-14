"""
Page app views.py
"""
from django.shortcuts import get_object_or_404, render

from example.pages.models import Page


def page_detail(request, page_slug=None, preview=False):
    """
    Page detail view.
    """
    page_slug = page_slug or ""
    page = get_object_or_404(Page, slug=page_slug)

    content_blocks = (
        page.content_blocks.previews() if preview else page.content_blocks.visible()
    )
    cache_timeout = 0 if preview else 5 * 60
    return render(
        request,
        "pages/page_detail.html",
        {
            "page": page,
            "content_blocks": content_blocks,
            "cache_timeout": cache_timeout,
        },
    )
