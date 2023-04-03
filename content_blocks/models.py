"""
Content Blocks models.py
"""
import json
import logging

from django import forms
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import get_storage_class
from django.core.validators import RegexValidator
from django.db import models
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from model_clone import CloneMixin

from content_blocks.abstract_models import (
    AutoDateModel,
    CachedHtmlModel,
    PositionModel,
    VisibleManager,
    VisibleModel,
)
from content_blocks.cache import cache
from content_blocks.conf import settings
from content_blocks.fields import (
    SVGAndImageField,
    SVGAndImageFieldFormField,
    VideoField,
)
from content_blocks.widgets import FileWidget

logger = logging.getLogger(__name__)

if (
    "django_cleanup" in settings.INSTALLED_APPS
    or "django_cleanup.apps.CleanupConfig" in settings.INSTALLED_APPS
):
    from django_cleanup.cleanup import cleanup_ignore
else:
    # noop shim for when django_cleanup isn't installed
    def cleanup_ignore(cls):  # pragma: no cover (covered in settings specific tests)
        return cls


class ContentBlockFields:
    # todo replace this with models.TextChoices
    TEXT_FIELD = "TextField"
    CONTENT_FIELD = "ContentField"
    IMAGE_FIELD = "ImageField"
    NESTED_FIELD = "NestedField"
    CHECKBOX_FIELD = "CheckboxField"
    CHOICE_FIELD = "ChoiceField"
    MODEL_CHOICE_FIELD = "ModelChoiceField"
    FILE_FIELD = "FileField"
    VIDEO_FIELD = "VideoField"
    EMBEDDED_VIDEO_FIELD = "EmbeddedVideoField"

    CHOICES = (
        (TEXT_FIELD, "Text Field"),
        (CONTENT_FIELD, "Content Field"),
        (IMAGE_FIELD, "Image Field"),
        (VIDEO_FIELD, "Video Field"),
        (FILE_FIELD, "File Field"),
        (EMBEDDED_VIDEO_FIELD, "Embedded Video Field"),
        (NESTED_FIELD, "Nested Field"),
        (MODEL_CHOICE_FIELD, "Model Choice Field"),
        (CHOICE_FIELD, "Choice Field"),
        (CHECKBOX_FIELD, "Checkbox Field"),
    )


class ContentBlockFieldManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("template_field")


def get_storage(field_type):
    """
    Get the storage class from dotted strings in settings.
    If the field storage class is in settings use that otherwise use the general storage class setting for content
    blocks, which will default to STORAGES["default"].
    :param field_type:
    :return:
    """
    storage_setting = getattr(settings, field_type, None)
    if storage_setting is not None:
        return get_storage_class(
            storage_setting
        )()  # pragma: no cover (covered by settings specific tests)
    return get_storage_class(settings.CONTENT_BLOCKS_STORAGE)()


def image_storage():
    return get_storage("CONTENT_BLOCKS_IMAGE_STORAGE")


def file_storage():
    return get_storage("CONTENT_BLOCKS_FILE_STORAGE")


def video_storage():
    return get_storage("CONTENT_BLOCKS_VIDEO_STORAGE")


@cleanup_ignore
class ContentBlockField(models.Model, CloneMixin):
    """
    Base model for all content block field models.
    """

    objects = ContentBlockFieldManager()
    template_field = models.ForeignKey(
        "content_blocks.ContentBlockTemplateField",
        on_delete=models.CASCADE,
        related_name="fields",
    )

    content_block = models.ForeignKey(
        "content_blocks.ContentBlock",
        on_delete=models.CASCADE,
        related_name="content_block_fields",
    )

    # duplicate from template_field here because it can't be changed on template field and seems impossible to have
    # select_related working in the __init__
    # todo fix the maxlength here 32 is more like it
    field_type = models.CharField(max_length=256)

    text = models.CharField(max_length=256, blank=True)
    content = models.TextField(blank=True)
    checkbox = models.BooleanField(blank=True, default=False)
    image = SVGAndImageField(
        upload_to="content-blocks/images", blank=True, storage=image_storage
    )
    file = models.FileField(
        upload_to="content-blocks/files", blank=True, storage=file_storage
    )
    choice = models.CharField(max_length=256, blank=True)
    video = VideoField(
        upload_to="content-blocks/videos", blank=True, storage=video_storage
    )
    embedded_video = models.CharField(max_length=256, blank=True)

    model_choice_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, blank=True, null=True
    )
    model_choice_object_id = models.PositiveIntegerField(blank=True, null=True)
    model_choice = GenericForeignKey(
        "model_choice_content_type", "model_choice_object_id"
    )

    template_name = "content_blocks/partials/fields/default.html"
    preview_template_name = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # todo remove this try
        try:
            for _class in ContentBlockField.__subclasses__():
                if self.field_type == _class.__name__:
                    self.__class__ = _class
                    break
        except:  # pragma: no cover # noqa
            logger.error("Polymorphism failed")  # pragma: no cover

    class Meta:
        ordering = ["template_field__position"]

    @property
    def form_field(self):
        """
        To be overridden. Will return a form.Field class if the field is to be shown on the form.
        This method should return _form_field() with the desired forms.Field.
        """
        raise NotImplementedError  # pragma: no cover

    def _form_field(self, field):
        """
        Adds content_block_field attribute to field
        :return:
        """
        # todo can this be replace with a decorator?
        field.cb_field = self
        return field

    @property
    def context_value(self):
        raise NotImplementedError  # pragma: no cover

    def save_value(self, value):
        raise NotImplementedError  # pragma: no cover

    @property
    def key(self):
        return self.template_field.key


