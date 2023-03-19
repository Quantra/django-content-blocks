from django import template

from content_blocks.forms import ContentBlockForm, NewNestedBlockForm

register = template.Library()


@register.simple_tag
def content_block_form(content_block):
    return ContentBlockForm(content_block=content_block)


@register.simple_tag
def new_nested_block_form(parent):
    return NewNestedBlockForm(
        initial={
            "parent": parent,
        }
    )


@register.simple_tag
def app_model_label(obj):
    return f"{obj._meta.app_label}.{obj._meta.model.__name__}"
