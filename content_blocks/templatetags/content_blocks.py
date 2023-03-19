"""
Content blocks template tags.
"""
from django import template

from content_blocks.models import ContentBlockCollection

register = template.Library()


@register.inclusion_tag("content_blocks/content_block_collection.html")
def content_block_collection(content_block_collection_slug):
    """
    Render content blocks for a ContentBlockCollection given the collection's slug.
    """
    context = {"slug": content_block_collection_slug}

    try:
        collection = ContentBlockCollection.objects.get(
            slug=content_block_collection_slug
        )
        context.update({"content_block_collection": collection})
    except ContentBlockCollection.DoesNotExist:
        pass

    return context
