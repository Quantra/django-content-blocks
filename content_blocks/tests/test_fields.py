import pytest

from content_blocks.fields import SVGAndImageFieldFormField


class TestSVGAndImageField:
    @pytest.mark.django_db
    def test_formfield(self, image_content_block_field_factory):
        content_block_field = image_content_block_field_factory.create()

        assert (
            content_block_field.image.field.formfield().__class__
            == SVGAndImageFieldFormField
        )


class TestVideoField:
    @pytest.mark.django_db
    def test_file_extension(self, populated_video_content_block_field_factory):
        content_block_field = populated_video_content_block_field_factory.create()

        assert content_block_field.video.file_extension == "mp4"
