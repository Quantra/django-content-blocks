"""
Content blocks test_views.py
"""
import pytest
from django.urls import reverse
from faker import Faker

from content_blocks.models import ContentBlock

BASE_ADMIN_URL = "admin:content_blocks_contentblockcollection"

faker = Faker()


class TestContentBlockEditor:
    @pytest.mark.django_db
    def test_content_block_editor_get(self, admin_client, content_block_collection):
        response = admin_client.get(
            reverse(
                f"{BASE_ADMIN_URL}_content_block_editor",
                args=[content_block_collection.id],
            )
        )
        assert response.status_code == 200


class TestContentBlockCreate:
    @pytest.mark.django_db
    def test_create_content_block_post(
        self,
        admin_client,
        content_block_collection,
        content_block_template,
    ):
        response = admin_client.post(
            reverse(
                f"{BASE_ADMIN_URL}_content_block_create",
                args=[content_block_collection.id],
            ),
            {"content_block_template": content_block_template.id, "position": 0},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        assert ContentBlock.objects.count() == 1


class TestNestedBlockCreate:
    @pytest.mark.django_db
    def test_create_nested_block_post(
        self, admin_client, nested_content_block, content_block_collection
    ):
        content_block, nested_content_block = nested_content_block
        content_block_collection.content_blocks.add(content_block)

        response = admin_client.post(
            reverse(
                f"{BASE_ADMIN_URL}_nested_block_create",
                args=[content_block_collection.id],
            ),
            {
                "position": 1,
                "parent": content_block,
                "content_block_template": nested_content_block.content_block_template,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200
        assert ContentBlock.objects.count() == 2


class TestContentBlockSave:
    @pytest.mark.django_db
    def test_content_block_save_post(self, admin_client, content_block_field):
        text = content_block_field.text
        response = admin_client.post(
            reverse(
                "content_blocks:content_block_save",
                args=[content_block_field.content_block.id],
            ),
            {"textfield": faker.text(256)},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert response.status_code == 200
        content_block_field.refresh_from_db()
        assert content_block_field.text != text


class TestUpdatePositions:
    @pytest.mark.django_db
    def test_update_positions_post(self, admin_client, content_block_factory):
        content_block_factory.create_batch(5)

        start_positions = [str(c.id) for c in ContentBlock.objects.all()]
        positions = [str(c.id) for c in ContentBlock.objects.order_by("-id").all()]
        assert start_positions != positions

        positions_str = "&cb[]=".join(positions)

        response = admin_client.post(
            reverse("content_blocks:update_position"),
            {"positions": "cb[]=" + positions_str},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200

        end_positions = [str(c.id) for c in ContentBlock.objects.all()]

        assert start_positions != end_positions
        assert positions == end_positions


class TestToggleVisible:
    @pytest.mark.django_db
    def test_toggle_visible_post(self, admin_client, content_block):
        visible = content_block.visible
        response = admin_client.post(
            reverse("content_blocks:toggle_visible", args=[content_block.id]),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        content_block.refresh_from_db()
        assert not visible == content_block.visible


class TestPublishContentBlocks:
    @pytest.mark.django_db
    def test_publish_content_blocks_post(
        self, admin_client, content_block_factory, content_block_collection
    ):
        content_block = content_block_factory.create(draft=True)
        assert ContentBlock.objects.drafts().count() == 1
        assert ContentBlock.objects.published().count() == 0

        content_block_collection.content_blocks.add(content_block)
        response = admin_client.post(
            reverse(
                f"{BASE_ADMIN_URL}_publish_content_blocks",
                args=[content_block_collection.id],
            ),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        assert ContentBlock.objects.published().count() == 1
        assert ContentBlock.objects.drafts().count() == 1


class TestDiscardChanges:
    @pytest.mark.django_db
    def test_discard_changes_post(
        self, admin_client, content_block, content_block_collection
    ):
        assert ContentBlock.objects.published().count() == 1
        assert ContentBlock.objects.drafts().count() == 0

        content_block_collection.content_blocks.add(content_block)

        response = admin_client.post(
            reverse(
                f"{BASE_ADMIN_URL}_discard_changes", args=[content_block_collection.id]
            ),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        assert ContentBlock.objects.published().count() == 1
        assert ContentBlock.objects.drafts().count() == 1


class TestImportContentBlocks:
    @pytest.mark.django_db
    def test_import_content_blocks(
        self, admin_client, content_block_factory, content_block_collection_factory
    ):
        collection_1 = content_block_collection_factory.create()
        collection_2 = content_block_collection_factory.create()

        content_block = content_block_factory.create(draft=True)
        assert ContentBlock.objects.drafts().count() == 1
        collection_1.content_blocks.add(content_block)

        response = admin_client.post(
            reverse(f"{BASE_ADMIN_URL}_import_content_blocks", args=[collection_2.id]),
            {"master": collection_1.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        assert ContentBlock.objects.drafts().count() == 2


class TestContentBlockPreview:
    @pytest.mark.django_db
    def test_content_block_preview(
        self, admin_client, content_block, content_block_collection
    ):
        content_block_collection.content_blocks.add(content_block)
        response = admin_client.post(
            reverse(
                "admin:content_blocks_contentblockcollection_content_block_preview",
                args=[content_block_collection.id, content_block.id],
            ),
        )
        assert response.status_code == 200


class TestDeleteContentBlock:
    @pytest.mark.django_db
    def test_delete_content_block(self, admin_client, content_block):
        assert ContentBlock.objects.count() == 1

        response = admin_client.post(
            reverse("content_blocks:content_block_delete", args=[content_block.id]),
            {},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        assert response.status_code == 200
        assert ContentBlock.objects.count() == 0
