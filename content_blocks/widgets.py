import uuid
from pathlib import Path

from django import forms, template
from django.contrib.admin.widgets import AdminTextInputWidget
from django.utils.text import slugify


class FileWidget(forms.ClearableFileInput):
    template_name = "content_blocks/widgets/clearable_file.html"

    def clear_checkbox_id(self, name):
        return uuid.uuid4().hex


class TemplateFilenameAutocompleteWidget(AdminTextInputWidget):
    """
    Add autocomplete suggestions to text input via datalist.
    Suggestions are template file names in the given template_dir.
    """

    template_name = "content_blocks/widgets/filename_autocomplete.html"

    def __init__(self, template_dir=None, attrs=None):
        self.template_dir = template_dir or ""
        attrs = attrs or {}
        super().__init__(attrs={"list": self.data_list_id, **attrs})

    @property
    def template_list(self):
        template_dirs = []
        for engine in template.engines.all():
            template_dirs += [d for d in engine.template_dirs]

        file_names = []
        for template_dir in template_dirs:
            file_names += [
                p.name
                for p in Path(template_dir).glob(f"**{self.template_dir}/*.html")
                if p
            ]

        return sorted(file_names)

    @property
    def data_list_id(self):
        return f"{slugify(self.template_dir)}__suggestions"

    def get_context(self, *args):
        context = super().get_context(*args)
        context["widget"]["data_list_id"] = self.data_list_id
        context["widget"]["template_list"] = self.template_list
        return context


class ChoicesWidget(forms.HiddenInput):
    template_name = "content_blocks/widgets/choices.html"

    @property
    def is_hidden(self):
        # Show the label in the admin change page.
        return False
