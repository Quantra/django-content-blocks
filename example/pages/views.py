"""
Page app views.py
"""
from django.shortcuts import get_object_or_404, render

from .models import Page


def page_detail(request, page_slug=None, preview=False):
    """
    Page detail view.
    """
    page_slug = page_slug or ""
    page = get_object_or_404(Page, slug=page_slug)

    content_blocks = (
        page.content_blocks.previews() if preview else page.content_blocks.visible()
    )
    return render(
        request,
        "pages/page_detail.html",
        {
            "page": page,
            "content_blocks": content_blocks,
        },
    )
