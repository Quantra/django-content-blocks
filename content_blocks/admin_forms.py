import json

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from content_blocks.models import (
    ContentBlock,
    ContentBlockField,
    ContentBlockFields,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)
from content_blocks.services.content_block_template import ImportExportServices
from content_blocks.widgets import ChoicesWidget, TemplateFilenameAutocompleteWidget

REQUIRED_ERROR_MSG = "This field is required"


class ContentBlockTemplateAdminForm(forms.ModelForm):
    class Meta:
        model = ContentBlockTemplate
        exclude = []
        widgets = {
            "template_filename": TemplateFilenameAutocompleteWidget(
                "/content_blocks/content_blocks"
            )
        }


def validate_choices(choices):
    try:
        choices = json.loads(choices)
    except json.JSONDecodeError:
        return False

    if not isinstance(choices, list):
        return False

    for choice in choices:
        if not isinstance(choice, list):
            return False

        if not len(choice) == 2:
            return False

    return True


class ContentBlockTemplateFieldAdminForm(forms.ModelForm):
    class Meta:
        model = ContentBlockTemplateField
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["choices"] = forms.CharField(
            widget=ChoicesWidget(),
            help_text="You must provide a value and label for each choice or it will be ignored.",
            required=False,
        )

    def clean(self):
        cleaned_data = super().clean()

        field_type = cleaned_data.get("field_type")

        if field_type == ContentBlockFields.NESTED_FIELD:
            nested_templates = cleaned_data.get("nested_templates")
            if not nested_templates:
                self.add_error("nested_templates", REQUIRED_ERROR_MSG)

            min_num = cleaned_data.get("min_num")
            max_num = cleaned_data.get("max_num")

            if min_num > max_num:
                self.add_error(
                    "min_num", "Min num must be less than or equal to max num."
                )
                self.add_error(
                    "max_num", "Max num must be greater than or equal to min num."
                )

        elif field_type == ContentBlockFields.CHOICE_FIELD:
            choices = cleaned_data.get("choices")
            if not choices:
                self.add_error("choices", REQUIRED_ERROR_MSG)
            elif not validate_choices(choices):
                # Validate choices
                self.add_error("choices", "Invalid choices")

        elif field_type == ContentBlockFields.MODEL_CHOICE_FIELD:
            model_choice_content_type = cleaned_data.get("model_choice_content_type")
            if not model_choice_content_type:
                self.add_error("model_choice_content_type", REQUIRED_ERROR_MSG)

        if self.instance.pk and "field_type" in self.changed_data:
            self.add_error("field_type", "Field type cannot be changed after save")

        return cleaned_data

    def save(self, commit=True):
        """
        Update content block fields based on this template field.
        """
        template_field = super().save(commit=False)

        created = False if template_field.pk else True

        # Find existing content blocks using this field
        content_blocks = ContentBlock.objects.filter(
            content_block_template=template_field.content_block_template
        )
        create_content_block_fields = created and content_blocks.exists()

        if commit or create_content_block_fields:
            template_field.save()
            self.save_m2m()

        if create_content_block_fields:
            # Create a new field for existing content blocks
            for content_block in content_blocks:
                ContentBlockField.objects.create(
                    template_field=template_field,
                    content_block=content_block,
                    field_type=template_field.field_type,
                )

        return template_field


class ContentBlockTemplateImportForm(forms.Form):
    fixture_file = forms.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["json"])]
    )

    def clean_fixture_file(self):
        """
        Validate the uploaded file is JSON.
        """
        fixture_file = self.cleaned_data["fixture_file"]
        value = fixture_file.read()

        try:
            json.loads(value)
        except json.JSONDecodeError:
            fixture_file.close()
            raise ValidationError("The file is not valid JSON.")

        return fixture_file

    def import_content_block_templates(self, fixture_file):
        """
        Only call this after testing is_valid()
        :param fixture_file: The file from request.FILES
        """
        with fixture_file.open() as file:
            ImportExportServices.import_content_block_templates(file)
