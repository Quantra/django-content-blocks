import xml.etree.ElementTree as et
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    get_available_image_extensions,
)
from django.db import models
from django.db.models import FileField
from django.db.models.fields.files import FieldFile


def validate_svg(f):
    f.seek(0)
    tag = None
    try:
        for event, el in et.iterparse(f, ("start",)):
            tag = el.tag
            break
    except et.ParseError:
        pass

    if tag != "{http://www.w3.org/2000/svg}svg":
        raise ValidationError("Uploaded file is not an image or SVG file.")

    f.seek(0)

    return f


class SVGAndImageFieldFormField(forms.ImageField):
    default_validators = [
        FileExtensionValidator(
            allowed_extensions=get_available_image_extensions() + ["svg"]
        )
    ]

    def to_python(self, data):
        try:
            f = super().to_python(data)
        except ValidationError:
            return validate_svg(data)

        return f


class SVGAndImageField(models.ImageField):
    def formfield(self, **kwargs):
        defaults = {"form_class": SVGAndImageFieldFormField}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class FieldVideo(FieldFile):
    @property
    def file_extension(self):
        return Path(self.name).suffix[1:]


class VideoField(FileField):
    attr_class = FieldVideo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validators.append(
            FileExtensionValidator(allowed_extensions=["mp4", "webm", "ogg"])
        )
