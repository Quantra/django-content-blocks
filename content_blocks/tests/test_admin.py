import pytest
from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from faker import Faker
from tests.test_management_commands import _test_imported_json

from content_blocks.models import (
    ContentBlockCollection,
    ContentBlockFields,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)

faker = Faker()


class TestContentBlockTemplateAdmin:
    @pytest.fixture
    def base_admin_url(self):
        return "admin:content_blocks_contentblocktemplate"

    @pytest.fixture
    def content_block_template_form_data(self):
        inline_form_prefix = "content_block_template_fields"
        return {
            "name": faker.text(256),
            "_save": "Save",
            f"{inline_form_prefix}-TOTAL_FORMS": 1,
            f"{inline_form_prefix}-INITIAL_FORMS": 0,
            f"{inline_form_prefix}-MIN_NUM_FORMS": 0,
            f"{inline_form_prefix}-MAX_NUM_FORMS": 1000,
            f"{inline_form_prefix}-0-field_type": ContentBlockFields.TEXT_FIELD,
            f"{inline_form_prefix}-0-key": faker.slug(256).replace("-", "_"),
            f"{inline_form_prefix}-0-position": 0,
            f"{inline_form_prefix}-0-min_num": 0,
            f"{inline_form_prefix}-0-max_num": 99,
        }

    def test_content_block_template_admin_changelist(
        self, admin_client, base_admin_url, content_block_template_factory
    ):
        content_block_template_factory.create_batch(10)
        response = admin_client.get(reverse(f"{base_admin_url}_changelist"))
        assert response.status_code == 200

    def test_content_block_template_admin_add_get(self, admin_client, base_admin_url):
        response = admin_client.get(reverse(f"{base_admin_url}_add"))
        assert response.status_code == 200

    def test_content_block_template_admin_add_post(
        self, admin_client, base_admin_url, content_block_template_form_data
    ):
        """
        Test submitting the admin add form with an inline.
        """
        response = admin_client.post(
            reverse(f"{base_admin_url}_add"), content_block_template_form_data
        )
        assert response.status_code == 302
        assert ContentBlockTemplate.objects.count() == 1
        assert ContentBlockTemplateField.objects.count() == 1

    def test_content_block_template_admin_change_get(
        self, admin_client, content_block_template_field, base_admin_url
    ):
        response = admin_client.get(
            reverse(
                f"{base_admin_url}_change",
                args=[content_block_template_field.content_block_template.id],
            )
        )
        assert response.status_code == 200

    def test_content_block_template_admin_change_post(
        self,
        admin_client,
        base_admin_url,
        content_block_template_field,
        content_block_template_form_data,
    ):
        response = admin_client.post(
            reverse(
                f"{base_admin_url}_change",
                args=[content_block_template_field.content_block_template.id],
            ),
            content_block_template_form_data,
        )

        assert response.status_code == 302

    @pytest.fixture
    def content_block_template_model_admin(self):
        return admin.site._registry.get(ContentBlockTemplate)

    @pytest.mark.django_db
    def test_content_block_template_admin_db_template_button(
        self, content_block_template_model_admin, content_block_template, settings
    ):
        """
        Should return '-' if no template_filename or an html button marked safe.
        """
        if not apps.is_installed("dbtemplates"):
            pytest.skip("skipping dbtemplates only tests")

        assert (
            content_block_template_model_admin.db_template_button(
                content_block_template
            )
            == "-"
        )
        content_block_template.template_filename = faker.file_name(extension=".html")
        assert content_block_template_model_admin.db_template_button(
            content_block_template
        ).startswith("<input")

    def test_content_block_template_admin_db_template_button_submit(
        self,
        admin_client,
        base_admin_url,
        content_block_template,
        content_block_template_form_data,
        site,
        text_template,
    ):
        """
        Should redirect when _dbtemplate is in POST.
        """
        content_block_template_form_data.pop("_save")
        content_block_template_form_data["_dbtemplate"] = "Dbtemplate"
        content_block_template_form_data["template_filename"] = text_template.name
        response = admin_client.post(
            reverse(f"{base_admin_url}_change", args=[content_block_template.id]),
            content_block_template_form_data,
        )
        assert response.status_code == 302

    def test_content_block_template_admin_model_save(
        self, admin_client, base_admin_url, content_block_template_form_data
    ):
        """
        Test submitting the admin add form warning when the template can't be loaded.
        """
        content_block_template_form_data["template_filename"] = faker.file_name(
            extension="html"
        )
        response = admin_client.post(
            reverse(f"{base_admin_url}_add"), content_block_template_form_data
        )

        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 2

        warning_message = messages[0]

        assert warning_message.level_tag == "warning"

        assert "No template found" in warning_message.message

    @pytest.mark.django_db
    def test_content_block_template_export(
        self, admin_client, cbt_import_export_objects, base_admin_url
    ):
        response = admin_client.get(reverse(f"{base_admin_url}_export"))

        assert response.status_code == 200

        assert response.has_header("Content-Disposition")
        assert "attachment" in response.headers["Content-Disposition"]

        assert response.has_header("Content-Type")
        assert response.headers["Content-Type"] == "application/json"

        json_string = response.getvalue()
        _test_imported_json(json_string)

    @pytest.mark.django_db
    def test_content_block_template_import_get(self, admin_client, base_admin_url):
        response = admin_client.get(reverse(f"{base_admin_url}_import"))

        assert response.status_code == 200

    @pytest.mark.django_db
    def test_content_block_template_import_post(
        self, admin_client, cbt_import_export_json_file, base_admin_url
    ):
        content_block_template_query = ContentBlockTemplate.objects.all()
        content_block_template_field_query = ContentBlockTemplateField.objects.all()

        assert content_block_template_query.count() == 1
        assert content_block_template_field_query.count() == 1

        content_block_template_query.delete()

        assert content_block_template_query.count() == 0
        assert content_block_template_field_query.count() == 0

        uploaded_json_file = SimpleUploadedFile(
            cbt_import_export_json_file.name,
            cbt_import_export_json_file.read_bytes(),
            "application/json",
        )
        post_data = {"fixture_file": uploaded_json_file}

        response = admin_client.post(reverse(f"{base_admin_url}_import"), post_data)

        assert response.status_code == 302

        assert content_block_template_query.count() == 1
        assert content_block_template_field_query.count() == 1

    @pytest.mark.django_db
    def test_content_block_template_export_action(
        self, content_block_template_model_admin, cbt_import_export_objects
    ):
        response = content_block_template_model_admin.export_content_block_templates(
            None, ContentBlockTemplate.objects.all()
        )

        assert response.status_code == 200

        assert response.has_header("Content-Disposition")
        assert "attachment" in response.headers["Content-Disposition"]

        assert response.has_header("Content-Type")
        assert response.headers["Content-Type"] == "application/json"

        json_string = response.getvalue()
        _test_imported_json(json_string)


