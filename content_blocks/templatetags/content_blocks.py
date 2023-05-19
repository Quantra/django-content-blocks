"""
Content blocks template tags.
"""
from django import template

from content_blocks.models import ContentBlockCollection
from content_blocks.services.content_block import RenderServices

register = template.Library()


@register.inclusion_tag(
    "content_blocks/content_block_collection.html", takes_context=True
)
def content_block_collection(context, content_block_collection_slug):
    """
    Render content blocks for a ContentBlockCollection given the collection's slug.
    """
    context.update({"slug": content_block_collection_slug})

    try:
        collection = ContentBlockCollection.objects.get(
            slug=content_block_collection_slug
        )
        context.update({"content_block_collection": collection})
    except ContentBlockCollection.DoesNotExist:
        pass

    return context


@register.simple_tag(takes_context=True)
def render_content_block(context, content_block):
    """
    Allows rendering of content blocks with request context.  Content blocks should have no_cache=True in this case.
    """

    # Because our context might have RequestContext already in it flatten ourselves
    context_dict = {}
    for d in context.dicts:
        try:
            d = d.flatten()
        except AttributeError:
            pass

        context_dict.update(d)

    return RenderServices.render_content_block(content_block, context=context_dict)


# todo render_content_blocks template tag to render a set of blocks given the parent

# todo render_content_block_previews template tag as above but renders previews
