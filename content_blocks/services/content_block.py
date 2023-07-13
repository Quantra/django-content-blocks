from django.template.loader import render_to_string

from content_blocks.models import ContentBlockFields


class ContentBlockFilters:
    """
    ContentBlock queryset filters.
    """


class RenderServices:
    """
    Services for rendering ContentBlock to html.
    """

    # todo review this. render_content_block/render_html can be combined.  Addition of sites is probably not needed.

    @staticmethod
    def render_content_block(content_block, context=None):
        """
        Main render method.  Used by ContentBlock.render and {% render_content_block %}
        :return: Rendered html for the content block.
        """
        return RenderServices.render_html(content_block, context)

    class DummyRequest:
        """
        DummyRequest to hold a site attribute. In no other way similar to an actual request.
        """

        def __init__(self, site):
            self.site = site
            self.META = {}
            self.session = {}

    @staticmethod
    def render_html(content_block, context=None, site=None):
        """
        Render the html for the given ContentBlock.
        :context: Dictionary of context to render the template with.
        :site: If a Site is supplied and there is no request context set it in the context under request.site
        :return: Rendered html for the content block.
        """
        if not content_block.can_render:
            return ""

        render_context = RenderServices.context(content_block, context=context)
        request = render_context.get("request")
        if request is None and site is not None:
            render_context["request"] = RenderServices.DummyRequest(site)

        html = render_to_string(content_block.template, render_context, request=request)
        return html

    @staticmethod
    def context(content_block, context=None):
        """
        Adds the ContentBlock.context and ContentBlock to supplied context or creates new context.
        :return: Context dictionary to be used when rendering html.
        """
        render_context = context or {}
        render_context[content_block.context_name] = content_block.context
        render_context[f"{content_block.context_name}_object"] = content_block
        return render_context

    @staticmethod
    def site(context):
        """
        :return: The site from the given context if possible.
        """
        if not context:
            return None

        request = context.get("request")
        site = getattr(request, "site", None)
        return site


class CloneServices:
    """
    Services for cloning ContentBlock.
    """

    @staticmethod
    def clone_content_block(content_block, attrs=None):
        """
        Clones the given content block and all content block fields.
        """
        new_content_block = content_block.make_clone(attrs=attrs)

        for field in content_block.content_block_fields.all():
            new_field = field.make_clone(attrs={"content_block": new_content_block})

            if field.template_field.field_type == ContentBlockFields.NESTED_FIELD:
                for nested_block in field.content_blocks.all():
                    CloneServices.clone_content_block(
                        nested_block, attrs={"parent": new_field}
                    )

        return new_content_block
