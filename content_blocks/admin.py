"""
Content blocks admin.py
"""
from io import StringIO

from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin
from django.conf import settings
from django.contrib import admin, messages
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import path, reverse
from django.utils.safestring import mark_safe

from content_blocks.admin_forms import (
    ContentBlockTemplateAdminForm,
    ContentBlockTemplateFieldAdminForm,
)
from content_blocks.models import (
    ContentBlockAvailability,
    ContentBlockCollection,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)
from content_blocks.services.content_block_template import ImportExportServices
from content_blocks.views import (
    content_block_create,
    content_block_editor,
    content_block_preview,
    content_block_template_export,
    content_block_template_import,
    discard_changes,
    import_content_blocks,
    nested_block_create,
    publish_content_blocks,
)

#  Admin constants and base classes

# Auto dates
AUTO_DATE_FIELDS = ["create_date", "mod_date"]
AUTO_DATE_FIELDSET = (
    "Dates",
    {"fields": (("create_date", "mod_date"),)},
)

# Visible
VISIBLE_FIELDS = ["visible"]
VISIBLE_FIELDSET = ("Visibility", {"fields": VISIBLE_FIELDS})


class ContentBlockTemplateFieldInline(SortableInlineAdminMixin, admin.StackedInline):
    model = ContentBlockTemplateField
    fk_name = "content_block_template"
    form = ContentBlockTemplateFieldAdminForm
    min_num = 0
    extra = 0
    autocomplete_fields = ["nested_templates"]


@admin.register(ContentBlockTemplate)
class ContentBlockTemplateAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = ContentBlockTemplateAdminForm

    change_list_template = (
        "content_blocks/admin/content_block_template_change_list.html"
    )
    list_display = [
        "name",
        "template_filename",
        "visible",
    ] + AUTO_DATE_FIELDS
    list_editable = ("visible",)
    list_filter = AUTO_DATE_FIELDS + ["visible"]
    search_fields = ("name", "template_filename")

    readonly_fields = AUTO_DATE_FIELDS
    inlines = [ContentBlockTemplateFieldInline]
    actions = ["export_content_block_templates"]

    class Media:
        css = {"all": ["content_blocks/css/content_block_template_admin.css"]}
        js = (
            "content_blocks/js/content_block_template_admin.js",
            "content_blocks/js/admin_choices_widget.js",
        )

    @property
    def content_block_template_fields(self):
        return ["name", "template_filename", "no_cache"]

    def get_fieldsets(self, request, obj=None):
        return (
            AUTO_DATE_FIELDSET,
            VISIBLE_FIELDSET,
            (
                "Content Block Template",
                {
                    "fields": self.content_block_template_fields,
                },
            ),
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        template_filename = form.cleaned_data.get("template_filename")

        if not template_filename:
            return

        template_filename = f"content_blocks/content_blocks/{template_filename}"

        try:
            get_template(template_filename)
        except TemplateDoesNotExist:
            url = reverse(
                "admin:content_blocks_contentblocktemplate_change", args=[obj.id]
            )
            msg = (
                f"Couldn't load a template for the content block template "
                f'"<a href="{url}">{obj}</a>". '
                f'No template found at "{template_filename}".'
            )
            messages.warning(request, mark_safe(msg))

    def get_urls(self):
        urls = [
            path(
                "export/",
                content_block_template_export,
                name="content_blocks_contentblocktemplate_export",
            ),
            path(
                "import/",
                content_block_template_import,
                {"model_admin": self},
                name="content_blocks_contentblocktemplate_import",
            ),
        ]
        return urls + super().get_urls()

    @admin.action(description="Export selected content block templates")
    def export_content_block_templates(self, request, queryset):
        """
        Export the selected ContentBlockTemplate objects as JSON suitable for import.
        """
        buffer = StringIO()
        ImportExportServices.export_content_block_templates(queryset, buffer)
        buffer.seek(0)

        return StreamingHttpResponse(
            buffer,
            content_type="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="content_block_templates.json"'
            },
        )


if "dbtemplates" in settings.INSTALLED_APPS:
    from dbtemplates.models import Template

    admin.site.unregister(ContentBlockTemplate)

    @admin.register(ContentBlockTemplate)
    class ContentBlockTemplateDBTemplatesAdmin(ContentBlockTemplateAdmin):
        @property
        def content_block_template_fields(self):
            return super().content_block_template_fields + ["db_template_button"]

        @admin.display(description="HTML Template")
        def db_template_button(self, obj):
            if not obj.template_filename:
                return "-"
            button = '<input type="submit" value="Save and edit HTML template" name="_dbtemplate">'
            return mark_safe(button)

        def get_readonly_fields(self, request, obj=None):
            return [
                *super().get_readonly_fields(request, obj=obj),
                "db_template_button",
            ]

        def _response(self, response, request, obj):
            if "_dbtemplate" in request.POST and obj.template:
                db_template, _ = Template.objects.get_or_create(name=obj.template)
                url = reverse(
                    "admin:dbtemplates_template_change", args=[db_template.id]
                )
                return HttpResponseRedirect(url)

            return response

        def response_change(self, request, obj):
            response = super().response_change(request, obj)
            return self._response(response, request, obj)

        def response_add(self, request, obj, post_url_continue=None):
            response = super().response_add(
                request, obj, post_url_continue=post_url_continue
            )
            return self._response(response, request, obj)