class TextField(ContentBlockField):
    class Meta:
        proxy = True

    @property
    def context_value(self):
        if settings.CONTENT_BLOCKS_MARK_SAFE:
            return mark_safe(self.text)
        return self.text

    def save_value(self, value):
        self.text = value
        self.save()
        return value

    @property
    def form_field(self):
        widget = (
            forms.Textarea
            if settings.CONTENT_BLOCKS_TEXTFIELD_TEXTAREA
            else forms.TextInput
        )
        # noinspection PyTypeChecker
        return self._form_field(
            forms.CharField(
                initial=self.text,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
                widget=widget,
            )
        )


class ContentField(ContentBlockField):
    class Meta:
        proxy = True

    @property
    def context_value(self):
        if settings.CONTENT_BLOCKS_MARK_SAFE:
            return mark_safe(self.content)
        return self.content

    def save_value(self, value):
        self.content = value
        self.save()
        return value

    @property
    def form_field(self):
        # noinspection PyTypeChecker
        return self._form_field(
            forms.CharField(
                initial=self.content,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
                widget=forms.Textarea(),
            )
        )


class CheckboxField(ContentBlockField):
    template_name = "content_blocks/partials/fields/checkbox.html"

    class Meta:
        proxy = True

    @property
    def context_value(self):
        return self.checkbox

    def save_value(self, value):
        self.checkbox = value
        self.save()
        return value

    @property
    def form_field(self):
        # noinspection PyTypeChecker
        return self._form_field(
            forms.BooleanField(
                initial=self.checkbox,
                required=False,
                help_text=self.template_field.help_text,
            )
        )


@cleanup_ignore
class ImageField(ContentBlockField):
    preview_template_name = "content_blocks/partials/fields/previews/image.html"

    class Meta:
        proxy = True

    @property
    def context_value(self):
        return self.image

    def save_value(self, value):
        self.image = None if value is False else value
        self.save()
        return value

    @property
    def form_field(self):
        # noinspection PyTypeChecker
        return self._form_field(
            SVGAndImageFieldFormField(
                initial=self.image,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
                widget=FileWidget(),
            )
        )


@cleanup_ignore
class FileField(ContentBlockField):
    class Meta:
        proxy = True

    @property
    def context_value(self):
        return self.file

    def save_value(self, value):
        self.file = None if value is False else value
        self.save()
        return value

    @property
    def form_field(self):
        # noinspection PyTypeChecker
        return self._form_field(
            forms.FileField(
                initial=self.file,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
                widget=FileWidget(),
            )
        )


@cleanup_ignore
class VideoField(ContentBlockField):
    preview_template_name = "content_blocks/partials/fields/previews/video.html"

    class Meta:
        proxy = True

    @property
    def context_value(self):
        return self.video

    def save_value(self, value):
        self.video = None if value is False else value
        self.save()
        return value

    @property
    def form_field(self):
        # noinspection PyTypeChecker
        return self._form_field(
            forms.FileField(
                initial=self.video,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
                widget=FileWidget(),
            )
        )


class EmbeddedVideoField(ContentBlockField):
    preview_template_name = (
        "content_blocks/partials/fields/previews/embedded_video.html"
    )

    class Meta:
        proxy = True

    @property
    def context_value(self):
        return self.embedded_video

    def save_value(self, value):
        self.embedded_video = value
        self.save()
        return value

    @property
    def form_field(self):
        # noinspection PyTypeChecker
        return self._form_field(
            forms.CharField(
                initial=self.embedded_video,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
            )
        )


