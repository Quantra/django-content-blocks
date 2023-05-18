"""
Content Blocks views.py
"""
from functools import wraps
from io import StringIO

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from content_blocks.admin_forms import ContentBlockTemplateImportForm
from content_blocks.conf import settings
from content_blocks.forms import (
    ContentBlockForm,
    ImportContentBlocksForm,
    NewContentBlockForm,
    NewNestedBlockForm,
    PublishContentBlocksForm,
    ResetContentBlocksForm,
)
from content_blocks.models import ContentBlock
from content_blocks.services.content_block_template import ImportExportServices


def require_ajax(view):
    @wraps(view)
    def _wrapped_view(request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return view(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return _wrapped_view


def create_log_entry(request, obj, action_flag, change_message, **kwargs):
    params = {
        "user_id": request.user.id,
        "object_repr": obj.__str__(),
        "action_flag": action_flag,
        "change_message": change_message,
        "content_type_id": None,
        "object_id": None,
    }

    if obj:
        params.update(
            {
                "content_type_id": ContentType.objects.get_for_model(obj.__class__).id,
                "object_id": obj.id,
            }
        )

    params.update(kwargs)

    LogEntry.objects.log_action(**params)


# Content block editor views


@staff_member_required
@ensure_csrf_cookie
def content_block_editor(request, object_id, model_admin=None):
    """
    Show the content block editor.
    """
    parent = get_object_or_404(model_admin.model, id=object_id)

    app_label, model_name = parent._meta.app_label, parent._meta.model_name

    return_url = reverse(f"admin:{app_label}_{model_name}_change", args=[parent.id])

    new_content_block_form = NewContentBlockForm(parent=parent)
    publish_form = PublishContentBlocksForm(
        initial={
            "return_url": return_url,
        },
        parent=parent,
    )
    discard_changes_form = ResetContentBlocksForm(
        initial={
            "return_url": return_url,
        },
        parent=parent,
    )
    import_content_blocks_form = ImportContentBlocksForm(parent=parent)

    status_message = settings.CONTENT_BLOCKS_DEFAULT_STATUS_MESSAGE
    if callable(status_message):
        status_message = status_message()

    context = {
        "import_content_blocks_form": import_content_blocks_form,
        "new_content_block_form": new_content_block_form,
        "parent": parent,
        "publish_form": publish_form,
        "discard_form": discard_changes_form,
        "return_url": return_url,
        "opts": parent._meta,
        "status_message": status_message,
    }
    context.update(**model_admin.admin_site.each_context(request))

    return render(request, "content_blocks/editor/editor.html", context)


def content_block_create_base(request, form, parent, log_name="content block"):
    """
    Ajax view for creating new top level and nested content blocks depending on the form passed.
    Returns html form for the new content block.
    """
    # This should never happen
    if not form.is_valid():
        return JsonResponse({"error": f"Invalid {form.__class__}"})  # pragma: no cover

    content_block = form.save()

    create_log_entry(
        request,
        content_block,
        ADDITION,
        [{"added": {"name": log_name, "object": content_block.__str__()}}],
    )

    content_block_form_html = render_to_string(
        "content_blocks/editor/content_block_form_wrapper.html",
        {
            "form": ContentBlockForm(content_block=content_block),
            "content_block": content_block,
            "opts": parent._meta,
            "parent": parent,
        },
    )

    return JsonResponse({"html": content_block_form_html})


@staff_member_required
@require_POST
@require_ajax
def content_block_create(request, object_id, model_admin=None):
    parent = get_object_or_404(model_admin.model, id=object_id)
    return content_block_create_base(
        request,
        NewContentBlockForm(request.POST, parent=parent),
        parent,
    )


@staff_member_required
@require_POST
@require_ajax
def nested_block_create(request, object_id, model_admin=None):
    parent = get_object_or_404(model_admin.model, id=object_id)
    return content_block_create_base(
        request,
        NewNestedBlockForm(request.POST),
        parent,
        log_name="nested block",
    )


@staff_member_required
@require_POST
@require_ajax
def content_block_save(request, content_block_id):
    """
    Save the content block.  Return form html.
    """
    content_block = get_object_or_404(ContentBlock, id=content_block_id)

    form = ContentBlockForm(request.POST, request.FILES, content_block=content_block)

    form_is_valid = form.is_valid()

    if form_is_valid:
        form.save()

        create_log_entry(
            request, content_block, CHANGE, [{"changed": {"fields": form.changed_data}}]
        )

        # Refetch content block from db due to model choice fields not being rendered with correct context when
        # saving a field with previous value of None. In this case the field was being rendered with the value None
        # instead of the newly saved value.  Curiously this behaviour only exists when the previous value is None.
        content_block = ContentBlock.objects.get(id=content_block_id)

    content_block_form_html = render_to_string(
        "content_blocks/editor/content_block_form.html",
        {
            "form": ContentBlockForm(content_block=content_block)
            if form_is_valid
            else form,
            "content_block": content_block,
            "saved": form_is_valid,
        },
    )

    return JsonResponse({"html": content_block_form_html, "saved": form_is_valid})


@staff_member_required
@require_POST
@require_ajax
def update_position(request):
    """
    Update position after a content block has been dragon dropped.
    """
    # todo refactor to service class
    positions = request.POST.get("positions", "")
    positions = f"&{positions}".split("&cb[]=")[1:]
    for i, id in enumerate(positions):
        ContentBlock.objects.filter(id=id).update(position=i)
    # Admin log entry?  Might be a bit spammy. Unless we pass the cb which was dragged and just log on that one?
    return JsonResponse({})


@staff_member_required
@require_POST
@require_ajax
def toggle_visible(request, content_block_id):
    """
    Toggle visible buttons
    """
    # todo refactor to service class
    content_block = ContentBlock.objects.get(id=content_block_id)
    content_block.visible = not content_block.visible
    content_block.save()

    create_log_entry(
        request,
        content_block,
        action_flag=CHANGE,
        change_message=[{"changed": {"fields": ["visible"]}}],
    )

    return JsonResponse({"visible": content_block.visible})


def ajax_form(
    request,
    object_id,
    form_klass,
    content_blocks_html=False,
    model_admin=None,
):
    """
    Used by import, reset and publish to process a form and optionally return the parent's content blocks html.
    :param model_admin:
    :param object_id:
    :param content_blocks_html:
    :param form_klass:
    :param request:
    :return:
    """
    parent = get_object_or_404(model_admin.model, id=object_id)
    form = form_klass(request.POST, parent=parent)

    # This should never happen
    if not form.is_valid():
        return JsonResponse(
            {"error": f"Invalid {form_klass.__class__}"}
        )  # pragma: no cover

    form.save()

    data = {}
    if content_blocks_html:
        data["html"] = render_to_string(
            "content_blocks/editor/content_block_forms.html",
            {"parent": form.parent, "opts": parent._meta},
        )

    log_entry_name = {
        PublishContentBlocksForm: "published",
        ResetContentBlocksForm: "reset",
        ImportContentBlocksForm: "imported",
    }

    create_log_entry(
        request, parent, CHANGE, f"Content blocks {log_entry_name[form_klass]}"
    )

    return JsonResponse(data)


@staff_member_required
@require_POST
@require_ajax
def publish_content_blocks(request, object_id, model_admin=None):
    return ajax_form(
        request, object_id, PublishContentBlocksForm, model_admin=model_admin
    )


@staff_member_required
@require_POST
@require_ajax
def discard_changes(request, object_id, model_admin=None):
    return ajax_form(
        request,
        object_id,
        ResetContentBlocksForm,
        content_blocks_html=True,
        model_admin=model_admin,
    )


@staff_member_required
@require_POST
@require_ajax
def import_content_blocks(request, object_id, model_admin=None):
    return ajax_form(
        request,
        object_id,
        ImportContentBlocksForm,
        content_blocks_html=True,
        model_admin=model_admin,
    )


@staff_member_required
def content_block_preview(request, object_id, content_block_id, model_admin=None):
    """
    Render a content block in a preview base template and return html.
    Normally shown in an iframe.
    """
    parent = get_object_or_404(model_admin.model, id=object_id)
    content_block = get_object_or_404(ContentBlock, id=content_block_id)

    response = render(
        request,
        "content_blocks/content_block_preview.html",
        {"content_block": content_block, "parent": parent},
    )
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    return response


@staff_member_required
@require_POST
@require_ajax
def content_block_delete(request, content_block_id):
    """
    Delete a content block.
    """
    # todo refactor to service class
    content_block = ContentBlock.objects.get(id=content_block_id)

    create_log_entry(request, content_block, DELETION, "")

    content_block.delete()
    return JsonResponse({})


# ContentBlockTemplate import export views


@staff_member_required
def content_block_template_export(request):
    """
    Export content block template view used in admin site.
    Uses the export_content_block_templates management command and streams the result directly to a file download.
    """
    buffer = StringIO()
    ImportExportServices.export_content_block_templates(file_like=buffer)
    buffer.seek(0)

    return StreamingHttpResponse(
        buffer,
        content_type="application/json",
        headers={
            "Content-Disposition": 'attachment; filename="content_block_templates.json"'
        },
    )


@staff_member_required
def content_block_template_import(request, model_admin=None):
    """
    Form for importing ContentBlockTemplate from json created by export_content_block_templates management command.
    """
    post_data = None
    files_data = None

    if request.method == "POST":
        post_data = request.POST
        files_data = request.FILES

    form = ContentBlockTemplateImportForm(post_data, files_data)

    if form.is_valid():
        fixture_file = files_data["fixture_file"]
        form.import_content_block_templates(fixture_file)
        messages.success(request, "Content block templates imported.")
        create_log_entry(
            request,
            None,
            CHANGE,
            f"Content block templates imported from {fixture_file.name}",
        )
        return redirect("admin:content_blocks_contentblocktemplate_changelist")

    context = {
        "form": form,
        "opts": model_admin.model._meta,
    }

    context.update(**model_admin.admin_site.each_context(request))

    return render(
        request,
        "content_blocks/admin/content_block_template_import_form.html",
        context,
    )