@admin.register(ContentBlockAvailability)
class ContentBlockAvailabilityAdmin(admin.ModelAdmin):
    list_display = ["content_type"] + AUTO_DATE_FIELDS
    list_filter = AUTO_DATE_FIELDS

    readonly_fields = AUTO_DATE_FIELDS
    filter_horizontal = ["content_block_templates"]

    fieldsets = (
        AUTO_DATE_FIELDSET,
        (
            "Content Block Availability",
            {"fields": ("content_type", "content_block_templates")},
        ),
    )


class ContentBlockModelAdmin(admin.ModelAdmin):
    """
    Base class to be added to the admin of any model which has a content_blocks m2m.  This will then add
    content_blocks_button which can then be added to the formset.
    """

    @admin.display(description="Content blocks")
    def content_blocks_link(self, obj):
        """
        A link to the content block editor for this object.
        Intended to be used on admin changelist.
        :param obj: subclass of :py:class:`ContentBlockParentModel`.
        """
        app_label, model_name = self.model._meta.app_label, self.model._meta.model_name
        url = reverse(
            f"admin:{app_label}_{model_name}_content_block_editor", args=[obj.id]
        )
        link = f'<a href="{url}">Edit content blocks</a>'
        return mark_safe(link)

    def content_blocks_button(self, *args):
        """
        A button which will save the object then, if successful, will redirect to the content block editor for this
        object.
        Intended to be used on the admin changepage.
        """
        button = '<input type="submit" value="Save and edit content blocks" name="_contentblocks">'
        return mark_safe(button)

    content_blocks_button.short_description = "Content blocks"

    def get_readonly_fields(self, *args, **kwargs):
        return (
            *super().get_readonly_fields(*args, **kwargs),
            "content_blocks_link",
            "content_blocks_button",
        )

    def _response(self, response, request, obj):
        if "_contentblocks" in request.POST:
            model_name = self.model._meta.model_name
            app_label = self.model._meta.app_label
            url = reverse(
                f"admin:{app_label}_{model_name}_content_block_editor", args=[obj.id]
            )
            return HttpResponseRedirect(url)

        return response

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        return self._response(response, request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        response = super().response_add(
            request, obj, post_url_continue=post_url_continue
        )
        return self._response(response, request, obj)

    def get_urls(self):
        app_label, model_name = self.model._meta.app_label, self.model._meta.model_name
        urls = [
            path(
                "<path:object_id>/content-blocks/",
                content_block_editor,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_content_block_editor",
            ),
            path(
                "<path:object_id>/content-blocks/_ajax/content-block-create/",
                content_block_create,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_content_block_create",
            ),
            path(
                "<path:object_id>/content-blocks/_ajax/nested-block-create/",
                nested_block_create,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_nested_block_create",
            ),
            path(
                "<path:object_id>/content-blocks/_ajax/publish/",
                publish_content_blocks,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_publish_content_blocks",
            ),
            path(
                "<path:object_id>/content-blocks/_ajax/discard-changes/",
                discard_changes,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_discard_changes",
            ),
            path(
                "<path:object_id>/content-blocks/_ajax/import-content-blocks/",
                import_content_blocks,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_import_content_blocks",
            ),
            path(
                "<path:object_id>/content-blocks/<int:content_block_id>/preview/",
                content_block_preview,
                {"model_admin": self},
                name=f"{app_label}_{model_name}_content_block_preview",
            ),
        ]
        return urls + super().get_urls()


@admin.register(ContentBlockCollection)
class ContentBlockCollectionAdmin(ContentBlockModelAdmin):
    list_display = ["name", "slug", "content_blocks_link"] + AUTO_DATE_FIELDS
    list_display_links = ["name", "slug"]
    list_filter = AUTO_DATE_FIELDS
    search_fields = ["name", "slug"]

    readonly_fields = AUTO_DATE_FIELDS
    prepopulated_fields = {"slug": ("name",)}

    fieldsets = (
        AUTO_DATE_FIELDSET,
        (
            "Content Block Collection",
            {"fields": ("name", "slug", "content_blocks_button")},
        ),
    )
