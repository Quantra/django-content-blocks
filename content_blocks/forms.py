from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from content_blocks.models import (
    ContentBlock,
    ContentBlockAvailability,
    ContentBlockField,
    ContentBlockFields,
    ContentBlockTemplate,
)
from content_blocks.services.content_block import CacheServices, CloneServices


class ParentModelForm(forms.Form):
    """
    Adds parent object to form from kwargs.
    """

    parent = None

    def __init__(self, *args, **kwargs):
        self.parent = kwargs.pop("parent")
        super().__init__(*args, **kwargs)


class NewContentBlockFormBase(forms.Form):
    """
    Shared functionality between NewContentBlockForm and NewNestedBlockForm.
    Has a select for content block template.
    """

    content_block_template = forms.ModelChoiceField(
        ContentBlockTemplate.objects.visible(), empty_label=None
    )

    position = forms.CharField(initial=0, widget=forms.HiddenInput())

    auto_id = True

    def __init__(self, *args, **kwargs):
        kwargs["auto_id"] = self.auto_id
        super().__init__(*args, **kwargs)
        self.fields["content_block_template"].queryset = self.get_available_templates()

    def get_available_templates(self):
        """
        Must be provided by subclasses.
        """
        raise NotImplementedError  # pragma: no cover

    def create_content_block(self, content_block_template, draft=False, **kwargs):
        # todo refactor to service class
        content_block = ContentBlock.objects.create(
            content_block_template=content_block_template,
            draft=draft,
            position=self.cleaned_data.get("position", 0),
            **kwargs,
        )

        for (
            template_field
        ) in content_block_template.content_block_template_fields.all():
            content_block_field = ContentBlockField.objects.create(
                content_block=content_block,
                template_field=template_field,
                field_type=template_field.field_type,
                model_choice_content_type=template_field.model_choice_content_type,
            )

            # create min_num nested blocks
            if template_field.field_type == ContentBlockFields.NESTED_FIELD:
                for j in range(template_field.min_num):
                    self.create_content_block(
                        template_field.nested_templates.first(),
                        draft=False,
                        parent=content_block_field,
                    )

        return content_block


class NewContentBlockForm(ParentModelForm, NewContentBlockFormBase):
    """
    Form for creating new top level content blocks.
    Creates new content block object with appropriate fields on save.
    Updates the parent which the content block belongs to m2m on save.
    """

    auto_id = "new_cb_%s"

    def get_available_templates(self):
        # todo refactor to service class
        try:
            content_type = ContentType.objects.get_for_model(self.parent)
            content_block_availability = ContentBlockAvailability.objects.get(
                content_type=content_type
            )
            return content_block_availability.content_block_templates.visible()
        except ContentBlockAvailability.DoesNotExist:
            return ContentBlockTemplate.objects.visible()

    def update_parent_m2m(self, content_block):
        self.parent.content_blocks.add(content_block)

    def save(self):
        # todo call service class
        content_block = self.create_content_block(
            self.cleaned_data["content_block_template"], draft=True
        )
        self.update_parent_m2m(content_block)
        return content_block


class NewNestedBlockForm(NewContentBlockFormBase):
    """
    As per NewContentBlockForm but for adding nested blocks.
    """

    parent = forms.ModelChoiceField(
        widget=forms.HiddenInput(), queryset=ContentBlockField.objects.all()
    )

    auto_id = False

    def get_available_templates(self):
        # todo refactor to service class
        try:
            parent = self.initial["parent"]
            return parent.template_field.nested_templates.visible()
        except KeyError:
            return ContentBlockTemplate.objects.all()

    def save(self):
        # todo call service class
        return self.create_content_block(
            self.cleaned_data["content_block_template"],
            draft=False,
            parent=self.cleaned_data["parent"],
        )


class ContentBlockForm(forms.Form):
    """
    Form for creating and changing content blocks.
    Form fields are generated from the content block fields.
    On save each content block field is updated and saved.
    """

    css_class = forms.CharField(
        max_length=256,
        required=False,
        label="CSS Class",
        help_text="For advanced styling.",
    )

    def __init__(self, *args, **kwargs):
        self.content_block = kwargs.pop("content_block")
        kwargs["auto_id"] = f"id_%s_{self.content_block.id}"
        super().__init__(*args, **kwargs)
        self.set_fields()
        self.fields["css_class"].initial = self.content_block.css_class

    def set_fields(self):
        for key, field in self.content_block.fields.items():
            form_field = field.form_field
            if form_field:
                self.fields[key] = form_field

    def save(self):
        # todo refactor to service class?
        with transaction.atomic():
            for key, field in self.content_block.fields.items():
                if key in self.cleaned_data.keys():
                    field.save_value(self.cleaned_data.get(key))

            self.content_block.css_class = self.cleaned_data.get("css_class")
            self.content_block.saved = True
            self.content_block.save()

            # We no longer manage the cache here as drafts and nested blocks are not cached.

        return self.content_block


class PublishContentBlocksForm(ParentModelForm):
    """
    Form for publishing content blocks.
    Duplicates all content blocks and fields and nested blocks and sets draft=False
    """

    def save(self):
        # todo refactor to service class
        self.parent.content_blocks.published().delete()

        for content_block in self.parent.content_blocks.drafts():
            new_content_block = CloneServices.clone_content_block(
                content_block, attrs={"draft": False}
            )
            self.parent.content_blocks.add(new_content_block)
            # Cache the html
            CacheServices.set_cache_content_block_parent(new_content_block, self.parent)


class ResetContentBlocksForm(ParentModelForm):
    """
    Deletes existing draft content blocks and creates new from published content blocks.
    """

    def save(self):
        # todo refactor to service class
        self.parent.content_blocks.drafts().delete()

        for content_block in self.parent.content_blocks.published():
            new_content_block = CloneServices.clone_content_block(
                content_block, attrs={"draft": True}
            )
            self.parent.content_blocks.add(new_content_block)


class ImportContentBlocksForm(ParentModelForm):
    """
    Import content blocks from another master object of the same type as parent.
    """

    master = forms.ModelChoiceField(None, empty_label=None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["master"].queryset = self.get_master_queryset()

    def get_master_queryset(self):
        return self.parent._meta.model.objects.exclude(id=self.parent.id)

    def save(self):
        # todo refactor to service class
        self.parent.content_blocks.drafts().delete()

        for content_block in self.cleaned_data["master"].content_blocks.drafts():
            new_content_block = CloneServices.clone_content_block(content_block)
            self.parent.content_blocks.add(new_content_block)
