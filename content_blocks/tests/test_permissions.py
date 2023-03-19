import pytest
from django.urls import reverse


class TestPermissions:
    @pytest.mark.django_db
    def test_ajax_required(self, admin_client, content_block):
        response = admin_client.post(
            reverse("content_blocks:content_block_delete", args=[content_block.id]),
            {},
        )

        assert response.status_code == 403
