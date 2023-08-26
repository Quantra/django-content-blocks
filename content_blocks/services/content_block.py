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

    @staticmethod
    def render_content_block(content_block, context=None):
        """
        Render the html for the given ContentBlock.
        :context: Dictionary of context to render the template with.
        :return: Rendered html for the content block.
        """
        if not content_block.can_render:
            return ""

        context = RenderServices.context(content_block, context=context)
        html = render_to_string(content_block.template, context)
        return html

    @staticmethod
    def context(content_block, context=None):
        """
        Adds the ``ContentBlock.context`` and ``ContentBlock`` to supplied context or creates new context.
        :return: Context dictionary to be used when rendering html.
        """
        context = context or {}
        context[content_block.context_name] = content_block.context
        context[f"{content_block.context_name}_object"] = content_block
        return context


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