class TestContentBlockAvailabilityAdmin:
    @pytest.fixture
    def base_admin_url(self):
        return "admin:content_blocks_contentblockavailability"

    def test_content_block_availablilty_admin_changelist(
        self, admin_client, base_admin_url, content_block_availability
    ):
        response = admin_client.get(reverse(f"{base_admin_url}_changelist"))
        assert response.status_code == 200

    def test_content_block_availability_admin_add_get(
        self, admin_client, base_admin_url
    ):
        response = admin_client.get(reverse(f"{base_admin_url}_add"))
        assert response.status_code == 200

    def test_content_block_availability_admin_add_post(
        self, admin_client, base_admin_url, content_block_template
    ):
        response = admin_client.post(
            reverse(f"{base_admin_url}_add"),
            {
                "content_type": ContentType.objects.get_for_model(
                    ContentBlockCollection
                ).id,
                "content_block_templates": [content_block_template.id],
            },
        )
        assert response.status_code == 302

    def test_content_block_availability_admin_change_get(
        self, admin_client, content_block_availability, base_admin_url
    ):
        response = admin_client.get(
            reverse(
                f"{base_admin_url}_change",
                args=[content_block_availability.id],
            )
        )
        assert response.status_code == 200

    def test_content_block_availability_admin_change_post(
        self,
        admin_client,
        base_admin_url,
        content_block_availability,
        content_block_template_factory,
    ):
        content_block_template_factory.create_batch(2)
        response = admin_client.post(
            reverse(f"{base_admin_url}_change", args=[content_block_availability.id]),
            {
                "content_type": ContentType.objects.get_for_model(
                    ContentBlockCollection
                ).id,
                "content_block_templates": ContentBlockTemplate.objects.all().values_list(
                    "id", flat=True
                ),
            },
        )
        assert response.status_code == 302


class TestContentBlockCollectionAdmin:
    @pytest.fixture
    def base_admin_url(self):
        return "admin:content_blocks_contentblockcollection"

    def test_content_block_collection_admin_changelist(
        self, admin_client, base_admin_url, content_block_collection_factory
    ):
        content_block_collection_factory.create_batch(10)
        response = admin_client.get(reverse(f"{base_admin_url}_changelist"))
        assert response.status_code == 200

    def test_content_block_collection_admin_add_get(self, admin_client, base_admin_url):
        response = admin_client.get(reverse(f"{base_admin_url}_add"))
        assert response.status_code == 200

    def test_content_block_collection_admin_add_post(
        self, admin_client, base_admin_url
    ):
        response = admin_client.post(
            reverse(f"{base_admin_url}_add"), {"slug": faker.slug(256)}
        )
        assert response.status_code == 302
        assert ContentBlockCollection.objects.count() == 1

    def test_content_block_collection_admin_change_get(
        self, admin_client, content_block_collection, base_admin_url
    ):
        response = admin_client.get(
            reverse(
                f"{base_admin_url}_change",
                args=[content_block_collection.id],
            )
        )
        assert response.status_code == 200

    def test_content_block_collection_admin_change_post(
        self, admin_client, content_block_collection, base_admin_url
    ):
        response = admin_client.post(
            reverse(f"{base_admin_url}_change", args=[content_block_collection.id]),
            {"slug": faker.slug(256)},
        )
        assert response.status_code == 302

    def test_content_block_collection_admin_content_blocks_button_submit(
        self, admin_client, base_admin_url, content_block_collection
    ):
        response = admin_client.post(
            reverse(f"{base_admin_url}_change", args=[content_block_collection.id]),
            {"slug": faker.slug(256), "_contentblocks": "Save and edit content blocks"},
        )
        assert response.status_code == 302