class ChoiceField(ContentBlockField):
    class Meta:
        proxy = True

    @property
    def context_value(self):
        return self.choice

    def save_value(self, value):
        self.choice = value
        self.save()
        return value

    @property
    def form_field(self):
        choices = [[None, "-" * 9]] + json.loads(self.template_field.choices)
        # noinspection PyTypeChecker
        return self._form_field(
            forms.CharField(
                initial=self.choice,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
                widget=forms.Select(choices=choices),
            )
        )


class ModelChoiceField(ContentBlockField):
    class Meta:
        proxy = True

    @property
    def form_field(self):
        # self.model_choice_content_type must be set or this will raise an error.
        model = self.model_choice_content_type.model_class()
        queryset = model.objects.all()
        # noinspection PyTypeChecker
        return self._form_field(
            forms.ModelChoiceField(
                queryset,
                initial=self.model_choice,
                required=self.template_field.required,
                help_text=self.template_field.help_text,
            )
        )

    @property
    def context_value(self):
        return self.model_choice

    def save_value(self, value):
        # If value is None, and we set self.model_choice = None it clears model_choice_content_type - not ideal
        # So instead we ste the model_choice_object_id
        self.model_choice_object_id = value.id if value is not None else None
        self.save()
        return value


class NestedField(ContentBlockField):
    class Meta:
        proxy = True

    @property
    def form_field(self):
        return None

    def save_value(self, value):
        return None

    @property
    def context_value(self):
        """
        :return: Nested content blocks which we can then call render or access context on.
        """
        return self.content_blocks.visible()


class ContentBlockManager(VisibleManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("content_block_fields")
            .select_related("content_block_template")
        )

    def visible(self):
        """
        Visible published only.
        Used in templates to render published content blocks.
        :return:
        """
        return super().visible().filter(draft=False)

    def previews(self):
        """
        Visible drafts only. Exclude those which haven't been saved via the editor yet (empties).
        Can be used in page previews.
        :return:
        """
        return super().visible().filter(draft=True, saved=True)

    def published(self):
        """
        All published including visible=False.
        Used by the publishing/reset mechanism.
        :return:
        """
        return self.get_queryset().filter(draft=False)

    def drafts(self):
        """
        All drafts including visible=False.
        Used by the editor and publishing/reset mechanism.
        :return:
        """
        return self.get_queryset().filter(draft=True)


class ContentBlock(
    PositionModel, AutoDateModel, VisibleModel, CloneMixin, CachedHtmlModel
):
    """
    Content Block Model
    Content block fields point here.  Those created are based on the content block template.
    """

    objects = ContentBlockManager()

    content_block_template = models.ForeignKey(
        "content_blocks.ContentBlockTemplate", on_delete=models.CASCADE
    )
    parent = models.ForeignKey(
        ContentBlockField,
        on_delete=models.CASCADE,
        related_name="content_blocks",
        blank=True,
        null=True,
    )

    # todo max_length=64
    css_class = models.CharField(max_length=256, blank=True)

    draft = models.BooleanField(blank=True, default=False)

    saved = models.BooleanField(blank=True, default=False)

    context_name = "content_block"
    cache_prefix = "content_block"

    @cached_property
    def template(self):
        """
        HTML template
        """
        return self.content_block_template.template or None

    @cached_property
    def fields(self):
        """
        Create/cache a dict of key to content block field objects.
        """
        nested_fields = {}
        fields = {}
        for field in self.content_block_fields.all():
            fields[field.template_field.key] = field
            if field.template_field.field_type == ContentBlockFields.NESTED_FIELD:
                nested_fields[field.template_field.key] = field

        self.__dict__["nested_fields"] = nested_fields
        return fields

    @cached_property
    def nested_fields(self):
        """
        Create/cache a dict of nested fields.  If self.fields has already been called this is already cached.
        """
        return {
            field.template_field.key: field
            for field in self.content_block_fields.filter(
                template_field__field_type=ContentBlockFields.NESTED_FIELD
            )
        }

    @cached_property
    def context(self):
        """
        Return dictionary of template context for this content block
        """
        context = {key: field.context_value for key, field in self.fields.items()}
        context["css_class"] = self.css_class
        return context

    def render(self, request=None):
        """
        Render html for this block and cache
        """
        if not self.can_render:
            return ""

        cache_enabled = (
            not self.content_block_template.no_cache
            and not settings.CONTENT_BLOCKS_DISABLE_CACHE
        )

        html = None
        if cache_enabled:
            html = cache.get(self.cache_key)

        if html is None:
            html = render_to_string(
                self.template,
                {self.context_name: self.context, "request": request},
                request=request,
            )

            if cache_enabled:
                cache.set(self.cache_key, html)

        return html

    def clear_cache(self):
        """
        Clear the cache for this block and any parent blocks
        """
        super().clear_cache()
        if self.parent:
            self.parent.content_block.clear_cache()

    def update_cache(self):
        if "context" in self.__dict__.keys():
            # Clear the context cached property if present
            del self.__dict__["context"]

        super().update_cache()
        if self.parent:
            self.parent.content_block.update_cache()

    def clone(self, attrs=None):
        """
        Clones the given content block and all content block fields.
        """
        new_content_block = self.make_clone(attrs=attrs)

        for field in self.content_block_fields.all():
            new_field = field.make_clone(attrs={"content_block": new_content_block})

            if field.template_field.field_type == ContentBlockFields.NESTED_FIELD:
                for nested_block in field.content_blocks.all():
                    nested_block.clone(attrs={"parent": new_field})

        return new_content_block


