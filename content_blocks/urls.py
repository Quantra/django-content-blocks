"""
Content Blocks urls.py
"""
from django.urls import path

from content_blocks.views import (
    content_block_delete,
    content_block_save,
    toggle_visible,
    update_position,
)

app_name = "content_blocks"
urlpatterns = [
    path(
        "_ajax/<int:content_block_id>/save/",
        content_block_save,
        name="content_block_save",
    ),
    path("_ajax/update-position/", update_position, name="update_position"),
    path(
        "_ajax/<int:content_block_id>/toggle-visible/",
        toggle_visible,
        name="toggle_visible",
    ),
    path(
        "_ajax/<int:content_block_id>/delete/",
        content_block_delete,
        name="content_block_delete",
    ),
]