class ContentBlockTemplate(PositionModel, AutoDateModel, VisibleModel):
    """
    Content Block Template model.
    Used to define content block types.
    """

    objects = VisibleManager()

    name = models.CharField(max_length=256, unique=True)

    template_filename = models.CharField(max_length=256, blank=True)

    no_cache = models.BooleanField(
        default=False,
        help_text="Disable caching for content blocks created with this template.",
    )

    def __str__(self):
        return self.name

    @property
    def template(self):
        if self.template_filename:
            return f"content_blocks/content_blocks/{self.template_filename}"


class ContentBlockTemplateField(PositionModel):
    """
    Content Block Template Field model.
    Used to define content block types.
    """

    content_block_template = models.ForeignKey(
        ContentBlockTemplate,
        on_delete=models.CASCADE,
        related_name="content_block_template_fields",
    )

    # todo max_length=32
    field_type = models.CharField(max_length=256, choices=ContentBlockFields.CHOICES)

    # todo max_length=64
    key = models.SlugField(
        max_length=256,
        validators=[
            RegexValidator(
                "[a-z0-9_]+", "Lowercase letters, numbers and underscores only."
            )
        ],
        help_text="Must be unique to this content block template. Lowercase letters, numbers and underscores only.",
    )

    help_text = models.TextField(blank=True)
    required = models.BooleanField(blank=True, default=False)

    # todo max_length=64
    css_class = models.CharField(
        max_length=256,
        blank=True,
        help_text="Set a custom CSS class for this field in the editor.",
    )

    # Only used if field_type == NestedField
    nested_templates = models.ManyToManyField(
        "content_blocks.ContentBlockTemplate",
        blank=True,
        help_text="Choose the content block templates that can be used in this nested field.",
    )
    min_num = models.PositiveIntegerField(
        default=0, help_text="The minimum number of nested blocks allowed."
    )
    max_num = models.PositiveIntegerField(
        default=99, help_text="The maximum number of nested blocks allowed."
    )

    # Only used if field_type == ChoiceField
    choices = models.TextField(blank=True)

    # Only used if field_type == ModelChoiceField
    model_choice_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, blank=True, null=True
    )

    class Meta(PositionModel.Meta):
        unique_together = ("key", "content_block_template")

    def __str__(self):
        return self.key or super().__str__()


class ContentBlockAvailability(AutoDateModel):
    """
    Used to set which content block templates can be added to a model.
    """

    # null=True is required for admin list to work. blank=False because this is a required field.
    content_type = models.OneToOneField(
        ContentType, on_delete=models.CASCADE, null=True
    )

    content_block_templates = models.ManyToManyField(ContentBlockTemplate)

    class Meta:
        verbose_name_plural = "Content block availabilities"

    def __str__(self):
        return str(self.content_type)


class ContentBlockParentModel(models.Model):
    """
    Model to be inherited by parent objects which then have content blocks assigned.  E.g. imperium.Page
    """

    content_blocks = models.ManyToManyField(ContentBlock)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.content_blocks.all().delete()
        return super().delete(using=using, keep_parents=keep_parents)


class ContentBlockCollection(AutoDateModel, ContentBlockParentModel):
    """
    Simple collections of content blocks identified by slug.
    Use the content_blocks_collection template tag to render a content block collection in a template.
    """

    name = models.CharField(
        max_length=256, blank=True, help_text="For identification purposes only."
    )

    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name or self.slug
